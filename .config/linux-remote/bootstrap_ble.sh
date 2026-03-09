#!/usr/bin/env bash
set -e

echo "Installing ble.sh (bash syntax highlighting)..."

if [ -f ~/.local/share/blesh/ble.sh ]; then
  echo "ble.sh already installed — skipping"
else
  cd /tmp
  wget -O - https://github.com/akinomyoga/ble.sh/releases/download/nightly/ble-nightly.tar.xz | tar xJf -
  bash ble-nightly/ble.sh --install ~/.local/share
fi

grep -qxF 'source -- ~/.local/share/blesh/ble.sh' ~/.bashrc || \
  echo 'source -- ~/.local/share/blesh/ble.sh' >> ~/.bashrc

echo "Done. Run: source ~/.bashrc"
