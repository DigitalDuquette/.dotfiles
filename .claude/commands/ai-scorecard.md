---
name: ai-scorecard
description: Adds or refreshes the latest monthly slide in the AI Scorecard deck. Computes KPIs from the AI @ PADNOS workbook (live snapshot, current month by default), clones or updates the last slide, validates in PowerPoint before deploying.
allowed-tools: Read, Glob, Write, Bash, Edit, AskUserQuestion
---

# AI Scorecard Monthly Update

Adds a new month slide to the leadership AI Scorecard deck, computing KPIs directly from the
AI @ PADNOS workbook (same numbers the Tableau RPAAIAudit/LeadershipKPIs dashboard shows).

---

## Files

- **Deck:**
  `/Users/jjduqu/Library/CloudStorage/OneDrive-PADNOS/Information Solutions-Artificial Intelligence - Documents/Artificial Intelligence/scorecard/AI Scorecard.pptx`
- **Source workbook:**
  `/Users/jjduqu/Library/CloudStorage/OneDrive-PADNOS/Information Solutions-Artificial Intelligence - Documents/Artificial Intelligence/AI @ PADNOS.xlsx`
  (sheet `rpa_ai`, table `tbl_rpa_ai`)
- **Dashboard (reference only):**
  https://prod-useast-b.online.tableau.com/#/site/padnos/views/RPAAIAudit/LeadershipKPIs

---

## KPI Definitions (validated against Tableau 2026-07)

All from sheet `rpa_ai`, columns `Project Code`, `Status`, `Hours per Month`. Skip fully
empty rows. Round hours to nearest integer.

- **Agents Live** = count of rows with Status in {`Production`, `Production - Recent`}
- **Hours Saved Monthly** = sum of `Hours per Month` for those same rows
- **Backlog Opportunity Agents** = **distinct count of `Project Code`** for rows with
  Status in {`Backlog`, `Blocked`, `Parking Lot`, `Scoping`} or blank Status.
  Distinct matters: duplicate codes (e.g., two `IDS` rows) collapse to one.
- **Backlog Est. Hours** = sum of `Hours per Month` for those rows (row-level, not distinct)
- `Production - Dead` counts toward **nothing**
- `Development`, `Open`, `UAT` count toward **no KPI** (narrative sections only)

## Narrative Sections (drafted from Status, user confirms)

- **RECENTLY COMPLETED** = rows with Status `Production - Recent`
- **CURRENT PRIORITIES** = rows with Status `UAT`, `Development`, `Scoping`
- **UP NEXT** = rows with Status `Open`

Bullet format matches existing slides: bold `Business Area` + `: short description` drawn
from Project Name / Description columns. Terse, no invented content.

---

## Instructions for Claude

### 1. Environment

Use a venv (never global pip). Reuse if present:

```bash
VENV="$HOME/.venvs/ai-scorecard"
[ -x "$VENV/bin/python" ] || (python3 -m venv "$VENV" && "$VENV/bin/pip" install -q openpyxl python-pptx)
```

### 2. Compute KPIs and draft the slide content

Read `rpa_ai` with openpyxl (`data_only=True`). Compute the four KPIs per the definitions
above and list the projects for the three narrative sections.

The workbook is a live snapshot — there is no way to query it as of a past date. The
numbers are always "as of now"; the month label just names the slide.

