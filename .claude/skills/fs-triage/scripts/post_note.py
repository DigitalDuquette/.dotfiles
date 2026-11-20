#!/usr/bin/env python3
"""Post to a Freshservice ticket as Duq (the API key owner).

The ONLY script in fs-triage that writes to Freshservice. Two modes:
  default   private note, emailed to the ticket's assigned agent (notify_emails)
  --reply   PUBLIC reply to the requester (POST /tickets/<id>/reply); the
            requester gets an email. Use only when Duq has approved the exact text.
Nothing else on the ticket changes (no status, no assignment).

Usage:
  post_note.py <ticket_id> "<text>"                    # dry run, private note
  post_note.py <ticket_id> "<text>" --post             # post private note
  post_note.py <ticket_id> "<text>" --reply            # dry run, public reply
  post_note.py <ticket_id> "<text>" --reply --post     # send public reply
"""
import argparse
import html
import json
import pathlib
import sys
import urllib.request

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import paths  # noqa: E402
from fs_api import Freshservice  # noqa: E402

CONFIG = paths.CONFIG


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("ticket_id", type=int)
    ap.add_argument("text")
    ap.add_argument("--post", action="store_true", help="actually post (default is dry run)")
    ap.add_argument("--reply", action="store_true", help="public reply to the requester instead of a private note")
    ap.add_argument("--cc", action="append", default=[], help="CC email on a --reply (repeatable)")
    args = ap.parse_args()

    fs = Freshservice(CONFIG["domain"])
    t = fs.get(f"tickets/{args.ticket_id}", include="requester")["ticket"]
    if t.get("workspace_id") != CONFIG["workspace_id"]:
        sys.exit(f"SR-{args.ticket_id} is not in workspace {CONFIG['workspace_name']}; refusing.")
    body = "<div>" + html.escape(args.text).replace("\n", "<br>") + "</div>"

    if args.reply:
        rq = t.get("requester") or {}
        endpoint, payload = "reply", {"body": body}
        to = f"{rq.get('name')} <{rq.get('email')}>  (PUBLIC reply, emailed to requester)"
        if args.cc:
            payload["cc_emails"] = args.cc
            to += f"  CC: {', '.join(args.cc)}"
    else:
        if not t.get("responder_id"):
            sys.exit(f"SR-{args.ticket_id} has no assigned agent; nobody to notify.")
        agent = fs.get(f"agents/{t['responder_id']}")["agent"]
        name = f"{agent.get('first_name', '')} {agent.get('last_name', '')}".strip()
        endpoint, payload = "notes", {"body": body, "private": True, "notify_emails": [agent["email"]]}
        to = f"{name} <{agent['email']}>  (private note)"

    print(f"SR-{args.ticket_id}: {t['subject']}")
    print(f"To: {to}")
    print(f"Text: {args.text}")
    if not args.post:
        print("\nDry run. Re-run with --post to send.")
        return

    req = urllib.request.Request(
        f"{fs.base}/tickets/{args.ticket_id}/{endpoint}",
        data=json.dumps(payload).encode(),
        headers={"Authorization": fs.auth, "Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        conv = json.load(r).get("conversation", {})
    print(f"\nPosted {endpoint} id={conv.get('id')} at {conv.get('created_at')}")
    print(f"https://{CONFIG['domain']}/a/tickets/{args.ticket_id}")


if __name__ == "__main__":
    main()
