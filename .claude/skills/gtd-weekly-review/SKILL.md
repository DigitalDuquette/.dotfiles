---
name: gtd-weekly-review
description: Performs GTD weekly review by consolidating daily notes, meeting logs, shipped PRs, and Teams messages into structured review with team update, private notes, and action items. Use when conducting weekly review, processing daily notes, or preparing team updates.
allowed-tools: Read, Glob, Write, Bash, mcp__claude_ai_Microsoft_365__chat_message_search
---

# GTD Weekly Review

This skill automates the GTD weekly review process by consolidating daily
notes from `0-inbox/daily-notes/`, the weekly meeting log, merged PRs, and
the week's Teams messages into a structured review.

---

## What This Skill Does

The weekly review creates a file in `2-areas/reviews/weekly/` that serves
three purposes:

1. **Team Update** - Public communication of accomplishments and status
2. **Private Notes** - Sensitive items not for team sharing
3. **Action Items** - Tasks to move into Fresh/task management

---

## Instructions for Claude

When invoked, follow this workflow:

### 1. Determine the Week

Calculate the current ISO week number using:

```bash
date +%Y-W%V
```

Create the review file as `2-areas/reviews/weekly/YYYY-WW.md` (e.g.,
`2026-W02.md`)

### 2. Process Meeting Transcripts (if any)

Check `0-inbox/meeting/` and `0-inbox/meeting/1on1/` for unprocessed
transcripts.

- If both are empty, skip to Step 3.
- If transcripts are present, execute the `/meeting-review` workflow first.
  Read `~/.claude/commands/meeting-review.md` and follow it end-to-end.
  Announce "Found N transcripts, processing via /meeting-review first"
  before starting.
- After `/meeting-review` completes, the file
  `2-areas/reviews/weekly/YYYY-WXX-meetings.md` will exist. Read it as an
  additional input alongside daily notes in the steps that follow.

This handles meeting-heavy weeks. On IC-heavy weeks with no transcripts,
the chain falls through and daily notes remain the sole synthesis source.

### 3. Gather Shipped PRs

Execute the `/shipped-this-week` workflow for GitHub user
`DigitalDuquette`. Read `~/.claude/commands/shipped-this-week.md` and
follow it end-to-end, unmodified — it creates the dev-activity note at
`2-areas/reviews/dev-activity/DigitalDuquette/YYYY-Www.md`, which is the
detailed archive the Team Update links to.

After it completes, use the PR summary as an input for Step 7. If no PRs
were merged this week, skip this input and omit shipped-work bullets from
the Team Update.

### 4. Gather Daily Notes

Find all daily notes for the target week from `0-inbox/daily-notes/`:

- Daily notes use format: `YYYY-MM-DD.md`
- Read all notes in the folder, regardless of date.
- If a daily note doesn't exist for a day, skip it

### 5. Mine Teams Messages

Requires the Microsoft 365 MCP tool
`mcp__claude_ai_Microsoft_365__chat_message_search`. If it is not
connected, announce that Teams mining is skipped and continue — the
review still works from the other sources.

Search recipe (validated 2026-07-27 — do NOT use `afterDateTime`/
`beforeDateTime`; that path rate-limits instantly and skips channel
messages entirely):

- Search `query: "from:jared@padnos.com"` with no date parameters.
  This uses the Graph full-text path, which covers channel posts AND
  chats, newest first.
- Paginate with `offset` (25 per page) until `createdDateTime` crosses
  the week start. Discard anything outside the target week — including
  messages from the current day if the review runs early the next week.
- Results are ~250-char summaries. Adjacent messages usually quote the
  thread context; when a load-bearing thread needs more, run 1-3
  targeted keyword searches (project name, person, incident term).

Extract for Step 7:

- Decisions made in chat — these often resolve or supersede items the
  meeting log left open; prefer the latest state
- Public commitments: dates and deadlines announced in channels
- Open loops: questions asked with no visible resolution by week's end
- Wins posted by the team in channels (e.g. weekly-update posts) that
  transcripts and PRs miss
- Coaching or feedback delivered in writing (routes to Private Notes)

Cross-check the mined signal against the meeting log and PR list before
writing: chat frequently closes action items the other sources would
carry forward as open.

### 6. Process Daily Notes and Meeting Log

For each daily note, extract relevant content:

- Meeting notes and decisions
- Code review notes
- Action items and todos
- Project planning notes
- Links to other Obsidian notes
- Important context
- Reference materials

If `2-areas/reviews/weekly/YYYY-WXX-meetings.md` exists for this week
(created by `/meeting-review` in Step 2), also read it and extract:

- Meeting decisions and themes
- 1:1 highlights worth folding into Private Notes
- The meeting log's Action Items section (used as the seed list in Step 7)

### 7. Populate the Weekly Review

Create a file with the sections below. Read `example.md` in this skill's
directory for the expected structure and tone — adapt content and length
to the actual week.

**Team Update**

Length constraints — feedback from leadership (July 2026): past updates
read as prose reports ("a Tolstoy Novel"). The fix is scannability and
summarization, not a hard bullet cap. The audience skims this every
week.

- At most a one-line preamble naming the week's theme
- Bullets are short fragments, not sentences — one line each where
  possible, never multi-clause prose with sub-details packed in
- Bullet count is flexible (up to ~20 when the week earns it) — cut
  the detail inside each bullet, not the list of things that happened
- Summarize at theme level: each bullet names the outcome, not the
  implementation story behind it
