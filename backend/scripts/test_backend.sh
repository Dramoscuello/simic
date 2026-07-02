#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COMPOSE_FILE="$ROOT_DIR/docker-compose.test.yml"

if command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then
  COMPOSE_CMD=(docker compose -f "$COMPOSE_FILE")
elif command -v docker-compose >/dev/null 2>&1; then
  COMPOSE_CMD=(docker-compose -f "$COMPOSE_FILE")
else
  echo "No se encontró 'docker compose' ni 'docker-compose'." >&2
  exit 1
fi

export DATABASE_URL="${DATABASE_URL:-postgresql://postgres:postgres@localhost:54329/icfes_test}"
export REDIS_URL="${REDIS_URL:-redis://localhost:6389/0}"
export APP_BOOTSTRAP_ON_STARTUP="${APP_BOOTSTRAP_ON_STARTUP:-false}"
export SECRET_KEY="${SECRET_KEY:-test_secret_key}"

cleanup() {
  "${COMPOSE_CMD[@]}" down -v
}
trap cleanup EXIT

"${COMPOSE_CMD[@]}" up -d

echo "Esperando PostgreSQL..."
until "${COMPOSE_CMD[@]}" exec -T postgres_test pg_isready -U postgres -d icfes_test >/dev/null 2>&1; do
  sleep 1
done

echo "Ejecutando migraciones + tests..."
(cd "$ROOT_DIR" && alembic upgrade head)
(cd "$ROOT_DIR" && pytest -m "critical or integration")
