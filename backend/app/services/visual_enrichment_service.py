"""
Servicio de Enriquecimiento Visual (Visual Enrichment Service)
============================================================
Este servicio actúa como un "Estudio de Arte" intermedio.
Intercepta las preguntas generadas por el cerebro lógico (o3) y, si requieren
ilustraciones artísticas, se las encarga a un modelo especializado (Claude Opus).

Flujo:
1. Recibe lista de preguntas.
2. Detecta `tipo_grafico: "svg_artistico"`.
3. Extrae `descripcion_visual` y `estilo_sugerido`.
4. Llama a Claude Opus para generar el SVG.
5. Incrusta el código SVG resultante en `configuracion_grafico["svg_code"]`.
"""
import os
import time
import re
from typing import List, Dict, Any, Optional, Tuple
from anthropic import Anthropic

# Configuración
ANTHROPIC_API_KEY = os.getenv("CLAUDE_API_KEY", "")
MODEL_HEAVY = "claude-opus-4-5-20251101" # Modelo State-of-the-Art (2026)

class VisualEnrichmentService:
    @staticmethod
    def enrich_simulacro_questions(
        preguntas: List[Dict[str, Any]],
        area: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Procesa una lista de preguntas e inyecta SVGs artísticos donde sea necesario.
        Modifica la lista in-place.
        """
        print("\n🎨 [VisualEnrichment] Iniciando revisión de arte para el simulacro...")
        
        preguntas_con_arte = [p for p in preguntas if VisualEnrichmentService._needs_art(p)]
        total_arte = len(preguntas_con_arte)
        
        if total_arte == 0:
            print("   ✅ Ninguna pregunta requiere 'svg_artistico'. Saltando estudio de arte.")
            return preguntas

        print(f"   🖌️  Se detectaron {total_arte} preguntas que requieren ilustración.")
        
        # Inicializar cliente solo si es necesario
        if not ANTHROPIC_API_KEY:
            print("   ⚠️  ERROR: ANTHROPIC_API_KEY no encontrada. No se pueden generar ilustraciones.")
            return preguntas
            
        client = Anthropic(api_key=ANTHROPIC_API_KEY)
        
        for i, pregunta in enumerate(preguntas):
            if VisualEnrichmentService._needs_art(pregunta):
                print(f"   🎨 Dibujando ilustración para Pregunta ID {pregunta.get('id', '?')} ({i+1}/{len(preguntas)})...")
                VisualEnrichmentService._generate_svg_for_question(client, pregunta, area=area)
                
        print("✅ [VisualEnrichment] Proceso de enriquecimiento visual completado.\n")
        return preguntas

    @staticmethod
    def _needs_art(pregunta: Dict[str, Any]) -> bool:
        """Verifica si la pregunta solicita arte generativo."""
        return (
            pregunta.get("tiene_grafico") is True and 
            pregunta.get("tipo_grafico") == "svg_artistico" and
            isinstance(pregunta.get("configuracion_grafico"), dict) and
            "descripcion_visual" in pregunta["configuracion_grafico"]
        )

    @staticmethod
    def _generate_svg_for_question(
        client: Anthropic,
        pregunta: Dict[str, Any],
        area: Optional[str] = None
    ):
        """Genera el SVG usando Claude y lo guarda en la pregunta."""
        config = pregunta["configuracion_grafico"]
        descripcion = config.get("descripcion_visual", "")
        estilo = config.get("estilo_sugerido", "vector_plano")
        prompt_sistema, prompt_usuario = VisualEnrichmentService._build_svg_prompts(
            descripcion=descripcion,
            estilo=estilo,
            area=area,
            pregunta=pregunta
        )

        try:
            start_t = time.time()
            message = client.messages.create(
                model=MODEL_HEAVY,
                max_tokens=4000,
                temperature=0.2, # Baja temperatura para precisión en código
                system=prompt_sistema,
                messages=[
                    {"role": "user", "content": prompt_usuario}
                ]
            )
            
            raw_content = message.content[0].text
            svg_code = VisualEnrichmentService._clean_svg_response(raw_content)
            
            # Guardamos el resultado
            pregunta["configuracion_grafico"]["svg_code"] = svg_code
            
            duration = time.time() - start_t
            svg_size = len(svg_code)
            print(f"      ✨ SVG Generado en {duration:.1f}s ({svg_size} bytes).")
            
        except Exception as e:
            print(f"      ❌ Error generando arte: {str(e)}")
            # Fallback: No rompemos el flujo, la pregunta se queda sin svg_code (frontend deberá manejarlo)

    @staticmethod
    def _normalize_text(value: Any) -> str:
        if value is None:
            return ""
        text = str(value).strip().upper()
        replacements = {
            "Á": "A",
            "É": "E",
            "Í": "I",
            "Ó": "O",
            "Ú": "U",
            "Ü": "U",
            "Ñ": "N"
        }
        for src, dst in replacements.items():
            text = text.replace(src, dst)
        return text

    @staticmethod
    def _is_english_area(area: Optional[str], pregunta: Dict[str, Any]) -> bool:
        candidates = [
            area,
            pregunta.get("area"),
            pregunta.get("area_codigo"),
            pregunta.get("area_code")
        ]
        for candidate in candidates:
            normalized = VisualEnrichmentService._normalize_text(candidate)
            if not normalized:
                continue
            if "INGLES" in normalized or "ENGLISH" in normalized:
                return True
        return False

    @staticmethod
    def _build_svg_prompts(
        descripcion: str,
        estilo: str,
        area: Optional[str] = None,
        pregunta: Optional[Dict[str, Any]] = None
    ) -> Tuple[str, str]:
        pregunta = pregunta or {}
        is_english = VisualEnrichmentService._is_english_area(area, pregunta)

        if is_english:
            prompt_sistema = (
                "You are an expert technical and artistic SVG illustrator. "
                "Your goal is to create clean, pedagogical, and aesthetic vector graphics for educational exams.\n"
                "CRITICAL RULES:\n"
                "1. Do NOT use markdown fences like ```xml or ```svg. Return ONLY raw <svg> code.\n"
                "2. Default viewBox must be '0 0 400 300' unless another ratio is required.\n"
                "3. Use primitive shapes, smooth paths, and harmonious colors.\n"
                "4. Ensure high contrast and readable text.\n"
                "5. Keep the SVG optimized (no excessive comments).\n"
                "6. ANTI-SPOILER: NEVER include the numeric final answer in the graphic when it is unknown. "
                "Use labels like 'x', '?', 'α', or the corresponding variable.\n"
                "7. LANGUAGE LOCK: Any visible text inside the SVG (labels, dialogue bubbles, signs, captions) MUST be in English."
            )
            prompt_usuario = (
                f"Generate an SVG illustration with this style: '{estilo}'.\n"
                f"Scene description: {descripcion}\n"
                "Important: If the scene includes visible text, write it in English."
            )
            return prompt_sistema, prompt_usuario

        prompt_sistema = (
            "Eres un experto Ilustrador Técnico y Artístico especializado en SVG. "
            "Tu objetivo es crear gráficos vectoriales limpios, pedagógicos y estéticos para exámenes educativos.\n"
            "REGLAS CRÍTICAS:\n"
            "1. NO uses etiquetas markdown como ```xml o ```svg. Devuelve SOLO el código <svg>.\n"
            "2. El viewBox debe ser '0 0 400 300' a menos que la escena requiera otra proporción.\n"
            "3. Usa formas primitivas, paths suaves y colores armoniosos.\n"
            "4. Asegura alto contraste y legibilidad para textos.\n"
            "5. Optimiza el código (no comentarios excesivos).\n"
            "6. 🚫 ANTI-SPOILER: NUNCA incluyas el valor numérico de la respuesta en el gráfico si es una incógnita. "
            "Si la pregunta pide calcular un ángulo o lado, etiquétalo como 'x', '?', 'α' o la variable correspondiente, "
            "pero JAMÁS pongas el número resultado.\n"
            "7. IDIOMA: Si el SVG incluye texto visible, escríbelo en español."
        )
        prompt_usuario = (
            f"Genera una ilustración SVG con el siguiente estilo: '{estilo}'.\n"
            f"Descripción de la escena: {descripcion}\n"
            "Importante: Si incluyes texto visible en el SVG, debe estar en español."
        )
        return prompt_sistema, prompt_usuario

    @staticmethod
    def _clean_svg_response(content: str) -> str:
        """Limpia la respuesta para extraer solo el SVG."""
        # Buscar patrón <svg ... </svg>
        pattern = r"(<svg[\s\S]*?<\/svg>)"
        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            return match.group(1)
        return content # Retornar todo si no se encuentra patrón (quizás Claude devolvió solo el código)
