#!/usr/bin/env python3
"""Build the data for the ticket review deck (deck/index.html, served by deck/serve.py).

Inputs (all local, no API calls):
  triage/latest.json              from sweep.py: every open ticket + flags
  triage/review-<date>.json       written by Claude: per-ticket prep (ask, discussion,
                                  blocker, who holds it, possible responses)
  decisions.jsonl                 via precedents.py: Duq's last call per ticket
Output:
  triage/review-latest.json       what the deck polls (write-then-rename, never half-written)

Usage: review_deck.py [--date YYYY-MM-DD]
"""
import argparse
import datetime as dt
import json
import os
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import paths  # noqa: E402
import precedents  # noqa: E402
import tempfile  # noqa: E402


SIGNAL_ORDER = ["OVERDUE", "FR_OVERDUE", "REQUESTER_WAITING", "IDLE", "PARKED_BUT_OURS", "UNASSIGNED", "FR_DUE_SOON"]
SIGNAL_LABEL = {"OVERDUE": "overdue", "FR_OVERDUE": "no first reply", "REQUESTER_WAITING": "requester waiting",
                "IDLE": "idle", "PARKED_BUT_OURS": "parked", "UNASSIGNED": "unassigned", "FR_DUE_SOON": "reply due"}


def build_rows(date):
    latest = json.loads((paths.TRIAGE / "latest.json").read_text())
    review_path = paths.TRIAGE / f"review-{date}.json"
    prep = json.loads(review_path.read_text())["tickets"] if review_path.exists() else {}
    calls = precedents.load_decisions()
    rows = []
    for t in latest["tickets"]:
        if t["automated"]:
            continue
        p = prep.get(str(t["id"]), {})
        last = calls.get(int(t["id"]), [])
        rows.append({
            "id": t["id"], "url": t["url"], "subject": t["subject"], "agent": t["agent"] or "Unassigned",
            "status": t["status"], "age": round(t["age_days"] or 0), "due": (t["due_by"] or "")[:10],
            "touch": t["days_since_agent_touch"], "pub": t["days_since_our_public_reply"],
            "flags": [f for f in SIGNAL_ORDER if f in t["flags"]],
            "prep": p, "last_call": (f"{last[-1]['date']}: {last[-1].get('decision', '')}" if last else ""),
            # sort: prepared tickets first (the bot's "needs you" list), then by signal weight, then age
            "rank": (0 if p and not p.get("decided") else 1 if p else 2,
                     min([SIGNAL_ORDER.index(f) for f in t["flags"] if f in SIGNAL_ORDER] or [99]),
                     -(t["age_days"] or 0)),
        })
    rows.sort(key=lambda r: r["rank"])
    for r in rows:
        del r["rank"]
    return latest, rows


def export(latest, rows, date):
    dest = paths.TRIAGE / "review-latest.json"
    doc = {"date": date, "sweep_at": latest["generated_at"], "exported_at": dt.datetime.now().astimezone().isoformat(),
           "totals": latest["totals"], "rows": rows}
    fd, tmp = tempfile.mkstemp(dir=dest.parent, prefix=".review-", suffix=".json")
    with os.fdopen(fd, "w") as fh:
        json.dump(doc, fh)
    os.replace(tmp, dest)
    return dest


def main():
    ap = argparse.ArgumentParser(description="Write review-latest.json for the review deck.")
    ap.add_argument("--date", default=dt.date.today().isoformat())
    ap.add_argument("--export", action="store_true", help="accepted for compatibility; always exports")
    args = ap.parse_args()
    latest, rows = build_rows(args.date)
    print(export(latest, rows, args.date))
    needs = sum(1 for r in rows if r["prep"].get("ask") and not r["prep"].get("decided"))
    print(f"{needs} need you")


if __name__ == "__main__":
    main()
