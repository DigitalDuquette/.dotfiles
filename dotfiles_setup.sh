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

# Check if dotfiles repo already exists
if [ -d "$HOME/.dotfiles" ]; then
  echo "[SETUP] Updating existing dotfiles repo (force overwrite)..."

  # Ensure we're in sync with remote
  /usr/bin/git --git-dir=$HOME/.dotfiles/ --work-tree=$HOME fetch origin main

  # Create main branch if it doesn't exist locally
  /usr/bin/git --git-dir=$HOME/.dotfiles/ --work-tree=$HOME checkout -B main origin/main

  # Force reset to match remote (overwrites everything)
  /usr/bin/git --git-dir=$HOME/.dotfiles/ --work-tree=$HOME reset --hard origin/main

else
  echo "[SETUP] Cloning dotfiles repository..."
  git clone --bare https://github.com/DigitalDuquette/.dotfiles.git $HOME/.dotfiles
  /usr/bin/git --git-dir=$HOME/.dotfiles/ --work-tree=$HOME config --local status.showUntrackedFiles no
  /usr/bin/git --git-dir=$HOME/.dotfiles/ --work-tree=$HOME checkout -f
fi

# Create dotfiles alias function
function dotfiles() {
  /usr/bin/git --git-dir=$HOME/.dotfiles/ --work-tree=$HOME $@
}

# Configure dotfiles repo
echo "[SETUP] Configuring dotfiles repository..."
dotfiles config --local status.showUntrackedFiles no

# Backup existing files if they conflict
echo "[SETUP] Checking for conflicting files..."
if ! dotfiles checkout 2>/dev/null; then
  echo "[SETUP] Backing up existing dotfiles..."
  mkdir -p .dotfiles-backup
  dotfiles checkout 2>&1 | grep -E "^\s+" | awk '{print $1}' | xargs -I{} mv {} .dotfiles-backup/{} 2>/dev/null || true
  echo "[SETUP] Backed up conflicting files to ~/.dotfiles-backup/"
  dotfiles checkout
fi

echo "[SETUP] Dotfiles checked out successfully!"

# Run bootstrap if it exists (source to avoid nested shells)
if [ -f "$HOME/.bootstrap/bootstrap.sh" ]; then
  echo "[SETUP] Running bootstrap sequence in current shell..."
  chmod +x "$HOME/.bootstrap/bootstrap.sh"
  source "$HOME/.bootstrap/bootstrap.sh"
else
  echo "[SETUP] No bootstrap script found. Setup complete."
fi

echo "[SETUP] Installation complete! Open a new terminal to apply all changes."