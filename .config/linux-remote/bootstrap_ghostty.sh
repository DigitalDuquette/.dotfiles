#!/usr/bin/env bash
set -e

echo "Configuring Ghostty terminal support..."

LINE='export TERM=xterm-256color'

if grep -qxF "$LINE" ~/.bashrc; then
  echo "TERM already set in .bashrc — skipping"
else
  echo "$LINE" >> ~/.bashrc
  echo "Added $LINE to .bashrc"
fi

echo "Done. Run: source ~/.bashrc"
