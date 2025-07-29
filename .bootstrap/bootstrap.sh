#!/bin/zsh
set -euo pipefail

echo "[BOOTSTRAP] Starting full bootstrap sequence..."

BOOTSTRAP_DIR="$HOME/.bootstrap"

for script in 00_homebrew.sh 10_defaults.sh 20_symlinks.sh 90_finish.sh; do
  SCRIPT_PATH="$BOOTSTRAP_DIR/$script"
  if [ -f "$SCRIPT_PATH" ]; then
    echo "[BOOTSTRAP] Running $script..."
    /bin/zsh "$SCRIPT_PATH"
  else
    echo "[BOOTSTRAP] Skipping $script (not found)"
  fi
done

echo "[BOOTSTRAP] All bootstrap steps complete."