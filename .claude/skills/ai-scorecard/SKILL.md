---
name: ai-scorecard
description: Adds or refreshes the latest monthly slide in the AI Scorecard deck. Computes KPIs from the AI @ PADNOS workbook (live snapshot, current month by default), clones or updates the last slide, validates in PowerPoint before deploying.
allowed-tools: Read, Glob, Write, Edit, AskUserQuestion, Bash(/Users/jjduqu/.venvs/ai-scorecard/bin/python:*), Bash(~/.venvs/ai-scorecard/bin/python:*), Bash(/Users/jjduqu/.claude/skills/ai-scorecard/scripts/deploy.sh:*), Bash(~/.claude/skills/ai-scorecard/scripts/deploy.sh:*), Bash(/Users/jjduqu/.claude/skills/ai-scorecard/scripts/ensure_env.sh:*), Bash(~/.claude/skills/ai-scorecard/scripts/ensure_env.sh:*)
---

# AI Scorecard Monthly Update

Adds or refreshes the month slide in the leadership AI Scorecard deck,
computing KPIs directly from the AI @ PADNOS workbook (same numbers the
Tableau RPAAIAudit/LeadershipKPIs dashboard shows).

The mechanics live in `scripts/` next to this file; run those instead of
writing ad-hoc python or osascript. The three commands below are the whole
pipeline and are pre-approved in `allowed-tools`, so a routine run prompts
for nothing.

---

## Files

- **Deck:**
  `/Users/jjduqu/Library/CloudStorage/OneDrive-PADNOS/Information Solutions-Artificial Intelligence - Documents/Artificial Intelligence/scorecard/AI Scorecard.pptx`
- **Source workbook:**
  `/Users/jjduqu/Library/CloudStorage/OneDrive-PADNOS/Information Solutions-Artificial Intelligence - Documents/Artificial Intelligence/AI @ PADNOS.xlsx`
  (sheet `rpa_ai`, table `tbl_rpa_ai`)
- **Scripts:** `/Users/jjduqu/.claude/skills/ai-scorecard/scripts/`
- **Dashboard (reference only):**
  https://prod-useast-b.online.tableau.com/#/site/padnos/views/RPAAIAudit/LeadershipKPIs

---

## KPI Definitions

Validated against Tableau 2026-07; AI grouping added 2026-07-27. Encoded in
`scripts/compute.py`; the list here is the human-readable contract.

All from sheet `rpa_ai`, columns `Project Code`, `AI`, `Status`,
`Hours per Month`. Skip fully empty rows. Round hours to nearest integer.

**Live rows** = Status in {`Production`, `Production - Recent`}.

- **Hours Saved Monthly** = sum of `Hours per Month` across all live rows
- Live rows split into three counts by the `AI` column, mirroring the
  Tableau `AI (group)` field:
  - **Agents** = `AI` in {`Agent`, `AI-RPA`, `Dashboard`, `RPA`}
  - **Assisted** = `AI` in {`MCP`, `Skill`}
  - **Support** = `AI` in {`Software`}
  - An `AI` value outside these lists (or blank) means the grouping
    drifted: flag it to the user instead of guessing a bucket
    (`compute.py` reports these as `unmapped_ai`).
- **Backlog Opportunity Agents** = distinct count of `Project Code` for
  rows with Status in {`Backlog`, `Blocked`, `Parking Lot`, `Scoping`} or
  blank Status. Distinct matters: duplicate codes collapse to one.
- **Backlog Est. Hours** = sum of `Hours per Month` for those rows
  (row-level, not distinct)
- `Production - Dead` counts toward nothing
- `Development`, `Open`, `UAT` count toward no KPI (narrative only)

---

## Narrative Sections

- **RECENTLY COMPLETED** = Status `Production - Recent`
- **CURRENT PRIORITIES** = Status `UAT`, `Development`, `Scoping`
- **UP NEXT** = Status `Open`

Bullet format: bold `Business Area` + `: short description` drawn from
Project Name / Description columns. Terse, no invented content.

- Blank `Business Area`: leave the bold prefix empty and start the bullet
  with the description alone (no colon). Never invent an area.
- When one area has many rows at once (e.g., 7 FP&A skills went live
  2026-07), consolidate them into a single bullet for that area listing
  the items, so the box stays balanced against the others.

---

## Workflow

### 1. Environment

