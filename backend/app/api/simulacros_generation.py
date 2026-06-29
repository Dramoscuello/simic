from fastapi import Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional, Literal
from datetime import datetime
from pydantic import BaseModel, ValidationError
import os
import re

from app.api.deps import get_current_active_user
from app.database.config import get_db

from app.models.sede import Sede
from app.models.simulacro import Simulacro
from app.models.usuario import Usuario
from app.schemas.simulacro_v2 import Simulacro as SimulacroV2
from app.services.generation_service import SimulacroGenerator
from app.services.preguntas_usadas_service import registrar_preguntas_usadas
from app.services.qa_gate2_service import Gate2Validator
from app.services.qa_gate2_5_service import Gate25Validator
from app.services.qa_gate3_service import Gate3Deduplicator
from app.services.qa_gate4_service import Gate4RenderValidator
from app.services.qa_gate5_service import Gate5SemanticValidator
from app.services.qa_gate5b_service import Gate5BContextValidator
from app.services.qa_gate6_service import Gate6LogicValidator

from app.services.qa_gate7_service import Gate7MathValidator
from app.services.qa_gate_sociales_service import GateSocialesValidator
from app.services.visual_enrichment_service import VisualEnrichmentService
from app.core.graphic_types import normalize_graph_types_in_questions

from app.api.simulacros_router import router

# Schema para el request de generación
class DificultadConfig(BaseModel):
    """Configuración de porcentajes de dificultad"""
    facil: int = 30
    medio: int = 40
    dificil: int = 30

class GenerateRequest(BaseModel):
    """Request para generar simulacros automáticamente"""
    nombre_base: str  # Nombre base del simulacro (se agrega el área)
    institucion_id: int
    sede_ids: Optional[List[int]] = None  # Sedes a las que aplica; si no se envía se resuelven las disponibles
    areas: List[str]  # Lista de áreas a generar
    num_preguntas: int = 30  # Número de preguntas a generar por simulacro
    duracion_minutos: int = 60
    activar: bool = False
    dificultad: Optional[DificultadConfig] = None  # Porcentajes de dificultad
    modelo_generacion: Optional[str] = None  # Si no se envía, se usa DEFAULT_GENERATION_MODEL


class GenerateAreaResult(BaseModel):
    """Resultado de generación por área"""
    area: str
    status: str  # 'pending', 'generating', 'validating', 'completed', 'error'
    simulacro_id: Optional[int] = None
    error: Optional[str] = None


class GenerateResponse(BaseModel):
    """Response de la generación de simulacros (síncrona)"""
    total_areas: int
    completados: int
    errores: int
    resultados: List[GenerateAreaResult]


class AsyncGenerateResponse(BaseModel):
    """Response de la generación asíncrona de simulacros"""
    job_id: str
    status: str  # 'queued', 'running', 'completed', 'failed'
    message: str


class JobStatusResponse(BaseModel):
    """Estado de un job de generación"""
    id: str
    status: str
    progress: dict
    results: List[dict]
    completados: int
    errores: int
    created_at: Optional[str] = None
    completed_at: Optional[str] = None
    error: Optional[str] = None


def _extract_english_part(pregunta: Dict[str, Any]) -> Optional[int]:
    """Extrae el número de parte (1-7) desde 'componente' en preguntas de inglés."""
    componente = str(pregunta.get("componente", "") or "")
    match = re.search(r"(?:parte|part)\s*([1-7])", componente, re.IGNORECASE)
    if not match:
        return None
    try:
        part = int(match.group(1))
        return part if 1 <= part <= 7 else None
    except ValueError:
        return None


def _english_target_by_part(num_preguntas: int, dificultad: Optional[Dict[str, Any]]) -> Dict[int, int]:
    """
    Calcula cuotas objetivo por parte para inglés según distribución de dificultad.
    Fácil -> Partes 1,2,3; Medio -> 4,5; Difícil -> 6,7.
    """
    dificultad_req = dificultad or {"facil": 30, "medio": 40, "dificil": 30}
    target_facil = round(num_preguntas * dificultad_req.get("facil", 30) / 100)
    target_medio = round(num_preguntas * dificultad_req.get("medio", 40) / 100)
    target_dificil = num_preguntas - target_facil - target_medio

    target_by_part = {i: 0 for i in range(1, 8)}

    def allocate(total: int, parts_order: List[int]):
        if total <= 0 or not parts_order:
            return
        base = total // len(parts_order)
        rem = total % len(parts_order)
        for p in parts_order:
            target_by_part[p] += base
        for p in parts_order[:rem]:
            target_by_part[p] += 1

    # Prioridad comunicativa y de inferencia según prompt de inglés.
    allocate(target_facil, [1, 3, 2])
    allocate(target_medio, [4, 5])
    allocate(target_dificil, [6, 7])

    # Para simulacros de 30+, intentar cobertura de todas las partes.
    if num_preguntas >= 30:
        for p in range(1, 8):
            target_by_part[p] = max(target_by_part[p], 1)

        # Rebalancear si por cobertura mínima nos pasamos del total.
        overflow = sum(target_by_part.values()) - num_preguntas
        rebalance_order = [1, 2, 3, 4, 5, 6, 7]
        while overflow > 0:
            moved = False
            for p in rebalance_order:
                if target_by_part[p] > 1:
                    target_by_part[p] -= 1
                    overflow -= 1
                    moved = True
                    if overflow == 0:
                        break
            if not moved:
                break

    return target_by_part


def _renumerar_preguntas_consecutivas(contenido: Dict[str, Any]) -> None:
    """
    Reasigna IDs consecutivos (1..N) a la lista final de preguntas antes de guardar.

    Evita huecos de IDs tras trimming/blindaje/reparación, para mantener alineación
    estable con el orden visual de OMR (índices 1..N).
    """
    preguntas = contenido.get("preguntas", [])
    if not isinstance(preguntas, list):
        return

    cambios = 0
    for idx, pregunta in enumerate(preguntas, start=1):
        if not isinstance(pregunta, dict):
            continue
        old_id = pregunta.get("id")
        if old_id != idx:
            cambios += 1
        pregunta["id"] = idx

    if isinstance(contenido.get("meta"), dict):
        contenido["meta"]["total_preguntas"] = len(preguntas)

    if cambios > 0:
        print(f"   🔢 IDs renumerados tras trimming/blindaje: {cambios} ajuste(s), total={len(preguntas)}")


# ── BLINDAJE EQUILIBRADO MATEMÁTICAS ──

_MATH_COMPETENCIAS = [
    "Interpretación y representación",
    "Formulación y ejecución",
    "Argumentación",
]

_MATH_DIFICULTADES = ["facil", "medio", "dificil"]
_MATH_COMPONENTES = ["Álgebra y cálculo", "Estadística", "Geometría"]


def _extract_math_competencia(pregunta: Dict[str, Any]) -> Optional[str]:
    """Normaliza el campo 'competencia' a una de las 3 competencias oficiales ICFES."""
    raw = str(pregunta.get("competencia", "") or "").lower().strip()
    if "interpretaci" in raw or "representaci" in raw:
        return "Interpretación y representación"
    if "formulaci" in raw or "ejecuci" in raw:
        return "Formulación y ejecución"
    if "argumentaci" in raw:
        return "Argumentación"
    return None


def _extract_math_dificultad(pregunta: Dict[str, Any]) -> Optional[str]:
    """Normaliza el campo 'dificultad' a facil/medio/dificil."""
    raw = str(pregunta.get("dificultad", "") or "").lower().strip()
    if raw in _MATH_DIFICULTADES:
        return raw
    return None


def _extract_math_componente(pregunta: Dict[str, Any]) -> Optional[str]:
    """Normaliza el campo 'componente' a Álgebra y cálculo / Estadística / Geometría."""
    raw = str(pregunta.get("componente", "") or "").lower().strip()

    if any(x in raw for x in ["estad", "probab", "dato", "aleatorio", "muestra", "frecuencia"]):
        return "Estadística"
    if any(x in raw for x in ["geometr", "espacial", "metr", "plano", "triang", "circun", "angulo"]):
        return "Geometría"
    if any(x in raw for x in ["algebra", "cálculo", "calculo", "funcion", "ecuacion", "variacion", "razon"]):
        return "Álgebra y cálculo"
    return None


def _has_math_visual(pregunta: Dict[str, Any]) -> bool:
    """Determina si una pregunta cuenta como visual para la cuota de Matemáticas."""
    raw_flag = pregunta.get("tiene_grafico", False)
    if isinstance(raw_flag, bool):
        tiene_grafico = raw_flag
    else:
        tiene_grafico = str(raw_flag).strip().lower() in {"true", "1", "si", "sí"}
    if not tiene_grafico:
        return False
    tipo = str(pregunta.get("tipo_grafico", "") or "").strip().lower()
    return bool(tipo and tipo not in {"none", "null", "ninguno"})


def _count_math_component_distribution(preguntas: List[Dict[str, Any]]) -> Dict[str, int]:
    """Cuenta distribución por componente para Matemáticas."""
    counts = {c: 0 for c in _MATH_COMPONENTES}
    for p in preguntas:
        comp = _extract_math_componente(p)
        if comp:
            counts[comp] += 1
    return counts


def _math_component_limits(num_preguntas: int) -> Dict[str, Dict[str, int]]:
    """
    Límites de componente para Matemáticas según marco ICFES:
    - Álgebra y cálculo: 35-40%
    - Estadística: 35-40%
    - Geometría: 20-35%
    """
    import math

    mins = {
        "Álgebra y cálculo": math.ceil(num_preguntas * 0.35),
        "Estadística": math.ceil(num_preguntas * 0.35),
        "Geometría": math.ceil(num_preguntas * 0.20),
    }
    maxs = {
        "Álgebra y cálculo": math.floor(num_preguntas * 0.40),
        "Estadística": math.floor(num_preguntas * 0.40),
        "Geometría": math.floor(num_preguntas * 0.35),
    }

    # Ajustes para tamaños pequeños donde ceil puede volver inviables los mínimos.
    while sum(mins.values()) > num_preguntas:
        k = max(mins, key=mins.get)
        if mins[k] == 0:
            break
        mins[k] -= 1

    for c in _MATH_COMPONENTES:
        mins[c] = max(0, mins[c])
        maxs[c] = max(maxs[c], mins[c])

    return {c: {"min": mins[c], "max": maxs[c]} for c in _MATH_COMPONENTES}


