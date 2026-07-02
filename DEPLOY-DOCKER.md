---
description: Guia operativa de despliegue y actualizacion de SIMIC con Docker
---

# DEPLOY-DOCKER.md

## 0) Alcance

Esta guia deja SIMIC operando en produccion usando Docker Compose con:

- PostgreSQL 16 + pgvector (contenedor `pgvector/pgvector:pg16`)
- Redis 7 (contenedor `redis:7-alpine`)
- Backend FastAPI (contenedor propio, `python:3.12-slim` + uvicorn + cron para Reaper)
- Frontend Vue compilado servido por Nginx (contenedor propio, multi-stage build)
- Bootstrap inicial de RAG (Chroma) manual post-deploy
- Reaper automatico via cron dentro del contenedor backend

Tambien incluye playbook de actualizacion, backup/restore y troubleshooting.

**Diferencias con DEPLOY-VPS.md:** esta guia usa Docker en lugar de instalacion bare-metal.
No requiere Nginx ni Supervisor en el host. SSL queda fuera del compose y debe manejarse
con un reverse proxy externo (nginx+certbot, Traefik, Caddy) si se necesita HTTPS.

## 1) Prerrequisitos

- Servidor con **Docker Engine 24+** y **Docker Compose v2+**.
- Git.
- Repositorio: `https://github.com/Dramoscuello/simic.git`.
- Branch objetivo: `main`.

Instalacion rapida de Docker en Debian/Ubuntu:

```bash
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker $USER
newgrp docker
docker compose version
```

## 2) Arquitectura de contenedores

```
┌──────────────────────────────────────────────────────┐
│  docker-compose.yml                                   │
│                                                       │
│  ┌──────────────┐  ┌──────────────┐                   │
│  │  postgres    │  │    redis     │                   │
│  │  pgvector:pg16│  │  redis:7    │                   │
│  │  :5432       │  │  :6379       │                   │
│  └──────┬───────┘  └──────┬───────┘                   │
│         │                 │                           │
│  ┌──────┴─────────────────┴───────┐                   │
│  │          backend                │                   │
│  │  python:3.12-slim + uvicorn    │                   │
│  │  :8000 (interno)               │                   │
│  │  + cron (Reaper cada 5 min)    │                   │
│  └──────────────┬─────────────────┘                   │
│                 │                                     │
│  ┌──────────────┴─────────────────┐                   │
│  │         frontend               │                   │
│  │  nginx:alpine                  │                   │
│  │  :80 → SPA static + proxy API │                   │
│  │  /api/ → backend:8000         │                   │
│  │  /monitoreo/ → backend:8000   │                   │
│  └────────────────────────────────┘                   │
│                                                       │
│  Volumes: postgres_data, redis_data, chroma_db        │
└──────────────────────────────────────────────────────┘
```

## 3) Matriz de variables de entorno

Todas las variables se cargan desde un archivo `.env` en la raiz del proyecto.
Las variables de infraestructura interna (`HOST_POSTGRES`, `REDIS_URL`) estan
prefijadas en `docker-compose.yml` y no necesitan cambiarse.

### 3.1 Obligatorias

| Variable | Descripcion | Default Docker |
|---|---|---|
| `USER_POSTGRES` | Usuario PostgreSQL | `simic` |
| `PASS_POSTGRES` | Contrasena PostgreSQL | (requiere cambio) |
| `DB_POSTGRES` | Nombre de la BD | `simic_db` |
| `SECRET_KEY` | Firma JWT | (requiere cambio) |
| `FRONTEND_URL` | Dominio para CORS | `http://localhost` |
| `MAIL_USERNAME` | Usuario SMTP | — |
| `MAIL_PASSWORD` | Contrasena SMTP | — |
| `MAIL_FROM` | Remitente correos | — |
| `MAIL_PORT` | Puerto SMTP | `465` |
| `MAIL_SERVER` | Servidor SMTP | `smtp.gmail.com` |

