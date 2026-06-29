# SIMIC — Plataforma de Simulacros ICFES Saber 11

SIMIC es una plataforma **open source** para la generación, aplicación y análisis de simulacros tipo ICFES Saber 11, el examen de estado estandarizado de la educación media en Colombia. Utiliza inteligencia artificial (OpenAI, Anthropic Claude, Wolfram Alpha) para crear preguntas alineadas con los marcos oficiales del ICFES, validarlas mediante un pipeline de 10 "Quality Gates" y generar reportes pedagógicos detallados.

> **Fines pedagógicos e investigativos, sin ánimo de lucro.** Este proyecto está diseñado para que instituciones educativas, docentes e investigadores preparen a sus estudiantes de forma gratuita y autónoma. El material de referencia del ICFES incluido en `backend/static/` se utiliza bajo el principio de uso legítimo (*fair use*) para investigación educativa.

---

## ¿Qué hace SIMIC?

- **Generación IA de simulacros**: produce exámenes en las 5 áreas del Saber 11 (Matemáticas, Lectura Crítica, Ciencias Naturales, Sociales y Ciudadanas, Inglés).
- **Quality Gates**: 10 etapas de validación automática — estructura, deduplicación semántica (pgvector + SHA-256), coherencia visual, verificación matemática con Wolfram Alpha, neutralidad constitucional.
- **Aplicación de simulacros**: interfaz web con cronómetro, auto-guardado cada 30 segundos, protección anti-fraude por WebSocket y cierre automático de intentos expirados.
- **OMR (Visión IA)**: generación de hojas de respuesta físicas con QR y procesamiento de escaneos mediante Claude Vision.
- **Reportes pedagógicos**: informes individuales con análisis de IA, dashboard institucional 360°, análisis canvas con drill-down por competencias.
- **Gestión institucional**: soporte para múltiples sedes, grupos, mensajería interna 1:1.

---

## Requisitos previos

Antes de empezar necesitas tener instalado:

| Herramienta | Versión mínima | ¿Para qué? |
|-------------|---------------|------------|
| **Python** | 3.10+ | Backend (FastAPI) |
| **Node.js** | 20+ | Frontend (Vue/Vite) |
| **PostgreSQL** | 16 | Base de datos principal |
| **pgvector** | 0.7+ | Búsqueda semántica y deduplicación |
| **Redis** | 6+ | Colas de jobs, locks y caché |
| **Git** | cualquiera | Clonar el repositorio |

---

## Paso 1 — Instalar PostgreSQL, pgvector y Redis

### macOS (con Homebrew)

```bash
# Instalar PostgreSQL 16
brew install postgresql@16
brew services start postgresql@16

# Instalar pgvector
brew install pgvector

# Instalar Redis
brew install redis
brew services start redis
```

### Ubuntu / Debian

```bash
# Instalar PostgreSQL 16
sudo sh -c 'echo "deb http://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list'
wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | sudo apt-key add -
sudo apt update
sudo apt install postgresql-16 postgresql-16-pgvector redis-server -y

# Iniciar servicios
sudo systemctl start postgresql
sudo systemctl start redis-server
```

---

## Paso 2 — Crear la base de datos

Conéctese a PostgreSQL y ejecuta:

```sql
-- Crear usuario
CREATE USER simic WITH PASSWORD 'tu_password_seguro';

-- Crear base de datos
CREATE DATABASE simic_db OWNER simic;

-- Conectarse a la base de datos
\c simic_db

-- Activar pgvector (requiere superusuario)
CREATE EXTENSION IF NOT EXISTS vector;

-- Verificar
SELECT extname FROM pg_extension WHERE extname = 'vector';
```

> Si usas `psql` desde terminal: `psql -U postgres` y luego ejecuta los comandos anteriores.

---

## Paso 3 — Clonar y configurar el backend

```bash
# Clonar el repositorio
git clone https://github.com/Dramoscuello/SIMIC.git
cd SIMIC/backend

# Crear entorno virtual
python3 -m venv .venv
source .venv/bin/activate      # macOS / Linux

# Instalar dependencias
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

### Configurar el archivo `.env`

El backend ya incluye un archivo de ejemplo. Copialo y editalo con tus datos:

```bash
cp app/.env.example app/.env
```

Edita `app/.env` y configura estas variables como mínimo:

```ini
# ── Base de datos (obligatorio) ──────────────────────────
USER_POSTGRES=simic
PASS_POSTGRES=tu_password_seguro
DB_POSTGRES=simic_db
HOST_POSTGRES=localhost
PORT_POSTGRES=5432

