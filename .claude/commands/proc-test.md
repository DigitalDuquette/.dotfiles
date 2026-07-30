---
description: Adversarially test a SQL component on a dev server
argument-hint: <path to component folder>
allowed-tools: Bash(padsql-exec:*), Bash(padsql-deploy:*), Bash(cd:*), Read(//Users/jjduqu/Developer/GitHub/**), Glob(//Users/jjduqu/Developer/GitHub/**), Grep(//Users/jjduqu/Developer/GitHub/**)
---

Adversarially test the SQL component at the given path: deploy it to
its dev server, try to break it, verify its guard rails, clean up
every test row, and report a verdict.

**Component folder:** `$ARGUMENTS`

A component is a folder in a data-product repo containing a stored
proc as an idempotent CREATE OR ALTER script, a `deploy_order`
(header declares server/database), usually an `exec.sql` test
harness, a README documenting the caller contract, and sometimes
`docs/defaults-matrix.md` and an AGENTS.md naming dependencies.

Follow the padsql agent contract
(`dev-guidelines/tools/padsql/padsql-exec-agents.md`) throughout.

## Ground rules — read before phase 0

- **Dev servers only.** The padsql-exec dev allowlist is `tsq1`,
  `tsq2`, `mssql-dev-01`, `mssql-dev-02`. If the component's
  `deploy_order` declares any other server, STOP and tell the user.
  Never pass `--allow-prod`, never override the server to work
  around a refusal. A padsql-exec refusal is the tool working as
  designed. No exceptions.
- **The component repo is read-only.** Never edit, add, or delete
  any file in it — harness copies and all scratch SQL go to the
  session scratchpad directory, never into a repo.
- **Every test row gets cleaned up.** Tag all test data so it is
  recognizable (distinctive CREATESTATION/createuser value or key
  prefix); delete it in phase 5 and prove deletion with counts.
- **Never trust the proc's own reporting** for write/no-write
  claims — prove them with independent before/after counts.
- **Sequence hygiene.** Prefer test-mode runs and explicit test
  keys. When real control numbers must be generated (SMDEF-style
  counters), minimize how many and report the count consumed —
  they cannot be returned.

## Phase 0 — Recon (read-only)

1. Read everything in the component folder: the proc source, the
   README, `exec.sql`, `deploy_order`, `docs/defaults-matrix.md`
   and AGENTS.md if present.
2. Parse `server:` and `database:` from `deploy_order`. Apply the
   dev-allowlist check above — HARD REFUSAL on any miss.
3. If AGENTS.md or the README name dependency components (shared
   write procs, control-number generators — also check what
   `exec.sql` EXECs), locate their folders, read their
   `deploy_order`s, and apply the same allowlist check to each.
   Record the dependency order.
4. Catalog from the proc source and docs:
   - the parameter signature and the test-mode flag
     (`@push_to_prod`-style) and its semantics
   - every guard rail: RAISERROR/THROW sites and the condition
     that triggers each
   - every table the proc writes (INSERT/UPDATE/DELETE targets)
   - the outcome vocabulary (`inserted`, `skipped_existing`,
     `updated`, `not_found`, `blocked_posted`, or the component's
     equivalents)
5. Pick the test tag: a distinctive createuser-style value that
   fits the destination width (check in phase 2) plus a key prefix
   (e.g. `ZZ...`) for explicit test keys that cannot collide with
   real counter-issued keys. In phase 2, verify no pre-existing
   rows already carry the tag or prefix before writing anything.
6. Write the test plan as a case list before touching the server:
   category, setup, expectation. Phases 3–4 execute this list.

## Phase 1 — Deploy

1. For each dependency in dependency order, then the component
   itself:

   ```bash
   cd <component-folder> && padsql-deploy
   ```

2. padsql-deploy reads `deploy_order` in the current directory —
   run it from inside each folder, no flags. Stop on any failure;
   do not improvise around a broken deploy.

## Phase 2 — Schema recon

Ground the adversarial cases in real schema, not guesses. Via
`padsql-exec --server <s> --db <d> --query "..."`. Metadata queries
on large databases can exceed the default 30-second timeout — pass
`--timeout 120`, and prefer `sys.*` catalog views over
`information_schema` joins for key lookups:

1. Columns, widths, and nullability for every table the proc
   writes:

   ```sql
   SELECT column_name, data_type,
          character_maximum_length, is_nullable
   FROM information_schema.columns
   WHERE table_name = '<table>'
   ORDER BY ordinal_position
   ```

2. Primary keys (drives duplicate-key and idempotency cases):

   ```sql
   SELECT OBJECT_NAME( ic.object_id ) AS table_name,
          c.name AS column_name, ic.key_ordinal
   FROM sys.indexes AS i
       INNER JOIN sys.index_columns AS ic
           ON i.object_id = ic.object_id
              AND i.index_id = ic.index_id
       INNER JOIN sys.columns AS c
           ON ic.object_id = c.object_id
              AND ic.column_id = c.column_id
   WHERE i.is_primary_key = 1
         AND i.object_id IN ( OBJECT_ID( '<table>' ) )
   ORDER BY table_name, ic.key_ordinal
   ```

3. The deployed proc's signature (confirms the deploy landed and
   the documented parameters are real):

   ```sql
   SELECT p.name, TYPE_NAME( p.user_type_id ) AS type_name,
          p.max_length, p.has_default_value
   FROM sys.parameters AS p
   WHERE p.object_id = OBJECT_ID( '<schema.proc>' )
   ORDER BY p.parameter_id
   ```

