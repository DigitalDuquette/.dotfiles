#!/usr/bin/env python3
"""Per-agent weekly punch list, built up as Duq reviews tickets.

One JSON file per agent per ISO week:
  ~/.local/state/cos/triage/punchlists/<YYYY-Www>/<agent-slug>.json
Each item = one ticket: what's going on, what Duq asked, when, current status.
`show` renders markdown suitable for pasting into the 1:1 Teams channel.
Local only; nothing is posted anywhere.

Usage:
  punchlist.py seed  "<Agent Name>"            # add the agent's flagged tickets from triage/latest.json as 'to review'
  punchlist.py add   "<Agent Name>" <ticket_id> --summary "..." [--ask "..."] [--status open|asked|done]
  punchlist.py show  "<Agent Name>"            # markdown
  punchlist.py list                            # agents with a punch list this week
"""
import argparse
import datetime as dt
import json
import os
import pathlib

import paths  # noqa: E402
WEEK = dt.date.today().strftime("%G-W%V")
DIR = paths.TRIAGE / "punchlists" / WEEK
DOMAIN = "padnos.freshservice.com"


def slug(name):
    return name.lower().replace(" ", "-")


def load(agent):
    p = DIR / f"{slug(agent)}.json"
    return json.loads(p.read_text()) if p.exists() else {"agent": agent, "week": WEEK, "items": {}}


def save(data):
    DIR.mkdir(parents=True, exist_ok=True)
    (DIR / f"{slug(data['agent'])}.json").write_text(json.dumps(data, indent=1))


def seed(agent):
    data = load(agent)
    sweep = json.loads((paths.TRIAGE / "latest.json").read_text())
    n = 0
    for r in sweep["tickets"]:
        if r["agent"] == agent and r["needs_eyes"] and not r["automated"] and str(r["id"]) not in data["items"]:
            data["items"][str(r["id"])] = {
                "subject": r["subject"].strip(), "flags": [f for f in r["flags"] if f != "FR_DUE_SOON"],
                "age_days": r["age_days"], "idle_days": r["days_since_agent_touch"],
                "summary": "", "ask": "", "status": "to review", "updated": dt.date.today().isoformat()}
            n += 1
    save(data)
    print(f"seeded {n} tickets for {agent} ({WEEK})")


def add(agent, tid, summary, ask, status):
    data = load(agent)
    item = data["items"].setdefault(str(tid), {"subject": "", "flags": []})
    if summary: item["summary"] = summary
    if ask: item["ask"] = ask
    item["status"] = status
    item["updated"] = dt.date.today().isoformat()
    save(data)
    print(f"{agent} SR-{tid}: {status}")


def show(agent):
    data = load(agent)
    order = {"asked": 0, "open": 1, "to review": 2, "done": 3}
    items = sorted(data["items"].items(), key=lambda kv: (order.get(kv[1]["status"], 9), -(kv[1].get("idle_days") or 0)))
    lines = [f"**{agent} — punch list, week {WEEK}**", ""]
    for tid, it in items:
        box = "x" if it["status"] == "done" else " "
        meta = f"{it.get('age_days', 0):.0f}d old, {it.get('idle_days', 0):.0f}d idle" if it.get("age_days") is not None else ""
        lines.append(f"- [{box}] [SR-{tid}](https://{DOMAIN}/a/tickets/{tid}) {it['subject']} ({meta})")
        if it.get("summary"): lines.append(f"  - {it['summary']}")
        if it.get("ask"): lines.append(f"  - Asked {it['updated']}: {it['ask']}")
    print("\n".join(lines))


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("seed"); s.add_argument("agent")
    a = sub.add_parser("add"); a.add_argument("agent"); a.add_argument("ticket_id", type=int)
    a.add_argument("--summary", default=""); a.add_argument("--ask", default="")
    a.add_argument("--status", default="open", choices=["to review", "open", "asked", "done"])
    sh = sub.add_parser("show"); sh.add_argument("agent")
    sub.add_parser("list")
    x = ap.parse_args()
    if x.cmd == "seed": seed(x.agent)
    elif x.cmd == "add": add(x.agent, x.ticket_id, x.summary, x.ask, x.status)
    elif x.cmd == "show": show(x.agent)
    else: print("\n".join(p.stem for p in sorted(DIR.glob("*.json"))) or "none")