# ── Seguridad (obligatorio) ──────────────────────────────
SECRET_KEY=una-clave-larga-y-aleatoria-de-al-menos-32-caracteres
REDIS_URL=redis://localhost:6379/0

# ── IA — API Keys (obligatorio para generar simulacros) ──
OPENAI_API_KEY=sk-proj-...
CLAUDE_API_KEY=sk-ant-...

# ── Frontend URL (obligatorio) ───────────────────────────
FRONTEND_URL=http://localhost:5173

# ── Wolfram Alpha (opcional pero recomendado) ────────────
WOLFRAM_APP_ID=...

# ── Correo SMTP (opcional) ───────────────────────────────
MAIL_USERNAME=
MAIL_PASSWORD=
MAIL_FROM=
MAIL_PORT=465
MAIL_SERVER=smtp.gmail.com
```

> **¿Dónde consigo las API keys?**
> - OpenAI: https://platform.openai.com/api-keys
> - Anthropic Claude: https://console.anthropic.com
> - Wolfram Alpha: https://developer.wolframalpha.com (opcional, para validación matemática)
>
> Sin las API keys de OpenAI y Claude, la generación de simulacros y los reportes con IA **no funcionarán**. Son el núcleo de la plataforma.

**Modelo por defecto**: si quieres forzar un modelo específico, agregá al `.env`:

```ini
DEFAULT_GENERATION_MODEL=o3
```

### Ejecutar las migraciones de base de datos

```bash
# Asegúrate de estar en backend/ con el venv activado
alembic upgrade head
```

Esto crea todas las tablas (`usuarios`, `instituciones`, `simulacros`, `grupos`, `sedes`, `conversaciones`, etc.).

---

## Paso 4 — Bootstrap del RAG (conocimiento ICFES)

SIMIC usa **ChromaDB** como base de datos vectorial para inyectar los marcos de referencia oficiales del ICFES en los modelos de lenguaje. Esto mejora drásticamente la calidad y alineación de las preguntas generadas.

Los textos extraídos de los documentos oficiales **ya están incluidos** en `backend/static/`. Solo necesitas ejecutar los scripts de ingestión para vectorizarlos.

Desde la carpeta `backend/` con el entorno virtual activado:

```bash
# 1. Script maestro — vectoriza patrones de preguntas de todas las áreas
python scripts/etl_unified_rag.py

# 2. Vectoriza la Constitución Política y estándares de Sociales
python scripts/vectorize_sociales.py

# 3. Vectoriza datos factuales de biología (evita alucinaciones)
python scripts/ingest_biology_vectors.py
```

Verifica que se haya creado el directorio de ChromaDB:

```bash
ls -la data/chroma_db
# Deberías ver varias carpetas de colecciones
```

> **¿Qué hace cada script?**
>
> | Script | Colección | Propósito |
> |--------|-----------|-----------|
> | `etl_unified_rag.py` | `patrones_preguntas` | Variabilidad y calidad en generación de preguntas |
> | `vectorize_sociales.py` | `constitucion` | Gate 10: Juez Constitucional para Sociales |
> | `ingest_biology_vectors.py` | `biology_facts` | Gate 8: Validación factual de Ciencias Naturales |

> **Si quieres regenerar el RAG desde cero** (por ejemplo, si el ICFES publica nuevos marcos), descarga los PDFs oficiales desde [icfes.gov.co](https://www.icfes.gov.co) y usa los scripts `extract_pdf_*.py` para extraer los textos. Luego vuelve a ejecutar los tres scripts de arriba.

---

## Paso 5 — Configurar el frontend

Abre una **nueva terminal**:

```bash
cd SIMIC/frontend/vue-project

# Instalar dependencias
npm install

# Crear archivo de entorno (si no existe)
echo "VITE_API_URL=http://localhost:8000" > .env.local
echo "VITE_WS_URL=ws://localhost:8000" >> .env.local
```

---

## Paso 6 — Iniciar la plataforma

Necesitás **dos terminales** (o usa tmux / screen).

### Terminal 1 — Backend

```bash
cd SIMIC/backend
source .venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

La API estará en `http://localhost:8000`. La documentación interactiva en `http://localhost:8000/docs`.

### Terminal 2 — Frontend

```bash
cd SIMIC/frontend/vue-project
npm run dev
```

La aplicación estará en `http://localhost:5173`.

---

## Paso 7 — Primer arranque: asistente de configuración

Al abrir `http://localhost:5173` por primera vez, serás redirigido automáticamente a `/setup`. El asistente te guiará en 4 pasos:

