#!/usr/bin/env python3
"""Show Claude's answer on a ticket card in the review deck.

  say.py <id> "<text>"        one message
  some_cmd | say.py <id> -    the command's output (e.g. a post_note.py dry run)

Appends {"id", "from": "claude", "text", "at"} to triage/outbox.jsonl. serve.py
logs Duq's deck messages to the same file, so the card shows both sides.
"""
import datetime
import json
import sys

import paths

OUTBOX = paths.TRIAGE / "outbox.jsonl"


def append(tid, who, text):
    row = {"id": str(tid), "from": who, "text": text.strip(),
           "at": datetime.datetime.now().astimezone().isoformat(timespec="seconds")}
    with open(OUTBOX, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(row) + "\n")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    tid, text = sys.argv[1].removeprefix("SR-"), sys.argv[2]
    if not tid.isdigit():
        sys.exit("ticket id must be a number")
    if text == "-":
        text = sys.stdin.read()
    if not text.strip():
        sys.exit("empty message")
    append(tid, "claude", text)
    print(f"shown on SR-{tid}")
