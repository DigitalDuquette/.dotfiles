#!/bin/zsh
set -euo pipefail  # Stop this step on failure; bootstrap continues with the next step.

echo ""
echo "[finish] ── Final Cleanup ──"
echo ""

echo "[finish] Running brew cleanup..."
brew cleanup

echo "[finish] Fixing zsh compinit permissions on Homebrew dirs..."
chmod go-w /opt/homebrew/share
chmod -R go-w /opt/homebrew/share/zsh

echo "[finish] Done. Open a new terminal to apply changes."
