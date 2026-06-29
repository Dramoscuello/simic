import os
import re
import sys
import logging
import chromadb
from chromadb.utils import embedding_functions
from pathlib import Path
from dotenv import load_dotenv

# Configuración de Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuración de Directorios
BASE_DIR = Path(__file__).resolve().parent.parent # backend/
ROOT_DIR = BASE_DIR.parent # icfes_project/

# Carga de Variables de Entorno
env_path = BASE_DIR / '.env'
if not env_path.exists():
    env_path = BASE_DIR / 'app' / '.env'
if not env_path.exists():
    env_path = ROOT_DIR / '.env'

logger.info(f"🌍 Intentando cargar variables de entorno desde: {env_path}")
load_dotenv(dotenv_path=env_path)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    logger.error("❌ ERROR: OPENAI_API_KEY no encontrada en variables de entorno.")
    sys.exit(1)

# Configuración ChromaDB
DB_PATH = os.path.join(BASE_DIR, "data", "chroma_db")
COLLECTION_NAME = "patrones_preguntas"
STATIC_DIR = os.path.join(BASE_DIR, "static")

# Mapa de Archivos Fuente
FILES_MAP = {
    "MATEMATICAS": [
        "matematicas/extracted/patron_simulacro_matematicas.md.source_for_rag"
    ],
    "CIENCIAS_NATURALES": [
        "ciencias_naturales/extracted/patron_simulacro_001.md"
    ],
    "SOCIALES_CIUDADANAS": [
        "sociales/extracted/patron_simulacro_sociales_limpio.md"
    ],
    "LECTURA_CRITICA": [
        "lectura_critica/extracted/patron_simulacro_lectura_critica.md"
    ]
}

def parse_markdown_patterns(content, area):
    """
    Parsea contenido buscando patrones. Intenta ser flexible con los formatos:
    - ## P1. Título
    - ### P1. Título
    - **P1. Título**
    """
    patterns = []
    
    # 1. Normalizar saltos de línea
    content = content.replace('\r\n', '\n')

    # Estrategia: Dividir por encabezados de patrones comunes
    # Regex para capturar inicio de patrón: 
    # (##\s*P\d+|###\s*P\d+|\*\*\s*P\d+)
    
    # Regex más robusta para encontrar separadores
    regex_separator = r'(?:\n|^)(?:##|###|\*\*)\s*P(\d+)[\.:\s]'
    
    # Encontramos todos los inicios
    matches = list(re.finditer(regex_separator, content))
    
    if not matches:
        logger.warning(f"⚠️ No se encontraron patrones con formato estándar en {area}")
        return []

    for i, match in enumerate(matches):
        start_idx = match.start()
        # El final es el inicio del siguiente match o el final del string
        end_idx = matches[i+1].start() if i + 1 < len(matches) else len(content)
        
        full_chunk = content[start_idx:end_idx].strip()
        
        # Extraer número del grupo de captura
        p_num = match.group(1)
        
        # Limpieza básica
        # Quitar separadores de markdown al final si existen (tipo ---)
        clean_text = full_chunk.split('\n---')[0].strip()
        
        # Extraer título (primera línea)
        lines = clean_text.split('\n')
        title = lines[0] if lines else f"Patrón {p_num}"
        # Limpiar caracteres de markdown del título
        title = re.sub(r'[#\*]', '', title).strip()

        if len(clean_text) > 50: # Filtro de contenido mínimo
            patterns.append({
                "id": f"{area}_P{p_num}_{i}", 
                "text": clean_text,
                "metadata": {
                    "area": area,
                    "patron_num": int(p_num),
                    "title": title
                }
            })
            
    return patterns

def main():
    logger.info(f"📂 Conectando a ChromaDB en: {DB_PATH}")
    client = chromadb.PersistentClient(path=DB_PATH)
    
    openai_ef = embedding_functions.OpenAIEmbeddingFunction(
        api_key=OPENAI_API_KEY,
        model_name="text-embedding-3-small"
    )

    # 1. Eliminación y Recreación Limpia
    try:
        client.delete_collection(COLLECTION_NAME)
        logger.info(f"🗑️ Colección '{COLLECTION_NAME}' eliminada (Clean Slate).")
    except ValueError:
        logger.info(f"ℹ️ La colección '{COLLECTION_NAME}' no existía.")
    except Exception as e:
        logger.warning(f"⚠️ Aviso al borrar colección: {e}")

    collection = client.create_collection(name=COLLECTION_NAME, embedding_function=openai_ef)
    logger.info(f"✨ Colección '{COLLECTION_NAME}' creada.")

    total_inserted = 0

    # 2. Iterar por Áreas
    for area, file_paths in FILES_MAP.items():
        logger.info(f"🚀 Procesando Área: {area}")
        for rel_path in file_paths:
            full_path = os.path.join(STATIC_DIR, rel_path)
            
            if not os.path.exists(full_path):
                logger.error(f"   ❌ Archivo no encontrado: {full_path}")
                continue
                
            logger.info(f"   📖 Leyendo: {rel_path}")
            try:
                with open(full_path, 'r', encoding='utf-8') as f:
                    content = f.read()
            except Exception as e:
                logger.error(f"   ❌ Error leyendo archivo: {e}")
                continue

            patterns = parse_markdown_patterns(content, area)
            logger.info(f"   🧩 Encontrados {len(patterns)} patrones.")
            
            if not patterns:
                continue

            # Batch Insert
            ids = [p["id"] for p in patterns]
            docs = [p["text"] for p in patterns]
            metas = [p["metadata"] for p in patterns]
            
            # Batch size para evitar errores de red/memoria
            BATCH_SIZE = 20
            for i in range(0, len(ids), BATCH_SIZE):
                end = min(i + BATCH_SIZE, len(ids))
                try:
                    collection.add(
                        ids=ids[i:end],
                        documents=docs[i:end],
                        metadatas=metas[i:end]
                    )
                except Exception as e:
                    logger.error(f"   ⚠️ Error insertando lote {i}-{end}: {e}")
            
            count = len(ids)
            total_inserted += count
            logger.info(f"   ✅ Insertados {count} patrones para {area}.")

    logger.info(f"\n🎉 MIGRACIÓN COMPLETADA. Total patrones en RAG: {total_inserted}")

if __name__ == "__main__":
    main()
