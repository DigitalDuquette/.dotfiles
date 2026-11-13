---
name: ai-coe-align
description: >-
  Weekly roll-up of the department AI@PADNOS trackers into the master
  AI @ PADNOS workbook. Builds a prompt for Claude in Excel that updates
  changed hours and adds newly completed rows to rpa_ai, and copies it to the
  clipboard. Use for the weekly AI CoE alignment, "align the AI trackers", or
  before the AI Scorecard.
---

# AI CoE weekly alignment

Department trackers feed the master `rpa_ai` table. This skill reads them,
finds what changed, and copies a prompt to the clipboard. Jared opens the
master workbook in Excel, opens Claude in Excel, and pastes it. Claude in
Excel edits the live workbook.

## Files

Both paths are under `~/Library/CloudStorage/` and are hard-coded in
`recon.py`.

- **Department trackers (read only):**
  `OneDrive-PADNOS-InformationSolutions-ai-coe/AI@PADNOS/AI@PADNOS - <Dept>.xlsx`
- **Master (read only here):**
  `OneDrive-PADNOS-InformationSolutions-aisc/Artificial Intelligence/`
  `AI @ PADNOS.xlsx`, sheet `rpa_ai`, table `tbl_rpa_ai`
- **Scripts:** `~/.claude/skills/ai-coe-align/scripts/`
- **Venv:** reuses `~/.venvs/ai-scorecard` (openpyxl). Create it with
  `~/.claude/skills/ai-scorecard/scripts/ensure_env.sh` if it is missing.

---

## Rules

The recon reports only two things:

1. **Add**: a department row with Status `Production` or
   `Production - Recent` that is not in master. It goes in as
   `Production - Recent`.
2. **Update hours**: a matched row whose Hours Saved Per Month differs from
   master Hours per Month. Only the hours change.

It ignores everything else on purpose: status drift, backlog ideas, and rows
that exist only in master.

- **Matching:** Freshservice Ticket first, then Project Code, then the exact
  Project Name within the same Business Area. Master has duplicate codes
  (IS26-58, SR-143141), so an hours update fires only when no row with that
  code has the department's hours.
- **AI column on adds:** `Skill` when Tool mentions Claude, otherwise blank.
  This is a default, not a fact. The AI Scorecard flags blanks.
- **Status values:** the master `dev_status` list. Departments may use
  `In Progress`; treat it as `Development`.

---

## Workflow

### 1. Run

```bash
~/.venvs/ai-scorecard/bin/python -I ~/.claude/skills/ai-coe-align/scripts/recon.py
```

The prompt goes to the clipboard and stdout. stderr shows the counts and any
department skipped because it has no table with a column named `Status`.

### 2. Report

Tell Jared the counts, list the hour updates, and summarize the adds by
department. Name any skipped department and why.

### 3. Hand off

Jared opens the master in Excel, opens Claude in Excel, and pastes. Claude in
Excel reports rows updated, rows added, and anything skipped.

---

## Never

- **Never write to any workbook from here, not even with openpyxl.**
  Rewriting a department workbook with openpyxl gave a file Excel would not
  open (2026-11-12). Edits to synced files also lose to Excel when the file
  is open with AutoSave: Excel overwrites them or renames columns
  (`Status_old`).
- **Never drive Excel with AppleScript.** It opens windows and repair prompts
  on Jared's screen.

---

## Onboarding a department with a legacy layout

Finance and FP&A had their own trackers. `scripts/template_writer.py` writes
rows to a new, clean workbook in the template layout. Jared then uses Move or
Copy to put that sheet into the department's workbook.
`scripts/fpa_to_template.py` is the worked example.

- **Template columns:** Project Code, Freshservice Ticket, Status, Project
  Name, Business Area, Owner, Tool, Hours Saved Per Month, Labor $, Savings
  per Year (table formula), Comments
- **Codes:** IS-, IS26- and SR- codes are Freshservice tickets. They go in
  Freshservice Ticket. The row gets the next department code
  (`FIN-65`, `FPA-42`).
- **Status:** in use means Production. In process and not in use means
  Development. Not started means Backlog, or Open if it is a stated next
  priority.
- **Hours:** count them only for Production. For other rows, put the
  estimate in Comments as "Est. N hrs/month".

---

## Related

- `ai-coe-savings-log` (claude.ai org skill) adds department rows. It still
  lists the old column order without Status, so it needs updating to the
  template above.
- Run this skill before `ai-scorecard`, which reads `rpa_ai`.
