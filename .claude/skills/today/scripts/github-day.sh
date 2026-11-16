#!/usr/bin/env bash
# GitHub activity for one local day: PR/issue/review events, then
# commit subjects for every repo pushed to. Times are local (ET).
# Usage: github-day.sh YYYY-MM-DD
set -euo pipefail
read -r START END < <("$(dirname "$0")/day-bounds.sh" "$1")
LOGIN=$(gh api user -q .login)
# shortcut: events API keeps ~90 days / 300 events; fine for a week of catch-up.
EVENTS=$(gh api "users/$LOGIN/events?per_page=100" --paginate \
  | jq -s --arg s "$START" --arg e "$END" \
    'add | map(select(.created_at >= $s and .created_at < $e))')
loc() { TZ=America/Detroit date -r "$(date -j -u -f "%Y-%m-%dT%H:%M:%SZ" "$1" +%s)" +%H:%M; }
echo "## Events"
echo "$EVENTS" | jq -r '.[] | select(.type != "PushEvent")
  | "\(.created_at)\t\(.repo.name)\t\(.type|sub("Event$";""))\t\(.payload.action // "")\t#\(.payload.pull_request.number // .payload.issue.number // "")\t\(.payload.pull_request.title // .payload.issue.title // "")"' \
  | sort | while IFS=$'\t' read -r t rest; do echo "$(loc "$t") ${rest//$'\t'/ }"; done
echo "## Commits"
for r in $(echo "$EVENTS" | jq -r '.[] | select(.type=="PushEvent") | .repo.name' | sort -u); do
  gh api "repos/$r/commits?since=$START&until=$END&author=$LOGIN&per_page=100" \
    -q '.[] | "\(.commit.author.date)\t\(.commit.message|split("\n")[0])"' \
    | sort | while IFS=$'\t' read -r t msg; do echo "$(loc "$t") $r $msg"; done
done
