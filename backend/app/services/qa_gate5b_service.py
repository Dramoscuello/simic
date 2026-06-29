"""
Gate 5B: Semantic Context Check (Lectura Crítica)
==================================================
Valida que las preguntas estén semánticamente relacionadas con el texto base
usando embeddings y similitud del coseno.

Problema que resuelve:
- Preguntas que no se relacionan con el contexto (alucinaciones del LLM)
- Preguntas "off-topic" que inventan información no presente en el texto

Modelo: sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
Área: Solo LECTURA_CRITICA
"""

import logging
from typing import Dict, List, Optional
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

# Modelo global (Lazy Loading para no consumir RAM innecesariamente)
_semantic_model = None


def get_semantic_model():
    """Carga el modelo de embeddings solo cuando se necesita (Lazy Loading)"""
    global _semantic_model
    if _semantic_model is None:
        try:
            from sentence_transformers import SentenceTransformer
            logger.info("🔄 Cargando modelo de embeddings (primera ejecución)...")
            _semantic_model = SentenceTransformer('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')
            logger.info("✅ Modelo de embeddings cargado correctamente")
        except ImportError:
            logger.error("❌ sentence-transformers no instalado. Ejecutar: pip install sentence-transformers")
            raise
    return _semantic_model


@dataclass
class ContextIssue:
    """Problema de coherencia contexto-pregunta"""
    pregunta_id: int
    nivel: str  # "error" o "warning"
    tipo: str   # "contexto_desconectado"
    mensaje: str
    similitud: float  # Score de similitud (0-1)


@dataclass
class Gate5BResult:
    """Resultado de la validación de contexto semántico"""
    passed: bool = True
    issues: List[ContextIssue] = field(default_factory=list)
    stats: Dict = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        return {
            "passed": self.passed,
            "issues": [
                {
                    "pregunta_id": i.pregunta_id,
                    "nivel": i.nivel,
                    "tipo": i.tipo,
                    "mensaje": i.mensaje,
                    "similitud": round(i.similitud, 3)
                }
                for i in self.issues
            ],
            "stats": self.stats
        }


