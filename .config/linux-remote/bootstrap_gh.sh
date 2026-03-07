#!/usr/bin/env bash
set -e

echo "Installing GitHub CLI..."

if command -v dnf &>/dev/null; then
  sudo dnf install -y dnf5-plugins
  sudo dnf config-manager addrepo --from-repofile=https://cli.github.com/packages/rpm/gh-cli.repo
  sudo dnf install -y gh --repo gh-cli
elif command -v apt &>/dev/null; then
  sudo mkdir -p /etc/apt/keyrings
  curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg \
    | sudo tee /etc/apt/keyrings/githubcli-archive-keyring.gpg > /dev/null
  echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" \
    | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null
  sudo apt update
  sudo apt install -y gh
else
  echo "Unsupported package manager. See https://cli.github.com for manual install."
  exit 1
fi

echo "Done. Run: gh auth login"
