#!/usr/bin/env bash
set -euo pipefail

echo "[BOOTSTRAP] Starting linux-remote bootstrap..."

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SETUP_DIR="$SCRIPT_DIR/setup"

for script in "$SETUP_DIR"/*.sh; do
  if [ -f "$script" ]; then
    echo "[BOOTSTRAP] Running $(basename "$script")..."
    bash "$script"
  fi
done

echo "[BOOTSTRAP] All steps complete."
