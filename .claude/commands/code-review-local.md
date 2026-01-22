---
allowed-tools: Bash(gh issue view:*), Bash(gh search:*), Bash(gh issue list:*), Bash(gh pr diff:*), Bash(gh pr view:*), Bash(gh pr list:*)
description: Code review a pull request
---

Provide an executive code review for the given pull request.

**Agent assumptions (applies to all agents and subagents):**
- All tools are functional and will work without error. Do not test tools or make exploratory calls.
- Only call a tool if it is required to complete the task. Every tool call should have a clear purpose.

To do this, follow these steps precisely:

1. Launch a haiku agent to check if any of the following are true:
   - The pull request is closed
   - The pull request is a draft

   If any condition is true, stop and do not proceed.

   Note: Still review Claude generated PR's.

2. Launch a haiku agent to check if the team template is followed. See section "Pre-Review: Check Template Compliance" for details. Note the result but continue regardless.

3. Launch a haiku agent to return a list of file paths (not their contents) for all relevant CLAUDE.md files including:
   - The root CLAUDE.md file, if it exists
   - Any CLAUDE.md files in directories containing files modified by the pull request

4. Launch a sonnet agent to view the pull request and return a summary of the changes

5. Launch 4 agents in parallel to independently review the changes. Each agent should return a list of issues, where each issue includes:
   - File path and line numbers
   - Brief description of the issue
   - Category (e.g., "CLAUDE.md violation", "bug", "architectural pattern")

   The agents should do the following:

   **Agents 1 + 2: CLAUDE.md compliance sonnet agents**

   Audit changes for CLAUDE.md compliance in parallel. Note: When evaluating CLAUDE.md compliance for a file, you should only consider CLAUDE.md files that share a file path with the file or parents.

   **CRITICAL architectural patterns to check:**

   **For Python code:**

   1. **Dependency Injection Violations:**
      - Flag utility modules (e.g., `ftp_tools.py`, `db_tools.py`) loading `.env` or `config.yaml` at module level
      - Flag module-level initialization of credentials/configuration (e.g., `env = dotenv_values('.env')` at module level)
      - Should see: Configuration loaded in main pipeline script, passed as function parameters to modules

   2. **Logging Architecture Violations:**
      - Flag utility modules accepting `log` or `logger` parameters in function signatures
      - Flag utility modules configuring their own loggers (e.g., `logging.basicConfig()`, `logger = logging.getLogger(__name__)`)
      - Should see: PADpy decorators (`@log_execution`) on main pipeline functions, modules raise exceptions only

   Reference CLAUDE.md sections: "Configuration and Dependency Injection" and "Logging Architecture"

   **For SQL DDL scripts:**

   1. **Unnecessary Session Settings:**
      - Flag `SET ANSI_NULLS ON` (it's the default)
      - Flag `SET QUOTED_IDENTIFIER ON` (it's the default)
      - Should see: Clean DDL without session settings unless explicitly required

   2. **Index Option Bloat:**
      - Flag index options that are all defaults: `FILLFACTOR = 100`, `PAD_INDEX = ON`, `STATISTICS_NORECOMPUTE = OFF`, `IGNORE_DUP_KEY = OFF`, `ALLOW_ROW_LOCKS = ON`, `ALLOW_PAGE_LOCKS = ON`, `OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF`
      - Flag `FILLFACTOR = 100` (it's the default, only set if you have a specific performance reason and document why)
      - Should see: Minimal index definitions without WITH clause unless changing defaults
      - Example: `PRIMARY KEY CLUSTERED (ID ASC)` not `PRIMARY KEY CLUSTERED (ID ASC) WITH (PAD_INDEX = ON, FILLFACTOR = 100, ...)`

   **Rationale:** This is SSMS "Generate Scripts" bloat that people copy-paste without thinking. Keep DDL clean and minimal.

   **Agent 3: Opus bug agent (parallel with agent 4)**

   Scan for obvious bugs. Focus only on the diff itself without reading extra context. Flag only significant bugs; ignore nitpicks and likely false positives. Do not flag issues that you cannot validate without looking at context outside of the git diff.

   **Agent 4: Opus bug agent (parallel with agent 3)**

   Look for problems that exist in the introduced code. This could be security issues, incorrect logic, etc. Only look for issues that fall within the changed code.

   **CRITICAL: We only want HIGH SIGNAL issues.** Flag issues where:
   - The code will fail to compile or parse (syntax errors, type errors, missing imports, unresolved references)
   - The code will definitely produce wrong results regardless of inputs (clear logic errors)
   - Clear, unambiguous CLAUDE.md violations where you can quote the exact rule being broken

   Do NOT flag:
   - Code style or quality concerns
   - Potential issues that depend on specific inputs or state
   - Subjective suggestions or improvements

   If you are not certain an issue is real, do not flag it. False positives erode trust and waste reviewer time.

   In addition to the above, each subagent should be told the PR title and description. This will help provide context regarding the author's intent.

6. Write the executive review to the filesystem (see "Output Format" section below).

Use this list when evaluating issues in Step 5 (these are false positives, do NOT flag):

- Pre-existing issues
- Something that appears to be a bug but is actually correct
- Pedantic nitpicks that a senior engineer would not flag
- Issues that a linter will catch (do not run the linter to verify)
- General code quality concerns (e.g., lack of test coverage, general security issues) unless explicitly required in CLAUDE.md
- Issues mentioned in CLAUDE.md but explicitly silenced in the code (e.g., via a lint ignore comment)

**Note:** Architectural violations that ARE documented in CLAUDE.md (dependency injection, logging architecture, etc.) SHOULD be flagged.

Notes:

- Use gh CLI to interact with GitHub (e.g., fetch pull requests). Do not use web fetch.
- Create a todo list before starting.

---

## Output Format

Write the review to: `~/obsidian-vaults/padnos/2-areas/software/pr-review/{repo-name}/PR-{pr-number}.md`

**Executive summary format:**

```markdown
# PR-{number}: {title}

**Link:** {github-url}

**Assessment:** ✅ GOOD | ⚠️ ISSUES FOUND | ❌ BLOCKED

**Template Compliance:** [Pass/Fail with brief note]

---

## Summary

{2-3 sentence summary of what the PR does}

---

## Issues

{If no issues: "No issues found."}

{If issues found, group by category:}

### Bugs

- **{file}:{line}** - {brief description}
- **{file}:{line}** - {brief description}

### CLAUDE.md Violations

- **{file}:{line}** - {brief description, cite CLAUDE.md rule}

### Architectural Patterns

- **{file}:{line}** - {brief description (e.g., dependency injection, logging)}

---

## Notes

{Any additional context, patterns observed, or concerns that don't rise to "issue" level}
```

**Key principles:**
- Keep descriptions brief (1-2 sentences max per issue)
- Focus on WHAT and WHERE, not detailed HOW to fix
- The human will ask follow-up questions if they need more detail
- Do NOT post to GitHub - filesystem only

---

## Pre-Review: Check Template Compliance

1. Fetch the canonical PR template from BI-Dev-Guidelines:

    ```bash
    gh api repos/PADNOS/BI-Dev-Guidelines/contents/templates/PULL-REQUEST-example.md \
        --jq '.content' | base64 -d
    ```

2. Get the current PR description:

    ```bash
    gh pr view {pr-number} --json body --jq '.body'
    ```

3. Compare PR body against template structure:

   - Are all main sections present? (Context, Changes, Testing, etc.)
   - Are placeholder instructions removed?
   - Is there actual content or just template boilerplate?

4. Note the result in the review output:
   - **Pass:** Note that template was followed
   - **Fail:** Note the missing sections or boilerplate content, include link to template

   Template link: https://github.com/PADNOS/BI-Dev-Guidelines/blob/main/templates/PULL-REQUEST-example.md

   **Continue with review regardless of template compliance.**