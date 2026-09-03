---
name: meeting-review
description: Pulls the week's meetings from the Krisp MCP into a personal weekly meeting log. Summarizes each meeting, extracts action items, and routes 1:1s to person folders. Use when conducting the weekly review or checking meetings for the week.
allowed-tools: Read, Write, Bash, Edit, mcp__krisp__search_meetings, mcp__krisp__get_multiple_documents
---

# Meeting Review

This command pulls the week's meetings straight from Krisp (via MCP) into a
personal weekly meeting log. It is private and separate from the GTD weekly
review.

---

## What This Command Does

1. Queries Krisp for meetings since last Friday
2. Writes a personal meeting log to `2-areas/reviews/weekly/`
3. For each 1:1, appends an entry to the person's `1on1-log.md` in
   `2-areas/management/team/`

---

## Instructions for Claude

### 1. Determine the Week and Query Window

```bash
date +%Y-W%V
```

Output file: `2-areas/reviews/weekly/YYYY-WXX-meetings.md` (e.g.
`2026-W09-meetings.md`).

Find the most recent Friday before today (same convention as
`/shipped-this-week`) and use it as the query window start, formatted
`YYYY-MM-DD`.

### 2. Pull Meetings from Krisp

Call `mcp__krisp__search_meetings` with `after: <friday_date>`, `limit: 50`,
and:

```
fields: ["name", "date", "attendees", "detailed_summary", "key_points",
         "action_items", "has_summary"]
```

If no meetings are returned, stop here and report "No meetings found since
<friday_date>" — do not create a log file.

### 3. Classify Each Meeting

A meeting is a **1:1** if its title starts with `1:1` (case-insensitive,
allowing separators like `1:1 |`, `1:1:`, `1-on-1`), or it has exactly two
named attendees. Everything else is a **general meeting**.

### 4. Summarize Each Meeting

**Speaker context:** The user is always `Jared Duquette`. Focus on what he
said, decided, and committed to. Other attendees may be named or labeled
`Speaker N`.

Use the `detailed_summary`, `key_points`, and `action_items` Krisp already
returned. If `has_summary` is false, or the notes are too thin to say
anything useful, fetch the full transcript for that one meeting via
`mcp__krisp__get_multiple_documents` (`include: ["transcript"]`) and
summarize from it directly.

**Per meeting, capture:**
- What the meeting was actually about (not incidental side conversations)
- Decisions made or confirmed
- Anything Jared committed to following up on
- Anything surprising or worth remembering

**Tone:** Honest, personal, informal. This is a private memory aid, not a
team document.

**Length:** 2–5 lines per meeting. If nothing happened worth noting, one
line is fine.

**Collapse:** Multiple short sessions with the same person on the same
topic → one entry.

### 5. Write the Meeting Log

Output: `2-areas/reviews/weekly/YYYY-WXX-meetings.md`

```md
# Week XX Meeting Log — YYYY-MM-DD to YYYY-MM-DD

---

### [Meeting Name] ([Day, Mon DD])
[2-5 lines of honest notes — what happened, decisions, anything worth remembering]

---

### [Next Meeting] ([Day, Mon DD])
...

---

## Action Items

- [ ] Item
- [ ] Item
```

**Rules:**
- `---` separator between each meeting entry
- Action items consolidated at the bottom only — not repeated inside
  meeting notes
- 120 character line length maximum
- 1:1s appear in the weekly log like any other meeting — no special
  section needed

### 6. Route 1:1s to Person Folders

For each meeting classified as a 1:1:

**Identify the other participant** from the `attendees` field, excluding
Jared Duquette. If attendees is ambiguous (bot names, generic labels), fall
back to the summary/transcript text to find a real name.

**Find their team folder:**

```bash
ls 2-areas/management/team/
```

Match the participant's full name to the closest folder name (e.g.,
`Connor Jabin` → `connor-j`, `Jeff Wood` → `jeff-w`). Folder names follow
`firstname-lastinitial` convention.

**Append to their 1:1 log:**

Target file: `2-areas/management/team/[folder]/1on1-log.md`

If the file does not exist, create it with this header:

```md
# 1:1 Log — [Full Name]

---
```

Append a new entry:

```md
### YYYY-MM-DD

- [topic or theme discussed]
- [topic or theme discussed]
- [any follow-up or commitment]
```

3–5 bullets max. Topics only — no narrative, no filler. If Jared committed
to something, note it as "Follow-up: [item]".

**If no folder match is found:** still include the 1:1 in the weekly
meeting log, and add a note at the end of the report: "Could not route
[Name] — no matching team folder."

### 7. Report Back

- File location of the meeting log
- How many general meetings and how many 1:1s were processed
- Any 1:1s that could not be routed (name not matched)
- Remind the user to transfer action items to Fresh
