"""
Servicio de Generación de Simulacros con selección de modelo.
=============================================================
Soporta generación con:
1. OpenAI o3
2. Claude Sonnet 4.6

Construye el prompt enriquecido combinando:
1. Prompt base del área
2. Contexto curado (marco de referencia, niveles, ejemplos)
3. Preguntas ya usadas para evitar duplicados
"""
import os
import json
from typing import List, Dict, Optional, Tuple, Any
from openai import OpenAI
from sqlalchemy.orm import Session

# Configuración de modelos y proveedores (todo desde variables de entorno)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "")
DEFAULT_GENERATION_MODEL = os.getenv("DEFAULT_GENERATION_MODEL", "o3")
CLAUDE_MODEL_NAME = "claude-sonnet-4-6"


def is_openai_model(modelo_codigo: str) -> bool:
    if not modelo_codigo:
        return False
    lower = modelo_codigo.lower()
    # Modelos oficiales de OpenAI
    if lower.startswith("gpt-") or lower.startswith("o1") or lower.startswith("o3") or lower.startswith("text-"):
        return True
    # Cualquier modelo se considera OpenAI-compatible si se configura un endpoint personalizado (p. ej. Ollama)
    if OPENAI_BASE_URL:
        return True
    return False


def is_claude_model(modelo_codigo: str) -> bool:
    if not modelo_codigo:
        return False
    return modelo_codigo.lower().startswith("claude-")

# Rutas base
# Este archivo está en backend/app/services/generation_service.py
# Necesitamos llegar a backend/static (2 niveles arriba de services, luego static)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # backend/
STATIC_DIR = os.path.join(BASE_DIR, "static")

# Mapeo de áreas a carpetas
AREA_FOLDERS = {
    "CIENCIAS_NATURALES": "ciencias_naturales",
    "MATEMATICAS": "matematicas",
    "SOCIALES_CIUDADANAS": "sociales",  # Carpeta real es 'sociales'
    "LECTURA_CRITICA": "lectura_critica",
    "INGLES": "ingles"
}

# Mapeo de áreas a nombres legibles
AREA_NAMES = {
    "CIENCIAS_NATURALES": "Ciencias Naturales",
    "MATEMATICAS": "Matemáticas",
    "SOCIALES_CIUDADANAS": "Sociales y Ciudadanas",
    "LECTURA_CRITICA": "Lectura Crítica",
    "INGLES": "Inglés"
}


class GenerationResult:
    """Resultado de la generación de un simulacro"""
    def __init__(self, success: bool, data: Optional[Dict] = None, error: Optional[str] = None):
        self.success = success
        self.data = data  # JSON del simulacro generado
        self.error = error
        self.tokens_used = 0
        self.generation_time = 0
    
    def to_dict(self):
        return {
            "success": self.success,
            "data": self.data,
            "error": self.error,
            "tokens_used": self.tokens_used,
            "generation_time": self.generation_time
        }


