#!/usr/bin/env bash
set -e

echo "Configuring tmux..."

if ! command -v gh &>/dev/null; then
  echo "gh CLI not found. Run bootstrap_gh.sh first."
  exit 1
fi

gh api repos/digitalduquette/.dotfiles/contents/.tmux.conf \
  --jq '.content' | base64 -d > ~/.tmux.conf

echo "Done. Wrote ~/.tmux.conf"
