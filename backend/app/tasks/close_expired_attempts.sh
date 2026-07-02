#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="/Users/dramoscuello/icfes_project"
BACKEND_DIR="${ROOT_DIR}/backend"

cd "${BACKEND_DIR}"

echo "[reaper] starting close_expired_attempts at $(date -u +"%Y-%m-%dT%H:%M:%SZ")"

if python3 -m app.tasks.close_expired_attempts; then
  echo "[reaper] success"
else
  code=$?
  echo "[reaper] error (exit code: ${code})" >&2
  exit "${code}"
fi