**Target month:** the current month, unless the user says otherwise in the invocation
(e.g., running `/ai-scorecard close out July` on August 5 targets July with today's data).

**Add vs update:** if the deck's last slide is already the target month, update that slide
in place (refresh KPIs; only touch narrative boxes if the user asks). Only clone a new
slide when the target month has no slide yet. Re-running mid-month is a refresh, not a
duplicate.

### 3. Confirm with the user before touching the deck

Show: the four KPIs, the month label, add vs update-in-place, and (for a new slide) the
drafted narrative bullets. Wait for approval. The user may reword bullets or drop items.

### 4. Build on a working copy — never edit the deck in place first

```bash
SCRATCH=<session scratchpad>
cp "<deck>" "$SCRATCH/scorecard-backup.pptx"   # untouched backup
cp "<deck>" "$SCRATCH/scorecard-work.pptx"     # working copy
```

All edits (add or update-in-place) happen on the working copy; the real deck is only
replaced after the PowerPoint validation in step 6. For update-in-place, skip the cloning
below and go straight to the text edits in step 5 against the existing last slide.

Clone the last slide with python-pptx **library-native** calls. NEVER hand-edit package
XML/rels at the zip level: the monthly slides carry notesSlide and tags relationships, and
copying a rels file verbatim shares a notes part between two slides, which corrupts the
package (PowerPoint "repair" then deletes the slide). This happened 2026-07.

```python
import copy
from pptx import Presentation
from pptx.oxml.ns import qn

p = Presentation(WORK)
src = p.slides[-1]
new = p.slides.add_slide(src.slide_layout)
for shp in list(new.shapes):                      # drop layout placeholders
    shp._element.getparent().remove(shp._element)
skip = {qn('p:nvGrpSpPr'), qn('p:grpSpPr')}
for child in src.shapes._spTree:                  # copy shapes only (no notes/tags)
    if child.tag not in skip:
        new.shapes._spTree.append(copy.deepcopy(child))
rid_map = {rId: new.part.relate_to(rel.target_part, rel.reltype)
           for rId, rel in src.part.rels.items() if "image" in rel.reltype}
for el in new.shapes._spTree.iter():              # remap image refs
    for attr in (qn('r:embed'), qn('r:link')):
        if el.get(attr) in rid_map:
            el.set(attr, rid_map[el.get(attr)])
```

Sanity-check before saving: every `r:`-prefixed attribute value in the new spTree must
exist in `new.part.rels`. Abort if any dangling reference remains.

### 5. Update the new slide's text

Shape IDs are stable because each slide is a clone of the previous one:

| shape_id | Content | Edit |
|----------|---------|------|
| 3 | Month label | run text, e.g. `July 2026` |
| 4 | KPI box | paragraph 0 run 0 = hours saved; paragraph 3 run 0 = agents live |
| 5 | Backlog box | paragraph 1 run 0 = `"NN "` agents; paragraph 2 run 1 = `" NNN "` hours |
| 28 | Recently Completed | rebuild paragraphs |
| 29 | Current Priorities | rebuild paragraphs |
| 30 | Up Next | rebuild paragraphs |

If a shape_id is missing, fall back to matching shapes by their June-slide text patterns
and tell the user the layout drifted.

Narrative rebuild: deepcopy the box's first paragraph as a template (bold run + regular
run), remove all existing `a:p` elements, then append one copy per bullet with run 0 =
bold area name, run 1 = `: description`. Trim extra runs beyond the first two.

KPI/label edits are plain `run.text` assignments — never replace whole text frames (loses
per-run formatting).

### 6. Validate in PowerPoint BEFORE deploying

Open the working copy in PowerPoint itself; if the package is bad it will demand a repair
here, not on the real file:

```applescript
tell application "Microsoft PowerPoint"
    open (POSIX file "<work copy>")
    set n to count of slides of presentation "scorecard-work.pptx"
    close presentation "scorecard-work.pptx" saving no
    return n
end tell
```

Slide count must be previous + 1. Do not use `out` as an AppleScript variable name
(reserved in PowerPoint's dictionary). PowerPoint's `duplicate slide` AppleScript command
does not work (parameter error) — that is why cloning happens in python-pptx.

### 7. Deploy

The user often has the deck open in PowerPoint as a cloud/AutoSave session. Overwriting
the file underneath it causes sync conflicts. Check and close first:

```applescript
tell application "Microsoft PowerPoint" to get name of every presentation
-- if "AI Scorecard.pptx" is listed:
tell application "Microsoft PowerPoint" to close presentation "AI Scorecard.pptx" saving no
```

Then copy the working file over the deck path, reopen it in PowerPoint, and jump to the
last slide so the user can review:

```applescript
tell application "Microsoft PowerPoint"
    activate
    open (POSIX file "<deck>")
    set n to count of slides of presentation "AI Scorecard.pptx"
    go to slide (view of document window 1) number n
end tell
```

### 8. Report back

- The four KPIs on the slide and the month label
- Which projects landed in each narrative section
- Where the backup copy lives
- Suggest a quick eyeball of the Tableau dashboard as an independent cross-check

---

## Notes

- The Tableau dashboard reads the same workbook; if numbers disagree, the dashboard's
  status filters were changed. The definitions above were reconciled 2026-07 against the
  dashboard's `Status (group)` field.
- New slides intentionally carry no speaker notes (notes stay with their original slide).
- `Hours per Month` has blanks and floats; treat non-numeric as 0 and round the sums only.
- The workbook is read-only in this workflow. Never write to the xlsx.
