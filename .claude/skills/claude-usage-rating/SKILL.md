---
name: claude-usage-rating
description: Adds Rating (Deep/Steady/Occasional/Dormant) and Score (0-100) columns to a Claude members-analytics CSV export. Works with the 30-day or 90-day export. Use when rating Claude seat usage for the AISC review, license reclamation, or enablement targeting.
allowed-tools: Read, Glob, Bash(python3 /Users/jjduqu/.claude/skills/claude-usage-rating/scripts/rate.py:*), Bash(python3 ~/.claude/skills/claude-usage-rating/scripts/rate.py:*)
---

# Claude Seat Utilization Rating

Reads a Claude members-analytics CSV export, appends a `Rating` word and a `Score` number,
writes a new CSV. That is the entire job.

## Scope

**CSV in, CSV out.** This skill touches nothing else.

**Do not modify `claude-rollout.xlsx`.** Programmatic edits to that workbook are out of
scope. It is a live multi-user file with a chart, an Excel Table, comments and web
extension task panes, and writing to it has already caused a corruption repair that cost
its add-in panes. If the rating needs to land in the workbook, hand the rated CSV over and
let a person paste or XLOOKUP it in.

## Command

    python3 ~/.claude/skills/claude-usage-rating/scripts/rate.py

Pure standard library, no venv, no dependencies.

| Invocation | Effect |
| --- | --- |
| `rate.py` | newest `members-analytics-*.csv` in `~/Downloads` |
| `rate.py <path>` | a specific export |
| `rate.py <path> -o <out>` | choose the output path |
| `rate.py <path> --surface` | also add a `Primary Surface` column |
| `rate.py <path> --days N` | window length, if the filename has no date range |

Output defaults to `<input>-rated.csv` beside the input. The input is never modified. Every
original column and value passes through untouched; only the new columns are appended.
Re-running on an already-rated file replaces them rather than duplicating them, and the
auto-pick skips previously rated files.

## Rating, the word grouping

| Rating | 90-day definition | Typical score | Implication |
| --- | --- | --- | --- |
| Deep | 40+ active days and 300+ interactions | 53-97 | Full value. No intervention. |
| Steady | 20+ active days and 100+ interactions | 26-58 | Real habitual use. No intervention. |
| Occasional | Real but sporadic use below that | 1-30 | The open question. One conversation each. |
| Dormant | Zero interactions in the window | 0 | Reclaim. |

Interactions are `Messages + Cowork Messages + Code sessions`.

## Score, the number

`Score` is a 0-100 utilization index, half consistency and half intensity:

    50% x (active days / window days)
    50% x log1p(interactions per day) / log1p(15)

Both halves are absolute, not ranked against the current export, so the number is
comparable month to month. Intensity is log-scaled against a heavy-use reference of 15
interactions per day, roughly the 90th percentile, so one outlier does not flatten
everyone else. Nobody hits 100.

The score exists to rank **within** a group, which the word alone cannot do. It is built
from the same two inputs as the rating, so the two agree: on the 90-day baseline the bands
barely overlap, with only 5 of 145 members scoring above the floor of the band above them.
Sorting by `Score` descending also orders the groups correctly, so no separate tier number
is needed.

A score is not a performance number and must never be presented as one. It says how much
of the licence a person is using, not how well they are doing their job.

Thresholds are stored as rates, so the 30-day and 90-day exports are judged on the same
standard: Deep needs 40 active days at 90 days, 13 at 30 days. Window length is read from
the filename date range. The script prints the exact thresholds it used every run.

The cutoffs are round and explainable on purpose, because they get defended out loud in a
meeting. They are frozen so month-over-month movement is real rather than an artifact of
re-fitting. Change them only deliberately, and say so.

## The framing that must not drift

**A coaching instrument, not a surveillance scorecard.** If it reads as the latter,
adoption stalls and the savings never materialise.

**Chat-only is a legitimate way to use the licence.** Roughly 70% of members work that way,
including the single heaviest user in the company. Cowork and Claude Code are headroom for
people who want more, not a target everyone must reach. The rating never rewards surface
count, which is why `Primary Surface` is optional and purely descriptive.

**`Occasional` is not a synonym for waste.** For some roles sporadic use is the correct
amount of use. The rating says who to ask, not who is failing.

**The licence decision is made entirely by the Dormant bucket.** Everything above that line
is about where optional headroom is worth offering.

## Caveats to state before anyone quotes a number

- Members near a cutoff could sit either side. 39 active days is not meaningfully
  different from 40. A rating is a routing hint, not a verdict on a person.
- `Days Active` is not usage. Members log active days with zero messages, which is why the
  rating gates on interactions rather than days alone.
- `Estimated Spend` is not a value signal. It tracks Code usage and is non-zero for only
  about a quarter of members. Use billed overage for anything about cost.
- No token columns exist on the Team tier, so nothing here measures conversation depth.
- Individual analytics defaulted on 2026-07-11. Members can likely already see their own
  figures in Settings > Usage. Confirm before discussing anyone's utilization.
