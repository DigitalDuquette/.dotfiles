#!/usr/bin/env bash
# Resolve everything a new AI idea card needs for the current year,
# fresh from the Freshservice API on every run (a cached task list goes
# stale as soon as a card is created). Self-contained: fs-project's
# lookup needs an existing task key, and this runs before one exists.
# Prints one JSON object; tasks.json in the out dir feeds the
# duplicate check.
# Usage: context.sh
set -euo pipefail
ROCK_TITLE="AI-Enabled Robotic Process Automation"
REPORTER_EMAIL="jared@padnos.com"
# Current calendar year, not the newest project: IS27 exists in Oct 2026.
PROJECT_KEY="IS$(date +%y)"
OUT_DIR="/tmp/ai-idea/$PROJECT_KEY"
BASE="https://padnos.freshservice.com/api/v2"
mkdir -p "$OUT_DIR"

# Run as op run's child so FRESH_KEY is a real env var (same pattern
# and reason as fs-project's lookup-task.sh).
if [[ -z "${FRESH_KEY:-}" ]]; then
    exec op run --env-file ~/.config/freshservice/.env -- "$0" "$@"
fi

get() {
    curl -sf -u "$FRESH_KEY:X" -H "Content-Type: application/json" "$1"
}

fetch_all() {
    # Paginated list endpoint (100/page) -> one JSON array of .<field>[]
    local url="$1" field="$2" page=1 items="[]" batch
    while true; do
        batch=$(get "${url}?per_page=100&page=${page}" | jq -c ".${field} // []")
        [[ "$batch" == "[]" ]] && break
        items=$(jq -c -n --argjson a "$items" --argjson b "$batch" '$a + $b')
        page=$((page + 1))
    done
    echo "$items"
}

PROJECT_ID=$(fetch_all "$BASE/pm/projects" projects \
    | jq -r --arg k "$PROJECT_KEY" 'map(select(.key == $k)) | .[0].id // empty')
if [[ -z "$PROJECT_ID" ]]; then
    echo "no project with key $PROJECT_KEY" >&2
    exit 1
fi

fetch_all "$BASE/pm/projects/$PROJECT_ID/tasks" tasks > "$OUT_DIR/tasks.json"
TYPES=$(fetch_all "$BASE/pm/projects/$PROJECT_ID/task-types" task_types)
STATUSES=$(fetch_all "$BASE/pm/projects/$PROJECT_ID/task-statuses" task_statuses)
REPORTER=$(get "$BASE/agents?email=$REPORTER_EMAIL" | jq '.agents[0].id')

jq -n \
    --arg key "$PROJECT_KEY" --arg dir "$OUT_DIR" --arg rock "$ROCK_TITLE" \
    --argjson pid "$PROJECT_ID" --argjson reporter "$REPORTER" \
    --argjson types "$TYPES" --argjson statuses "$STATUSES" \
    --slurpfile tasks "$OUT_DIR/tasks.json" '
    ($tasks[0] | map(select(.title == $rock)) | .[0]) as $r
    | if $r == null then error("no rock goal \"\($rock)\" in \($key); create it first") else . end
    | {
        project_key: $key,
        project_id: $pid,
        rock_key: $r.display_key,
        rock_id: $r.id,
        type_id: ($types | map(select(.name == "project")) | .[0].id),
        status_id: ($statuses | map(select(.name == "Backlog")) | .[0].id),
        reporter_id: $reporter,
        tasks_file: "\($dir)/tasks.json",
        card_url_base: "https://padnos.freshservice.com/a/project_management/ws/\($key)/tasks/"
      }'
