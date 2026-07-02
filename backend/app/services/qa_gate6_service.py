"""
Gate 6: QA Lógico (Versión Light)
=================================
Validaciones de coherencia lógica que se pueden hacer sin parser matemático.

Checks implementados:
- Opciones únicas (no duplicadas)
- Respuesta correcta válida y no vacía
- Detección de placeholders en opciones
- Coherencia básica de justificación
- Detección de patrones sospechosos

Nota: La validación matemática completa requiere IA o SymPy,
lo cual se implementará cuando se conecte la API del LLM.
"""

import re
from typing import Dict, List, Set
from dataclasses import dataclass, field


@dataclass
class LogicIssue:
    """Representa un problema lógico detectado"""
    pregunta_id: int
    nivel: str  # "error" o "warning"
    tipo: str   # Categoría del problema
    mensaje: str


@dataclass
class Gate6Result:
    """Resultado de la validación de Gate 6"""
    passed: bool = True
    issues: List[LogicIssue] = field(default_factory=list)
    stats: Dict = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        return {
            "passed": self.passed,
            "issues": [
                {
                    "pregunta_id": i.pregunta_id,
                    "nivel": i.nivel,
                    "tipo": i.tipo,
                    "mensaje": i.mensaje
                }
                for i in self.issues
            ],
            "stats": self.stats
        }


