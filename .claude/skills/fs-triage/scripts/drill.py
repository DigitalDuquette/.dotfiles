#!/usr/bin/env python3
"""Readable digest of one or more tickets, for triage drill-downs.

For each ticket: requester (name, title), assignee, status, dates, the
description as text, the FULL conversation thread (paged via
/tickets/<id>/conversations: include=conversations stops at 10), author names
for agents and requesters, attachments, project task keys (e.g. IS26-390)
and GitHub links found anywhere in the ticket.
Read-only.

Usage: drill.py <ticket_id> [<ticket_id> ...]  > digest.md
"""
import html
import json
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import paths  # noqa: E402
from fs_api import Freshservice  # noqa: E402

CONFIG = paths.CONFIG
fs = Freshservice(CONFIG["domain"])
_people = {}


def person(uid):
    """'First Last (job title)' for an agent or requester id."""
    if not uid:
        return "—"
    if uid not in _people:
        _people[uid] = str(uid)
        for ep, key in (("agents", "agent"), ("requesters", "requester")):
            try:
                p = fs.get(f"{ep}/{uid}")[key]
                title = f", {p['job_title']}" if p.get("job_title") else ""
                _people[uid] = f"{p.get('first_name', '')} {p.get('last_name', '')}".strip() + title
                break
            except (RuntimeError, ValueError):  # ValueError: empty/non-JSON body (e.g. deleted user)
                continue
    return _people[uid]


def text(h, limit=None):
    t = html.unescape(re.sub(r"<[^>]+>", " ", h or ""))
    t = re.split(r"\s(?:From: |-----Original Message)", t)[0]  # drop quoted email history
    t = re.sub(r"\s+", " ", t).strip()
    return t if not limit or len(t) <= limit else t[:limit] + " …"


def digest(tid):
    t = fs.get(f"tickets/{tid}", include="stats")["ticket"]
    convs = []
    for page in range(1, 20):
        batch = fs.get(f"tickets/{tid}/conversations", per_page=100, page=page)["conversations"]
        convs += batch
        if len(batch) < 100:
            break
    convs.sort(key=lambda c: c["created_at"])
    blob = (t.get("description") or "") + " ".join(c.get("body") or "" for c in convs)
    keys = sorted(set(re.findall(r"\b(?:IS2\d|IS|OPS2\d|SLG|ITMGMT)-\d+\b", re.sub(r"<[^>]+>", " ", blob))))
    gh = sorted(set(re.findall(r"https://github\.com/[^\s\"'<>]+", blob)))
    st = CONFIG["unresolved_statuses"].get(str(t["status"]), t["status"])

    out = [f"## SR-{tid} · {t['subject'].strip()}",
           f"https://{CONFIG['domain']}/a/tickets/{tid}",
           f"- Requester: {person(t['requester_id'])}",
           f"- Assigned: {person(t.get('responder_id'))} · group {CONFIG['groups'].get(str(t.get('group_id')), t.get('group_id'))}",
           f"- Status: {st} · created {t['created_at'][:10]} · due {str(t.get('due_by'))[:10]} · "
           f"first response {str((t.get('stats') or {}).get('first_responded_at'))[:10]}",
           f"- Category: {t.get('category')} / {t.get('sub_category')}"]
    if t.get("attachments"):
        out.append("- Attachments: " + ", ".join(a["name"] for a in t["attachments"]))
    if keys:
        out.append("- Project task keys: " + ", ".join(keys))
    if gh:
        out.append("- GitHub: " + ", ".join(gh))
    out += ["", "**Description:** " + text(t.get("description"), 2500), "",
            f"**Thread ({len(convs)}):**"]
    for c in convs:
        kind = ("IN " if c["incoming"] else "OUT") + (" private" if c["private"] else " public ")
        att = f" [attachments: {', '.join(a['name'] for a in c.get('attachments', []))}]" if c.get("attachments") else ""
        out.append(f"- {c['created_at'][:16].replace('T', ' ')} {kind} {person(c['user_id'])}: {text(c.get('body'), 1500)}{att}")
    return "\n".join(out) + "\n"


if __name__ == "__main__":
    for arg in sys.argv[1:]:
        print(digest(int(arg.removeprefix("SR-"))))
