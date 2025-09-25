#!/bin/zsh
# Force Homebrew Ruby for non-interactive bootstrap
export PATH="/opt/homebrew/opt/ruby/bin:/usr/local/opt/ruby/bin:$PATH"
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

# npm global CLI installs
if command -v npm >/dev/null 2>&1; then
  echo "[BOOTSTRAP] Installing Claude Code CLI..."
  npm install -g @anthropic-ai/claude-code
else
  echo "[BOOTSTRAP] npm not found — ensure Node is installed via Brewfile."
fi

echo "[BOOTSTRAP] Ruby gems install complete."