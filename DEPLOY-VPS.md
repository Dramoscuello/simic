---
description: Guia operativa de despliegue y actualizacion de SIMIC en VPS Debian 13
---

# DEPLOY-VPS.md

## 0) Alcance
Esta guia deja SIMIC operando en produccion sobre un VPS Debian 13 con:
- Nginx + Supervisor
- PostgreSQL 16 + pgvector
- Redis
- Backend FastAPI en `backend/.venv`
- Frontend Vue compilado en estaticos
- Bootstrap inicial de RAG (Chroma)
- Reaper cron cada 5 minutos

Tambien incluye playbook de actualizacion segura y troubleshooting.

## 1) Prerrequisitos
- VPS Debian 13 (usuario root inicial).
- Dominio apuntando al VPS (A/AAAA) para SSL.
- Repositorio: `https://github.com/Dramoscuello/SIMIC.git`.
- Branch objetivo (actual): `libre`.
- Las claves de OpenAI/Claude se configuran por institución durante el setup (fallback opcional en `.env`).

## 2) Matriz de variables de entorno

### 2.1 Obligatorias (backend)
| Variable | Uso |
|---|---|
| `USER_POSTGRES` | Usuario PostgreSQL |
| `PASS_POSTGRES` | Contraseña PostgreSQL |
| `DB_POSTGRES` | Base de datos PostgreSQL |
| `HOST_POSTGRES` | Host PostgreSQL |
| `PORT_POSTGRES` | Puerto PostgreSQL |
| `SECRET_KEY` | Firma JWT |
| `REDIS_URL` | Jobs async/locks/cache (`redis://localhost:6379/0`) |
| `FRONTEND_URL` | CORS runtime permitido (dominio frontend) |
| `MAIL_USERNAME` | Usuario/correo SMTP |
| `MAIL_PASSWORD` | Contraseña SMTP |
| `MAIL_FROM` | Correo remitente |
| `MAIL_PORT` | Puerto SMTP |
| `MAIL_SERVER` | Servidor SMTP |

### 2.2 Opcionales (fallbacks)
- `OPENAI_API_KEY`, `CLAUDE_API_KEY`, `WOLFRAM_APP_ID` (si no están en BD)
- `SIMULACRO_MARGIN_MINUTES` (default 5)
- `SIMULACRO_REAPER_BATCH` (default 200)
- `SIMULACRO_MIN_FINISH_PCT` (default 0.30)

## 3) Fase A - Preparacion base Debian 13

### 3.1 Actualizar SO
```bash
sudo apt update
sudo apt upgrade -y
```

### 3.2 Paquetes base
```bash
sudo apt install -y \
  git curl wget ca-certificates gnupg lsb-release \
  build-essential pkg-config unzip zip \
  ufw htop nano
```

### 3.3 Crear usuario de operacion
```bash
sudo adduser SIMIC
sudo usermod -aG sudo SIMIC
su - SIMIC
```

### 3.4 Firewall minimo
```bash
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow OpenSSH
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw --force enable
sudo ufw status
```

Criterio de exito:
- SSH sigue activo.
- 80/443 permitidos.

## 4) Fase B - PostgreSQL 16 + pgvector

### 4.1 Agregar repo PGDG (sin `apt-key`)
```bash
sudo install -d /usr/share/postgresql-common/pgdg
curl -fsSL https://www.postgresql.org/media/keys/ACCC4CF8.asc \
  | sudo gpg --dearmor -o /usr/share/postgresql-common/pgdg/apt.postgresql.org.gpg

echo "deb [signed-by=/usr/share/postgresql-common/pgdg/apt.postgresql.org.gpg] https://apt.postgresql.org/pub/repos/apt $(. /etc/os-release && echo $VERSION_CODENAME)-pgdg main" \
  | sudo tee /etc/apt/sources.list.d/pgdg.list >/dev/null

sudo apt update
```

### 4.2 Instalar PostgreSQL 16
```bash
sudo apt install -y postgresql-16 postgresql-client-16 postgresql-contrib-16 postgresql-server-dev-16
sudo systemctl enable postgresql
sudo systemctl start postgresql
sudo systemctl status postgresql --no-pager
```

### 4.3 Crear usuario y base de datos
```bash
sudo -u postgres psql <<'SQL'
CREATE USER SIMIC WITH PASSWORD 'CAMBIA_ESTA_PASSWORD';
CREATE DATABASE SIMIC_db OWNER SIMIC;
GRANT ALL PRIVILEGES ON DATABASE SIMIC_db TO SIMIC;
SQL
```

### 4.4 Instalar pgvector (ruta principal)
```bash
apt-cache search pgvector | grep postgresql-16 || true
```
Si aparece paquete:
```bash
sudo apt install -y postgresql-16-pgvector
```