def _rebalance_math_components(
    selected: List[Dict[str, Any]],
    pool: List[Dict[str, Any]],
    num_preguntas: int,
) -> List[Dict[str, Any]]:
    """
    Rebalancea componentes para mantenerlos en rangos ICFES con swaps de mínimo impacto.
    Prioriza swaps que conserven competencia + dificultad.
    """
    if not selected or not pool:
        return selected

    limits = _math_component_limits(num_preguntas)
    counts = _count_math_component_distribution(selected)
    max_iters = max(10, len(selected) * 4)
    it = 0

    while it < max_iters:
        over = sorted(
            [c for c in _MATH_COMPONENTES if counts[c] > limits[c]["max"]],
            key=lambda c: counts[c] - limits[c]["max"],
            reverse=True,
        )
        under = sorted(
            [c for c in _MATH_COMPONENTES if counts[c] < limits[c]["min"]],
            key=lambda c: limits[c]["min"] - counts[c],
            reverse=True,
        )
        if not over or not under:
            break

        over_c = over[0]
        under_c = under[0]
        best_swap = None  # (score, sel_idx, pool_idx)

        for sel_idx, current in enumerate(selected):
            if _extract_math_componente(current) != over_c:
                continue
            comp_cur = _extract_math_competencia(current)
            dif_cur = _extract_math_dificultad(current)
            vis_cur = _has_math_visual(current)

            for pool_idx, candidate in enumerate(pool):
                if _extract_math_componente(candidate) != under_c:
                    continue
                score = 0
                if _extract_math_competencia(candidate) == comp_cur:
                    score += 2
                if _extract_math_dificultad(candidate) == dif_cur:
                    score += 2
                if _has_math_visual(candidate) == vis_cur:
                    score += 1
                if best_swap is None or score > best_swap[0]:
                    best_swap = (score, sel_idx, pool_idx)
                    if score >= 5:
                        break
            if best_swap and best_swap[0] >= 5:
                break

        if not best_swap:
            break

        _, sel_idx, pool_idx = best_swap
        old_q = selected[sel_idx]
        new_q = pool[pool_idx]
        selected[sel_idx] = new_q
        pool[pool_idx] = old_q

        counts[over_c] -= 1
        counts[under_c] += 1
        it += 1

    return selected


def _rebalance_math_visual_quota(
    selected: List[Dict[str, Any]],
    pool: List[Dict[str, Any]],
    num_preguntas: int,
) -> List[Dict[str, Any]]:
    """Ajusta con swaps para cumplir cuota visual exacta del 60% en Matemáticas."""
    if not selected or not pool:
        return selected

    target_visual = round(num_preguntas * 0.60)
    current_visual = sum(1 for p in selected if _has_math_visual(p))

    if current_visual == target_visual:
        return selected

    need_visual = current_visual < target_visual
    max_swaps = max(10, abs(target_visual - current_visual) * 4)
    swaps = 0

    while current_visual != target_visual and swaps < max_swaps:
        best_swap = None  # (score, sel_idx, pool_idx)

        for sel_idx, current in enumerate(selected):
            if _has_math_visual(current) == need_visual:
                continue

            comp_cur = _extract_math_competencia(current)
            dif_cur = _extract_math_dificultad(current)
            com_cur = _extract_math_componente(current)

            for pool_idx, candidate in enumerate(pool):
                if _has_math_visual(candidate) != need_visual:
                    continue
                score = 0
                if _extract_math_competencia(candidate) == comp_cur:
                    score += 2
                if _extract_math_dificultad(candidate) == dif_cur:
                    score += 2
                if _extract_math_componente(candidate) == com_cur:
                    score += 1
                if best_swap is None or score > best_swap[0]:
                    best_swap = (score, sel_idx, pool_idx)
                    if score >= 5:
                        break
            if best_swap and best_swap[0] >= 5:
                break

        if not best_swap:
            break

        _, sel_idx, pool_idx = best_swap
        old_q = selected[sel_idx]
        new_q = pool[pool_idx]
        selected[sel_idx] = new_q
        pool[pool_idx] = old_q

        current_visual = sum(1 for p in selected if _has_math_visual(p))
        need_visual = current_visual < target_visual
        swaps += 1

    return selected


def _math_target_distribution(
    num_preguntas: int,
    dificultad: Optional[Dict[str, Any]],
) -> Dict[str, Dict[str, int]]:
    """
    Calcula cuotas objetivo por (competencia, dificultad) para Matemáticas.

    Distribución ICFES:
      - Competencias: 34% Interpretación, 43% Formulación, 23% Argumentación
      - Dificultad: según parámetro (default 30/40/30)

    Retorna: {competencia: {facil: N, medio: N, dificil: N}}
    """
    # Cuotas por competencia
    comp_ratios = {
        "Interpretación y representación": 0.34,
        "Formulación y ejecución": 0.43,
        "Argumentación": 0.23,
    }

    dificultad_req = dificultad or {"facil": 30, "medio": 40, "dificil": 30}
    dif_ratios = {
        "facil": dificultad_req.get("facil", 30) / 100,
        "medio": dificultad_req.get("medio", 40) / 100,
        "dificil": dificultad_req.get("dificil", 30) / 100,
    }

    # Calcular cuota ideal por celda (competencia × dificultad)
    targets: Dict[str, Dict[str, int]] = {}
    assigned_total = 0

    for comp, comp_r in comp_ratios.items():
        targets[comp] = {}
        for dif, dif_r in dif_ratios.items():
            val = round(num_preguntas * comp_r * dif_r)
            targets[comp][dif] = val
            assigned_total += val

    # Ajustar redondeo para que sume exactamente num_preguntas
    diff = num_preguntas - assigned_total
    # Distribuir diferencia en las celdas más grandes
    if diff != 0:
        cells = [(c, d) for c in targets for d in targets[c]]
        cells.sort(key=lambda x: targets[x[0]][x[1]], reverse=True)
        step = 1 if diff > 0 else -1
        for i in range(abs(diff)):
            c, d = cells[i % len(cells)]
            targets[c][d] += step

    return targets


def _count_math_distribution(
    preguntas: List[Dict[str, Any]],
) -> Dict[str, Dict[str, int]]:
    """Cuenta la distribución actual de preguntas por competencia × dificultad."""
    counts: Dict[str, Dict[str, int]] = {
        c: {d: 0 for d in _MATH_DIFICULTADES}
        for c in _MATH_COMPETENCIAS
    }
    for p in preguntas:
        comp = _extract_math_competencia(p)
        dif = _extract_math_dificultad(p)
        if comp and dif:
            counts[comp][dif] += 1
    return counts


