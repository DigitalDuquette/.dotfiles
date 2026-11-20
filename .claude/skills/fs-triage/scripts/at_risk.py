#!/usr/bin/env python3
"""Early-warning view per agent: what's about to go stale, from triage/latest.json.

Run sweep.py first. Read-only, no API calls. Signals (any ticket can have several):
  NO_FIRST_RESPONSE / FR_DUE_SOON   requester never got a public reply
  REQ_WAITING_<n>d                  requester spoke last, n days ago (>= 2)
  SILENT_PROGRESS                   agent active in private notes, but last public
                                    reply >= 7 days old  (Duq's #1 frustration)
  PRIVATE_ONLY                      agent activity exists but zero public replies
  DUE_IN_<n>d                       resolution due within 7 days, not yet overdue
  GOING_STALE(<n>d)                 5-6 days since agent touch: about to hit the weekly rule
  IDLE_<n>d                         >= 7 days since agent touch
  PARKED_<n>d                       Pending/On Hold, we spoke last, >= 7 days ago
Automated tickets (DBA Checklist) are counted separately.

Usage: at_risk.py [--agent "Name"] [--all]   (default hides tickets with no signals)
"""
import argparse
import collections
import datetime as dt
import json
import os
import pathlib
import paths  # noqa: E402

NOW = dt.datetime.now(dt.timezone.utc)


def risks(r):
    out, pub, touch = [], r["days_since_our_public_reply"], r["days_since_agent_touch"]
    due_in = (dt.datetime.fromisoformat(r["due_by"].replace("Z", "+00:00")) - NOW).days if r["due_by"] else None
    if "OVERDUE" in r["flags"]: out.append("OVERDUE")
    if "FR_OVERDUE" in r["flags"]: out.append("NO_FIRST_RESPONSE")
    elif "FR_DUE_SOON" in r["flags"]: out.append("FR_DUE_SOON")
    if r["requester_spoke_last"] and (r["days_since_requester_msg"] or 0) >= 2:
        out.append(f"REQ_WAITING_{r['days_since_requester_msg']:.0f}d")
    if pub is not None and pub >= 7 and touch is not None and touch < pub - 3:
        out.append(f"SILENT_PROGRESS(public {pub:.0f}d ago, touched {touch:.0f}d ago)")
    if pub is None and not r["first_responded_at"] and touch is not None and touch < (r["age_days"] or 0) - 1:
        out.append("PRIVATE_ONLY")
    if due_in is not None and 0 <= due_in <= 7 and "OVERDUE" not in r["flags"]: out.append(f"DUE_IN_{due_in}d")
    if touch is not None and 5 <= touch < 7: out.append(f"GOING_STALE({touch:.0f}d)")
    if touch is not None and touch >= 7: out.append(f"IDLE_{touch:.0f}d")
    if r["status"] in ("Pending", "On Hold") and not r["requester_spoke_last"] and (pub or 0) >= 7:
        out.append(f"PARKED_{pub:.0f}d")
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--agent"); ap.add_argument("--all", action="store_true")
    a = ap.parse_args()
    d = json.loads((paths.TRIAGE / "latest.json").read_text())
    by, auto = collections.defaultdict(list), collections.Counter()
    for r in d["tickets"]:
        if r["automated"]:
            auto[r["agent"]] += 1; continue
        if a.agent and r["agent"] != a.agent: continue
        r["risks"] = risks(r); by[r["agent"]].append(r)
    print(f"# Early warning — sweep {d['generated_at'][:16]}Z")
    for agent, rs in sorted(by.items(), key=lambda kv: -sum(bool(r["risks"]) for r in kv[1])):
        flagged = [r for r in rs if r["risks"]]
        print(f"\n## {agent}: {len(rs)} open, {len(flagged)} with signals" + (f", +{auto[agent]} automated" if auto[agent] else ""))
        for r in sorted(rs if a.all else flagged, key=lambda r: (-len(r["risks"]), -(r["days_since_agent_touch"] or 0))):
            print(f"- [{r['sr']}]({r['url']}) {r['status']} · {r['age_days']:.0f}d old · {r['subject'].strip()[:60]} — {' '.join(r['risks']) or 'ok'}")


if __name__ == "__main__":
    main()