class Gate6LogicValidator:
    """
    Validación lógica ligera para simulacros
    
    Uso:
        result = Gate6LogicValidator.validar_logica(contenido["preguntas"])
        if not result.passed:
            raise HTTPException(400, detail=result.to_dict())
    """
    
    # Patrones sospechosos en texto
    PLACEHOLDERS = [
        r'\[TODO\]',
        r'\[.*insertar.*\]',
        r'\.\.\.$',              # Termina en ...
        r'^\.\.\.?$',            # Solo puntos
        r'XXX',
        r'\[PENDIENTE\]',
        r'\?{3,}',               # ???
    ]
    
    # Palabras que deberían aparecer en justificación para la respuesta correcta
    CONEXIONES_JUSTIFICACION = {
        'A': ['a', 'primera', 'opción a'],
        'B': ['b', 'segunda', 'opción b'],
        'C': ['c', 'tercera', 'opción c'],
        'D': ['d', 'cuarta', 'opción d'],
    }
    
    @classmethod
    def validar_logica(cls, preguntas: List[Dict]) -> Gate6Result:
        """
        Valida coherencia lógica de las preguntas.
        """
        result = Gate6Result()
        result.stats["total_preguntas"] = len(preguntas)
        result.stats["opciones_duplicadas"] = 0
        result.stats["placeholders_detectados"] = 0
        result.stats["justificaciones_debiles"] = 0
        
        for pregunta in preguntas:
            pregunta_id = pregunta.get("id", 0)
            opciones = pregunta.get("opciones", [])
            respuesta_correcta = pregunta.get("respuesta_correcta", "")
            justificacion = pregunta.get("justificacion", "")
            
            # Check 1: Opciones únicas
            cls._verificar_opciones_unicas(pregunta_id, opciones, result)
            
            # Check 2: Respuesta correcta válida
            cls._verificar_respuesta_correcta(pregunta_id, opciones, respuesta_correcta, result)
            
            # Check 3: Detección de placeholders
            cls._detectar_placeholders(pregunta_id, pregunta, result)
            
            # Check 4: Coherencia de justificación
            cls._verificar_justificacion(pregunta_id, respuesta_correcta, justificacion, opciones, result)
        
        # El gate pasa si no hay errores
        result.passed = not any(i.nivel == "error" for i in result.issues)
        
        return result
    
    @classmethod
    def _verificar_opciones_unicas(cls, pregunta_id: int, opciones: List, result: Gate6Result):
        """Verifica que no haya opciones duplicadas"""
        textos = []
        
        for opt in opciones:
            if isinstance(opt, dict):
                texto = opt.get("texto", "").strip().lower()
            else:
                texto = str(opt).strip().lower()
            textos.append(texto)
        
        # Buscar duplicados
        vistos: Set[str] = set()
        duplicados: Set[str] = set()
        
        for t in textos:
            if t and t in vistos:
                duplicados.add(t)
            vistos.add(t)
        
        if duplicados:
            result.stats["opciones_duplicadas"] += 1
            result.issues.append(LogicIssue(
                pregunta_id=pregunta_id,
                nivel="error",
                tipo="opciones_duplicadas",
                mensaje=f"Hay opciones duplicadas: {list(duplicados)[:2]}"
            ))
    
    @classmethod
    def _verificar_respuesta_correcta(cls, pregunta_id: int, opciones: List, respuesta: str, result: Gate6Result):
        """Verifica que la respuesta correcta sea válida"""
        
        # Ya está validado en Gate 2 que sea A/B/C/D, aquí verificamos contenido
        if respuesta not in {'A', 'B', 'C', 'D'}:
            return  # Ya lo atrapa Gate 2
        
        # Encontrar la opción marcada como correcta
        opcion_correcta = None
        for opt in opciones:
            if isinstance(opt, dict) and opt.get("id") == respuesta:
                opcion_correcta = opt.get("texto", "")
                break
        
        if opcion_correcta is not None:
            # Verificar que no esté vacía
            if not opcion_correcta.strip():
                result.issues.append(LogicIssue(
                    pregunta_id=pregunta_id,
                    nivel="error",
                    tipo="respuesta_vacia",
                    mensaje=f"La opción {respuesta} (respuesta correcta) está vacía"
                ))
    
    @classmethod
    def _detectar_placeholders(cls, pregunta_id: int, pregunta: Dict, result: Gate6Result):
        """Detecta placeholders o texto incompleto"""
        
        campos_a_revisar = [
            ("contexto", pregunta.get("contexto", "")),
            ("enunciado", pregunta.get("enunciado", "")),
            ("justificacion", pregunta.get("justificacion", "")),
        ]
        
        # Agregar opciones
        for opt in pregunta.get("opciones", []):
            if isinstance(opt, dict):
                campos_a_revisar.append((f"opcion_{opt.get('id', '?')}", opt.get("texto", "")))
        
        for campo, texto in campos_a_revisar:
            if not texto:
                continue
            
            for patron in cls.PLACEHOLDERS:
                if re.search(patron, texto, re.IGNORECASE):
                    result.stats["placeholders_detectados"] += 1
                    result.issues.append(LogicIssue(
                        pregunta_id=pregunta_id,
                        nivel="error",
                        tipo="placeholder",
                        mensaje=f"Placeholder detectado en '{campo}': patrón '{patron}'"
                    ))
                    break  # Solo reportar uno por campo
    
    @classmethod
    def _verificar_justificacion(cls, pregunta_id: int, respuesta: str, justificacion: str, opciones: List, result: Gate6Result):
        """Verifica coherencia básica de la justificación"""
        
        if not justificacion or not justificacion.strip():
            result.issues.append(LogicIssue(
                pregunta_id=pregunta_id,
                nivel="warning",
                tipo="justificacion_vacia",
                mensaje="La justificación está vacía"
            ))
            return
        
        # Obtener texto de la opción correcta
        texto_correcto = ""
        for opt in opciones:
            if isinstance(opt, dict) and opt.get("id") == respuesta:
                texto_correcto = opt.get("texto", "").lower()
                break
        
        # Verificar si la justificación menciona algo relacionado con la respuesta
        justificacion_lower = justificacion.lower()
        
        # Buscar si menciona palabras clave de la opción correcta
        if texto_correcto:
            # Extraer palabras significativas (>4 caracteres) de la opción correcta
            palabras_clave = [p for p in texto_correcto.split() if len(p) > 4]
            
            # Verificar si al menos una palabra clave aparece en la justificación
            coincidencias = [p for p in palabras_clave if p in justificacion_lower]
            
            if not coincidencias and len(palabras_clave) > 0:
                result.stats["justificaciones_debiles"] += 1
                result.issues.append(LogicIssue(
                    pregunta_id=pregunta_id,
                    nivel="warning",
                    tipo="justificacion_debil",
                    mensaje=f"La justificación no parece explicar por qué '{respuesta}' es correcta"
                ))
