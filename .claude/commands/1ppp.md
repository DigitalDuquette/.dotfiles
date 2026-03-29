---
description: Populate quarterly 1-pager from Freshservice project data
---

Review and update personal 1-pager workbook using Freshservice
project task data. This is a conversation — ask what the user
wants to do, don't assume.

**User context:** `$ARGUMENTS`

**Start by asking what the user needs:**
- Which quarter are we working on?
- Full quarter review, single month update, or just reviewing
  what's there?
- Any context they want to add manually (things not in the
  data)?

Then proceed based on the conversation.

**Data retrieval:**

1. **Run both queries:**
   - Source `.env` from the SQL-Query-Library working directory
   - Current state query (rock goals and tasks):
     ```
     source .env && sqlcmd -S "$SQLCMD_SERVER" \
       -U "$SQLCMD_USERNAME" -P "$SQLCMD_PASSWORD" \
       -d "$SQLCMD_DATABASE" -s "|" -W \
       -i Business-Application/Freshservice/one_pager_by_assignee.sql
     ```
   - Snapshot history query (status transitions over time):
     ```
     source .env && sqlcmd -S "$SQLCMD_SERVER" \
       -U "$SQLCMD_USERNAME" -P "$SQLCMD_PASSWORD" \
       -d "$SQLCMD_DATABASE" -s "|" -W \
       -i Business-Application/Freshservice/one_pager_by_assignee_history.sql
     ```
   - If either query fails, stop and troubleshoot — do not
     generate content from memory
   - Use the current-state query for the rock list and sprint
     assignments
   - Use the snapshot query for accurate month attribution —
     when tasks actually changed status, not just what sprint
     they're in

2. **Read the current workbook:**
   - Path: `~/Library/CloudStorage/OneDrive-PADNOS/Information Technology - Information Solutions/Jared 1Pager.xlsx`
   - Use `/tmp/xlsx-reader/bin/python3` with openpyxl
   - If the venv doesn't exist, create it at `/tmp/xlsx-reader`
     and `pip install openpyxl`
   - Read the target quarter sheet AND any existing values
     already populated — preserve what's there unless the user
     says to replace it

**Sprint-to-month mapping:**
- Sprint naming pattern: `Month Sprint YY.M.1`
  (e.g., "March Sprint 26.1.1")
- Parse the month name from the sprint to bucket tasks
- BUT prefer snapshot transitions for month attribution when
  available — a task sprinted to March that actually started
  in January should show activity in January
- Tasks with no sprint: note them separately as unsprinted
- Group tasks by `rock_goal` (the task_list column)

**When presenting updates:**
- Show what you'd write for each cell, compared against what's
  already there (if anything)
- For single-month updates, only propose changes to that
  month's column — leave other months untouched
- Flag anything that looks off (empty rocks, all backlog,
  items from outside the quarter)
- Always ask before writing. The user may want to adjust
  wording, add context, or skip certain rocks

**Workbook structure:**
- Quarter sheet names: `Q1 26`, `Q2 26`, etc.
- Row 1: Name and quarter label (G1)
- Row 2: Last Updated date (E2)
- Rows 3-6: KPIs - Company (MANUAL — do not touch)
- Rows 7-10: Personal Accountability Numbers (MANUAL — do not
  touch)
- Row 11: Quarterly Rocks header row
- Rows 12-19: Rock goal data
  - Column D: Rock name
  - Column E: Strategy
  - Column F/G/H: Monthly updates (month 1/2/3 of quarter)
- Rows 20+: Personal tracking / instructions (do not touch)

**When writing to the workbook:**
- Only write cells the user has confirmed
- Update E2 (Last Updated) to today's date
- Read existing values first — if a cell already has content
  and the user didn't ask to change it, leave it alone
- Save the file after writing

**Manager context:**
- The user is a manager. Rocks are assigned to them but child
  tasks may be assigned to team members
- Monthly summaries should name who did the work, briefly:
  "Ernie: Deduction Detection closed"
- This workbook is a rubber stamp — keep updates short and
  factual. A few words per task, not sentences. Match the
  terse style in existing quarter sheets.
- Closed tasks = name + "(closed)" or just state the outcome
- In Progress = brief what's happening
- Blocked/Waiting = one-liner on what's blocking
- Rolled = note it moved, don't belabor it

**Writing style examples (from Q4 25 sheet):**
- Good: "Pipeline live"
- Good: "Dev, reviewed, in prod"
- Good: "Late Nov kickoff."
- Too long: "Data pipeline successfully delivered to partners
  and engagement is wrapping up with final handoff"

**CRITICAL RULES:**
- NEVER fabricate data. Every value must come from the query
  results or from what the user tells you in conversation
- NEVER write to the workbook without showing the draft first
- NEVER touch KPI or Personal Accountability sections
- If a rock has no tasks in a month, use `-` not empty
- Keep it SHORT. This is a checkbox exercise, not a report.