#!/bin/zsh
set -euo pipefail

echo "[BOOTSTRAP] Installing Homebrew + Brewfile..."

# Ensure bash is available
if [ ! -x "/bin/bash" ]; then
  echo "[BOOTSTRAP] Bash not found. Installing Xcode Command Line Tools..."
  xcode-select --install || true
fi

# Install Homebrew if missing
if ! command -v brew &> /dev/null; then
  echo "[BOOTSTRAP] Homebrew is not installed. Installing..."  
  
  # Pipe directly to bin/bash
  curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh | /bin/bash
  
  # Load Homebrew into current session
  eval "$(/opt/homebrew/bin/brew shellenv)"
fi

# Update and install from Brewfile
echo "[BOOTSTRAP] Updating Homebrew..."
brew update
brew doctor
brew bundle --global

echo "[BOOTSTRAP] Cleaning up..."
brew cleanup

echo "[BOOTSTRAP] Homebrew + Brewfile complete."