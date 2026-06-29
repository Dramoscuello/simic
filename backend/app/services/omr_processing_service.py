"""
Servicio de Procesamiento de Hojas OMR (OMR Processing Service)
================================================================
Utiliza Claude Vision para leer hojas de respuestas escaneadas/fotografiadas.

Flujo:
1. Recibe imagen (base64)
2. Claude Vision analiza:
   - Código QR (simulacro_id, estudiante_id)
   - Marcas en cada pregunta (A/B/C/D)
3. Retorna respuestas estructuradas

Por ahora: Solo extracción, sin guardado en BD.
"""
import os
import base64
import json
import time
from typing import Dict, Any, List, Optional, Tuple
from anthropic import Anthropic

# Configuración
ANTHROPIC_API_KEY = os.getenv("CLAUDE_API_KEY", "")
MODEL_VISION = "claude-sonnet-4-20250514"  # Modelo con capacidad de visión


class OMRProcessingService:
    """Servicio para procesar hojas de respuestas OMR usando Claude Vision."""
    
    def __init__(self):
        if not ANTHROPIC_API_KEY:
            raise ValueError("CLAUDE_API_KEY no configurada")
        self.client = Anthropic(api_key=ANTHROPIC_API_KEY)
    
    def process_single_sheet(
        self, 
        image_data: bytes, 
        content_type: str,
        num_preguntas: int = 35
    ) -> Dict[str, Any]:
        """
        Procesa una única hoja OMR.
        
        Args:
            image_data: Bytes de la imagen
            content_type: Tipo MIME (image/jpeg, image/png, etc.)
            num_preguntas: Número esperado de preguntas
            
        Returns:
            Dict con las respuestas extraídas y metadatos
        """
        print(f"\n📋 [OMRProcessing] Iniciando análisis de hoja OMR...")
        start_time = time.time()
        
        # Convertir a base64
        image_base64 = base64.standard_b64encode(image_data).decode("utf-8")
        
        # Mapear content type a media type de Anthropic
        media_type = self._normalize_media_type(content_type)
        
        # Prompt del sistema para extracción estructurada
        system_prompt = """Eres un experto lector de hojas de respuestas OMR (Optical Mark Recognition).
Tu tarea es analizar la imagen de una hoja de respuestas y extraer:

1. **Información del QR y Estudiante**: 
   - El código QR principal contiene datos en formato: SIM:123|EST:456|FECHA:20260204
     Donde SIM es el ID del simulacro y EST es el ID del estudiante
   - También hay un campo "Documento:" visible en la hoja con el número de identificación del estudiante
   - Extrae AMBOS: el estudiante_id del QR (EST:...) y el número de documento visible
   
2. **Respuestas marcadas**: Para cada pregunta, identifica cuál opción está marcada (A, B, C o D).
   - Si no hay marca clara, indica "sin_respuesta"
   - Si hay múltiples marcas, indica "multiple"

IMPORTANTE:
- Sé preciso. Una marca es válida si está claramente rellenada (>50% del óvalo) o tiene una X.
- Las hojas tienen formato de columnas con preguntas numeradas.
- El QR principal está en la sección del estudiante (arriba a la derecha).
- El nombre del estudiante aparece junto a "ESTUDIANTE:" en la hoja.

Responde ÚNICAMENTE en formato JSON válido con esta estructura:
{
    "qr_detectado": true/false,
    "qr_datos": {
        "simulacro_id": número o null (extraído del QR como SIM:X),
        "estudiante_id": número o null (puede ser el EST:X del QR o el número de documento),
        "estudiante_nombre": "string" o null (el nombre visible en la hoja)
    },
    "respuestas": {
        "1": "A" | "B" | "C" | "D" | "sin_respuesta" | "multiple",
        "2": "A" | "B" | "C" | "D" | "sin_respuesta" | "multiple",
        ...
    },
    "confianza_general": 0.0 a 1.0,
    "observaciones": "string con notas si hay problemas"
}"""

        user_prompt = f"""Analiza esta hoja de respuestas OMR.
La hoja debería tener {num_preguntas} preguntas.
Extrae toda la información del QR y las respuestas marcadas.

Devuelve SOLO el JSON, sin texto adicional ni markdown."""

        try:
            message = self.client.messages.create(
                model=MODEL_VISION,
                max_tokens=2000,
                temperature=0,  # Temperatura 0 para máxima precisión
                system=system_prompt,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": media_type,
                                    "data": image_base64
                                }
                            },
                            {
                                "type": "text",
                                "text": user_prompt
                            }
                        ]
                    }
                ]
            )
            
            # Extraer respuesta
            raw_response = message.content[0].text
            
            # Parsear JSON
            result = self._parse_response(raw_response)
            
            duration = time.time() - start_time
            print(f"   ✅ Análisis completado en {duration:.2f}s")
            print(f"   📊 QR detectado: {result.get('qr_detectado', False)}")
            print(f"   📝 Respuestas extraídas: {len(result.get('respuestas', {}))}")
            
            return {
                "success": True,
                "data": result,
                "processing_time": duration
            }
            
        except Exception as e:
            duration = time.time() - start_time
            print(f"   ❌ Error procesando hoja: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "processing_time": duration
            }
    
    def process_batch(
        self,
        images: List[Tuple[bytes, str, str]],  # (data, content_type, filename)
        num_preguntas: int = 35
    ) -> List[Dict[str, Any]]:
        """
        Procesa múltiples hojas OMR.
        
        Args:
            images: Lista de tuplas (image_data, content_type, filename)
            num_preguntas: Número esperado de preguntas por hoja
            
        Returns:
            Lista de resultados, uno por imagen
        """
        print(f"\n📋 [OMRProcessing] Procesando lote de {len(images)} hojas...")
        results = []
        
        for i, (image_data, content_type, filename) in enumerate(images):
            print(f"\n   [{i+1}/{len(images)}] Procesando: {filename}")
            result = self.process_single_sheet(image_data, content_type, num_preguntas)
            result["filename"] = filename
            result["index"] = i
            results.append(result)
        
        # Resumen
        successful = sum(1 for r in results if r["success"])
        print(f"\n✅ [OMRProcessing] Lote completado: {successful}/{len(images)} exitosos")
        
        return results
    
    def _normalize_media_type(self, content_type: str) -> str:
        """Normaliza el content type para Anthropic."""
        mapping = {
            "image/jpeg": "image/jpeg",
            "image/jpg": "image/jpeg",
            "image/png": "image/png",
            "image/webp": "image/webp",
            "image/gif": "image/gif",
        }
        return mapping.get(content_type.lower(), "image/jpeg")
    
    def _parse_response(self, raw_response: str) -> Dict[str, Any]:
        """Parsea la respuesta de Claude a JSON."""
        # Intentar parsear directamente
        try:
            return json.loads(raw_response)
        except json.JSONDecodeError:
            pass
        
        # Intentar extraer JSON de markdown code blocks
        import re
        json_pattern = r'```(?:json)?\s*([\s\S]*?)```'
        match = re.search(json_pattern, raw_response)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                pass
        
        # Intentar encontrar el primer { y último }
        start = raw_response.find('{')
        end = raw_response.rfind('}')
        if start != -1 and end != -1:
            try:
                return json.loads(raw_response[start:end+1])
            except json.JSONDecodeError:
                pass
        
        # Fallback: retornar estructura vacía con error
        return {
            "qr_detectado": False,
            "qr_datos": {"simulacro_id": None, "estudiante_id": None, "estudiante_nombre": None},
            "respuestas": {},
            "confianza_general": 0.0,
            "observaciones": f"Error parseando respuesta: {raw_response[:200]}"
        }
