#!/usr/bin/env python3
"""Record one of Duq's ticket calls in one step (stdlib only).

1. appends a line to decisions.jsonl (vault, paths.DECISIONS)
2. sets tickets[<id>].decided in triage/review-<date>.json (creates the entry if missing)
3. re-runs review_deck.py --date <date> so the review deck moves it to Decided
4. prints how many prepared tickets still need Duq

Usage:
  python3 ~/.claude/skills/fs-triage/scripts/log_decision.py \
    --ticket 158009 --agent "Ernie Farias" --flags REQUESTER_WAITING \
    --facts "..." --reason "..." --decision "Duq already handled it." \
    --action "None." --why "..." --decided "Duq handled it."
Use it after post_note.py --post (put the note id in --action). """
import argparse
import datetime as dt
import json
import os
import pathlib
import subprocess
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import paths  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default=dt.date.today().isoformat())
    ap.add_argument("--ticket", type=int, required=True)
    ap.add_argument("--agent", default="")
    ap.add_argument("--flags", default="", help="comma-separated sweep flags")
    ap.add_argument("--facts", default="")
    ap.add_argument("--reason", default="", help="escalation_reason: why it needed Duq")
    ap.add_argument("--decision", required=True)
    ap.add_argument("--action", default="None.")
    ap.add_argument("--why", default="")
    ap.add_argument("--decided", required=True, help="short label shown in the pane, without the date")
    a = ap.parse_args()

    line = {"date": a.date, "ticket": a.ticket, "agent": a.agent,
            "flags": [f for f in a.flags.split(",") if f], "facts": a.facts,
            "escalation_reason": a.reason, "decision": a.decision, "action": a.action, "why": a.why}
    with open(paths.DECISIONS, "a") as fh:
        fh.write(json.dumps(line) + "\n")

    prep_path = paths.TRIAGE / f"review-{a.date}.json"
    prep = json.loads(prep_path.read_text()) if prep_path.exists() else {"date": a.date, "tickets": {}}
    mmdd = dt.date.fromisoformat(a.date).strftime("%m/%d")
    prep["tickets"].setdefault(str(a.ticket), {})["decided"] = f"{mmdd}: {a.decided}"
    prep_path.write_text(json.dumps(prep, indent=2))

    deck = pathlib.Path(__file__).resolve().parent / "review_deck.py"
    subprocess.run([sys.executable, str(deck), "--date", a.date], check=True, stdout=subprocess.DEVNULL)

    left = [i for i, t in prep["tickets"].items() if t.get("ask") and not t.get("decided")]
    print(f"logged SR-{a.ticket}; {len(left)} still need you: {', '.join(left)}")


if __name__ == "__main__":
    main()
