"""
Gate 3: Deduplicación Inteligente
=================================
Detecta preguntas duplicadas o muy similares comparando contra preguntas_usadas.

Niveles de detección:
- Nivel 1: Hash exacto (SHA-256 de contexto + enunciado)
- Nivel 2: Fuzzy matching (RapidFuzz - Levenshtein)
- Nivel 3C: Matching semántico (Embeddings + pgvector)

Alcance: Misma institución + misma área.
"""

import hashlib
import json
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from sqlalchemy.exc import SQLAlchemyError

from app.services.embedding_service import EmbeddingService, EmbeddingServiceError

# Intentar importar rapidfuzz, si no está disponible usar fallback
try:
    from rapidfuzz import fuzz

    RAPIDFUZZ_AVAILABLE = True
except ImportError:
    RAPIDFUZZ_AVAILABLE = False


logger = logging.getLogger(__name__)


def _normalize_contexto(contexto) -> str:
    if contexto is None:
        return ""
    if isinstance(contexto, str):
        return contexto
    if isinstance(contexto, (dict, list)):
        return json.dumps(contexto, ensure_ascii=False, sort_keys=True)
    return str(contexto)


@dataclass
class DuplicadoInfo:
    """Información sobre un duplicado detectado."""

    pregunta_id: int
    nivel: str  # "exacto" | "fuzzy" | "semantico"
    score: float  # 1.0 para exacto, 0-1 para fuzzy/semántico
    match_texto: Optional[str] = None
    pregunta_historica_id: Optional[int] = None


@dataclass
class Gate3Result:
    """Resultado de la validación de Gate 3."""

    passed: bool = True
    duplicados: List[DuplicadoInfo] = field(default_factory=list)
    stats: Dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "passed": self.passed,
            "duplicados": [
                {
                    "pregunta_id": d.pregunta_id,
                    "nivel": d.nivel,
                    "score": d.score,
                    "match_texto": d.match_texto[:100] + "..."
                    if d.match_texto and len(d.match_texto) > 100
                    else d.match_texto,
                    "pregunta_historica_id": d.pregunta_historica_id,
                }
                for d in self.duplicados
            ],
            "stats": self.stats,
        }


