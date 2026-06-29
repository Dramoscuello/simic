
import os
import chromadb
from chromadb.utils import embedding_functions
from pypdf import PdfReader
import re

# Configuración
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) # Subir un nivel desde /scripts
DATA_DIR = os.path.join(BASE_DIR, "data")
CHROMA_PATH = os.path.join(DATA_DIR, "chroma_db")
COLLECTION_NAME = "sociales_ciudadanas_kb"

# Archivos PDF
CONSTITUCION_PDF = os.path.join(DATA_DIR, "constitucio-politica-colombia-1991.pdf")
ESTANDARES_PDF = os.path.join(DATA_DIR, "estandares_basicos_de_competencias.pdf")

def clean_text(text):
    """Limpia el texto extraído del PDF."""
    text = re.sub(r'\s+', ' ', text)  # Eliminar saltos de línea múltiples
    return text.strip()

def chunk_text(text, chunk_size=1000, overlap=100):
    """Divide el texto en fragmentos solapados."""
    chunks = []
    start = 0
    text_len = len(text)
    
    while start < text_len:
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)
        start += (chunk_size - overlap)
        
    return chunks

def extract_text_from_pdf(pdf_path):
    """Extrae texto de un archivo PDF."""
    print(f"📄 Extrayendo texto de: {os.path.basename(pdf_path)}...")
    try:
        reader = PdfReader(pdf_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return clean_text(text)
    except Exception as e:
        print(f"❌ Error leyendo PDF {pdf_path}: {e}")
        return ""

def main():
    print("🚀 Iniciando proceso de vectorización para Sociales y Ciudadanas...")
    
    # 1. Verificar Archivos
    if not os.path.exists(CONSTITUCION_PDF):
        print(f"❌ No encontrado: {CONSTITUCION_PDF}")
        return
    if not os.path.exists(ESTANDARES_PDF):
        print(f"❌ No encontrado: {ESTANDARES_PDF}")
        return

    # 2. Inicializar ChromaDB
    print(f"💾 Conectando a ChromaDB en: {CHROMA_PATH}")
    client = chromadb.PersistentClient(path=CHROMA_PATH)
    
    # Embedding Function (OpenAI)
    # Asegúrate de tener OPENAI_API_KEY en tu entorno
    openai_ef = embedding_functions.OpenAIEmbeddingFunction(
        api_key=os.getenv("OPENAI_API_KEY"),
        model_name="text-embedding-3-small"
    )
    
    # Crear o Reiniciar Colección
    try:
        client.delete_collection(name=COLLECTION_NAME)
        print(f"🗑️  Colección anterior '{COLLECTION_NAME}' eliminada.")
    except Exception:
        pass
        
    collection = client.create_collection(
        name=COLLECTION_NAME,
        embedding_function=openai_ef
    )
    print(f"✅ Colección '{COLLECTION_NAME}' creada.")

    # 3. Procesar Constitución
    const_text = extract_text_from_pdf(CONSTITUCION_PDF)
    if const_text:
        chunks = chunk_text(const_text, chunk_size=800, overlap=100) # Chunks más pequeños para precisión legal
        print(f"🧩 Constitución dividida en {len(chunks)} fragmentos.")
        
        ids = [f"const_chnk_{i}" for i in range(len(chunks))]
        metadatas = [{"source": "Constitucion 1991", "type": "legal"} for _ in range(len(chunks))]
        
        # Ingesta por lotes (batching) para no saturar
        batch_size = 100
        for i in range(0, len(chunks), batch_size):
            end = min(i + batch_size, len(chunks))
            collection.add(
                documents=chunks[i:end],
                ids=ids[i:end],
                metadatas=metadatas[i:end]
            )
            print(f"   -> Insertados chunks {i} a {end}")

    # 4. Procesar Estándares
    std_text = extract_text_from_pdf(ESTANDARES_PDF)
    if std_text:
        chunks = chunk_text(std_text, chunk_size=1000, overlap=100)
        print(f"🧩 Estándares divididos en {len(chunks)} fragmentos.")
        
        ids = [f"std_chnk_{i}" for i in range(len(chunks))]
        metadatas = [{"source": "Estandares Competencias", "type": "pedagogico"} for _ in range(len(chunks))]
        
        for i in range(0, len(chunks), batch_size):
            end = min(i + batch_size, len(chunks))
            collection.add(
                documents=chunks[i:end],
                ids=ids[i:end],
                metadatas=metadatas[i:end]
            )
            print(f"   -> Insertados chunks {i} a {end}")

    print("\n🎉 ¡Vectorización Completada Exitosamente!")
    print(f"📍 Total elementos en colección: {collection.count()}")

if __name__ == "__main__":
    main()