4. If a counter table (SMDEF-style) feeds key generation, record
   its current value now so consumption can be reported in phase 6.

## Phase 3 — Happy path

1. Copy `exec.sql` to the scratchpad. In the copy only: enable any
   `IF 1 = 0` blocks, swap in the test tag and explicit test keys,
   and keep the run minimal (fewest counter numbers possible).
   Never edit the repo's `exec.sql`.
2. If the component has no harness, construct one in the
   scratchpad from the README caller contract.
3. Each padsql-exec invocation is one connection — session temp
   tables die between calls, so every scratch file must be
   self-contained (setup + EXEC + verification SELECTs in one
   file).
4. Run it: `padsql-exec --server <s> --db <d> --file <scratch>.sql`.
   When a run dumps wide stage tables (test-mode flags usually
   do), add `--out <scratch>.out` and Read/grep the file instead
   of flooding the transcript.
5. Verify the documented outcomes: result temp tables materialize,
   outcome columns hold the documented values, and the written
   rows actually exist (SELECT them back by test tag).

## Phase 4 — Adversarial battery

One scratch `.sql` per case (or small groups), each self-contained.
Two mechanics matter:

- sqlcmd stops at the first SQL error, so batching expected-error
  cases naively means only the first one runs. Either run one
  padsql-exec per error case (assert non-zero exit + stderr text),
  or batch them in one file with each EXEC wrapped in TRY/CATCH
  that SELECTs a case id and `ERROR_MESSAGE()` — and a
  NO-ERROR-FAIL marker on the success path so a guard that fails
  to fire is caught.
- A mid-file error still commits every autocommitted statement
  before it. Write each case so a re-run neither duplicates rows
  nor errors, and assert on counts, not on run-order assumptions.

Derive the concrete cases from the phase-0 guard-rail catalog and
phase-2 widths; cover at minimum:

1. **Dry-run purity.** With the test-mode flag off
   (`@push_to_prod = 0` or equivalent), the proc must write ZERO
   rows. Prove it: `COUNT(*)` on every target table before and
   after, inside the same scratch file. Do not accept the proc's
   own summary as evidence.
2. **Every documented guard rail** raises its specific error:
   unknown column, missing required column, truncation, duplicate
   key in the caller's input, placeholder values (`'GENERATE'`),
   posted-row blocks (`@block_posted`-style flags), invalid
   action/arguments — whatever phase 0 cataloged.
3. **Truncation boundaries.** Read the proc to see how the guard
   is implemented — value-level or DDL-level (caller column
   *declared* wider than the destination, values irrelevant) —
   and build the case accordingly. Exactly the destination width
   must pass; width + 1 must raise the truncation error.
4. **NULL vs empty string** on columns where the README documents
   a deliberate distinction (e.g. `CONTRACT = ''` vs NULL changing
   enrichment) — verify both sides of the distinction.
5. **Idempotent re-run.** Submit the same rows twice. Expect the
   component's skipped/existing outcome — never a PK violation,
   never a duplicate row (prove with a count).
6. **Update path** (where one exists): only caller-provided
   columns change (check an untouched column survives), LAST*
   columns are stamped, caller-supplied CREATE*/LAST* columns are
   rejected, and not-found rows are counted, not errored. Compose
   posted-row-block cases with the test-mode flag so no real row
   is touched.
7. **Defaults.** Where `docs/defaults-matrix.md` exists, verify a
   sample of documented defaults actually materialize on an
   inserted row (SELECT the row back and compare).

Record for every case: category, expectation, observed evidence
(error text or counts, quoted), PASS/FAIL. An error case passes
only on the RIGHT error — a different error is a FAIL.

## Phase 5 — Cleanup

1. DELETE every row carrying the test tag or key prefix from every
   target table (children before parents if FKs exist).
2. Verify: `COUNT(*)` by test tag on every target table must be 0.
3. Report anything that could not be removed, with the error.
4. Report counter consumption: current counter value vs phase 2,
   and how many numbers the run consumed. They cannot be returned;
   just report the count.

## Phase 6 — Report

1. Write a structured markdown report to the session scratchpad:
   - header: component, server/database, proc, date, deploy result
   - one table row per test case: `| # | category | expectation |
     observed | verdict |` — FAIL rows must quote the observed
     evidence verbatim (error text, counts)
   - cleanup confirmation: per-table before/after counts, plus
     counter numbers consumed
   - overall verdict: PASS only if every case passed and cleanup
     verified to zero
2. In chat: print the report path, the verdict table, and the
   overall verdict. This report is consumed as evidence by the
   code-review workflow — keep the format consistent and
   machine-skimmable.
