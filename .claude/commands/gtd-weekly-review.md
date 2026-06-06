---
name: gtd-weekly-review
description: Performs GTD weekly review by consolidating daily notes into structured review with team update, private notes, and action items. Use when conducting weekly review, processing daily notes, or preparing team updates.
allowed-tools: Read, Glob, Write, Bash
---

# GTD Weekly Review

This skill automates the GTD weekly review process by consolidating daily notes from `0-inbox/daily-notes/` into a structured review.

---

## What This Skill Does

The weekly review creates a file in `2-areas/reviews/weekly/` that serves three purposes:

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

Create the review file as `2-areas/reviews/weekly/YYYY-WW.md` (e.g., `2026-W02.md`)

### 2. Process Meeting Transcripts (if any)

Check `0-inbox/meeting/` and `0-inbox/meeting/1on1/` for unprocessed transcripts.

- If both are empty, skip to Step 3.
- If transcripts are present, execute the `/meeting-review` workflow first.
  Read `~/.claude/commands/meeting-review.md` and follow it end-to-end.
  Announce "Found N transcripts, processing via /meeting-review first" before starting.
- After `/meeting-review` completes, the file
  `2-areas/reviews/weekly/YYYY-WXX-meetings.md` will exist. Read it as an additional
  input alongside daily notes in the steps that follow.

This handles meeting-heavy weeks. On IC-heavy weeks with no transcripts, the chain
falls through and daily notes remain the sole synthesis source.

### 3. Gather Daily Notes

Find all daily notes for the target week from `0-inbox/daily-notes/`:

- Daily notes use format: `YYYY-MM-DD.md`
- Read all notes in the folder, regardless of date.
- If a daily note doesn't exist for a day, skip it

### 4. Process Daily Notes and Meeting Log

For each daily note, extract relevant content:

- Meeting notes and decisions
- Code review notes
- Action items and todos
- Project planning notes
- Links to other Obsidian notes
- Important context
- Reference materials

If `2-areas/reviews/weekly/YYYY-WXX-meetings.md` exists for this week (created by
`/meeting-review` in Step 2), also read it and extract:

- Meeting decisions and themes
- 1:1 highlights worth folding into Private Notes
- The meeting log's Action Items section (used as the seed list in Step 5)

### 5. Populate the Weekly Review

Create a file using the template below with these sections:

**Team Update**

- Format as a post ready to share with the team
- Include: accomplishments, key decisions, blockers, upcoming focus
- If a meeting log exists, pull shareable decisions, demos, and themes from it into
  accomplishments and decisions
- Keep it concise and action-oriented
- Remove sensitive or non-essential details
- Write in first person ("We shipped...", "I reviewed...")
- Keep items in bullet list with no preamble

**DO NOT include in Team Update:**

- Recruiting issues or candidate information which should be for managers only, sharing that recruiting is happened is acceptable.
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
- If a meeting log exists, fold in sensitive 1:1 themes, performance-management
  threads, and vendor frictions surfaced there

**Action Items for Fresh**

- If a meeting log exists, start with its Action Items section as the seed list
- Add uncompleted tasks from daily notes
- Add new todos identified during this review
- Add follow-ups and commitments
- Deduplicate before writing
- Format as checkboxes: `- [ ] Task description`

**Meeting Log**

- If a meeting log exists for this week, add a section with a wiki-link to it
- Do not duplicate the meeting log content here, the link is enough
- Format: `See [[YYYY-WXX-meetings]] for the detailed meeting log.`

**Daily Note Review**

- Organize content by day (Monday through Sunday)
- Preserve important context and Obsidian links
- Keep this section detailed—it becomes searchable archive
- If no daily note exists for a day, omit that day's section

### 6. Archive Processed Daily Notes

Note: meeting transcripts were already archived by `/meeting-review` in Step 2. This
step only handles daily notes.

After successfully creating the weekly review, move the processed daily notes to the archive:

1. Ensure the archive directory exists: `4-archive/daily-notes/`
2. Move all daily notes from `0-inbox/daily-notes/` that were included in the weekly review to `4-archive/daily-notes/`
    - confirm the file name doesn't already exist in the archive folder, if it does, append the latest datetime stamp to the file
3. Use `mv` command to preserve file metadata
4. Confirm the moves completed successfully

Example:

```bash
mkdir -p 4-archive/daily-notes
mv 0-inbox/daily-notes/2026-01-06.md 4-archive/daily-notes/
mv 0-inbox/daily-notes/2026-01-07.md 4-archive/daily-notes/
```

This clears the inbox after processing, following GTD principles.

### 7. Guide the User

After creating the review and archiving notes:

1. Show the user the file location
2. Report which daily notes were archived
3. Suggest they review the "Team Update" section before sharing
4. Remind them to transfer "Action Items for Fresh" to their task management system

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

---

## Example

This example demonstrates the structure and tone. Adapt the content and length based on your actual daily notes.

```md
# Week 03, 2026

## Team Update

This week was focused on infrastructure improvements and project planning.

Key accomplishments:

- Fixed the contact center grouping transformation that powers multiple dashboards. Working with Jeff G on the rename
  pattern, we established a sustainable process where future additions won't break dashboards.
- Made significant progress on Auto Pricing Calculator with user stories and project planning revisions.
- Reviewed AISC work and built out January scorecard, including sprint planning for January and February.

Upcoming focus: Connor out next week with new baby. Completed knowledge transfer sessions on flow toggles.

Blockers:
- Still no communication from Salesforce as of Jan 16, risking our ability to negotiate a good deal.

---

## Private Notes

Recruiting: Processed large batch of resumes through LinkedIn. Created separate email workflow for Devon to handle phone
screens. Several top candidates already replied.

Performance management: Created capture log for Arnaud following TG example. Enough of a trend for structured
intervention.

Technical frustrations: 2 hours lost trying to get scorecard to print - waiting on Tony for Mac drivers and Jim for MG1.

---

## Action Items for Fresh

- [ ] Jared to convert ticket 111239 or check if already converted
- [ ] Review DBA scripts repo structure following BI dev guidelines
- [ ] Turn on flow on Monday and communicate with auto team
- [ ] Follow up on Salesforce communication/negotiation

---

## Meeting Log

See [[2026-W03-meetings]] for the detailed meeting log.

---

## Daily Note Review

### Thursday, January 9

Discovered Claude Code internal tool simplification process. Worth reviewing source and testing for code review
workflows.

### Friday, January 10

Researched conferences to book review dates. Notes on agents and skills architecture.

### Sunday, January 12

**Sprint Planning:** Discussed outbound inspection in RIMAS with Jeff. Scoping decisions on VIN title issues (111040).

**Technical Frustrations:** Nearly 2 hours trying to get scorecard to print.

```
