---
allowed-tools: Bash(gh issue view:*), Bash(gh search:*), Bash(gh issue list:*), Bash(gh pr diff:*), Bash(gh pr view:*), Bash(gh pr list:*), Bash(gh repo view:*), Bash(gh api:*), Read(~/obsidian-vaults/padnos/**), Write(~/obsidian-vaults/padnos/**), Glob(~/obsidian-vaults/padnos/**), Grep(~/obsidian-vaults/padnos/**), Read(/Users/jjduqu/Library/Mobile Documents/iCloud~md~obsidian/Documents/padnos/**), Write(/Users/jjduqu/Library/Mobile Documents/iCloud~md~obsidian/Documents/padnos/**), Glob(/Users/jjduqu/Library/Mobile Documents/iCloud~md~obsidian/Documents/padnos/**), Grep(/Users/jjduqu/Library/Mobile Documents/iCloud~md~obsidian/Documents/padnos/**)
description: Code review a pull request
argument-hint: "[REPO] <PR_NUMBER>"
---

Provide a straightforward code review for pull request: $ARGUMENTS

**Argument parsing:**

I was given: $ARGUMENTS

- If two arguments (format: REPO PR_NUMBER): Use REPO=$0 and PR_NUMBER=$1
- If one argument (format: PR_NUMBER): Use PR_NUMBER=$0 and get REPO from `gh repo view --json nameWithOwner -q .nameWithOwner`

**Steps:**

1. Determine REPO and PR_NUMBER using the logic above (check if $1 is empty or not)

2. Get PR metadata:
   - PR title, URL: `gh pr view -R <REPO> <PR_NUMBER> --json title,url`
   - Head branch ref: `gh pr view -R <REPO> <PR_NUMBER> --json headRefName -q .headRefName`
   - Changed files: `gh pr view -R <REPO> <PR_NUMBER> --json files -q '.files[].path'`

3. Read relevant CLAUDE.md files from Obsidian vault (root + any in directories matching modified files)

4. Get the PR diff: `gh pr diff -R <REPO> <PR_NUMBER>`

5. Get file contents from GitHub (NOT local filesystem):
   - For any file you need to review in detail, use:
     `gh api repos/<REPO>/contents/<FILE_PATH>?ref=<HEAD_REF> --jq '.content' | base64 -d`
   - This ensures you're always reviewing the actual PR code, not stale local files
   - Only fetch files when you need to see full context beyond the diff

6. Review the code looking for:
   - **Bugs:** Syntax errors, logic errors, will-break issues only (not style/nitpicks)
   - **DRY violations:** Repeated code that should be extracted
   - **SOLID violations:** Especially Single Responsibility violations
   - **Readability/maintainability:** Is the code clear and easy to maintain?
   - **Pattern violations:** Does it follow appropriate patterns (e.g., DAG-like for
     pipelines)?
   - **CLAUDE.md architectural violations:**
     - Python: Dependency injection violations (module-level .env loading, module-level
       credential init)
     - Python: Logging architecture violations (utility modules with logger params or
       logging.basicConfig)
     - SQL DDL: Unnecessary defaults (SET ANSI_NULLS ON, FILLFACTOR = 100, etc.)

7. Write the review file (see Output Format below)
   - If file already exists: append new review after `---` separator
   - Count existing reviews to determine review number (first review has no number, subsequent are "Review 2", "Review 3", etc.)
   - Include date in review header for appended reviews
   - **IMPORTANT:** For appended reviews, nest all content under the "Review {N}" heading:
     - Use `## Review {N}` as the top-level heading
     - Use `### Findings` and `### Notes` (nested under Review)
     - Use `#### Bugs`, `#### DRY Violations`, etc. (nested under Findings)

**What NOT to flag (false positives):**
- Pre-existing issues not introduced by this PR
- Style/quality concerns unless CLAUDE.md requires them
- Issues that depend on runtime state or specific inputs
- Anything a linter would catch
- Nitpicks a senior engineer would ignore

**Common false positives to avoid:**
- **Module-level config loading**: Standard practice for application entry points (files with `if __name__ == '__main__'`). Only flag if it's a library module meant to be imported.
- **API client classes**: A class that wraps an API (setup, call API, parse response) is ONE responsibility, not a SOLID violation. Don't confuse "multiple steps" with "multiple responsibilities."
- **Cohesive workflows**: Database operations that are part of one logical workflow (e.g., initialize_queue running 6 setup queries) are NOT DRY violations. That's just how workflows work.
- **SQL file organization**: Separating SQL into .sql files with descriptive names is GOOD organization, not a maintainability problem. Don't flag this as "separated from usage."
- **Contextual constants**: Simple limits like `[:10]` for claim keys or `[:150]` for note truncation aren't "magic numbers" worth flagging if the context is clear.
- **Defensive error handling**: Edge case error handling for stable APIs (bounds checking, type validation) is nice-to-have, not critical. Only flag actual bugs that will break in normal operation.
- **Line numbers**: Always verify line numbers are from the actual file, not the diff output. Check file length before citing line numbers.

**Critical thinking checklist:**
- Does this pattern exist for a good reason? (Don't flag patterns without understanding WHY)
- Would this actually break in production? (Theoretical edge cases ≠ critical bugs)
- Is this how senior engineers typically write this type of code? (Don't be overly dogmatic)
- Can I defend this finding if challenged? (Be ready to explain or retract)

**If uncertain whether something is a bug, frame it as a question in the Notes
section, not as a finding.**

**Notes:**
- Use gh CLI only, no web fetch
- Keep it simple - no parallel agents, no excessive orchestration
- Focus on high-signal issues only

---

## Output Format

Write the review to: `~/obsidian-vaults/padnos/2-areas/software/pr-review/{repo-name}/PR-{pr-number}.md`

### For NEW review file (first review):

```markdown
# PR-{number}: {title}

**Link:** {github-url}

**Status:** ✅ LOOKS GOOD | ⚠️ ISSUES FOUND

## Findings

{If no issues: "No issues found."}

{If issues found, list them simply:}

### Bugs
- `file.py:123` - Brief description (1 sentence)
- `other.py:456` - Brief description

### DRY Violations
- `file.py:100-150` - Duplicated logic in function X and Y

### SOLID Violations
- `class.py:50` - Class doing too many things (SRP violation)

### Readability/Maintainability
- `complex.py:200` - Complex nested logic, hard to follow

### Pattern Violations
- `pipeline.py:75` - Not following DAG pattern, has circular dependency

### CLAUDE.md Violations
- `utils.py:10` - Module-level .env loading (dependency injection violation)

## Notes

{Optional: Questions, uncertainties, or observations that don't rise to "finding" level}
```

### For APPENDING to existing review file:

If the file already exists, **append** the following after the existing content (after a `---` separator):

```markdown
---

## Review {N} - {YYYY-MM-DD}

**Status:** ✅ LOOKS GOOD | ⚠️ ISSUES FOUND

### Findings

{Same format as above but with one extra # - use #### for subsections like Bugs, DRY Violations, etc.}

#### Bugs
- `file.py:123` - Brief description

#### DRY Violations
- `file.py:100-150` - Duplicated logic

### Notes

{Optional notes about what changed or what was re-reviewed}
```

**Review numbering:**
- First review: No number (just the main sections)
- Second review: "Review 2"
- Third review: "Review 3"
- etc.

**How to determine review number:**
- Count existing "## Review" headings in the file
- If none exist, this is Review 2 (first append)
- If "## Review 2" exists but not "## Review 3", this is Review 3

**Key principles:**
- One line per issue: `file:line - description`
- Brief descriptions (1 sentence max)
- User will check the code and add GitHub review comments themselves
- Do NOT post to GitHub - filesystem only
- Use GitHub CLI `gh` exclusively for ALL PR data (diff, files, metadata)
- NEVER read code files from local filesystem - always use `gh api` to get file contents from GitHub