### 4.5 pgvector fallback (si no hay paquete)
```bash
cd /tmp
git clone --branch v0.8.0 https://github.com/pgvector/pgvector.git
cd pgvector
make
sudo make install
```

### 4.6 Habilitar y validar extension
```bash
sudo -u postgres psql -d SIMIC_db -c "CREATE EXTENSION IF NOT EXISTS vector;"
sudo -u postgres psql -d SIMIC_db -c "SELECT extname FROM pg_extension WHERE extname='vector';"
```

Criterio de exito:
- `vector` aparece en `pg_extension`.

## 5) Fase C - Redis, Python, Node y dependencias nativas

### 5.1 Redis
```bash
sudo apt install -y redis-server
sudo systemctl enable redis-server
sudo systemctl start redis-server
redis-cli ping
```
Debe responder `PONG`.

### 5.2 Python
```bash
sudo apt install -y python3 python3-venv python3-pip python3-dev
python3 --version
```

### 5.3 Node.js 20 (NodeSource con keyring)
```bash
curl -fsSL https://deb.nodesource.com/gpgkey/nodesource-repo.gpg.key \
  | sudo gpg --dearmor -o /usr/share/keyrings/nodesource.gpg

echo "deb [signed-by=/usr/share/keyrings/nodesource.gpg] https://deb.nodesource.com/node_20.x nodistro main" \
  | sudo tee /etc/apt/sources.list.d/nodesource.list >/dev/null

sudo apt update
sudo apt install -y nodejs
node -v
npm -v
```

### 5.4 Nginx + Supervisor
```bash
sudo apt install -y nginx supervisor
sudo systemctl enable nginx supervisor
sudo systemctl start nginx supervisor
```

### 5.5 Dependencias de sistema para PDF/SVG/Graficos
Incluye bloque solicitado para `svglib`:
```bash
sudo apt-get install -y python3-dev libcairo2 libpango-1.0-0 \
  libpangocairo-1.0-0 libgdk-pixbuf2.0-0 libffi-dev shared-mime-info
```

Dependencias recomendadas adicionales:
```bash
sudo apt install -y \
  libjpeg-dev zlib1g-dev libfreetype6-dev \
  libxml2 libxslt1.1 \
  fonts-dejavu-core
```

OCR opcional (si usas tooling OCR local):
```bash
sudo apt install -y tesseract-ocr
```

## 6) Fase D - Clonado y setup del proyecto

### 6.1 Directorio base y clon
```bash
sudo mkdir -p /var/www/SIMIC
sudo chown -R SIMIC:SIMIC /var/www/SIMIC
cd /var/www/SIMIC

git clone https://github.com/Dramoscuello/SIMIC.git .
git checkout static
git pull origin static
```

### 6.2 Backend (venv en `backend/.venv`)
```bash
cd /var/www/SIMIC/backend
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

### 6.3 Crear `backend/.env`
```bash
cd /var/www/SIMIC/backend
nano .env
```

Ejemplo minimo (completa valores reales):
```env
# Base de datos
USER_POSTGRES=SIMIC
PASS_POSTGRES=CAMBIA_ESTA_PASSWORD
DB_POSTGRES=SIMIC_db
HOST_POSTGRES=localhost
PORT_POSTGRES=5432

# Seguridad / infra
SECRET_KEY=CAMBIA_ESTA_CLAVE_LARGA_Y_ALEATORIA
REDIS_URL=redis://localhost:6379/0
FRONTEND_URL=https://tu-dominio.com

# SMTP (configurable rápidamente desde .env)
MAIL_USERNAME=simic.alerts@gmail.com
MAIL_PASSWORD=gbtyzdyepbcpdfum
MAIL_FROM=simic.alerts@gmail.com
MAIL_PORT=465
MAIL_SERVER=smtp.gmail.com

# Simulacros
SIMULACRO_MARGIN_MINUTES=5
SIMULACRO_MIN_FINISH_PCT=0.30
```

### 6.4 Frontend build
```bash
cd /var/www/SIMIC/frontend/vue-project
npm ci
```

Crear archivo `.env.production`:
```bash
nano /var/www/SIMIC/frontend/vue-project/.env.production
```
Contenido sugerido:
```env
VITE_API_URL=https://tu-dominio.com/api
VITE_WS_URL=wss://tu-dominio.com
```

Compilar y publicar:
```bash
cd /var/www/SIMIC/frontend/vue-project
npm run build

