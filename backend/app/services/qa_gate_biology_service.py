
import os
import json
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field

# Intentar importar dependencias vectoriales (opcionales para no romper si faltan) ok
try:
    import chromadb
    from chromadb.utils import embedding_functions
    CHROMA_AVAILABLE = True
except ImportError:
    CHROMA_AVAILABLE = False

logger = logging.getLogger(__name__)

@dataclass
class BioIssue:
    pregunta_id: int
    nivel: str # "error" o "warning"
    mensaje: str
    evidencia: str # Texto del chunk que contradice o valida
    score_similitud: float

@dataclass
class GateBiologyResult:
    passed: bool = True
    issues: List[BioIssue] = field(default_factory=list)
    stats: Dict[str, Any] = field(default_factory=dict)

class GateBiologyValidator:
    """
    Gate 8 (Gate E): Validación de Biología usando RAG (Retrieval Augmented Generation).
    
    1. Detecta preguntas del componente BIOLÓGICO.
    2. Busca en la base de conocimientos curada (ChromaDB).
    3. Verifica consistencia científica usando un LLM Juez.
    """
    
    # Configuración
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    CHROMA_PATH = os.path.join(BASE_DIR, "data", "chroma_db")
    COLLECTION_NAME = "ciencias_naturales_biologia"
    SIMILARITY_THRESHOLD = 0.35  # Distancia coseno (más bajo = más similar en algunas métricas, cuidado con Chroma)
    
    @classmethod
    def validar_biologia(cls, preguntas: List[Dict], area: str) -> GateBiologyResult:
        result = GateBiologyResult()
        
        # Solo aplica para Ciencias Naturales
        if area != "CIENCIAS_NATURALES":
            return result
            
        if not CHROMA_AVAILABLE:
            logger.warning("⚠️ Gate Biología omitido: 'chromadb' no instalado.")
            result.stats["status"] = "skipped_missing_lib"
            return result

        if not os.path.exists(cls.CHROMA_PATH):
             logger.warning(f"⚠️ Gate Biología omitido: No existe DB en {cls.CHROMA_PATH}")
             result.stats["status"] = "skipped_no_db"
             return result

        # Iniciar Cliente Vectorial
        try:
            client = chromadb.PersistentClient(path=cls.CHROMA_PATH)
            openai_ef = embedding_functions.OpenAIEmbeddingFunction(
                api_key=os.getenv("OPENAI_API_KEY"),
                model_name="text-embedding-3-small"
            )
            collection = client.get_collection(name=cls.COLLECTION_NAME, embedding_function=openai_ef)
        except Exception as e:
            logger.error(f"Error conectando a ChromaDB: {e}")
            result.stats["error_db"] = str(e)
            return result

        from openai import OpenAI
        llm_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        preguntas_bio = []
        for p in preguntas:
            # Detección heurística de componente biológico
            comp = p.get("componente", "").lower()
            context = p.get("contexto", "").lower()
            if "bioló" in comp or "biolo" in comp or "célula" in context or "ecosistema" in context:
                preguntas_bio.append(p)

        result.stats["total_bio"] = len(preguntas_bio)
        print(f"\n🧬 Gate Bio: Validando {len(preguntas_bio)} preguntas contra Base de Conocimiento...")

        errores_bio = 0
        
        for p in preguntas_bio:
            try:
                # 1. Recuperar Contexto (RAG)
                query_text = f"{p.get('enunciado', '')} {p.get('opciones', '')}"
                
                search_results = collection.query(
                    query_texts=[query_text],
                    n_results=3
                )
                
                documents = search_results['documents'][0]
                metadatas = search_results['metadatas'][0]
                distances = search_results['distances'][0] # Ojo: Chroma usa distancia L2 o Coseno. Valor bajo = cercanía.

                # Construir Contexto Recuperado
                contexto_ref = "\n".join([f"- {doc} (Fuente: {meta.get('unit','')})" for doc, meta in zip(documents, metadatas)])
                
                # LOG VERBOSE: Mostrar qué encontró el RAG
                snippet = documents[0][:80] + "..." if documents else "No context found"
                print(f"   🔍 [Q{p.get('id')}] Contexto hallado: \"{snippet}\"")

                # 2. Juicio con LLM
                prompt_juez = f"""
ACTÚA COMO UN VERIFICADOR CIENTÍFICO ESTRICTO (BIOLOGÍA).

TIENES 3 FRAGMENTOS DE LA "BIBLIA" DEL CONTENIDO OFICIAL (CONTEXTO):
{contexto_ref}

ANALIZA ESTA PREGUNTA GENERADA:
ENUNCIADO: {p.get("enunciado")}
OPCIONES: {json.dumps(p.get("opciones"), ensure_ascii=False)}
RESPUESTA CORRECTA MARCADA: {p.get("respuesta_correcta")}

TAREA:
Determina si la PREGUNTA y su RESPUESTA CORRECTA son científicamente válidas según el contexto proporcionado.

REGLAS DE DECISIÓN (IMPORTANTE):
0. PRIORIDAD ABSOLUTA A LA EVIDENCIA INTERNA: Si la pregunta incluye un contexto específico, tabla, gráfico o datos experimentales, ASUME ESOS DATOS COMO VERDADEROS para el ejercicio. NO rechaces porque "el contexto teórico recuperado no lo menciona" si la evidencia está en los datos de la propia pregunta.
1. Si el contexto recuperado CONTIENE explícitamente la información y la pregunta la contradice DIRECTAMENTE -> RECHAZADO (Error científico).
2. Si el contexto recuperado NO MENCIONA el tema específico (ej. falta información sobre Fase G2) -> APROBADO (Beneficio de la duda). NO rechaces por falta de contexto externo.
3. Solo rechaza si hay una FALSEDAD CIENTÍFICA OBVIA y UNIVERSAL (ej. "el agua es seca", "los humanos ponen huevos") que no sea justificada por un contexto hipotético en el enunciado.

RESPONDE SOLO UN JSON:
{{
  "veredicto": "APROBADO" | "RECHAZADO",
  "razon": "Explicación breve",
  "evidencia_clave": "Cita del fragmento usado (o 'N/A' si no aplica)"
}}
"""
                resp = llm_client.chat.completions.create(
                    model="gpt-4o-mini", # Modelo rápido y barato para validación
                    messages=[{"role": "user", "content": prompt_juez}],
                    response_format={"type": "json_object"},
                    temperature=0
                )
                
                juicio = json.loads(resp.choices[0].message.content)
                
                if juicio.get("veredicto") == "RECHAZADO":
                    errores_bio += 1
                    msg = juicio.get("razon", "Error científico detectado")
                    evi = juicio.get("evidencia_clave", "")
                    
                    print(f"      ❌ RECHAZADO: {msg}")
                    
                    result.issues.append(BioIssue(
                        pregunta_id=p.get("id"),
                        nivel="error",
                        mensaje=msg,
                        evidencia=evi,
                        score_similitud=0.0
                    ))
                else:
                    print(f"      ✅ APROBADO")

            except Exception as e:
                logger.error(f"Error validando pregunta {p.get('id')}: {e}")
                continue

        result.stats["errores"] = errores_bio
        result.passed = (errores_bio == 0)
        
        if errores_bio == 0:
            print(f"   ✅ Gate Bio: PASSED - Conocimiento alineado.")
            
        return result
