#!/usr/bin/env bash
set -euo pipefail

echo "[entrypoint] Iniciando servicios..."
cron

echo "[entrypoint] Esperando PostgreSQL (${HOST_POSTGRES}:${PORT_POSTGRES})..."
if python -c "
import psycopg2, os, time
for i in range(60):
    try:
        conn = psycopg2.connect(
            host=os.environ['HOST_POSTGRES'],
            port=os.environ['PORT_POSTGRES'],
            user=os.environ['USER_POSTGRES'],
            password=os.environ['PASS_POSTGRES'],
            dbname=os.environ['DB_POSTGRES'],
            connect_timeout=3,
        )
        conn.close()
        exit(0)
    except Exception:
        time.sleep(2)
exit(1)
" 2>/dev/null; then
  echo "[entrypoint] PostgreSQL conectado."
else
  echo "[entrypoint] PostgreSQL no disponible tras 2 min, abortando."
  exit 1
fi

echo "[entrypoint] Esperando Redis (${REDIS_URL})..."
if python -c "
import redis, os, time
for i in range(30):
    try:
        r = redis.from_url(os.environ['REDIS_URL'])
        r.ping()
        r.close()
        exit(0)
    except Exception:
        time.sleep(2)
exit(1)
" 2>/dev/null; then
  echo "[entrypoint] Redis conectado."
else
  echo "[entrypoint] Redis no disponible tras 1 min, abortando."
  exit 1
fi

echo "[entrypoint] Ejecutando migraciones..."
cd /app
PYTHONPATH=/app alembic upgrade head

echo "[entrypoint] Iniciando uvicorn..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 1