sudo mkdir -p /var/www/SIMIC-static
sudo rsync -av --delete dist/ /var/www/SIMIC-static/
sudo chown -R www-data:www-data /var/www/SIMIC-static
```

## 7) Fase E - Migraciones y validaciones DB

### 7.1 Ejecutar migraciones
```bash
cd /var/www/SIMIC/backend
source .venv/bin/activate
alembic upgrade head
```

### 7.2 Verificar pgvector post-migracion
```bash
sudo -u postgres psql -d SIMIC_db -c "\dx"
sudo -u postgres psql -d SIMIC_db -c "SELECT extname FROM pg_extension WHERE extname='vector';"
```

### 7.3 Configuración inicial vía asistente web

Con la base de datos vacía y el backend/frontend en ejecución, abre el dominio en el navegador. El router redirige a `/setup` para:

1. Registrar la institución (DANE, NIT, dirección, rector).
2. Crear el usuario administrador.
3. Configurar al menos un modelo de IA (nombre visible, código exacto y API key).
4. Opcionalmente registrar la API key de Wolfram Alpha.

Después del setup se mostrará el login con el nombre de la institución.

### 7.4 Verificar endpoint backend local
```bash
cd /var/www/SIMIC/backend
source .venv/bin/activate
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 1
```
En otra terminal:
```bash
curl -s http://127.0.0.1:8000/
curl -I http://127.0.0.1:8000/docs
```
Luego detener con `Ctrl+C`.

## 8) Fase F - Bootstrap RAG/Chroma (obligatorio)

Las colecciones Chroma se construyen en `backend/data/chroma_db`.

```bash
cd /var/www/SIMIC/backend
source .venv/bin/activate

# Patrones multiarea
python scripts/etl_unified_rag.py

# Base constitucional/competencias (Sociales)
python scripts/vectorize_sociales.py

# Biologia factual
python scripts/ingest_biology_vectors.py
```

Validacion minima:
```bash
ls -la /var/www/SIMIC/backend/data/chroma_db
```

## 9) Fase G - Supervisor backend + Nginx (API + WS + static)

## 9.1 Supervisor (backend solamente)
Nota: Redis queda gestionado por `systemd`, no por Supervisor.

Crear logs:
```bash
sudo mkdir -p /var/log/SIMIC
sudo chown -R SIMIC:SIMIC /var/log/SIMIC
```

Crear config supervisor:
```bash
sudo tee /etc/supervisor/conf.d/SIMIC-backend.conf >/dev/null <<'EOF_SUP'
[program:SIMIC-backend]
directory=/var/www/SIMIC/backend
command=/var/www/SIMIC/backend/.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 1
user=SIMIC
autostart=true
autorestart=true
startsecs=5
stopasgroup=true
killasgroup=true
environment=PYTHONPATH="/var/www/SIMIC/backend",PATH="/var/www/SIMIC/backend/.venv/bin:/usr/bin:/bin"
stdout_logfile=/var/log/SIMIC/backend.out.log
stderr_logfile=/var/log/SIMIC/backend.err.log
EOF_SUP
```

Aplicar:
```bash
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl restart SIMIC-backend
sudo supervisorctl status
```

### 9.2 Nginx
Crear configuracion:
```bash
sudo tee /etc/nginx/sites-available/SIMIC >/dev/null <<'EOF_NGX'
server {
    listen 80;
    server_name tu-dominio.com www.tu-dominio.com;

    root /var/www/SIMIC-static;
    index index.html;

    # Frontend SPA
    location / {
        try_files $uri $uri/ /index.html;
    }

    # API (frontend usa /api)
    location /api/ {
        proxy_pass http://127.0.0.1:8000/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
        client_max_body_size 50M;
    }

    # WebSocket monitoreo (ruta real: /monitoreo/ws/...)
    location /monitoreo/ {
        proxy_pass http://127.0.0.1:8000/monitoreo/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 3600s;
        proxy_send_timeout 3600s;
    }

    access_log /var/log/nginx/SIMIC.access.log;
    error_log /var/log/nginx/SIMIC.error.log;
}
EOF_NGX
```

Activar y recargar:
```bash
sudo ln -sf /etc/nginx/sites-available/SIMIC /etc/nginx/sites-enabled/SIMIC
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl reload nginx
```

## 10) Fase H - SSL Let's Encrypt
```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d tu-dominio.com -d www.tu-dominio.com
sudo certbot renew --dry-run
```

## 11) Fase I - Reaper cron (automatica y manual)

## 11.1 Opcion automatica (recomendada)
El repo incluye el script `scripts/install_reaper_cron.sh`.

```bash
cd /var/www/SIMIC
chmod +x /var/www/SIMIC/scripts/install_reaper_cron.sh
PROJECT_DIR=/var/www/SIMIC /var/www/SIMIC/scripts/install_reaper_cron.sh
```

Verificar cron instalado:
```bash
crontab -l | grep close_expired_attempts
```

### 11.2 Opcion manual
```bash
crontab -e
```
Agregar:
```cron
*/5 * * * * cd /var/www/SIMIC/backend && PYTHONPATH=/var/www/SIMIC/backend /var/www/SIMIC/backend/.venv/bin/python3 -m app.tasks.close_expired_attempts >> /var/log/SIMIC/reaper.log 2>&1
```

### 11.3 Probar reaper manualmente
```bash
cd /var/www/SIMIC/backend
source .venv/bin/activate
PYTHONPATH=/var/www/SIMIC/backend python -m app.tasks.close_expired_attempts

