#!/usr/bin/env bash
# Print the UTC start and end (ISO) of a local America/Detroit day.
# Usage: day-bounds.sh YYYY-MM-DD
set -euo pipefail
s=$(TZ=America/Detroit date -j -f "%Y-%m-%d %H:%M:%S" "$1 00:00:00" +%s)
e=$(TZ=America/Detroit date -j -v+1d -f "%Y-%m-%d %H:%M:%S" "$1 00:00:00" +%s)
echo "$(date -u -r "$s" +%FT%TZ) $(date -u -r "$e" +%FT%TZ)"