### 3.2 Opcionales

| Variable | Descripcion | Default |
|---|---|---|
| `OPENAI_API_KEY` | API key OpenAI (fallback) | — |
| `CLAUDE_API_KEY` | API key Anthropic (fallback) | — |
| `OPENAI_BASE_URL` | Endpoint API compatible | — |
| `DEFAULT_GENERATION_MODEL` | Modelo por defecto | `o3` |
| `WOLFRAM_APP_ID` | Wolfram Alpha App ID | — |
| `SIMULACRO_MARGIN_MINUTES` | Margen de cierre | `5` |
| `SIMULACRO_MIN_FINISH_PCT` | % minimo para cerrar | `0.30` |
| `FRONTEND_PORT` | Puerto externo frontend | `80` |
| `VITE_API_URL` | Build arg frontend | `/api` |

### 3.3 Variables fijas en docker-compose (NO modificar)

| Variable | Valor |
|---|---|
| `HOST_POSTGRES` | `postgres` (nombre del servicio) |
| `PORT_POSTGRES` | `5432` |
| `REDIS_URL` | `redis://redis:6379/0` |

## 4) Fase A - Clonar y configurar entorno

### 4.1 Clonar repositorio

```bash
git clone https://github.com/Dramoscuello/simic.git
cd simic
git checkout main
```

### 4.2 Crear archivo .env

```bash
cp .env.docker.example .env
nano .env
```

Completa **como minimo**:

```ini
USER_POSTGRES=simic
PASS_POSTGRES=password_segura_postgres
DB_POSTGRES=simic_db
SECRET_KEY=clave_larga_y_aleatoria_para_jwt
FRONTEND_URL=http://tu-dominio.com
```

Las claves de IA (OpenAI, Claude, Wolfram) pueden configurarse despues desde
el asistente web `/setup`. Las variables en `.env` son un fallback opcional.

### 4.3 Construir e iniciar servicios

```bash
docker compose build --no-cache
docker compose up -d
```

Verificar que todos los contenedores esten corriendo:

```bash
docker compose ps
```

Deben aparecer 4 servicios con estado `Up`:
- `simic_postgres`
- `simic_redis`
- `simic_backend`
- `simic_frontend`

### 4.4 Verificar logs del backend

```bash
docker compose logs backend -f --tail=50
```

Debe mostrarse:
```
[entrypoint] PostgreSQL conectado.
[entrypoint] Redis conectado.
[entrypoint] Ejecutando migraciones...
[entrypoint] Iniciando uvicorn...
```

## 5) Fase B - Bootstrap RAG/Chroma (obligatorio)

Las colecciones Chroma se construyen dentro del contenedor backend en
`/app/data/chroma_db` (mapeado al volumen `chroma_db`).

```bash
docker compose exec backend python scripts/etl_unified_rag.py
docker compose exec backend python scripts/vectorize_sociales.py
docker compose exec backend python scripts/ingest_biology_vectors.py
```

Validacion:

```bash
docker compose exec backend ls -la /app/data/chroma_db
```

## 6) Fase C - Configuracion inicial via asistente web

Abre `http://<ip-del-servidor>` (o el dominio configurado) en el navegador.
El router redirige a `/setup` para:

1. Registrar la institucion (DANE, NIT, direccion, rector).
2. Crear el usuario administrador.
3. Configurar al menos un modelo de IA (nombre visible, codigo exacto y API key).
4. Opcionalmente registrar la API key de Wolfram Alpha.

Despues del setup se mostrara el login con el nombre de la institucion.

## 7) Fase D - Verificacion de servicios

### 7.1 Estado de contenedores

```bash
docker compose ps
docker compose stats --no-stream
```

### 7.2 Probar endpoints

```bash
# Backend directo (interno)
docker compose exec backend curl -s http://localhost:8000/

# Frontend (ya expuesto en puerto 80 o FRONTEND_PORT)
curl -I http://localhost/
curl -s http://localhost/api/docs | head -20
```