- No separate Decisions / Blockers / Upcoming subsections — a key
  decision, a real blocker, or next week's focus is one bullet each
- Everything cut from the Team Update still has a home: shipped detail
  in the dev-activity note, meeting detail in the meeting log, daily
  detail in the Daily Note Review section below

Content:

- Format as a post ready to share with the team
- Summarize shipped PRs from Step 3 as one theme-level bullet (e.g.,
  "Shipped 8 PRs across 4 repos, nearly all for the inspection image
  outage"). Do not list individual PRs. End the bullet with a wiki-link
  to the dev-activity note:
  `[[2-areas/reviews/dev-activity/DigitalDuquette/YYYY-Www|full PR list]]`
- If a meeting log exists, pull only the most shareable decision or
  theme from it
- Fold in Teams-mined wins and public commitments from Step 5 (a team
  milestone posted in a channel is Team Update material)
- Remove sensitive or non-essential details
- Write in first person ("We shipped...", "I reviewed...")
- Keep items in bullet list

**DO NOT include in Team Update:**

- Recruiting issues or candidate information which should be for managers
  only, sharing that recruiting is happening is acceptable.
- Performance management discussions
- Personnel matters or interventions
- Salary, compensation, or HR topics
- Individual performance issues
- Confidential business decisions

These items belong exclusively in Private Notes.

**Private Notes**

- Personnel matters
- Sensitive technical decisions
- Items requiring discretion
- Context the user needs but team doesn't
- If a meeting log exists, fold in sensitive 1:1 themes,
  performance-management threads, and vendor frictions surfaced there
- Coaching or feedback delivered in Teams chat goes here, with the
  balance it deserves (pair a correction with the same week's praise)

**Action Items for Fresh**

- If a meeting log exists, start with its Action Items section as the
  seed list
- Add uncompleted tasks from daily notes
- Add Teams open loops and commitments from Step 5; drop or mark
  resolved any item that chat shows was already closed during the week
- Add new todos identified during this review
- Add follow-ups and commitments
- Deduplicate before writing
- Format as checkboxes: `- [ ] Task description`

**Meeting Log**

- If a meeting log exists for this week, add a section with a wiki-link
  to it
- Do not duplicate the meeting log content here, the link is enough
- Format: `See [[YYYY-WXX-meetings]] for the detailed meeting log.`

**Teams Review**

- Only include this section when Step 5 ran and produced signal
- Place it between Meeting Log and Daily Note Review
- Organize by day like the Daily Note Review; short bullets
- This is the searchable archive of chat signal — curated wins,
  decisions, and action items already live in the sections above; do
  not duplicate them at length here

**Daily Note Review**

- Organize content by day (Monday through Sunday)
- Preserve important context and Obsidian links
- Keep this section detailed—it becomes searchable archive
- If no daily note exists for a day, omit that day's section

### 8. Propose Now Updates to INDEX

Read `INDEX.md` at the vault root and note the current `## Now` section.

Using the synthesis just produced (Team Update, Private Notes, Action
Items), the meeting log if any, and the last 2-3 weekly review files in
`2-areas/reviews/weekly/`, propose 3-5 candidate items for the `## Now`
section of `INDEX.md`.

Criteria for a good Now item:

- Currently hot or about to be hot
- Worth surfacing to future-Jared in a fresh conversation as "this is on
  the front burner"
- Not routine, not a one-off, has narrative weight
- Could be a project name, decision point, person dynamic, or emerging
  trend

Append the proposals to the bottom of the weekly review file in a section
like this:

```md
## INDEX Now Suggestions

Proposed updates for the Now section of `INDEX.md` based on this week's
signal. Curate into `INDEX.md` manually.

- <proposed item with brief reasoning>
- <proposed item with brief reasoning>
- <proposed item with brief reasoning>
```

Do not edit `INDEX.md` directly. Curation is manual.

### 9. Archive Processed Daily Notes

Note: meeting transcripts were already archived by `/meeting-review` in
Step 2. This step only handles daily notes.

After successfully creating the weekly review, move the processed daily
notes to the archive:

1. Ensure the archive directory exists: `4-archive/daily-notes/`
2. Move all daily notes from `0-inbox/daily-notes/` that were included in
   the weekly review to `4-archive/daily-notes/`
    - confirm the file name doesn't already exist in the archive folder,
      if it does, append the latest datetime stamp to the file
3. Use `mv` command to preserve file metadata
4. Confirm the moves completed successfully

Example:

```bash
mkdir -p 4-archive/daily-notes
mv 0-inbox/daily-notes/2026-01-06.md 4-archive/daily-notes/
mv 0-inbox/daily-notes/2026-01-07.md 4-archive/daily-notes/
```

This clears the inbox after processing, following GTD principles.

### 10. Guide the User

After creating the review and archiving notes:

1. Show the user the file location
2. Report which daily notes were archived
3. Suggest they review the "Team Update" section before sharing
4. Remind them to transfer "Action Items for Fresh" to their task
   management system

---

## GTD Principles

This skill implements the GTD weekly review:

- **Collect** - Gather from daily notes
- **Process** - Categorize into team/private/action
- **Organize** - Structure for communication and action
- **Review** - Create searchable archive
- **Do** - Transfer actions to trusted system

"Your brain is for having ideas, not holding them."

---

## Notes

- Line length: 120 characters maximum
- Preserve line breaks as-is from daily notes
- Maintain all Obsidian wiki-links: `[[note-name]]`
- Use horizontal rules `---` between major sections
- Focus on clean git diffs
