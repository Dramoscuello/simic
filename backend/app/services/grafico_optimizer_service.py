"""
Servicio de Optimización de Gráficos SVG
=========================================
Usa Anthropic Claude 3.5 Sonnet con visión para analizar y corregir gráficos SVG
que no se renderizan correctamente.
"""
import os
import json
import base64
from typing import Dict, Any, Optional
from anthropic import Anthropic

# Configuración de claves
CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY", "")
# Usamos el modelo especificado por el usuario (Claude 4.5 Opus)
MODEL_NAME = "claude-opus-4-5-20251101" 


class OptimizacionResult:
    """Resultado de la optimización de un gráfico"""
    def __init__(self, success: bool, svg_spec: Optional[Dict] = None, error: Optional[str] = None):
        self.success = success
        self.svg_spec = svg_spec
        self.error = error
        self.tokens_used = 0


class GraficoOptimizer:
    """
    Optimizador de gráficos SVG usando Claude 3.5 Sonnet.
    
    Flujo:
    1. Recibe la imagen renderizada del SVG (capturada en frontend)
    2. Recibe el svg_spec actual
    3. Recibe el contexto de la pregunta
    4. Llama a Claude con visión
    5. Devuelve un svg_spec corregido
    """
    
    @classmethod
    def optimizar(
        cls,
        imagen_base64: str,
        svg_spec_actual: Dict[str, Any],
        contexto_pregunta: str,
        enunciado_pregunta: str,
        area: str,
        instrucciones_adicionales: Optional[str] = None,
        timeout: int = 60
    ) -> OptimizacionResult:
        """
        Optimiza un gráfico SVG usando visión de IA (Claude).
        """
        if not CLAUDE_API_KEY:
            # Fallback a OpenAI si no hay Claude key
            openai_key = os.getenv("OPENAI_API_KEY", "")
            if openai_key:
                print("⚠️ No se encontró CLAUDE_API_KEY, intentando con OpenAI como fallback...")
                # Aquí podrías llamar a una implementación de OpenAI si quisieras mantener compatibilidad
            
            return OptimizacionResult(
                success=False,
                error="CLAUDE_API_KEY no configurada"
            )
        
        # Construir el prompt de optimización
        prompt = cls._construir_prompt(
            svg_spec_actual=svg_spec_actual,
            contexto_pregunta=contexto_pregunta,
            enunciado_pregunta=enunciado_pregunta,
            area=area,
            instrucciones_adicionales=instrucciones_adicionales
        )
        
        try:
            client = Anthropic(api_key=CLAUDE_API_KEY)
            
            print(f"🎨 Optimizando gráfico SVG con Claude 4.5 Opus...")
            print(f"   Área: {area}")
            print(f"   Shapes actuales: {len(svg_spec_actual.get('shapes', []))}")
            
            # Preparar el mensaje para Anthropic
            # Anthropic espera "image/png" o "image/jpeg" en media_type
            media_type = "image/png" 
            
            message = client.messages.create(
                model=MODEL_NAME,
                max_tokens=4000,
                temperature=0.2, # Baja temperatura para precisión técnica
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": media_type,
                                    "data": imagen_base64
                                }
                            },
                            {
                                "type": "text",
                                "text": prompt
                            }
                        ]
                    }
                ]
            )
            
            # Obtener contenido de la respuesta
            content = message.content[0].text
            
            # Limpiar posible markdown json
            content_clean = content.replace("```json", "").replace("```", "").strip()
            
            try:
                result_json = json.loads(content_clean)
            except json.JSONDecodeError as e:
                return OptimizacionResult(
                    success=False,
                    error=f"Error parseando JSON de Claude: {str(e)}\nContenido parcial: {content[:100]}..."
                )
            
            # Extraer el svg_spec optimizado (adaptamos según la estructura que devuelve Claude)
            # Nuestro prompt pide { "analisis": ..., "svg_spec": ... }
            svg_spec_nuevo = result_json.get("svg_spec")
            
            if not svg_spec_nuevo:
                return OptimizacionResult(
                    success=False,
                    error="La respuesta no contiene 'svg_spec'"
                )
            
            if "shapes" not in svg_spec_nuevo:
                return OptimizacionResult(
                    success=False,
                    error="El svg_spec no contiene 'shapes'"
                )
            
            result = OptimizacionResult(success=True, svg_spec=svg_spec_nuevo)
            result.tokens_used = message.usage.input_tokens + message.usage.output_tokens
            
            print(f"   ✅ Optimización exitosa (Claude): {len(svg_spec_nuevo.get('shapes', []))} shapes")
            
            return result
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return OptimizacionResult(
                success=False,
                error=f"Error en optimización con Claude: {str(e)}"
            )
    
    @classmethod
    def _construir_prompt(
        cls,
        svg_spec_actual: Dict[str, Any],
        contexto_pregunta: str,
        enunciado_pregunta: str,
        area: str,
        instrucciones_adicionales: Optional[str] = None
    ) -> str:
        """Construye el prompt para la optimización"""
        
        # Mapeo de áreas a nombres legibles
        area_names = {
            "MATEMATICAS": "Matemáticas",
            "CIENCIAS_NATURALES": "Ciencias Naturales",
            "SOCIALES_CIUDADANAS": "Sociales y Ciudadanas",
            "LECTURA_CRITICA": "Lectura Crítica",
            "INGLES": "Inglés"
        }
        
        prompt = f"""Eres un experto en gráficos vectoriales SVG y visualización científica. Tu única tarea es analizar imágenes de SVGs defectuosos y regenerarlos corregidos y optimizados.

## Tu proceso de análisis:

1. **Interpretar la intención**: ¿Qué intenta representar este gráfico? Identifica el concepto visual independientemente de sus errores actuales (geometría, diagrama de fuerzas, gráfica estadística, esquema biológico, etc.).

2. **Detectar defectos**:
   - Proporciones distorsionadas o incorrectas
   - Elementos desalineados o mal posicionados
   - Superposición no intencional de elementos
   - Etiquetas/textos ilegibles o mal ubicados
   - Líneas que no conectan donde deberían
   - Formas incompletas o mal cerradas
   - Escala inconsistente entre elementos
   - Simetría rota donde debería existir
   - Flechas o direcciones incorrectas
   - Espaciado irregular
   - Elementos cortados o fuera del viewport
   - Contradicción con el contexto del problema (¡CRÍTICO!)

3. **Regenerar con precisión**: Crear un diseño limpio que represente correctamente la intención original.

## DATOS DE ENTRADA
**Contexto**: {contexto_pregunta}
**Pregunta**: {enunciado_pregunta}
**Pregunta**: {enunciado_pregunta}
"""

        if instrucciones_adicionales:
            prompt += f"""
## 🚨 ODEN SUPREMA DEL USUARIO (MÁXIMA PRIORIDAD) 🚨
El Experto Humano te da esta instrucción DIRECTA:
"{instrucciones_adicionales}"

⚠️ CRÍTICO:
1. Si esta instrucción contradice lo que ves en la imagen, **OBEDECE AL USUARIO**.
2. Si el usuario te pide dibujar algo que NO ves (ej: "conecta los puntos"), **HAZLO**. Asume las coordenadas basándote en la posición de las etiquetas o invéntalas lógicamente.
3. **NO** digas "no veo los puntos". ¡Tu trabajo es RECONSTRUIR lo que falta!
"""

        prompt += f"""
**SVG Spec Actual**:
```json
{json.dumps(svg_spec_actual, ensure_ascii=False, indent=2)}
```

## ESPECIFICACIONES TÉCNICAS OBLIGATORIAS

- **ViewBox**: Usar "0 0 400 300" (o ajustar si la proporción lo requiere)
- **Colores**: #333 (líneas principales), #666 (secundarias/cotas), #e74c3c (énfasis rojo), #3498db (énfasis azul)
- **Texto**: fontSize entre 12-16px. Posicionar etiquetas SIN superponer líneas.
- **Líneas**: stroke-width 2-3px principales, 1px auxiliares.
- **Coordenadas**: Usar números enteros ("Snap to grid") para alineación perfecta.
- **Ángulos Rectos**: Si el contexto implica 90° (paredes, altura), asegúralo visualmente y con marcadores.

## 🚫 REGLA ANTI-SPOILER (CRÍTICO) 🚫
1. **NUNCA** incluyas la respuesta, el resultado numérico final ni el desarrollo de la fórmula en el gráfico (ej: "Área = 30.28").
2. Solo etiqueta los **datos iniciales** dados en el enunciado (lados, ángulos, nombres).
3. El gráfico es para **PLANTEAR** el problema, no para resolverlo. ¡Si ves la solución, bórrala!

## FORMATO DE RESPUESTA (ADAPTADO A JSON)

Responde ÚNICAMENTE con un objeto JSON válido con esta estructura exacta.
NO devuelvas código SVG plano (<svg>...), usa nuestra estructura de primitiva `shapes`.

```json
{{
  "analisis": {{
    "interpretacion": "qué representa el gráfico",
    "defectos": ["lista de problemas encontrados"],
    "correccion_principal": "descripción de la solución"
  }},
  "svg_spec": {{
    "viewBox": "0 0 400 300",
    "shapes": [
      {{ "type": "rect", "x": 10, "y": 10, "width": 100, "height": 50, "stroke": "#333", "fill": "none" }},
      {{ "type": "line", "x1": 0, "y1": 0, "x2": 100, "y2": 100, "stroke": "#333", "stroke_width": 2 }},
      {{ "type": "circle", "cx": 50, "cy": 50, "r": 20, "fill": "#e74c3c" }},
      {{ "type": "text", "x": 50, "y": 60, "value": "Texto", "fontSize": 14, "fill": "#333" }},
      {{ "type": "arrow", "x1": 0, "y1": 0, "x2": 50, "y2": 50, "label": "Vector" }},
      {{ "type": "polygon", "points": "0,0 50,50 100,0", "fill": "none", "stroke": "#333" }},
      {{ "type": "path", "d": "M...", "stroke": "#333", "fill": "none" }}
    ]
  }}
}}
```

¡RECONSTRUYE EL GRÁFICO PARA QUE SEA PERFECTO, PROFESIONAL Y COHERENTE!
"""
        return prompt
