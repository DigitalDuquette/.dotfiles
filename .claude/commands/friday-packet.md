---
name: friday-packet
description: >-
  Prepares the weekly Friday AI & OES send. Builds the AISC meeting notes PDF,
  pulls Claude MTD overage from claude.ai into a Claude in Excel prompt and a
  table image, drops the files in Downloads, and makes the reply-all draft.
allowed-tools: >-
  Read, Glob, Write, Bash, Edit,
  mcp__claude-in-chrome__tabs_context_mcp,
  mcp__claude-in-chrome__tabs_create_mcp,
  mcp__claude-in-chrome__navigate,
  mcp__claude-in-chrome__find,
  mcp__claude-in-chrome__computer,
  mcp__claude-in-chrome__javascript_tool,
  mcp__claude_ai_Microsoft_365__outlook_email_search,
  mcp__claude_ai_Microsoft_365__read_resource,
  mcp__claude_ai_Microsoft_365__outlook_create_reply_all_draft
---

# Friday Packet

Prepares the weekly Friday send to the AI & OES group (Kevin, JP, Ben, Chad,
Heather). The email is a reply-all on Kevin's "AI & OES" invite with three
things:

- Claude overage image in the body
- `AI @ PADNOS <date>.pdf` (Jared exports this by hand)
- `AISC Notes <Monday>.pdf`

Claude builds everything except the AI @ PADNOS PDF. Jared drops the files into
the draft and sends. The Outlook connector cannot add images or attachments, so
the files go to `~/Downloads`.

---

## What This Skill Does

1. Reads the Monday meeting agenda from `2-areas/AI@PADNOS/aisc/meeting/`
2. Expands all `[[wiki-links]]` inline (one level deep)
3. Strips all hyperlinks — no URLs in the final output
4. Converts to PDF using `md2pdf`
5. Moves the PDF to the shared OneDrive Meeting Notes folder, and copies it to
   `~/Downloads`
6. Pulls Claude MTD overage from claude.ai, puts a Claude in Excel prompt on the
   clipboard, and renders `~/Downloads/claude-overage-YYYY-MM-DD.png`
7. Makes the reply-all draft if Jared has not made one

---

## Instructions for Claude

### 1. Determine the Target Meeting Date

If invoked with an argument (e.g., `/friday-packet 2026-04-20`), use that date.

Otherwise, find the most recent meeting note **on or before today**. The user
creates the next week's agenda file before going into the meeting, so there will
often be a future-dated file present. Ignore it.

```bash
# List meeting files, filter to dates <= today, take the most recent
today=$(date +%Y-%m-%d)
ls 2-areas/AI@PADNOS/aisc/meeting/*.md | sort -r | while read f; do
  d=$(basename "$f" .md)
  if [[ "$d" <= "$today" ]]; then echo "$f"; break; fi
done
```

The meeting note file is: `2-areas/AI@PADNOS/aisc/meeting/YYYY-MM-DD.md`

If no qualifying file is found, tell the user and stop.

### 2. Read the Meeting Note and All Linked Files

Read the meeting note. Then find all `[[wiki-links]]` in the document.

For each wiki-link, search the vault for the target file:

```bash
VAULT="/Users/jjduqu/Library/Mobile Documents/iCloud~md~obsidian/Documents"
find "$VAULT/padnos" -name "link-name.md" -not -path "*/4-archive/*"
```

Read each linked file's content. Wiki-link resolution is one level deep —
linked files do not themselves contain wiki-links that need expanding.

### 3. Build the Expanded Document

Starting from the meeting note content:

**Expand wiki-links:**
Replace each `[[link-name]]` with the full content of the linked file. Drop the
file's H1 heading if it would be redundant with the surrounding context (e.g.,
`[[IDS Backlog]]` under a `## IDS` section doesn't need the `# IDS Backlog`
heading repeated).

**Strip Freshservice links — keep project codes only:**
`[IS26-232](https://padnos.freshservice.com/...)` → `IS26-232`
Pattern: any markdown link where the display text is a Freshservice code
(IS-xxx, IS26-xxx, SR-xxxxx, CASE-xxxxx). Replace with just the code.

**Strip SharePoint/OneDrive links — keep display text:**
`[Link Text](https://padnos365.sharepoint.com/...)` → `Link Text`

**Remove Zoom meeting blocks entirely:**
Strip "Join Zoom Meeting" sections, Meeting IDs, Passcodes, one-tap mobile
lines, join instruction URLs. These are useless in print.

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

### 6. Deliver to OneDrive and Downloads

Move the PDF to the shared folder, then copy it to Downloads for the email:

```bash
NOTES="$HOME/Library/CloudStorage/OneDrive-PADNOS-InformationSolutions-aisc"
NOTES="$NOTES/Artificial Intelligence/Meeting Notes"
mv /tmp/aisc-packet-YYYY-MM-DD.pdf "$NOTES/AISC Notes YYYY-MM-DD.pdf"
cp "$NOTES/AISC Notes YYYY-MM-DD.pdf" ~/Downloads/
```

### 7. Clean Up

```bash
rm -f /tmp/aisc-packet-YYYY-MM-DD.md
```

### 8. Claude Overage

Source: `https://claude.ai/admin-settings/usage`, table "Spend limits by user".
Jared must be signed in to claude.ai in Chrome as an org admin.

1. Load the Chrome tools in one ToolSearch call. Call `tabs_context_mcp`, open a
   new tab, and go to the Usage page.
2. **Sort by MTD spend, highest first.** The page does not keep the sort after a
   reload, and only 100 of ~148 users show on page 1. Unsorted, users with spend
   can be on page 2. Use `find` for the "MTD spend" column header button and
   click it. A JS `click()` on the `th` does not sort.
3. Run this with `javascript_tool`. It waits for the table, checks the sort, and
   stores the rows. Output over ~1500 characters gets truncated, so it returns
   only the first chunk:

   ```js
   const main = () => document.querySelector('main')?.innerText || '';
   for (let i = 0; i < 40 && !/ spent\n/.test(main()); i++)
     await new Promise(r => setTimeout(r, 500));
   const t = main();
   const re = /([^\n\t]+)\n([^\s@]+@\S+)\s+\S+\s+\$([\d,]+\.\d\d)/g;
   const all = [...t.matchAll(re)];
   const amts = all.map(m => +m[3].replace(/,/g, ''));
   if (!amts.every((v, i) => i === 0 || amts[i - 1] >= v))
     throw new Error('not sorted by MTD desc');
   window.__spend = [
     'TOTAL\t' + t.match(/^\$([\d,]+\.\d\d) spent$/m)[1],
     ...all.filter(m => m[3] !== '0.00')
       .map(m => `${m[2]}\t${m[1].trim()}\t${m[3]}`)];
   window.__spend.slice(0, 18).join('\n')
   ```

   If it throws "not sorted", click the header again (it may have sorted
   ascending) and rerun. Then get the rest:

   ```js
   window.__spend.slice(18).join('\n')
     + '\nROWS\t' + (window.__spend.length - 1)
   ```

4. Write both chunks, unchanged and in order, to `/tmp/claude-spend.tsv`, then
   run:

   ```bash
   python3 -I ~/.claude/scripts/claude_spend.py /tmp/claude-spend.tsv
   ```

   The script checks that the row count matches `ROWS` and that the user sum is
   within $1 of the page header. If either check fails, stop and tell Jared. Do
   not fix the numbers by hand. On success it puts the Claude in Excel prompt on
   the clipboard and writes the image.
5. Read the PNG and check it looks right.

### 9. Draft

Find this week's invite thread: search `query: "AI & OES"` with no sender,
newest first. Kevin sometimes sends a new invite, so the subject can change (for
example "AI & OES (Zoom - start at 10:30)"). Then search the Drafts folder for a
draft on that subject.

- **Draft exists:** leave it alone. Jared often makes it himself with the
  AI @ PADNOS PDF attached.
- **No draft:** `outlook_create_reply_all_draft` on Kevin's invite with no body.

Never send.

### 10. Report Back

- Confirm the PDF location and filename
- List which wiki-links were expanded
- Note any links that could not be resolved
- Overage: user count, total, header total, image path
- Draft: found or created, its subject, and what is already attached
- Jared's remaining steps:
  1. Open `claude-rollout.xlsx` (tab title shows `ai-tooling`), sheet
     `claude-overage`, open Claude in Excel, paste the clipboard. G1 holds the
     rules.
  2. Export the AI @ PADNOS workbook PDF, if it is not already in the draft.
  3. Put the overage image in the draft body, attach both PDFs, send.

---

## Output

- **PDF filename:** `AISC Notes YYYY-MM-DD.pdf` (date is the Monday meeting
  date)
- **Destination:** `$NOTES` from step 6, plus a copy in `~/Downloads`
- **Overage image:** `~/Downloads/claude-overage-YYYY-MM-DD.png` (today's date)

---

## Notes

- The Excel tracking workbook PDF is a separate manual export
- The overage image comes from the export, not from an Excel screenshot. The
  sheet can be stale until Jared pastes the prompt into Claude in Excel.
- Script: `~/.claude/scripts/claude_spend.py`. Run `--selftest` after you
  change it.
- Wiki-link resolution is one level deep
- No URLs in the final output. Jonathan Padnos does not have Freshservice
  access. Project codes (IS26-xxx, etc.) are the identifiers that matter.
- Focus on clean, readable content for print or iPad reading
