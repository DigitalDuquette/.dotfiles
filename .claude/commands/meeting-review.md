---
name: meeting-review
description: Processes meeting transcripts from the meetings inbox into a personal weekly meeting log. Summarizes each meeting, extracts action items, and archives the transcripts. Use when processing Krisp meeting transcripts for the week.
allowed-tools: Read, Glob, Write, Bash
---

# Meeting Review

This command processes raw Krisp meeting transcripts into a personal weekly meeting log.
It is private and separate from the GTD weekly review.

---

## What This Command Does

1. Reads all transcript files from `0-inbox/meetings/`
2. Writes a personal meeting log to `2-areas/reviews/weekly/`
3. Archives transcripts to `4-archive/meetings/` with a week prefix

---

## Instructions for Claude

### 1. Determine the Week

```bash
date +%Y-W%V
```

The output file will be `2-areas/reviews/weekly/YYYY-WXX-meetings.md` (e.g., `2026-W09-meetings.md`).

### 2. Find Transcript Files

```bash
ls 0-inbox/meetings/
```

Process everything present — there is no date filter. Use file creation date as the meeting
date proxy when it is not obvious from the filename or content.

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

### 5. Archive Transcripts

```bash
mkdir -p 4-archive/meetings
```

Move each file with the week prefix. Check for conflicts first:

```bash
# if 4-archive/meetings/YYYY-WXX-filename.txt already exists,
# append datetime: YYYY-WXX-filename-YYYYMMDD-HHMMSS.txt
mv 0-inbox/meetings/filename.txt 4-archive/meetings/YYYY-WXX-filename.txt
```

Confirm all moves completed successfully.

### 6. Report Back

- File location of the meeting log
- How many transcripts were processed and archived
- Remind the user to transfer action items to Fresh
