#!/usr/bin/env bash
set -e

echo "Updating packages..."
sudo apt update -y

echo "Installing dependencies..."
sudo apt install -y ruby ruby-dev build-essential libncurses-dev wget unzip

echo "Installing Nerd Font..."
FONT_DIR="$HOME/.local/share/fonts"
mkdir -p "$FONT_DIR"
wget -q https://github.com/ryanoasis/nerd-fonts/releases/latest/download/FiraCode.zip -O /tmp/FiraCode.zip
unzip -q /tmp/FiraCode.zip -d "$FONT_DIR"
fc-cache -fv > /dev/null

echo "Installing colorls..."
sudo gem install colorls

echo "Adding alias to shell config..."
if [ -n "$ZSH_VERSION" ]; then
  SHELL_RC="$HOME/.zshrc"
elif [ -n "$BASH_VERSION" ]; then
  SHELL_RC="$HOME/.bashrc"
else
  SHELL_RC="$HOME/.profile"
fi

grep -qxF 'alias ls="colorls --group-directories-first"' "$SHELL_RC" || \
  echo 'alias ls="colorls --group-directories-first"' >> "$SHELL_RC"

echo "Bootstrap complete. Reload shell or run: source $SHELL_RC"