#!/usr/bin/env python3
"""Change ticket status (e.g. resolve), with an optional private note first.

Writes to Freshservice. Dry run unless --post. For each ticket:
  1. checks it is in the IS workspace and still unresolved
  2. posts the note as a PRIVATE note, with no email notification (use for
     housekeeping, so a bulk cleanup doesn't flood the agent's inbox)
  3. sets the status via PUT /tickets/<id>
If Freshservice rejects the status change (e.g. a field required on resolve),
the error is printed and that ticket is left as-is; the others continue.

Usage:
  set_status.py --status resolved --note "Cleaning up backlog of tickets." 158445 158260 ...
  set_status.py ... --post
"""
import argparse
import html
import json
import pathlib
import sys
import urllib.error
import urllib.request

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import paths  # noqa: E402
from fs_api import Freshservice  # noqa: E402

CONFIG = paths.CONFIG
STATUS = {"open": 2, "pending": 3, "resolved": 4, "closed": 5}


def send(fs, method, path, payload):
    req = urllib.request.Request(f"{fs.base}/{path}", data=json.dumps(payload).encode(), method=method,
                                 headers={"Authorization": fs.auth, "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.load(r), None
    except urllib.error.HTTPError as e:
        return None, f"HTTP {e.code}: {e.read().decode()[:400]}"


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("ticket_ids", nargs="+", type=int)
    ap.add_argument("--status", required=True, choices=STATUS)
    ap.add_argument("--note", default="", help="private note to post before the status change (no email)")
    ap.add_argument("--post", action="store_true", help="actually write (default is dry run)")
    args = ap.parse_args()
    fs = Freshservice(CONFIG["domain"])
    target = STATUS[args.status]

    for tid in args.ticket_ids:
        t = fs.get(f"tickets/{tid}")["ticket"]
        label = f"SR-{tid} [{CONFIG['unresolved_statuses'].get(str(t['status']), t['status'])}] {t['subject'].strip()[:60]}"
        if t.get("workspace_id") != CONFIG["workspace_id"]:
            print(f"SKIP {label}: not in {CONFIG['workspace_name']}")
            continue
        if str(t["status"]) not in CONFIG["unresolved_statuses"]:
            print(f"SKIP {label}: already resolved/closed")
            continue
        if not args.post:
            print(f"DRY  {label} -> {args.status}" + (f"  (note: {args.note})" if args.note else ""))
            continue
        if args.note:
            _, err = send(fs, "POST", f"tickets/{tid}/notes",
                          {"body": f"<div>{html.escape(args.note)}</div>", "private": True})
            if err:
                print(f"FAIL {label}: note not posted, status unchanged. {err}")
                continue
        r, err = send(fs, "PUT", f"tickets/{tid}", {"status": target})
        if err:
            print(f"FAIL {label}: note posted, status change rejected. {err}")
        else:
            print(f"OK   {label} -> {args.status} (status now {r['ticket']['status']})")
    if not args.post:
        print("\nDry run. Re-run with --post to write.")


if __name__ == "__main__":
    main()
