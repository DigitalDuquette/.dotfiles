#!/bin/zsh
# set -euo pipefail  # disabled — failures are logged, not fatal

BOOTSTRAP_DIR="$HOME/.bootstrap"
SCRIPTS=(00_homebrew.sh 10_defaults.sh 20_symlinks.sh 30_languages.sh 90_finish.sh)
TOTAL=${#SCRIPTS[@]}
FAILED=()
BOOT_START=$SECONDS

echo ""
echo "========================================"
echo "  macOS Bootstrap"
echo "  $(date '+%Y-%m-%d %H:%M:%S')"
echo "========================================"
echo ""
echo "[BOOTSTRAP] $TOTAL scripts to run:"
for s in "${SCRIPTS[@]}"; do echo "  - $s"; done
echo ""

STEP=0
for script in "${SCRIPTS[@]}"; do
  STEP=$((STEP + 1))
  SCRIPT_PATH="$BOOTSTRAP_DIR/$script"

  if [ ! -f "$SCRIPT_PATH" ]; then
    echo "[BOOTSTRAP] [$STEP/$TOTAL] SKIP $script (not found)"
    echo ""
    continue
  fi

  echo "----------------------------------------"
  echo "[BOOTSTRAP] [$STEP/$TOTAL] START $script"
  echo "           $(date '+%H:%M:%S')"
  echo "----------------------------------------"

  STEP_START=$SECONDS
  /bin/zsh "$SCRIPT_PATH"
  RC=$?
  ELAPSED=$(( SECONDS - STEP_START ))

  if [ $RC -eq 0 ]; then
    echo "[BOOTSTRAP] [$STEP/$TOTAL] DONE  $script (${ELAPSED}s)"
  else
    echo "[BOOTSTRAP] [$STEP/$TOTAL] FAIL  $script (exit $RC, ${ELAPSED}s)"
    FAILED+=("$script")
  fi
  echo ""
done

TOTAL_ELAPSED=$(( SECONDS - BOOT_START ))

echo "========================================"
echo "  Bootstrap finished in ${TOTAL_ELAPSED}s"
echo "  $(date '+%Y-%m-%d %H:%M:%S')"
if [ ${#FAILED[@]} -eq 0 ]; then
  echo "  All $TOTAL scripts succeeded."
else
  echo "  ${#FAILED[@]} script(s) FAILED:"
  for f in "${FAILED[@]}"; do echo "    - $f"; done
fi
echo "========================================"
echo ""