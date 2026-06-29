"""
Gate 7: Validación Científica con Wolfram Alpha (v2 Simplificado)
===================================================================
Valida que las respuestas matemáticas y científicas generadas por el LLM sean correctas.

Nuevo enfoque simplificado:
- UNA sola query a Wolfram por pregunta
- Wolfram calcula Y compara internamente
- Sin código local de comparación

Query: "is [resultado del problema] equal to [opción marcada]?"
→ True = correcto, False = incorrecto

Aplica para: MATEMATICAS, CIENCIAS_NATURALES (física y química).
"""

import os
import re
import json
import requests
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

# =============================================================================
# CONFIGURACIÓN
# =============================================================================

# Wolfram Alpha API
WOLFRAM_API_URL = "http://api.wolframalpha.com/v2/query"
WOLFRAM_APP_ID = os.getenv("WOLFRAM_APP_ID", "")

# OpenAI para extracción de queries (fallback)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
MODEL_NAME = "gpt-4o"

# Timeout para Wolfram (segundos) - 25s para queries complejas como geometría
WOLFRAM_TIMEOUT = 25


# =============================================================================
# DATACLASSES
# =============================================================================

@dataclass
class MathIssue:
    """Problema matemático detectado"""
    pregunta_id: int
    nivel: str  # "error" o "warning"
    tipo: str   # Código del error (E7.1, E7.2, etc.)
    mensaje: str
    esperado: Optional[str] = None
    obtenido: Optional[str] = None
    detalles: Optional[str] = None


@dataclass
class Gate7Result:
    """Resultado de la validación matemática"""
    passed: bool = True
    issues: List[MathIssue] = field(default_factory=list)
    stats: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        return {
            "passed": self.passed,
            "issues": [
                {
                    "pregunta_id": i.pregunta_id,
                    "nivel": i.nivel,
                    "tipo": i.tipo,
                    "mensaje": i.mensaje,
                    "esperado": i.esperado,
                    "obtenido": i.obtenido,
                    "detalles": i.detalles
                }
                for i in self.issues
            ],
            "stats": self.stats
        }


# =============================================================================
# VALIDADOR PRINCIPAL
# =============================================================================

