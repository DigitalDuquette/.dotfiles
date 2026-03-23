#!/bin/zsh
# set -euo pipefail  # disabled — failures are logged, not fatal

echo ""
echo "[finish] ── Final Cleanup ──"
echo ""

echo "[finish] Running brew cleanup..."
brew cleanup

echo "[finish] Done. Open a new terminal to apply changes."
