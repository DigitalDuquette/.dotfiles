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


echo "[BOOTSTRAP] Brew is cleaning up..."
# Cleanup old versions
brew cleanup

echo "[BOOTSTRAP] Homebrew + Brewfile complete."
