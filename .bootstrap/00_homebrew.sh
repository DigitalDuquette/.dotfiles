#!/bin/zsh
set -euo pipefail

echo "[BOOTSTRAP] Installing Homebrew + Brewfile..."

# Check if brew is installed
if ! command -v brew &> /dev/null; then
  echo "Homebrew is not installed. Installing..."
  /bin/zsh -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
  eval "$(/opt/homebrew/bin/brew shellenv)"
fi 

# Update + install from Brewfile
brew update
brew doctor
brew bundle --global


echo "[BOOTSTRAP] Schedule automatic updates..."
# Cleanup old versions
brew cleanup

# Ensure brew autoupdate is running
if ! brew autoupdate status 2>&1 | grep -q "running"; then
    echo "[BOOTSTRAP] Starting brew autoupdate..."
    brew autoupdate start --upgrade --cleanup --immediate
else
    echo "[BOOTSTRAP] brew autoupdate already running."
fi

echo "[BOOTSTRAP] Homebrew + Brewfile complete."


