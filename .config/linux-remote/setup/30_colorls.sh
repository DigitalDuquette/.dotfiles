#!/usr/bin/env bash
set -e

echo "Detecting distro..."
if command -v apt &>/dev/null; then
  echo "Debian/Ubuntu detected..."
  sudo apt update -y
  sudo apt install -y ruby ruby-dev build-essential libncurses-dev wget unzip
elif command -v dnf &>/dev/null; then
  echo "RHEL/Fedora detected..."
  MISSING=()
  for pkg in ruby ruby-devel gcc gcc-c++ make ncurses-devel wget unzip; do
    rpm -q "$pkg" &>/dev/null || MISSING+=("$pkg")
  done
  if [ ${#MISSING[@]} -gt 0 ]; then
    echo "Installing missing packages: ${MISSING[*]}"
    sudo dnf install -y "${MISSING[@]}"
  else
    echo "All system packages already installed — skipping"
  fi
else
  echo "Unsupported package manager. Install ruby, gcc, make, wget, unzip manually."
  exit 1
fi

echo "Installing Nerd Font..."
FONT_DIR="$HOME/.local/share/fonts"
mkdir -p "$FONT_DIR"
wget -q https://github.com/ryanoasis/nerd-fonts/releases/latest/download/FiraCode.zip -O /tmp/FiraCode-$USER.zip
unzip -q /tmp/FiraCode-$USER.zip -d "$FONT_DIR"
fc-cache -fv > /dev/null

echo "Installing colorls..."
if gem list colorls -i &>/dev/null; then
  echo "colorls already installed — skipping"
else
  sudo gem install colorls
fi

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
