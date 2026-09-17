#!/bin/zsh
set -euo pipefail  # Stop this step on failure; bootstrap continues with the next step.

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
  echo "[npm] ERROR: npm not found — ensure Brewfile includes node before running this script."
  exit 1
fi

echo "[npm] Done."
