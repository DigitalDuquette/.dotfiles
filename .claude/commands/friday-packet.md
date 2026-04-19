---
name: friday-packet
description: Generates printable AISC meeting notes PDF for the Monday meeting packet. Expands wiki-links, strips URLs, converts to PDF, and delivers to shared OneDrive folder.
allowed-tools: Read, Glob, Write, Bash, Edit
---

# Friday Packet

Generates a self-contained, printable PDF of the upcoming Monday AISC meeting notes for the
AI steering committee. Part of the weekly Friday send.

---

## What This Skill Does

1. Reads the Monday meeting agenda from `2-areas/AI@PADNOS/aisc/meeting/`
2. Expands all `[[wiki-links]]` inline (one level deep)
3. Strips all hyperlinks — no URLs in the final output
4. Converts to PDF using `md2pdf`
5. Moves the PDF to the shared OneDrive Meeting Notes folder

---

## Instructions for Claude

### 1. Determine the Target Meeting Date

If invoked with an argument (e.g., `/friday-packet 2026-04-20`), use that date.

Otherwise, find the most recent meeting note **on or before today**. The user creates the
next week's agenda file before going into the meeting, so there will often be a future-dated
file present. Ignore it.

```bash
# List meeting files, filter to dates <= today, take the most recent
today=$(date +%Y-%m-%d)
ls 2-areas/AI@PADNOS/aisc/meeting/*.md | sort -r | while read f; do
  d=$(basename "$f" .md)
  if [[ "$d" <= "$today" ]]; then echo "$f"; break; fi
done
```

The meeting note file is:
`2-areas/AI@PADNOS/aisc/meeting/YYYY-MM-DD.md`

If no qualifying file is found, tell the user and stop.

### 2. Read the Meeting Note and All Linked Files

Read the meeting note. Then find all `[[wiki-links]]` in the document.

For each wiki-link, search the vault for the target file:

```bash
find /Users/jjduqu/Library/Mobile\ Documents/iCloud~md~obsidian/Documents/padnos \
  -name "link-name.md" -not -path "*/4-archive/*"
```

Read each linked file's content. Wiki-link resolution is one level deep — linked files do not
themselves contain wiki-links that need expanding.

### 3. Build the Expanded Document

Starting from the meeting note content:

**Expand wiki-links:**
Replace each `[[link-name]]` with the full content of the linked file. Drop the file's H1
heading if it would be redundant with the surrounding context (e.g., `[[IDS Backlog]]`
under a `## IDS` section doesn't need the `# IDS Backlog` heading repeated).

**Strip Freshservice links — keep project codes only:**
`[IS26-232](https://padnos.freshservice.com/...)` → `IS26-232`
Pattern: any markdown link where the display text is a Freshservice code
(IS-xxx, IS26-xxx, SR-xxxxx, CASE-xxxxx). Replace with just the code.

**Strip SharePoint/OneDrive links — keep display text:**
`[Link Text](https://padnos365.sharepoint.com/...)` → `Link Text`

**Remove Zoom meeting blocks entirely:**
Strip "Join Zoom Meeting" sections, Meeting IDs, Passcodes, one-tap mobile lines,
join instruction URLs. These are useless in print.

**Strip any remaining markdown links:**
`[text](url)` → `text`
No raw URLs should survive in the final document.

### 4. Write Temporary Markdown

Write the processed content to:

```
/tmp/aisc-packet-YYYY-MM-DD.md
```

120 character line length maximum. No emojis.

### 5. Convert to PDF

```bash
~/.local/bin/md2pdf /tmp/aisc-packet-YYYY-MM-DD.md
```

This produces `/tmp/aisc-packet-YYYY-MM-DD.pdf`.

### 6. Deliver to OneDrive

Move the PDF to the shared folder:

```bash
mv /tmp/aisc-packet-YYYY-MM-DD.pdf \
  "/Users/jjduqu/Library/CloudStorage/OneDrive-PADNOS/Information Solutions-Artificial Intelligence - Documents/Artificial Intelligence/Meeting Notes/AISC Notes YYYY-MM-DD.pdf"
```

### 7. Clean Up

```bash
rm -f /tmp/aisc-packet-YYYY-MM-DD.md
```

### 8. Report Back

- Confirm the PDF location and filename
- List which wiki-links were expanded
- Note any links that could not be resolved
- Remind the user to export the Excel tracking workbook PDF to the same folder

---

## Output

**PDF filename:** `AISC Notes YYYY-MM-DD.pdf` (date is the Monday meeting date)

**Destination:**
`/Users/jjduqu/Library/CloudStorage/OneDrive-PADNOS/Information Solutions-Artificial Intelligence - Documents/Artificial Intelligence/Meeting Notes/`

---

## Notes

- The Excel tracking workbook PDF is a separate manual export — this skill only handles
  meeting notes
- Wiki-link resolution is one level deep
- No URLs in the final output. Jonathan Padnos does not have Freshservice access. Project
  codes (IS26-xxx, etc.) are the identifiers that matter.
- Focus on clean, readable content for print or iPad reading
