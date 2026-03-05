---
name: meeting-review
description: Processes meeting transcripts from the meeting inbox into a personal weekly meeting log. Summarizes each meeting, extracts action items, and archives the transcripts. Use when processing Krisp meeting transcripts for the week.
allowed-tools: Read, Glob, Write, Bash, Edit
---

# Meeting Review

This command processes raw Krisp meeting transcripts into a personal weekly meeting log.
It is private and separate from the GTD weekly review.

---

## What This Command Does

1. Reads general transcripts from `0-inbox/meeting/` and 1:1 transcripts from `0-inbox/meeting/1on1/`
2. Writes a personal meeting log to `2-areas/reviews/weekly/`
3. For each 1:1, appends an entry to the person's `1on1-log.md` in `2-areas/management/team/`
4. Archives all transcripts to `4-archive/meeting/` with a week prefix

---

## Instructions for Claude

### 1. Determine the Week

```bash
date +%Y-W%V
```

The output file will be `2-areas/reviews/weekly/YYYY-WXX-meetings.md` (e.g., `2026-W09-meetings.md`).

### 2. Find Transcript Files

```bash
ls 0-inbox/meeting/
ls 0-inbox/meeting/1on1/
```

Process everything present — there is no date filter. Use file creation date as the meeting
date proxy when it is not obvious from the filename or content.

Treat the two folders as separate streams:
- `0-inbox/meeting/` → general meetings
- `0-inbox/meeting/1on1/` → 1:1s (routed to person folders in addition to the weekly log)

### 3. Read and Summarize Each Transcript

**Speaker context:** The user is always `Jared Duquette` in the transcripts. Focus on what
he said, decided, and committed to. Other speakers may be named or labeled `Speaker N`.

**Per meeting, capture:**
- What the meeting was actually about (not incidental side conversations)
- Decisions made or confirmed
- Anything Jared committed to following up on
- Anything surprising or worth remembering

**Tone:** Honest, personal, informal. This is a private memory aid, not a team document.

**Length:** 2–5 lines per meeting. If nothing happened worth noting, one line is fine.

**Collapse:** Multiple short sessions with the same person on the same topic → one entry.

### 4. Write the Meeting Log

Output: `2-areas/reviews/weekly/YYYY-WXX-meetings.md`

```md
# Week XX Meeting Log — YYYY-MM-DD to YYYY-MM-DD

---

### [Meeting Name] ([Day, Mon DD])
[2-5 lines of honest notes — what happened, decisions, anything worth remembering]
`YYYY-WXX-[original-filename]`

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
- Filename reference as inline code at the bottom of each entry
- Action items consolidated at the bottom only — not repeated inside meeting notes
- 120 character line length maximum
- 1:1s appear in the weekly log like any other meeting — no special section needed

### 5. Route 1:1s to Person Folders

For each transcript from `0-inbox/meeting/1on1/`:

**Identify the other participant** from the transcript content. Ignore generic labels like
`Speaker 1` — look for a real name.

**Find their team folder:**

```bash
ls 2-areas/management/team/
```

Match the participant's full name to the closest folder name (e.g., `Connor Jabin` →
`connor-j`, `Jeff Wood` → `jeff-w`). Folder names follow `firstname-lastinitial` convention.

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

3–5 bullets max. Topics only — no narrative, no filler. If Jared committed to something,
note it as "Follow-up: [item]".

**If no folder match is found:** still include the 1:1 in the weekly meeting log, and add a
note at the end of the report: "Could not route [Name] — no matching team folder."

### 6. Archive Transcripts

```bash
mkdir -p 4-archive/meeting
mkdir -p 4-archive/meeting/1on1
```

Move each file with the week prefix. Check for conflicts first:

```bash
# if 4-archive/meeting/YYYY-WXX-filename.txt already exists,
# append datetime: YYYY-WXX-filename-YYYYMMDD-HHMMSS.txt
mv 0-inbox/meeting/filename.txt 4-archive/meeting/YYYY-WXX-filename.txt
mv 0-inbox/meeting/1on1/filename.txt 4-archive/meeting/1on1/YYYY-WXX-filename.txt
```

Confirm all moves completed successfully.

### 7. Report Back

- File location of the meeting log
- How many general transcripts were processed
- How many 1:1 transcripts were processed and where they were routed
- Any transcripts that could not be routed (name not matched)
- Remind the user to transfer action items to Fresh
