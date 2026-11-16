#!/usr/bin/env bash
# Freshservice project tasks created or updated on one local day,
# with full description for tasks assigned to or reported by Jared.
# The API does not say who made an update; "other" rows may still be
# Jared's edits. Usage: fs-tasks-day.sh YYYY-MM-DD
set -euo pipefail
if [[ -z "${FRESH_KEY:-}" ]]; then
  exec op run --env-file ~/.config/freshservice/.env -- "$0" "$@"
fi
read -r START END < <("$(dirname "$0")/day-bounds.sh" "$1")
BASE="https://padnos.freshservice.com/api/v2"
get() { curl -sf -u "$FRESH_KEY:X" -H "Content-Type: application/json" "$1"; }
ME=$(get "$BASE/agents?email=jared@padnos.com" | jq -r '.agents[0].id')
STATUS=$(get "$BASE/pm/projects?per_page=100" | jq -c '.projects | map({id,key})')
for p in $(echo "$STATUS" | jq -r '.[] | "\(.id):\(.key)"'); do
  id=${p%%:*}; key=${p#*:}; page=1
  statuses=$(get "$BASE/pm/projects/$id/task-statuses" 2>/dev/null \
    | jq -c '[(.task_statuses // .statuses // [])[] | {key: (.id|tostring), value: .name}] | from_entries' || echo '{}')
  while :; do
    b=$(get "$BASE/pm/projects/$id/tasks?per_page=100&page=$page" | jq -c '.tasks // []')
    [[ "$b" == "[]" ]] && break
    echo "$b" | jq -r --arg s "$START" --arg e "$END" --arg k "$key" \
      --argjson me "$ME" --argjson st "$statuses" '.[]
      | select((.updated_at >= $s and .updated_at < $e) or (.created_at >= $s and .created_at < $e))
      | (if .assignee_id == $me or .reporter_id == $me then "mine" else "other" end) as $who
      | "### \(.display_key // "\($k)-\(.id)") [\($st[.status_id|tostring] // .status_id)] (\($who); created \(.created_at[0:10]); updated \(.updated_at))\n\(.title)"
        + (if $who == "mine" then "\n" + ((.description // "") | gsub("<[^>]+>"; "") | gsub("&gt;"; ">") | gsub("&lt;"; "<") | gsub("&amp;"; "&") | gsub("&nbsp;"; " ") | .[0:1200]) else "" end)'
    page=$((page+1))
  done
done
