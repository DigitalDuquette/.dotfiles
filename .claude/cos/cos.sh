#!/bin/bash
# Chief of staff: launchd entry point. No LLM here except the morning triage.
#
#   cos.sh today     4:55 PM weekdays: nag if today's /today note is missing
#   cos.sh morning   every 5 min: once Duq has been at the laptop ~10 min,
#                    nag about yesterday's /today, then prep the triage brief
#   cos.sh watch     every 15 min: commit and push the watched repos
#   cos.sh test      send a test notification (click it to check the action)
#
# A notification click opens Ghostty in the vault running the right command.
# Each notification fires once per key (see notify), so a 4:55 job that runs
# late on wake and the morning check don't nag twice about the same thing.
set -uo pipefail
export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:$PATH"

VAULT="$HOME/Library/Mobile Documents/iCloud~md~obsidian/Documents/padnos"
COS="$(cd "$(dirname "$0")" && pwd)"
STATE="$HOME/.local/state/cos"
LOG="$STATE/cos.log"
TODAY=$(date +%F)
mkdir -p "$STATE/stamps"

log() { echo "$(date '+%F %T') $*" >> "$LOG"; }

# Shell command that opens a Ghostty window in the vault running $1.
in_ghostty() {
  local inner
  inner="cd $(printf %q "$VAULT") && $1; exec zsh -l"
  printf 'open -na Ghostty.app --args -e /bin/zsh -lc %q' "$inner"
}

# notify KEY TITLE MESSAGE CLICK_COMMAND: once per KEY, ever.
notify() {
  local stamp="$STATE/stamps/$1"
  [[ -e $stamp ]] && return 0
  terminal-notifier -title "$2" -message "$3" -group "cos-$1" \
    -execute "$4" -sound Glass -ignoreDnD >/dev/null
  touch "$stamp"
  log "notified [$1] $3"
}

# Screen unlocked, keyboard or mouse used in the last 5 min. No lid check:
# docked in clamshell mode the lid is closed while Duq works.
present() {
  local root idle
  root=$(ioreg -n Root -d1)
  grep -Eq '"CGSSessionScreenIsLocked" *= *Yes' <<<"$root" && return 1
  idle=$(ioreg -c IOHIDSystem | awk '/HIDIdleTime/ {print int($NF/1e9); exit}')
  (( ${idle:-9999} < 300 ))
}

# Present on consecutive 5-min checks for >= 10 min (the "in the flow" test).
in_flow() {
  local since="$STATE/active-since"
  if ! present; then rm -f "$since"; return 1; fi
  [[ -e $since && $(date -r "$since" +%F) == "$TODAY" ]] || { touch "$since"; return 1; }
  (( $(date +%s) - $(stat -f %m "$since") >= 600 ))
}

today() {
  local msg
  msg=$(python3 "$COS/today_check.py") || { log "today_check failed"; return; }
  [[ -z $msg ]] && return
  # Key on the message: the same missing days nag once; a new day nags again.
  notify "today-$TODAY-$(md5 -q -s "$msg")" "Daily note missing" "$msg" \
    "$(in_ghostty 'claude "/today"')"
}

morning() {
  (( $(date +%u) <= 5 )) || return 0
  local h=$((10#$(date +%H)))
  (( h >= 6 && h < 13 )) || return 0
  in_flow || return 0
  today
  local started="$STATE/stamps/triage-started-$TODAY"
  [[ -e $started ]] && return 0
  # Any HTTP answer means Freshservice is reachable; 000 means no network yet.
  [[ $(curl -s -o /dev/null -m 8 -w '%{http_code}' https://padnos.freshservice.com/api/v2/tickets) != 000 ]] || return 0
  touch "$started"
  log "triage: starting headless prep"
  local out last
  # Headless: cleanup + sweep + drill + prep. No posts except the DBA cleanup;
  # post_note/set_status are not allowed here and would be denied.
  out=$(cd "$VAULT" && claude -p "/fs-triage morning" --permission-mode acceptEdits --add-dir "$STATE" \
    --allowedTools "Bash(python3 ~/.claude/skills/fs-triage/scripts/sweep.py:*)" \
      "Bash(python3 ~/.claude/skills/fs-triage/scripts/at_risk.py:*)" \
      "Bash(python3 ~/.claude/skills/fs-triage/scripts/precedents.py:*)" \
      "Bash(python3 ~/.claude/skills/fs-triage/scripts/drill.py:*)" \
      "Bash(python3 ~/.claude/skills/fs-triage/scripts/review_deck.py:*)" \
      "Bash(python3 ~/.claude/skills/fs-triage/scripts/cleanup_automated.py:*)" \
      "Bash(gh issue view:*)" "Bash(gh pr view:*)" "Bash(gh api:*)" \
    --disallowedTools "Bash(python3 ~/.claude/skills/fs-triage/scripts/post_note.py:*)" \
      "Bash(python3 ~/.claude/skills/fs-triage/scripts/set_status.py:*)" \
    2>>"$LOG")
  last=$(tail -n1 <<<"$out")
  log "triage: done: $last"
  [[ $last == *"need you"* ]] || last="Prep didn't finish cleanly; open to see why"
  notify "triage-$TODAY" "Freshservice triage" "$last" \
    "$(in_ghostty 'claude "/fs-triage review"')"
}

watch() {
  local out
  out=$(python3 "$COS/repo_watch.py" 2>&1)
  [[ -z $out ]] && return
  log "watch: $out"
  # Key on the text: repo_watch already repeats a problem at most every 6h.
  notify "watch-$(md5 -q -s "$out$(date +%F-%H)")" "Git watcher" "$out" \
    "open -a TextEdit $(printf %q "$LOG")"
}

case "${1:-}" in
  today) today ;;
  morning) morning ;;
  watch) watch ;;
  test)
    rm -f "$STATE/stamps/test"
    notify test "Chief of staff" "Test: click me to open Ghostty in the vault" \
      "$(in_ghostty 'echo "cos click works"')" ;;
  *) echo "usage: cos.sh today|morning|watch|test" >&2; exit 2 ;;
esac
