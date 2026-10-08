---
name: ai-idea
description: >-
  Turn an incoming AI/automation idea (email, Teams message, Loom
  transcript, pasted text) into a Freshservice card under the current
  year's AI rock goal, plus a row on the clipboard for the rpa_ai table
  in the AI @ PADNOS workbook. Use when an AI idea or request comes in.
argument-hint: <email subject, Teams link, or pasted idea>
allowed-tools: >-
  Read, Write, AskUserQuestion,
  Bash(~/.claude/skills/ai-idea/scripts/context.sh:*),
  Bash(~/.claude/skills/ai-idea/scripts/clip_row.py:*),
  Bash(~/.claude/skills/fs-project/scripts/lookup-task.sh:*),
  Bash(~/.claude/skills/fs-project/scripts/create-task.sh:*),
  Bash(~/.claude/skills/fs-project/scripts/update-task.sh:*),
  Bash(~/.claude/skills/fs-project/scripts/add-note.sh:*)
---

# AI Idea Intake

**Source:** `$ARGUMENTS`

One idea in, two things out:

1. A Freshservice card under the AI rock goal.
2. A row on the clipboard, ready to paste into the `rpa_ai` table.

Card writes go through the `fs-project` scripts. Read
`~/.claude/skills/fs-project/SKILL.md` "Writing tasks" for the API rules.

---

## Hard rules

- **Never write to the workbook.** `AI @ PADNOS.xlsx` is co-authored on
  OneDrive and has conditional-formatting extensions that openpyxl drops
  on save. The user pastes the row in Excel. This skill only reads it.
- Use only facts from the source. Leave a field blank when the source
  does not say it. Do not estimate hours or dollars.
- Do not create the card until the user approves the draft.

---

## Steps

### 1. Gather the source

- Email subject: search Outlook, read the newest message in the thread
  with `read_resource`. Read the forwarded content too. That is often the
  real process detail.
- Attachments: read a charter, spec, or process document. These often
  hold sponsor, scope, out-of-scope, and KPI. Skip images and PDFs when
  the body already explains the ask.
- Teams link, Loom transcript, or pasted text: use it as given.
- Get: who asked, what they want, the current manual process, the
  business area, any stated volume or time.

### 2. Resolve context and check for duplicates

Run `~/.claude/skills/ai-idea/scripts/context.sh`. It fetches the
current year's project fresh (`IS` + two-digit year) and prints
`project_id`, rock goal, `type_id`, `status_id`, `reporter_id`,
`tasks_file`, and `card_url_base`. If it fails with "no rock goal", stop
and tell the user to create the rock goal for the new year.

Search `tasks_file` for children of `rock_id` (any status) close to the
idea. Also search the whole project for key terms: related work is not
always under the rock. Show matches. A match can mean: add a note to the
old card instead of a new card.

### 3. Draft

**Frame the general need, not the trigger.** An idea often arrives
attached to one case (one customer, one country, one form). Title and
ask describe the reusable capability. The specific case goes in the
description as the current example.

**Card title:** short noun phrase, same style as existing cards
(e.g. "Container Vision: Receiver/Shipment Fill Levels").

**Card description (HTML: `<p>` per paragraph, `<p><br></p>` between,
`<ol>`/`<ul>` for steps and scope):**

1. The ask: what the requester wants, in one or two sentences. Name the
   requester (and sponsor/owner if given).
2. The current process or scope, from the source. Keep names of systems,
   teams, folders, and triggers. Put out-of-scope and KPI here if given.
3. Context: source (email subject, date, attachments, links), and
   related cards from step 2.

**Row (columns A to K of `tbl_rpa_ai`):**

| Col | Field | Value |
|-----|-------|-------|
| A | Project Code | card key, linked to the card |
| B | o | blank |
| C | Primary | blank unless the user confirms a name |
| D | Project Name | card title |
| E | Description | one line |
| F | Business Area | see list below |
| G | AI | see list below |
| H | Status | Backlog |
| I | Hours per Month | only if the source states it |
| J | Labor $ | blank unless stated |
| K | Software Opp Cost | blank unless stated |

Business Area values in use: Finance, BeHIVE, FP&A, Admin, Sales,
Purchasing, Recycling Centers, Auto Division, NF, FE, IT, Executive, LPT,
HR, EHS, Marketing.

AI values (workbook dropdown) and their AI Scorecard group:

- AI-RPA, RPA, Dashboard: Agents
- Skill, MCP: Assisted
- Software: Support

Show the draft with AskUserQuestion. When the source does not state
Business Area or AI type, ask for them in the same call, with a
recommended option first. Options: create, edit, or note on a duplicate.

### 4. Create the card

Write the body to the scratchpad and run
`~/.claude/skills/fs-project/scripts/create-task.sh <project_id> <file>`:

```json
{"task": {"title": "...", "description": "<p>...</p>",
  "type_id": 0, "status_id": 0, "parent_id": "<rock_id>",
  "reporter_id": 0}}
```

All IDs come from step 2. No sprint, assignee, priority, or dates.
Get `display_key` from the response. Card URL = `card_url_base` +
`display_key`.

To change a card after creation, use `update-task.sh` with the task
`id` from the create response. To add a note, use `add-note.sh` (content
file holds raw HTML).

### 5. Put the row on the clipboard

Write `row.json` to the scratchpad and run
`~/.claude/skills/ai-idea/scripts/clip_row.py <row.json>`:

```json
{"key": "IS26-571", "url": "<card URL>", "name": "...",
  "description": "...", "area": "...", "ai": "...",
  "status": "Backlog", "primary": "", "hours": "", "labor": "",
  "opp_cost": ""}
```

The script escapes the text and puts HTML (with the link) and TSV on
the clipboard. If the card title or row changes later, run it again.

### 6. Report

- Card key and URL
- Row values on the clipboard
- Paste: in `rpa_ai`, select column A of the first empty row directly
  below the table, then paste. The table grows and fills L and P.
- Anything the source leaves open that affects priority (often: no
  volume or hours).
