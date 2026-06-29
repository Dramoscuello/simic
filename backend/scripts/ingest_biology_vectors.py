
import os
import json
import chromadb
from chromadb.utils import embedding_functions
from dotenv import load_dotenv
from pathlib import Path


# Configuración de Directorios
BASE_DIR = Path(__file__).resolve().parent.parent # backend/
ROOT_DIR = BASE_DIR.parent # icfes_project/

# Cargar variables de entorno ok
# Carga de Variables de Entorno
env_path = BASE_DIR / '.env'
if not env_path.exists():
    env_path = BASE_DIR / 'app' / '.env'
if not env_path.exists():
    env_path = ROOT_DIR / '.env'

load_dotenv(dotenv_path=env_path)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("❌ ERROR: OPENAI_API_KEY no encontrada en variables de entorno.")

# Rutas
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATASET_PATH = os.path.join(BASE_DIR, "static", "ciencias_naturales", "dataset", "chunks_clean.jsonl")
PERSIST_DIR = os.path.join(BASE_DIR, "data", "chroma_db")

def ingest_vectors():
    print(f"🧬 Iniciando Ingesta de Vectores Biología...")
    print(f"📂 Dataset: {DATASET_PATH}")
    print(f"💾 Persistencia: {PERSIST_DIR}")

    # 1. Configurar Cliente ChromaDB
    chroma_client = chromadb.PersistentClient(path=PERSIST_DIR)
    
    # 2. Configurar Función de Embeddings (OpenAI)
    openai_ef = embedding_functions.OpenAIEmbeddingFunction(
        api_key=OPENAI_API_KEY,
        model_name="text-embedding-3-small"
    )

    # 3. Crear o Obtener Colección
    collection_name = "ciencias_naturales_biologia"
    try:
        # Intentar borrar si existe para re-indexar limpio
        chroma_client.delete_collection(name=collection_name)
        print(f"🗑️  Colección anterior eliminada.")
    except:
        pass

    collection = chroma_client.create_collection(
        name=collection_name,
        embedding_function=openai_ef
    )
    print(f"✨ Colección '{collection_name}' creada.")

    # 4. Leer y Procesar Chunks
    documents = []
    metadatas = []
    ids = []

    count = 0
    batch_size = 100 # Ingestar por lotes

    with open(DATASET_PATH, 'r', encoding='utf-8') as f:
        batch_docs = []
        batch_metas = []
        batch_ids = []
        
        for line in f:
            try:
                data = json.loads(line)
                text = data.get("text", "")
                chunk_id = data.get("chunk_id", f"chunk_{count}")
                
                # Preparar metada (aplanar estructura si es necesario)
                meta = {
                    "doc_id": data.get("doc_id", "unknown"),
                    "source_type": data.get("source_type", "unknown"),
                    "quality_tier": data.get("quality_tier", "unknown")
                }
                # Aplanar estructura
                struct = data.get("structure", {})
                if struct:
                    meta["unit"] = struct.get("unit") or ""
                    meta["subsection"] = struct.get("subsection") or ""
                
                batch_docs.append(text)
                batch_metas.append(meta)
                batch_ids.append(chunk_id)
                
                count += 1

                # Ingestar Batch
                if len(batch_docs) >= batch_size:
                    collection.add(
                        documents=batch_docs,
                        metadatas=batch_metas,
                        ids=batch_ids
                    )
                    print(f"   -> Indexados {count} chunks...")
                    batch_docs = []
                    batch_metas = []
                    batch_ids = []

            except json.JSONDecodeError:
                continue

        # Ingestar remanente
        if batch_docs:
            collection.add(
                documents=batch_docs,
                metadatas=batch_metas,
                ids=batch_ids
            )
            print(f"   -> Indexados {count} chunks (Final).")

    print(f"✅ Ingesta Completada exitosamente.")
    print(f"📊 Total vectores: {count}")

if __name__ == "__main__":
    ingest_vectors()
