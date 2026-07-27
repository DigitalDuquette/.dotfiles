#!/bin/zsh
# AI Scorecard step 3: validate the working copy in PowerPoint, then deploy.
#
# Usage: deploy.sh <workdir> [validate]
#   <workdir>  directory holding scorecard-work.pptx (from update_slide.py)
#   validate   optional: stop after the PowerPoint validation, do not deploy
#
# PowerPoint quirks encoded here: do not use `out` as an AppleScript variable
# (reserved); PowerPoint's `duplicate slide` AppleScript command is broken,
# which is why cloning happens in update_slide.py. Opening the working copy in
# PowerPoint first means a corrupt package demands "repair" on the scratch
# file, never on the real deck.
set -euo pipefail

WORKDIR="${1:?usage: deploy.sh <workdir> [validate]}"
MODE="${2:-deploy}"
WORK="$WORKDIR/scorecard-work.pptx"
DECK="/Users/jjduqu/Library/CloudStorage/OneDrive-PADNOS/Information Solutions-Artificial Intelligence - Documents/Artificial Intelligence/scorecard/AI Scorecard.pptx"

[ -f "$WORK" ] || { echo "no working copy at $WORK" >&2; exit 1; }

echo "-- validating working copy in PowerPoint"
N=$(osascript <<EOF
tell application "Microsoft PowerPoint"
    open (POSIX file "$WORK")
    set n to count of slides of presentation "scorecard-work.pptx"
    close presentation "scorecard-work.pptx" saving no
    return n
end tell
EOF
)
echo "working copy opened cleanly, $N slides"

if [ "$MODE" = "validate" ]; then
    exit 0
fi

# the user often has the deck open as a cloud/AutoSave session; overwriting
# underneath it causes sync conflicts, so close it first
if osascript -e 'tell application "Microsoft PowerPoint" to get name of every presentation' 2>/dev/null | grep -q "AI Scorecard.pptx"; then
    echo "-- closing the open deck"
    osascript -e 'tell application "Microsoft PowerPoint" to close presentation "AI Scorecard.pptx" saving no'
fi

cp "$WORK" "$DECK"
echo "-- deployed, reopening at the last slide"

osascript <<EOF
tell application "Microsoft PowerPoint"
    activate
    open (POSIX file "$DECK")
    set n to count of slides of presentation "AI Scorecard.pptx"
    go to slide (view of document window 1) number n
end tell
EOF
echo "done"
