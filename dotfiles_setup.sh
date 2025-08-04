#!/bin/zsh
set -euo pipefail

echo "[SETUP] Starting dotfiles installation..."

# Check if Xcode Command Line Tools are installed
if ! xcode-select -p &>/dev/null; then
  echo "[SETUP] Xcode Command Line Tools not installed. Installing..."
  xcode-select --install
  echo "[SETUP] Please wait for Xcode Command Line Tools installation to complete."
  echo "[SETUP] Re-run this script after installation finishes."
  exit 0
else
  echo "[SETUP] Xcode Command Line Tools already installed."
fi

# Clone the bare repository
echo "[SETUP] Cloning dotfiles repository..."
git clone --bare https://github.com/DigitalDuquette/.dotfiles.git $HOME/.dotfiles

# Create dotfiles alias function for this session
function dotfiles() {
  /usr/bin/git --git-dir=$HOME/.dotfiles/ --work-tree=$HOME $@
}

# Prevent untracked files from showing up
echo "[SETUP] Configuring repository..."
dotfiles config --local status.showUntrackedFiles no

# Checkout the tracked files
echo "[SETUP] Checking out dotfiles..."
if ! dotfiles checkout 2>/dev/null; then
  echo "[SETUP] Backing up existing files..."
  mkdir -p .dotfiles-backup
  dotfiles checkout 2>&1 | grep -E "^\s+" | awk '{print $1}' | xargs -I{} mv {} .dotfiles-backup/{} 2>/dev/null || true
  echo "[SETUP] Backed up conflicting files to ~/.dotfiles-backup/"
  dotfiles checkout
fi

echo "[SETUP] Dotfiles setup complete!"
echo ""
echo "Next steps:"
echo "1. Open a new terminal to load your shell configuration"
echo "2. Run the bootstrap sequence:"
echo "   chmod +x ~/.bootstrap/bootstrap.sh && ~/.bootstrap/bootstrap.sh"