### 7.3 Verificar Reaper

El Reaper corre automaticamente via cron dentro del contenedor backend cada 5 minutos.

Verificar que cron esta activo:

```bash
docker compose exec backend pgrep cron
```

Verificar log del Reaper:

```bash
docker compose exec backend cat /var/log/SIMIC/reaper.log
```

Para ejecutar el Reaper manualmente:

```bash
docker compose exec backend python -m app.tasks.close_expired_attempts
```

### 7.4 Validacion funcional minima

1. Login en frontend.
2. Crear/consultar recursos basicos (`usuarios`, `instituciones`).
3. Ejecutar generacion de simulacro y consultar estado.
4. Verificar WebSocket de monitoreo en flujo de simulacro.

## 8) Playbook de actualizacion

### 8.1 Secuencia recomendada

```bash
cd /ruta/a/simic

# Detener servicios
docker compose down

# Actualizar codigo
git fetch --all
git checkout main
git pull origin main

# Reconstruir imagenes (sin cache para asegurar dependencias frescas)
docker compose build --no-cache

# Iniciar (las migraciones se ejecutan en el entrypoint)
docker compose up -d

# Verificar logs
docker compose logs backend -f --tail=50

# Si hubo cambios en RAG:
docker compose exec backend python scripts/etl_unified_rag.py
docker compose exec backend python scripts/vectorize_sociales.py
docker compose exec backend python scripts/ingest_biology_vectors.py
```

### 8.2 Validacion post-update

```bash
docker compose ps
curl -I http://localhost/
docker compose exec backend curl -s http://localhost:8000/api/docs | head -5
docker compose logs backend --tail=30
```

## 9) Backup y restore de base de datos

### 9.1 Crear backup

```bash
docker compose exec postgres pg_dump \
  -U simic \
  -d simic_db \
  --format=custom \
  --file=/tmp/simic_backup_$(date +%Y%m%d_%H%M%S).dump

docker compose cp \
  postgres:/tmp/simic_backup_*.dump \
  ./backups/
```

### 9.2 Restaurar backup

```bash
docker compose cp ./backups/simic_backup_20250101_120000.dump \
  postgres:/tmp/restore.dump

docker compose exec postgres pg_restore \
  -U simic \
  -d simic_db \
  --clean \
  --if-exists \
  /tmp/restore.dump
```

### 9.3 Backup del volumen ChromaDB

```bash
docker compose exec backend tar czf /tmp/chroma_backup.tar.gz \
  -C /app/data chroma_db

docker compose cp \
  backend:/tmp/chroma_backup.tar.gz \
  ./backups/
```

## 10) Rollback

Si una actualizacion falla:

```bash
cd /ruta/a/simic
git log --oneline -n 10
git checkout <commit_estable>

docker compose down
docker compose build --no-cache
docker compose up -d

docker compose logs backend -f --tail=50
```

## 11) Troubleshooting

### 11.1 El backend no arranca

Ver logs detallados:

```bash
docker compose logs backend
```

Causas comunes:
- PostgreSQL no acepta conexion → verificar `PASS_POSTGRES` en `.env`.
- Error en migraciones → revisar que pgvector este instalado en el schema `vector`.
- Redis no disponible → verificar `simic_redis` este `Up`.

### 11.2 Error pgvector en migraciones

```bash
# Verificar extension en PostgreSQL
docker compose exec postgres psql -U simic -d simic_db \
  -c "SELECT extname FROM pg_extension WHERE extname='vector';"

# Si no existe, crearla manualmente
docker compose exec postgres psql -U simic -d simic_db \
  -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

### 11.3 Jobs async no avanzan

```bash
# Verificar Redis
docker compose exec redis redis-cli ping
# Debe responder PONG

