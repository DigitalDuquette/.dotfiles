---
description: Add entry to team member capture log
---

Add a factual entry to a team member's capture log file.

**Format:** Each entry follows the 3-line structure (Event, Impact, Evidence)
with today's date as the heading.

**Steps:**

1. Prompt the user for:
   - Team member name (for file selection)
   - Event description (what happened)
   - Impact description (what it caused or risk introduced)
   - Evidence links (PR, ticket, Teams conversation, etc.)

2. Read the capture log file:
   `~/obsidian-vaults/padnos/2-areas/management/team/{name}/capture-log.md`

3. Add new entry under ## Entries section with today's date (YYYY-MM-DD)

4. Write the updated file

**CRITICAL RULES:**

- Use ONLY the information provided by the user - no speculation or embellishment
- Keep descriptions factual and neutral (no "failed to", "struggled with")
- If details are sparse, the entry should be sparse - do not ask clarifying
  questions
- One entry per date (if multiple events same day, use separate date headings)
- Evidence must be specific links (PR numbers, ticket numbers, Teams URLs)
- Match existing tone/style in the file exactly

**Entry format:**

```markdown
### YYYY-MM-DD

- Event: [User's description - factual only]
- Impact: [User's description - factual only]
- Evidence: [User's links - exact format they provide]
```

**Example:**

```markdown
### 2026-02-08

- Event: PR-525 review identified missing null checks in validation logic
- Impact: Code review required; potential production bug caught before merge
- Evidence: [[PR-525]], [GitHub PR-525](https://github.com/org/repo/pull/525)
```
