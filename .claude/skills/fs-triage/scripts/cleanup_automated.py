#!/usr/bin/env python3
"""Standing housekeeping: resolve old automated tickets (e.g. DBA Checklists).

Rules live in config.json -> automated_cleanup.max_age_days (subject -> days).
Each matching unresolved IS ticket older than its limit gets the private note
(no email) and is set to Resolved, via the same calls as set_status.py.
Duq authorized this as a standing order on 2026-11-12.
Dry run unless --post. Prints one line per ticket; prints nothing when there's nothing to do.

Usage: cleanup_automated.py [--post]
"""
import argparse
import datetime as dt
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import paths  # noqa: E402
from fs_api import Freshservice  # noqa: E402
from set_status import STATUS, send  # noqa: E402
import html  # noqa: E402

CONFIG = paths.CONFIG


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--post", action="store_true")
    args = ap.parse_args()
    rules = CONFIG["automated_cleanup"]
    fs = Freshservice(CONFIG["domain"])
    statuses = " OR ".join(f"status:{s}" for s in CONFIG["unresolved_statuses"])
    now = dt.datetime.now(dt.timezone.utc)
    for t in fs.filter_tickets(f"workspace_id:{CONFIG['workspace_id']} AND ({statuses})"):
        limit = rules["max_age_days"].get(t["subject"].strip())
        if limit is None:
            continue
        age = (now - dt.datetime.fromisoformat(t["created_at"].replace("Z", "+00:00"))).total_seconds() / 86400
        if age <= limit:
            continue
        label = f"SR-{t['id']} {t['subject'].strip()} ({age:.1f}d old, limit {limit}d)"
        if not args.post:
            print(f"DRY  {label}")
            continue
        _, err = send(fs, "POST", f"tickets/{t['id']}/notes", {"body": f"<div>{html.escape(rules['note'])}</div>", "private": True})
        if not err:
            _, err = send(fs, "PUT", f"tickets/{t['id']}", {"status": STATUS["resolved"]})
        print(f"{'FAIL' if err else 'OK  '} {label}" + (f" {err}" if err else " -> resolved"))


if __name__ == "__main__":
    main()