class SimulacroGenerator:
    """
    Generador de simulacros usando OpenAI.
    
    Uso:
        result = SimulacroGenerator.generar(
            area="CIENCIAS_NATURALES",
            institucion_id=5,
            db=db_session
        )
        
        if result.success:
            simulacro_json = result.data
        else:
            print(f"Error: {result.error}")
    """
    
    @classmethod
    def _capture_prompt(cls, area: str, content: str, stage: str = "main"):
        """Captura el prompt en un archivo de texto para debugging/pruebas."""
        return 0
        try:
            from datetime import datetime
            dump_dir = os.path.join(BASE_DIR, "dumps")
            os.makedirs(dump_dir, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"prompt_{area}_{stage}_{timestamp}.txt"
            filepath = os.path.join(dump_dir, filename)
            
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
                
            print(f"      Prompt capturado en: {filename}")
        except Exception as e:
            print(f"       No se pudo capturar prompt: {e}")

    @classmethod
    def _normalize_generation_model(cls, generation_model: Optional[str]) -> str:
        model = (generation_model or DEFAULT_GENERATION_MODEL).strip()
        if is_openai_model(model) or is_claude_model(model):
            return model
        raise ValueError(
            f"Modelo de generación no soportado: {model}. "
            f"Modelos válidos: modelos OpenAI (gpt-, o1, o3) o Anthropic Claude (claude-)"
        )

    @classmethod
    def _ensure_model_api_key(cls, generation_model: str) -> None:
        if is_openai_model(generation_model) and not OPENAI_API_KEY.strip():
            raise ValueError("OPENAI_API_KEY no está configurada")
        if is_claude_model(generation_model) and not os.getenv("CLAUDE_API_KEY", "").strip():
            raise ValueError("CLAUDE_API_KEY no está configurada")

    @classmethod
    def _extract_anthropic_text(cls, response: Any) -> str:
        content_blocks = getattr(response, "content", None) or []
        text_parts: List[str] = []

        for block in content_blocks:
            block_type = getattr(block, "type", None)
            if block_type == "text":
                text_parts.append(getattr(block, "text", "") or "")
                continue

            if isinstance(block, dict) and block.get("type") == "text":
                text_parts.append(block.get("text", "") or "")

        raw = "".join(text_parts).strip()
        if not raw:
            raise ValueError("La respuesta de Claude llegó vacía o sin bloques de texto")
        return raw

    @classmethod
    def _extract_json_from_text(cls, raw_content: str, context_label: str = "respuesta") -> Any:
        if not raw_content or not raw_content.strip():
            raise ValueError(f"La {context_label} del modelo llegó vacía")

        raw = raw_content.strip()

        # 1) Intento directo
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            pass

        # 2) Bloque fenced ```json ... ```
        import re

        fenced_match = re.search(r"```(?:json)?\s*([\s\S]*?)```", raw, re.IGNORECASE)
        if fenced_match:
            candidate = fenced_match.group(1).strip()
            try:
                return json.loads(candidate)
            except json.JSONDecodeError:
                pass

        # 3) Buscar primer objeto/array JSON válido dentro del texto
        decoder = json.JSONDecoder()
        for idx, char in enumerate(raw):
            if char not in "{[":
                continue
            try:
                parsed, _ = decoder.raw_decode(raw[idx:])
                return parsed
            except json.JSONDecodeError:
                continue

        snippet = raw[:220].replace("\n", " ")
        raise ValueError(f"No se pudo extraer JSON válido desde la {context_label}. Inicio: {snippet}...")

    @classmethod
    def _llm_complete_text(
        cls,
        prompt: str,
        generation_model: str,
        timeout: int,
        expect_json: bool = False,
    ) -> Tuple[str, int, Optional[str]]:
        model = cls._normalize_generation_model(generation_model)
        cls._ensure_model_api_key(model)

        api_key = OPENAI_API_KEY if is_openai_model(model) else os.getenv("CLAUDE_API_KEY", "").strip()

        if is_openai_model(model):
            client_kwargs: Dict[str, Any] = {"api_key": api_key}
            if OPENAI_BASE_URL:
                client_kwargs["base_url"] = OPENAI_BASE_URL
            client = OpenAI(**client_kwargs)
            kwargs: Dict[str, Any] = {
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "timeout": timeout,
            }
            if expect_json:
                kwargs["response_format"] = {"type": "json_object"}

            response = client.chat.completions.create(**kwargs)
            content = (response.choices[0].message.content or "").strip()
            usage = response.usage
            tokens = getattr(usage, "total_tokens", 0) if usage else 0
            finish_reason = response.choices[0].finish_reason
            return content, tokens, finish_reason

        from anthropic import Anthropic

        client = Anthropic(
            api_key=api_key,
            timeout=timeout,
        )
        req: Dict[str, Any] = {
            "model": model,
            "max_tokens": 8192,
            "temperature": 0,
            "messages": [{"role": "user", "content": prompt}],
        }
        if expect_json:
            req["system"] = "Responde únicamente un JSON válido, sin texto extra."

        response = client.messages.create(**req)
        content = cls._extract_anthropic_text(response)
        usage = getattr(response, "usage", None)
        tokens = 0
        if usage:
            tokens += int(getattr(usage, "input_tokens", 0) or 0)
            tokens += int(getattr(usage, "output_tokens", 0) or 0)
        finish_reason = getattr(response, "stop_reason", None)
        return content, tokens, finish_reason

    @classmethod
    def _llm_complete_json(
        cls,
        prompt: str,
        generation_model: str,
        timeout: int,
        context_label: str = "respuesta",
    ) -> Tuple[Any, int, Optional[str], str]:
        raw_content, tokens, finish_reason = cls._llm_complete_text(
            prompt=prompt,
            generation_model=generation_model,
            timeout=timeout,
            expect_json=True,
        )
        parsed = cls._extract_json_from_text(raw_content, context_label=context_label)
        return parsed, tokens, finish_reason, raw_content

    @classmethod
    def _chunk_size_for_model(
        cls,
        generation_model: str,
        default_chunk_size: int,
        sonnet_chunk_size: int = 10,
    ) -> int:
        model = cls._normalize_generation_model(generation_model)
        if is_claude_model(model):
            return min(default_chunk_size, sonnet_chunk_size)
        return default_chunk_size

    @classmethod
    def _is_expected_finish_reason(
        cls,
        generation_model: str,
        finish_reason: Optional[str],
    ) -> bool:
        if not finish_reason:
            return True
        model = cls._normalize_generation_model(generation_model)
        if is_openai_model(model):
            return finish_reason == "stop"
        return finish_reason in {"end_turn", "stop_sequence", "stop"}

    @classmethod
    def _should_retry_for_finish_reason(
        cls,
        generation_model: str,
        finish_reason: Optional[str],
    ) -> bool:
        model = cls._normalize_generation_model(generation_model)
        return is_claude_model(model) and finish_reason == "max_tokens"

    @classmethod
    def generar(
        cls,
        area: str,
        institucion_id: int,
        db: Session,
        num_preguntas: int = 30,
        timeout: int = 300,
        dificultad: dict = None,  # {facil: 30, medio: 40, dificil: 30}
        generation_model: Optional[str] = None,
    ) -> GenerationResult:
        """
        Genera un simulacro completo para un área específica.
        
        Args:
            area: Código del área (CIENCIAS_NATURALES, MATEMATICAS, etc.)
            institucion_id: ID de la institución para filtrar preguntas usadas
            db: Sesión de base de datos
            num_preguntas: Número de preguntas a generar (default 30)
            timeout: Timeout en segundos para la llamada API
            
        Returns:
            GenerationResult con el JSON del simulacro o error
        """
        import time
        start_time = time.time()
        
        # Validar área
        if area not in AREA_FOLDERS:
            return GenerationResult(
                success=False,
                error=f"Área no soportada: {area}. Áreas válidas: {list(AREA_FOLDERS.keys())}"
            )
        
        try:
            generation_model = cls._normalize_generation_model(generation_model)
            cls._ensure_model_api_key(generation_model)

            # 0. Pipelines Especiales
            if area == "LECTURA_CRITICA":
                return cls._generar_pipeline_lectura_critica(
                    area,
                    institucion_id,
                    db,
                    num_preguntas,
                    dificultad,
                    timeout,
                    generation_model=generation_model,
                )
            
            if area == "MATEMATICAS":
                return cls._generar_pipeline_matematicas(
                    area,
                    institucion_id,
                    db,
                    num_preguntas,
                    dificultad,
                    timeout,
                    generation_model=generation_model,
                )
            
            if area == "CIENCIAS_NATURALES":
                return cls._generar_pipeline_ciencias_naturales(
                    area,
                    institucion_id,
                    db,
                    num_preguntas,
                    dificultad,
                    timeout,
                    generation_model=generation_model,
                )
            
            if area == "INGLES":
                return cls._generar_pipeline_ingles(
                    area,
                    institucion_id,
                    db,
                    num_preguntas,
                    dificultad,
                    timeout,
                    generation_model=generation_model,
                )
            
            if area == "SOCIALES_CIUDADANAS":
                return cls._generar_pipeline_sociales_ciudadanas(
                    area,
                    institucion_id,
                    db,
                    num_preguntas,
                    dificultad,
                    timeout,
                    generation_model=generation_model,
                )

            # 1. Construir el prompt enriquecido (flujo estándar)
            prompt_final = cls._construir_prompt(area, institucion_id, db, num_preguntas, dificultad)
            
            if not prompt_final:
                return GenerationResult(
                    success=False,
                    error=f"No se pudo construir el prompt para el área {area}. Verifica que existan los archivos de contexto."
                )
            
            print(f"Prompt construido: {len(prompt_final)} caracteres (~{len(prompt_final.split())} palabras)")
            
            print(f"Llamando al modelo de generación ({generation_model})...")
            
            cls._capture_prompt(area, prompt_final, "standard_generation")

            simulacro_json, tokens_used, _, _ = cls._llm_complete_json(
                prompt=prompt_final,
                generation_model=generation_model,
                timeout=timeout,
                context_label=f"generación de {area}",
            )
            
            # 4. Crear resultado exitoso
            result = GenerationResult(success=True, data=simulacro_json)
            result.tokens_used = tokens_used
            result.generation_time = time.time() - start_time
            
            # Log para depuración: mostrar estructura del JSON generado
            print(f"Generación exitosa: {result.tokens_used} tokens, {result.generation_time:.1f}s")
            print(f"Claves del JSON raíz: {list(simulacro_json.keys())}")
            if "meta" in simulacro_json:
                print(f"   meta: {simulacro_json['meta']}")
            if "preguntas" in simulacro_json:
                print(f"   Total preguntas: {len(simulacro_json['preguntas'])}")
                if simulacro_json['preguntas']:
                    print(f"   Primera pregunta (claves): {list(simulacro_json['preguntas'][0].keys())}")
            else:
                print(f"   No hay campo 'preguntas' en el JSON")
                print(f"   JSON completo (primeros 2000 chars): {json.dumps(simulacro_json, ensure_ascii=False)[:2000]}")
            
            return result
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return GenerationResult(
                success=False,
                error=f"Error en generación: {str(e)}"
            )


    @classmethod
    def _recuperar_patrones_rag(cls, area: str, topics: List[str], n_total: int = 6) -> str:
        """
        Recupera patrones desde ChromaDB usando una estrategia de Diversidad de Tópicos.
        Devuelve un string formateado con instrucciones de 'Blindaje Anti-Sesgo'.
        
        Args:
            area (str): Nombre del área (ej: SOCIALES_CIUDADANAS)
            topics (List[str]): Lista de subtemas para buscar diversidad (ej: ['Historia', 'Economía'])
            n_total (int): Total de patrones a recuperar (default 6)
        """
        try:
            import chromadb
            from chromadb.utils import embedding_functions
            
            # Paths relativos
            base_dir_rag = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            chroma_path_rag = os.path.join(base_dir_rag, "data", "chroma_db")
            
            if not os.path.exists(chroma_path_rag):
                return ""
                
            chroma_client = chromadb.PersistentClient(path=chroma_path_rag)
            openai_ef = embedding_functions.OpenAIEmbeddingFunction(
                api_key=OPENAI_API_KEY,
                model_name="text-embedding-3-small"
            )
            
            # Intentar obtener colección
            try:
                collection = chroma_client.get_collection(name="patrones_preguntas", embedding_function=openai_ef)
            except Exception:
                return "" # Colección no existe aún
                
            # Calcular cuántos por tópico
            n_per_topic = max(1, n_total // len(topics))
            patrones_recuperados = []
            
            for tema in topics:
                # Filtrar también por metadata 'area' para asegurar cross-contamination cero
                # Chroma filter syntax: where={"area": area}
                res = collection.query(
                    query_texts=[tema], 
                    n_results=n_per_topic + 1,
                    where={"area": area} 
                )
                if res['documents']:
                    patrones_recuperados.extend(res['documents'][0])
            
            # Seleccionar únicos y limitar al total
            patrones_unicos = list(set(patrones_recuperados))
            selection = patrones_unicos[:n_total]
            
            if not selection:
                return ""

            # Formatear Salida con Blindaje
            rag_text = "\n\n# BANCO DE PATRONES DINÁMICO (REFERENCIA DE ESTILO)\n"
            rag_text += "IMPORTANTE: Estos patrones se proveen SOLO para ilustrar el formato, tono y estructura esperada.\n"
            rag_text += "NO COPIES la distribución de temas o dificultades de estos ejemplos.\n"
            rag_text += "TU OBLIGACIÓN es generar contenido NUEVO que cumpla estrictamente con la DISTRIBUCIÓN solicitada, "
            rag_text += "independientemente de lo que veas en estos ejemplos.\n"
            
            for i, p in enumerate(selection):
                rag_text += f"\n--- PATRÓN REFERENCIAL {i+1} ---\n{p}\n"
                
            print(f"   RAG: {len(selection)} patrones inyectados para {area}.")
            return rag_text
            
        except Exception as e:
            print(f"   Falló RAG retrieval ({area}): {e}")
            return ""

    @classmethod
    def _recuperar_pool_patrones_rag(
        cls,
        area: str,
        topics: List[str],
        n_results_por_topic: int = 2,
        fallback_limit: int = 80
    ) -> List[str]:
        """
        Recupera un pool de patrones para rotación por lotes.

        Estrategia:
        1) Búsqueda semántica por tópicos (query_texts + where={"area": area}).
        2) Fallback robusto: `collection.get(where={"area": area})` sin embeddings,
           útil cuando falla el proveedor de embeddings en runtime.
        """
        try:
            import chromadb
            from chromadb.utils import embedding_functions

            base_dir_rag = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            chroma_path_rag = os.path.join(base_dir_rag, "data", "chroma_db")

            if not os.path.exists(chroma_path_rag):
                print("   No se encontro DB vectorial de patrones.")
                return []

            chroma_client = chromadb.PersistentClient(path=chroma_path_rag)
            openai_ef = embedding_functions.OpenAIEmbeddingFunction(
                api_key=OPENAI_API_KEY,
                model_name="text-embedding-3-small"
            )
            collection = chroma_client.get_collection(name="patrones_preguntas", embedding_function=openai_ef)

            # 1) Recuperación semántica por tópicos
            patrones_recuperados: List[str] = []
            for tema in topics:
                res = collection.query(
                    query_texts=[tema],
                    n_results=n_results_por_topic,
                    where={"area": area}
                )
                if res.get("documents"):
                    patrones_recuperados.extend(res["documents"][0])

            patrones_unicos = list(dict.fromkeys(patrones_recuperados))
            if patrones_unicos:
                return patrones_unicos

            print(
                f"   RAG semantico sin resultados para {area}. "
                "Intentando fallback por area..."
            )

            # 2) Fallback: extracción directa por metadata area (sin query embeddings)
            raw = collection.get(where={"area": area}, limit=fallback_limit, include=["documents"])
            docs = raw.get("documents") or []
            pool = list(dict.fromkeys(docs))
            return pool

        except Exception as e:
            print(
                f"   Fallo RAG semantico ({area}): {e}. "
                "Intentando fallback por area sin embeddings..."
            )
            try:
                import chromadb

                base_dir_rag = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                chroma_path_rag = os.path.join(base_dir_rag, "data", "chroma_db")
                if not os.path.exists(chroma_path_rag):
                    return []

                chroma_client = chromadb.PersistentClient(path=chroma_path_rag)
                collection = chroma_client.get_collection(name="patrones_preguntas")
                raw = collection.get(where={"area": area}, limit=fallback_limit, include=["documents"])
                docs = raw.get("documents") or []
                pool = list(dict.fromkeys(docs))
                if pool:
                    print(f"   RAG fallback por area ({area}): {len(pool)} patrones cargados.")
                else:
                    print(f"   RAG fallback por area ({area}) sin documentos.")
                return pool
            except Exception as fallback_e:
                print(f"   Fallback RAG fallido ({area}): {fallback_e}")
                return []

    @classmethod
    def _recuperar_pool_constitucional_sociales(
        cls,
        queries: List[str],
        n_results_por_query: int = 2,
        fallback_limit: int = 120
    ) -> List[str]:
        """
        Recupera contexto jurídico-constitucional para Sociales.

        Estrategia:
        1) Búsqueda semántica en `sociales_ciudadanas_kb`.
        2) Fallback sin embeddings: extracción directa de documentos.
        """
        collection_name = "sociales_ciudadanas_kb"
        try:
            import chromadb
            from chromadb.utils import embedding_functions

            base_dir_rag = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            chroma_path_rag = os.path.join(base_dir_rag, "data", "chroma_db")
            if not os.path.exists(chroma_path_rag):
                print(f"[RAG] No se encontro BD en {chroma_path_rag}")
                return []

            chroma_client = chromadb.PersistentClient(path=chroma_path_rag)
            openai_ef = embedding_functions.OpenAIEmbeddingFunction(
                api_key=OPENAI_API_KEY,
                model_name="text-embedding-3-small"
            )
            collection = chroma_client.get_collection(name=collection_name, embedding_function=openai_ef)

            retrieved_docs: List[str] = []
            for q in queries:
                results = collection.query(query_texts=[q], n_results=n_results_por_query)
                docs = results.get("documents", [[]])[0]
                metas = results.get("metadatas", [[]])[0]
                for doc, meta in zip(docs, metas):
                    source = (meta or {}).get("source", "Constitución")
                    retrieved_docs.append(f"- [{source}]: {(doc or '')[:400]}...")

            unique = list(dict.fromkeys(retrieved_docs))
            if unique:
                return unique

            print("[RAG] Constitucional semantico sin resultados. Intentando fallback directo...")
            raw = collection.get(limit=fallback_limit, include=["documents", "metadatas"])
            docs = raw.get("documents") or []
            metas = raw.get("metadatas") or []
            fallback_docs: List[str] = []
            for i, doc in enumerate(docs):
                meta = metas[i] if i < len(metas) else {}
                source = (meta or {}).get("source", "Constitución")
                fallback_docs.append(f"- [{source}]: {(doc or '')[:400]}...")
            return list(dict.fromkeys(fallback_docs))

        except Exception as e:
            print(
                f"[RAG] Falló recuperación constitucional semantica: {e}. "
                "Intentando fallback sin embeddings..."
            )
            try:
                import chromadb

                base_dir_rag = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                chroma_path_rag = os.path.join(base_dir_rag, "data", "chroma_db")
                if not os.path.exists(chroma_path_rag):
                    return []

                chroma_client = chromadb.PersistentClient(path=chroma_path_rag)
                collection = chroma_client.get_collection(name=collection_name)
                raw = collection.get(limit=fallback_limit, include=["documents", "metadatas"])
                docs = raw.get("documents") or []
                metas = raw.get("metadatas") or []
                fallback_docs: List[str] = []
                for i, doc in enumerate(docs):
                    meta = metas[i] if i < len(metas) else {}
                    source = (meta or {}).get("source", "Constitución")
                    fallback_docs.append(f"- [{source}]: {(doc or '')[:400]}...")
                unique = list(dict.fromkeys(fallback_docs))
                if unique:
                    print(f"   RAG constitucional fallback: {len(unique)} fragmentos cargados.")
                else:
                    print("   RAG constitucional fallback sin documentos.")
                return unique
            except Exception as fallback_e:
                print(f"[RAG] Fallback constitucional fallido: {fallback_e}")
                return []

    @classmethod
    def _generar_pipeline_lectura_critica(
        cls,
        area: str,
        institucion_id: int,
        db: Session,
        num_preguntas: int,
        dificultad: dict,
        timeout: int,
        generation_model: Optional[str] = None,
    ) -> GenerationResult:
        """
        Pipeline CHUNKED para Lectura Critica:
        - Buffer del 40%
        - Lotes de maximo 14 preguntas
        - 1 texto por cada 4 preguntas
        - Cuotas por afirmacion (25/42/33) y dificultad por lote
        - Rotacion de patrones RAG entre lotes
        """
        import time
        import random
        import math
        from datetime import datetime
        start_time = time.time()

        # -- Configuracion --
        CHUNK_SIZE = 14
        PREGUNTAS_POR_TEXTO = 4
        MAX_RETRIES_PER_CHUNK = 2
        MAX_RAG_PATTERNS_PER_CHUNK = 6

        # =====================================================================
        # CONSTANTES OFICIALES ICFES - LECTURA CRITICA
        # =====================================================================
        DISTRIBUCION_AFIRMACIONES = {
            "Identificar y entender contenidos locales": 0.25,
            "Comprender cómo se articulan las partes": 0.42,
            "Reflexionar y evaluar un texto": 0.33
        }

        EVIDENCIAS_POR_AFIRMACION = {
            "Identificar y entender contenidos locales": [
                "Entiende el significado de elementos locales (palabras, frases)",
                "Identifica eventos, personajes y acciones explícitos"
            ],
            "Comprender cómo se articulan las partes": [
                "Comprende la estructura formal del texto y su función",
                "Identifica voces o situaciones presentes en el texto",
                "Comprende relaciones entre partes o enunciados del texto",
                "Identifica y caracteriza ideas en textos informativos",
                "Identifica relaciones en textos discontinuos (tablas, gráficas)"
            ],
            "Reflexionar y evaluar un texto": [
                "Establece validez e implicaciones de enunciados",
                "Establece relaciones intertextuales",
                "Reconoce contenidos valorativos del texto",
                "Reconoce estrategias discursivas del autor",
                "Contextualiza adecuadamente el texto"
            ]
        }
        
        TIPOS_TEXTO = [
            "Continuo literario (cuento, fragmento novelístico, poema en prosa)",
            "Continuo informativo no filosófico (artículo científico, periodístico)",
            "Continuo informativo filosófico (ensayo, reflexión filosófica)",
            "Discontinuo (infografía con datos, tabla interpretativa)"
        ]

        # 1) Sobre-aprovisionamiento
        target_preguntas = int(num_preguntas * 1.4)
        if target_preguntas < num_preguntas + 2:
            target_preguntas = num_preguntas + 2

        num_chunks = math.ceil(target_preguntas / CHUNK_SIZE)

        print(f" Iniciando Pipeline LECTURA CRITICA CHUNKED ({num_preguntas} solicitadas -> {target_preguntas} con buffer)")
        print(f"   Dividido en {num_chunks} lote(s) de ~{CHUNK_SIZE} preguntas")

        # 2) Validar contexto estatico obligatorio de Lectura Critica
        folder = AREA_FOLDERS.get(area)
        area_path = os.path.join(STATIC_DIR, folder, "extracted") if folder else ""
        required_static_files = [
            "prompt_lectura_critica.md",
            "marco_referencia_lectura_critica_limpio.md",
            "niveles_desempeno_lectura_critica.md",
        ]
        for filename in required_static_files:
            filepath = os.path.join(area_path, filename)
            if (not os.path.exists(filepath)) or os.path.getsize(filepath) == 0:
                return GenerationResult(
                    success=False,
                    error=(
                        f"Contexto estatico obligatorio faltante o vacio para Lectura Critica: {filename}. "
                        "Se requiere prompt base + marco + niveles."
                    )
                )

        # 2) Contexto base sin tarea final (evita contradiccion con cuotas por lote)
        #    num_preguntas=0 impide que _construir_prompt agregue "Genera exactamente N preguntas".
        contexto_oficial = cls._construir_prompt(area, institucion_id, db, 0, dificultad) or ""
        if not contexto_oficial:
            return GenerationResult(success=False, error="No se pudo cargar el contexto oficial de Lectura Critica")

        # 3) RAG raw para rotacion por lote
        temas_busqueda = [
            "Texto Literario",
            "Ensayo Filosofico",
            "Texto Informativo",
            "Columna de Opinion",
            "Infografia",
            "Analisis de argumento",
            "Comprension inferencial"
        ]
        print("[RAG] Recuperando patrones de Lectura Critica...")
        all_rag_patterns = cls._recuperar_pool_patrones_rag(
            area=area,
            topics=temas_busqueda,
            n_results_por_topic=2,
            fallback_limit=80
        )
        if all_rag_patterns:
            print(f"   RAG: {len(all_rag_patterns)} patrones unicos recuperados para rotacion.")
        else:
            print("   RAG de Lectura Critica no disponible; continuando sin patrones dinamicos.")

        def _dividir_cuota(total: int, num_partes: int) -> list:
            base = total // num_partes
            resto = total % num_partes
            return [base + (1 if i < resto else 0) for i in range(num_partes)]

        def _crear_secuencia_cuotas(cuotas: Dict[str, int], orden: List[str]) -> List[str]:
            total = sum(cuotas.values())
            restantes = dict(cuotas)
            secuencia = []

            while len(secuencia) < total:
                progreso = False
                for key in orden:
                    if restantes.get(key, 0) > 0:
                        secuencia.append(key)
                        restantes[key] -= 1
                        progreso = True
                if not progreso:
                    break

            if len(secuencia) < total:
                for key in orden:
                    faltan = max(0, restantes.get(key, 0))
                    secuencia.extend([key] * faltan)

            return secuencia[:total]

        def _rotar_patrones(patrones: List[str], chunk_idx: int, max_por_lote: int = MAX_RAG_PATTERNS_PER_CHUNK) -> List[str]:
            if not patrones:
                return []
            n = len(patrones)
            count = min(max_por_lote, n)
            start = chunk_idx % n
            return [patrones[(start + i) % n] for i in range(count)]

        # 4) Cuotas globales
        afirmaciones = list(DISTRIBUCION_AFIRMACIONES.keys())
        total_literal = int(target_preguntas * 0.25)
        total_inferencial = int(target_preguntas * 0.42)
        total_critico = target_preguntas - total_literal - total_inferencial

        dificultad_req = dificultad or {"facil": 30, "medio": 40, "dificil": 30}
        total_facil = round(target_preguntas * dificultad_req.get("facil", 30) / 100)
        total_medio = round(target_preguntas * dificultad_req.get("medio", 40) / 100)
        total_dificil = target_preguntas - total_facil - total_medio

        print(f"    Cuotas globales afirmaciones: Literal={total_literal}, Inferencial={total_inferencial}, Critico={total_critico}")
        print(f"    Cuotas globales dificultad: F={total_facil}, M={total_medio}, D={total_dificil}")

        chunks_size = _dividir_cuota(target_preguntas, num_chunks)

        secuencia_afirmaciones = _crear_secuencia_cuotas(
            {
                afirmaciones[0]: total_literal,
                afirmaciones[1]: total_inferencial,
                afirmaciones[2]: total_critico,
            },
            afirmaciones
        )
        secuencia_dificultades = _crear_secuencia_cuotas(
            {
                "facil": total_facil,
                "medio": total_medio,
                "dificil": total_dificil,
            },
            ["facil", "medio", "dificil"]
        )

        if len(secuencia_afirmaciones) < target_preguntas:
            secuencia_afirmaciones.extend([afirmaciones[1]] * (target_preguntas - len(secuencia_afirmaciones)))
        if len(secuencia_dificultades) < target_preguntas:
            secuencia_dificultades.extend(["medio"] * (target_preguntas - len(secuencia_dificultades)))

        preguntas_generadas = []
        tokens_total = 0
        chunks_exitosos = 0
        secuencia_offset = 0

        for chunk_idx, chunk_target in enumerate(chunks_size):
            chunk_num = chunk_idx + 1
            chunk_afirmaciones = secuencia_afirmaciones[secuencia_offset:secuencia_offset + chunk_target]
            chunk_dificultades = secuencia_dificultades[secuencia_offset:secuencia_offset + chunk_target]
            secuencia_offset += chunk_target

            if len(chunk_afirmaciones) < chunk_target:
                chunk_afirmaciones.extend([afirmaciones[1]] * (chunk_target - len(chunk_afirmaciones)))
            if len(chunk_dificultades) < chunk_target:
                chunk_dificultades.extend(["medio"] * (chunk_target - len(chunk_dificultades)))

            c_literal = sum(1 for a in chunk_afirmaciones if a == afirmaciones[0])
            c_inferencial = sum(1 for a in chunk_afirmaciones if a == afirmaciones[1])
            c_critico = sum(1 for a in chunk_afirmaciones if a == afirmaciones[2])
            d_facil = sum(1 for d in chunk_dificultades if d == "facil")
            d_medio = sum(1 for d in chunk_dificultades if d == "medio")
            d_dificil = sum(1 for d in chunk_dificultades if d == "dificil")

            print(f"\n   -- LOTE {chunk_num}/{num_chunks} ({chunk_target} preguntas) --")
            print(f"      Afirmaciones: Literal={c_literal}, Inferencial={c_inferencial}, Critico={c_critico}")
            print(f"      Dificultad: F={d_facil}, M={d_medio}, D={d_dificil}")

            chunk_patterns = _rotar_patrones(all_rag_patterns, chunk_idx)
            rag_text_chunk = ""
            if chunk_patterns:
                rag_text_chunk = "\n# BANCO DE PATRONES DINAMICO (REFERENCIA DE ESTILO)\n"
                rag_text_chunk += "Estos patrones son SOLO referencia de formato y tono. NO copies contenido.\n"
                rag_text_chunk += "Genera contenido NUEVO para este lote.\n"
                for i, pattern in enumerate(chunk_patterns):
                    rag_text_chunk += f"\n--- PATRON {i+1} ---\n{pattern}\n"
                print(f"       RAG: {len(chunk_patterns)} patrones rotados para este lote")

            contexto_lote_completo = (
                f"CONTEXTO ESTATICO OBLIGATORIO (PROMPT BASE + MARCO + NIVELES):\n"
                f"{contexto_oficial}\n\n"
                f"{rag_text_chunk}"
            )

            chunk_success = False
            chunk_preguntas = []

            for attempt in range(1, MAX_RETRIES_PER_CHUNK + 2):
                if attempt > 1:
                    print(f"       Reintento {attempt - 1}/{MAX_RETRIES_PER_CHUNK} del lote {chunk_num}...")

                chunk_preguntas = []
                slot_idx = 0
                tokens_chunk_attempt = 0
                num_textos_chunk = math.ceil(chunk_target / PREGUNTAS_POR_TEXTO)

                for i_texto in range(num_textos_chunk):
                    preguntas_este_texto = min(PREGUNTAS_POR_TEXTO, chunk_target - slot_idx)
                    if preguntas_este_texto <= 0:
                        break

                    tipo_texto = TIPOS_TEXTO[(chunk_idx + i_texto) % len(TIPOS_TEXTO)]
                    print(
                        f"      [L{chunk_num}] Texto {i_texto + 1}/{num_textos_chunk} "
                        f"({preguntas_este_texto} preguntas, {tipo_texto[:30]}...)"
                    )

                    prompt_etapa_a = f"""Genera un texto para una prueba de LECTURA CRITICA tipo ICFES Saber 11.

{contexto_lote_completo}

---
INSTRUCCION DEL LOTE {chunk_num}/{num_chunks}:
- Este lote debe producir EXACTAMENTE {chunk_target} preguntas.
- Cuotas lote por afirmacion: Literal={c_literal}, Inferencial={c_inferencial}, Critico={c_critico}.
- Cuotas lote por dificultad: Facil={d_facil}, Medio={d_medio}, Dificil={d_dificil}.

SOLICITUD DE ESTE TEXTO:
- Tipo de texto: {tipo_texto}
- Longitud: entre 150 y 250 palabras.
- Este texto debe permitir {preguntas_este_texto} preguntas con foco literal, inferencial y/o critico.

INSTRUCCIONES DE ESTILO:
1. Imita densidad conceptual y vocabulario de los patrones de referencia (sin copiar).
2. Evita tono escolar simplificado.
3. Mantiene cohesion argumentativa o narrativa segun el tipo.
4. Usa conectores logicos complejos y ambiguedades controladas.

SALIDA ESPERADA: solo el cuerpo del texto, sin titulos ni metadatos.
"""
                    if attempt == 1:
                        cls._capture_prompt(area, prompt_etapa_a, f"lc_chunk_{chunk_num}_texto_{i_texto + 1}")

                    try:
                        texto_base, tokens_a, _ = cls._llm_complete_text(
                            prompt=prompt_etapa_a,
                            generation_model=generation_model,
                            timeout=timeout,
                        )
                    except Exception as e:
                        print(f"      ❌ Error generando texto base del lote {chunk_num}: {e}")
                        continue

                    tokens_chunk_attempt += tokens_a
                    if not texto_base:
                        print(f"      ⚠️ Texto base vacio en lote {chunk_num}, texto {i_texto + 1}.")
                        continue

                    for _ in range(preguntas_este_texto):
                        if slot_idx >= chunk_target:
                            break

                        afirmacion_actual = chunk_afirmaciones[slot_idx]
                        nivel_actual = chunk_dificultades[slot_idx]
                        slot_idx += 1

                        evidencias_disponibles = EVIDENCIAS_POR_AFIRMACION.get(afirmacion_actual, [])
                        evidencia_actual = random.choice(evidencias_disponibles) if evidencias_disponibles else "General"

                        prompt_etapa_b_c = f"""
Eres un experto evaluador del ICFES. Tu tarea es crear UNA pregunta de opción múltiple basada en el siguiente texto.

---
TEXTO BASE:
\"\"\"{texto_base}\"\"\"
---

OBJETIVO: Evaluar la competencia: "{afirmacion_actual}"
EVIDENCIA ESPECÍFICA: "{evidencia_actual}"
NIVEL DE DIFICULTAD: {nivel_actual}
LOTE: {chunk_num}/{num_chunks}

{contexto_lote_completo}

DEFINICIONES RÁPIDAS (MARCO DE REFERENCIA):
1. LITERAL ("Identificar contenidos"): ¿Qué dice el texto explícitamente? (Personajes, eventos, definiciones).
2. INFERENCIAL ("Articular partes"): ¿Qué se deduce? (Intenciones, relaciones causa-efecto, estructura).
3. CRÍTICA ("Reflexionar/Evaluar"): ¿Qué validez/sesgo tiene? (Argumentos, premisas, relación con otros textos).

INSTRUCCIONES DE CREACIÓN:
1. La pregunta debe depender 100% del texto.
2. La respuesta correcta debe ser INEQUÍVOCA y justificable con el texto.
3. Los 3 distractores deben ser plausibles pero incorrectos (errores comunes de lectura).
4. Longitud de opciones equilibrada.

FORMATO JSON ÚNICO (NO LISTA):
{{
  "enunciado": "¿Pregunta...?",
  "opciones": [
    {{"id": "A", "texto": "..."}},
    {{"id": "B", "texto": "..."}},
    {{"id": "C", "texto": "..."}},
    {{"id": "D", "texto": "..."}}
  ],
  "respuesta_correcta": "A",
  "dificultad": "{nivel_actual}",
  "competencia": "{afirmacion_actual}",
  "componente": "{evidencia_actual}",
  "justificacion": "Explicación breve...",
  "tema": "Tema...",
  "_razonamiento_pedagogico": "Breve explicación de por qué esta pregunta evalúa {afirmacion_actual} en nivel {nivel_actual}."
}}
"""
                        if attempt == 1:
                            cls._capture_prompt(area, prompt_etapa_b_c, f"lc_chunk_{chunk_num}_slot_{slot_idx}")

                        try:
                            pregunta_data, tokens_b, _, content_b = cls._llm_complete_json(
                                prompt=prompt_etapa_b_c,
                                generation_model=generation_model,
                                timeout=timeout,
                                context_label=f"pregunta lectura lote {chunk_num}, slot {slot_idx}",
                            )
                            tokens_chunk_attempt += tokens_b
                        except Exception as e:
                            print(f"      ❌ Error generando pregunta (lote {chunk_num}, slot {slot_idx}): {e}")
                            continue

                        try:
                            # Resiliencia: si el modelo devolvio lista, extraer primera pregunta
                            if "preguntas" in pregunta_data and isinstance(pregunta_data["preguntas"], list):
                                if len(pregunta_data["preguntas"]) > 0:
                                    pregunta_data = pregunta_data["preguntas"][0]
                                else:
                                    raise ValueError("El campo 'preguntas' esta vacio")

                            required_keys = ["enunciado", "opciones", "respuesta_correcta"]
                            missing_keys = [k for k in required_keys if k not in pregunta_data]
                            if missing_keys:
                                raise ValueError(f"Faltan claves obligatorias: {missing_keys}")
                            if not pregunta_data.get("enunciado"):
                                raise ValueError("El campo 'enunciado' esta vacio")
                            if not isinstance(pregunta_data.get("opciones"), list) or len(pregunta_data["opciones"]) < 2:
                                raise ValueError("El campo 'opciones' es invalido o insuficiente")

                            # Enriquecer/forzar metadata oficial
                            pregunta_data["id"] = len(chunk_preguntas) + 1
                            pregunta_data["contexto"] = texto_base
                            pregunta_data["tiene_grafico"] = False
                            pregunta_data["competencia"] = afirmacion_actual
                            pregunta_data["componente"] = evidencia_actual
                            pregunta_data["dificultad"] = nivel_actual

                            if isinstance(pregunta_data.get("opciones"), list):
                                ids = ["A", "B", "C", "D"]
                                for idx_opt, opt in enumerate(pregunta_data["opciones"]):
                                    if isinstance(opt, str):
                                        opt = {"id": ids[idx_opt] if idx_opt < 4 else "X", "texto": opt}
                                        pregunta_data["opciones"][idx_opt] = opt
                                    if "id" not in opt:
                                        opt["id"] = ids[idx_opt] if idx_opt < 4 else "X"

                            chunk_preguntas.append(pregunta_data)
                        except ValueError as e:
                            print(f"      ❌ Error parseando pregunta (lote {chunk_num}, slot {slot_idx}): {e}")
                            print(f"         Contenido recibido: {str(content_b)[:240]}...")

                min_esperado = max(1, chunk_target // 2)
                if len(chunk_preguntas) >= min_esperado:
                    print(
                        f"      ✅ Lote {chunk_num} exitoso: {len(chunk_preguntas)}/{chunk_target} "
                        f"preguntas ({tokens_chunk_attempt} tokens)"
                    )
                    chunk_success = True
                    tokens_total += tokens_chunk_attempt
                    break

                print(
                    f"      ⚠️ Lote {chunk_num} insuficiente: {len(chunk_preguntas)}/{chunk_target} "
                    f"(minimo aceptable: {min_esperado})"
                )
                tokens_total += tokens_chunk_attempt

            if chunk_success and chunk_preguntas:
                preguntas_generadas.extend(chunk_preguntas)
                chunks_exitosos += 1
            else:
                print(f"      ❌ Lote {chunk_num} fallido completamente.")

        print(f"\n   -- RESULTADO CHUNKED LECTURA --")
        print(f"   📦 Lotes exitosos: {chunks_exitosos}/{num_chunks}")
        print(f"   📊 Preguntas obtenidas: {len(preguntas_generadas)}")

        min_chunks_exitosos = 2 if num_chunks >= 3 else 1
        if chunks_exitosos < min_chunks_exitosos:
            error_msg = (
                f"Lectura chunked insuficiente por lotes: "
                f"{chunks_exitosos}/{num_chunks} lotes exitosos "
                f"(minimo requerido: {min_chunks_exitosos})"
            )
            print(f"   ❌ {error_msg}")
            return GenerationResult(success=False, error=error_msg)

        min_total_esperado = max(1, target_preguntas // 2)
        if len(preguntas_generadas) < min_total_esperado:
            error_msg = (
                f"Lectura chunked insuficiente: {len(preguntas_generadas)}/{target_preguntas} "
                f"preguntas (minimo requerido: {min_total_esperado})"
            )
            print(f"   ❌ {error_msg}")
            return GenerationResult(success=False, error=error_msg)

        # Re-ID consecutivo global
        for idx, pregunta in enumerate(preguntas_generadas):
            pregunta["id"] = idx + 1

        # Estadisticas finales
        stats_afirm = {}
        stats_dif = {"facil": 0, "medio": 0, "dificil": 0}
        for p in preguntas_generadas:
            comp = p.get("competencia", "Desconocido")
            stats_afirm[comp] = stats_afirm.get(comp, 0) + 1
            dif = str(p.get("dificultad", "") or "").lower().strip()
            if dif in stats_dif:
                stats_dif[dif] += 1

        print(f"\n   📊 Distribucion final de afirmaciones:")
        for afirm, count in stats_afirm.items():
            pct = (count / len(preguntas_generadas)) * 100 if preguntas_generadas else 0
            print(f"      - {afirm[:40]}: {count} ({pct:.1f}%)")
        print(f"   📊 Distribucion final dificultad: F={stats_dif['facil']}, M={stats_dif['medio']}, D={stats_dif['dificil']}")

        simulacro_final = {
            "meta": {
                "area": "Lectura Crítica",
                "total_preguntas": len(preguntas_generadas),
                "modo_generacion": f"pipeline_lc_chunked_v3 ({num_chunks} lotes)",
                "distribucion_afirmaciones": stats_afirm,
                "distribucion_dificultad": stats_dif,
                "fecha_generacion": datetime.now().isoformat()
            },
            "preguntas": preguntas_generadas
        }

        result = GenerationResult(success=True, data=simulacro_final)
        result.tokens_used = tokens_total
        result.generation_time = time.time() - start_time

        print(
            f"✅ Pipeline LC Chunked finalizado: {len(preguntas_generadas)} preguntas "
            f"en {result.generation_time:.1f}s ({tokens_total} tokens)"
        )
        return result





    @classmethod
    def _generar_pipeline_matematicas(
        cls,
        area: str,
        institucion_id: int,
        db: Session,
        num_preguntas: int,
        dificultad: dict,
        timeout: int,
        generation_model: Optional[str] = None,
    ) -> GenerationResult:
        """
        Pipeline HÍBRIDO para Matemáticas con Generación por Lotes (Chunked Generation):
        1. Contexto Rico: Usa los prompts originales (.md, patrones, etc) para conservar riqueza visual.
        2. Chain of Thought (CoT): Inyecta instrucción para obligar a resolver paso a paso.
        3. Blindaje: Pide +40% de preguntas (Buffer).
        4. Chunking: Divide la generación en lotes de CHUNK_SIZE para evitar que o3 se sature
           con la carga de razonamiento matemático y devuelva respuestas vacías.
        """
        import time
        import math
        from datetime import datetime
        start_time = time.time()
        
        # ── Configuración ──
        CHUNK_SIZE = cls._chunk_size_for_model(
            generation_model=generation_model,
            default_chunk_size=14,   # estable para o3
            sonnet_chunk_size=10,    # reduce truncamiento en Sonnet
        )
        MAX_RETRIES_PER_CHUNK = 2  # Reintentos por lote si devuelve respuesta vacía
        
        # 1. Sobre-aprovisionamiento
        target_preguntas = int(num_preguntas * 1.4) 
        if target_preguntas < num_preguntas + 2:
            target_preguntas = num_preguntas + 2
        
        # 2. Calcular número de lotes
        num_chunks = math.ceil(target_preguntas / CHUNK_SIZE)
        
        print(f"🧮 Iniciando Pipeline Híbrido Math CHUNKED ({num_preguntas} solicitadas -> {target_preguntas} con Buffer)")
        if is_claude_model(generation_model):
            print(f"   🧠 Ajuste Sonnet activo: CHUNK_SIZE={CHUNK_SIZE}")
        print(f"   📦 Dividido en {num_chunks} lote(s) de ~{CHUNK_SIZE} preguntas cada uno")
        
        # 3. Cargar Prompt Base (sin instrucción de tarea — cada chunk la inyecta)
        #    num_preguntas=0 evita que _construir_prompt añada "Genera exactamente N preguntas"
        #    porque esa instrucción la maneja cada chunk con su propia cuota.
        base_prompt_content = cls._construir_prompt(area, institucion_id, db, 0, None)
        
        if not base_prompt_content:
            return GenerationResult(success=False, error="No se pudo cargar contexto de Matemáticas")
        
        # ── RAG: Recuperar Patrones Dinámicos desde ChromaDB ──
        temas_busqueda = [
            "Álgebra y Funciones",
            "Ecuaciones y Sistemas",
            "Geometría Plana",
            "Geometría Analítica",
            "Estadística Descriptiva",
            "Probabilidad",
            "Variación y Modelación"
        ]
        print("🧮 [RAG] Recuperando patrones de Matemáticas...")
        all_rag_patterns = cls._recuperar_pool_patrones_rag(
            area=area,
            topics=temas_busqueda,
            n_results_por_topic=2,
            fallback_limit=80
        )
        if all_rag_patterns:
            print(f"   ✅ Se recuperaron {len(all_rag_patterns)} patrones únicos del RAG.")
        else:
            print("   ⚠️ RAG de Matemáticas no disponible; continuando sin patrones dinamicos.")

        # ── Distribuciones globales por competencia y dificultad ──
        total_c_interpretacion = int(target_preguntas * 0.34)
        total_c_formulacion = int(target_preguntas * 0.43)
        total_c_argumentacion = target_preguntas - total_c_interpretacion - total_c_formulacion

        # Componentes matemáticos (dentro de rangos ICFES):
        # Álgebra y cálculo: 35-40%, Estadística: 35-40%, Geometría: 20-35%
        total_comp_algebra = round(target_preguntas * 0.38)
        total_comp_estadistica = round(target_preguntas * 0.37)
        total_comp_geometria = target_preguntas - total_comp_algebra - total_comp_estadistica

        # Cuota visual exacta (60%)
        total_visual = round(target_preguntas * 0.60)
        
        dificultad_req = dificultad or {"facil": 30, "medio": 40, "dificil": 30}
        total_facil = round(target_preguntas * dificultad_req.get("facil", 30) / 100)
        total_medio = round(target_preguntas * dificultad_req.get("medio", 40) / 100)
        total_dificil = target_preguntas - total_facil - total_medio
        
        print(f"   📊 Distribución Objetivo Global: Int={total_c_interpretacion}, Form={total_c_formulacion}, Arg={total_c_argumentacion}")
        print(f"   📊 Componentes Global: Algebra={total_comp_algebra}, Estadistica={total_comp_estadistica}, Geometria={total_comp_geometria}")
        print(f"   📊 Dificultad Global: F={total_facil}, M={total_medio}, D={total_dificil}")
        print(f"   📊 Visual Global (exacto): {total_visual}/{target_preguntas}")
        
        # ── Dividir cuotas entre lotes ──
        def _dividir_cuota(total: int, num_partes: int) -> list:
            """Divide un total en N partes lo más equitativas posible."""
            base = total // num_partes
            resto = total % num_partes
            partes = [base + (1 if i < resto else 0) for i in range(num_partes)]
            return partes
        
        chunks_size = _dividir_cuota(target_preguntas, num_chunks)
        chunks_interp = _dividir_cuota(total_c_interpretacion, num_chunks)
        chunks_formul = _dividir_cuota(total_c_formulacion, num_chunks)
        chunks_argum = _dividir_cuota(total_c_argumentacion, num_chunks)
        chunks_comp_algebra = _dividir_cuota(total_comp_algebra, num_chunks)
        chunks_comp_estadistica = _dividir_cuota(total_comp_estadistica, num_chunks)
        chunks_comp_geometria = _dividir_cuota(total_comp_geometria, num_chunks)
        chunks_visual = _dividir_cuota(total_visual, num_chunks)
        chunks_facil = _dividir_cuota(total_facil, num_chunks)
        chunks_medio = _dividir_cuota(total_medio, num_chunks)
        chunks_dificil = _dividir_cuota(total_dificil, num_chunks)
        
        # ── Dividir RAG patterns entre lotes para diversidad ──
        def _rotar_patrones(patrones: list, chunk_idx: int, num_chunks: int, max_por_lote: int = 7) -> list:
            """Rota los patrones entre lotes para que cada lote vea patrones distintos."""
            if not patrones:
                return []
            n = len(patrones)
            start = (chunk_idx * max_por_lote) % n
            seleccion = []
            for i in range(max_por_lote):
                idx = (start + i) % n
                seleccion.append(patrones[idx])
            return seleccion
        
        # ── Generar por lotes ──
        all_preguntas = []
        total_tokens_used = 0
        chunks_exitosos = 0
        
        for chunk_idx in range(num_chunks):
            chunk_num = chunk_idx + 1
            chunk_target = chunks_size[chunk_idx]
            c_int = chunks_interp[chunk_idx]
            c_for = chunks_formul[chunk_idx]
            c_arg = chunks_argum[chunk_idx]
            comp_alg = chunks_comp_algebra[chunk_idx]
            comp_est = chunks_comp_estadistica[chunk_idx]
            comp_geo = chunks_comp_geometria[chunk_idx]
            vis_target = chunks_visual[chunk_idx]
            d_fac = chunks_facil[chunk_idx]
            d_med = chunks_medio[chunk_idx]
            d_dif = chunks_dificil[chunk_idx]
            
            print(f"\n   ── LOTE {chunk_num}/{num_chunks} ({chunk_target} preguntas) ──")
            print(f"      Competencias: Int={c_int}, Form={c_for}, Arg={c_arg}")
            print(f"      Componentes: Alg={comp_alg}, Est={comp_est}, Geo={comp_geo}")
            print(f"      Dificultad: F={d_fac}, M={d_med}, D={d_dif}")
            print(f"      Visual exacto: {vis_target}/{chunk_target}")
            
            # Seleccionar patrones RAG rotados para este lote
            chunk_patterns = _rotar_patrones(all_rag_patterns, chunk_idx, num_chunks)
            rag_text = ""
            if chunk_patterns:
                rag_text = "\n\n# 🧩 BANCO DE PATRONES DINÁMICO (REFERENCIA DE ESTILO)\n"
                rag_text += "❗ Estos patrones son SOLO referencia de formato y tono. NO copies su contenido.\n"
                rag_text += "✅ Genera contenido NUEVO cumpliendo la distribución solicitada.\n"
                for i, p in enumerate(chunk_patterns):
                    rag_text += f"\n--- PATRÓN {i+1} ---\n{p}\n"
                print(f"      🧩 RAG: {len(chunk_patterns)} patrones inyectados (rotados)")
            
            # Construir instrucción específica para este lote
            cot_instruction = f"""
________________________________________________________________________________
!!! INSTRUCCIÓN DE DISTRIBUCIÓN OBLIGATORIA (LOTE {chunk_num} DE {num_chunks}) !!!

Debes generar EXACTAMENTE {chunk_target} preguntas con la siguiente distribución:

POR COMPETENCIA:
1. **Interpretación y Representación**: {c_int} preguntas.
   (Uso de tablas, gráficos, esquemas para extraer información)
2. **Formulación y Ejecución**: {c_for} preguntas.
   (Diseño de estrategias, resolución de problemas algorítmicos)
3. **Argumentación**: {c_arg} preguntas.
   (Validar afirmaciones, justificar procedimientos, refutar conclusiones)

POR COMPONENTE:
1. **Álgebra y cálculo**: {comp_alg} preguntas.
2. **Estadística**: {comp_est} preguntas.
3. **Geometría**: {comp_geo} preguntas.

POR DIFICULTAD:
- Fácil: {d_fac} preguntas (Nivel 2): Contextos cotidianos que requieren ANÁLISIS BÁSICO. El estudiante debe interpretar, comparar o aplicar un concepto sencillo. PROHIBIDO: preguntas donde la respuesta se lee directamente de una tabla/gráfica o se obtiene con una sola operación aritmética obvia sin contexto.
- Media: {d_med} preguntas (Nivel 2-3): Relacionar variables, 2+ pasos lógicos, aritmética en contexto no rutinario.
- Difícil: {d_dif} preguntas (Nivel 3-4): Modelado algebraico, justificación formal, múltiples pasos de abstracción.

⚠️ RESTRICCIÓN ANTI-TRIVIAL: Incluso una pregunta fácil debe retar intelectualmente a un estudiante de Grado 11. Si la respuesta se puede obtener solo leyendo un dato o haciendo una cuenta mental inmediata, la pregunta es INVÁLIDA.

POR ESTÍMULO VISUAL:
- Exactamente {vis_target} preguntas con `tiene_grafico: true`.
- Exactamente {chunk_target - vis_target} preguntas con `tiene_grafico: false`.

TOTAL DE ESTE LOTE: {chunk_target} preguntas.

!!! ALINEACIÓN PEDAGÓGICA !!!
Para cada pregunta, justifica en `_razonamiento_pedagogico`:
COMPETENCIA -> EVIDENCIA -> NIVEL DE DESEMPEÑO -> Paso a paso matemático.

{rag_text}

REGLA DE ORO (CHAIN OF THOUGHT):
Para cada pregunta, ANTES de escribir el JSON final, resuelve internamente el problema.
- Si usas una TABLA (`tabla_datos`), verifica que los números cuadren.
- Si usas un GRÁFICO (chartjs_*), verifica que los datos sean correctos.
- Si es álgebra, resuelve la ecuación paso a paso.

TU SALIDA DEBE SER UN ÚNICO JSON:
{{
  "meta": {{
    "area": "{area}",
    "total_preguntas": {chunk_target},
    "fecha_generacion": "{datetime.now().isoformat()}"
  }},
  "preguntas": [
    ... (las {chunk_target} preguntas con "_razonamiento_pedagogico") ...
  ]
}}
"""
            final_prompt = base_prompt_content + cot_instruction
            
            # Intentar generación con reintentos por lote
            chunk_preguntas = []
            chunk_success = False
            
            for attempt in range(1, MAX_RETRIES_PER_CHUNK + 2):  # +2 porque intento 1 = primer intento
                try:
                    if attempt == 1:
                        cls._capture_prompt(area, final_prompt, f"math_chunk_{chunk_num}")
                    else:
                        print(f"      🔄 Reintento {attempt - 1}/{MAX_RETRIES_PER_CHUNK}...")
                    
                    data, tokens_this_call, finish_reason, content = cls._llm_complete_json(
                        prompt=final_prompt,
                        generation_model=generation_model,
                        timeout=timeout,
                        context_label=f"math lote {chunk_num}",
                    )
                    total_tokens_used += tokens_this_call
                    
                    # Anthropic usa end_turn/stop_sequence; max_tokens implica truncamiento.
                    if not cls._is_expected_finish_reason(generation_model, finish_reason):
                        print(f"      ⚠️ finish_reason='{finish_reason}' (no esperado para {generation_model})")
                    if cls._should_retry_for_finish_reason(generation_model, finish_reason):
                        print("      ⚠️ Respuesta truncada por max_tokens. Reintentando lote...")
                        if attempt <= MAX_RETRIES_PER_CHUNK:
                            continue
                    
                    chunk_preguntas = data.get("preguntas", [])
                    
                    # Validar que la respuesta no esté vacía/anómala
                    min_esperado = max(1, chunk_target // 2)  # Al menos 50% del target del lote
                    if len(chunk_preguntas) < min_esperado:
                        # Loguear respuesta anómala para diagnóstico
                        print(f"      ⚠️ Respuesta anómala: {len(chunk_preguntas)}/{chunk_target} preguntas (mínimo: {min_esperado})")
                        print(f"      📊 Tokens: {tokens_this_call}, finish_reason: {finish_reason}")
                        try:
                            log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "logs", "anomalous")
                            os.makedirs(log_dir, exist_ok=True)
                            import uuid
                            log_file = os.path.join(log_dir, f"MATH_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}.txt")
                            with open(log_file, "w", encoding="utf-8") as f:
                                f.write(f"[ANOMALOUS RESPONSE - MATH CHUNKED]\n")
                                f.write(f"DATE: {datetime.now().isoformat()}\n")
                                f.write(f"CHUNK: {chunk_num}/{num_chunks} (target: {chunk_target})\n")
                                f.write(f"RECEIVED: {len(chunk_preguntas)} preguntas\n")
                                f.write(f"TOKENS: {tokens_this_call}\n")
                                f.write(f"FINISH_REASON: {finish_reason}\n")
                                f.write(f"RESPONSE KEYS: {list(data.keys())}\n")
                                f.write(f"\nRAW CONTENT (first 3000 chars):\n{content[:3000]}\n")
                            print(f"      📼 Log guardado: {os.path.basename(log_file)}")
                        except Exception as log_err:
                            print(f"      ⚠️ Error escribiendo log: {log_err}")
                        
                        if attempt <= MAX_RETRIES_PER_CHUNK:
                            continue  # Reintentar
                        else:
                            print(f"      ❌ Lote {chunk_num} agotó reintentos con respuesta insuficiente.")
                            break
                    
                    # Éxito
                    chunk_success = True
                    print(f"      ✅ Lote {chunk_num}: {len(chunk_preguntas)} preguntas generadas ({tokens_this_call} tokens)")
                    break
                    
                except ValueError as e:
                    print(f"      ❌ Error JSON en lote {chunk_num}: {e}")
                    if attempt <= MAX_RETRIES_PER_CHUNK:
                        continue
                    break
                except Exception as e:
                    print(f"      ❌ Error en lote {chunk_num}: {e}")
                    if attempt <= MAX_RETRIES_PER_CHUNK:
                        continue
                    break
            
            if chunk_success and chunk_preguntas:
                all_preguntas.extend(chunk_preguntas)
                chunks_exitosos += 1
            else:
                print(f"      ❌ Lote {chunk_num} fallido completamente.")
        
        # ── Evaluar resultado global ──
        print(f"\n   ── RESULTADO CHUNKED ──")
        print(f"   📦 Lotes exitosos: {chunks_exitosos}/{num_chunks}")
        print(f"   📊 Total preguntas obtenidas: {len(all_preguntas)}")
        
        # Necesitamos al menos 50% del target total para considerar éxito
        if len(all_preguntas) < max(1, target_preguntas // 2):
            error_msg = f"Generación chunked insuficiente: {len(all_preguntas)}/{target_preguntas} preguntas ({chunks_exitosos}/{num_chunks} lotes exitosos)"
            print(f"   ❌ {error_msg}")
            return GenerationResult(success=False, error=error_msg)
        
        # Re-numerar IDs consecutivos
        for idx, p in enumerate(all_preguntas):
            p["id"] = idx + 1
            
        simulacro_final = {
            "meta": {
                "area": "Matemáticas",
                "total_preguntas": len(all_preguntas),
                "modo_generacion": f"pipeline_math_chunked_v3 ({num_chunks} lotes)",
                "fecha_generacion": datetime.now().isoformat()
            },
            "preguntas": all_preguntas
        }
        
        result = GenerationResult(success=True, data=simulacro_final)
        result.tokens_used = total_tokens_used
        result.generation_time = time.time() - start_time
        
        print(f"✅ Pipeline Math Chunked finalizado: {len(all_preguntas)} preguntas en {result.generation_time:.1f}s ({total_tokens_used} tokens)")
        return result
    
    @classmethod
    def _generar_pipeline_ciencias_naturales(
        cls,
        area: str,
        institucion_id: int,
        db: Session,
        num_preguntas: int,
        dificultad: dict,
        timeout: int,
        generation_model: Optional[str] = None,
    ) -> GenerationResult:
        """
        Pipeline HIBRIDO para Ciencias Naturales con Generacion por Lotes (Chunked Generation):
        1. Contexto Rico: Usa todos los archivos estaticos (.md) para alineacion con el marco ICFES.
        2. Chain of Thought (CoT): Inyecta instruccion para verificar leyes y principios cientificos.
        3. Blindaje: Pide +40% de preguntas (Buffer).
        4. Chunking: Divide en lotes de CHUNK_SIZE para evitar saturacion de o3.
        """
        import time
        import math
        from datetime import datetime
        start_time = time.time()
        
        # -- Configuracion --
        CHUNK_SIZE = cls._chunk_size_for_model(
            generation_model=generation_model,
            default_chunk_size=14,
            sonnet_chunk_size=10,
        )
        MAX_RETRIES_PER_CHUNK = 2
        
        # 1. Sobre-aprovisionamiento (Buffer del 40%)
        target_preguntas = int(num_preguntas * 1.4) 
        if target_preguntas < num_preguntas + 2:
            target_preguntas = num_preguntas + 2
        
        # 2. Calcular numero de lotes
        num_chunks = math.ceil(target_preguntas / CHUNK_SIZE)
        
        print(f"🧬 Iniciando Pipeline Hibrido Ciencias CHUNKED ({num_preguntas} solicitadas -> {target_preguntas} con Buffer)")
        if is_claude_model(generation_model):
            print(f"   🧠 Ajuste Sonnet activo: CHUNK_SIZE={CHUNK_SIZE}")
        print(f"   📦 Dividido en {num_chunks} lote(s) de ~{CHUNK_SIZE} preguntas cada uno")
        
        # 3. Cargar Prompt Base (sin instruccion de tarea -- cada chunk la inyecta)
        #    num_preguntas=0 evita que _construir_prompt aada "Genera exactamente N preguntas"
        base_prompt_content = cls._construir_prompt(area, institucion_id, db, 0, None)
        
        if not base_prompt_content:
             return GenerationResult(success=False, error="No se pudo cargar el contexto de Ciencias Naturales.")

        # -- RAG: Recuperar Patrones Dinamicos (raw, para rotar entre lotes) --
        temas_cn = ["Biologia", "Quimica", "Fisica Mecanica", "Ecologia", "Cinematica", "Estequiometria"]
        all_rag_patterns_cn = cls._recuperar_pool_patrones_rag(
            area=area,
            topics=temas_cn,
            n_results_por_topic=2,
            fallback_limit=80
        )
        if all_rag_patterns_cn:
            print(f"   ✅ RAG: {len(all_rag_patterns_cn)} patrones unicos recuperados para rotacion.")
        else:
            print("   ⚠️ RAG de patrones no disponible. Continuando sin patrones dinamicos.")

        def _rotar_patrones_cn(patrones: list, chunk_idx: int, max_por_lote: int = 5) -> list:
            if not patrones:
                return []
            n = len(patrones)
            start = (chunk_idx * max_por_lote) % n
            seleccion = []
            for i in range(max_por_lote):
                idx = (start + i) % n
                seleccion.append(patrones[idx])
            return seleccion

        # -- Distribuciones globales --
        # Por Componente (Disciplina)
        total_bio = int(target_preguntas * 0.30)
        total_fis = int(target_preguntas * 0.30)
        total_quim = int(target_preguntas * 0.30)
        total_cts = target_preguntas - total_bio - total_fis - total_quim
        
        # Por Competencia (Habilidad transversal)
        total_indagacion = int(target_preguntas * 0.40)
        total_uso = int(target_preguntas * 0.30)
        total_explicacion = target_preguntas - total_indagacion - total_uso

        dificultad_req = dificultad or {"facil": 30, "medio": 40, "dificil": 30}
        total_facil = round(target_preguntas * dificultad_req.get("facil", 30) / 100)
        total_medio = round(target_preguntas * dificultad_req.get("medio", 40) / 100)
        total_dificil = target_preguntas - total_facil - total_medio
        
        print(f"   📊 Componentes Global: Bio={total_bio}, Fis={total_fis}, Quim={total_quim}, CTS={total_cts}")
        print(f"   📊 Competencias Global: Ind={total_indagacion}, Uso={total_uso}, Exp={total_explicacion}")
        print(f"   📊 Dificultad Global: F={total_facil}, M={total_medio}, D={total_dificil}")
        
        # -- Dividir cuotas entre lotes --
        def _dividir_cuota(total: int, num_partes: int) -> list:
            base = total // num_partes
            resto = total % num_partes
            return [base + (1 if i < resto else 0) for i in range(num_partes)]
        
        chunks_size = _dividir_cuota(target_preguntas, num_chunks)
        chunks_bio = _dividir_cuota(total_bio, num_chunks)
        chunks_fis = _dividir_cuota(total_fis, num_chunks)
        chunks_quim = _dividir_cuota(total_quim, num_chunks)
        chunks_cts = _dividir_cuota(total_cts, num_chunks)
        chunks_indagacion = _dividir_cuota(total_indagacion, num_chunks)
        chunks_uso = _dividir_cuota(total_uso, num_chunks)
        chunks_explicacion = _dividir_cuota(total_explicacion, num_chunks)
        chunks_facil = _dividir_cuota(total_facil, num_chunks)
        chunks_medio = _dividir_cuota(total_medio, num_chunks)
        chunks_dificil = _dividir_cuota(total_dificil, num_chunks)
        
        # -- Generar por lotes --
        all_preguntas = []
        total_tokens_used = 0
        chunks_exitosos = 0
        
        for chunk_idx in range(num_chunks):
            chunk_num = chunk_idx + 1
            chunk_target = chunks_size[chunk_idx]
            c_bio = chunks_bio[chunk_idx]
            c_fis = chunks_fis[chunk_idx]
            c_quim = chunks_quim[chunk_idx]
            c_cts = chunks_cts[chunk_idx]
            k_ind = chunks_indagacion[chunk_idx]
            k_uso = chunks_uso[chunk_idx]
            k_exp = chunks_explicacion[chunk_idx]
            d_fac = chunks_facil[chunk_idx]
            d_med = chunks_medio[chunk_idx]
            d_dif = chunks_dificil[chunk_idx]
            
            print(f"\n   -- LOTE {chunk_num}/{num_chunks} ({chunk_target} preguntas) --")
            print(f"      Componentes: Bio={c_bio}, Fis={c_fis}, Quim={c_quim}, CTS={c_cts}")
            print(f"      Competencias: Ind={k_ind}, Uso={k_uso}, Exp={k_exp}")
            print(f"      Dificultad: F={d_fac}, M={d_med}, D={d_dif}")
            
            # Seleccionar patrones RAG rotados para este lote
            chunk_patterns = _rotar_patrones_cn(all_rag_patterns_cn, chunk_idx)
            rag_text_chunk = ""
            if chunk_patterns:
                rag_text_chunk = "\n\n# BANCO DE PATRONES DINAMICO (REFERENCIA DE ESTILO)\n"
                rag_text_chunk += "Estos patrones son SOLO referencia de formato y tono. NO copies su contenido.\n"
                rag_text_chunk += "Genera contenido NUEVO cumpliendo la distribucion solicitada.\n"
                for i, p in enumerate(chunk_patterns):
                    rag_text_chunk += f"\n--- PATRON {i+1} ---\n{p}\n"
                print(f"      RAG: {len(chunk_patterns)} patrones inyectados (rotados)")
            
            # Construir instruccion especifica para este lote
            cot_instruction = f"""
________________________________________________________________________________
!!! INSTRUCCION DE DISTRIBUCION OBLIGATORIA (LOTE {chunk_num} DE {num_chunks}) !!!

Debes generar EXACTAMENTE {chunk_target} preguntas con la siguiente distribucion:

1. POR COMPONENTE (DISCIPLINA):
   - **BIOLOGIA**: {c_bio} preguntas.
   - **FISICA**: {c_fis} preguntas.
   - **QUIMICA**: {c_quim} preguntas.
   - **CTS (Ciencia, Tecnologia y Sociedad)**: {c_cts} preguntas.

2. POR COMPETENCIA (HABILIDAD TRANSVERSAL):
   Distribuye las preguntas para cumplir tambien:
   - **INDAGACION**: {k_ind} preguntas.
     (CRUCIAL: Usar tablas, graficas de experimentos para evaluar analisis de datos)
   - **USO COMPRENSIVO DEL CONOCIMIENTO**: {k_uso} preguntas.
   - **EXPLICACION DE FENOMENOS**: {k_exp} preguntas.

3. POR DIFICULTAD:
   - Facil: {d_fac} preguntas (Nivel 1-2)
   - Media: {d_med} preguntas (Nivel 2-3)
   - Dificil: {d_dif} preguntas (Nivel 3-4)

TOTAL DE ESTE LOTE: {chunk_target} preguntas.

!!! INSTRUCCION DE SEGURIDAD Y CALIDAD CIENTIFICA !!!

REGLA DE ORO (RAZONAMIENTO CIENTIFICO):
Para cada pregunta, ANTES de escribir el JSON final, verifica internamente:
1. VALIDEZ FISICA: Si usas formulas, verifica calculos y unidades.
2. VALIDEZ QUIMICA: Reacciones balanceadas, masas molares y estados de oxidacion correctos.
3. PRECISION BIOLOGICA: Terminologia tecnica correcta.

!!! ALINEACION PEDAGOGICA !!!
Cada pregunta debe reflejar: Competencia -> Componente -> Evidencia -> Nivel de Desempeno.
Justifica en `_razonamiento_pedagogico`.

{rag_text_chunk}

RECORDATORIO DE ESTRUCTURA GRAFICA (OBLIGATORIO):
Si usas 'chartjs_line' o 'chartjs_bar', DEBES incluir 'labels' y 'datasets':
  "configuracion_grafico": {{
"tipo_grafico": "chartjs_line",
"titulo_eje_x": "Tiempo (s)", "titulo_eje_y": "Velocidad (m/s)",
"data": {{
   "labels": ["0", "2", "4", "6"],
   "datasets": [{{ "label": "Movil A", "data": [0, 5, 10, 15] }}]
}}
  }}

TU SALIDA DEBE SER UN UNICO JSON:
{{
  "meta": {{
    "area": "{area}",
    "total_preguntas": {chunk_target},
    "fecha_generacion": "{datetime.now().isoformat()}"
  }},
  "preguntas": [
    ... (las {chunk_target} preguntas con "_razonamiento_pedagogico") ...
  ]
}}
"""
            final_prompt = base_prompt_content + cot_instruction
            
            # Intentar generacion con reintentos por lote
            chunk_preguntas = []
            chunk_success = False
            
            for attempt in range(1, MAX_RETRIES_PER_CHUNK + 2):
                try:
                    if attempt == 1:
                        cls._capture_prompt(area, final_prompt, f"ciencias_chunk_{chunk_num}")
                    else:
                        print(f"      🔄 Reintento {attempt - 1}/{MAX_RETRIES_PER_CHUNK}...")
                    
                    data, tokens_this_call, finish_reason, content = cls._llm_complete_json(
                        prompt=final_prompt,
                        generation_model=generation_model,
                        timeout=timeout,
                        context_label=f"ciencias lote {chunk_num}",
                    )
                    total_tokens_used += tokens_this_call
                    
                    if not cls._is_expected_finish_reason(generation_model, finish_reason):
                        print(f"      ⚠️ finish_reason='{finish_reason}' (no esperado para {generation_model})")
                    if cls._should_retry_for_finish_reason(generation_model, finish_reason):
                        print("      ⚠️ Respuesta truncada por max_tokens. Reintentando lote...")
                        if attempt <= MAX_RETRIES_PER_CHUNK:
                            continue
                    
                    chunk_preguntas = data.get("preguntas", [])
                    
                    min_esperado = max(1, chunk_target // 2)
                    if len(chunk_preguntas) < min_esperado:
                        print(f"      ⚠️ Respuesta anomala: {len(chunk_preguntas)}/{chunk_target} preguntas (minimo: {min_esperado})")
                        print(f"      📊 Tokens: {tokens_this_call}, finish_reason: {finish_reason}")
                        try:
                            log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "logs", "anomalous")
                            os.makedirs(log_dir, exist_ok=True)
                            import uuid
                            log_file = os.path.join(log_dir, f"CIENCIAS_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}.txt")
                            with open(log_file, "w", encoding="utf-8") as f:
                                f.write(f"[ANOMALOUS RESPONSE - CIENCIAS CHUNKED]\n")
                                f.write(f"DATE: {datetime.now().isoformat()}\n")
                                f.write(f"CHUNK: {chunk_num}/{num_chunks} (target: {chunk_target})\n")
                                f.write(f"RECEIVED: {len(chunk_preguntas)} preguntas\n")
                                f.write(f"TOKENS: {tokens_this_call}\n")
                                f.write(f"FINISH_REASON: {finish_reason}\n")
                                f.write(f"RESPONSE KEYS: {list(data.keys())}\n")
                                f.write(f"\nRAW CONTENT (first 3000 chars):\n{content[:3000]}\n")
                            print(f"      📼 Log guardado: {os.path.basename(log_file)}")
                        except Exception as log_err:
                            print(f"      ⚠️ Error escribiendo log: {log_err}")
                        
                        if attempt <= MAX_RETRIES_PER_CHUNK:
                            continue
                        else:
                            print(f"      ❌ Lote {chunk_num} agoto reintentos con respuesta insuficiente.")
                            break
                    
                    chunk_success = True
                    print(f"      ✅ Lote {chunk_num}: {len(chunk_preguntas)} preguntas generadas ({tokens_this_call} tokens)")
                    break
                    
                except ValueError as e:
                    print(f"      ❌ Error JSON en lote {chunk_num}: {e}")
                    if attempt <= MAX_RETRIES_PER_CHUNK:
                        continue
                    break
                except Exception as e:
                    print(f"      ❌ Error en lote {chunk_num}: {e}")
                    if attempt <= MAX_RETRIES_PER_CHUNK:
                        continue
                    break
            
            if chunk_success and chunk_preguntas:
                all_preguntas.extend(chunk_preguntas)
                chunks_exitosos += 1
            else:
                print(f"      ❌ Lote {chunk_num} fallido completamente.")
        
        # -- Evaluar resultado global --
        print(f"\n   -- RESULTADO CHUNKED --")
        print(f"   📦 Lotes exitosos: {chunks_exitosos}/{num_chunks}")
        print(f"   📊 Total preguntas obtenidas: {len(all_preguntas)}")
        
        if len(all_preguntas) < max(1, target_preguntas // 2):
            error_msg = f"Generacion chunked insuficiente: {len(all_preguntas)}/{target_preguntas} preguntas ({chunks_exitosos}/{num_chunks} lotes exitosos)"
            print(f"   ❌ {error_msg}")
            return GenerationResult(success=False, error=error_msg)
        
        # Re-numerar IDs consecutivos
        for idx, p in enumerate(all_preguntas):
            p["id"] = idx + 1
            
        simulacro_final = {
            "meta": {
                "area": "Ciencias Naturales",
                "total_preguntas": len(all_preguntas),
                "modo_generacion": f"pipeline_ciencias_chunked_v2 ({num_chunks} lotes)",
                "fecha_generacion": datetime.now().isoformat()
            },
            "preguntas": all_preguntas
        }
        
        result = GenerationResult(success=True, data=simulacro_final)
        result.tokens_used = total_tokens_used
        result.generation_time = time.time() - start_time
        
        print(f"✅ Pipeline Ciencias Chunked finalizado: {len(all_preguntas)} preguntas en {result.generation_time:.1f}s ({total_tokens_used} tokens)")
        return result


    @classmethod
    def _generar_pipeline_sociales_ciudadanas(
        cls,
        area: str,
        institucion_id: int,
        db: Session,
        num_preguntas: int,
        dificultad: dict,
        timeout: int,
        generation_model: Optional[str] = None,
    ) -> GenerationResult:
        """
        Pipeline HIBRIDO CHUNKED para Sociales y Ciudadanas:
        1. Contexto base oficial (num_preguntas=0 para evitar saturar prompt).
        2. Buffer +40% para absorber descartes posteriores en Quality Gates.
        3. Chunking en lotes de 14 preguntas para evitar saturacion de o3.
        4. RAG rotado por lote para diversidad de estilo.
        5. Cuotas fijas por competencia (segun lineamiento institucional) y
           cuotas dinamicas por dificultad (segun request).
        """
        import time
        import math
        from datetime import datetime
        start_time = time.time()

        # -- Configuracion --
        CHUNK_SIZE = cls._chunk_size_for_model(
            generation_model=generation_model,
            default_chunk_size=14,
            sonnet_chunk_size=10,
        )
        MAX_RETRIES_PER_CHUNK = 2

        # 1. Sobre-aprovisionamiento (Buffer del 40%)
        target_preguntas = int(num_preguntas * 1.4)
        if target_preguntas < num_preguntas + 2:
            target_preguntas = num_preguntas + 2

        # 2. Numero de lotes
        num_chunks = math.ceil(target_preguntas / CHUNK_SIZE)

        print(
            f"⚖️ Iniciando Pipeline Sociales CHUNKED "
            f"({num_preguntas} solicitadas -> {target_preguntas} con Buffer)"
        )
        if is_claude_model(generation_model):
            print(f"   🧠 Ajuste Sonnet activo: CHUNK_SIZE={CHUNK_SIZE}")
        print(f"   📦 Dividido en {num_chunks} lote(s) de ~{CHUNK_SIZE} preguntas cada uno")

        # 3. Prompt base sin tarea final (cada chunk inyecta su propia cuota)
        base_prompt_content = cls._construir_prompt(area, institucion_id, db, 0, None)
        if not base_prompt_content:
            return GenerationResult(
                success=False,
                error="No se pudo cargar contexto de Sociales y Ciudadanas"
            )

        # -- RAG DE PATRONES: Recuperar corpus bruto para rotar entre lotes --
        temas_sociales = [
            "Historia de Colombia",
            "Geografia y territorio",
            "Economia y modelos de desarrollo",
            "Constitucion y mecanismos de participacion",
            "Conflictos socioambientales",
            "Derechos humanos y movimientos sociales"
        ]
        all_rag_patterns_sociales = cls._recuperar_pool_patrones_rag(
            area=area,
            topics=temas_sociales,
            n_results_por_topic=2,
            fallback_limit=80
        )
        if all_rag_patterns_sociales:
            print(
                "   ✅ RAG Sociales: "
                f"{len(all_rag_patterns_sociales)} patrones unicos para rotacion."
            )
        else:
            print("   ⚠️ RAG de patrones no disponible para Sociales.")

        def _rotar_patrones_sociales(patrones: list, chunk_idx: int, max_por_lote: int = 4) -> list:
            if not patrones:
                return []
            n = len(patrones)
            start = (chunk_idx * max_por_lote) % n
            seleccion = []
            for i in range(min(max_por_lote, n)):
                idx = (start + i) % n
                seleccion.append(patrones[idx])
            return seleccion

        # -- RAG JURIDICO (Constitucion) pool rotado por lote --
        queries_constitucion = [
            "Derechos fundamentales tutela habeas corpus",
            "Mecanismos participación ciudadana voto plebiscito referendo",
            "Ramas del poder público legislativa ejecutiva judicial",
            "Estado Social de Derecho principios"
        ]
        rag_constitucional_pool = cls._recuperar_pool_constitucional_sociales(
            queries=queries_constitucion,
            n_results_por_query=2,
            fallback_limit=120
        )
        if rag_constitucional_pool:
            print(
                "   ✅ RAG constitucional: "
                f"{len(rag_constitucional_pool)} fragmentos disponibles para rotación por lote."
            )

        def _rotar_rag_constitucional_sociales(fragmentos: list, chunk_idx: int, max_por_lote: int = 4) -> list:
            if not fragmentos:
                return []
            n = len(fragmentos)
            start = (chunk_idx * max_por_lote) % n
            seleccion = []
            for i in range(min(max_por_lote, n)):
                idx = (start + i) % n
                seleccion.append(fragmentos[idx])
            return seleccion

        # -- Distribuciones globales (competencia fija, dificultad dinamica) --
        # Competencias fijas segun lineamiento institucional del proyecto:
        # 35% Pensamiento social, 35% Pensamiento reflexivo y sistemico, 30% Interpretacion.
        total_p_social = int(target_preguntas * 0.35)
        total_p_reflexivo = int(target_preguntas * 0.35)
        total_p_interpret = target_preguntas - total_p_social - total_p_reflexivo

        dificultad_req = dificultad or {"facil": 30, "medio": 40, "dificil": 30}
        total_facil = round(target_preguntas * dificultad_req.get("facil", 30) / 100)
        total_medio = round(target_preguntas * dificultad_req.get("medio", 40) / 100)
        total_dificil = target_preguntas - total_facil - total_medio

        print(
            "   📊 Competencias Globales: "
            f"PensamientoSocial={total_p_social}, "
            f"Interpretacion={total_p_interpret}, "
            f"Reflexivo={total_p_reflexivo}"
        )
        print(f"   📊 Dificultad Global: F={total_facil}, M={total_medio}, D={total_dificil}")

        def _dividir_cuota(total: int, num_partes: int) -> list:
            base = total // num_partes
            resto = total % num_partes
            return [base + (1 if i < resto else 0) for i in range(num_partes)]

        chunks_size = _dividir_cuota(target_preguntas, num_chunks)
        chunks_p_social = _dividir_cuota(total_p_social, num_chunks)
        chunks_p_interpret = _dividir_cuota(total_p_interpret, num_chunks)
        chunks_p_reflexivo = _dividir_cuota(total_p_reflexivo, num_chunks)
        chunks_facil = _dividir_cuota(total_facil, num_chunks)
        chunks_medio = _dividir_cuota(total_medio, num_chunks)
        chunks_dificil = _dividir_cuota(total_dificil, num_chunks)

        # -- Generacion por lotes --
        all_preguntas = []
        total_tokens_used = 0
        chunks_exitosos = 0

        for chunk_idx in range(num_chunks):
            chunk_num = chunk_idx + 1
            chunk_target = chunks_size[chunk_idx]
            c_social = chunks_p_social[chunk_idx]
            c_interpret = chunks_p_interpret[chunk_idx]
            c_reflexivo = chunks_p_reflexivo[chunk_idx]
            d_fac = chunks_facil[chunk_idx]
            d_med = chunks_medio[chunk_idx]
            d_dif = chunks_dificil[chunk_idx]

            print(f"\n   -- LOTE {chunk_num}/{num_chunks} ({chunk_target} preguntas) --")
            print(
                f"      Competencias: Social={c_social}, "
                f"Interpretacion={c_interpret}, Reflexivo={c_reflexivo}"
            )
            print(f"      Dificultad: F={d_fac}, M={d_med}, D={d_dif}")

            chunk_patterns = _rotar_patrones_sociales(all_rag_patterns_sociales, chunk_idx)
            rag_text_chunk = ""
            if chunk_patterns:
                rag_text_chunk = "\n\n# BANCO DE PATRONES DINAMICO (REFERENCIA DE ESTILO)\n"
                rag_text_chunk += "Estos patrones son solo referencia de formato y tono. NO copies contenido.\n"
                rag_text_chunk += "Genera contenido NUEVO cumpliendo la distribucion solicitada.\n"
                for i, p in enumerate(chunk_patterns):
                    rag_text_chunk += f"\n--- PATRON {i+1} ---\n{p}\n"
                print(f"      RAG: {len(chunk_patterns)} patrones inyectados (rotados)")

            chunk_constitucion = _rotar_rag_constitucional_sociales(
                rag_constitucional_pool,
                chunk_idx
            )
            rag_constitucion_chunk = ""
            if chunk_constitucion:
                rag_constitucion_chunk = (
                    "\n\n# CONTEXTO JURIDICO PRIORITARIO (RAG ROTADO)\n"
                    "Use estos articulos oficiales como fuente de verdad:\n"
                    + "\n".join(chunk_constitucion)
                )
                print(
                    "      ⚖️ RAG constitucional: "
                    f"{len(chunk_constitucion)} fragmentos inyectados (rotados)"
                )

            cot_instruction = f"""
________________________________________________________________________________
!!! INSTRUCCION DE DISTRIBUCION OBLIGATORIA (LOTE {chunk_num} DE {num_chunks}) !!!

Debes generar EXACTAMENTE {chunk_target} preguntas con la siguiente distribucion:

1. POR COMPETENCIA:
   - **Pensamiento social**: {c_social} preguntas.
   - **Interpretación y análisis de perspectivas**: {c_interpret} preguntas.
   - **Pensamiento reflexivo y sistémico**: {c_reflexivo} preguntas.

2. POR DIFICULTAD (DINAMICA):
   - Facil: {d_fac} preguntas
   - Medio: {d_med} preguntas
   - Dificil: {d_dif} preguntas

TOTAL DE ESTE LOTE: {chunk_target} preguntas.

{rag_constitucion_chunk}

{rag_text_chunk}

!!! INSTRUCCION DE NEUTRALIDAD Y CONSTITUCIONALIDAD !!!
1. Neutralidad valorativa: no adoctrines ni favorezcas ideologias.
2. Multiperspectivismo: presenta conflicto de actores con argumentos de ambos lados.
3. Para temas juridico-constitucionales, alinea la clave con la Constitucion de 1991.
4. Evita anacronismos en preguntas historicas.

!!! ALINEACION PEDAGOGICA !!!
Cada pregunta debe incluir `_razonamiento_pedagogico` con:
Competencia -> Evidencia -> Nivel de desempeno -> Criterio de neutralidad.

TU SALIDA DEBE SER UN UNICO JSON:
{{
  "meta": {{
    "area": "{area}",
    "total_preguntas": {chunk_target},
    "fecha_generacion": "{datetime.now().isoformat()}"
  }},
  "preguntas": [
    ... (las {chunk_target} preguntas con "_razonamiento_pedagogico") ...
  ]
}}
"""
            final_prompt = base_prompt_content + cot_instruction

            chunk_preguntas = []
            chunk_success = False

            for attempt in range(1, MAX_RETRIES_PER_CHUNK + 2):
                try:
                    if attempt == 1:
                        cls._capture_prompt(area, final_prompt, f"sociales_chunk_{chunk_num}")
                    else:
                        print(f"      🔄 Reintento {attempt - 1}/{MAX_RETRIES_PER_CHUNK}...")

                    data, tokens_this_call, finish_reason, content = cls._llm_complete_json(
                        prompt=final_prompt,
                        generation_model=generation_model,
                        timeout=timeout,
                        context_label=f"sociales lote {chunk_num}",
                    )
                    total_tokens_used += tokens_this_call

                    if not cls._is_expected_finish_reason(generation_model, finish_reason):
                        print(f"      ⚠️ finish_reason='{finish_reason}' (no esperado para {generation_model})")
                    if cls._should_retry_for_finish_reason(generation_model, finish_reason):
                        print("      ⚠️ Respuesta truncada por max_tokens. Reintentando lote...")
                        if attempt <= MAX_RETRIES_PER_CHUNK:
                            continue

                    chunk_preguntas = data.get("preguntas", [])

                    min_esperado = max(1, chunk_target // 2)
                    if len(chunk_preguntas) < min_esperado:
                        print(
                            f"      ⚠️ Respuesta anomala: {len(chunk_preguntas)}/{chunk_target} "
                            f"preguntas (minimo: {min_esperado})"
                        )
                        print(f"      📊 Tokens: {tokens_this_call}, finish_reason: {finish_reason}")
                        try:
                            log_dir = os.path.join(
                                os.path.dirname(
                                    os.path.dirname(
                                        os.path.dirname(os.path.abspath(__file__))
                                    )
                                ),
                                "logs",
                                "anomalous"
                            )
                            os.makedirs(log_dir, exist_ok=True)
                            import uuid
                            log_file = os.path.join(
                                log_dir,
                                f"SOCIALES_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}.txt"
                            )
                            with open(log_file, "w", encoding="utf-8") as f:
                                f.write("[ANOMALOUS RESPONSE - SOCIALES CHUNKED]\n")
                                f.write(f"DATE: {datetime.now().isoformat()}\n")
                                f.write(f"CHUNK: {chunk_num}/{num_chunks} (target: {chunk_target})\n")
                                f.write(f"RECEIVED: {len(chunk_preguntas)} preguntas\n")
                                f.write(f"TOKENS: {tokens_this_call}\n")
                                f.write(f"FINISH_REASON: {finish_reason}\n")
                                f.write(f"RESPONSE KEYS: {list(data.keys())}\n")
                                f.write(f"\nRAW CONTENT (first 3000 chars):\n{content[:3000]}\n")
                            print(f"      📼 Log guardado: {os.path.basename(log_file)}")
                        except Exception as log_err:
                            print(f"      ⚠️ Error escribiendo log: {log_err}")

                        if attempt <= MAX_RETRIES_PER_CHUNK:
                            continue
                        print(f"      ❌ Lote {chunk_num} agoto reintentos con respuesta insuficiente.")
                        break

                    chunk_success = True
                    print(
                        f"      ✅ Lote {chunk_num}: "
                        f"{len(chunk_preguntas)} preguntas generadas ({tokens_this_call} tokens)"
                    )
                    break

                except ValueError as e:
                    print(f"      ❌ Error JSON en lote {chunk_num}: {e}")
                    if attempt <= MAX_RETRIES_PER_CHUNK:
                        continue
                    break
                except Exception as e:
                    print(f"      ❌ Error en lote {chunk_num}: {e}")
                    if attempt <= MAX_RETRIES_PER_CHUNK:
                        continue
                    break

            if chunk_success and chunk_preguntas:
                all_preguntas.extend(chunk_preguntas)
                chunks_exitosos += 1
            else:
                print(f"      ❌ Lote {chunk_num} fallido completamente.")

        print("\n   -- RESULTADO CHUNKED --")
        print(f"   📦 Lotes exitosos: {chunks_exitosos}/{num_chunks}")
        print(f"   📊 Total preguntas obtenidas: {len(all_preguntas)}")

        if len(all_preguntas) < max(1, target_preguntas // 2):
            error_msg = (
                "Generacion chunked insuficiente: "
                f"{len(all_preguntas)}/{target_preguntas} preguntas "
                f"({chunks_exitosos}/{num_chunks} lotes exitosos)"
            )
            print(f"   ❌ {error_msg}")
            return GenerationResult(success=False, error=error_msg)

        for idx, p in enumerate(all_preguntas):
            p["id"] = idx + 1

        simulacro_final = {
            "meta": {
                "area": "Sociales y Ciudadanas",
                "total_preguntas": len(all_preguntas),
                "modo_generacion": f"pipeline_sociales_chunked_v2 ({num_chunks} lotes)",
                "fecha_generacion": datetime.now().isoformat()
            },
            "preguntas": all_preguntas
        }

        result = GenerationResult(success=True, data=simulacro_final)
        result.tokens_used = total_tokens_used
        result.generation_time = time.time() - start_time

        print(
            "✅ Pipeline Sociales Chunked finalizado: "
            f"{len(all_preguntas)} preguntas en {result.generation_time:.1f}s "
            f"({total_tokens_used} tokens)"
        )
        return result

    @classmethod
    def _construir_prompt(
        cls,
        area: str,
        institucion_id: int,
        db: Session,
        num_preguntas: int,
        dificultad: dict = None
    ) -> Optional[str]:
        """
        Construye el prompt final concatenando:
        1. Prompt base del área
        2. Contexto curado (marco, niveles, ejemplos)
        3. Preguntas ya usadas
        """
        folder = AREA_FOLDERS.get(area)
        if not folder:
            return None
        
        area_path = os.path.join(STATIC_DIR, folder, "extracted")
        
        # Verificar que existe la carpeta
        if not os.path.exists(area_path):
            print(f"⚠️ Carpeta no encontrada: {area_path}")
            return None
        
        prompt_parts = []
        
        # Inicializar caché de Redis (compartido para todo el método)
        try:
            from app.core.redis_config import ContextCache, is_redis_available
            redis_cache_available = is_redis_available()
            if redis_cache_available:
                context_cache = ContextCache()
        except Exception:
            redis_cache_available = False
        
        # 1. Cargar prompt base (buscar varios nombres posibles)
        # area.lower() para casos como SOCIALES_CIUDADANAS -> sociales_ciudadanas
        area_lower = area.lower()
        prompt_base_names = [
            f"prompt_{folder}.md",        # prompt_ciencias_naturales.md
            f"prompt_{area_lower}.md",    # prompt_sociales_ciudadanas.md
            "prompt.md",                  # prompt.md
        ]
        
        prompt_loaded = False
        for name in prompt_base_names:
            prompt_base_path = os.path.join(area_path, name)
            
            # Función para cargar desde disco
            def load_prompt(path=prompt_base_path):
                if os.path.exists(path):
                    with open(path, 'r', encoding='utf-8') as f:
                        return f.read()
                return None
            
            # Intentar desde caché o disco
            if redis_cache_available:
                content = context_cache.get(area, name, load_prompt)
                if content:
                    prompt_parts.append(content)
                    print(f"📄 Cargado: {name} (caché)")
                    prompt_loaded = True
                    break
            else:
                content = load_prompt()
                if content:
                    prompt_parts.append(content)
                    print(f"📄 Cargado: {name} (disco)")
                    prompt_loaded = True
                    break
        
        if not prompt_loaded:
            print(f"⚠️ No se encontró prompt en {area_path}")
            return None
        
        # 2. Cargar contexto curado (buscar archivos por patrón según área)
        # Mapeo de patrones de archivos por área
        CONTEXT_PATTERNS = {
            "CIENCIAS_NATURALES": [
                ("marco_referencia_ciencias_naturales.md", "Marco de Referencia"),
                ("niveles_desempeno_ciencia_naturales.md", "Niveles de Desempeño"),
                # ("patron_simulacro_001.md", "Ejemplo de Simulacro Oficial"),  <-- REMOVIDO: Usamos RAG
            ],
            "MATEMATICAS": [
                ("marco_referencia_matematicas_optimizado.md", "Marco de Referencia"),
                ("niveles_desempeno_matematicas.md", "Niveles de Desempeño"),
                ("estandares_basicos_matematicas.md", "Estandares basicos de competencias en matemáticas")
            ],
            "SOCIALES_CIUDADANAS": [
                ("marco_referencia_sociales.md", "Marco de Referencia"),
                ("niveles_desempeno_sociales.md", "Niveles de Desempeño"),
                # ("patron_simulacro_sociales_limpio.md", "Ejemplo de Simulacro Oficial"), <-- REMOVIDO: Usamos RAG
            ],
            "LECTURA_CRITICA": [
                ("marco_referencia_lectura_critica_limpio.md", "Marco de Referencia"),
                ("niveles_desempeno_lectura_critica.md", "Niveles de Desempeño"),
                # ("patron_simulacro_lectura_critica_lite.md", "Ejemplo de Simulacro Oficial"), <-- REMOVIDO: Usamos RAG
            ],
            "INGLES": [
                ("marco_referencia_ingles_limpio.md", "Marco de Referencia"),
                ("niveles_desempeno_ingles.md", "Niveles de Desempeño"),
                ("patron_simulacro_ingles.md", "Ejemplo de Simulacro Oficial"), # Se mantiene estático por ahora
            ],
        }
        
        context_files = CONTEXT_PATTERNS.get(area, [])
        
        prompt_parts.append("\n\n---\n\n# 📚 DOCUMENTOS DE REFERENCIA ICFES\n")
        prompt_parts.append("*Usa esta información como contexto para generar preguntas alineadas con los estándares oficiales.*\n")
        
        # Usar caché ya inicializado arriba
        
        for filename, title in context_files:
            filepath = os.path.join(area_path, filename)
            
            # Función para cargar desde disco (filepath capturado por defecto)
            def load_from_disk(path=filepath):
                if os.path.exists(path):
                    with open(path, 'r', encoding='utf-8') as f:
                        return f.read()
                return None
            
            # Intentar desde caché o disco
            if redis_cache_available:
                content = context_cache.get(area, filename, load_from_disk)
                if content:
                    prompt_parts.append(f"\n## {title}\n\n{content}\n")
                    print(f"📄 Cargado: {filename} (caché)")
                else:
                    print(f"⚠️ Archivo no encontrado: {filename}")
            else:
                # Sin Redis, cargar directamente del disco
                content = load_from_disk()
                if content:
                    prompt_parts.append(f"\n## {title}\n\n{content}\n")
                    print(f"📄 Cargado: {filename} (disco)")
                else:
                    print(f"⚠️ Archivo no encontrado: {filename}")
        
        # 3. Cargar preguntas ya usadas de esta institución y área
        # [PHASE 1 SCALABILITY]
        # Estrategia de Deduplicación: "Blind Generation" + Gate 3.
        # Ya no inyectamos el historial de preguntas ("Negative Constraints") al prompt.
        # Esto reduce el consumo de tokens de O(N) a O(1) y evita diluir la atención del modelo.
        # La deduplicación se delega completamente al Gate 3 (Hashing + Fuzzy Search).
        pass
        
        # 4. Instrucción final (Solo si se solicita generación directa)
        if num_preguntas > 0:
            prompt_parts.append(f"\n\n---\n\n# 🎯 TAREA\n")
            prompt_parts.append(f"Genera exactamente **{num_preguntas} preguntas** nuevas para el área de **{AREA_NAMES.get(area, area)}**.\n")
            
            # Agregar instrucción de dificultad si se especificó
            if dificultad:
                facil = dificultad.get('facil', 30)
                medio = dificultad.get('medio', 40)
                dificil = dificultad.get('dificil', 30)
                
                # Calcular número aproximado de preguntas por nivel
                n_facil = round(num_preguntas * facil / 100)
                n_medio = round(num_preguntas * medio / 100)
                n_dificil = num_preguntas - n_facil - n_medio  # El resto para evitar errores de redondeo
                
                prompt_parts.append(f"\n## DISTRIBUCIÓN DE DIFICULTAD OBLIGATORIA (CALIBRACIÓN ICFES):\n")
                prompt_parts.append(f"- **{facil}% preguntas FÁCILES** (~{n_facil}): Nivel 2. Requieren análisis básico: interpretar datos, identificar patrones simples o aplicar un concepto en contexto cotidiano. PROHIBIDO: Preguntas triviales donde la respuesta se obtiene solo con lectura directa o una operación aritmética inmediata sin razonamiento.\n")
                prompt_parts.append(f"- **{medio}% preguntas de dificultad MEDIA** (~{n_medio}): Nivel 2-3. Requieren relacionar información dispersa, realizar inferencias, o aplicar conocimientos en contextos no rutinarios.\n")
                prompt_parts.append(f"- **{dificil}% preguntas DIFÍCILES** (~{n_dificil}): Nivel 3-4. Requieren evaluar la validez de enunciados/hipótesis, reflexionar sobre el sentido global, contrastar perspectivas o resolver problemas complejos de múltiples pasos.\n")
                
                prompt_parts.append("\n⚠️ RESTRICCIÓN DE CALIDAD: Evita a toda costa preguntas 'tontas' o evidentes. Incluso una pregunta fácil debe retar intelectualmente al estudiante de Grado 11.\n")
                prompt_parts.append(f"\nIMPORTANTE: Asigna a cada pregunta un campo `dificultad` con valor 'facil', 'medio' o 'dificil'.\n")
            
            prompt_parts.append("Sigue ESTRICTAMENTE las instrucciones del prompt y el formato JSON especificado.\n")
        
        return "\n".join(prompt_parts)
    
    @classmethod
    def reparar_preguntas(
        cls,
        preguntas_problematicas: list,
        errores: list,
        area: str,
        timeout: int = 120,
        generation_model: Optional[str] = None,
    ) -> GenerationResult:
        """
        Repara preguntas que fallaron en los Quality Gates.
        
        Args:
            preguntas_problematicas: Lista de preguntas con errores
            errores: Lista de errores específicos por pregunta
            area: Área del simulacro
            timeout: Timeout en segundos
            
        Returns:
            GenerationResult con las preguntas reparadas
        """
        import time
        start_time = time.time()
        
        try:
            generation_model = cls._normalize_generation_model(generation_model)
            cls._ensure_model_api_key(generation_model)
        except Exception as e:
            return GenerationResult(success=False, error=str(e))
        
        if not preguntas_problematicas:
            return GenerationResult(success=True, data={"preguntas": []})

        # ---------------------------------------------------------
        # 1. CARGA DE CONTEXTO (Igual que en _construir_prompt)
        # ---------------------------------------------------------
        folder = AREA_FOLDERS.get(area)
        if not folder:
            return GenerationResult(success=False, error=f"Área no soportada: {area}")
        
        area_path = os.path.join(STATIC_DIR, folder, "extracted")
        if not os.path.exists(area_path):
             return GenerationResult(success=False, error=f"Carpeta no encontrada: {area_path}")

        context_parts = []
        
        # Redis Cache setup
        try:
            from app.core.redis_config import ContextCache, is_redis_available
            redis_cache_available = is_redis_available()
            if redis_cache_available:
                context_cache = ContextCache()
        except Exception:
            redis_cache_available = False

        # 1.1 Prompt Base
        area_lower = area.lower()
        prompt_base_names = [f"prompt_{folder}.md", f"prompt_{area_lower}.md", "prompt.md"]
        
        for name in prompt_base_names:
            filepath = os.path.join(area_path, name)
            content = None
            
            def load_from_disk(path=filepath):
                if os.path.exists(path):
                    with open(path, 'r', encoding='utf-8') as f: return f.read()
                return None

            if redis_cache_available:
                content = context_cache.get(area, name, load_from_disk)
            else:
                content = load_from_disk()
                
            if content:
                context_parts.append(content)
                print(f"📄 [Repair] Prompt base cargado: {name}")
                break

        # 1.2 Documentos ICFES
        CONTEXT_PATTERNS = {
            "CIENCIAS_NATURALES": [
                ("marco_referencia_ciencias_naturales.md", "Marco de Referencia"),
                ("niveles_desempeno_ciencia_naturales.md", "Niveles de Desempeño"),
                # ("patron_simulacro_001.md", "Ejemplo de Simulacro Oficial"), <-- REMOVIDO: Usamos RAG
            ],
            "MATEMATICAS": [
                ("marco_referencia_matematicas_optimizado.md", "Marco de Referencia"),
                ("niveles_desempeno_matematicas.md", "Niveles de Desempeño"),
                ("estandares_basicos_matematicas.md", "Estandares basicos de competencias en matemáticas")
            ],
            "SOCIALES_CIUDADANAS": [
                ("marco_referencia_sociales.md", "Marco de Referencia"),
                ("niveles_desempeno_sociales.md", "Niveles de Desempeño"),
                # ("patron_simulacro_sociales_limpio.md", "Ejemplo de Simulacro Oficial"), <-- REMOVIDO: Usamos RAG
            ],
            "LECTURA_CRITICA": [
                ("marco_referencia_lectura_critica_limpio.md", "Marco de Referencia"),
                ("niveles_desempeno_lectura_critica.md", "Niveles de Desempeño"),
                # ("patron_simulacro_lectura_critica_lite.md", "Ejemplo de Simulacro Oficial"), <-- REMOVIDO: Usamos RAG
            ],
            "INGLES": [
                ("marco_referencia_ingles_limpio.md", "Marco de Referencia"),
                ("niveles_desempeno_ingles.md", "Niveles de Desempeño"),
                ("patron_simulacro_ingles.md", "Ejemplo de Simulacro Oficial"),
            ],
        }
        
        context_files = CONTEXT_PATTERNS.get(area, [])
        if context_files:
            context_parts.append("\\n\\n---\\n\\n# 📚 DOCUMENTOS DE REFERENCIA ICFES (CONTEXTO)\\n")
            for filename, title in context_files:
                filepath = os.path.join(area_path, filename)
                content = None
                
                def load_from_disk(path=filepath):
                    if os.path.exists(path):
                        with open(path, 'r', encoding='utf-8') as f: return f.read()
                    return None

                if redis_cache_available:
                    content = context_cache.get(area, filename, load_from_disk)
                else:
                    content = load_from_disk()

                if content:
                    context_parts.append(f"\\n## {title}\\n\\n{content}\\n")

        full_context = "\\n".join(context_parts)

        # ---------------------------------------------------------
        # 2. CONSTRUCCIÓN DEL PROMPT DE REPARACIÓN
        # ---------------------------------------------------------
        repair_prompt = f"""{full_context}

---

# 🛠️ TAREA DE CORRECCIÓN DE CALIDAD

{cls._recuperar_patrones_rag(area, topics=["Patrón General", "Ejemplo"], n_total=3)}


Has generado previamente un simulacro, pero algunas preguntas fueron **RECHAZADAS** por nuestros validadores de calidad (Quality Gates).
Tu tarea es **REGENERAR** estas preguntas específicas para corregir los errores detectados.

## ⚠️ REGLAS DE ORO PARA LA REPARACIÓN:

1.  **MANTENER ID**: Usa exactamente el mismo `id` numérico que la pregunta original.
2.  **CONTEXTO AUTÓNOMO**: La nueva pregunta debe incluir TODO su contexto necesario (texto de lectura, descripción de gráfico, situación problema). No asumas que "ya se dijo antes". **Genera un contexto nuevo y completo para esta pregunta.**
3.  **CORREGIR EL ERROR**: Lee el motivo del rechazo y asegúrate de no cometerlo de nuevo.
    *   Si el error es *Gate 5 (Semántica)* o *Gate 5B (Contexto)*: Significa que la pregunta no tenía sentido con su texto base o estaba alucinada. -> **SOLUCIÓN: Crea un texto base/contexto nuevo y coherente.**
    *   Si el error especifica "respuesta_invalida" o temas científicos (Genética, Física, Química): **REVISA TU TEORÍA**. No confíes en tu primer intento. Verifica proporciones, fórmulas y leyes antes de generar la respuesta.
    *   Si el error es *Gate 7 (Validación)*: Significa que el cálculo o la lógica era incorrecta. -> **SOLUCIÓN: Verifica paso a paso la respuesta correcta.**

## LISTA DE PREGUNTAS A REPARAR:
"""
        
        for i, (pregunta, error_info) in enumerate(zip(preguntas_problematicas, errores), 1):
            pregunta_id = pregunta.get("id", i)
            pregunta_dump = json.dumps(pregunta, ensure_ascii=False, indent=2)
            
            repair_prompt += f"""
### 🔴 Pregunta ID {pregunta_id} (RECHAZADA)
**Motivo del rechazo**: {error_info}

**Versión anterior (con errores)**:
```json
{pregunta_dump}
```

👉 **INSTRUCCIÓN:** Ignora la versión anterior. Genera una pregunta NUEVA para el ID {pregunta_id} que sea pedagógicamente perfecta y no tenga el error mencionado.
Asegúrate de incluir todos los campos: `contexto`, `enunciado`, `opciones`, `respuesta_correcta` (A,B,C,D), `justificacion`, `dificultad`, `competencia`, `componente`, `tema`.

---
"""
        
        repair_prompt += """
## 🧠 PROCESO DE AUTO-CORRECCIÓN (SELF-CORRECTION):
Para CADA pregunta rechazada, antes de escribir el JSON, realiza mentalmente el siguiente análisis:
1. **DIAGNÓSTICO**: ¿Por qué falló la pregunta anterior? (Ej: ¿Cálculo mal? ¿Lectura superficial? ¿Opción incorrecta?)
2. **ESTRATEGIA**: ¿Qué voy a cambiar para asegurar que no vuelva a pasar?
3. **VERIFICACIÓN**: Si la pregunta requiere matemáticas o ciencia, **resuelve el problema desde cero** para confirmar la nueva clave.

## FORMATO DE SALIDA (JSON ÚNICO)
Devuelve UN solo objeto JSON estrictamente con esta estructura:

```json
{
  "preguntas_reparadas": [
    {
      "id": 1,
      "competencia": "...",
      "componente": "...",
      "tema": "...",
      "dificultad": "...",
      "contexto": "TEXTO O SITUACIÓN COMPLETA NUEVA...",
      "enunciado": "¿Texto completo de la pregunta...?",
      "opciones": [
        {"id": "A", "literal": "A", "texto": "Opción A..."},
        {"id": "B", "literal": "B", "texto": "Opción B..."},
        {"id": "C", "literal": "C", "texto": "Opción C..."},
        {"id": "D", "literal": "D", "texto": "Opción D..."}
      ],
      "respuesta_correcta": "A",
      "justificacion": "...",
      "_analisis_correccion": "RCA (Root Cause Analysis): Explica brevemente por qué falló la anterior y cómo esta nueva versión soluciona el problema definitivamente."
    },
    ...
  ]
}
```
"""
        
        # ---------------------------------------------------------
        # 3. LLAMADA AL MODELO SELECCIONADO
        # ---------------------------------------------------------
        try:
            print(
                f"🤖 [Repair] Enviando solicitud a {generation_model} "
                f"para {len(preguntas_problematicas)} preguntas..."
            )
            print(f"   Tamaño del prompt enriquecido: {len(repair_prompt)} caracteres")
            
            cls._capture_prompt(area, repair_prompt, "repair_questions")

            repair_json, tokens_used, _, _ = cls._llm_complete_json(
                prompt=repair_prompt,
                generation_model=generation_model,
                timeout=timeout,
                context_label=f"repair de {area}",
            )
            
            # Extraer preguntas reparadas
            preguntas_reparadas = repair_json.get("preguntas_reparadas", [])
            
            result = GenerationResult(success=True, data={"preguntas": preguntas_reparadas})
            result.tokens_used = tokens_used
            
            return result

        except Exception as e:
            import traceback
            traceback.print_exc()
            return GenerationResult(
                success=False,
                error=f"Error en reparación: {str(e)}"
            )

    @classmethod
    def _extraer_parte_ingles_desde_componente(cls, componente: Any) -> Optional[int]:
        """Extrae numero de parte (1-7) desde el campo componente."""
        import re

        raw = str(componente or "")
        match = re.search(r"(?:parte|part)\s*([1-7])", raw, re.IGNORECASE)
        if not match:
            return None
        try:
            part = int(match.group(1))
            return part if 1 <= part <= 7 else None
        except ValueError:
            return None

    @classmethod
    def _es_contexto_referencial_ingles(cls, contexto: Any) -> bool:
        """
        Detecta contextos de referencia cruzada (ej. "same passage as question 24")
        que rompen autonomia cuando una pregunta base es descartada.
        """
        import re

        text = str(contexto or "").strip()
        if not text:
            return False

        normalized = re.sub(r"\s+", " ", text.lower())
        patterns = [
            r"\bsame\s+(passage|text|context)\s+as\s+(question|q|pregunta)\s*\d+\b",
            r"\bsame\s+as\s+(question|q|pregunta)\s*\d+\b",
            r"\bsee\s+(question|q|pregunta)\s*\d+\b",
            r"\buse\s+the\s+same\s+(passage|text|context)\b",
            r"\bcontext:\s*same\b",
        ]

        if not any(re.search(p, normalized) for p in patterns):
            return False

        # Si aparece patron referencial y el texto es corto, casi seguro no es autonomo.
        if len(normalized) <= 260:
            return True

        # Incluso en textos largos, si inicia como referencia es señal fuerte de dependencia.
        if re.match(r"^(same|see|use)\b", normalized):
            return True

        return False

    @classmethod
    def _normalizar_contexto_ingles(cls, preguntas: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[int]]:
        """
        Normaliza contextos de ingles para garantizar autonomia por pregunta.
        - Si contexto es "same as question X", intenta sustituir por contexto canonico.
        - Prioridad de resolucion: texto_id -> referencia a pregunta -> no resuelto.
        Retorna:
          (preguntas_normalizadas, unresolved_ids)
        """
        import re

        if not preguntas:
            return preguntas, []

        canonical_by_texto_id: Dict[str, str] = {}
        canonical_by_question_id: Dict[int, str] = {}

        # Pass 1: construir bancos de contexto canonico (solo contextos no referenciales)
        for p in preguntas:
            qid_raw = p.get("id")
            try:
                qid = int(qid_raw)
            except (TypeError, ValueError):
                qid = None

            ctx = str(p.get("contexto", "") or "").strip()
            if not ctx or cls._es_contexto_referencial_ingles(ctx):
                continue

            if qid is not None:
                canonical_by_question_id[qid] = ctx

            texto_id = p.get("texto_id")
            if texto_id is not None:
                key = str(texto_id).strip()
                if key:
                    prev = canonical_by_texto_id.get(key, "")
                    if len(ctx) > len(prev):
                        canonical_by_texto_id[key] = ctx

        # Pass 2: reparar referencias
        unresolved_ids: List[int] = []
        for p in preguntas:
            ctx = str(p.get("contexto", "") or "").strip()
            needs_repair = (not ctx) or cls._es_contexto_referencial_ingles(ctx)
            if not needs_repair:
                continue

            replacement = None

            texto_id = p.get("texto_id")
            if texto_id is not None:
                replacement = canonical_by_texto_id.get(str(texto_id).strip())

            if not replacement and ctx:
                ref_match = re.search(r"(?:question|q|pregunta)\s*(\d+)", ctx, re.IGNORECASE)
                if ref_match:
                    try:
                        ref_qid = int(ref_match.group(1))
                        replacement = canonical_by_question_id.get(ref_qid)
                    except ValueError:
                        replacement = None

            if replacement:
                p["contexto"] = replacement
            else:
                try:
                    unresolved_ids.append(int(p.get("id")))
                except (TypeError, ValueError):
                    continue

        # Unicos y ordenados para logs estables
        unresolved_ids = sorted(list(set(unresolved_ids)))
        return preguntas, unresolved_ids

    @classmethod
    def _generar_pipeline_ingles(
        cls,
        area: str,
        institucion_id: int,
        db: Session,
        num_preguntas: int,
        dificultad: Optional[Any],
        timeout: int = 120,
        generation_model: Optional[str] = None,
    ) -> GenerationResult:
        """
        Pipeline CHUNKED para INGLES:
        - Buffer del 40%
        - Lotes de maximo 14 preguntas
        - Contexto estatico completo en cada llamada (prompt base + marco + niveles + patron estatico .md)
        - Blindaje anti-referencias cruzadas (same as question X)
        """
        import time
        import math
        from datetime import datetime

        start_time = time.time()

        CHUNK_SIZE = cls._chunk_size_for_model(
            generation_model=generation_model,
            default_chunk_size=14,
            sonnet_chunk_size=10,
        )
        MAX_RETRIES_PER_CHUNK = 2

        # 1) Buffer
        target_preguntas = int(num_preguntas * 1.4)
        if target_preguntas < num_preguntas + 2:
            target_preguntas = num_preguntas + 2

        num_chunks = math.ceil(target_preguntas / CHUNK_SIZE)
        print(f"🇬🇧 Iniciando Pipeline Inglés CHUNKED ({num_preguntas} -> {target_preguntas} preguntas)")
        if is_claude_model(generation_model):
            print(f"   🧠 Ajuste Sonnet activo: CHUNK_SIZE={CHUNK_SIZE}")
        print(f"   📦 Dividido en {num_chunks} lote(s) de ~{CHUNK_SIZE} preguntas")

        # 2) Validar contexto estatico obligatorio de Ingles
        folder = AREA_FOLDERS.get(area)
        area_path = os.path.join(STATIC_DIR, folder, "extracted") if folder else ""
        required_static_files = [
            "prompt_ingles.md",
            "marco_referencia_ingles_limpio.md",
            "niveles_desempeno_ingles.md",
            "patron_simulacro_ingles.md",
        ]
        for filename in required_static_files:
            filepath = os.path.join(area_path, filename)
            if (not os.path.exists(filepath)) or os.path.getsize(filepath) == 0:
                return GenerationResult(
                    success=False,
                    error=(
                        f"Contexto estatico obligatorio faltante o vacio para Ingles: {filename}. "
                        "Se requiere prompt base + marco + niveles + patron estatico."
                    )
                )

        # 3) Contexto base sin tarea final (evita contradiccion con cuotas por lote)
        base_prompt_content = cls._construir_prompt(area, institucion_id, db, 0, None)
        if not base_prompt_content:
            return GenerationResult(success=False, error="No se pudo cargar contexto Inglés")

        def _dividir_cuota(total: int, num_partes: int) -> list:
            base = total // num_partes
            resto = total % num_partes
            return [base + (1 if i < resto else 0) for i in range(num_partes)]

        def _english_target_by_part_local(total_questions: int, dificultad_cfg: Optional[Any]) -> Dict[int, int]:
            dificultad_req = dificultad_cfg or {"facil": 30, "medio": 40, "dificil": 30}
            target_facil = round(total_questions * dificultad_req.get("facil", 30) / 100)
            target_medio = round(total_questions * dificultad_req.get("medio", 40) / 100)
            target_dificil = total_questions - target_facil - target_medio

            target_by_part = {i: 0 for i in range(1, 8)}

            def allocate(total: int, parts_order: List[int]):
                if total <= 0 or not parts_order:
                    return
                base = total // len(parts_order)
                rem = total % len(parts_order)
                for p in parts_order:
                    target_by_part[p] += base
                for p in parts_order[:rem]:
                    target_by_part[p] += 1

            allocate(target_facil, [1, 3, 2])
            allocate(target_medio, [4, 5])
            allocate(target_dificil, [6, 7])

            if total_questions >= 30:
                for p in range(1, 8):
                    target_by_part[p] = max(target_by_part[p], 1)
                overflow = sum(target_by_part.values()) - total_questions
                rebalance_order = [1, 2, 3, 4, 5, 6, 7]
                while overflow > 0:
                    moved = False
                    for p in rebalance_order:
                        if target_by_part[p] > 1:
                            target_by_part[p] -= 1
                            overflow -= 1
                            moved = True
                            if overflow == 0:
                                break
                    if not moved:
                        break

            return target_by_part

        # 5) Cuotas globales por parte y dificultad
        dificultad_req = dificultad or {"facil": 30, "medio": 40, "dificil": 30}
        total_facil = round(target_preguntas * dificultad_req.get("facil", 30) / 100)
        total_medio = round(target_preguntas * dificultad_req.get("medio", 40) / 100)
        total_dificil = target_preguntas - total_facil - total_medio
        total_by_part = _english_target_by_part_local(target_preguntas, dificultad)

        print(
            "   📊 Cuotas globales por parte: "
            + ", ".join([f"P{k}={v}" for k, v in total_by_part.items()])
        )
        print(f"   📊 Dificultad global: F={total_facil}, M={total_medio}, D={total_dificil}")

        chunks_size = _dividir_cuota(target_preguntas, num_chunks)
        chunks_facil = _dividir_cuota(total_facil, num_chunks)
        chunks_medio = _dividir_cuota(total_medio, num_chunks)
        chunks_dificil = _dividir_cuota(total_dificil, num_chunks)
        chunks_by_part = {p: _dividir_cuota(total_by_part[p], num_chunks) for p in range(1, 8)}

        # 6) Generacion por lotes
        all_preguntas = []
        total_tokens_used = 0
        chunks_exitosos = 0

        for chunk_idx in range(num_chunks):
            chunk_num = chunk_idx + 1
            chunk_target = chunks_size[chunk_idx]
            d_fac = chunks_facil[chunk_idx]
            d_med = chunks_medio[chunk_idx]
            d_dif = chunks_dificil[chunk_idx]
            part_quotas = {p: chunks_by_part[p][chunk_idx] for p in range(1, 8)}

            print(f"\n   -- LOTE {chunk_num}/{num_chunks} ({chunk_target} preguntas) --")
            print("      Partes: " + ", ".join([f"P{p}={part_quotas[p]}" for p in range(1, 8)]))
            print(f"      Dificultad: F={d_fac}, M={d_med}, D={d_dif}")

            chunk_instruction = f"""
________________________________________________________________________________
!!! INSTRUCCION DE DISTRIBUCION OBLIGATORIA (LOTE {chunk_num} DE {num_chunks}) !!!

Debes generar EXACTAMENTE {chunk_target} preguntas con esta distribucion:

POR PARTE:
- Parte 1: {part_quotas[1]}
- Parte 2: {part_quotas[2]}
- Parte 3: {part_quotas[3]}
- Parte 4: {part_quotas[4]}
- Parte 5: {part_quotas[5]}
- Parte 6: {part_quotas[6]}
- Parte 7: {part_quotas[7]}

POR DIFICULTAD:
- Facil: {d_fac}
- Medio: {d_med}
- Dificil: {d_dif}

REGLA CRITICA DE CONTEXTO AUTONOMO:
1. PROHIBIDO escribir referencias cruzadas del tipo:
   - "same as question X"
   - "same passage as question X"
   - "see question X"
2. Cada pregunta debe ser AUTOCONTENIDA en su propio `contexto`.
3. Si varias preguntas comparten texto (Partes 4 y 7), usa `texto_id` comun, pero repite el texto completo en `contexto` en cada pregunta.
4. Nunca dependas de otra pregunta para que esta se pueda responder.

ALINEACION PEDAGOGICA:
Para cada pregunta, incluye `_razonamiento_pedagogico` con:
Parte -> Nivel MCER -> Evidencia segun marco de referencia.

TU SALIDA DEBE SER UN UNICO JSON:
{{
  "meta": {{
    "area": "INGLES",
    "total_preguntas": {chunk_target},
    "fecha_generacion": "{datetime.now().isoformat()}"
  }},
  "preguntas": [
    ... (las {chunk_target} preguntas) ...
  ]
}}
"""

            final_prompt = base_prompt_content + chunk_instruction

            chunk_preguntas = []
            chunk_success = False

            for attempt in range(1, MAX_RETRIES_PER_CHUNK + 2):
                try:
                    if attempt == 1:
                        cls._capture_prompt(area, final_prompt, f"ingles_chunk_{chunk_num}")
                    else:
                        print(f"      🔄 Reintento {attempt - 1}/{MAX_RETRIES_PER_CHUNK}...")

                    data, tokens_this_call, finish_reason, content = cls._llm_complete_json(
                        prompt=final_prompt,
                        generation_model=generation_model,
                        timeout=timeout,
                        context_label=f"ingles lote {chunk_num}",
                    )
                    total_tokens_used += tokens_this_call

                    if not cls._is_expected_finish_reason(generation_model, finish_reason):
                        print(f"      ⚠️ finish_reason='{finish_reason}' (no esperado para {generation_model})")
                    if cls._should_retry_for_finish_reason(generation_model, finish_reason):
                        print("      ⚠️ Respuesta truncada por max_tokens. Reintentando lote...")
                        if attempt <= MAX_RETRIES_PER_CHUNK:
                            continue

                    raw_chunk = data.get("preguntas", [])

                    # IDs temporales para normalizacion defensiva de contexto
                    for idx_tmp, p in enumerate(raw_chunk):
                        p["id"] = idx_tmp + 1

                    normalized_chunk, unresolved_chunk = cls._normalizar_contexto_ingles(raw_chunk)
                    if unresolved_chunk:
                        print(
                            "      ⚠️ Contextos ingles no resueltos en lote "
                            f"{chunk_num}: {unresolved_chunk}"
                        )
                        unresolved_set = set(unresolved_chunk)
                        normalized_chunk = [p for p in normalized_chunk if p.get("id") not in unresolved_set]

                    chunk_preguntas = normalized_chunk

                    min_esperado = max(1, chunk_target // 2)
                    if len(chunk_preguntas) < min_esperado:
                        print(
                            f"      ⚠️ Respuesta anomala: {len(chunk_preguntas)}/{chunk_target} "
                            f"preguntas (minimo: {min_esperado})"
                        )
                        print(f"      📊 Tokens: {tokens_this_call}, finish_reason: {finish_reason}")
                        if attempt <= MAX_RETRIES_PER_CHUNK:
                            continue
                        print(f"      ❌ Lote {chunk_num} agoto reintentos con respuesta insuficiente.")
                        break

                    chunk_success = True
                    print(f"      ✅ Lote {chunk_num}: {len(chunk_preguntas)} preguntas generadas ({tokens_this_call} tokens)")
                    break

                except ValueError as e:
                    print(f"      ❌ Error JSON en lote {chunk_num}: {e}")
                    if attempt <= MAX_RETRIES_PER_CHUNK:
                        continue
                    break
                except Exception as e:
                    print(f"      ❌ Error en lote {chunk_num}: {e}")
                    if attempt <= MAX_RETRIES_PER_CHUNK:
                        continue
                    break

            if chunk_success and chunk_preguntas:
                all_preguntas.extend(chunk_preguntas)
                chunks_exitosos += 1
            else:
                print(f"      ❌ Lote {chunk_num} fallido completamente.")

        # 7) Evaluacion global
        print(f"\n   -- RESULTADO CHUNKED INGLES --")
        print(f"   📦 Lotes exitosos: {chunks_exitosos}/{num_chunks}")
        print(f"   📊 Preguntas obtenidas: {len(all_preguntas)}")

        min_chunks_exitosos = 2 if num_chunks >= 3 else 1
        if chunks_exitosos < min_chunks_exitosos:
            error_msg = (
                f"Ingles chunked insuficiente por lotes: {chunks_exitosos}/{num_chunks} "
                f"(minimo requerido: {min_chunks_exitosos})"
            )
            print(f"   ❌ {error_msg}")
            return GenerationResult(success=False, error=error_msg)

        min_total_esperado = max(1, target_preguntas // 2)
        if len(all_preguntas) < min_total_esperado:
            error_msg = (
                f"Ingles chunked insuficiente: {len(all_preguntas)}/{target_preguntas} "
                f"(minimo requerido: {min_total_esperado})"
            )
            print(f"   ❌ {error_msg}")
            return GenerationResult(success=False, error=error_msg)

        # Re-ID global
        for idx, p in enumerate(all_preguntas):
            p["id"] = idx + 1

        # Normalizacion global final anti-referencias cruzadas
        all_preguntas, unresolved_global = cls._normalizar_contexto_ingles(all_preguntas)
        if unresolved_global:
            unresolved_set = set(unresolved_global)
            print(f"   ⚠️ Eliminando {len(unresolved_set)} preguntas con contexto no resoluble: {sorted(unresolved_set)}")
            all_preguntas = [p for p in all_preguntas if p.get("id") not in unresolved_set]
            for idx, p in enumerate(all_preguntas):
                p["id"] = idx + 1

        if len(all_preguntas) < min_total_esperado:
            error_msg = (
                f"Ingles chunked insuficiente tras normalizacion de contexto: "
                f"{len(all_preguntas)}/{target_preguntas} "
                f"(minimo requerido: {min_total_esperado})"
            )
            print(f"   ❌ {error_msg}")
            return GenerationResult(success=False, error=error_msg)

        # Estadisticas
        part_counts = {i: 0 for i in range(1, 8)}
        for p in all_preguntas:
            part = cls._extraer_parte_ingles_desde_componente(p.get("componente"))
            if part:
                part_counts[part] += 1

        simulacro_final = {
            "meta": {
                "area": "Inglés",
                "total_preguntas": len(all_preguntas),
                "modo_generacion": f"pipeline_ingles_chunked_v3 ({num_chunks} lotes)",
                "distribucion_partes": part_counts,
                "fecha_generacion": datetime.now().isoformat()
            },
            "preguntas": all_preguntas
        }

        result = GenerationResult(success=True, data=simulacro_final)
        result.tokens_used = total_tokens_used
        result.generation_time = time.time() - start_time
        print(f"✅ Pipeline Inglés Chunked finalizado: {len(all_preguntas)} preguntas en {result.generation_time:.1f}s")
        return result

    
    @classmethod
    def regenerar_preguntas_completas(
        cls,
        preguntas_a_reemplazar: list,
        area: str,
        institucion_id: int,
        db: Session,
        timeout: int = 180,
        generation_model: Optional[str] = None,
    ) -> GenerationResult:
        """
        Regenera preguntas COMPLETAMENTE nuevas (contexto, gráficos, opciones).
        A diferencia de reparar_preguntas, esto genera contenido totalmente nuevo
        manteniendo solo los IDs originales.
        
        Args:
            preguntas_a_reemplazar: Lista de preguntas a reemplazar (para obtener IDs)
            area: Área del simulacro
            institucion_id: ID de la institución
            db: Sesión de base de datos para cargar contexto
            timeout: Timeout en segundos
            
        Returns:
            GenerationResult con las preguntas completamente nuevas
        """
        import time
        start_time = time.time()
        
        try:
            generation_model = cls._normalize_generation_model(generation_model)
            cls._ensure_model_api_key(generation_model)
        except Exception as e:
            return GenerationResult(success=False, error=str(e))
        
        if not preguntas_a_reemplazar:
            return GenerationResult(success=True, data={"preguntas": []})
        
        # Obtener los IDs y DIFICULTADES a mantener
        instrucciones_por_pregunta = ""
        for p in preguntas_a_reemplazar:
            pid = p.get("id")
            dificultad_original = p.get("dificultad", "medio") # Default a medio si falta
            instrucciones_por_pregunta += f"- Pregunta ID {pid}: Generar con dificultad '{dificultad_original}'\n"
        
        ids_originales = [p.get("id") for p in preguntas_a_reemplazar]
        num_preguntas = len(ids_originales)
        
        # =====================================================================
        # CARGAR CONTEXTO COMPLETO (igual que generación inicial)
        # =====================================================================
        print(f"📚 Cargando contexto completo para regeneración (igual que generación inicial)...")
        
        # Usar _construir_prompt() para obtener todo el contexto oficial
        contexto_completo = cls._construir_prompt(
            area=area,
            institucion_id=institucion_id,
            db=db,
            num_preguntas=num_preguntas,
            dificultad=None  # Usará la distribución por defecto
        )
        
        if not contexto_completo:
            # Fallback: Solo prompt base si _construir_prompt falla
            folder = AREA_FOLDERS.get(area)
            if not folder:
                return GenerationResult(
                    success=False,
                    error=f"Área no soportada: {area}"
                )
            
            area_path = os.path.join(STATIC_DIR, folder, "extracted")
            area_lower = area.lower()
            prompt_base_names = [
                f"prompt_{folder}.md",
                f"prompt_{area_lower}.md",
                "prompt.md",
            ]
            
            for name in prompt_base_names:
                prompt_base_path = os.path.join(area_path, name)
                if os.path.exists(prompt_base_path):
                    with open(prompt_base_path, 'r', encoding='utf-8') as f:
                        contexto_completo = f.read()
                    print(f"⚠️ Usando solo prompt base como fallback: {name}")
                    break
            
            if not contexto_completo:
                return GenerationResult(
                    success=False,
                    error=f"No se encontró prompt base para el área {area}"
                )
        else:
            print(f"✅ Contexto completo cargado (incluye Marco, Niveles, Patrones)")
        
        # =====================================================================
        # CONSTRUIR PROMPT DE REGENERACIÓN CON CONTEXTO COMPLETO
        # =====================================================================
        regeneracion_prompt = f"""{contexto_completo}

---

# 🎯 TAREA DE REGENERACIÓN DE PREGUNTAS

Debes generar exactamente **{num_preguntas} preguntas COMPLETAMENTE NUEVAS** para el área de **{AREA_NAMES.get(area, area)}**.

## ⚠️ IMPORTANTE - REQUISITOS DE CALIDAD:
1. Cada pregunta debe tener un **CONTEXTO NUEVO y ORIGINAL** (no reutilizar los anteriores)
2. Si el área requiere gráficos o visualizaciones, genera **NUEVOS gráficos** con datos diferentes
3. Las opciones de respuesta deben ser **COMPLETAMENTE NUEVAS** y plausibles
4. El enunciado debe ser **DIFERENTE** al que se está reemplazando
5. Aplica los mismos estándares de calidad que para una generación inicial
6. Sigue las distribuciones de competencias/afirmaciones del marco oficial

## 📋 REQUISITOS ESPECÍFICOS POR PREGUNTA:
Debes respetar estrictamente la dificultad solicitada para mantener el balance del simulacro:
{instrucciones_por_pregunta}

## IDs A MANTENER:
Las preguntas deben usar **EXACTAMENTE** estos IDs (en orden): {ids_originales}

## ESTRUCTURA JSON REQUERIDA:
```json
{{
  "preguntas": [
    {{ 
      "id": {ids_originales[0]}, 
      "tema": "...",
      "competencia": "...",
      "componente": "...",
      "contexto": "...", 
      "enunciado": "...", 
      "opciones": [{{"id": "A", "texto": "..."}}, ...], 
      "respuesta_correcta": "A",
      "justificacion": "...",
      "dificultad": "medio|facil|dificil",
      "tiene_grafico": false
    }},
    ...
  ]
}}
```

**RECUERDA:** Genera preguntas con la **MISMA CALIDAD** que si fuera una generación inicial completa.
"""
        
        try:
            print(
                f"   🤖 Regenerando {num_preguntas} preguntas con "
                f"{generation_model} usando prompt completo del área..."
            )
            
            cls._capture_prompt(area, regeneracion_prompt, "regeneration_full")

            regeneration_json, tokens_used, _, _ = cls._llm_complete_json(
                prompt=regeneracion_prompt,
                generation_model=generation_model,
                timeout=timeout,
                context_label=f"regeneración completa de {area}",
            )
            
            # Extraer preguntas regeneradas
            preguntas_regeneradas = regeneration_json.get("preguntas", [])
            
            result = GenerationResult(success=True, data={"preguntas": preguntas_regeneradas})
            result.tokens_used = tokens_used
            result.generation_time = time.time() - start_time
            
            print(f"   ✅ Regeneración completa: {len(preguntas_regeneradas)} preguntas, {result.generation_time:.1f}s")
            
            return result
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return GenerationResult(
                success=False,
                error=f"Error en regeneración completa: {str(e)}"
            )


# Función de conveniencia para uso directo
def generar_simulacro(area: str, institucion_id: int, db: Session) -> GenerationResult:
    """Wrapper simple para generar un simulacro"""
    return SimulacroGenerator.generar(area, institucion_id, db)
