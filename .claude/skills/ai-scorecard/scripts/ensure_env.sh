#!/bin/zsh
# AI Scorecard step 0: make sure the venv exists (no global pip, ever).
set -euo pipefail

VENV="$HOME/.venvs/ai-scorecard"
if [ -x "$VENV/bin/python" ]; then
    echo "venv ok: $VENV"
else
    echo "creating venv: $VENV"
    python3 -m venv "$VENV"
    "$VENV/bin/pip" install -q openpyxl python-pptx
    echo "venv ready"
fi