def _seleccionar_blindaje_equilibrado_matematicas(
    preguntas_validas: List[Dict[str, Any]],
    num_preguntas: int,
    dificultad: Optional[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Selección de blindaje para MATEMÁTICAS:
    - Respeta cuotas por competencia (34/43/23) y dificultad (configurable).
    - Aplica rebalanceo secundario por componente (rangos ICFES).
    - Aplica rebalanceo secundario para cuota visual exacta (60%).
    - Usa selección greedy por déficit para maximizar equidad.
    """
    if len(preguntas_validas) <= num_preguntas:
        return list(preguntas_validas)

    targets = _math_target_distribution(num_preguntas, dificultad)

    # Clasificar preguntas disponibles en buckets (competencia, dificultad)
    buckets: Dict[str, Dict[str, List]] = {
        c: {d: [] for d in _MATH_DIFICULTADES}
        for c in _MATH_COMPETENCIAS
    }
    fallback: List = []

    for p in preguntas_validas:
        comp = _extract_math_competencia(p)
        dif = _extract_math_dificultad(p)
        if comp and dif:
            buckets[comp][dif].append(p)
        else:
            fallback.append(p)

    # Ordenar cada bucket por ID para estabilidad
    for comp in buckets:
        for dif in buckets[comp]:
            buckets[comp][dif].sort(key=lambda q: q.get("id", 0))
    fallback.sort(key=lambda q: q.get("id", 0))

    selected: List = []
    selected_count: Dict[str, Dict[str, int]] = {
        c: {d: 0 for d in _MATH_DIFICULTADES}
        for c in _MATH_COMPETENCIAS
    }

    # Paso 1: Llenar cuotas objetivo por celda
    for comp in _MATH_COMPETENCIAS:
        for dif in _MATH_DIFICULTADES:
            need = targets[comp][dif]
            while need > 0 and buckets[comp][dif] and len(selected) < num_preguntas:
                selected.append(buckets[comp][dif].pop(0))
                selected_count[comp][dif] += 1
                need -= 1

    # Paso 2: Completar faltantes con selección por mayor déficit
    while len(selected) < num_preguntas:
        best_cell = None
        best_deficit = -999

        for comp in _MATH_COMPETENCIAS:
            for dif in _MATH_DIFICULTADES:
                if not buckets[comp][dif]:
                    continue
                deficit = targets[comp][dif] - selected_count[comp][dif]
                if deficit > best_deficit:
                    best_deficit = deficit
                    best_cell = (comp, dif)

        if best_cell:
            comp, dif = best_cell
            selected.append(buckets[comp][dif].pop(0))
            selected_count[comp][dif] += 1
            continue

        # Sin preguntas clasificables, usar fallback
        if fallback:
            selected.append(fallback.pop(0))
            continue

        break  # No quedan preguntas

    # Armar pool remanente para posibles swaps de rebalanceo.
    remaining_pool: List[Dict[str, Any]] = []
    for comp in _MATH_COMPETENCIAS:
        for dif in _MATH_DIFICULTADES:
            remaining_pool.extend(buckets[comp][dif])
    remaining_pool.extend(fallback)
    remaining_pool.sort(key=lambda q: q.get("id", 0))

    # Rebalanceos secundarios (sin tocar otras áreas).
    selected = _rebalance_math_components(selected, remaining_pool, num_preguntas)
    selected = _rebalance_math_visual_quota(selected, remaining_pool, num_preguntas)

    selected.sort(key=lambda q: q.get("id", 0))
    return selected[:num_preguntas]


# -- BLINDAJE EQUILIBRADO LECTURA CRITICA --

_LECTURA_AFIRMACIONES = [
    "Identificar y entender contenidos locales",
    "Comprender cómo se articulan las partes",
    "Reflexionar y evaluar un texto",
]
_LECTURA_DIFICULTADES = ["facil", "medio", "dificil"]


def _extract_lectura_afirmacion(pregunta: Dict[str, Any]) -> Optional[str]:
    """Normaliza la competencia de Lectura a una de las 3 afirmaciones oficiales."""
    raw = str(pregunta.get("competencia", "") or "").lower().strip()

    if (
        "identificar y entender contenidos locales" in raw
        or "contenido local" in raw
        or "literal" in raw
    ):
        return "Identificar y entender contenidos locales"

    if (
        "comprender cómo se articulan las partes" in raw
        or "comprender como se articulan las partes" in raw
        or "articul" in raw
        or "inferenc" in raw
    ):
        return "Comprender cómo se articulan las partes"

    if (
        "reflexionar y evaluar un texto" in raw
        or "reflex" in raw
        or "critic" in raw
        or "evalu" in raw
    ):
        return "Reflexionar y evaluar un texto"

    return None


def _lectura_target_distribution(
    num_preguntas: int,
    dificultad: Optional[Dict[str, Any]],
) -> Dict[str, Dict[str, int]]:
    """
    Cuotas objetivo por (afirmacion, dificultad) para Lectura Critica.

    Afirmaciones:
      - 25% Identificar y entender contenidos locales
      - 42% Comprender como se articulan las partes
      - 33% Reflexionar y evaluar un texto
    """
    comp_ratios = {
        "Identificar y entender contenidos locales": 0.25,
        "Comprender cómo se articulan las partes": 0.42,
        "Reflexionar y evaluar un texto": 0.33,
    }

    dificultad_req = dificultad or {"facil": 30, "medio": 40, "dificil": 30}
    dif_ratios = {
        "facil": dificultad_req.get("facil", 30) / 100,
        "medio": dificultad_req.get("medio", 40) / 100,
        "dificil": dificultad_req.get("dificil", 30) / 100,
    }

    targets: Dict[str, Dict[str, int]] = {}
    assigned_total = 0

    for comp, comp_r in comp_ratios.items():
        targets[comp] = {}
        for dif, dif_r in dif_ratios.items():
            val = round(num_preguntas * comp_r * dif_r)
            targets[comp][dif] = val
            assigned_total += val

    diff = num_preguntas - assigned_total
    if diff != 0:
        cells = [(c, d) for c in targets for d in targets[c]]
        cells.sort(key=lambda x: targets[x[0]][x[1]], reverse=True)
        step = 1 if diff > 0 else -1
        for i in range(abs(diff)):
            c, d = cells[i % len(cells)]
            targets[c][d] += step

    return targets


def _count_lectura_distribution(
    preguntas: List[Dict[str, Any]],
) -> Dict[str, Dict[str, int]]:
    """Cuenta distribucion actual por afirmacion x dificultad."""
    counts: Dict[str, Dict[str, int]] = {
        c: {d: 0 for d in _LECTURA_DIFICULTADES}
        for c in _LECTURA_AFIRMACIONES
    }

    for p in preguntas:
        comp = _extract_lectura_afirmacion(p)
        dif = _extract_math_dificultad(p)
        if comp and dif:
            counts[comp][dif] += 1

    return counts


def _seleccionar_blindaje_equilibrado_lectura(
    preguntas_validas: List[Dict[str, Any]],
    num_preguntas: int,
    dificultad: Optional[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Seleccion de blindaje para LECTURA_CRITICA:
    - Respeta cuotas por afirmacion (25/42/33).
    - Respeta dificultad dinamica solicitada.
    - Usa seleccion greedy por deficit.
    """
    if len(preguntas_validas) <= num_preguntas:
        return list(preguntas_validas)

    targets = _lectura_target_distribution(num_preguntas, dificultad)

    buckets: Dict[str, Dict[str, List]] = {
        c: {d: [] for d in _LECTURA_DIFICULTADES}
        for c in _LECTURA_AFIRMACIONES
    }
    fallback: List = []

    for p in preguntas_validas:
        comp = _extract_lectura_afirmacion(p)
        dif = _extract_math_dificultad(p)
        if comp and dif:
            buckets[comp][dif].append(p)
        else:
            fallback.append(p)

    for comp in buckets:
        for dif in buckets[comp]:
            buckets[comp][dif].sort(key=lambda q: q.get("id", 0))
    fallback.sort(key=lambda q: q.get("id", 0))

    selected: List = []
    selected_count: Dict[str, Dict[str, int]] = {
        c: {d: 0 for d in _LECTURA_DIFICULTADES}
        for c in _LECTURA_AFIRMACIONES
    }

    # Paso 1: llenar cuotas objetivo por celda
    for comp in _LECTURA_AFIRMACIONES:
        for dif in _LECTURA_DIFICULTADES:
            need = targets[comp][dif]
            while need > 0 and buckets[comp][dif] and len(selected) < num_preguntas:
                selected.append(buckets[comp][dif].pop(0))
                selected_count[comp][dif] += 1
                need -= 1

    # Paso 2: completar faltantes por mayor deficit
    while len(selected) < num_preguntas:
        best_cell = None
        best_deficit = -999

        for comp in _LECTURA_AFIRMACIONES:
            for dif in _LECTURA_DIFICULTADES:
                if not buckets[comp][dif]:
                    continue
                deficit = targets[comp][dif] - selected_count[comp][dif]
                if deficit > best_deficit:
                    best_deficit = deficit
                    best_cell = (comp, dif)

        if best_cell:
            comp, dif = best_cell
            selected.append(buckets[comp][dif].pop(0))
            selected_count[comp][dif] += 1
            continue

        if fallback:
            selected.append(fallback.pop(0))
            continue

        break

    selected.sort(key=lambda q: q.get("id", 0))
    return selected[:num_preguntas]


# -- BLINDAJE EQUILIBRADO CIENCIAS NATURALES --

_CN_COMPONENTES = ["Biologico", "Fisico", "Quimico", "CTS"]
_CN_COMPETENCIAS = [
    "Uso comprensivo del conocimiento cientifico",
    "Explicacion de fenomenos",
    "Indagacion",
]
_CN_DIFICULTADES = ["facil", "medio", "dificil"]


def _extract_cn_componente(pregunta: Dict[str, Any]) -> Optional[str]:
    """Normaliza el campo 'componente' a uno de los 4 componentes oficiales ICFES."""
    raw = str(pregunta.get("componente", "") or "").lower().strip()
    if "biolog" in raw or "bio" in raw:
        return "Biologico"
    if "fisic" in raw or "fis" in raw:
        return "Fisico"
    if "quim" in raw or "quim" in raw:
        return "Quimico"
    if "cts" in raw or "tecnolog" in raw or "sociedad" in raw:
        return "CTS"
    return None


def _extract_cn_competencia(pregunta: Dict[str, Any]) -> Optional[str]:
    """Normaliza el campo 'competencia' a una de las 3 competencias oficiales ICFES."""
    raw = str(pregunta.get("competencia", "") or "").lower().strip()
    if "indagaci" in raw:
        return "Indagacion"
    if "uso" in raw or "comprensivo" in raw:
        return "Uso comprensivo del conocimiento cientifico"
    if "explicaci" in raw:
        return "Explicacion de fenomenos"
    return None


def _cn_target_distribution(
    num_preguntas: int,
    dificultad: Optional[Dict[str, Any]],
) -> Dict[str, Dict[str, int]]:
    """
    Calcula cuotas objetivo por (componente, dificultad) para Ciencias Naturales.

    Distribucion ICFES:
      - Componentes: Bio 30%, Fis 30%, Quim 30%, CTS 10%
      - Dificultad: segun parametro (default 30/40/30)
    """
    comp_ratios = {
        "Biologico": 0.30,
        "Fisico": 0.30,
        "Quimico": 0.30,
        "CTS": 0.10,
    }

    dificultad_req = dificultad or {"facil": 30, "medio": 40, "dificil": 30}
    dif_ratios = {
        "facil": dificultad_req.get("facil", 30) / 100,
        "medio": dificultad_req.get("medio", 40) / 100,
        "dificil": dificultad_req.get("dificil", 30) / 100,
    }

    targets: Dict[str, Dict[str, int]] = {}
    assigned_total = 0

    for comp, comp_r in comp_ratios.items():
        targets[comp] = {}
        for dif, dif_r in dif_ratios.items():
            val = round(num_preguntas * comp_r * dif_r)
            targets[comp][dif] = val
            assigned_total += val

    diff = num_preguntas - assigned_total
    if diff != 0:
        cells = [(c, d) for c in targets for d in targets[c]]
        cells.sort(key=lambda x: targets[x[0]][x[1]], reverse=True)
        step = 1 if diff > 0 else -1
        for i in range(abs(diff)):
            c, d = cells[i % len(cells)]
            targets[c][d] += step

    return targets


def _count_cn_distribution(
    preguntas: List[Dict[str, Any]],
) -> Dict[str, Dict[str, int]]:
    """Cuenta la distribucion actual por componente x dificultad."""
    counts: Dict[str, Dict[str, int]] = {
        c: {d: 0 for d in _CN_DIFICULTADES}
        for c in _CN_COMPONENTES
    }
    for p in preguntas:
        comp = _extract_cn_componente(p)
        dif = _extract_math_dificultad(p)  # Reutiliza normalizacion de dificultad
        if comp and dif:
            counts[comp][dif] += 1
    return counts


def _seleccionar_blindaje_equilibrado_ciencias(
    preguntas_validas: List[Dict[str, Any]],
    num_preguntas: int,
    dificultad: Optional[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Seleccion de blindaje para CIENCIAS NATURALES:
    - Respeta cuotas por componente (30/30/30/10) y dificultad (configurable).
    - Usa seleccion greedy por deficit para maximizar equidad.
    """
    if len(preguntas_validas) <= num_preguntas:
        return list(preguntas_validas)

    targets = _cn_target_distribution(num_preguntas, dificultad)

    buckets: Dict[str, Dict[str, List]] = {
        c: {d: [] for d in _CN_DIFICULTADES}
        for c in _CN_COMPONENTES
    }
    fallback: List = []

    for p in preguntas_validas:
        comp = _extract_cn_componente(p)
        dif = _extract_math_dificultad(p)
        if comp and dif:
            buckets[comp][dif].append(p)
        else:
            fallback.append(p)

    for comp in buckets:
        for dif in buckets[comp]:
            buckets[comp][dif].sort(key=lambda q: q.get("id", 0))
    fallback.sort(key=lambda q: q.get("id", 0))

    selected: List = []
    selected_count: Dict[str, Dict[str, int]] = {
        c: {d: 0 for d in _CN_DIFICULTADES}
        for c in _CN_COMPONENTES
    }

    # Paso 1: Llenar cuotas objetivo por celda
    for comp in _CN_COMPONENTES:
        for dif in _CN_DIFICULTADES:
            need = targets[comp][dif]
            while need > 0 and buckets[comp][dif] and len(selected) < num_preguntas:
                selected.append(buckets[comp][dif].pop(0))
                selected_count[comp][dif] += 1
                need -= 1

    # Paso 2: Completar faltantes con seleccion por mayor deficit
    while len(selected) < num_preguntas:
        best_cell = None
        best_deficit = -999

        for comp in _CN_COMPONENTES:
            for dif in _CN_DIFICULTADES:
                if not buckets[comp][dif]:
                    continue
                deficit = targets[comp][dif] - selected_count[comp][dif]
                if deficit > best_deficit:
                    best_deficit = deficit
                    best_cell = (comp, dif)

        if best_cell:
            comp, dif = best_cell
            selected.append(buckets[comp][dif].pop(0))
            selected_count[comp][dif] += 1
            continue

        if fallback:
            selected.append(fallback.pop(0))
            continue

        break

    selected.sort(key=lambda q: q.get("id", 0))
    return selected[:num_preguntas]


_SOCIALES_COMPETENCIAS = [
    "Pensamiento social",
    "Interpretación y análisis de perspectivas",
    "Pensamiento reflexivo y sistémico",
]
_SOCIALES_DIFICULTADES = ["facil", "medio", "dificil"]


def _extract_sociales_competencia(pregunta: Dict[str, Any]) -> Optional[str]:
    """Normaliza la competencia de Sociales a uno de los 3 ejes oficiales."""
    raw = str(pregunta.get("competencia", "") or "").lower().strip()

    if "pensamiento social" in raw:
        return "Pensamiento social"
    if "interpret" in raw and ("perspect" in raw or "analisis" in raw):
        return "Interpretación y análisis de perspectivas"
    if "reflexivo" in raw or "sistem" in raw:
        return "Pensamiento reflexivo y sistémico"
    return None


def _extract_sociales_dificultad(pregunta: Dict[str, Any]) -> Optional[str]:
    """Normaliza dificultad para Sociales (facil/medio/dificil)."""
    raw = str(pregunta.get("dificultad", "") or "").lower().strip()
    if "fac" in raw:
        return "facil"
    if "med" in raw:
        return "medio"
    if "dif" in raw:
        return "dificil"
    return None


def _sociales_target_distribution(
    num_preguntas: int,
    dificultad: Optional[Dict[str, Any]],
) -> Dict[str, Dict[str, int]]:
    """
    Cuotas objetivo por (competencia, dificultad) para Sociales.

    Competencias: fijas segun lineamiento institucional del proyecto.
    Dificultad: dinamica segun request del usuario.
    """
    comp_ratios = {
        "Pensamiento social": 0.35,
        "Interpretación y análisis de perspectivas": 0.30,
        "Pensamiento reflexivo y sistémico": 0.35,
    }

    dificultad_req = dificultad or {"facil": 30, "medio": 40, "dificil": 30}
    dif_ratios = {
        "facil": dificultad_req.get("facil", 30) / 100,
        "medio": dificultad_req.get("medio", 40) / 100,
        "dificil": dificultad_req.get("dificil", 30) / 100,
    }

    targets: Dict[str, Dict[str, int]] = {}
    assigned_total = 0

    for comp, comp_r in comp_ratios.items():
        targets[comp] = {}
        for dif, dif_r in dif_ratios.items():
            val = round(num_preguntas * comp_r * dif_r)
            targets[comp][dif] = val
            assigned_total += val

    diff = num_preguntas - assigned_total
    if diff != 0:
        cells = [(c, d) for c in targets for d in targets[c]]
        cells.sort(key=lambda x: targets[x[0]][x[1]], reverse=True)
        step = 1 if diff > 0 else -1
        for i in range(abs(diff)):
            c, d = cells[i % len(cells)]
            targets[c][d] += step

    return targets


def _count_sociales_distribution(
    preguntas: List[Dict[str, Any]],
) -> Dict[str, Dict[str, int]]:
    """Cuenta distribucion actual por competencia x dificultad."""
    counts: Dict[str, Dict[str, int]] = {
        c: {d: 0 for d in _SOCIALES_DIFICULTADES}
        for c in _SOCIALES_COMPETENCIAS
    }
    for p in preguntas:
        comp = _extract_sociales_competencia(p)
        dif = _extract_sociales_dificultad(p)
        if comp and dif:
            counts[comp][dif] += 1
    return counts


def _seleccionar_blindaje_equilibrado_sociales(
    preguntas_validas: List[Dict[str, Any]],
    num_preguntas: int,
    dificultad: Optional[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Seleccion de blindaje para SOCIALES_CIUDADANAS:
    - Respeta cuotas fijas por competencia.
    - Respeta dificultad dinamica solicitada.
    - Usa seleccion greedy por deficit.
    """
    if len(preguntas_validas) <= num_preguntas:
        return list(preguntas_validas)

    targets = _sociales_target_distribution(num_preguntas, dificultad)

    buckets: Dict[str, Dict[str, List]] = {
        c: {d: [] for d in _SOCIALES_DIFICULTADES}
        for c in _SOCIALES_COMPETENCIAS
    }
    fallback: List = []

    for p in preguntas_validas:
        comp = _extract_sociales_competencia(p)
        dif = _extract_sociales_dificultad(p)
        if comp and dif:
            buckets[comp][dif].append(p)
        else:
            fallback.append(p)

    for comp in buckets:
        for dif in buckets[comp]:
            buckets[comp][dif].sort(key=lambda q: q.get("id", 0))
    fallback.sort(key=lambda q: q.get("id", 0))

    selected: List = []
    selected_count: Dict[str, Dict[str, int]] = {
        c: {d: 0 for d in _SOCIALES_DIFICULTADES}
        for c in _SOCIALES_COMPETENCIAS
    }

    # Paso 1: llenar cuotas objetivo
    for comp in _SOCIALES_COMPETENCIAS:
        for dif in _SOCIALES_DIFICULTADES:
            need = targets[comp][dif]
            while need > 0 and buckets[comp][dif] and len(selected) < num_preguntas:
                selected.append(buckets[comp][dif].pop(0))
                selected_count[comp][dif] += 1
                need -= 1

    # Paso 2: completar faltantes por mayor deficit
    while len(selected) < num_preguntas:
        best_cell = None
        best_deficit = -999

        for comp in _SOCIALES_COMPETENCIAS:
            for dif in _SOCIALES_DIFICULTADES:
                if not buckets[comp][dif]:
                    continue
                deficit = targets[comp][dif] - selected_count[comp][dif]
                if deficit > best_deficit:
                    best_deficit = deficit
                    best_cell = (comp, dif)

        if best_cell:
            comp, dif = best_cell
            selected.append(buckets[comp][dif].pop(0))
            selected_count[comp][dif] += 1
            continue

        if fallback:
            selected.append(fallback.pop(0))
            continue

        break

    selected.sort(key=lambda q: q.get("id", 0))
    return selected[:num_preguntas]


def _count_english_parts(preguntas: List[Dict[str, Any]]) -> Dict[int, int]:
    counts = {i: 0 for i in range(1, 8)}
    for p in preguntas:
        part = _extract_english_part(p)
        if part:
            counts[part] += 1
    return counts


def _seleccionar_blindaje_equilibrado_ingles(
    preguntas_validas: List[Dict[str, Any]],
    num_preguntas: int,
    dificultad: Optional[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Selección de blindaje para INGLÉS:
    - Respeta cuotas por parte derivadas de 30/40/30 (o config solicitada).
    - Para simulacros de 30+ fuerza cobertura mínima de partes 1-7 si hay disponibilidad.
    """
    if len(preguntas_validas) <= num_preguntas:
        return list(preguntas_validas)

    # Buckets por parte y fallback (sin componente parseable)
    buckets = {i: [] for i in range(1, 8)}
    fallback = []
    for p in preguntas_validas:
        part = _extract_english_part(p)
        if part in buckets:
            buckets[part].append(p)
        else:
            fallback.append(p)

    for part in buckets:
        buckets[part].sort(key=lambda q: q.get("id", 0))
    fallback.sort(key=lambda q: q.get("id", 0))

    target_by_part = _english_target_by_part(num_preguntas, dificultad)
    selected = []
    selected_by_part = {i: 0 for i in range(1, 8)}

    # Paso 1: cobertura mínima de partes en simulacros grandes
    if num_preguntas >= 30:
        for part in range(1, 8):
            if len(selected) >= num_preguntas:
                break
            if buckets[part]:
                selected.append(buckets[part].pop(0))
                selected_by_part[part] += 1

    # Paso 2: llenar cuotas objetivo por parte
    for part in range(1, 8):
        need = max(target_by_part[part] - selected_by_part[part], 0)
        while need > 0 and len(selected) < num_preguntas and buckets[part]:
            selected.append(buckets[part].pop(0))
            selected_by_part[part] += 1
            need -= 1

    # Paso 3: completar preguntas faltantes de forma balanceada por déficit
    while len(selected) < num_preguntas:
        available_parts = [p for p in range(1, 8) if buckets[p]]
        if available_parts:
            # Prioriza la parte más deficitaria vs su cuota; si no hay déficit, la de mayor inventario.
            available_parts.sort(
                key=lambda p: (
                    target_by_part[p] - selected_by_part[p],
                    len(buckets[p]),
                    -p,
                ),
                reverse=True
            )
            chosen_part = available_parts[0]
            selected.append(buckets[chosen_part].pop(0))
            selected_by_part[chosen_part] += 1
            continue

        if fallback:
            selected.append(fallback.pop(0))
            continue

        break

    selected.sort(key=lambda q: q.get("id", 0))
    return selected[:num_preguntas]


def _resolve_openai_timeout(num_preguntas: int) -> int:
    """
    Timeout dinámico para comunicación con OpenAI durante creación de simulacros.
    - <= 30 preguntas: 300s
    - 31..50 preguntas: 600s
    - > 50 preguntas: 600s (fallback defensivo)
    """
    if num_preguntas <= 30:
        return 300
    if num_preguntas <= 50:
        return 600
    return 600


# ==========================================
# GENERACIÓN ASÍNCRONA
# ==========================================

from fastapi import BackgroundTasks

@router.post("/generate-async", response_model=AsyncGenerateResponse)
def generate_simulacros_async(
    request: GenerateRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """
    Genera simulacros de forma asíncrona (background).
    
    - Retorna inmediatamente con un job_id
    - El proceso continúa en background
    - Usar GET /jobs/{job_id} para consultar progreso
    
    Solo el administrador de la institución puede usar este endpoint.
    """
    # Validar permisos
    rol_nombre = current_user.rol.nombre if current_user.rol else ""
    allowed_roles = ['admin']
    if rol_nombre not in allowed_roles:
         raise HTTPException(status_code=403, detail="No tiene permisos para generar simulacros")

    # Forzar ID de su propia institución
    request.institucion_id = current_user.institucion_id

    # Validar áreas
    areas_validas = ["MATEMATICAS", "CIENCIAS_NATURALES", "SOCIALES_CIUDADANAS", "LECTURA_CRITICA", "INGLES"]
    for area in request.areas:
        if area not in areas_validas:
            raise HTTPException(
                status_code=400,
                detail=f"Área inválida: {area}. Áreas válidas: {areas_validas}"
            )

    # Crear job en Redis
    try:
        from app.core.redis_config import JobTracker, is_redis_available
        if not is_redis_available():
            raise HTTPException(
                status_code=503,
                detail="Redis no disponible. Use /generate para generación síncrona."
            )

        # Resolver y validar sedes
        if not request.sede_ids:
            sedes = db.query(Sede).filter(
                Sede.institucion_id == request.institucion_id,
                Sede.activo == True
            ).order_by(Sede.id).all()
            if not sedes:
                raise HTTPException(
                    status_code=400,
                    detail="La institución no tiene sedes configuradas"
                )
            request.sede_ids = [sede.id for sede in sedes]
        else:
            # Validar que las sedes pertenezcan a la institución
            sedes = db.query(Sede).filter(Sede.id.in_(request.sede_ids)).all()
            sedes_ids_db = {sede.id for sede in sedes}
            if len(sedes_ids_db) != len(request.sede_ids):
                raise HTTPException(status_code=400, detail="Una o más sedes no existen")
            for sede in sedes:
                if sede.institucion_id != request.institucion_id:
                    raise HTTPException(status_code=400, detail="La sede no pertenece a la institución")

        tracker = JobTracker()
        job_id = tracker.create_job(
            institucion_id=request.institucion_id,
            areas=request.areas,
            user_id=current_user.id
        )

        # Encolar tarea en background
        # IMPORTANTE: render_as_string(hide_password=False) para obtener URL completa
        db_url = db.get_bind().url.render_as_string(hide_password=False)
        # Preparar request dict con metadata del solicitante
        request_dict = request.dict()
        request_dict["requester_id"] = current_user.id

        background_tasks.add_task(
            run_generation_job,
            job_id=job_id,
            request_dict=request_dict,
            db_url=db_url
        )

        return AsyncGenerateResponse(
            job_id=job_id,
            status="queued",
            message=f"Job creado. Generando {len(request.areas)} área(s) para {len(request.sede_ids)} sede(s) en background."
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/jobs/{job_id}", response_model=JobStatusResponse)
def get_job_status(
    job_id: str,
    current_user: Usuario = Depends(get_current_active_user)
):
    """
    Consulta el estado de un job de generación.
    
    Hacer polling cada 5 segundos para ver el progreso.
    """
    try:
        from app.core.redis_config import JobTracker, is_redis_available
        if not is_redis_available():
            raise HTTPException(status_code=503, detail="Redis no disponible")
        
        tracker = JobTracker()
        job = tracker.get_job(job_id)
        
        if not job:
            raise HTTPException(status_code=404, detail=f"Job {job_id} no encontrado")
        
        return JobStatusResponse(
            id=job["id"],
            status=job["status"],
            progress=job["progress"],
            results=job["results"],
            completados=job["completados"],
            errores=job["errores"],
            created_at=job.get("created_at"),
            completed_at=job.get("completed_at"),
            error=job.get("error")
        )
        
    except HTTPException:
        raise
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def run_generation_job(job_id: str, request_dict: dict, db_url: str):
    """
    Función que se ejecuta en background para generar simulacros.
    Incluye validación completa con todos los Quality Gates y repair loop.
    """
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from app.core.redis_config import JobTracker, JobLock
    
    print(f"\n{'='*60}")
    print(f"🚀 BACKGROUND JOB: {job_id}")
    print(f"{'='*60}")
    
    # Crear sesión de DB independiente (background task tiene su propio contexto)
    engine = create_engine(db_url)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    tracker = JobTracker()
    # Repair dinámico: el número de intentos se calcula según errores detectados
    
    try:
        areas = request_dict["areas"]
        institucion_id = request_dict["institucion_id"]
        sede_ids = request_dict.get("sede_ids") or []
        if not sede_ids:
            sede = db.query(Sede).filter(
                Sede.institucion_id == institucion_id,
                Sede.activo == True
            ).order_by(Sede.id).first()
            if sede:
                sede_ids = [sede.id]
        sedes_map = {s.id: s.nombre for s in db.query(Sede).filter(Sede.id.in_(sede_ids)).all()} if sede_ids else {}
        num_preguntas = request_dict.get("num_preguntas", 30)
        nombre_base = request_dict.get("nombre_base", "Simulacro")
        duracion_minutos = request_dict.get("duracion_minutos", 60)
        activar = request_dict.get("activar", False)
        dificultad = request_dict.get("dificultad")  # {facil: 30, medio: 40, dificil: 30}
        generation_model = request_dict.get("modelo_generacion") or os.getenv("DEFAULT_GENERATION_MODEL", "o3")

        # Resolver configuración institucional para validaciones externas
        wolfram_app_id = os.getenv("WOLFRAM_APP_ID")
        openai_api_key = os.getenv("OPENAI_API_KEY")

        requester_id = request_dict.get("requester_id")
        
        area_names = {
            "CIENCIAS_NATURALES": "Ciencias Naturales",
            "MATEMATICAS": "Matemáticas",
            "SOCIALES_CIUDADANAS": "Sociales y Ciudadanas",
            "LECTURA_CRITICA": "Lectura Crítica",
            "INGLES": "Inglés"
        }
        
        for area in areas:
            print(f"\n{'='*60}")
            print(f"🎯 Generando simulacro para: {area}")
            print(f"{'='*60}")
            
            tracker.update_progress(job_id, area, "generating")
            openai_timeout = _resolve_openai_timeout(num_preguntas)
            print(f"   ⏱️ Timeout OpenAI configurado: {openai_timeout}s (num_preguntas={num_preguntas})")
            
            job_lock = None
            contenido = None
            
            try:
                # Job Lock
                job_lock = JobLock(institucion_id=institucion_id, area=area)
                if not job_lock.acquire():
                    print(f"   🔒 BLOQUEADO: Ya hay una generación en curso para esta área")
                    tracker.update_progress(job_id, area, "error")
                    tracker.add_result(job_id, {
                        "area": area,
                        "status": "error",
                        "error": "Ya hay una generación en curso"
                    })
                    continue
                print(f"   🔓 Lock adquirido")
                
                # 1. Generar con IA
                print(f"   📝 Solicitando {num_preguntas} preguntas...")
                if dificultad:
                    print(f"   🎯 Dificultad: Fácil {dificultad.get('facil', 30)}% | Media {dificultad.get('medio', 40)}% | Difícil {dificultad.get('dificil', 30)}%")
                gen_result = SimulacroGenerator.generar(
                    area=area,
                    institucion_id=institucion_id,
                    db=db,
                    num_preguntas=num_preguntas,
                    dificultad=dificultad,
                    timeout=openai_timeout,
                    generation_model=generation_model
                )
                
                if not gen_result.success:
                    print(f"   ❌ Error en generación: {gen_result.error}")
                    tracker.update_progress(job_id, area, "error")
                    tracker.add_result(job_id, {
                        "area": area,
                        "status": "error",
                        "error": gen_result.error
                    })
                    continue
                
                contenido = gen_result.data
                num_preguntas_gen = len(contenido.get("preguntas", []))
                print(f"   ✅ Generación completada: {num_preguntas_gen} preguntas")
                print(f"   📊 Tokens usados: {gen_result.tokens_used}, Tiempo: {gen_result.generation_time:.1f}s")
                
                tracker.update_progress(job_id, area, "validating")
                
                # 2. VALIDACIÓN CON REPAIR LOOP DINÁMICO
                # MAX_REPAIRS = cantidad de preguntas con error (calculado dinámicamente)
                validation_passed = False
                repair_attempt = 0
                preguntas_ya_reparadas = set()  # Track de IDs ya reparados
                
                while not validation_passed:
                    if repair_attempt > 0:
                        print(f"\n   🔧 REPAIR LOOP - Intento {repair_attempt}")
                    else:
                        print(f"\n   🔍 Ejecutando Quality Gates...")
                    
                    gate_errors = []
                    errores_por_pregunta = {}

                    # Gate 0: Integridad de Contexto (SOLO para INGLES)
                    # Evita referencias cruzadas rotas del tipo "same as question X".
                    if area == "INGLES":
                        print(f"   📋 Gate 0 - Integridad de contexto (Inglés)...", end=" ")
                        try:
                            preguntas_norm, unresolved_ctx_ids = SimulacroGenerator._normalizar_contexto_ingles(
                                contenido.get("preguntas", [])
                            )
                            contenido["preguntas"] = preguntas_norm

                            # Chequeo adicional: no debe quedar ningun contexto referencial.
                            residual_ref_ids = []
                            for p in contenido.get("preguntas", []):
                                if SimulacroGenerator._es_contexto_referencial_ingles(p.get("contexto", "")):
                                    try:
                                        residual_ref_ids.append(int(p.get("id")))
                                    except (TypeError, ValueError):
                                        continue

                            all_bad_ctx_ids = sorted(set(unresolved_ctx_ids + residual_ref_ids))

                            if all_bad_ctx_ids:
                                print("❌ FAIL")
                                for pid in all_bad_ctx_ids:
                                    error_msg = (
                                        "Contexto no autonomo o referencial "
                                        "(ej. 'same as question X')."
                                    )
                                    print(f"      [ERROR] Gate 0 - Pregunta {pid}: {error_msg}")
                                    gate_errors.append(("gate0", error_msg, pid))
                                    if pid not in errores_por_pregunta:
                                        errores_por_pregunta[pid] = []
                                    errores_por_pregunta[pid].append(f"Gate 0: {error_msg}")
                            else:
                                print("✅ PASS")
                        except Exception as e:
                            print(f"⚠️ ERROR INTERNO ({str(e)})")

                    # Gate 1: Validación estructural
                    normalization_report = normalize_graph_types_in_questions(contenido.get("preguntas", []))
                    if normalization_report.get("normalized_count", 0) > 0:
                        print(
                            f"   🧩 Normalización gráfica: "
                            f"{normalization_report['normalized_count']} tipo(s) ajustado(s) por alias."
                        )

                    print(f"   📋 Gate 1 - Validación estructural...", end=" ")
                    try:
                        SimulacroV2(**contenido)
                        print("✅ PASS")
                    except ValidationError as e:
                        print("❌ FAIL")
                        for err in e.errors()[:5]:
                            loc = " -> ".join(str(x) for x in err['loc'])
                            error_msg = f"Gate 1: {loc} - {err['msg']}"
                            print(f"      [ERROR] {error_msg}")
                            gate_errors.append(("gate1", error_msg, None))
                    
                    # Gate 2: Reglas de negocio
                    print(f"   📋 Gate 2 - Reglas de negocio...", end=" ")
                    qa_result = Gate2Validator.validar_simulacro(contenido)
                    if not qa_result.passed:
                        print("❌ FAIL")
                        for error in qa_result.errors[:3]:
                            print(f"      [ERROR] Gate 2: {error}")
                            gate_errors.append(("gate2", error, None))
                    else:
                        print("✅ PASS")

                    # Gate 2.5: Distribución de Dificultad
                    print(f"   📋 Gate 2.5 - Distribución de Dificultad...", end=" ")
                    gate25_result = Gate25Validator.validar(contenido, dificultad)
                    if not gate25_result.passed:
                        print("❌ FAIL")
                        for error in gate25_result.errors:
                            print(f"      [ERROR] Gate 2.5: {error}")
                            gate_errors.append(("gate25", error, None))
                            # Como es un error global, no se puede atribuir a una pregunta específica fácilmente
                            # Pero podríamos agregarlo como una instrucción general de reparación
                            if "gate25" not in errores_por_pregunta: # Usamos un key especial
                                errores_por_pregunta["global"] = []
                            errores_por_pregunta["global"].append(error)
                    else:
                        print("✅ PASS")
                        for w in gate25_result.warnings:
                            print(f"      [WARN] {w}")
                    
                    # Gate 3: Deduplicación
                    print(f"   📋 Gate 3 - Deduplicación...", end=" ")
                    dedup_result = Gate3Deduplicator.verificar_duplicados(
                        preguntas_nuevas=contenido.get("preguntas", []),
                        institucion_id=institucion_id,
                        area=area,
                        db=db
                    )
                    if not dedup_result.passed:
                        print("❌ FAIL")
                        for dup in dedup_result.duplicados[:3]:
                            error_msg = (
                                f"Pregunta duplicada: {dup.pregunta_id} "
                                f"(nivel={dup.nivel}, score={dup.score})"
                            )
                            print(f"      [ERROR] Gate 3: {error_msg}")
                            gate_errors.append(("gate3", error_msg, dup.pregunta_id))
                    else:
                        print("✅ PASS")
                    
                    # Gate 4: Validación visual
                    print(f"   📋 Gate 4 - Validación visual...", end=" ")
                    render_result = Gate4RenderValidator.validar_graficos(contenido.get("preguntas", []))
                    if not render_result.passed:
                        print("❌ FAIL")
                        for issue in [i for i in render_result.issues if i.nivel == 'error'][:3]:
                            error_msg = f"{issue.tipo_grafico}: {issue.mensaje}"
                            print(f"      [ERROR] Gate 4 - Pregunta {issue.pregunta_id}: {error_msg}")
                            gate_errors.append(("gate4", error_msg, issue.pregunta_id))
                            if issue.pregunta_id not in errores_por_pregunta:
                                errores_por_pregunta[issue.pregunta_id] = []
                            errores_por_pregunta[issue.pregunta_id].append(f"Gate 4: {error_msg}")
                    else:
                        print("✅ PASS")
                    
                    # Gate 5: Validación semántica (IA)
                    print(f"   📋 Gate 5 - Validación semántica (IA)...", end=" ")
                    semantic_result = Gate5SemanticValidator.validar_semantica(
                        preguntas=contenido.get("preguntas", []),
                        area=area
                    )
                    if not semantic_result.passed:
                        print("❌ FAIL")
                        for issue in [i for i in semantic_result.issues if i.nivel == 'error']:
                            error_msg = f"{issue.tipo}: {issue.mensaje}"
                            print(f"      [ERROR] Gate 5 - Pregunta {issue.pregunta_id}: {error_msg}")
                            gate_errors.append(("gate5", error_msg, issue.pregunta_id))
                            if issue.pregunta_id not in errores_por_pregunta:
                                errores_por_pregunta[issue.pregunta_id] = []
                            errores_por_pregunta[issue.pregunta_id].append(f"Gate 5: {error_msg}")
                    else:
                        print("✅ PASS")
                    
                    # Gate 5B: Validación contexto-pregunta (SOLO para LECTURA_CRITICA)
                    if area == "LECTURA_CRITICA":
                        print(f"   📋 Gate 5B - Coherencia contexto-pregunta (Embeddings)...", end=" ")
                        context_result = Gate5BContextValidator.validar_contexto(
                            preguntas=contenido.get("preguntas", [])
                        )
                        if not context_result.passed:
                            print("❌ FAIL")
                            for issue in [i for i in context_result.issues if i.nivel == 'error']:
                                error_msg = f"{issue.tipo}: {issue.mensaje} (sim: {issue.similitud:.2f})"
                                print(f"      [ERROR] Gate 5B - Pregunta {issue.pregunta_id}: {error_msg}")
                                gate_errors.append(("gate5b", error_msg, issue.pregunta_id))
                                if issue.pregunta_id not in errores_por_pregunta:
                                    errores_por_pregunta[issue.pregunta_id] = []
                                errores_por_pregunta[issue.pregunta_id].append(f"Gate 5B: {error_msg}")
                        else:
                            print("✅ PASS")
                    
                    # Gate 6: Validación lógica
                    print(f"   📋 Gate 6 - Validación lógica...", end=" ")
                    logic_result = Gate6LogicValidator.validar_logica(contenido.get("preguntas", []))
                    if not logic_result.passed:
                        print("❌ FAIL")
                        for issue in [i for i in logic_result.issues if i.nivel == 'error'][:3]:
                            error_msg = f"{issue.tipo}: {issue.mensaje}"
                            print(f"      [ERROR] Gate 6 - Pregunta {issue.pregunta_id}: {error_msg}")
                            gate_errors.append(("gate6", error_msg, issue.pregunta_id))
                            if issue.pregunta_id not in errores_por_pregunta:
                                errores_por_pregunta[issue.pregunta_id] = []
                            errores_por_pregunta[issue.pregunta_id].append(f"Gate 6: {error_msg}")
                    else:
                        print("✅ PASS")
                    
                    # Gate 7: Validación matemática (SOLO para área MATEMATICAS)
                    if area == "MATEMATICAS":
                        print(f"   📋 Gate 7 - Validación matemática (Wolfram Alpha)...", end=" ")
                        math_result = Gate7MathValidator.validar_matematicas(
                            preguntas=contenido.get("preguntas", []),
                            wolfram_app_id=wolfram_app_id,
                            openai_api_key=openai_api_key,
                        )
                        if not math_result.passed:
                            print("❌ FAIL")
                            for issue in [i for i in math_result.issues if i.nivel == 'error'][:3]:
                                error_msg = f"{issue.tipo}: {issue.mensaje}"
                                if issue.esperado and issue.obtenido:
                                    error_msg += f" (esperado: {issue.esperado}, obtenido: {issue.obtenido})"
                                print(f"      [ERROR] Gate 7 - Pregunta {issue.pregunta_id}: {error_msg}")
                                gate_errors.append(("gate7", error_msg, issue.pregunta_id))
                                if issue.pregunta_id not in errores_por_pregunta:
                                    errores_por_pregunta[issue.pregunta_id] = []
                                errores_por_pregunta[issue.pregunta_id].append(f"Gate 7: {error_msg}")
                        else:
                            print("✅ PASS")
                    
                    
                    # Gate 8: Validación Biológica (RAG) - SOLO para CIENCIAS_NATURALES
                    if area == "CIENCIAS_NATURALES":
                        print(f"   📋 Gate 8 - Validación Biológica Avanzada (Gate E)...", end=" ")
                        try:
                            from app.services.qa_gate_biology_service import GateBiologyValidator
                            bio_result = GateBiologyValidator.validar_biologia(
                                preguntas=contenido.get("preguntas", []),
                                area=area
                            )
                            if not bio_result.passed:
                                print("❌ FAIL")
                                for issue in bio_result.issues:
                                    error_msg = f"Gate 8 (Bio): {issue.mensaje}"
                                    print(f"      [ERROR] - Pregunta {issue.pregunta_id}: {error_msg}")
                                    gate_errors.append(("gate8", error_msg, issue.pregunta_id))
                                    if issue.pregunta_id not in errores_por_pregunta:
                                        errores_por_pregunta[issue.pregunta_id] = []
                                    errores_por_pregunta[issue.pregunta_id].append(error_msg)
                            else:
                                status_msg = "✅ PASS"
                                if bio_result.stats.get("status", "").startswith("skipped"):
                                    status_msg = f"⚠️ SKIPPED ({bio_result.stats.get('status')})"
                                print(status_msg)
                        except Exception as e:
                            print(f"⚠️ Gate 8 Error Interno: {str(e)}")

                    # Gate 9: Validación de Nivel Inglés (Analítico) - SOLO para INGLES
                    if area == "INGLES":
                        print(f"   📋 Gate 9 - Validación Nivel CEFR (Analítico)...", end=" ")
                        try:
                            from app.services.qa_gate_english_analytic_service import GateEnglishAnalyticValidator
                            cefr_result = GateEnglishAnalyticValidator.validar_nivel_analitico(contenido.get("preguntas", []))
                            
                            if not cefr_result.passed:
                                print("❌ FAIL")
                                for issue in cefr_result.issues:
                                    error_msg = f"Gate 9 (CEFR): {issue.mensaje}"
                                    print(f"      [ERROR] - Pregunta {issue.pregunta_id}: {error_msg}")
                                    gate_errors.append(("gate9", error_msg, issue.pregunta_id))
                                    if issue.pregunta_id not in errores_por_pregunta:
                                        errores_por_pregunta[issue.pregunta_id] = []
                                    errores_por_pregunta[issue.pregunta_id].append(error_msg + f". Palabras difíciles: {issue.palabras_dificiles}")
                            else:
                                print("✅ PASS")
                        except Exception as e:
                             import traceback
                             traceback.print_exc()
                             print(f"⚠️ Gate 9 Error Interno: {str(e)}")





                    if area == "CIENCIAS_NATURALES":
                        print(f"   📋 Gate 7 - Validación científica (Wolfram Alpha)...", end=" ")
                        science_result = Gate7MathValidator.validar_ciencias(
                            preguntas=contenido.get("preguntas", []),
                            wolfram_app_id=wolfram_app_id,
                            openai_api_key=openai_api_key,
                        )
                        if not science_result.passed:
                            print("❌ FAIL")
                            for issue in [i for i in science_result.issues if i.nivel == 'error'][:3]:
                                error_msg = f"{issue.tipo}: {issue.mensaje}"
                                if issue.esperado and issue.obtenido:
                                    error_msg += f" (esperado: {issue.esperado}, obtenido: {issue.obtenido})"
                                print(f"      [ERROR] Gate 7 - Pregunta {issue.pregunta_id}: {error_msg}")
                                gate_errors.append(("gate7", error_msg, issue.pregunta_id))
                                if issue.pregunta_id not in errores_por_pregunta:
                                    errores_por_pregunta[issue.pregunta_id] = []
                                errores_por_pregunta[issue.pregunta_id].append(f"Gate 7: {error_msg}")
                        else:
                            print("✅ PASS")
                    
                    
                    # Gate 10: Validación Constitucional (SOLO para SOCIALES_CIUDADANAS)
                    if area.strip() == "SOCIALES_CIUDADANAS":
                        print(f"   📋 Gate 10 - Validación Constitucional (Juez RAG)...", end=" ")
                        const_result = GateSocialesValidator.validar_constitucionalidad(
                            preguntas=contenido.get("preguntas", []),
                            area=area
                        )
                        if not const_result.passed:
                            print("❌ FAIL")
                            for issue in [i for i in const_result.issues if i.nivel == 'error']:
                                error_msg = f"INCONSTITUCIONAL: {issue.mensaje} ({issue.articulo_vulnerado})"
                                print(f"      [ERROR] Gate 10 - Pregunta {issue.pregunta_id}: {error_msg}")
                                
                                gate_errors.append(("gate10", error_msg, issue.pregunta_id))
                                if issue.pregunta_id not in errores_por_pregunta:
                                    errores_por_pregunta[issue.pregunta_id] = []
                                errores_por_pregunta[issue.pregunta_id].append(error_msg)
                        else:
                            print("✅ PASS")

                    # Determinar si pasó
                    if not gate_errors:
                        validation_passed = True
                        print(f"\n   ✅ Todos los Quality Gates pasaron!")
                    else:
                        # Verificar si hay errores en preguntas que NO hemos reparado aún
                        preguntas_con_errores = set(errores_por_pregunta.keys())
                        preguntas_nuevas_con_error = preguntas_con_errores - preguntas_ya_reparadas
                        
                        # Caso 1b: ESTRATEGIA DE BLINDAJE (Smart Trimming)
                        # Si tenemos buffer (preguntas extra) y las validas son suficientes, DESCARTAR las malas.
                        all_questions = contenido.get("preguntas", [])
                        valid_questions = [p for p in all_questions if p.get("id") not in errores_por_pregunta]
                        
                        # --- BLACK BOX RECORDER: Log Rejected Questions ---
                        try:
                            import uuid
                            import json
                            
                            log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "logs", "rejected")
                            os.makedirs(log_dir, exist_ok=True)
                            
                            failed_questions = [p for p in all_questions if p.get("id") in errores_por_pregunta]
                            
                            if failed_questions:
                                print(f"      📼 Grabando {len(failed_questions)} preguntas fallidas en Black Box...")
                                
                                for p in failed_questions:
                                    p_id = p.get("id")
                                    errors = errores_por_pregunta.get(p_id, [])
                                    
                                    log_entry = {
                                        "timestamp": datetime.now().isoformat(),
                                        "job_id": job_id,
                                        "area": area,
                                        "pregunta_id": p_id,
                                        "errores": errors,
                                        "contenido_pregunta": p
                                    }
                                    
                                    filename = f"{area}_{datetime.now().strftime('%Y%m%d')}_{uuid.uuid4().hex[:6]}.txt"
                                    filepath = os.path.join(log_dir, filename)
                                    
                                    with open(filepath, "w", encoding="utf-8") as f:
                                        f.write(f"[REJECTED QUESTION REPORT]\n")
                                        f.write(f"DATE: {log_entry['timestamp']}\n")
                                        f.write(f"AREA: {area}\n")
                                        f.write(f"ERRORS:\n")
                                        for e in errors:
                                            f.write(f" - {e}\n")
                                        f.write(f"\nJSON DUMP:\n")
                                        f.write(json.dumps(p, indent=2, ensure_ascii=False))
                        except Exception as e:
                            print(f"      ⚠️ Error escribiendo logs: {e}")
                        # --------------------------------------------------

                        if len(valid_questions) >= num_preguntas:
                            print(f"\n   🛡️ ESTRATEGIA BLINDAJE ACTIVADA:")
                            print(f"      Descartando {len(errores_por_pregunta)} preguntas defectuosas.")
                            print(f"      Nos quedan {len(valid_questions)} preguntas válidas (solicitadas: {num_preguntas}).")
                            
                            # Recortar a las N solicitadas
                            if area == "INGLES":
                                final_selection = _seleccionar_blindaje_equilibrado_ingles(
                                    preguntas_validas=valid_questions,
                                    num_preguntas=num_preguntas,
                                    dificultad=dificultad
                                )
                                dist_partes = _count_english_parts(final_selection)
                                print(
                                    "      🇬🇧 Blindaje equilibrado por partes: "
                                    + ", ".join([f"P{k}={v}" for k, v in dist_partes.items()])
                                )
                            elif area == "MATEMATICAS":
                                final_selection = _seleccionar_blindaje_equilibrado_matematicas(
                                    preguntas_validas=valid_questions,
                                    num_preguntas=num_preguntas,
                                    dificultad=dificultad
                                )
                                dist_math = _count_math_distribution(final_selection)
                                comp_summary = ", ".join([
                                    f"{c.split()[0]}={sum(d.values())}"
                                    for c, d in dist_math.items()
                                ])
                                dif_summary = ", ".join([
                                    f"{d}={sum(dist_math[c][d] for c in dist_math)}"
                                    for d in _MATH_DIFICULTADES
                                ])
                                print(f"      🧮 Blindaje equilibrado Matemáticas:")
                                print(f"         Competencias: {comp_summary}")
                                print(f"         Dificultad: {dif_summary}")
                            elif area == "CIENCIAS_NATURALES":
                                final_selection = _seleccionar_blindaje_equilibrado_ciencias(
                                    preguntas_validas=valid_questions,
                                    num_preguntas=num_preguntas,
                                    dificultad=dificultad
                                )
                                dist_cn = _count_cn_distribution(final_selection)
                                comp_summary = ", ".join([
                                    f"{c}={sum(d.values())}"
                                    for c, d in dist_cn.items()
                                ])
                                dif_summary = ", ".join([
                                    f"{d}={sum(dist_cn[c][d] for c in dist_cn)}"
                                    for d in _CN_DIFICULTADES
                                ])
                                print(f"      🧬 Blindaje equilibrado Ciencias:")
                                print(f"         Componentes: {comp_summary}")
                                print(f"         Dificultad: {dif_summary}")
                            elif area == "SOCIALES_CIUDADANAS":
                                final_selection = _seleccionar_blindaje_equilibrado_sociales(
                                    preguntas_validas=valid_questions,
                                    num_preguntas=num_preguntas,
                                    dificultad=dificultad
                                )
                                dist_soc = _count_sociales_distribution(final_selection)
                                comp_summary = ", ".join([
                                    f"{c}={sum(d.values())}"
                                    for c, d in dist_soc.items()
                                ])
                                dif_summary = ", ".join([
                                    f"{d}={sum(dist_soc[c][d] for c in dist_soc)}"
                                    for d in _SOCIALES_DIFICULTADES
                                ])
                                print(f"      ⚖️ Blindaje equilibrado Sociales:")
                                print(f"         Competencias: {comp_summary}")
                                print(f"         Dificultad: {dif_summary}")
                            elif area == "LECTURA_CRITICA":
                                final_selection = _seleccionar_blindaje_equilibrado_lectura(
                                    preguntas_validas=valid_questions,
                                    num_preguntas=num_preguntas,
                                    dificultad=dificultad
                                )
                                dist_lc = _count_lectura_distribution(final_selection)
                                comp_map = {
                                    "Identificar y entender contenidos locales": "Literal",
                                    "Comprender cómo se articulan las partes": "Inferencial",
                                    "Reflexionar y evaluar un texto": "Critico",
                                }
                                comp_summary = ", ".join([
                                    f"{comp_map.get(c, c)}={sum(d.values())}"
                                    for c, d in dist_lc.items()
                                ])
                                dif_summary = ", ".join([
                                    f"{d}={sum(dist_lc[c][d] for c in dist_lc)}"
                                    for d in _LECTURA_DIFICULTADES
                                ])
                                print(f"      📚 Blindaje equilibrado Lectura:")
                                print(f"         Afirmaciones: {comp_summary}")
                                print(f"         Dificultad: {dif_summary}")
                            else:
                                final_selection = valid_questions[:num_preguntas]
                            contenido["preguntas"] = final_selection
                            
                            print(f"      ✅ Simulacro salvado exitosamente con {len(final_selection)} preguntas perfectas.")
                            validation_passed = True
                            break

                        # Caso 1: Las mismas preguntas que ya reparamos siguen fallando (y NO tenemos suficientes validas)
                        if not preguntas_nuevas_con_error and preguntas_ya_reparadas:
                            preguntas_reincidentes = preguntas_con_errores & preguntas_ya_reparadas
                            if preguntas_reincidentes:
                                print(f"\n   ❌ Las preguntas {preguntas_reincidentes} siguen fallando y no hay suficientes de repuesto.")
                                print(f"      Abortando proceso.")
                                break
                        
                        # Caso 2: No hay preguntas específicas (errores estructurales)
                        if not errores_por_pregunta:
                            print(f"\n   ❌ Errores estructurales sin pregunta específica. Abortando.")
                            break
                        
                        repair_attempt += 1
                        total_a_reparar = len(errores_por_pregunta)
                        
                        print(f"\n   🔧 Reparando {total_a_reparar} pregunta(s)... (Intento {repair_attempt})")
                        print(f"      📊 Ya reparadas anteriormente: {len(preguntas_ya_reparadas)}")
                        print(f"      📊 Nuevas con error: {len(preguntas_nuevas_con_error)}")
                        
                        preguntas_todas = contenido.get("preguntas", [])
                        preguntas_a_reparar = []
                        errores_lista = []
                        
                        for preg_id, errs in errores_por_pregunta.items():
                            for p in preguntas_todas:
                                if p.get("id") == preg_id:
                                    preguntas_a_reparar.append(p)
                                    errores_lista.append(" | ".join(errs))
                                    print(f"      📝 Pregunta {preg_id}: {' | '.join(errs)}")
                                    preguntas_ya_reparadas.add(preg_id)  # Marcar como reparada
                                    break
                        
                        if preguntas_a_reparar:
                            print(f"      🤖 Llamando a OpenAI para reparación...")
                            repair_result = SimulacroGenerator.reparar_preguntas(
                                preguntas_problematicas=preguntas_a_reparar,
                                errores=errores_lista,
                                area=area,
                                timeout=openai_timeout,
                                generation_model=generation_model
                            )
                            
                            if repair_result.success and repair_result.data:
                                # Fix: Buscar ambas claves posibles y asegurar que es lista
                                raw_preguntas = repair_result.data.get("preguntas_reparadas") or repair_result.data.get("preguntas") or []
                                if not isinstance(raw_preguntas, list): raw_preguntas = []

                                preguntas_reparadas_validas = []
                                
                                # 🔍 VALIDACIÓN PRE-INSERCIÓN (SANITIZATION)
                                print(f"      🛡️ Validando estructura de {len(raw_preguntas)} preguntas reparadas...")
                                
                                # Importar modelo de pregunta individual para validación granular
                                from app.schemas.simulacro_v2 import Pregunta as PreguntaSchema
                                
                                for p_rep in raw_preguntas:
                                    try:
                                        # Validar contra esquema Pydantic estricto
                                        PreguntaSchema(**p_rep)
                                        preguntas_reparadas_validas.append(p_rep)
                                    except ValidationError as e:
                                        p_id = p_rep.get('id', '?')
                                        print(f"      ⚠️ Pregunta reparada {p_id} DESCARTADA por error estructural: {e.errors()[0]['msg']}")
                                        # No la agregamos a validas, se mantiene la original (con error) para reintento o descarte final

                                print(f"      ✅ {len(preguntas_reparadas_validas)} preguntas reparadas pasaron sanitización ({repair_result.generation_time:.1f}s)")
                                
                                preguntas_actualizadas = list(preguntas_todas)
                                reemplazadas_count = 0
                                
                                for preg_reparada in preguntas_reparadas_validas:
                                    preg_id = preg_reparada.get("id")
                                    # Buscar y reemplazar en la lista original
                                    for i, p in enumerate(preguntas_actualizadas):
                                        if p.get("id") == preg_id:
                                            preguntas_actualizadas[i] = preg_reparada
                                            reemplazadas_count += 1
                                            # print(f"      🔄 Pregunta {preg_id} reemplazada")
                                            break
                                
                                print(f"      🔄 Se actualizaron {reemplazadas_count} preguntas en el simulacro.")
                                contenido["preguntas"] = preguntas_actualizadas
                            else:
                                print(f"      ❌ Error en reparación: {repair_result.error}")
                                break
                        else:
                            print(f"      ⚠️ No hay preguntas específicas para reparar")
                            break
                
                # 3. Evaluar resultado final
                if not validation_passed:
                    # Último intento de salvamento: Si se acabaron los intentos pero tenemos >80% de preguntas buenas
                    valid_percent = len([p for p in contenido.get("preguntas", []) if p.get("id") not in errores_por_pregunta]) / num_preguntas
                    if valid_percent >= 0.8:
                         print(f"\n   ⚠️ Máximo de intentos alcanzado, pero salvando simulacro parcial ({valid_percent*100:.0f}% OK).")
                         contenido["preguntas"] = [p for p in contenido.get("preguntas", []) if p.get("id") not in errores_por_pregunta]
                    else:
                        print(f"\n   ❌ Máximo de intentos alcanzado. Área {area} fallida.")
                        tracker.update_progress(job_id, area, "error")
                        tracker.add_result(job_id, {
                            "area": area,
                            "status": "error",
                            "error": f"Falló después de {repair_attempt} intentos de reparación"
                        })
                        continue
                
                # 3.b RECORTAR EXCEDENTE CON DISTRIBUCIÓN INTELIGENTE
                final_questions = contenido.get("preguntas", [])
                if len(final_questions) > num_preguntas:
                    if area == "INGLES":
                        print(f"\n   ✂️ Recortando excedente ({len(final_questions)} -> {num_preguntas}) con equilibrio por partes (INGLÉS)...")
                        seleccionadas = _seleccionar_blindaje_equilibrado_ingles(
                            preguntas_validas=final_questions,
                            num_preguntas=num_preguntas,
                            dificultad=dificultad
                        )
                        dist_partes = _count_english_parts(seleccionadas)
                        print(
                            "      🇬🇧 Distribución final por partes: "
                            + ", ".join([f"P{k}={v}" for k, v in dist_partes.items()])
                        )
                        contenido["preguntas"] = seleccionadas
                    elif area == "MATEMATICAS":
                        print(f"\n   ✂️ Recortando excedente ({len(final_questions)} -> {num_preguntas}) con equilibrio por competencia+dificultad (MATEMÁTICAS)...")
                        seleccionadas = _seleccionar_blindaje_equilibrado_matematicas(
                            preguntas_validas=final_questions,
                            num_preguntas=num_preguntas,
                            dificultad=dificultad
                        )
                        dist_math = _count_math_distribution(seleccionadas)
                        comp_summary = ", ".join([
                            f"{c.split()[0]}={sum(d.values())}"
                            for c, d in dist_math.items()
                        ])
                        dif_summary = ", ".join([
                            f"{d}={sum(dist_math[c][d] for c in dist_math)}"
                            for d in _MATH_DIFICULTADES
                        ])
                        comp_dist = _count_math_component_distribution(seleccionadas)
                        comp_limits = _math_component_limits(num_preguntas)
                        comp_range_summary = ", ".join([
                            f"{c}={comp_dist[c]} (min={comp_limits[c]['min']}, max={comp_limits[c]['max']})"
                            for c in _MATH_COMPONENTES
                        ])
                        visual_total = sum(1 for p in seleccionadas if _has_math_visual(p))
                        visual_target = round(num_preguntas * 0.60)
                        print(f"      🧮 Distribución final Matemáticas:")
                        print(f"         Competencias: {comp_summary}")
                        print(f"         Dificultad: {dif_summary}")
                        print(f"         Componentes: {comp_range_summary}")
                        print(f"         Visual: {visual_total}/{num_preguntas} (objetivo={visual_target})")
                        contenido["preguntas"] = seleccionadas
                    elif area == "CIENCIAS_NATURALES":
                        print(f"\n   ✂️ Recortando excedente ({len(final_questions)} -> {num_preguntas}) con equilibrio por componente+dificultad (CIENCIAS)...")
                        seleccionadas = _seleccionar_blindaje_equilibrado_ciencias(
                            preguntas_validas=final_questions,
                            num_preguntas=num_preguntas,
                            dificultad=dificultad
                        )
                        dist_cn = _count_cn_distribution(seleccionadas)
                        comp_summary = ", ".join([
                            f"{c}={sum(d.values())}"
                            for c, d in dist_cn.items()
                        ])
                        dif_summary = ", ".join([
                            f"{d}={sum(dist_cn[c][d] for c in dist_cn)}"
                            for d in _CN_DIFICULTADES
                        ])
                        print(f"      🧬 Distribución final Ciencias:")
                        print(f"         Componentes: {comp_summary}")
                        print(f"         Dificultad: {dif_summary}")
                        contenido["preguntas"] = seleccionadas
                    elif area == "SOCIALES_CIUDADANAS":
                        print(f"\n   ✂️ Recortando excedente ({len(final_questions)} -> {num_preguntas}) con equilibrio por competencia+dificultad (SOCIALES)...")
                        seleccionadas = _seleccionar_blindaje_equilibrado_sociales(
                            preguntas_validas=final_questions,
                            num_preguntas=num_preguntas,
                            dificultad=dificultad
                        )
                        dist_soc = _count_sociales_distribution(seleccionadas)
                        comp_summary = ", ".join([
                            f"{c}={sum(d.values())}"
                            for c, d in dist_soc.items()
                        ])
                        dif_summary = ", ".join([
                            f"{d}={sum(dist_soc[c][d] for c in dist_soc)}"
                            for d in _SOCIALES_DIFICULTADES
                        ])
                        print(f"      ⚖️ Distribución final Sociales:")
                        print(f"         Competencias: {comp_summary}")
                        print(f"         Dificultad: {dif_summary}")
                        contenido["preguntas"] = seleccionadas
                    elif area == "LECTURA_CRITICA":
                        print(f"\n   ✂️ Recortando excedente ({len(final_questions)} -> {num_preguntas}) con equilibrio por afirmacion+dificultad (LECTURA)...")
                        seleccionadas = _seleccionar_blindaje_equilibrado_lectura(
                            preguntas_validas=final_questions,
                            num_preguntas=num_preguntas,
                            dificultad=dificultad
                        )
                        dist_lc = _count_lectura_distribution(seleccionadas)
                        comp_map = {
                            "Identificar y entender contenidos locales": "Literal",
                            "Comprender cómo se articulan las partes": "Inferencial",
                            "Reflexionar y evaluar un texto": "Critico",
                        }
                        comp_summary = ", ".join([
                            f"{comp_map.get(c, c)}={sum(d.values())}"
                            for c, d in dist_lc.items()
                        ])
                        dif_summary = ", ".join([
                            f"{d}={sum(dist_lc[c][d] for c in dist_lc)}"
                            for d in _LECTURA_DIFICULTADES
                        ])
                        print(f"      📚 Distribución final Lectura:")
                        print(f"         Afirmaciones: {comp_summary}")
                        print(f"         Dificultad: {dif_summary}")
                        contenido["preguntas"] = seleccionadas
                    else:
                        print(f"\n   ✂️ Recortando excedente ({len(final_questions)} -> {num_preguntas}) respetando dificultad...")
                        
                        # 1. Calcular cuotas objetivo
                        dificultad_req = dificultad or {"facil": 30, "medio": 40, "dificil": 30}
                        target_facil = round(num_preguntas * dificultad_req.get("facil", 30) / 100)
                        target_medio = round(num_preguntas * dificultad_req.get("medio", 40) / 100)
                        target_dificil = num_preguntas - target_facil - target_medio
                        
                        # 2. Clasificar disponibles
                        pool_facil = [p for p in final_questions if p.get("dificultad") == "facil"]
                        pool_medio = [p for p in final_questions if p.get("dificultad") == "medio"]
                        pool_dificil = [p for p in final_questions if p.get("dificultad") == "dificil"]
                        pool_otros = [p for p in final_questions if p.get("dificultad") not in ["facil", "medio", "dificil"]]
                        
                        seleccionadas = []
                        
                        # 3. Llenar cuotas
                        tomadas_facil = pool_facil[:target_facil]
                        tomadas_medio = pool_medio[:target_medio]
                        tomadas_dificil = pool_dificil[:target_dificil]
                        
                        seleccionadas.extend(tomadas_facil)
                        seleccionadas.extend(tomadas_medio)
                        seleccionadas.extend(tomadas_dificil)
                        
                        # 4. Rellenar si falta
                        sobrantes = (pool_facil[target_facil:] + 
                                   pool_medio[target_medio:] + 
                                   pool_dificil[target_dificil:] + 
                                   pool_otros)
                        
                        faltantes = num_preguntas - len(seleccionadas)
                        if faltantes > 0:
                            print(f"      ⚠️ Faltaron preguntas para cubrir cuotas exactas. Rellenando con {faltantes} de otros niveles.")
                            seleccionadas.extend(sobrantes[:faltantes])
                        
                        # Ordenar por ID para mantener orden lógico
                        seleccionadas.sort(key=lambda x: x.get("id"))
                        contenido["preguntas"] = seleccionadas

                # 3.c Reindexado final (sin huecos) para alinear posición OMR (1..N) con IDs.
                _renumerar_preguntas_consecutivas(contenido)

                # 3.c ENRIQUECIMIENTO VISUAL (Claude Opus)
                print(f"   🎨 Enriquecimiento Visual (Claude Opus)...")
                VisualEnrichmentService.enrich_simulacro_questions(
                    contenido.get("preguntas", []),
                    area=area
                )
                
                # 3.d LIMPIEZA DE CAMPOS INTERNOS (Razonamiento CoT)
                print(f"   🧹 Limpiando razonamientos internos antes de guardar...")
                keys_to_remove_root = [k for k in contenido.keys() if k.startswith("_")]
                for k in keys_to_remove_root: contenido.pop(k)
                
                cleaned_count = 0
                for p in contenido.get("preguntas", []):
                     p_keys = [k for k in p.keys() if k.startswith("_")]
                     for k in p_keys: 
                        p.pop(k)
                        cleaned_count += 1
                if cleaned_count > 0:
                    print(f"      - Se eliminaron {cleaned_count} campos de razonamiento oculto.")

                print(f"\n   💾 Guardando simulacro(s) en base de datos...")
                if not isinstance(contenido.get("meta"), dict):
                    contenido["meta"] = {}
                contenido["meta"]["modelo_generacion"] = generation_model
                
                # 4. Crear un simulacro por cada sede seleccionada
                sedes_creadas = []
                for sede_id in sede_ids:
                    try:
                        sede_nombre = sedes_map.get(sede_id, "")
                        titulo_simulacro = f"{nombre_base} - {area_names.get(area, area)}"
                        if sede_nombre:
                            titulo_simulacro += f" - {sede_nombre}"
                        
                        db_simulacro = Simulacro(
                            titulo=titulo_simulacro,
                            descripcion=f"Simulacro generado automáticamente para {area_names.get(area, area)}",
                            area=area,
                            institucion_id=institucion_id,
                            sede_id=sede_id,
                            contenido=contenido,
                            total_preguntas=len(contenido.get("preguntas", [])),
                            duracion_minutos=duracion_minutos,
                            estado="activo",
                            activo=activar,
                            created_by=requester_id  # Usuario que solicitó la generación
                        )
                        db.add(db_simulacro)
                        db.commit()
                        db.refresh(db_simulacro)
                        
                        # 5. Registrar preguntas usadas (incluye embeddings semánticos, fail-open en API de embeddings)
                        registrar_preguntas_usadas(
                            db=db,
                            preguntas=contenido.get("preguntas", []),
                            institucion_id=institucion_id,
                            area=area,
                            version_simulacro=db_simulacro.version,
                            simulacro_id=db_simulacro.id,
                            commit=True,
                        )
                        
                        sedes_creadas.append(db_simulacro.id)
                        tracker.add_result(job_id, {
                            "area": area,
                            "sede_id": sede_id,
                            "status": "completed",
                            "simulacro_id": db_simulacro.id
                        })
                        print(f"✅ Simulacro creado: ID={db_simulacro.id}, Sede={sede_nombre}, Título='{titulo_simulacro}'")
                    except Exception as sede_e:
                        db.rollback()
                        import traceback
                        traceback.print_exc()
                        tracker.add_result(job_id, {
                            "area": area,
                            "sede_id": sede_id,
                            "status": "error",
                            "error": str(sede_e)
                        })
                        print(f"   ❌ Error guardando simulacro para sede {sede_id}: {sede_e}")
                
                if sedes_creadas:
                    tracker.update_progress(job_id, area, "completed")
                    repair_msg = f" (con {repair_attempt} repair{'s' if repair_attempt > 1 else ''})" if repair_attempt > 0 else ""
                    print(f"✅ Área {area} completada: {len(sedes_creadas)} simulacro(s) creado(s){repair_msg}")
                else:
                    tracker.update_progress(job_id, area, "error")
                    tracker.add_result(job_id, {
                        "area": area,
                        "status": "error",
                        "error": "No se pudo crear ningún simulacro para las sedes seleccionadas"
                    })
                
            except Exception as e:
                db.rollback()  # 🛡️ ROLLBACK DE EMERGENCIA: Limpiar sesión para no afectar sig. áreas
                import traceback
                traceback.print_exc()
                tracker.update_progress(job_id, area, "error")
                tracker.add_result(job_id, {
                    "area": area,
                    "status": "error",
                    "error": str(e)
                })
            finally:
                if job_lock:
                    released = job_lock.release()
                    if released:
                        print(f"   🔓 Lock liberado para {area}")
                    else:
                        print(f"   ⚠️ Lock no liberado (sin ownership o expirado) para {area}")
        
        # Marcar job como completado
        tracker.complete_job(job_id)
        print(f"\n✅ JOB {job_id} COMPLETADO")
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        tracker.fail_job(job_id, str(e))
        print(f"\n❌ JOB {job_id} FALLIDO: {e}")
    finally:
        db.close()

@router.post("/generate", deprecated=True)
def generate_simulacros_deprecated():
    """
    DEPRECATED: Use /generate-async instead.
    Este endpoint sincrono ha sido eliminado por no soportar el flujo completo de Quality Gates y Repair.
    """
    raise HTTPException(
        status_code=410, 
        detail="Este endpoint está obsoleto. Por favor use /api/simulacros/generate-async para generación robusta con IA."
    )