```bash
~/.claude/skills/ai-scorecard/scripts/ensure_env.sh
```

Reuses the venv, creating it only if missing. Do not inline the venv check
as a raw shell one-liner: compound operators (`||`, `&&`) always trigger a
permission prompt no matter what is allowlisted. The same applies to every
step here: run the scripts as single plain commands, never chained.

### 2. Compute

```bash
~/.venvs/ai-scorecard/bin/python ~/.claude/skills/ai-scorecard/scripts/compute.py
```

Prints JSON: fresh KPIs, `unmapped_ai`, narrative candidate rows, and what
the deck's last slide currently shows (for the anomaly check).

The workbook is a live snapshot; numbers are always "as of now" and the
month label just names the slide. Target month = current month unless the
user says otherwise (e.g., `/ai-scorecard close out July` run on August 5).

**Add vs update:** if the deck's last slide is already the target month,
update it in place. Only add a new slide when the target month has none.
Re-running mid-month is a refresh, not a duplicate.

### 3. Confirm gate (anomaly-only, don't prompt on routine refreshes)

Routine runs proceed without asking; the numbers are deterministic and get
reported at the end. Stop and confirm (AskUserQuestion) only when:

- `unmapped_ai` is non-empty (grouping drifted), or
- any KPI moved more than ~15% from what the slide currently shows, or
- the run rebuilds narrative boxes: show the drafted bullets (new-month
  slides always; update-in-place only when the user asked for a narrative
  refresh). The user may reword bullets or drop items.

If a confirmation round trip happened, re-run `compute.py` before
building: the workbook is live and the user may have edited it
mid-conversation (happened 2026-07-27; the KPIs changed between reads).

### 4. Build the slide on a working copy

Write a spec JSON to the session scratchpad, then:

```bash
~/.venvs/ai-scorecard/bin/python ~/.claude/skills/ai-scorecard/scripts/update_slide.py <spec.json>
```

Spec shape (see the script docstring): `workdir` (session scratchpad),
`mode` (`update`/`add`), `month_label`, `kpis`, and `sections` where each
section is a list of `[area, description]` pairs or `null` to leave that
box untouched. The script backs up the deck, edits only the working copy,
and prints a full text dump of the slide: read it and check every box
before deploying.

### 5. Validate and deploy

```bash
~/.claude/skills/ai-scorecard/scripts/deploy.sh <workdir>            # validate + deploy
~/.claude/skills/ai-scorecard/scripts/deploy.sh <workdir> validate   # validate only
```

Opens the working copy in PowerPoint first (a corrupt package demands
"repair" on the scratch file, never the real deck), closes the deck if the
user has it open (avoids OneDrive AutoSave conflicts), copies the working
file over it, and reopens at the last slide for review.

### 6. Report back

- The six KPIs on the slide and the month label
- Which projects landed in each narrative section (if rebuilt)
- Where the backup copy lives (`<workdir>/scorecard-backup.pptx`)
- Suggest a quick eyeball of the Tableau dashboard as a cross-check

---

## Slide Layout Reference

Shape IDs are stable because each slide is a clone of the previous one.
`update_slide.py` knows this table; it is here for debugging drift.

| shape_id | Content |
|----------|---------|
| 3 | Month label |
| 4 | KPI box: 9 paragraphs, hours (44pt) + Agents/Assisted/Support pairs (32pt/20pt) |
| 5 | Backlog box: agents + est. hours |
| 28 | Recently Completed bullets |
| 29 | Current Priorities bullets |
| 30 | Up Next bullets |

The KPI box auto-fits (SHAPE_TO_FIT_TEXT) and must not grow past the
Backlog box at top = 5.36 in; the sizes above fit. If `compute.py` returns
nulls in `slide`, the layout drifted: tell the user before proceeding.

---

## Notes

- The Tableau dashboard reads the same workbook; if numbers disagree, the
  dashboard's group fields changed. Definitions reconciled 2026-07 against
  `Status (group)` and 2026-07-27 against `AI (group)`.
- New slides intentionally carry no speaker notes.
- `Hours per Month` has blanks and floats; non-numeric counts as 0, round
  sums only.
- The workbook is read-only in this workflow. Never write to the xlsx.
- Never hand-edit package XML/rels at the zip level and never use
  PowerPoint's AppleScript `duplicate slide`; both corrupt or fail. The
  cloning in `update_slide.py` is the only safe path (learned 2026-07).
