#!/usr/bin/env python3
"""
Add Rating and Score columns to a Claude members-analytics CSV export.

One job. Reads the export, appends the two columns, writes a new CSV. Every original
column and value is passed through untouched.

    Rating  the word grouping: Deep / Steady / Occasional / Dormant
    Score   0-100 utilization index, for ranking within a group

    python3 rate.py                        # newest members-analytics-*.csv in ~/Downloads
    python3 rate.py path/to/export.csv     # a specific export
    python3 rate.py export.csv -o out.csv  # choose the output path

Works with any window length. The 30-day and 90-day exports use the same thresholds
expressed as rates, so a member rated Deep on one window is rated on the same standard in
the other. Window length comes from the filename date range, or --days.

Never modifies the input file, and never touches claude-rollout.xlsx.
"""

import argparse
import csv
import math
import re
import sys
from datetime import date
from pathlib import Path

DOWNLOADS = Path.home() / "Downloads"

# Thresholds as rates, so any window length is judged on the same standard.
# Anchored to the 90-day definitions: Deep = 40 of 90 days and 300 interactions,
# Steady = 20 of 90 days and 100 interactions.
DEEP_DAY_RATE, DEEP_PER_DAY = 40 / 90, 300 / 90
STEADY_DAY_RATE, STEADY_PER_DAY = 20 / 90, 100 / 90

# Score is half "how often" and half "how much", both on absolute scales so the number is
# comparable month to month rather than relative to whoever happens to be in the export.
# Intensity is log-scaled against a heavy-use reference of 15 interactions per day, about
# the 90th percentile, so one outlier does not flatten everyone else.
SCORE_REFERENCE_PER_DAY = 15.0

INTERACTION_COLS = ["Messages", "Cowork Messages", "Code sessions"]
SURFACE_COLS = {"Chat": "Messages", "Cowork": "Cowork Messages", "Code": "Code sessions"}


def num(row, key):
    try:
        return float(row.get(key) or 0)
    except (ValueError, TypeError):
        return 0.0


def window_days(path, override=None):
    """Window length from the filename date range, else --days, else 90."""
    if override:
        return override, "--days"
    m = re.search(r"(\d{4}-\d{2}-\d{2})-to-(\d{4}-\d{2}-\d{2})", path.name)
    if m:
        a = date(*[int(x) for x in m.group(1).split("-")])
        b = date(*[int(x) for x in m.group(2).split("-")])
        span = (b - a).days
        if span > 0:
            return span, f"filename ({m.group(1)} to {m.group(2)})"
    return 90, "default, no date range in filename"


def newest_export():
    """Newest raw export. Skips this script's own output, which matches the same glob."""
    files = sorted((p for p in DOWNLOADS.glob("members-analytics-*.csv")
                    if not p.stem.endswith("-rated")),
                   key=lambda p: p.stat().st_mtime, reverse=True)
    return files[0] if files else None


def rate(row, days):
    """(rating word, score 0-100, primary surface)."""
    active = num(row, "Days Active")
    acts = sum(num(row, c) for c in INTERACTION_COLS)
    if acts == 0:
        return "Dormant", 0, ""

    if active >= DEEP_DAY_RATE * days and acts >= DEEP_PER_DAY * days:
        r = "Deep"
    elif active >= STEADY_DAY_RATE * days and acts >= STEADY_PER_DAY * days:
        r = "Steady"
    else:
        r = "Occasional"

    consistency = min(1.0, active / days)
    intensity = min(1.0, math.log1p(acts / days) / math.log1p(SCORE_REFERENCE_PER_DAY))
    score = round(100 * (0.5 * consistency + 0.5 * intensity))

    mix = {k: num(row, v) for k, v in SURFACE_COLS.items()}
    return r, score, max(mix, key=mix.get)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("csv_path", nargs="?", help="analytics export (default: newest in ~/Downloads)")
    ap.add_argument("-o", "--out", help="output path (default: <input>-rated.csv)")
    ap.add_argument("--days", type=int, help="window length if not in the filename")
    ap.add_argument("--surface", action="store_true",
                    help="also add a Primary Surface column")
    args = ap.parse_args()

    path = Path(args.csv_path) if args.csv_path else newest_export()
    if not path:
        sys.exit(f"no members-analytics-*.csv found in {DOWNLOADS}")
    if not path.exists():
        sys.exit(f"not found: {path}")

    days, source = window_days(path, args.days)

    with open(path, encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        fields = list(reader.fieldnames or [])
        rows = list(reader)

    missing = [c for c in ["Days Active", *INTERACTION_COLS] if c not in fields]
    if missing:
        sys.exit(f"{path.name} is missing expected columns: {', '.join(missing)}\n"
                 f"found: {', '.join(fields)}")

    out_fields = [c for c in fields
                  if c not in ("Rating", "Score", "Primary Surface")]
    out_fields += ["Rating", "Score"]
    if args.surface:
        out_fields.append("Primary Surface")

    counts, scores = {}, {}
    for r in rows:
        rating, score, surface = rate(r, days)
        r["Rating"] = rating
        r["Score"] = score
        if args.surface:
            r["Primary Surface"] = surface
        counts[rating] = counts.get(rating, 0) + 1
        scores.setdefault(rating, []).append(score)

    out = Path(args.out) if args.out else path.with_name(path.stem + "-rated.csv")
    with open(out, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=out_fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)

    print(f"input   : {path.name}")
    print(f"window  : {days} days, from {source}")
    print(f"criteria: Deep >= {DEEP_DAY_RATE * days:.0f} active days and "
          f"{DEEP_PER_DAY * days:.0f} interactions")
    print(f"          Steady >= {STEADY_DAY_RATE * days:.0f} active days and "
          f"{STEADY_PER_DAY * days:.0f} interactions")
    print(f"score   : 50% active-day rate + 50% log intensity vs "
          f"{SCORE_REFERENCE_PER_DAY:.0f} interactions/day")
    print()
    print(f"  {'rating':<12}{'n':>5}{'share':>7}{'score range':>16}{'median':>8}")
    for k in ["Deep", "Steady", "Occasional", "Dormant"]:
        n = counts.get(k, 0)
        if not n:
            continue
        v = sorted(scores[k])
        rng = f"{v[0]}-{v[-1]}"
        print(f"  {k:<12}{n:>5}{100 * n / len(rows):>6.0f}%{rng:>16}{v[len(v) // 2]:>8}")
    print(f"  {'total':<12}{len(rows):>5}")
    print()
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
