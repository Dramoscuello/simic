# Scripts del Backend (SIMIC)

Este directorio contiene herramientas para extracción de datos (ETL), ingesta de bases de datos vectoriales (RAG) y mantenimiento de la plataforma.

## Extracción de PDFs (Oficiales)
Scripts encargados de leer marcos de referencia oficiales y extraer el texto en plano.
* **`extract_pdf_ingles.py`** → Extrae texto de PDFs de Inglés.
* **`extract_pdf_lectura.py`** → Extrae texto de PDFs de Lectura Crítica.
* **`extract_pdf_matematicas.py`** → Extrae texto de PDFs de Matemáticas.
* **`extract_pdf_sociales.py`** → Extrae texto de PDFs de Sociales y Ciudadanas.
* **`extract_pdf_text.py`** → Extrae texto de PDFs de Ciencias Naturales.

## ETL y Bases de Datos Vectoriales (ChromaDB)
Scripts que preparan e ingestan conocimiento para el LLM.
* **`etl_unified_rag.py`** → **[MAESTRO]** Ingesta patrones unificados de todas las áreas a la colección `patrones_preguntas` en ChromaDB. Utilizado para inyectar variedad en la generación de preguntas.
* **`vectorize_sociales.py`** → Ingesta la Constitución de 1991 y Estándares Básicos a ChromaDB. Usado por el Juez Constitucional (Gate 10) de Sociales.
* **`clean_biology_dataset.py`** → Limpia y estructura dataset factual de biología.
* **`ingest_biology_vectors.py`** → Vectoriza datos limpios de biología. Usado para prevenir alucinaciones (Gate 8).
* **`curate_ocr_to_chunks.py`** → Toma textos escaneados (OCR) y los divide en fragmentos semánticos (chunks).

## Utilidades y Mantenimiento
* **`create_superuser.py`** → Crea el primer usuario administrador global del sistema (DB Relacional).
* **`backfill_preguntas_usadas_embeddings.py`** → Genera embeddings para preguntas viejas en BD para deduplicación.
* **`test_backend.sh`** → Ejecuta suite de pruebas del backend.
