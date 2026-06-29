# SIMIC — Plataforma de Simulacros ICFES (Saber 11)

SIMIC es una plataforma open source para la **generación, aplicación y análisis** de simulacros tipo ICFES Saber 11. Combina modelos de lenguaje de última generación con marcos oficiales del ICFES para crear exámenes validados, calificar respuestas y entregar reportes pedagógicos detallados.

> ⚠️ **Nota sobre datos oficiales**: los PDFs de marcos de referencia y pruebas oficiales del ICFES no se distribuyen con este repositorio. El código incluye extractores y scripts para que cada institución pueda generar sus propios vectores RAG a partir de documentos públicos obtenidos directamente del ICFES.

> **Fines pedagógicos e investigativos, sin ánimo de lucro.** Este proyecto está diseñado exclusivamente con propósitos educativos y de investigación. El material de referencia del ICFES incluido en `backend/static/` se utiliza bajo el principio de uso legítimo (*fair use*) para investigación educativa, sin intención comercial alguna.

---

## Tabla de contenidos

1. [¿Qué hace SIMIC?](#qué-hace-SIMIC)
2. [¿A quién va dirigido?](#a-quién-va-dirigido)
3. [Stack tecnológico](#stack-tecnológico)
4. [Requisitos previos](#requisitos-previos)
5. [Instalación y configuración](#instalación-y-configuración)
6. [Ejecutar en local](#ejecutar-en-local)
7. [Variables de entorno](#variables-de-entorno)
8. [Pruebas](#pruebas)
9. [Estructura del proyecto](#estructura-del-proyecto)
10. [Despliegue en producción](#despliegue-en-producción)
11. [Contribuir y licencia](#contribuir-y-licencia)

---

## ¿Qué hace SIMIC?

- **Generación IA de simulacros**: crea preguntas por área (Matemáticas, Lectura Crítica, Ciencias Naturales, Sociales y Ciudadanas, Inglés) alineadas con los marcos oficiales del ICFES.
- **Quality Gates**: valida automáticamente estructura, taxonomía, dificultad, deduplicación, coherencia visual, verificación matemática/científica y neutralidad constitucional.
- **Aplicación de simulacros**: interfaz web para que los estudiantes presenten exámenes con cronómetro, guardado parcial y seguimiento de progreso.
- **Reportes pedagógicos**: informes individuales, grupales y por paquete con análisis de fortalezas, debilidades y niveles de desempeño.
- **OMR (Hojas de respuesta físicas)**: genera hojas personalizadas con QR y permite procesar escaneos con visión por computadora.
- **Gestión institucional**: una sola institución con posibles sedes, sistema de créditos y mensajería interna.

---

## ¿A quién va dirigido?

- **Instituciones educativas**: colegios, academias pre-universitarias y centros de preparación que desean aplicar simulacros tipo Saber 11.
- **Administradores académicos**: coordinadores, rectores y directores que gestionan estudiantes, grupos, simulacros y reportes.
- **Docentes**: para revisar desempeño grupal e individual.
- **Estudiantes**: para practicar con simulacros que emulan la prueba real.
- **Desarrolladores**: cualquier persona interesada en adaptar, extender o contribuir al proyecto.

---

## Stack tecnológico

### Backend

| Tecnología | Uso |
|------------|-----|
| Python 3.10+ | Lenguaje principal |
| FastAPI | API REST y WebSockets |
| SQLAlchemy 2.0 | ORM para PostgreSQL |
| Pydantic v2 | Validación de datos |
| PostgreSQL 16 + pgvector | Base de datos relacional y vectorial |
| Redis | Cache, colas de jobs y locks |
| Alembic | Migraciones de base de datos |
| Pytest | Pruebas automatizadas |

### Frontend

| Tecnología | Uso |
|------------|-----|
| Vue.js 3 (Composition API) | Framework de interfaz |
| Vite | Build tool y dev server |
| Pinia | Estado global |
| PrimeVue | Componentes UI |
| Tailwind CSS | Estilos |
| Chart.js + vue-chartjs | Gráficos de reportes |
| KaTeX | Renderizado de matemáticas |

### Inteligencia artificial y datos

| Tecnología | Uso |
|------------|-----|
| OpenAI (o3 / o3-mini / GPT-4o-mini) | Generación de preguntas y análisis |
| Anthropic Claude (Opus / Sonnet) | Enriquecimiento visual SVG, OMR, optimización de gráficos |
| sentence-transformers | Embeddings semánticos y validación |
| ChromaDB | RAG: almacenamiento de chunks vectoriales |
| Wolfram Alpha API | Verificación matemática y científica (opcional) |

### Infraestructura

| Tecnología | Uso |
|------------|-----|
| Uvicorn | Servidor ASGI en desarrollo y producción |
| Nginx | Proxy inverso y estáticos (producción) |
| Supervisor | Gestión de procesos (producción) |
| Docker Compose | Base de datos y Redis para pruebas |

---

## Requisitos previos

Antes de comenzar necesitas:

- **Git**
- **Python 3.10 o superior**
- **Node.js 20 o superior**
- **PostgreSQL 16** con la extensión **pgvector** habilitada
- **Redis** 6 o superior
- **Wolfram Alpha** (opcional, para validación matemática) — se configura después en el asistente inicial.
- Un cliente de correo SMTP (opcional, para notificaciones por email)

> Las claves de OpenAI, Anthropic y Wolfram Alpha se configuran durante el setup inicial y se almacenan de forma segura en la base de datos. El archivo `.env` solo requiere las credenciales de infraestructura (base de datos, Redis, JWT, SMTP).

> Los documentos oficiales del ICFES (marcos de referencia, pruebas pasadas) deben obtenerse directamente desde [icfes.gov.co](https://www.icfes.gov.co) si deseas regenerar el RAG desde cero. El repositorio ya incluye los textos extraídos en `backend/static/`.

---

## Instalación y configuración

### 1. Clonar el repositorio

```bash
git clone https://github.com/Dramoscuello/simic.git
cd simic
git checkout libre
```

### 2. Crear la base de datos

Conéctate a PostgreSQL como superusuario y ejecuta:

```sql
CREATE USER SIMIC WITH PASSWORD 'tu_password_seguro';
CREATE DATABASE SIMIC_db OWNER SIMIC;
GRANT ALL PRIVILEGES ON DATABASE SIMIC_db TO SIMIC;
\c SIMIC_db
CREATE EXTENSION IF NOT EXISTS vector;
```

Verifica que la extensión esté activa:

```sql
SELECT extname FROM pg_extension WHERE extname = 'vector';
```

### 3. Configurar el backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

Copia el archivo de ejemplo y edítalo:

```bash
cp .env.example .env
```

Edita `.env` con tus credenciales. Como mínimo debes configurar:

- `DATABASE_URL`
- `SECRET_KEY`
- `REDIS_URL`
- `FRONTEND_URL`

Las claves de OpenAI/Claude son opcionales como *fallback*; lo recomendado es configurar los modelos desde el asistente inicial.

Ejecuta las migraciones:

```bash
alembic upgrade head
```

> **Nota:** la extensión `pgvector` debe estar habilitada previamente por un superusuario de PostgreSQL.

### 4. Bootstrap del RAG

SIMIC usa **ChromaDB** como base de datos vectorial para inyectar contexto oficial a los modelos de lenguaje. Los archivos fuente del conocimiento ya están en `backend/static/` (textos extraídos de los marcos del ICFES), por lo que la mayoría de usuarios solo necesita ejecutar los scripts de ingestión.

Ejecuta los tres scripts fundamentales:

```bash
python scripts/etl_unified_rag.py
python scripts/vectorize_sociales.py
python scripts/ingest_biology_vectors.py
```

| Script | Función | Colección / Uso |
|--------|---------|-----------------|
| `etl_unified_rag.py` | **Maestro**. Vectoriza patrones de preguntas de todas las áreas. | Colección `patrones_preguntas` — variabilidad en generación. |
| `vectorize_sociales.py` | Vectoriza la Constitución Política de 1991 y Estándares Básicos. | Usado por el *Juez Constitucional* (Gate 10) de Sociales. |
| `ingest_biology_vectors.py` | Vectoriza datos factuales de biología. | Usado para evitar alucinaciones (Gate 8) en Ciencias Naturales. |

Verifica que se haya creado el directorio:

```bash
ls -la data/chroma_db
```

#### ¿Regenerar el RAG desde PDFs oficiales?

Si descargas los PDFs oficiales del ICFES y quieres regenerar los textos base, usa los scripts de extracción:

| Script | PDF de entrada | Salida típica |
|--------|----------------|---------------|
| `extract_pdf_matematicas.py` | Marco de Matemáticas | `backend/static/matematicas/extracted/` |
| `extract_pdf_lectura.py` | Marco de Lectura Crítica | `backend/static/lectura_critica/extracted/` |
| `extract_pdf_ingles.py` | Marco de Inglés | `backend/static/ingles/extracted/` |
| `extract_pdf_sociales.py` | Marco de Sociales | `backend/static/sociales/extracted/` |
| `extract_pdf_text.py` | Ciencias Naturales | `backend/static/ciencias_naturales/extracted/` |

Luego vuelve a ejecutar `etl_unified_rag.py`, `vectorize_sociales.py` e `ingest_biology_vectors.py`.

#### Otros scripts de soporte

- `clean_biology_dataset.py`: limpia y estructura el dataset factual de biología antes de vectorizar.
- `curate_ocr_to_chunks.py`: divide textos escaneados en fragmentos semánticos (chunks).
- `backfill_preguntas_usadas_embeddings.py`: genera embeddings para preguntas históricas y mejora la deduplicación.

### 5. Configurar el frontend

```bash
cd ../frontend/vue-project
cp .env.example .env.local   # si existe; de lo contrario crea el archivo manualmente
npm install
```

Configura la URL del backend en `.env.local`:

```bash
cp .env.example .env.local
```

El archivo de ejemplo ya contiene:

```env
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000
```

---

## Ejecutar en local

### Backend

Desde `backend/` con el entorno virtual activado:

```bash
source .venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

La API estará disponible en:

- API: `http://localhost:8000`
- Documentación interactiva: `http://localhost:8000/docs`

### Frontend

Desde `frontend/vue-project/`:

```bash
npm run dev
```

La aplicación estará disponible en `http://localhost:5173`.

### Primer arranque: asistente de configuración

La primera vez que la base de datos está vacía, el frontend redirige automáticamente a `/setup`. Allí se solicita:

1. **Datos de la institución**: nombre, código DANE (12 dígitos), NIT, dirección, teléfono, email de contacto, datos del rector.
2. **Datos del administrador**: opción de copiar los datos del rector, o cargo, nombres, apellidos, email y contraseña.
3. **Modelos de IA**: nombre visible, código exacto del modelo (por ejemplo `gpt-4o-mini`, `o3`, `claude-sonnet-4-6`) y API key. Se requiere al menos un modelo; si hay varios, el marcado como por defecto se usa para todas las generaciones.
4. **Wolfram Alpha** (opcional): API key para validación matemática/científica.

Una vez finalizado el setup, la aplicación muestra el login con el saludo personalizado de la institución.

### Reaper (cierre automático de intentos expirados)

En producción se recomienda un cron cada 5 minutos. En desarrollo puedes ejecutarlo manualmente:

```bash
cd backend
source .venv/bin/activate
PYTHONPATH=. python -m app.tasks.close_expired_attempts
```

---

## Variables de entorno

> **Cambio importante:** las claves de API de OpenAI, Claude y Wolfram se configuran durante el setup inicial y se almacenan de forma segura en la base de datos. El `.env` conserva conexión a BD, seguridad, infraestructura y la configuración de correo.

### Obligatorias

| Variable | Descripción | Ejemplo |
|----------|-------------|---------|
| `USER_POSTGRES` | Usuario de PostgreSQL | `SIMIC` |
| `PASS_POSTGRES` | Contraseña de PostgreSQL | `tu_password` |
| `DB_POSTGRES` | Nombre de la base de datos | `SIMIC_db` |
| `HOST_POSTGRES` | Host de PostgreSQL | `localhost` |
| `PORT_POSTGRES` | Puerto de PostgreSQL | `5432` |
| `SECRET_KEY` | Clave secreta para firmar JWT | `una-clave-larga-y-aleatoria` |
| `REDIS_URL` | URL de Redis | `redis://localhost:6379/0` |
| `FRONTEND_URL` | URL del frontend (CORS) | `http://localhost:5173` |

### Opcionales

| Variable | Descripción | Por defecto |
|----------|-------------|-------------|
| `OPENAI_API_KEY` | Fallback si no hay modelo configurado en BD | — |
| `CLAUDE_API_KEY` | Fallback si no hay modelo configurado en BD | — |
| `WOLFRAM_APP_ID` | Fallback si la institución no tiene uno en BD | — |
| `MAIL_USERNAME` | Usuario/correo SMTP | — |
| `MAIL_PASSWORD` | Contraseña SMTP | — |
| `MAIL_FROM` | Correo remitente | — |
| `MAIL_PORT` | Puerto SMTP | `465` |
| `MAIL_SERVER` | Servidor SMTP | `smtp.gmail.com` |
| `SIMULACRO_MARGIN_MINUTES` | Margen de gracia para simulacros | `5` |
| `SIMULACRO_REAPER_BATCH` | Batch del reaper | `200` |
| `SIMULACRO_MIN_FINISH_PCT` | Porcentaje mínimo para finalizar | `0.30` |
| `ENABLE_PROMPT_CAPTURE` | Guardar prompts en disco (debug) | `false` |

---

## Pruebas

### Backend

```bash
cd backend
source .venv/bin/activate
pytest
```

Si deseas usar Docker para la base de datos y Redis de prueba:

```bash
cd backend
docker-compose -f docker-compose.test.yml up -d
pytest
```

### Frontend

```bash
cd frontend/vue-project
npm run test:run
```

---

## Estructura del proyecto

```
SIMIC/
├── backend/
│   ├── app/
│   │   ├── api/              # Routers de FastAPI
│   │   ├── core/             # Configuración, seguridad, WebSockets
│   │   ├── database/         # Configuración de SQLAlchemy
│   │   ├── models/           # Modelos de datos
│   │   ├── schemas/          # Esquemas Pydantic
│   │   ├── services/         # Lógica de negocio (IA, reportes, OMR)
│   │   ├── tasks/            # Tareas programadas (reaper)
│   │   └── main.py           # Punto de entrada de FastAPI
│   ├── alembic/              # Migraciones de base de datos
│   ├── data/                 # Datos y colecciones ChromaDB
│   ├── scripts/              # Scripts de ETL y utilidades
│   ├── static/               # Textos extraídos de marcos oficiales
│   └── tests/                # Pruebas automatizadas
├── frontend/
│   └── vue-project/          # Aplicación Vue 3
│       ├── src/
│       │   ├── components/   # Componentes reutilizables
│       │   ├── stores/       # Pinia stores
│       │   ├── views/        # Vistas principales
│       │   ├── router/       # Vue Router
│       │   └── api/          # Configuración de Axios
│       └── package.json
├── DEPLOY-VPS.md             # Guía de despliegue en VPS
└── opensource-readme.md      # Este archivo
```

---

## Despliegue en producción

Para desplegar SIMIC en un servidor Debian/Ubuntu con Nginx, Supervisor, PostgreSQL, Redis y SSL, consulta la guía completa:

📄 [`DEPLOY-VPS.md`](./DEPLOY-VPS.md)

El resumen del flujo de producción es:

1. Instalar PostgreSQL 16 + pgvector, Redis, Python, Node.js y Nginx.
2. Clonar el repositorio y configurar variables de entorno.
3. Instalar dependencias del backend y frontend.
4. Ejecutar migraciones y bootstrap de RAG.
5. Compilar el frontend (`npm run build`) y servirlo con Nginx.
6. Ejecutar el backend con Uvicorn bajo Supervisor.
7. Configurar SSL con Let's Encrypt.
8. Instalar el cron del reaper.

---

## Contribuir y licencia

SIMIC es un proyecto open source. Puedes:

- Reportar errores o sugerir mejoras mediante issues.
- Enviar pull requests con nuevas funcionalidades o correcciones.
- Adaptar el código para tu institución o región.

> ⚠️ **Seguridad**: nunca subas archivos `.env`, claves de API ni contraseñas al repositorio. Revisa el `.gitignore` antes de commitear.

**Licencia**: [Apache License 2.0](./LICENSE)

---

## Soporte

Si tienes dudas sobre la configuración o el uso de SIMIC, revisa primero:

- [`readme.md`](./readme.md) — visión general del proyecto.
- [`readmev2.md`](./readmev2.md) — detalles técnicos del pipeline de IA.
- [`DEPLOY-VPS.md`](./DEPLOY-VPS.md) — despliegue en producción.

---

**Hecho con ❤️ para democratizar el acceso a simulacros de calidad en Colombia.**
