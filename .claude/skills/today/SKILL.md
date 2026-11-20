---
name: today
description: >-
  End-of-day capture. Pulls what Jared did from Krisp meetings, Outlook,
  Teams, GitHub, vault commits, and Freshservice project tasks, asks him
  for the why, and writes one
  daily note per day to 0-inbox/daily-notes/. Catches up on every day
  since the last note, so a missed day is not lost. Use when Jared
  says /today, "log my day", "what did I do today", or "catch up my
  daily notes".
argument-hint: "[YYYY-MM-DD]  (optional: capture only this day)"
allowed-tools: >-
  Read, Write, Edit, Glob,
  Bash(~/.claude/skills/today/scripts/day-bounds.sh:*),
  Bash(~/.claude/skills/today/scripts/github-day.sh:*),
  Bash(~/.claude/skills/today/scripts/fs-tasks-day.sh:*),
  Bash(git -C * log:*), Bash(git -C * show:*),
  mcp__claude_ai_Microsoft_365__chat_message_search,
  mcp__claude_ai_Microsoft_365__outlook_calendar_search,
  mcp__claude_ai_Microsoft_365__read_resource,
  mcp__claude_ai_Krisp__search_meetings,
  mcp__claude_ai_Krisp__get_multiple_documents
---

# Today

The sources hold the *what*. Only Jared holds the *why*: which sweep,
which 1:1, which follow-up a piece of work came from. This skill pulls
the what, then asks for the why, while he still remembers it.

`gtd-weekly-review` reads and archives every note in
`0-inbox/daily-notes/`, so this skill only writes there.

All paths are relative to the vault root:
`~/Library/Mobile Documents/iCloud~md~obsidian/Documents/padnos`.

---

## 1. Pick the days

- If an argument date is given, capture only that day.
- Otherwise, list `0-inbox/daily-notes/YYYY-MM-DD.md`.
  - No notes: the weekly review emptied the inbox. Start on the most
    recent Friday before today (the review's window starts on Friday).
  - Newest note is today: capture today only, and merge (Step 4).
  - Otherwise: start the day after the newest note.
- End on today. Cap at 7 days. Tell Jared which days you will cover.
- Skip a Saturday or Sunday if all sources are empty for it.

## 2. Pull each day

Run the sources for all days in parallel.

**GitHub:** `~/.claude/skills/today/scripts/github-day.sh YYYY-MM-DD`

- PR, issue, and review events, plus commit subjects for every repo
  pushed to. Times are ET.

**Freshservice project tasks:**
`~/.claude/skills/today/scripts/fs-tasks-day.sh YYYY-MM-DD`

- Tasks created or updated that day. `mine` rows (assignee or
  reporter) include the description, which often holds the decision.
- The API does not record who made an update. Ask about `other` rows
  only if they look like Jared's work; otherwise drop them.
- Runs under `op run`, so 1Password may ask for Touch ID.

**Krisp meetings:** `search_meetings` with `after` and `before` set to
the day, fields `name`, `date`, `attendees`, `key_points`,
`action_items`.

- This is the main source. Most of Jared's day is meetings, and Krisp
  holds the decisions, owners, and the why. Never ask Jared what a
  meeting was about; read it.

**Outlook calendar:** `outlook_calendar_search`, `query: "*"`, the day,
`order: "oldest"`.

- Names every meeting and its attendees. Use it to name the meeting
  behind a Teams message or Krisp record. Skip personal, focus, and
  commute blocks.

**Vault commits:** `git -C <vault root> log --since=<day> --until=<day+1>
--stat`

- Shows what Jared built or wrote in the vault. Read a new project
  note's decisions section for the why.

**Teams:** `chat_message_search`

- Jared's messages: `query: "*"`, `sender: "Jared Duquette"`,
  `afterDateTime` and `beforeDateTime` both set to the day.
- Page with `offset` (25 per page). Stop when a page returns only
  message ids you have already seen; past the end, the API repeats
  the last result.
- Thread replies: run the same date range with no sender. Keep only
  messages in a `chatId` where Jared posted that day. These hold the
  answers (a bot's findings, a pushback reply).
- Asks of Jared: `query: "Jared"` with the same dates. Keep messages
  that ask him for something. This run also returns some of Jared's own
  posts that the `sender` run misses (2026-11-20: a channel post). Keep
  them.
- Do not use the no-date `from:` recipe. On 2026-11-16 it missed 5
  of Jared's 7 messages.
- `createdDateTime` can be wrong in group chats. When a time looks
  off, the message id is epoch milliseconds; date by the id.
- Summaries are about 250 characters. Read a full message with
  `read_resource` only when a thread is load-bearing and the summary
  does not show the outcome.

## 3. Draft, then ask for the why

Group each day's activity into threads of work, not one line per
event. Example: 4 merged PRs, a Teams session, and a task move to UAT
on the same bot are one thread.

Show the draft for all days at once. The sources above should answer
most of the why. Ask only about specific gaps they cannot fill, by
name: "PR #12 on X: what was it for?" Never ask about a meeting that
Krisp or Outlook covers, or for something a source already shows. If
there are no real gaps, ask only:

> Anything I missed?

Fold his answer into the threads. Work he names with no trace in the
sources goes in as he said it. Do not invent a why he did not give.

If Jared is not at the keyboard or skips the question, write the
draft as-is and add `- (no context captured)` as the last bullet.

## 4. Write the notes

One file per day: `0-inbox/daily-notes/YYYY-MM-DD.md`.

- If the file exists, keep every line in it. Add only threads not
  already there. Jared writes in these notes by hand too.
- Format, matching the vault's daily notes:
  - A blank first line, then a flat bullet list. No headings, no
    frontmatter.
  - One bullet per thread. Lead with the why when there is one.
  - Nested bullets for detail. Cite ids (PR #, issue #, IS26-nnn,
    ticket #) instead of restating their content.
  - Last bullet `Open loops`, nested: undecided items, asks waiting
    on Jared, open questions on closed tasks.
  - Wrap at 80 characters. A hook blocks longer lines.
  - No em dashes.
- Do not commit. Jared commits.

Report which files you wrote or changed, and anything you skipped.

---

## Reference example (2026-11-16)

```markdown

- Escalation sweep of old, stuck tickets. Pushed back to Jeff Wood on
  splitting RIMAS transactions across periods; Jeff gave the month-end
  trailer case. No decision yet.
- Jason 1:1 follow-up: he can now bypass-merge his own PRs on
  dev-guidelines, PADNOS-data-warehouse, api-collections (PR still
  required). Reviewed his api-collections PR #48.
- New process: IS26-632, recurring Freshservice scheduled ticket to review
  expiring 1Password items from the Business Watchtower report. No
  automated pipeline (needs a read-all-vaults service account). Open:
  recurrence interval.
- Open loops
  - RIMAS period split decision with Jeff Wood.
```
