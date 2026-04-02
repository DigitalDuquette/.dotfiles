---
description: Review what a GitHub user shipped this week
argument-hint: <github_username>
---

Show all merged PRs for a GitHub user since last Friday night,
with descriptions of each PR.

**GitHub username:** `$ARGUMENTS`

## Workflow

1. Validate that a GitHub username was provided. If missing,
   ask for one.

2. Determine the date of last Friday. Use `date` to calculate
   it — find the most recent Friday before today. Format as
   `YYYY-MM-DD`.

3. Search for merged PRs since that Friday:
   ```
   gh search prs --author=<username> \
     --merged-at=">=<friday_date>" \
     --limit 50 \
     --json number,title,repository,closedAt,url
   ```

4. If no PRs found, tell the user and stop.

5. For each PR, fetch details:
   ```
   gh pr view <number> --repo <owner/repo> \
     --json body,title,files
   ```

6. **Present results** grouped by repository (sorted by PR
   count descending). Within each repo, sort by merge date
   ascending. Format:

   ```
   **N merged PRs** across M repos:

   ### Owner/RepoName (X PRs)

   - [#number](url) — **PR title** *(Mon DD)*
     One to two sentence description derived from the PR body.
   ```

7. Save the summary to the Obsidian vault at:
   ```
   ~/Library/Mobile Documents/iCloud~md~obsidian/Documents/padnos/2-areas/reviews/dev-activity/<username>/YYYY-Www.md
   ```
   Use the ISO week number for the current week (e.g.
   `2026-W14.md`). Create the username directory if it
   doesn't exist.

8. Copy the full formatted summary to the clipboard via
   `pbcopy`.

9. Print the summary and confirm it is saved and on the
   clipboard.

## Notes

- Derive descriptions from the PR body — do not fabricate
  content. If the body is empty or uninformative, describe
  based on the title and changed files.
- The date in italics should be the actual merge date, not
  the Friday cutoff.
- Fetch PR details sequentially to avoid GitHub API rate
  limiting.
