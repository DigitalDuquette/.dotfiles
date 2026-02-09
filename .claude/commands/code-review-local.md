---
allowed-tools: Bash(gh issue view:*), Bash(gh search:*), Bash(gh issue list:*), Bash(gh pr diff:*), Bash(gh pr view:*), Bash(gh pr list:*)
description: Code review a pull request
---

Provide a straightforward code review for the given pull request.

**Steps:**

1. Read relevant CLAUDE.md files (root + any in directories with modified files)

2. Get the PR diff and understand what changed

3. Review the code looking for:
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

4. Write the review file (see Output Format below)

**What NOT to flag (false positives):**
- Pre-existing issues not introduced by this PR
- Style/quality concerns unless CLAUDE.md requires them
- Issues that depend on runtime state or specific inputs
- Anything a linter would catch
- Nitpicks a senior engineer would ignore

**If uncertain whether something is a bug, frame it as a question in the Notes
section, not as a finding.**

**Notes:**
- Use gh CLI only, no web fetch
- Keep it simple - no parallel agents, no excessive orchestration
- Focus on high-signal issues only

---

## Output Format

Write the review to: `~/obsidian-vaults/padnos/2-areas/software/pr-review/{repo-name}/PR-{pr-number}.md`

**KISS format - just the findings:**

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

**Key principles:**
- One line per issue: `file:line - description`
- Brief descriptions (1 sentence max)
- User will check the code and add GitHub review comments themselves
- Do NOT post to GitHub - filesystem only
- Use GitHub CLI `gh` to access PR details
- Use local file system for current version of the files in the PR.
