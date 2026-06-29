"""
Gate 5: QA Semántico con LLM (Groq)
====================================
Valida coherencia semántica de las preguntas usando IA.

Detecta:
- Preguntas que no corresponden al tema declarado
- Enunciados incoherentes con el contexto
- Posibles alucinaciones
- Respuestas que no responden la pregunta

Usa Groq (llama-3.3-70b-versatile) para validación.
"""

import os
import json
import requests
import logging
from typing import Dict, List, Optional
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

# Configuración OpenAI
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
MODEL_NAME = "gpt-4o-mini"

@dataclass
class SemanticIssue:
    """Problema semántico detectado por el LLM"""
    pregunta_id: int
    nivel: str  # "error" o "warning"
    tipo: str   # Categoría del problema
    mensaje: str
    detalles: Optional[str] = None


@dataclass
class Gate5Result:
    """Resultado de la validación semántica"""
    passed: bool = True
    issues: List[SemanticIssue] = field(default_factory=list)
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
                    "detalles": i.detalles
                }
                for i in self.issues
            ],
            "stats": self.stats
        }


class Gate5SemanticValidator:
    """
    Validación semántica con LLM para simulacros.
    Usa BATCH PROCESSING: valida todas las preguntas en un solo prompt.
    
    Uso:
        result = Gate5SemanticValidator.validar_semantica(
            preguntas=contenido["preguntas"],
            area="Matemáticas"
        )
        if not result.passed:
            raise HTTPException(400, detail=result.to_dict())
    """
    
    # Prompt de sistema para validación batch
    SYSTEM_PROMPT = """Eres un validador de calidad para preguntas tipo ICFES (prueba estandarizada colombiana).
Tu tarea es detectar problemas de coherencia semántica en TODAS las preguntas proporcionadas.

CRÍTICO detectar:
1. Tema declarado NO coincide con el contenido de la pregunta
2. Enunciado pregunta algo diferente a lo que el contexto plantea
3. Información inventada o implausible (alucinaciones)
4. La respuesta correcta no responde realmente la pregunta
5. Las opciones no son mutuamente excluyentes o lógicas

Responde SIEMPRE en JSON válido con esta estructura exacta:
{
  "validaciones": [
    {
      "pregunta_id": 1,
      "coherente": true,
      "problemas": []
    },
    {
      "pregunta_id": 2,
      "coherente": false,
      "problemas": [
        {
          "tipo": "tema_incorrecto|contexto_incoherente|alucinacion|respuesta_invalida|opciones_problematicas",
          "nivel": "error|warning",
          "mensaje": "Descripción breve del problema"
        }
      ]
    }
  ]
}

IMPORTANTE: Responde con UNA validación por cada pregunta proporcionada, en el mismo orden."""

    @classmethod
    def validar_semantica(
        cls,
        preguntas: List[Dict],
        area: str,
        timeout: int = 60
    ) -> Gate5Result:
        """
        Valida coherencia semántica de TODAS las preguntas en un solo prompt.
        
        Args:
            preguntas: Lista de preguntas del simulacro
            area: Área del simulacro (Matemáticas, Ciencias, etc.)
            timeout: Timeout en segundos para la llamada API
            
        Returns:
            Gate5Result con problemas encontrados
        """
        result = Gate5Result()
        result.stats["total_preguntas"] = len(preguntas)
        result.stats["api_disponible"] = bool(OPENAI_API_KEY)
        result.stats["modo"] = "batch"
        
        if not OPENAI_API_KEY:
            logger.warning("OPENAI_API_KEY no configurada. Gate 5 deshabilitado.")
            result.stats["mensaje"] = "Gate 5 deshabilitado: API key no configurada"
            return result
        
        if not preguntas:
            return result
        
        try:
            print(f"🔍 Gate 5: Iniciando validación semántica de {len(preguntas)} preguntas ({area})...")
            
            # Validar todas las preguntas en batch
            import time
            start_time = time.time()
            
            validaciones = cls._validar_batch(preguntas, area, timeout)
            
            elapsed = time.time() - start_time
            result.stats["validadas_con_ia"] = len(preguntas)
            result.stats["tiempo_segundos"] = round(elapsed, 2)
            
            # Contar coherentes vs problemas
            coherentes = sum(1 for v in validaciones if v.get("coherente", True))
            con_problemas = len(validaciones) - coherentes
            
            # Procesar resultados
            for v in validaciones:
                pregunta_id = v.get("pregunta_id", 0)
                
                if not v.get("coherente", True):
                    for problema in v.get("problemas", []):
                        result.issues.append(SemanticIssue(
                            pregunta_id=pregunta_id,
                            nivel=problema.get("nivel", "warning"),
                            tipo=problema.get("tipo", "desconocido"),
                            mensaje=problema.get("mensaje", "Problema no especificado")
                        ))
            
            # Log de resultado
            if con_problemas == 0:
                print(f"✅ Gate 5: PASSED - {coherentes}/{len(preguntas)} preguntas coherentes ({elapsed:.2f}s)")
            else:
                errores = len([i for i in result.issues if i.nivel == "error"])
                warnings = len([i for i in result.issues if i.nivel == "warning"])
                print(f"⚠️ Gate 5: {con_problemas} preguntas con problemas ({errores} errores, {warnings} warnings) - {elapsed:.2f}s")
                # Mostrar detalles de cada error
                for issue in result.issues:
                    print(f"      [{issue.nivel.upper()}] Pregunta {issue.pregunta_id}: {issue.tipo} - {issue.mensaje}")
                        
        except Exception as e:
            print(f"❌ Gate 5 Error: {e}")
            result.stats["error"] = str(e)[:200]
            # No bloquear por errores de API - solo warning
            result.issues.append(SemanticIssue(
                pregunta_id=0,
                nivel="warning",
                tipo="error_validacion",
                mensaje=f"No se pudo validar con IA: {str(e)[:100]}"
            ))
        
        # El gate pasa si no hay errores (solo warnings)
        result.passed = not any(i.nivel == "error" for i in result.issues)
        
        return result
    
    @classmethod
    def _validar_batch(cls, preguntas: List[Dict], area: str, timeout: int) -> List[Dict]:
        """Valida todas las preguntas en un solo prompt usando GPT-4o-mini"""
        
        # Construir resumen de cada pregunta
        preguntas_texto = []
        
        for p in preguntas:
            pregunta_id = p.get("id", 0)
            tema = p.get("tema", "No especificado")
            competencia = p.get("competencia", "No especificada")
            contexto = p.get("contexto", "")[:800]  # Limitar para no exceder tokens
            enunciado = p.get("enunciado", "")
            opciones = p.get("opciones", [])
            respuesta = p.get("respuesta_correcta", "")
            justificacion = p.get("justificacion", "")[:200]
            
            opciones_texto = " | ".join([
                f"{o.get('id', '?')}) {o.get('texto', '')[:50]}"
                for o in opciones if isinstance(o, dict)
            ])
            
            pregunta_resumen = f"""
---
ID: {pregunta_id}
TEMA: {tema}
COMPETENCIA: {competencia}
CONTEXTO: {contexto}...
ENUNCIADO: {enunciado}
OPCIONES: {opciones_texto}
CORRECTA: {respuesta}
JUSTIFICACIÓN: {justificacion}...
---"""
            preguntas_texto.append(pregunta_resumen)
        
        user_prompt = f"""Valida estas {len(preguntas)} preguntas del área de {area}:

{"".join(preguntas_texto)}

Para CADA pregunta verifica:
1. ¿El contenido corresponde realmente al tema declarado?
2. ¿El enunciado es coherente con el contexto?
3. ¿Hay información que parezca inventada o implausible?
4. ¿La respuesta marcada como correcta realmente responde la pregunta?

Responde en JSON con una validación por cada pregunta."""

        # Usar OpenAI
        try:
            from openai import OpenAI
            client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": cls.SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"},
                max_tokens=4000,
                temperature=0.1,
                timeout=timeout
            )
            
            content = response.choices[0].message.content
            parsed = json.loads(content)
            return parsed.get("validaciones", [])
            
        except ImportError:
            raise Exception("Librería openai no instalada")
        except Exception as e:
            raise Exception(f"OpenAI API Error: {str(e)}")
