#!/usr/bin/env bash
# Freshservice tickets Jared worked on one local day: tickets he opened, and
# every reply or private note he wrote, with the text. Read for the theme of
# the day's ticket work, not as a per-ticket log.
# Reads the SQ2 warehouse (one query) instead of the API: the API needs one
# call per updated ticket (~400/day) against a 160/min limit that the agents
# share. The warehouse loads on a schedule and can lag a few hours; run
# today's capture late, or check recent tickets with fs-ticket.
# Usage: fs-tickets-day.sh YYYY-MM-DD
set -euo pipefail
read -r START END < <("$(dirname "$0")/day-bounds.sh" "$1")
export START="${START%Z}" END="${END%Z}" SQL="$(dirname "$0")/fs-tickets-day.sql"
op run --env-file ~/.config/padsql/.env.sq2 -- \
  bash -c 'sqlcmd -S SQ2 -d Fivetran -U "$PADSQL_USER" -P "$PADSQL_PASSWORD" \
    -v START="$START" END="$END" -s "|" -W -y 1000 -i "$SQL"'
