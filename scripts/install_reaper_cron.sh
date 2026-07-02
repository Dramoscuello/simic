#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="${PROJECT_DIR:-/var/www/SIMIC}"
BACKEND_DIR="${PROJECT_DIR}/backend"

# Autodeteccion de binario python del backend
if [[ -n "${PYTHON_BIN:-}" ]]; then
  PYTHON_BIN_RESOLVED="${PYTHON_BIN}"
elif [[ -x "${BACKEND_DIR}/.venv/bin/python3" ]]; then
  PYTHON_BIN_RESOLVED="${BACKEND_DIR}/.venv/bin/python3"
elif [[ -x "${BACKEND_DIR}/venv/bin/python3" ]]; then
  PYTHON_BIN_RESOLVED="${BACKEND_DIR}/venv/bin/python3"
else
  echo "[reaper-cron] ERROR: no se encontro python del backend (.venv/bin/python3 o venv/bin/python3)." >&2
  exit 1
fi

if [[ ! -d "${BACKEND_DIR}" ]]; then
  echo "[reaper-cron] ERROR: no existe BACKEND_DIR=${BACKEND_DIR}" >&2
  exit 1
fi

LOG_DIR="/var/log/SIMIC"
LOG_FILE="${LOG_DIR}/reaper.log"

if [[ ! -d "${LOG_DIR}" ]]; then
  sudo mkdir -p "${LOG_DIR}"
fi

# Intento de ownership hacia el usuario actual, sin fallar si no aplica
sudo chown "$(id -u):$(id -g)" "${LOG_DIR}" 2>/dev/null || true
touch "${LOG_FILE}" || sudo touch "${LOG_FILE}"

CRON_LINE="*/5 * * * * cd ${BACKEND_DIR} && PYTHONPATH=${BACKEND_DIR} ${PYTHON_BIN_RESOLVED} -m app.tasks.close_expired_attempts >> ${LOG_FILE} 2>&1"

CURRENT_CRON="$(crontab -l 2>/dev/null || true)"

if echo "${CURRENT_CRON}" | grep -F "app.tasks.close_expired_attempts" >/dev/null; then
  # Reemplazo idempotente de cualquier version previa
  NEW_CRON="$(echo "${CURRENT_CRON}" | sed '/app.tasks.close_expired_attempts/d')"
  {
    printf "%s\n" "${NEW_CRON}"
    printf "%s\n" "${CRON_LINE}"
  } | sed '/^$/N;/^\n$/D' | crontab -
  echo "[reaper-cron] Entrada existente actualizada."
else
  {
    printf "%s\n" "${CURRENT_CRON}"
    printf "%s\n" "${CRON_LINE}"
  } | sed '/^$/N;/^\n$/D' | crontab -
  echo "[reaper-cron] Entrada creada."
fi

echo "[reaper-cron] Cron activo:"
crontab -l | grep -F "app.tasks.close_expired_attempts" || true

echo "[reaper-cron] OK"