tail -n 100 /var/log/SIMIC/reaper.log
```

## 12) Fase J - Smoke tests y checklist final

### 12.1 Estado de servicios
```bash
sudo systemctl status postgresql --no-pager
sudo systemctl status redis-server --no-pager
sudo systemctl status nginx --no-pager
sudo supervisorctl status
```

### 12.2 Pruebas HTTP
```bash
# Local backend directo
curl -s http://127.0.0.1:8000/

# API por Nginx
curl -I https://tu-dominio.com/api/docs

# Frontend
curl -I https://tu-dominio.com/
```

### 12.3 Validacion funcional minima
1. Login en frontend.
2. Crear/consultar recursos basicos (`usuarios`, `instituciones`).
3. Ejecutar `generate-async` y consultar estado de job.
4. Verificar WebSocket de monitoreo en flujo de simulacro.

## 13) Fase K - Playbook de actualizacion (instalar cambios)

### 13.1 Secuencia recomendada
```bash
cd /var/www/SIMIC

git fetch --all
git checkout static
git pull origin static

# Backend
cd /var/www/SIMIC/backend
source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head

# Si hubo cambios de RAG/chunks o colecciones requeridas:
python scripts/etl_unified_rag.py
python scripts/vectorize_sociales.py
python scripts/ingest_biology_vectors.py

# Frontend
cd /var/www/SIMIC/frontend/vue-project
npm ci
npm run build
sudo rsync -av --delete dist/ /var/www/SIMIC-static/

# Restart backend + reload nginx
sudo supervisorctl restart SIMIC-backend
sudo systemctl reload nginx
```

### 13.2 Validacion post-update
```bash
sudo supervisorctl status
curl -I https://tu-dominio.com/
curl -I https://tu-dominio.com/api/docs
tail -n 100 /var/log/SIMIC/backend.err.log
```

## 14) Rollback basico
Si una actualizacion falla:
```bash
cd /var/www/SIMIC
git log --oneline -n 10
# elegir commit previo estable
git checkout <commit_estable>

cd /var/www/SIMIC/backend
source .venv/bin/activate
pip install -r requirements.txt
# opcional: alembic downgrade solo si tienes plan formal de rollback de schema

cd /var/www/SIMIC/frontend/vue-project
npm ci
npm run build
sudo rsync -av --delete dist/ /var/www/SIMIC-static/

sudo supervisorctl restart SIMIC-backend
sudo systemctl reload nginx
```

## 15) Troubleshooting rapido

### 15.1 502 Bad Gateway
- Verificar backend: `sudo supervisorctl status`.
- Revisar logs: `/var/log/SIMIC/backend.err.log`.
- Probar backend directo: `curl http://127.0.0.1:8000/`.

### 15.2 Error pgvector en migraciones
- Verificar extension: `SELECT extname FROM pg_extension WHERE extname='vector';`
- Confirmar instalacion pgvector (paquete o compilado).

### 15.3 Jobs async no avanzan
- Verificar Redis: `redis-cli ping`.
- Confirmar `REDIS_URL` en `backend/.env`.

### 15.4 WebSocket no conecta
- Verificar `location /monitoreo/` en Nginx.
- Verificar `workers=1` en supervisor uvicorn.
- Revisar consola del navegador y `nginx error.log`.

### 15.5 Reaper no ejecuta
- Revisar `crontab -l`.
- Revisar permisos de `/var/log/SIMIC/reaper.log`.
- Ejecutar manual el modulo para validar path/env.

### 15.6 Frontend en blanco
- Verificar `.env.production` (`VITE_API_URL`, `VITE_WS_URL`).
- Rebuild limpio: `npm ci && npm run build`.
- Verificar que `dist` se publico en `/var/www/SIMIC-static`.

## 16) Checklist final
- [ ] PostgreSQL 16 operativo y DB creada
- [ ] Extension `vector` habilitada
- [ ] Redis operativo
- [ ] Backend en `backend/.venv` con dependencias instaladas
- [ ] Migraciones `alembic upgrade head` exitosas
- [ ] RAG bootstrap ejecutado
- [ ] Supervisor backend activo (`workers=1`)
- [ ] Nginx con `/api/` y `/monitoreo/` configurados
- [ ] SSL activo
- [ ] Reaper cron instalado y validado
- [ ] Smoke tests HTTP/funcionales aprobados

