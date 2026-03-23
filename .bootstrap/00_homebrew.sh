#!/bin/zsh
# set -euo pipefail  # disabled — failures are logged, not fatal

echo ""
echo "[homebrew] ── Homebrew + Brewfile ──"
echo ""

# Ensure bash is available
echo "[homebrew] Checking for /bin/bash..."
if [ ! -x "/bin/bash" ]; then
  echo "[homebrew] Bash not found. Installing Xcode Command Line Tools..."
  xcode-select --install || true
else
  echo "[homebrew] /bin/bash found."
fi

# Install Homebrew if missing
echo "[homebrew] Checking for Homebrew..."
if ! command -v brew &> /dev/null; then
  echo "[homebrew] Homebrew is not installed. Installing..."
  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
  echo "[homebrew] Loading Homebrew into current session..."
  eval "$(/opt/homebrew/bin/brew shellenv)"
else
  echo "[homebrew] Homebrew already installed at $(which brew)."
fi

echo "[homebrew] Running brew update..."
brew update

echo "[homebrew] Running brew doctor..."
brew doctor

echo "[homebrew] Running brew bundle --global (Brewfile)..."
brew bundle --global

echo "[homebrew] Running brew cleanup..."
brew cleanup

echo "[homebrew] Done."