#!/bin/zsh
# set -euo pipefail  # disabled — failures are logged, not fatal

echo ""
echo "[npm] ── npm Global Packages ──"
echo ""

# Node should already be installed via Brewfile (brew "node")
echo "[npm] Checking for npm..."
if command -v npm >/dev/null 2>&1; then
  echo "[npm] npm found: $(npm --version)"

  GLOBALS=(tree-sitter-cli)

  for pkg in "${GLOBALS[@]}"; do
    echo "[npm] Checking for $pkg..."
    if npm list -g "$pkg" >/dev/null 2>&1; then
      echo "[npm] $pkg already installed."
    else
      echo "[npm] Installing $pkg..."
      npm install -g "$pkg"
      echo "[npm] $pkg installed."
    fi
  done
else
  echo "[npm] WARNING: npm not found — ensure Brewfile includes node before running this script."
fi

echo "[npm] Done."