# Verificar REDIS_URL en backend
docker compose exec backend env | grep REDIS_URL
# Debe ser redis://redis:6379/0
```

### 11.4 WebSocket no conecta

- Verificar que `workers=1` en el entrypoint (uvicorn).
- Verificar que nginx.conf tiene headers `Upgrade` y `Connection` en `/api/` y `/monitoreo/`.
- Si usas un reverse proxy externo, asegurar que soporte WebSocket.

### 11.5 Frontend en blanco (pantalla blanca despues de build)

- Verificar que `VITE_API_URL` se paso como build arg (default `/api`).
- Revisar consola del navegador (F12) para errores CORS o 404.
- Reconstruir sin cache: `docker compose build --no-cache frontend`.

### 11.6 Reaper no ejecuta

```bash
# Verificar cron activo en backend
docker compose exec backend pgrep cron

# Ejecutar manual para diagnosticar
docker compose exec backend python -m app.tasks.close_expired_attempts

# Revisar log
docker compose exec backend cat /var/log/SIMIC/reaper.log
```

### 11.7 Puerto 80 ocupado

Si el puerto 80 ya esta en uso, cambia `FRONTEND_PORT` en `.env`:

```ini
FRONTEND_PORT=8080
```

Luego: `docker compose up -d`

### 11.8 Error CORS al acceder desde otro dominio

Actualiza `FRONTEND_URL` en `.env` al dominio real desde donde se accede:

```ini
FRONTEND_URL=https://simic.mi-dominio.com
```

Luego: `docker compose up -d backend`

## 12) Comandos utiles

```bash
# Ver todos los logs
docker compose logs -f

# Logs de un servicio especifico
docker compose logs backend -f --tail=100

# Reiniciar un servicio
docker compose restart backend

# Entrar a shell del backend
docker compose exec backend bash

# Entrar a psql
docker compose exec postgres psql -U simic -d simic_db

# Detener todo
docker compose down

# Detener y eliminar volumenes (RESET TOTAL)
docker compose down -v

# Reconstruir solo backend
docker compose build --no-cache backend
docker compose up -d backend
```

## 13) SSL / HTTPS (externo al compose)

El docker-compose expone solo HTTP. Para habilitar HTTPS se recomienda
un reverse proxy en el host. Ejemplo con Nginx + Certbot:

```bash
sudo apt install -y nginx certbot python3-certbot-nginx

sudo tee /etc/nginx/sites-available/simic-ssl >/dev/null <<'EOF'
server {
    listen 80;
    server_name tu-dominio.com;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl;
    server_name tu-dominio.com;

    ssl_certificate     /etc/letsencrypt/live/tu-dominio.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/tu-dominio.com/privkey.pem;

    location / {
        proxy_pass http://127.0.0.1:80;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto https;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_read_timeout 3600s;
        proxy_send_timeout 3600s;
        client_max_body_size 50M;
    }
}
EOF

sudo ln -sf /etc/nginx/sites-available/simic-ssl /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
sudo certbot --nginx -d tu-dominio.com
```

Alternativas: [Traefik](https://traefik.io) o [Caddy](https://caddyserver.com) como reverse proxy con SSL automatico.

## 14) Checklist final

- [ ] `.env` creado con todas las variables obligatorias
- [ ] `docker compose up -d` exitoso, 4 contenedores `Up`
- [ ] Logs de backend muestran migraciones exitosas y uvicorn iniciado
- [ ] Extension `vector` habilitada en PostgreSQL
- [ ] Redis responde `PONG` (`docker compose exec redis redis-cli ping`)
- [ ] RAG bootstrap ejecutado (3 scripts)
- [ ] Frontend accesible en `http://<ip>` y `/api/docs` responde
- [ ] Asistente `/setup` completado (institucion, admin, modelo IA)
- [ ] Login funcional
- [ ] Reaper cron activo (`docker compose exec backend pgrep cron`)
- [ ] WebSocket monitoreo funcional en flujo de simulacro
- [ ] Backup de BD automatizado (cron en host o script externo)
