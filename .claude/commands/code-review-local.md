---
allowed-tools: Bash(gh issue view:*), Bash(gh search:*), Bash(gh issue list:*), Bash(gh pr comment:*), Bash(gh pr diff:*), Bash(gh pr view:*), Bash(gh pr list:*), mcp__github_inline_comment__create_inline_comment
description: Code review a pull request
---

Provide a code review for the given pull request.

**Agent assumptions (applies to all agents and subagents):**
- All tools are functional and will work without error. Do not test tools or make exploratory calls.
- Only call a tool if it is required to complete the task. Every tool call should have a clear purpose.

To do this, follow these steps precisely:

1. Launch a haiku agent to check if any of the following are true:
   - The pull request is closed
   - The pull request is a draft

   If any condition is true, stop and do not proceed.

    Note: Still review Claude generated PR's.

2. Launch a haiku agent to check if the team template is followed, follow section below (Pre-Review: Check Template Compliance) for details

3. Launch a haiku agent to return a list of file paths (not their contents) for all relevant CLAUDE.md files including:
   - The root CLAUDE.md file, if it exists
   - Any CLAUDE.md files in directories containing files modified by the pull request

4. Launch a sonnet agent to view the pull request and return a summary of the changes

5. Launch 4 agents in parallel to independently review the changes. Each agent should return the list of issues, where each issue includes a description and the reason it was flagged (e.g. "CLAUDE.md adherence", "bug"). The agents should do the following:

   Agents 1 + 2: CLAUDE.md compliance sonnet agents
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

   Agent 3: Opus bug agent (parallel subagent with agent 4)
   Scan for obvious bugs. Focus only on the diff itself without reading extra context. Flag only significant bugs; ignore nitpicks and likely false positives. Do not flag issues that you cannot validate without looking at context outside of the git diff.

   Agent 4: Opus bug agent (parallel subagent with agent 3)
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

6. For each issue found in the previous step by agents 1, 2, 3, and 4, launch parallel subagents to validate the issue. These subagents should get the PR title and description along with a description of the issue. The agent's job is to review the issue to validate that the stated issue is truly an issue with high confidence. For example, if an issue such as "variable is not defined" was flagged, the subagent's job would be to validate that is actually true in the code. Another example would be CLAUDE.md issues (including architectural violations like dependency injection or logging patterns). The agent should validate that the CLAUDE.md rule that was violated is scoped for this file and is actually violated. Use Opus subagents for bugs and logic issues, and sonnet agents for CLAUDE.md violations.

7. Filter out any issues that were not validated in step 5. This step will give us our list of high signal issues for our review.

8. If issues were found, skip to step 8 to post inline comments directly.

   If NO issues were found, post a summary comment using `gh pr comment` (if `--comment` argument is provided):
   "No issues found. Checked for bugs, CLAUDE.md compliance, dependency injection patterns, and logging architecture."

9. Post inline comments for each issue using `mcp__github_inline_comment__create_inline_comment`. For each comment:
   - Provide a brief description of the issue
   - For small, self-contained fixes, include a committable suggestion block
   - For larger fixes (6+ lines, structural changes, or changes spanning multiple locations), describe the issue and suggested fix without a suggestion block

   **IMPORTANT: Only post ONE comment per unique issue. Do not post duplicate comments.**

Use this list when evaluating issues in Steps 4 and 5 (these are false positives, do NOT flag):

- Pre-existing issues
- Something that appears to be a bug but is actually correct
- Pedantic nitpicks that a senior engineer would not flag
- Issues that a linter will catch (do not run the linter to verify)
- General code quality concerns (e.g., lack of test coverage, general security issues) unless explicitly required in CLAUDE.md
- Issues mentioned in CLAUDE.md but explicitly silenced in the code (e.g., via a lint ignore comment)

**Note:** Architectural violations that ARE documented in CLAUDE.md (dependency injection, logging architecture, etc.) SHOULD be flagged.

Notes:

- Use gh CLI to interact with GitHub (e.g., fetch pull requests, create comments). Do not use web fetch.
- Create a todo list before starting.
- You must cite and link each issue in inline comments (e.g., if referring to a CLAUDE.md, include a link to it).
- If no issues are found, post a comment with the following format:

---

## Code review

No issues found. Checked for bugs, CLAUDE.md compliance, dependency injection patterns, and logging architecture.

---

## Output Location

Write the review to: `~/obsidian-vaults/padnos/2-areas/software/pr-review/{repo-name}/{pr-number}/review_{number}.md`

Use this structure:

- PR title and link
- Summary of changes
- [Your existing template sections]

**Do not post to GitHub.** Write to filesystem only.

---

## Pre-Review: Check Template Compliance

**This step must complete BEFORE any code review begins.**

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

4. If template compliance fails:

   - Print warning to CLI: "⚠️ PR does not follow the required template from BI-Dev-Guidelines. Please update PR with template."
   - Include link to template: https://github.com/PADNOS/BI-Dev-Guidelines/blob/main/templates/PULL-REQUEST-example.md
   - **STOP. Do not proceed with code review.**

5. If template compliance passes:

   - Note this in the review output
   - Proceed with remaining steps

---

- When linking to code in inline comments, follow the following format precisely, otherwise the Markdown preview won't render correctly: https://github.com/anthropics/claude-code/blob/c21d3c10bc8e898b7ac1a2d745bdc9bc4e423afe/package.json#L10-L15
  - Requires full git sha
  - You must provide the full sha. Commands like `https://github.com/owner/repo/blob/$(git rev-parse HEAD)/foo/bar` will not work, since your comment will be directly rendered in Markdown.
  - Repo name must match the repo you're code reviewing
  - # sign after the file name
  - Line range format is L[start]-L[end]
  - Provide at least 1 line of context before and after, centered on the line you are commenting about (eg. if you are commenting about lines 5-6, you should link to `L4-7`)