#!/bin/zsh
set -euo pipefail

echo "[BOOTSTRAP] Final cleanup..."

brew cleanup

echo "[BOOTSTRAP] All set. Open a new terminal to apply changes."
