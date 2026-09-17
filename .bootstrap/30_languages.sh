#!/bin/zsh
set -euo pipefail

# Use Homebrew Ruby, including for the generated gem executables.
export PATH="/opt/homebrew/opt/ruby/bin:/usr/local/opt/ruby/bin:$PATH"
if [[ ! -x /opt/homebrew/opt/ruby/bin/ruby && ! -x /usr/local/opt/ruby/bin/ruby ]]; then
  echo "[languages] ERROR: Homebrew Ruby is missing; check the Homebrew step." >&2
  exit 1
fi

echo "[languages] Ruby found: $(ruby --version)"
# Isolate installation and repair from the legacy root-owned Homebrew gems.
# This also installs dependencies locally even when a global copy already exists.
GEM_HOME=$(ruby -r rubygems -e 'puts Gem.user_dir')
export GEM_HOME
export GEM_PATH="$GEM_HOME"
export PATH="$GEM_HOME/bin:$PATH"
echo "[languages] User gem dir: $GEM_HOME"

if ! gem list --local --installed --exact colorls >/dev/null 2>&1; then
  echo "[languages] Installing colorls and dependencies without sudo..."
  gem install colorls --no-document --env-shebang
fi

if ! "$GEM_HOME/bin/colorls" --version; then
  echo "[languages] Repairing missing native extensions in user gems..."
  gem pristine --only-missing-extensions --install-dir "$GEM_HOME"
  # Also refresh the executable after Homebrew replaces the Ruby cellar path.
  gem pristine colorls --only-executables --env-shebang --install-dir "$GEM_HOME"
  if ! "$GEM_HOME/bin/colorls" --version; then
    echo "[languages] ERROR: colorls still fails after repair." >&2
    exit 1
  fi
fi

echo "[languages] Done."
