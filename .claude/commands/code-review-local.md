---
allowed-tools: Bash(gh issue view:*), Bash(gh search:*), Bash(gh issue list:*), Bash(gh pr diff:*), Bash(gh pr view:*), Bash(gh pr list:*), Bash(gh repo view:*), Bash(gh api:*), Bash(git fetch:*), Bash(git worktree:*), Bash(padsql-exec:*), Bash(padsql-deploy:*), Bash(ssh rhel-dev-local01:*), Read(~/obsidian-vault/padnos/**), Write(~/obsidian-vault/padnos/**), Glob(~/obsidian-vault/padnos/**), Grep(~/obsidian-vault/padnos/**), Read(/Users/jjduqu/Library/Mobile Documents/iCloud~md~obsidian/Documents/padnos/**), Write(/Users/jjduqu/Library/Mobile Documents/iCloud~md~obsidian/Documents/padnos/**), Glob(/Users/jjduqu/Library/Mobile Documents/iCloud~md~obsidian/Documents/padnos/**), Grep(/Users/jjduqu/Library/Mobile Documents/iCloud~md~obsidian/Documents/padnos/**), Read(/Users/jjduqu/Developer/GitHub/**), Glob(/Users/jjduqu/Developer/GitHub/**), Grep(/Users/jjduqu/Developer/GitHub/**)
description: Code review a pull request against team standards, with gated live verification
argument-hint: "[REPO] <PR_NUMBER>"
---

Review pull request: $ARGUMENTS

The review runs in stages. Stage 1 (standards review) always runs.
Stage 2 (live verification) runs ONLY if stage 1 passes AND the PR
has a shape worth verifying. Never verify code that failed the
standards review — "it runs" is not a rebuttal to "it's the wrong
shape."

**Argument parsing:**

I was given: $ARGUMENTS

- If two arguments (format: REPO PR_NUMBER): Use REPO=$0 and
  PR_NUMBER=$1
- If one argument (format: PR_NUMBER): Use PR_NUMBER=$0 and get REPO
  from `gh repo view --json nameWithOwner -q .nameWithOwner`

---

## Stage 1 — Standards review (always)

1. Get PR metadata:
   - PR title, URL: `gh pr view -R <REPO> <PR_NUMBER> --json title,url`
   - Head branch ref: `gh pr view -R <REPO> <PR_NUMBER> --json headRefName -q .headRefName`
   - Changed files: `gh pr view -R <REPO> <PR_NUMBER> --json files -q '.files[].path'`
   - PR body: `gh pr view -R <REPO> <PR_NUMBER> --json body -q .body`

2. **Route to the live team standards.** The standards live in the
   local dev-guidelines checkout at
   `/Users/jjduqu/Developer/GitHub/dev-guidelines` (run
   `git -C <path> fetch && git -C <path> log -1 origin/main --format=%cr`
   and note if the local checkout looks stale). Based on the changed
   file types, read the matching docs BEFORE reviewing — review
   against what they say today, not from memory:

   | Changed files | Read |
   |---|---|
   | Stored procs, DDL, deploy_order (`*.sql` under `production/` or `sql/source|target/`) | `guidelines/architecture/sql-first-elt.md`, `languages/sql/stored-procedures/README.md` |
   | Pipeline code (`pipeline/*/` — `.py`, `sql/duckdb/*.sql`, `cron`, `.env.*.example`, `requirements.txt`) | `guidelines/architecture/sql-first-elt.md`, `guidelines/architecture/mssql-to-mssql-pipelines.md`, `languages/python/` README if present |
   | Docs, README, AGENTS.md only | `guidelines/documentation/README.md` |
   | Anything else | `guidelines/README.md` index — follow what applies |

   Also read any AGENTS.md / CLAUDE.md in the PR's own repo
   directories touched by the diff (fetch via `gh api` from the head
   ref) — component-local context overrides general rules.

3. Get the PR diff: `gh pr diff -R <REPO> <PR_NUMBER>`

4. Get file contents from GitHub (NOT the local filesystem):
   - `gh api repos/<REPO>/contents/<FILE_PATH>?ref=<HEAD_REF> --jq '.content' | base64 -d`
   - This ensures you review the actual PR code, not stale local
     files. Only fetch files when you need context beyond the diff.

5. **Understand what the PR does FIRST:**
   - What problem is this PR solving?
   - Is this a new feature, bug fix, refactor, or hotfix?
   - What's the context (new code vs. fixing existing trash)?
   - Read the PR description and linked issues to understand intent

6. **Explain the code changes:**
   - What technical changes are being made?
   - What patterns/libraries/approaches are being used?
   - How does this implementation solve the problem?

7. **Review for problems with the changes:**
   - **Bugs:** Syntax errors, logic errors, will-break issues only
     (not style/nitpicks)
   - **DRY violations:** Repeated code that should be extracted
   - **SOLID violations:** Especially Single Responsibility
     violations (new god classes, making existing ones worse)
   - **Shape violations** (these are the gate for stage 2 — check
     against the routed docs, and cite the doc when flagging):
     - Business logic living in Python or in `sql/duckdb/*.sql`
       instead of in stored procs — Python is the thin orchestrator
       (sql-first-elt.md)
     - Procs skipping the earned patterns: temp tables as
       inspectable stages, dry-run by default
       (`@push_to_prod`-style gate), update-then-insert and never
       MERGE, state-machine staging columns (`is_processed`,
       `has_error`, `error_message`)
     - Pipelines breaking the canonical anatomy: entrypoint, `cron`,
       `.env.dev.example` + `.env.prod.example`, `requirements.txt`,
       `sql/` split, `deploy_order` per side
   - **Context-appropriate severity:** Performance nitpicks and code
     cleanliness don't block hotfixes on known-bad code

8. **Interrogate Testing Performed.** Read the PR body's testing
   claims critically against the diff:
   - Which risky paths does the diff touch, and does a claim cover
     each? A new guard rail with no claimed test that exercises it
     is a finding.
   - Are the claims plausible and specific (server, data, observed
     result), or vague ("tested locally")?
   - List every load-bearing claim — a claim the approval would rest
     on. Stage 2, if it runs, verifies the top one or two of these.

---

## Gate — decide whether stage 2 runs

- Any shape violation or bug found → **stop after writing the
  review file.** Status: ISSUES FOUND. Do not verify; the run would
  be spent on code that needs restructuring anyway.
- Stage 1 clean (or notes-only) → pick the verification lane:
  - **Proc lane:** diff centers on stored procs with guard rails
    and a `deploy_order` targeting a dev server
  - **Pipeline lane:** diff touches a `pipeline/<name>/` directory's
    runtime (Python, duckdb SQL, cron, requirements)
  - **No lane:** docs, config, or business-rule value tweaks —
    stage 1 was the whole review. Write the file and finish.
- If a PR fits both lanes, run the proc lane first (the pipeline
  run depends on the procs), then the pipeline lane.

---

## Stage 2A — Proc lane (padsql-exec verification)

Follow the padsql agent contract
(`dev-guidelines/tools/padsql/padsql-exec-agents.md`). Dev servers
only (`tsq1`, `tsq2`, `mssql-dev-01`, `mssql-dev-02`); never pass
`--allow-prod`; a refusal is the tool working.

1. Create a worktree of the PR branch (do not disturb the main
   checkout):
   `git -C ~/Developer/GitHub/<repo> fetch origin <HEAD_REF> && git -C ~/Developer/GitHub/<repo> worktree add <scratchpad>/pr-<PR_NUMBER> FETCH_HEAD`
2. Deploy the component from the worktree via `padsql-deploy` (its
   `deploy_order` declares the dev server/db). Note in the review
   that the dev copy of the proc now reflects the PR branch.
3. Verify ONLY the top 1–2 load-bearing claims from step 8 — this
   is targeted verification, not an exhaustive battery. Typical
   picks: dry-run purity (test-mode flag writes zero rows — prove
   with before/after counts, never trust the proc's own summary) or
   the specific guard rail the PR adds (raises its documented
   error, and the RIGHT error).
4. Mechanics: each padsql-exec call is one connection, so every
   scratch `.sql` must be self-contained (setup + EXEC +
   verification SELECTs). Scratch files go to the session
   scratchpad, never into a repo. Expected-error cases: assert
   non-zero exit and the error text.
5. Tag any test rows distinctively, delete them when done, prove
   deletion with a count. If test-mode runs suffice, prefer them —
   write nothing at all.
6. Remove the worktree when finished:
   `git -C ~/Developer/GitHub/<repo> worktree remove <scratchpad>/pr-<PR_NUMBER>`

## Stage 2B — Pipeline lane (rhel-dev-local01 run)

1. Check the VM is up: `ssh rhel-dev-local01 true`. If unreachable,
   note "verification skipped: rhel-dev-local01 unreachable" in the
   review and finish with the stage 1 result — degraded, not
   blocked. (Ask me to boot it if the verification matters for this
   PR.)
2. Create the PR worktree as in 2A step 1.
3. Deploy the pipeline directory to the VM using the box's standard
   deploy path (`deploy-pipeline.sh` from the RHEL runbooks — it
   handles venv, requirements, and `op inject` with dev creds from
   the `-dev-`/local hostname split). Do not invent a second deploy
   mechanism; if the box's tooling is missing or broken, report
   that as the finding instead of working around it.
4. Run the pipeline WITHOUT `--push-to-prod` — staging-only writes,
   full real path (creds, DuckDB attach, proc calls, sync).
5. Collect evidence:
   - exit code
   - `logs/app.log` tail — step heartbeats, errors
   - staging outcomes verified independently via padsql-exec
     against the dev server (row counts, `has_error` rows), not
     just the pipeline's own logging
6. Clean up: remove the deployed PR copy from the VM if it replaced
   nothing, or note that the VM now runs the PR version. Remove the
   local worktree.

---

## Write the review file

Write to:
`~/obsidian-vault/padnos/2-areas/software/pr-review/{repo-name}/PR-{pr-number}.md`

- If the file already exists: append after a `---` separator as
  "Review {N}" (count existing `## Review` headings; first append
  is Review 2). Nest subsections under the Review heading (`###
  Findings`, `#### Bugs`, etc.).
- Do NOT post to GitHub — filesystem only. I check the code and add
  the GitHub review comments myself.

### Format (first review)

```markdown
# PR-{number}: {title}

**Link:** {github-url}

**Status:** LOOKS GOOD | ISSUES FOUND

**Standards reviewed against:** {list the dev-guidelines docs read}

## Findings

{If none: "No violations found."}

### Bugs
- `file.py:123` - Brief description (1 sentence)

### Shape Violations
- `pipeline/x/x.py:88` - Business logic in orchestrator; belongs in
  a proc (sql-first-elt.md)

### DRY Violations
### SOLID Violations

### Testing Gaps
- New truncation guard at `proc.sql:214` has no claimed test in
  Testing Performed

## Verification

{One of:}
{- "Not run: stage 1 found issues."}
{- "Not run: no verification lane fits this PR."}
{- "Skipped: rhel-dev-local01 unreachable."}
{- Evidence table:}

| # | claim verified | method | observed | verdict |
|---|---|---|---|---|

{FAIL rows quote observed evidence verbatim — error text, counts.}
{Note cleanup: test rows removed (count), worktree removed, VM
state.}

## Notes

**What this PR does:**
**Code changes:**
**Minor observations (not blocking):**
```

---

## What NOT to flag (false positives)

- Pre-existing issues not introduced by this PR
- Style/quality concerns unless the routed standards require them
- Issues that depend on runtime state or specific inputs
- Anything a linter would catch
- Nitpicks a senior engineer would ignore

**Common false positives to avoid:**

- **Module-level config loading**: Standard practice for
  application entry points (files with `if __name__ ==
  '__main__'`). Only flag if it's a library module meant to be
  imported.
- **API client classes**: A class that wraps an API (setup, call
  API, parse response) is ONE responsibility, not a SOLID
  violation. Don't confuse "multiple steps" with "multiple
  responsibilities."
- **Cohesive workflows**: Database operations that are part of one
  logical workflow (e.g., initialize_queue running 6 setup queries)
  are NOT DRY violations. That's just how workflows work.
- **SQL file organization**: Separating SQL into .sql files with
  descriptive names is GOOD organization, not a maintainability
  problem. Don't flag this as "separated from usage."
- **Contextual constants**: Simple limits like `[:10]` for claim
  keys or `[:150]` for note truncation aren't "magic numbers" worth
  flagging if the context is clear.
- **Defensive error handling**: Edge case error handling for stable
  APIs (bounds checking, type validation) is nice-to-have, not
  critical. Only flag actual bugs that will break in normal
  operation.
- **Line numbers**: Always verify line numbers are from the actual
  file, not the diff output. Check file length before citing line
  numbers.

**Critical thinking checklist:**

- Does this pattern exist for a good reason? (Don't flag patterns
  without understanding WHY)
- Would this actually break in production? (Theoretical edge cases
  ≠ critical bugs)
- Is this how senior engineers typically write this type of code?
  (Don't be overly dogmatic)
- Can I defend this finding if challenged? (Be ready to explain or
  retract)

**If uncertain whether something is a bug, frame it as a question
in the Notes section, not as a finding.**

**Notes:**

- Use gh CLI for ALL PR data (diff, files, metadata) — never read
  PR code from the local filesystem; local checkouts are only for
  dev-guidelines standards and the verification worktree.
- Keep it simple — no parallel agents, no excessive orchestration.
- Focus on high-signal issues only.
- Verification is targeted (1–2 claims), never exhaustive. If it
  starts sprawling, stop and report what you have.
