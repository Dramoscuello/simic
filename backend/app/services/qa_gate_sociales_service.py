
import os
import json
import logging
from typing import List, Dict, Any
from dataclasses import dataclass, field

# Intentar importar dependencias
try:
    import chromadb
    from chromadb.utils import embedding_functions
    CHROMA_AVAILABLE = True
except ImportError:
    CHROMA_AVAILABLE = False

logger = logging.getLogger(__name__)

@dataclass
class SocialIssue:
    pregunta_id: int
    nivel: str # "error" o "warning"
    mensaje: str
    articulo_vulnerado: str # Ej: "Art. 86 (Tutela)"
    score_similitud: float

@dataclass
class GateSocialesResult:
    passed: bool = True
    issues: List[SocialIssue] = field(default_factory=list)
    stats: Dict[str, Any] = field(default_factory=dict)

class GateSocialesValidator:
    """
    Gate 10: Validación Constitucional y de Competencias Ciudadanas.
    Usa RAG contra la Constitución de 1991 y los Estándares Básicos.
    """
    
    # Configuración
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    CHROMA_PATH = os.path.join(BASE_DIR, "data", "chroma_db")
    COLLECTION_NAME = "sociales_ciudadanas_kb"
    
    @classmethod
    def validar_constitucionalidad(cls, preguntas: List[Dict], area: str) -> GateSocialesResult:
        result = GateSocialesResult()
        
        if area != "SOCIALES_CIUDADANAS":
            return result
            
        if not CHROMA_AVAILABLE or not os.path.exists(cls.CHROMA_PATH):
            logger.warning("⚠️ Gate Sociales omitido: ChromaDB no disponible.")
            result.stats["status"] = "skipped_no_infra"
            return result

        # Iniciar Cliente
        try:
            client = chromadb.PersistentClient(path=cls.CHROMA_PATH)
            openai_ef = embedding_functions.OpenAIEmbeddingFunction(
                api_key=os.getenv("OPENAI_API_KEY"),
                model_name="text-embedding-3-small"
            )
            collection = client.get_collection(name=cls.COLLECTION_NAME, embedding_function=openai_ef)
        except Exception as e:
            logger.error(f"Error conectando a Chroma Sociales: {e}")
            result.stats["error_db"] = str(e)
            return result

        from openai import OpenAI
        llm_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        print(f"\n⚖️ Gate Constitucional: Auditando {len(preguntas)} preguntas...")
        
        errores_const = 0
        
        for p in preguntas:
            try:
                # 1. Recuperar Contexto Legal (RAG)
                # Buscamos conceptos clave en el enunciado y la justificación
                query_text = f"{p.get('tema', '')} {p.get('enunciado', '')} {p.get('justificacion', '')}"
                
                search_results = collection.query(
                    query_texts=[query_text],
                    n_results=3
                )
                
                documents = search_results['documents'][0]
                metadatas = search_results['metadatas'][0]
                
                # Filtrar solo documentos relevantes (Constitución tiene prioridad)
                contexto_legal = ""
                for doc, meta in zip(documents, metadatas):
                    fuente = meta.get('source', 'Documento')
                    contexto_legal += f"- [{fuente}]: {doc[:300]}...\n"

                # 2. Juicio con LLM (Magistrado Auxiliar)
                prompt_juez = f"""
ACTÚA COMO UN MAGISTRADO DE LA CORTE CONSTITUCIONAL DE COLOMBIA CON FORMACIÓN EN CIENCIAS SOCIALES.
Tu misión es bloquear preguntas inválidas, aplicando criterios diferencidos según el tipo de pregunta.

CONTEXTO JURÍDICO OFICIAL (RAG - SOLO APLICAR SI ES PERTINENTE):
{contexto_legal}

PREGUNTA A AUDITAR:
Tema: {p.get("tema")}
Enunciado: {p.get("enunciado")}
Opciones: {json.dumps(p.get("opciones"), ensure_ascii=False)}
Respuesta Correcta: {p.get("respuesta_correcta")}
Justificación dada: {p.get("justificacion")}

INSTRUCCIONES DE EVALUACIÓN:
1. CLASIFICA la pregunta: ¿Es de "Competencia Ciudadana/Derecho" o de "Historia/Geografía/Economía"?

2. SI ES DE CIUDADANÍA/DERECHO/POLÍTICA ACTUAL:
   - Aplica RIGOR CONSTITUCIONAL TOTAL.
   - La respuesta DEBE alinearse con la Constitución de 1991.
   - RECHAZA si contradice derechos fundamentales o mecanismos de participación.

3. SI ES DE HISTORIA/GEOGRAFÍA/ECONOMÍA:
   - NO juzgues el pasado con la Constitución de 1991 (evita anacronismos).
   - Valida la OBJETIVIDAD HISTÓRICA y la lógica causal.
   - RECHAZA solo si hay sesgo ideológico evidente (ej: "el partido X fue el mejor") o falsedad histórica grave.

CRITERIOS DE RECHAZO (FATAL ERRORS):
1. INCONSTITUCIONALIDAD (Solo para temas ciudadanos): Contradice la norma vigente.
2. SESGO IDEOLÓGICO (Para todos): Toma partido explícito, usa adjetivos peyorativos ("el tirano X"), o adoctrina.
3. FALSEDAD JURÍDICA O HISTÓRICA: Inventa leyes o hechos.

VEREDICTO (JSON):
{{
  "clasificacion": "CIUDADANIA" | "DISCIPLINAR",
  "estado": "APROBADO" | "RECHAZADO",
  "causa": "Breve explicación del fallo o aprobación",
  "articulo_cita": "Si aplica (N/A para Historia)"
}}
"""
                resp = llm_client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": prompt_juez}],
                    response_format={"type": "json_object"},
                    temperature=0
                )
                
                juicio = json.loads(resp.choices[0].message.content)
                
                if juicio.get("estado") == "RECHAZADO":
                    errores_const += 1
                    msg = juicio.get("causa", "Error constitucional detectado")
                    art = juicio.get("articulo_cita", "Principios Generales")
                    
                    print(f"      ❌ RECHAZADA [Q{p.get('id')}]: {msg} ({art})")
                    
                    result.issues.append(SocialIssue(
                        pregunta_id=p.get("id"),
                        nivel="error",
                        mensaje=msg,
                        articulo_vulnerado=art,
                        score_similitud=0.0
                    ))
                # else:
                #     print(f"      ✅ APROBADA [Q{p.get('id')}]")

            except Exception as e:
                logger.error(f"Error validando pregunta {p.get('id')}: {e}")
                continue

        result.stats["errores"] = errores_const
        result.passed = (errores_const == 0)
        
        if errores_const == 0:
            print(f"   ✅ Gate Constitucional: SIN NOVEDAD. Todas las preguntas se ajustan a derecho.")
            
        return result