class Gate5BContextValidator:
    """
    Validación de coherencia semántica contexto-pregunta para Lectura Crítica.
    
    Usa embeddings locales para calcular similitud del coseno entre:
    - Texto base (contexto)
    - Pregunta + Respuesta correcta
    
    Umbrales:
    - < 0.35: ERROR (rechazar, pregunta desconectada del contexto)
    - 0.35 - 0.45: WARNING (revisar, posible divergencia)
    - >= 0.45: OK (pregunta coherente con el contexto)
    
    Uso:
        result = Gate5BContextValidator.validar_contexto(preguntas)
        if not result.passed:
            # Rechazar o reparar
    """
    
    # Umbrales de similitud
    THRESHOLD_ERROR = 0.35    # Por debajo = ERROR (rechazar)
    THRESHOLD_WARNING = 0.45  # Entre 0.35 y 0.45 = WARNING
    
    @classmethod
    def validar_contexto(cls, preguntas: List[Dict]) -> Gate5BResult:
        """
        Valida que cada pregunta esté semánticamente relacionada con su contexto.
        
        Args:
            preguntas: Lista de preguntas del simulacro
            
        Returns:
            Gate5BResult con problemas encontrados
        """
        result = Gate5BResult()
        result.stats["total_preguntas"] = len(preguntas)
        
        if not preguntas:
            return result
        
        try:
            import time
            start_time = time.time()
            
            print(f"🔍 Gate 5B: Validando coherencia contexto-pregunta ({len(preguntas)} preguntas)...")
            
            model = get_semantic_model()
            
            validadas = 0
            similitudes = []
            
            for p in preguntas:
                if not isinstance(p, dict):
                     print(f"      ⚠️ Ignorando elemento inválido en preguntas: {type(p)}")
                     continue
                
                pregunta_id = p.get("id", 0)
                contexto = p.get("contexto", "")
                enunciado = p.get("enunciado", "")
                
                # Obtener texto de respuesta correcta
                respuesta_correcta_id = p.get("respuesta_correcta", "")
                opciones = p.get("opciones", [])
                respuesta_texto = ""
                
                if isinstance(opciones, list):
                    for opcion in opciones:
                        if isinstance(opcion, dict):
                            if opcion.get("id") == respuesta_correcta_id:
                                respuesta_texto = opcion.get("texto", "")
                                break
                        else:
                            # Si la opción no es dict, ignorarla o manejarla
                            pass
                
                # Si no hay contexto, no podemos validar
                if not contexto or len(contexto.strip()) < 50:
                    continue
                
                # Preparar textos para embedding
                texto_contexto = contexto[:2000]  # Limitar para evitar tokens excesivos
                texto_pregunta = f"{enunciado} {respuesta_texto}"
                
                # Calcular embeddings
                embeddings = model.encode([texto_contexto, texto_pregunta])
                
                # Calcular similitud del coseno
                from sklearn.metrics.pairwise import cosine_similarity
                similitud = cosine_similarity([embeddings[0]], [embeddings[1]])[0][0]
                similitudes.append(similitud)
                validadas += 1
                
                # Evaluar umbral
                if similitud < cls.THRESHOLD_ERROR:
                    result.issues.append(ContextIssue(
                        pregunta_id=pregunta_id,
                        nivel="error",
                        tipo="contexto_desconectado",
                        mensaje=f"La pregunta no está relacionada con el texto base (similitud: {similitud:.2f})",
                        similitud=similitud
                    ))
                    print(f"      ❌ Pregunta {pregunta_id}: similitud={similitud:.3f} (ERROR - desconectada)")
                    
                elif similitud < cls.THRESHOLD_WARNING:
                    result.issues.append(ContextIssue(
                        pregunta_id=pregunta_id,
                        nivel="warning",
                        tipo="contexto_debil",
                        mensaje=f"Relación débil con el texto base (similitud: {similitud:.2f})",
                        similitud=similitud
                    ))
                    print(f"      ⚠️ Pregunta {pregunta_id}: similitud={similitud:.3f} (WARNING - relación débil)")
                else:
                    print(f"      ✅ Pregunta {pregunta_id}: similitud={similitud:.3f} (OK)")
            
            elapsed = time.time() - start_time
            
            # Estadísticas
            result.stats["validadas"] = validadas
            result.stats["tiempo_segundos"] = round(elapsed, 2)
            result.stats["similitud_promedio"] = round(sum(similitudes) / len(similitudes), 3) if similitudes else 0
            result.stats["similitud_minima"] = round(min(similitudes), 3) if similitudes else 0
            result.stats["similitud_maxima"] = round(max(similitudes), 3) if similitudes else 0
            
            # Resultado
            errores = len([i for i in result.issues if i.nivel == "error"])
            warnings = len([i for i in result.issues if i.nivel == "warning"])
            
            if errores == 0:
                print(f"✅ Gate 5B: PASSED - Todas las preguntas coherentes con su contexto ({elapsed:.2f}s)")
                if warnings > 0:
                    print(f"      ⚠️ {warnings} pregunta(s) con relación débil (revisar)")
            else:
                print(f"❌ Gate 5B: FAILED - {errores} pregunta(s) desconectadas del contexto ({elapsed:.2f}s)")
            
            # El gate pasa si no hay errores
            result.passed = errores == 0
            
        except ImportError as e:
            logger.error(f"Gate 5B: Dependencia faltante - {e}")
            result.stats["error"] = "sentence-transformers o sklearn no instalado"
            # No bloquear, solo advertir
            result.issues.append(ContextIssue(
                pregunta_id=0,
                nivel="warning",
                tipo="dependencia_faltante",
                mensaje="Gate 5B deshabilitado: instalar sentence-transformers y sklearn",
                similitud=0
            ))
            
        except Exception as e:
            logger.error(f"Gate 5B Error: {e}")
            result.stats["error"] = str(e)[:200]
            # No bloquear por errores técnicos
            result.issues.append(ContextIssue(
                pregunta_id=0,
                nivel="warning",
                tipo="error_tecnico",
                mensaje=f"Error en validación: {str(e)[:100]}",
                similitud=0
            ))
        
        return result
