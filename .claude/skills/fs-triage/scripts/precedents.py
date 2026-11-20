#!/usr/bin/env python3
"""Duq's past triage calls (training/decisions.jsonl), matched to today's queue.

Read-only, no API calls. Two modes:

  precedents.py            After sweep.py. For every open ticket in triage/latest.json that
                           Duq has made a call on: his last call, how many working days ago,
                           and whether the agent / requester / our public reply moved since.
                             RECENT    call is within `recent_decision_working_days` (config).
                                       It's the agent's turn: list it under "Recently decided",
                                       don't re-escalate, unless the requester spoke since.
                             FOLLOW-UP older call and the agent hasn't touched the ticket since:
                                       escalate again and say the earlier call didn't move it.
                             MOVED     older call, agent active since: treat like any ticket.
  precedents.py --digest   Compact history of every call (newest first), for the routine's
                           pre-run context, so each run starts with Duq's past decisions.

decisions.jsonl rows: date, ticket (id or list of ids), agent, flags, facts,
escalation_reason, decision, action, why. Optional: "rejected" (what Duq said no to).
"""
import argparse
import collections
import datetime as dt
import json
import os
import pathlib
import paths  # noqa: E402

CONFIG = paths.CONFIG
DECISIONS = paths.DECISIONS
LATEST = paths.TRIAGE / "latest.json"
URL = "https://{}/a/tickets/{{}}".format(CONFIG["domain"])
WINDOW = CONFIG.get("thresholds", {}).get("recent_decision_working_days", 3)


def load_decisions():
    """{ticket_id: [row, ...] oldest first}. A row with a list of tickets counts for each."""
    by_ticket = collections.defaultdict(list)
    if not DECISIONS.exists():
        return by_ticket
    for n, line in enumerate(DECISIONS.read_text().splitlines(), 1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as e:
            raise SystemExit(f"{DECISIONS}:{n}: bad JSON ({e})")
        ids = row["ticket"] if isinstance(row["ticket"], list) else [row["ticket"]]
        for t in ids:
            by_ticket[int(t)].append(row)
    for rows in by_ticket.values():
        rows.sort(key=lambda r: r["date"])
    return by_ticket


def working_days_since(day: str, today: dt.date) -> int:
    d, n = dt.date.fromisoformat(day), 0
    while d < today:
        d += dt.timedelta(days=1)
        if d.weekday() < 5:
            n += 1
    return n


def short(text, n=220):
    text = " ".join(str(text or "").split())
    return text if len(text) <= n else text[: n - 1] + "…"


def digest(by_ticket):
    seen, out = set(), []
    rows = sorted({id(r): r for rs in by_ticket.values() for r in rs}.values(),
                  key=lambda r: r["date"], reverse=True)
    for r in rows:
        if id(r) in seen:
            continue
        seen.add(id(r))
        ids = r["ticket"] if isinstance(r["ticket"], list) else [r["ticket"]]
        line = f"- {r['date']} SR-{', SR-'.join(map(str, ids))} ({r.get('agent', '?')}): {short(r.get('decision'))}"
        if r.get("why"):
            line += f" | why: {short(r['why'], 160)}"
        if r.get("rejected"):
            line += f" | rejected: {short(r['rejected'], 120)}"
        out.append(line)
    print(f"# Duq's past triage calls ({len(out)} decisions, newest first)\n")
    print("Use these: his last call on a ticket, and the pattern of calls on similar tickets.\n")
    print("\n".join(out) if out else "_none yet_")


def match(by_ticket):
    if not LATEST.exists():
        raise SystemExit("triage/latest.json missing: run sweep.py first")
    latest = json.loads(LATEST.read_text())
    swept = dt.datetime.fromisoformat(latest["generated_at"].replace("Z", "+00:00")).astimezone()
    today = swept.date()
    groups = {"RECENT": [], "FOLLOW-UP": [], "MOVED": []}
    for t in latest["tickets"]:
        rows = by_ticket.get(int(t["id"]))
        if not rows:
            continue
        last = rows[-1]
        wd = working_days_since(last["date"], today)
        # Agent touch already excludes Duq's notes (sweep.py, manager_user_ids), so count it from the
        # START of the call day. A public reply on the call day is often Duq's own reply (the call
        # itself), so count replies only from the END of the call day.
        day = dt.date.fromisoformat(last["date"])

        def after(days_ago, start):
            edge = dt.datetime.combine(start, dt.time(), tzinfo=swept.tzinfo)
            return days_ago is not None and days_ago < (swept - edge).total_seconds() / 86400

        touched = after(t["days_since_agent_touch"], day)
        replied = after(t["days_since_our_public_reply"], day + dt.timedelta(days=1))
        req_spoke = t["requester_spoke_last"] and after(t["days_since_requester_msg"], day)
        moved = ", ".join(x for x, ok in (("agent touched it", touched), ("public reply sent", replied),
                                          ("requester wrote", req_spoke)) if ok) or "nothing since"
        status = "RECENT" if wd <= WINDOW else ("MOVED" if touched or replied else "FOLLOW-UP")
        line = (f"- [{t['sr']}]({URL.format(t['id'])}) {t['agent'] or 'unassigned'} · {short(t['subject'], 60)}\n"
                f"  last call {last['date']} ({wd} working days ago, {len(rows)} call(s) total): {short(last.get('decision'))}\n"
                f"  since then: {moved} · flags now: {' '.join(t['flags']) or 'none'}")
        if status == "RECENT" and req_spoke:
            line += "\n  ! requester wrote since your call: escalate"
        groups[status].append(line)
    print(f"# Past calls on today's open tickets (window {WINDOW} working days, sweep {latest['generated_at']})\n")
    titles = {"FOLLOW-UP": "Follow-up: your call didn't move it (escalate again, say so)",
              "RECENT": "Recently decided: agent's turn (list briefly, don't re-escalate)",
              "MOVED": "Moved since your call (treat as normal)"}
    for k in ("FOLLOW-UP", "RECENT", "MOVED"):
        print(f"## {titles[k]} ({len(groups[k])})")
        print("\n".join(groups[k]) if groups[k] else "_none_")
        print()


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Duq's past triage calls matched to today's queue.")
    ap.add_argument("--digest", action="store_true", help="compact history for pre-run context")
    args = ap.parse_args()
    d = load_decisions()
    digest(d) if args.digest else match(d)
