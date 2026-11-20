#!/usr/bin/env python3
"""Sweep the Information Solutions queue and flag tickets that need Duq.

Deterministic: every flag below is a rule in code, not a model judgment.
The bot reads the output and investigates the flagged tickets; it never
decides on its own what to skip.

Flags (per unresolved ticket):
  FR_OVERDUE         no first response and fr_due_by has passed
                     (matches the dashboard tile "IS - First Response Overdue")
  OVERDUE            is_escalated: resolution due_by passed
                     (matches the dashboard tile "IS - Overdue Tickets")
  REQUESTER_WAITING  requester's latest public message is newer than our latest
                     public reply, and has waited >= requester_waiting_days
  PARKED_BUT_OURS    status is Pending/On Hold, yet the requester spoke last
  IDLE               no agent activity (public reply, private note, or status
                     change) in >= idle_days  -> the "moved once a week" rule
  UNASSIGNED         no responder
Informational only:  FR_DUE_SOON (no first response yet, not yet due)

Tickets whose subject starts with an automated prefix (e.g. "DBA Checklist")
are reported in their own bucket so they don't drown the real work.

Usage:
  sweep.py                 # markdown report to stdout, JSON to ~/.local/state/cos/triage/
  sweep.py --json          # JSON to stdout
Cost: 1 filter page per 30 tickets + 3 credits per ticket + 1 agents page.
"""
import argparse
import collections
import datetime as dt
import json
import os
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import paths  # noqa: E402
from fs_api import Freshservice  # noqa: E402

CONFIG = paths.CONFIG
NOW = dt.datetime.now(dt.timezone.utc)
NEEDS_EYES = {"FR_OVERDUE", "OVERDUE", "REQUESTER_WAITING", "PARKED_BUT_OURS", "IDLE", "UNASSIGNED"}


def ts(s):
    return dt.datetime.fromisoformat(s.replace("Z", "+00:00")) if s else None


def days(s):
    return None if not s else (NOW - ts(s)).total_seconds() / 86400


def assess(t: dict, agents: dict) -> dict:
    """Turn one full ticket (stats + conversations) into facts and flags."""
    th = CONFIG["thresholds"]
    stats = t.get("stats") or {}
    convs = sorted(t.get("conversations") or [], key=lambda c: c["created_at"])
    requester_ids = {t.get("requester_id"), t.get("requested_for_id")}

    our_public = [c for c in convs if not c["incoming"] and not c["private"]]
    requester_public = [c for c in convs if c["incoming"] and not c["private"] and c["user_id"] in requester_ids]
    managers = {int(k) for k in CONFIG.get("manager_user_ids", {})}
    agent_activity = [c for c in convs if c["user_id"] in agents and c["user_id"] not in requester_ids
                      and c["user_id"] not in managers]  # Duq's pings are not the agent working

    last_reply = our_public[-1]["created_at"] if our_public else None
    last_requester = requester_public[-1]["created_at"] if requester_public else None
    last_agent_touch = max(
        [c["created_at"] for c in agent_activity] + [stats.get("status_updated_at") or t["created_at"]]
    )
    requester_spoke_last = bool(last_requester and (not last_reply or last_requester > last_reply))

    flags = []
    if not stats.get("first_responded_at"):
        flags.append("FR_OVERDUE" if t.get("fr_due_by") and ts(t["fr_due_by"]) < NOW else "FR_DUE_SOON")
    if t.get("is_escalated"):
        flags.append("OVERDUE")
    if requester_spoke_last and days(last_requester) >= th["requester_waiting_days"]:
        flags.append("REQUESTER_WAITING")
    if requester_spoke_last and t["status"] in CONFIG["waiting_statuses"]:
        flags.append("PARKED_BUT_OURS")
    if days(last_agent_touch) >= th["idle_days"]:
        flags.append("IDLE")
    if not t.get("responder_id"):
        flags.append("UNASSIGNED")

    r1 = lambda x: None if x is None else round(x, 1)  # noqa: E731
    return {
        "id": t["id"],
        "sr": f"SR-{t['id']}",
        "url": f"https://{CONFIG['domain']}/a/tickets/{t['id']}",
        "subject": t["subject"],
        "status": CONFIG["unresolved_statuses"].get(str(t["status"]), t["status"]),
        "priority": CONFIG["priorities"].get(str(t["priority"]), t["priority"]),
        "group": CONFIG["groups"].get(str(t.get("group_id")), t.get("group_id")),
        "agent": agents.get(t.get("responder_id"), "Unassigned"),
        "requester_id": t.get("requester_id"),
        "automated": any(t["subject"].startswith(p) for p in CONFIG["automated_subject_prefixes"]),
        "age_days": r1(days(t["created_at"])),
        "fr_due_by": t.get("fr_due_by"),
        "due_by": t.get("due_by"),
        "first_responded_at": stats.get("first_responded_at"),
        "days_since_our_public_reply": r1(days(last_reply)),
        "days_since_requester_msg": r1(days(last_requester)),
        "days_since_agent_touch": r1(days(last_agent_touch)),
        "requester_spoke_last": requester_spoke_last,
        "public_replies": len(our_public),
        "private_notes": sum(1 for c in convs if c["private"]),
        "flags": flags,
        "needs_eyes": bool(NEEDS_EYES & set(flags)),
    }


