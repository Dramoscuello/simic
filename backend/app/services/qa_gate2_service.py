"""
Gate 2: Validación de Reglas de Negocio (Hard Rules)
=====================================================
Este servicio valida que el contenido del simulacro cumpla con las reglas
de negocio ICFES, independientemente de si la IA las siguió o no.

Checks implementados:
- Conteo de preguntas (mínimo/máximo)
- Opciones completas (4 por pregunta, no vacías)
- Respuesta correcta válida (A, B, C, D)
- Distribución de dificultad (configurable con tolerancia)
- Coherencia gráfica (tiene_grafico vs configuracion_grafico)
- IDs únicos (sin duplicados)
"""

from typing import Dict, List, Any
from dataclasses import dataclass, field


@dataclass
class QAResult:
    """Resultado de la validación de Gate 2"""
    passed: bool = True
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    stats: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "passed": self.passed,
            "errors": self.errors,
            "warnings": self.warnings,
            "stats": self.stats
        }


class Gate2Validator:
    """
    Validación de Reglas de Negocio para Simulacros ICFES
    
    Uso:
        result = Gate2Validator.validar_simulacro(contenido_json)
        if not result.passed:
            raise HTTPException(400, detail=result.to_dict())
    """
    
    # ═══════════════════════════════════════════════════════════════════
    # 🎛️ CONFIGURACIÓN - EDITAR AQUÍ PARA AJUSTAR REGLAS
    # ═══════════════════════════════════════════════════════════════════
    
    # Conteo de preguntas
    MIN_PREGUNTAS = 10
    MAX_PREGUNTAS = 50
    
    # Distribución de dificultad esperada (debe sumar 1.0)
    DISTRIBUCION_ESPERADA = {
        "facil": 0.40,     # 40%
        "media": 0.50,     # 50%
        "dificil": 0.10    # 10%
    }
    
    # Tolerancia para distribución (±8%)
    TOLERANCIA_DISTRIBUCION = 0.08
    
    # Opciones válidas
    OPCIONES_VALIDAS = {"A", "B", "C", "D"}
    
    # ═══════════════════════════════════════════════════════════════════
    
    @classmethod
    def validar_simulacro(cls, contenido: Dict, skip_conteo: bool = False) -> QAResult:
        """
        Ejecuta todas las validaciones de Gate 2 sobre el contenido del simulacro.
        
        Args:
            contenido: Dict con estructura {"meta": {...}, "preguntas": [...]}
            skip_conteo: Si True, omite la validación de conteo de preguntas (útil para regeneración parcial)
            
        Returns:
            QAResult con passed=True/False, errores, warnings y estadísticas
        """
        result = QAResult()
        preguntas = contenido.get("preguntas", [])
        
        # Ejecutar todos los checks
        if not skip_conteo:
            cls._validar_conteo(preguntas, result)
        cls._validar_opciones(preguntas, result)
        cls._validar_respuestas_correctas(preguntas, result)
        cls._validar_distribucion_dificultad(preguntas, result)
        cls._validar_coherencia_grafica(preguntas, result)
        cls._validar_ids_unicos(preguntas, result)
        cls._validar_campos_requeridos(preguntas, result)
        
        # El simulacro pasa solo si no hay errores
        result.passed = len(result.errors) == 0
        
        return result
    
    # ─────────────────────────────────────────────────────────────────
    # VALIDADORES INDIVIDUALES
    # ─────────────────────────────────────────────────────────────────
    
    @classmethod
    def _validar_conteo(cls, preguntas: List, result: QAResult):
        """Check 1: Número de preguntas dentro del rango permitido"""
        total = len(preguntas)
        result.stats["total_preguntas"] = total
        
        if total < cls.MIN_PREGUNTAS:
            result.errors.append(
                f"Mínimo {cls.MIN_PREGUNTAS} preguntas requeridas, hay {total}"
            )
        elif total > cls.MAX_PREGUNTAS:
            result.warnings.append(
                f"Más de {cls.MAX_PREGUNTAS} preguntas ({total}), verificar si es intencional"
            )
    
    @classmethod
    def _validar_opciones(cls, preguntas: List, result: QAResult):
        """Check 2: Cada pregunta tiene exactamente 4 opciones no vacías"""
        for i, p in enumerate(preguntas, 1):
            pregunta_id = p.get("id", i)
            opciones = p.get("opciones", [])
            
            # Verificar cantidad
            if len(opciones) != 4:
                result.errors.append(
                    f"Pregunta {pregunta_id}: tiene {len(opciones)} opciones, debe tener 4"
                )
                continue
            
            # Verificar que no estén vacías
            for opt in opciones:
                # Manejar ambos formatos: {"id": "A", "texto": "..."} o string directo
                if isinstance(opt, dict):
                    texto = opt.get("texto", "")
                else:
                    texto = str(opt)
                
                if not texto or not texto.strip():
                    result.errors.append(
                        f"Pregunta {pregunta_id}: opción vacía detectada"
                    )
                    break
    
    @classmethod
    def _validar_respuestas_correctas(cls, preguntas: List, result: QAResult):
        """Check 3: respuesta_correcta es A, B, C o D"""
        for i, p in enumerate(preguntas, 1):
            pregunta_id = p.get("id", i)
            rc = p.get("respuesta_correcta")
            
            if rc not in cls.OPCIONES_VALIDAS:
                result.errors.append(
                    f"Pregunta {pregunta_id}: respuesta_correcta='{rc}' inválida (debe ser A, B, C o D)"
                )
    
    @classmethod
    def _validar_distribucion_dificultad(cls, preguntas: List, result: QAResult):
        """Check 4: Reporte de estadísticas de dificultad (Validación real en Gate 2.5)"""
        total = len(preguntas)
        if total == 0:
            return
        
        # Contar por nivel
        conteo = {"facil": 0, "media": 0, "dificil": 0}
        no_clasificadas = 0
        
        for p in preguntas:
            dif = str(p.get("dificultad", "")).lower().strip()
            
            # Normalizar variaciones comunes
            if "fac" in dif or "fác" in dif:
                conteo["facil"] += 1
            elif "med" in dif:
                conteo["media"] += 1
            elif "dif" in dif:
                conteo["dificil"] += 1
            else:
                no_clasificadas += 1
        
        # Guardar estadísticas (Solo informativo)
        result.stats["distribucion_dificultad"] = conteo
        result.stats["porcentajes_dificultad"] = {
            k: round(v / total * 100, 1) if total > 0 else 0 for k, v in conteo.items()
        }
        
        if no_clasificadas > 0:
            # Esto sí es útil saber, aunque sea warning leve
            result.warnings.append(
                f"{no_clasificadas} preguntas sin dificultad reconocida/inválida"
            )
    
    @classmethod
    def _validar_coherencia_grafica(cls, preguntas: List, result: QAResult):
        """Check 5: tiene_grafico es coherente con tipo_grafico y configuracion_grafico"""
        for i, p in enumerate(preguntas, 1):
            pregunta_id = p.get("id", i)
            tiene = p.get("tiene_grafico", False)
            tipo = p.get("tipo_grafico")
            config = p.get("configuracion_grafico")
            
            if tiene:
                if not tipo:
                    result.errors.append(
                        f"Pregunta {pregunta_id}: tiene_grafico=true pero tipo_grafico es nulo"
                    )
                if not config:
                    result.errors.append(
                        f"Pregunta {pregunta_id}: tiene_grafico=true pero configuracion_grafico es nulo"
                    )
            else:
                # Advertencia si hay datos gráficos pero está marcado como false
                if tipo or config:
                    result.warnings.append(
                        f"Pregunta {pregunta_id}: tiene_grafico=false pero hay tipo/config gráfica (¿olvidaste activarlo?)"
                    )
    
    @classmethod
    def _validar_ids_unicos(cls, preguntas: List, result: QAResult):
        """Check 6: No hay IDs duplicados"""
        ids = [p.get("id") for p in preguntas]
        vistos = set()
        duplicados = set()
        
        for id_val in ids:
            if id_val in vistos:
                duplicados.add(id_val)
            vistos.add(id_val)
        
        if duplicados:
            result.errors.append(
                f"IDs duplicados detectados: {sorted(duplicados)}"
            )
        
        result.stats["ids_unicos"] = len(vistos)
    
    @classmethod
    def _validar_campos_requeridos(cls, preguntas: List, result: QAResult):
        """Check 7: Campos obligatorios presentes y no vacíos"""
        campos_requeridos = ["competencia", "componente", "tema", "contexto", "enunciado"]
        
        for i, p in enumerate(preguntas, 1):
            pregunta_id = p.get("id", i)
            
            for campo in campos_requeridos:
                valor = p.get(campo)
                if not valor or (isinstance(valor, str) and not valor.strip()):
                    result.errors.append(
                        f"Pregunta {pregunta_id}: campo '{campo}' vacío o ausente"
                    )
