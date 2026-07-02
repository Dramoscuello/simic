#!/usr/bin/env bash
set -euo pipefail

echo "[entrypoint] Configurando cron para Reaper..."
cat > /etc/cron.d/icfes-reaper <<EOF_CRON
HOST_POSTGRES=${HOST_POSTGRES}
PORT_POSTGRES=${PORT_POSTGRES}
USER_POSTGRES=${USER_POSTGRES}
PASS_POSTGRES=${PASS_POSTGRES}
DB_POSTGRES=${DB_POSTGRES}
REDIS_URL=${REDIS_URL}

*/5 * * * * root cd /app && PYTHONPATH=/app /usr/local/bin/python -m app.tasks.close_expired_attempts >> /var/log/SIMIC/reaper.log 2>&1

EOF_CRON
chmod 0644 /etc/cron.d/icfes-reaper
cron
echo "[entrypoint] Cron configurado."

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

echo "[entrypoint] Verificando extension pgvector..."
python -c "
import psycopg2, os
conn = psycopg2.connect(
    host=os.environ['HOST_POSTGRES'],
    port=os.environ['PORT_POSTGRES'],
    user=os.environ['USER_POSTGRES'],
    password=os.environ['PASS_POSTGRES'],
    dbname=os.environ['DB_POSTGRES'],
)
conn.autocommit = True
conn.cursor().execute('CREATE EXTENSION IF NOT EXISTS vector;')
conn.close()
print('vector extension ready.')
"

alembic upgrade head

echo "[entrypoint] Iniciando uvicorn..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 1