class Gate3Deduplicator:
    """
    Validación de duplicados para simulacros ICFES.
    """

    # Nivel 2 (fuzzy)
    UMBRAL_FUZZY = 0.92
    MIN_LONGITUD_FUZZY = 50

    # Nivel 3C (semántico)
    ENABLE_SEMANTIC = True
    UMBRAL_SEMANTICO = 0.95
    TOP_K_SEMANTICO = 5
    EMBEDDING_MODEL = EmbeddingService.DEFAULT_MODEL

    @classmethod
    def calcular_hash(cls, contexto: str, enunciado: str) -> str:
        texto = f"{(contexto or '').strip().lower()} {(enunciado or '').strip().lower()}"
        return hashlib.sha256(texto.encode("utf-8")).hexdigest()

    @classmethod
    def verificar_duplicados(
        cls,
        preguntas_nuevas: List[Dict],
        institucion_id: int,
        area: str,
        db,  # SQLAlchemy Session
    ) -> Gate3Result:
        from app.models.pregunta_usada import PreguntaUsada

        result = Gate3Result()
        result.stats["total_verificadas"] = len(preguntas_nuevas)
        result.stats["nivel_1_checks"] = 0
        result.stats["nivel_2_checks"] = 0
        result.stats["nivel_3_checks"] = 0
        result.stats["nivel_3_candidates"] = 0
        result.stats["duplicados_semanticos"] = 0
        result.stats["semantic_errors"] = 0
        result.stats["semantic_skipped"] = 0
        result.stats["semantic_skip_reasons"] = {}

        def _semantic_skip(reason: str):
            result.stats["semantic_skipped"] += 1
            reasons = result.stats["semantic_skip_reasons"]
            reasons[reason] = reasons.get(reason, 0) + 1

        historico = (
            db.query(PreguntaUsada)
            .filter(
                PreguntaUsada.institucion_id == institucion_id,
                PreguntaUsada.area == area,
            )
            .all()
        )

        result.stats["preguntas_historicas"] = len(historico)
        result.stats["historico_con_embedding"] = len(
            [p for p in historico if getattr(p, "embedding", None) is not None]
        )

        if not historico:
            result.passed = True
            return result

        hashes_existentes = {p.hash_contenido: p for p in historico if p.hash_contenido}
        textos_existentes = [(p.pregunta or "", p.id) for p in historico if p.pregunta]

        for pregunta in preguntas_nuevas:
            pregunta_id = pregunta.get("id", 0)
            contexto = _normalize_contexto(pregunta.get("contexto", ""))
            enunciado = (
                pregunta.get("enunciado") or pregunta.get("pregunta") or ""
            )
            if not isinstance(enunciado, str):
                enunciado = str(enunciado or "")

            texto_completo = f"{contexto} {enunciado}".strip()

            # NIVEL 1: Hash exacto
            hash_nuevo = cls.calcular_hash(contexto, enunciado)
            result.stats["nivel_1_checks"] += 1

            if hash_nuevo in hashes_existentes:
                match = hashes_existentes[hash_nuevo]
                result.duplicados.append(
                    DuplicadoInfo(
                        pregunta_id=pregunta_id,
                        nivel="exacto",
                        score=1.0,
                        match_texto=match.pregunta,
                        pregunta_historica_id=match.id,
                    )
                )
                continue

            # NIVEL 2: Fuzzy matching
            if RAPIDFUZZ_AVAILABLE and len(texto_completo) >= cls.MIN_LONGITUD_FUZZY:
                result.stats["nivel_2_checks"] += 1
                fuzzy_found = False
                for texto_hist, hist_id in textos_existentes:
                    if len(texto_hist) < cls.MIN_LONGITUD_FUZZY:
                        continue
                    similitud = fuzz.token_set_ratio(texto_completo, texto_hist) / 100.0
                    if similitud >= cls.UMBRAL_FUZZY:
                        result.duplicados.append(
                            DuplicadoInfo(
                                pregunta_id=pregunta_id,
                                nivel="fuzzy",
                                score=round(similitud, 3),
                                match_texto=texto_hist,
                                pregunta_historica_id=hist_id,
                            )
                        )
                        fuzzy_found = True
                        break
                if fuzzy_found:
                    continue

            # NIVEL 3C: Semantic matching (fail-open)
            if not cls.ENABLE_SEMANTIC:
                _semantic_skip("disabled")
                continue
            if result.stats["historico_con_embedding"] == 0:
                _semantic_skip("no_embedding")
                continue
            if not texto_completo:
                _semantic_skip("texto_vacio")
                continue

            result.stats["nivel_3_checks"] += 1

            try:
                embedding_nuevo = EmbeddingService.embed_texts(
                    [texto_completo], model=cls.EMBEDDING_MODEL
                )[0]
            except EmbeddingServiceError as e:
                logger.warning("Gate 3 semantic skip (api_error): %s", e)
                result.stats["semantic_errors"] += 1
                _semantic_skip("api_error")
                continue

            try:
                candidates = (
                    db.query(
                        PreguntaUsada.id.label("hist_id"),
                        PreguntaUsada.pregunta.label("hist_texto"),
                        PreguntaUsada.embedding.cosine_distance(embedding_nuevo).label("distance"),
                    )
                    .filter(
                        PreguntaUsada.institucion_id == institucion_id,
                        PreguntaUsada.area == area,
                        PreguntaUsada.embedding.isnot(None),
                    )
                    .order_by(PreguntaUsada.embedding.cosine_distance(embedding_nuevo))
                    .limit(cls.TOP_K_SEMANTICO)
                    .all()
                )
            except SQLAlchemyError as e:
                logger.warning("Gate 3 semantic skip (db_error): %s", e)
                result.stats["semantic_errors"] += 1
                _semantic_skip("db_error")
                continue

            result.stats["nivel_3_candidates"] += len(candidates)
            if not candidates:
                _semantic_skip("no_candidates")
                continue

            best = candidates[0]
            distance = float(best.distance) if best.distance is not None else 1.0
            similitud_semantica = max(0.0, min(1.0, 1.0 - distance))

            if similitud_semantica > cls.UMBRAL_SEMANTICO:
                result.duplicados.append(
                    DuplicadoInfo(
                        pregunta_id=pregunta_id,
                        nivel="semantico",
                        score=round(similitud_semantica, 3),
                        match_texto=best.hist_texto,
                        pregunta_historica_id=best.hist_id,
                    )
                )
                result.stats["duplicados_semanticos"] += 1

        result.stats["duplicados_encontrados"] = len(result.duplicados)
        result.passed = len(result.duplicados) == 0
        return result


def backfill_hashes(db, institucion_id: Optional[int] = None):
    """
    Utilidad para calcular hashes faltantes en preguntas_usadas.
    """
    from app.models.pregunta_usada import PreguntaUsada

    query = db.query(PreguntaUsada).filter(PreguntaUsada.hash_contenido.is_(None))
    if institucion_id:
        query = query.filter(PreguntaUsada.institucion_id == institucion_id)

    preguntas_sin_hash = query.all()
    actualizadas = 0

    for p in preguntas_sin_hash:
        texto = p.pregunta or ""
        p.hash_contenido = Gate3Deduplicator.calcular_hash("", texto)
        actualizadas += 1

    db.commit()
    return actualizadas
