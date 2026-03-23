#!/bin/zsh
# Force Homebrew Ruby for non-interactive bootstrap
export PATH="/opt/homebrew/opt/ruby/bin:/usr/local/opt/ruby/bin:$PATH"
# Ensure gem executables are resolvable in non-interactive runs
export PATH="$(ruby -r rubygems -e 'puts Gem.bindir'):$PATH"
# set -euo pipefail  # disabled — failures are logged, not fatal

echo ""
echo "[languages] ── Languages & Gems ──"
echo ""

# Ruby should already be installed via Brewfile (brew "ruby")
echo "[languages] Checking for Ruby..."
if command -v ruby >/dev/null 2>&1; then
  echo "[languages] Ruby found: $(ruby --version)"
  echo "[languages] Gem dir: $(gem environment gemdir)"

  echo "[languages] Checking for colorls gem..."
  if gem list -i colorls >/dev/null 2>&1; then
    echo "[languages] colorls already installed."
  else
    echo "[languages] Installing colorls via sudo gem install..."
    sudo gem install colorls
    echo "[languages] colorls installed."
  fi
else
  echo "[languages] WARNING: Ruby not found — ensure Brewfile includes it before running this script."
fi

echo "[languages] Done."