1. **Datos de la institución**: nombre, código DANE, NIT, dirección, datos del rector.
2. **Administrador**: nombre, email y contraseña del primer usuario admin.
3. **Modelos de IA**: nombre visible y código del modelo (`gpt-4o-mini`, `o3`, `claude-sonnet-4-6`). Se requiere al menos uno.
4. **Wolfram Alpha** (opcional): API key para validación matemática.

Al finalizar, la aplicación muestra la pantalla de login con el nombre de tu institución. ¡Listo!

---

## Paso 8 — Configurar el Reaper (cierre automático de intentos)

Cuando un estudiante abandona un simulacro sin finalizarlo, el **Reaper** lo cierra automáticamente al expirar el tiempo. Debe ejecutarse cada 5 minutos vía cron.

```bash
crontab -e
```

Agregá esta línea (ajusta las rutas a tu sistema):

```
*/5 * * * * cd /ruta/a/SIMIC/backend && export PYTHONPATH=/ruta/a/SIMIC/backend && /ruta/a/SIMIC/backend/.venv/bin/python /ruta/a/SIMIC/backend/app/tasks/close_expired_attempts.py >> /ruta/a/SIMIC/backend/reaper.log 2>&1
```

Para probarlo manualmente en desarrollo:

```bash
cd backend
source .venv/bin/activate
PYTHONPATH=. python -m app.tasks.close_expired_attempts
```

---

## Estructura del proyecto

```
SIMIC/
├── backend/
│   ├── app/
│   │   ├── api/          # Routers FastAPI
│   │   ├── core/         # Config, seguridad JWT, Redis, WebSockets
│   │   ├── models/       # Modelos SQLAlchemy
│   │   ├── schemas/      # Esquemas Pydantic
│   │   ├── services/     # Lógica de negocio (IA, Quality Gates, OMR, reportes)
│   │   └── tasks/        # Reaper (cierre de intentos expirados)
│   ├── alembic/          # Migraciones de base de datos
│   ├── static/           # Textos extraídos de marcos oficiales ICFES
│   ├── scripts/          # ETL, vectorización RAG, utilidades
│   ├── data/             # Colecciones ChromaDB (se crean al ejecutar los scripts)
│   └── tests/            # pytest
├── frontend/
│   └── vue-project/      # Vue 3 + Vite + Pinia + PrimeVue
├── LICENSE               # Apache License 2.0
├── AGENTS.md             # Guía para desarrolladores
└── opensource-readme.md  # Guía completa de instalación y despliegue en VPS
```

---

## Solución de problemas frecuentes

### Error: `relation "alembic_version" does not exist`

Significa que no ejecutaste las migraciones. Volvé al Paso 3 y ejecuta `alembic upgrade head`.

### Error: `ModuleNotFoundError: No module named 'alembic.config'`

El directorio `backend/alembic/` tiene un `__init__.py` que sombrea el paquete instalado. Usá el CLI directamente: `.venv/bin/alembic upgrade head`.

### Error: `pgvector` no encontrado

Asegúrate de haber ejecutado `CREATE EXTENSION IF NOT EXISTS vector;` como superusuario de PostgreSQL.

### Error: `Redis connection refused`

Verifica que Redis esté corriendo: `redis-cli ping` debería responder `PONG`. Si no, inicia el servicio: `brew services start redis` (macOS) o `sudo systemctl start redis-server` (Linux).

### Las preguntas generadas no tienen buena calidad

Asegúrate de haber ejecutado los 3 scripts del Paso 4 (bootstrap del RAG). Sin los vectores de ChromaDB, la generación de preguntas pierde contexto de los marcos oficiales.

### El frontend no carga o muestra error de CORS

Verifica que `FRONTEND_URL=http://localhost:5173` esté configurado en `app/.env` y que el backend esté corriendo en el puerto 8000.

---

## Licencia

SIMIC se distribuye bajo **Apache License 2.0**. Consulta [LICENSE](LICENSE).

Eres libre de usar, modificar y distribuir este software con fines educativos e investigativos.

---

## Contribuir

- Reporta errores o sugiere mejoras mediante issues en GitHub.
- Envía pull requests con nuevas funcionalidades o correcciones.
- Adapta el código para otras pruebas estandarizadas.

> ⚠️ **Seguridad**: nunca subir archivos `.env`, claves de API ni contraseñas al repositorio.

---

**Hecho con el ❤️ por un educador, para democratizar el acceso a simulacros de calidad en Colombia.**
