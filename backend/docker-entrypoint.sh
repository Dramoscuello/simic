#!/usr/bin/env bash
set -euo pipefail

echo "[entrypoint] Iniciando servicios..."
cron

echo "[entrypoint] Esperando PostgreSQL (${HOST_POSTGRES}:${PORT_POSTGRES})..."
until PGPASSWORD="${PASS_POSTGRES}" pg_isready \
  -h "${HOST_POSTGRES}" \
  -p "${PORT_POSTGRES}" \
  -U "${USER_POSTGRES}" \
  -d "${DB_POSTGRES}" \
  -t 5 >/dev/null 2>&1; do
  echo "[entrypoint] PostgreSQL no disponible, esperando..."
  sleep 2
done
echo "[entrypoint] PostgreSQL conectado."

echo "[entrypoint] Esperando Redis (${REDIS_URL})..."
REDIS_HOST=$(echo "${REDIS_URL}" | sed -n 's|.*://\(.*\):.*|\1|p')
REDIS_PORT=$(echo "${REDIS_URL}" | sed -n 's|.*:\([0-9]*\).*|\1|p')
until redis-cli -h "${REDIS_HOST:-redis}" -p "${REDIS_PORT:-6379}" ping >/dev/null 2>&1; do
  echo "[entrypoint] Redis no disponible, esperando..."
  sleep 2
done
echo "[entrypoint] Redis conectado."

echo "[entrypoint] Ejecutando migraciones..."
cd /app
PYTHONPATH=/app alembic upgrade head

echo "[entrypoint] Iniciando uvicorn..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 1
