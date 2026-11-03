---
name: it-scorecard
description: >-
  Adds a point-in-time slide to the IT Planning Scorecard deck. Clones the
  last slide, stamps today's date, and swaps in a fresh Tableau Roadmap
  render. Validates in PowerPoint before deploying. Run at the start of a
  month.
allowed-tools:
  - Read
  - AskUserQuestion
  - mcp__claude_ai_Tableau__get-view-image
  - Bash(/Users/jjduqu/.venvs/ai-scorecard/bin/python -I
    /Users/jjduqu/.claude/skills/it-scorecard/scripts/build_slide.py:*)
  - Bash(/Users/jjduqu/.claude/skills/it-scorecard/scripts/deploy.sh:*)
  - Bash(/Users/jjduqu/.claude/skills/ai-scorecard/scripts/ensure_env.sh:*)
---

# IT Planning Scorecard Update

Adds a new slide to the IT Planning Scorecard deck. Each slide is a snapshot
from the day it is made, not a month. Jared runs it at the start of a month.

The mechanics live in `scripts/` next to this file. Run those as single
plain commands, never chained (compound operators trigger permission prompts).

---

## Files

- **Deck:**
  `/Users/jjduqu/Library/CloudStorage/OneDrive-SharedLibraries-PADNOS/Information Solutions - General/IT Planning Scorecard.pptx`
  (public: Information Solutions General channel)
- **Roadmap view:** Tableau `Freshservice Project Dashboard` / `Roadmap`,
  view id `31ed9b35-85a6-48a8-8fbb-c98eecd30ee0`
- **venv:** shared with ai-scorecard, `~/.venvs/ai-scorecard` (python-pptx)

---

## Workflow

### 1. Environment and last slide

```bash
/Users/jjduqu/.claude/skills/ai-scorecard/scripts/ensure_env.sh
/Users/jjduqu/.venvs/ai-scorecard/bin/python -I /Users/jjduqu/.claude/skills/it-scorecard/scripts/build_slide.py peek
```

`peek` prints the last slide. Its date label sets the movement window
(days since that update). Its bullets show the house style.

**Add vs update:** if the last slide's label is already today, use
`update`. Otherwise `add`.

### 2. Render the Roadmap

Call `mcp__claude_ai_Tableau__get-view-image` with the view id above and no
width/height (the dashboard has a fixed 2200x2500 size). The result names
the saved PNG path (`source: .../tool-results/...png`). Use it as `roadmap`.

### 3. Pull project data

Use the `/fs-status` queries in `~/.claude/commands/fs-status.md`, with the
connection and data model rules there. Run them for **IS26 and OPS26** (the
Roadmap shows both; use next year's keys in January). Extract the SQL
blocks to files in the scratchpad, swap `<PROJECT>` and `<DAYS>`, run:

- Query 1: rock rollup (rock status, open/closed counts)
- Query 2: current sprint by rock
- Query 4: movement since the last slide (`<DAYS>` from step 1)

For single-task detail, `/fs-project <key>`.

### 4. Draft title and bullets, then confirm

**Top Goals title:** line 0 is `Top Goals Q<n> <year>: ` (quarter from
today's date), then one line per goal. Goals are Jared's call: propose from
the rock rollup (open rocks with sprint activity) and the previous title,
then ask (AskUserQuestion with a preview).

**Status bullets:** 7-8 lines, 16pt, box is 5.24x3.06 in (about 11
wrapped lines of ~50 chars). One line per rock, rock name first. Facts from
movement and the current sprint only: shipped (CLOSED), in UAT, next (Open
or In Progress in the current sprint). Never invent status, numbers, or
risk. Lines that are not in the data (e.g. bold `RIMAS Performance`) are
Jared's: carry them over. Skip work with no rock goal unless Jared asks.
Name what was left out when asking for confirmation.

Never describe a past planned end date as late; dates drift by habit.

### 5. Build the slide on a working copy

Write a spec JSON to the scratchpad (keys in the script docstring):

```json
{"workdir": "<scratchpad>", "mode": "add", "roadmap": "<png>",
 "title": ["Top Goals Q4 2026: ", "AI-RPA", "..."],
 "bullets": [["AI-RPA: ...", false], ["RIMAS Performance", true]]}
```

```bash
/Users/jjduqu/.venvs/ai-scorecard/bin/python -I /Users/jjduqu/.claude/skills/it-scorecard/scripts/build_slide.py <spec.json>
```

`null` for `title`, `bullets`, or `roadmap` keeps what the slide has. The
script backs up the deck and prints a dump: check every box.

### 6. Validate and deploy

```bash
/Users/jjduqu/.claude/skills/it-scorecard/scripts/deploy.sh <scratchpad> validate
/Users/jjduqu/.claude/skills/it-scorecard/scripts/deploy.sh <scratchpad>
```

deploy.sh closes the open deck **without saving**. It refuses to deploy if
the deck changed after the build copied it; then rebuild. If the deck is
open, confirm with Jared that his edits are saved before deploying.

### 7. Report back

- Slide number, date label, title, and bullets
- What was left out of the bullets
- Backup path (`<scratchpad>/it-scorecard-backup.pptx`)

---

## Slide Layout Reference

Shape ids are stable because each slide is a clone of the previous one.

| shape_id | Content |
|----------|---------|
| 4 | Top Goals title: heading paragraph, then a numbered list |
| 5 | Date label: `2026 Plan – Nov 3 2026 Update` |
| 10 | Roadmap picture (crop to chart area, keeps height and left edge) |
| 3 | Status bullets |

If `build_slide.py` asserts on a missing shape id or on the render size,
the layout or the dashboard changed: tell Jared, do not guess.

---

## Notes

- Never hand-edit package XML/rels at the zip level and never use
  PowerPoint's AppleScript `duplicate slide`. The clone in `build_slide.py`
  is the only safe path (learned on ai-scorecard 2026-07).
- PowerPoint is sandboxed: AppleScript "save as PNG" to a scratchpad path
  writes nothing. There is no slide render check; Jared eyeballs the deck.