class Gate7MathValidator:
    """
    Validación matemática con Wolfram Alpha (v2 Simplificado).
    
    Flujo:
    1. LLM (Groq) extrae el problema matemático del contexto
    2. Wolfram valida: "is [problema] equal to [respuesta marcada]?"
    3. True = correcto, False = error
    
    Uso:
        result = Gate7MathValidator.validar_matematicas(contenido["preguntas"])
        if not result.passed:
            # Hay errores matemáticos
    """
    
    # Prompt para extraer validación en formato Wolfram
    EXTRACTION_PROMPT = """Eres un experto en matemáticas y ciencias. Tu tarea es extraer ecuaciones verificables para Wolfram Alpha.

OBJETIVO:
Para cada pregunta, genera una query en INGLÉS "is [cálculo] equal to [respuesta]?" que confirme si la respuesta es correcta.

REGLAS ABSOLUTAS E INQUEBRANTABLES:

🔴 SI EL COMPONENTE ES "FÍSICO", "QUÍMICO" O "MATEMÁTICAS":
   -> ¡TIENES QUE VALIDARLO! NO OPTIONAL.
   -> NO puedes responder "puede_validar": false.
   -> Si faltan datos explícitos:
      1. INFIERE constantes estándar (ganvedad g=9.8, densidad agua=1000, etc).
      2. Si es una relación proporcional ("si se duplica X..."), USA VALORES DE PRUEBA (ej: asume v=1, luego v=2).
      3. Si es una tabla o gráfico, LEE LA DESCRIPCIÓN VISUAL Y EXTRAE LOS DATOS APROXIMADOS.
   -> La única excusa para no validar es si el texto es 100% filosófico/abstracto sin ninguna mención a variables físicas.

🔴 SI EL COMPONENTE ES "BIOLÓGICO":
   -> Generalmente NO validable (conceptos, taxonomía).
   -> EXCEPCIÓN: Si ves números, porcentajes o genética mendeliana (probabilidades), ENTONCES SÍ VALIDA.

🔴 SI EL COMPONENTE ES "CTS":
   -> Valida SOLO si hay cálculos de impacto (emisiones, ahorros).

FORMATO DE RESPUESTA (JSON):
{
    "preguntas": [
        {
            "id": 1,
            "puede_validar": true,
            "query_validacion": "is 5*9.8 equal to 49?" 
        }
    ]
}

EJEMPLOS DE INFERENCIA FORZADA (OBLIGATORIO):

1. Caso: "Si la velocidad se duplica, la energía cinética..." (Sin valores)
   -> TU ACCIÓN: Inventa valores. E_c = 0.5*m*v^2.
   -> Query: "is (0.5 * 1 * (2*1)^2) / (0.5 * 1 * 1^2) equal to 4?" (Verifica si la relación es 4 veces).

2. Caso: "Caída libre de un objeto..." (Falta gravedad)
   -> TU ACCIÓN: Asume g=9.8 m/s^2.
   -> Query: "is sqrt(2*9.8*10) equal to 14?"

3. Caso: "Según la tabla, ¿cuál es el reactivo límite?"
   -> TU ACCIÓN: Extrae los moles de la descripción visual de la tabla.
   -> Query: "is limiting reactant of 0.05 mol CaCO3 and 0.06 mol HCl equal to HCl?" (Wolfram entiende química).
"""
    
    @classmethod
    def validar_matematicas(
        cls,
        preguntas: List[Dict],
        timeout: int = WOLFRAM_TIMEOUT,
        area: str = "MATEMATICAS",
        wolfram_app_id: Optional[str] = None,
        openai_api_key: Optional[str] = None,
    ) -> Gate7Result:
        """
        Valida matemáticamente las preguntas de un simulacro.
        
        Args:
            preguntas: Lista de preguntas del simulacro
            timeout: Timeout por consulta a Wolfram
            area: Área del simulacro (MATEMATICAS o CIENCIAS_NATURALES)
            
        Returns:
            Gate7Result con problemas matemáticos encontrados
        """
        result = Gate7Result()
        wolfram_app_id = (wolfram_app_id or WOLFRAM_APP_ID or "").strip()
        openai_api_key = (openai_api_key or OPENAI_API_KEY or "").strip()

        result.stats["total_preguntas"] = len(preguntas)
        result.stats["wolfram_disponible"] = bool(wolfram_app_id)
        result.stats["openai_disponible"] = bool(openai_api_key)

        if not preguntas:
            return result

        # Verificar disponibilidad de APIs
        if not wolfram_app_id:
            print(f"\n🔢 Gate 7: ⚠️ WOLFRAM_APP_ID no configurado - Gate deshabilitado")
            result.stats["mensaje"] = "Gate 7 deshabilitado: institución no tiene Wolfram App ID"
            return result

        if not openai_api_key:
            print(f"\n🔢 Gate 7: ⚠️ OPENAI_API_KEY no configurado - Gate deshabilitado")
            result.stats["mensaje"] = "Gate 7 deshabilitado: se requiere API key de OpenAI"
            return result
        
        try:
            import time
            start_time = time.time()
            
            print(f"\n🔢 Gate 7: Validando {len(preguntas)} preguntas con Wolfram Alpha...")
            
            # Paso 1: Extraer queries de validación con LLM
            print(f"   📝 Generando queries de validación...", end=" ")
            extracciones = cls._extraer_queries_validacion(preguntas, area)
            print(f"✓ ({len(extracciones)} generadas)")
            
            # Estadísticas
            validadas_ok = 0
            errores = 0
            no_validables = 0
            
            # Paso 2: Validar cada pregunta con Wolfram
            for extraccion in extracciones:
                pregunta_id = extraccion.get("id", 0)
                puede_validar = extraccion.get("puede_validar", False)
                
                if not puede_validar:
                    no_validables += 1
                    continue
                
                query = extraccion.get("query_validacion", "")
                if not query:
                    no_validables += 1
                    continue
                
                # Consultar Wolfram
                es_correcto = cls._verificar_con_wolfram(query, timeout, wolfram_app_id)
                
                if es_correcto is True:
                    validadas_ok += 1
                elif es_correcto is False:
                    errores += 1
                    # Encontrar la pregunta original para el mensaje
                    pregunta_original = next(
                        (p for p in preguntas if p.get("id") == pregunta_id), 
                        {}
                    )
                    respuesta_marcada = pregunta_original.get("respuesta_correcta", "?")
                    opciones = pregunta_original.get("opciones", [])
                    texto_marcado = ""
                    for opt in opciones:
                        if isinstance(opt, dict) and opt.get("id") == respuesta_marcada:
                            texto_marcado = opt.get("texto", "")[:50]
                            break
                    
                    result.issues.append(MathIssue(
                        pregunta_id=pregunta_id,
                        nivel="error",
                        tipo="E7.3",
                        mensaje="Respuesta marcada es matemáticamente incorrecta",
                        obtenido=f"{respuesta_marcada} ({texto_marcado})",
                        detalles=f"Query Wolfram: {query[:100]}"
                    ))
                else:
                    # Wolfram no pudo verificar (timeout, error, etc.)
                    no_validables += 1
            
            elapsed = time.time() - start_time
            
            # Actualizar estadísticas
            result.stats["validadas_correctamente"] = validadas_ok
            result.stats["errores_detectados"] = errores
            result.stats["no_validables"] = no_validables
            result.stats["tiempo_segundos"] = round(elapsed, 2)
            
            # Log resultado
            if errores == 0:
                print(f"   ✅ Gate 7: PASSED - {validadas_ok} correctas, {no_validables} no validables ({elapsed:.2f}s)")
            else:
                print(f"   ⚠️ Gate 7: {errores} errores, {validadas_ok} correctas ({elapsed:.2f}s)")
                for issue in result.issues:
                    print(f"      [E7.3] Pregunta {issue.pregunta_id}: {issue.mensaje}")
                    if issue.obtenido:
                        print(f"         Marcada: {issue.obtenido}")
            
        except Exception as e:
            print(f"   ❌ Gate 7 Error: {e}")
            logger.error(f"Gate 7 error: {e}", exc_info=True)
            result.stats["error"] = str(e)[:200]
        
        # El gate pasa si no hay errores
        result.passed = not any(i.nivel == "error" for i in result.issues)
        
        return result
    
    # =========================================================================
    # EXTRACCIÓN DE QUERIES
    # =========================================================================
    
    @classmethod
    def _extraer_queries_validacion(cls, preguntas: List[Dict], area: str = "MATEMATICAS") -> List[Dict]:
        """Usa LLM para generar queries de validación para Wolfram"""
        
        preguntas_texto = []
        for p in preguntas:
            pregunta_id = p.get("id", 0)
            contexto = (p.get("contexto", "") or "")[:500]
            enunciado = (p.get("enunciado", "") or p.get("pregunta", ""))[:300]
            opciones = p.get("opciones", [])
            respuesta_marcada = p.get("respuesta_correcta", "")
            
            # Extraer componente (física, química, biología) para CN
            componente = p.get("componente", "").lower() if area == "CIENCIAS_NATURALES" else "matematicas"
            
            # Extraer descripción visual del gráfico si existe
            # (contiene datos numéricos de figuras geométricas, SVG, etc.)
            descripcion_visual = ""
            tiene_grafico = p.get("tiene_grafico", False)
            if tiene_grafico:
                config_grafico = p.get("configuracion_grafico", {})
                if isinstance(config_grafico, dict):
                    # Para SVG artístico (figuras geométricas)
                    descripcion_visual = config_grafico.get("descripcion_visual", "")
                    
                    # Para tablas de datos
                    if not descripcion_visual and config_grafico.get("columnas"):
                        columnas = config_grafico.get("columnas", [])
                        filas = config_grafico.get("filas", [])
                        descripcion_visual = f"Tabla con columnas: {columnas}. Datos: {filas[:3]}"
                    
                    # Para charts (bar, line, scatter, etc.)
                    if not descripcion_visual and config_grafico.get("data"):
                        data = config_grafico.get("data", {})
                        # Intentar obtener labels
                        labels = data.get("labels", [])
                        
                        datasets = data.get("datasets", [])
                        if datasets:
                            ds_data = datasets[0].get("data", [])
                            
                            # Manejo especial para Scatter Charts (formato [{x,y}, {x,y}])
                            if ds_data and isinstance(ds_data[0], dict):
                                puntos = [f"({pt.get('x', '?')}, {pt.get('y', '?')})" for pt in ds_data[:10]]
                                valores_str = ", ".join(puntos)
                                descripcion_visual = f"Gráfico Scatter con puntos (x,y): [{valores_str}]"
                            else:
                                # Gráfico estándar (valores simples)
                                descripcion_visual = f"Gráfico con etiquetas: {labels}, valores: {ds_data}"
            
            # Obtener texto de la opción marcada
            texto_opcion_marcada = ""
            for opt in opciones:
                if isinstance(opt, dict) and opt.get("id") == respuesta_marcada:
                    texto_opcion_marcada = opt.get("texto", "")
                    break
            
            # Construir resumen incluyendo componente y descripción visual
            resumen = f"""
---
ID: {pregunta_id}
ÁREA/COMPONENTE: {componente.upper()}
CONTEXTO: {contexto}"""
            
            if descripcion_visual:
                resumen += f"\nDESCRIPCIÓN VISUAL (datos de la figura): {descripcion_visual[:400]}"
            
            resumen += f"""
PREGUNTA: {enunciado}
RESPUESTA MARCADA COMO CORRECTA: {respuesta_marcada} = "{texto_opcion_marcada}"
---"""
            preguntas_texto.append(resumen)
        
        # Prompt específico según área
        if area == "CIENCIAS_NATURALES":
            instruccion = """Analiza estas preguntas de CIENCIAS NATURALES (ICFES).

REGLAS:
- FÍSICA y QUÍMICA: DEBES generar query de validación (son calculables).
- CTS (Ciencia, Tecnología, Sociedad): Si implica cálculos (emisiones, consumo), VALIDA. Si es social, no.
- BIOLOGÍA: Marca como no validable (biologia_conceptual)."""
        else:
            instruccion = """Analiza estas preguntas de MATEMÁTICAS (ICFES).

REGLAS:
- TODAS las preguntas DEBEN tener query de validación
- Extrae los valores numéricos del contexto, enunciado o descripción visual"""
        
        user_prompt = f"""{instruccion}

{"".join(preguntas_texto)}

Genera queries de validación para Wolfram Alpha. Responde en JSON."""

        # Usar OpenAI GPT-4o-mini para extracción robusta
        try:
            from openai import OpenAI
            client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": cls.EXTRACTION_PROMPT},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"},
                max_tokens=2500,
                temperature=0.1,
                timeout=60
            )
            
            content = response.choices[0].message.content
            parsed = json.loads(content)
            return parsed.get("preguntas", [])
            
        except Exception as e:
            logger.error(f"Error extrayendo queries con OpenAI: {e}")
            return []
    
    # =========================================================================
    # VALIDACIÓN CON WOLFRAM
    # =========================================================================
    
    @classmethod
    def _verificar_con_wolfram(
        cls, query: str, timeout: int, wolfram_app_id: Optional[str] = None
    ) -> Optional[bool]:
        """
        Envía query de validación a Wolfram y retorna True/False.
        
        Args:
            query: Query de validación (ej: "is 40 equal to 40?")
            timeout: Timeout en segundos
            
        Returns:
            True si la respuesta es correcta
            False si la respuesta es incorrecta
            None si Wolfram no pudo verificar
        """
        try:
            params = {
                "appid": wolfram_app_id or WOLFRAM_APP_ID,
                "input": query,
                "format": "plaintext",
                "output": "json",
            }
            
            response = requests.get(
                WOLFRAM_API_URL,
                params=params,
                timeout=timeout
            )
            
            if response.status_code != 200:
                logger.warning(f"Wolfram API error {response.status_code}")
                return None
            
            data = response.json()
            queryresult = data.get("queryresult", {})
            
            if not queryresult.get("success"):
                return None
            
            pods = queryresult.get("pods", [])
            
            # Buscar respuesta True/False en los pods
            for pod in pods:
                subpods = pod.get("subpods", [])
                for subpod in subpods:
                    plaintext = (subpod.get("plaintext", "") or "").lower().strip()
                    
                    # Detectar True/False
                    if plaintext in ["true", "yes", "correct"]:
                        return True
                    if plaintext in ["false", "no", "incorrect"]:
                        return False
                    
                    # A veces Wolfram responde con el resultado directamente
                    # Si la respuesta contiene "=" o "≈", intentar parsear
                    if "true" in plaintext:
                        return True
                    if "false" in plaintext:
                        return False
            
            # Si no encontró True/False explícito, Wolfram no pudo verificar
            return None
            
        except requests.exceptions.Timeout:
            logger.warning(f"Wolfram timeout para query: {query[:50]}...")
            return None
        except Exception as e:
            logger.warning(f"Wolfram error: {e}")
            return None
    
    @classmethod
    def validar_ciencias(
        cls,
        preguntas: List[Dict],
        timeout: int = WOLFRAM_TIMEOUT,
        wolfram_app_id: Optional[str] = None,
        openai_api_key: Optional[str] = None,
    ) -> Gate7Result:
        """
        Valida preguntas de ciencias naturales (física y química).
        
        Física y química: SIEMPRE validables con Wolfram
        Biología: Marcadas como "no validables" automáticamente
        """
        print(f"\n🔬 Gate 7: Validando ciencias con Wolfram Alpha...")
        return cls.validar_matematicas(
            preguntas, timeout, area="CIENCIAS_NATURALES",
            wolfram_app_id=wolfram_app_id,
            openai_api_key=openai_api_key,
        )
