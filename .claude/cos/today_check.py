#!/usr/bin/env python3
"""today-check: did Jared run /today (Claude Code) for every workday?

Run by cos.sh (launchd) at 4:55pm weekdays and at the morning presence
check. stdout becomes a macOS notification, so:

  - all caught up  -> print nothing (no notification)
  - days missing   -> print one nag message listing them

Signal: /today writes 0-inbox/daily-notes/YYYY-MM-DD.md in the padnos vault
and always ends it with an "Open loops" bullet. A note without that bullet
was started by hand, so /today has not run for that day yet.

Missing days = weekdays after the newest /today note, through today.
Today only counts once it's 4pm or later, so a late catch-up run the next
morning nags about yesterday, not about a day that isn't over.

Manual use:
  python3 today_check.py            # what the routine would post
  python3 today_check.py --status   # always print a one-line status
Stdlib only; Python 3.9+.
"""
import argparse
import datetime as dt
import re
import sys
from pathlib import Path
from zoneinfo import ZoneInfo

VAULT = Path.home() / "Library/Mobile Documents/iCloud~md~obsidian/Documents/padnos"
NOTES = VAULT / "0-inbox/daily-notes"
TZ = ZoneInfo("America/New_York")
TODAY_COUNTS_AFTER = dt.time(16, 0)
TODAY_SKILL_CAP = 7  # /today catches up at most 7 days
MARKER = re.compile(r"^\s*-\s*Open loops", re.MULTILINE)
NAME = re.compile(r"^(\d{4}-\d{2}-\d{2})\.md$")


def ran_today_skill(path: Path) -> bool:
    try:
        return bool(MARKER.search(path.read_text(encoding="utf-8")))
    except OSError:
        return False


def weekdays(start: dt.date, end: dt.date):
    d = start
    while d <= end:
        if d.weekday() < 5:
            yield d
        d += dt.timedelta(days=1)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--status", action="store_true", help="always print a status line")
    args = ap.parse_args()

    if not NOTES.is_dir():
        print(f"today-check: notes folder not found: {NOTES}. "
              "Is iCloud Drive synced? Can't tell whether /today ran.")
        return 0

    now = dt.datetime.now(TZ)
    last_day = now.date() if now.time() >= TODAY_COUNTS_AFTER else now.date() - dt.timedelta(days=1)

    done = sorted(
        dt.date.fromisoformat(m.group(1))
        for p in NOTES.iterdir()
        if (m := NAME.match(p.name)) and ran_today_skill(p)
    )

    if done:
        newest = done[-1]
        missing = list(weekdays(newest + dt.timedelta(days=1), last_day))
    else:
        # Inbox emptied by the weekly review: only today/yesterday is knowable.
        newest = None
        missing = [d for d in [last_day] if d.weekday() < 5]

    if not missing:
        if args.status:
            print(f"OK: /today is current (newest note {newest}).")
        return 0

    days = ", ".join(d.strftime("%a %b %-d") for d in missing)
    n = len(missing)
    lines = [
        f"/today hasn't run for {n} workday{'s' if n > 1 else ''}: {days}.",
        f"Newest /today note: {newest or 'none (inbox empty since the weekly review)'}.",
    ]
    oldest_gap = (now.date() - missing[0]).days
    if oldest_gap >= TODAY_SKILL_CAP:
        lines.append(f"The oldest missing day is {oldest_gap} days back. "
                     f"/today only catches up {TODAY_SKILL_CAP}, so run it with that date.")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    sys.exit(main())
