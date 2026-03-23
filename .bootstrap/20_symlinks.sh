#!/bin/zsh
set -euo pipefail

echo "[BOOTSTRAP] Linking dotfiles..."

# Obsidian vault (iCloud)
OBSIDIAN_TARGET="$HOME/Library/Mobile Documents/iCloud~md~obsidian/Documents"
OBSIDIAN_LINK="$HOME/obsidian-vault"

if [ -L "$OBSIDIAN_LINK" ]; then
  echo "[BOOTSTRAP] $OBSIDIAN_LINK already linked."
elif [ -e "$OBSIDIAN_LINK" ]; then
  echo "[BOOTSTRAP] WARNING: $OBSIDIAN_LINK exists but is not a symlink. Skipping."
else
  ln -s "$OBSIDIAN_TARGET" "$OBSIDIAN_LINK"
  echo "[BOOTSTRAP] Linked $OBSIDIAN_LINK → $OBSIDIAN_TARGET"
fi

echo "[BOOTSTRAP] Symlinks created."