def sweep() -> dict:
    fs = Freshservice(CONFIG["domain"])
    statuses = " OR ".join(f"status:{s}" for s in CONFIG["unresolved_statuses"])
    listed = fs.filter_tickets(f"workspace_id:{CONFIG['workspace_id']} AND ({statuses})")
    agents = fs.agents()
    rows = [assess(fs.ticket(t["id"]), agents) for t in listed]
    return {
        "generated_at": NOW.isoformat(),
        "workspace": CONFIG["workspace_name"],
        "api_calls": fs.calls,
        "totals": {
            "unresolved": len(rows),
            "fr_overdue": sum("FR_OVERDUE" in r["flags"] for r in rows),
            "overdue": sum("OVERDUE" in r["flags"] for r in rows),
            "needs_eyes": sum(r["needs_eyes"] for r in rows),
        },
        "tickets": rows,
    }


def markdown(data: dict) -> str:
    rows, tot = data["tickets"], data["totals"]
    out = [f"# {data['workspace']} sweep — {data['generated_at'][:16]}Z",
           f"Unresolved {tot['unresolved']} · First response overdue {tot['fr_overdue']} · "
           f"Overdue {tot['overdue']} · Needs eyes {tot['needs_eyes']}", ""]

    def table(items):
        out.append("| Ticket | Agent | Status | Age d | Since touch d | Flags | Subject |")
        out.append("|---|---|---|---:|---:|---|---|")
        for r in sorted(items, key=lambda r: -(r["days_since_agent_touch"] or 0)):
            out.append(f"| [{r['sr']}]({r['url']}) | {r['agent']} | {r['status']} | {r['age_days']:.0f} | "
                       f"{r['days_since_agent_touch']:.0f} | {' '.join(f for f in r['flags'] if f in NEEDS_EYES)} | "
                       f"{r['subject'][:60]} |")
        out.append("")

    out.append("## First response overdue")
    table([r for r in rows if "FR_OVERDUE" in r["flags"] and not r["automated"]])
    out.append("## Overdue (resolution SLA)")
    table([r for r in rows if "OVERDUE" in r["flags"] and not r["automated"]])

    out.append("## By agent")
    out.append("| Agent | Open | Needs eyes | FR overdue | Overdue | Requester waiting | Idle ≥7d | Automated |")
    out.append("|---|---:|---:|---:|---:|---:|---:|---:|")
    by = collections.defaultdict(list)
    for r in rows:
        by[r["agent"]].append(r)
    for agent, rs in sorted(by.items(), key=lambda kv: -sum(r["needs_eyes"] and not r["automated"] for r in kv[1])):
        human = [r for r in rs if not r["automated"]]
        c = lambda f: sum(f in r["flags"] for r in human)  # noqa: E731
        out.append(f"| {agent} | {len(rs)} | {sum(r['needs_eyes'] for r in human)} | {c('FR_OVERDUE')} | "
                   f"{c('OVERDUE')} | {c('REQUESTER_WAITING')} | {c('IDLE')} | {len(rs) - len(human)} |")
    out.append("")

    for agent, rs in sorted(by.items()):
        flagged = [r for r in rs if r["needs_eyes"] and not r["automated"]]
        if flagged:
            out.append(f"### {agent} — {len(flagged)} need eyes")
            table(flagged)

    auto = [r for r in rows if r["automated"]]
    if auto:
        out.append(f"## Automated tickets ({len(auto)}) — " +
                   ", ".join(f"{k}: {v}" for k, v in collections.Counter(r["agent"] for r in auto).items()))
        out.append(f"First response overdue among them: {sum('FR_OVERDUE' in r['flags'] for r in auto)}; "
                   f"oldest {max(r['age_days'] for r in auto):.0f} days.")
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--json", action="store_true", help="print JSON instead of markdown")
    args = ap.parse_args()
    data = sweep()
    outdir = paths.TRIAGE
    outdir.mkdir(exist_ok=True)
    stamp = NOW.strftime("%Y%m%dT%H%MZ")
    (outdir / f"sweep-{stamp}.json").write_text(json.dumps(data, indent=1))
    (outdir / "latest.json").write_text(json.dumps(data, indent=1))
    print(json.dumps(data, indent=1) if args.json else markdown(data))
    print(f"\n_saved {outdir}/sweep-{stamp}.json · {data['api_calls']} API calls_", file=sys.stderr)


if __name__ == "__main__":
    main()
