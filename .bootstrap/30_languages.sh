#!/bin/zsh
set -euo pipefail

echo "[BOOTSTRAP] Installing Ruby gems..."

# Ruby should already be installed via Brewfile (brew "ruby")
if command -v ruby >/dev/null 2>&1; then
  if gem list -i colorls >/dev/null 2>&1; then
    echo "[BOOTSTRAP] colorls already installed."
  else
    echo "[BOOTSTRAP] Installing colorls..."
    sudo gem install colorls
  fi
else
  echo "[BOOTSTRAP] Ruby not found — ensure Brewfile includes it before running this script."
fi

echo "[BOOTSTRAP] Ruby gems install complete."