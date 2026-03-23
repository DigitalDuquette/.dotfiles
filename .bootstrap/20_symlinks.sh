#!/bin/zsh
# set -euo pipefail  # disabled — failures are logged, not fatal

echo ""
echo "[symlinks] ── Symlinks ──"
echo ""

# Obsidian vault (iCloud)
OBSIDIAN_TARGET="$HOME/Library/Mobile Documents/iCloud~md~obsidian/Documents"
OBSIDIAN_LINK="$HOME/obsidian-vault"

echo "[symlinks] Checking Obsidian vault link..."
echo "[symlinks]   target: $OBSIDIAN_TARGET"
echo "[symlinks]   link:   $OBSIDIAN_LINK"

if [ -L "$OBSIDIAN_LINK" ]; then
  echo "[symlinks] Already linked. Nothing to do."
elif [ -e "$OBSIDIAN_LINK" ]; then
  echo "[symlinks] WARNING: $OBSIDIAN_LINK exists but is not a symlink. Skipping."
else
  ln -s "$OBSIDIAN_TARGET" "$OBSIDIAN_LINK"
  echo "[symlinks] Created link."
fi

echo "[symlinks] Done."