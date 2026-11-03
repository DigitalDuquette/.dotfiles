---
description: Read current state of a Freshservice project by rock goal
argument-hint: [project_key] [person] [--sprint <name>] [--days N]
---

Read where a Freshservice project stands right now, grouped by
rock goal, from the SQ2 data warehouse. Answers "where are we"
for a mono-project year, not "what is this one task."

**Arguments:** `$ARGUMENTS`

## Argument handling

All optional. Parse loosely from free text:

- **Project key** — `IS26`, `OPS26`, `IS27`. Default `IS26`.
  One project per team per year: `IS` = Information Solutions,
  `OPS` = IT Operations.
- **Person** — a surname or `Last, First`. Filters the sprint
  body and the movement list to that assignee. The rollup and
  flags stay project-wide so the person is shown in context.
- **`--sprint <name>`** — exact `sprint_name`, e.g.
  `July Sprint 26.7.1`. Default is the sprint whose date range
  contains today.
- **`--days N`** — movement lookback. Default 7.

If the arguments are ambiguous, say which reading you took and
run it. Do not stop to ask.

## Connection

- Credentials: `~/.config/padsql/.env.sq2` (1Password CLI)
- Server: `SQ2`
- Database: `Fivetran`
- Resolve credentials with `op run`:
  ```
  op run --env-file ~/.config/padsql/.env.sq2 -- \
    bash -c 'sqlcmd -S SQ2 -d Fivetran \
      -U "$PADSQL_USER" -P "$PADSQL_PASSWORD" \
      -s "|" -W -y 45 -i <query.sql>'
  ```
- If `op` returns `authorization timeout`, retry once. It is a
  biometric prompt that expired, not a failure.

## Data model

Four levels, per `dev-guidelines/tools/freshservice/README.md`:

1. **Project** — one per team per year (`project_key`).
2. **Task List** — a rock goal, team or company. In
   Freshservice this is a task type. The warehouse flattens
   it: a task list is attached to a task card, so it arrives
   as the `task_list` string on that card and no warehouse row
   carries `task_type = 'Task List'`. Never filter on that
   value. `task_list_status` carries the rock's own status.
   **A task does not have to belong to a rock goal.** Plenty
   of real work sits outside one on purpose. Blank `task_list`
   is a category, not a gap.
3. **Task** — `task_type` sets the priority class:
   `Project` = A (business-facing), `Task` = B (internal),
   `Issue` = C (defect).
4. **Sub Task** — `task_type = 'Sub Task'`, linked to its
   parent by `parent_task` matching the parent's `task_title`.
   A parent that has subtasks is elevated above other
   standalone tasks; mark it, do not assign it a letter.

Real column values in `freshservice_extensibility.project_task`:

- `task_status`: `Open`, `In Progress`, `UAT`, `Blocked`,
  `Waiting on someone else`, `Backlog`, `Parking Lot`, `Closed`.
  Only `Closed` is done. Group the rest as **active**
  (`In Progress`, `UAT`), **queued** (`Open`, `Backlog`),
  **stalled** (`Blocked`, `Waiting on someone else`), and
  **deferred** (`Parking Lot`).
- `task_priority` is set only when someone deliberately picks
  one. Blank is the default and reads as **Medium**. Render it
  that way; do not report blanks as missing data. Class
  (`task_type`) and subtask presence carry the ordering;
  `task_priority` refines within a class, and `Urgent` is the
  one value worth calling out on its own.
- `planned_end_date` drifts. Dates are not maintained closely
  and a past due date usually means the date is stale, not
  that the work is late. Report overdue counts, but never
  build the read on them or describe a task as late.
- Sprints are calendar months named `Month Sprint YY.M.1`. The
  numeric part is unreliable (February 2026 is `26.1.1`). Parse
  the month **name**, or use the sprint date range.

## Workflow

Write each query to its own temp file and run it. Replace
`<PROJECT>` with the resolved project key everywhere.

### Query 1 — Header and rock rollup

`/tmp/fs-status-rollup.sql`:

```sql
DECLARE @project VARCHAR(20) = '<PROJECT>';

SELECT
    p.[key] AS project_key, p.name AS project_name,
    p.start_date, p.end_date,
    s.title AS current_sprint,
    CAST( s.planned_start_date AS DATE ) AS sprint_start,
    CAST( s.planned_end_date AS DATE ) AS sprint_end
FROM freshservice.project AS p
    LEFT JOIN freshservice.project_sprint AS s
        ON s.project_id = p.id
       AND CAST( GETDATE( ) AS DATE ) >= CAST( s.planned_start_date AS DATE )
       AND CAST( GETDATE( ) AS DATE ) < CAST( s.planned_end_date AS DATE )
WHERE p.[key] = @project;

SELECT
    ISNULL( NULLIF( task_list, '' ), '(no rock goal)' ) AS rock,
    MAX( task_list_status ) AS rock_status,
    COUNT(*) AS total,
    SUM( CASE WHEN task_status = 'Closed' THEN 1 ELSE 0 END ) AS closed,
    SUM( CASE WHEN task_status <> 'Closed' THEN 1 ELSE 0 END ) AS open_n
FROM freshservice_extensibility.project_task
WHERE project_key = @project
GROUP BY ISNULL( NULLIF( task_list, '' ), '(no rock goal)' )
ORDER BY open_n DESC, total DESC;
```

### Query 2 — Current sprint by rock goal

The body of the report. `/tmp/fs-status-sprint.sql`:

```sql
DECLARE @project VARCHAR(20) = '<PROJECT>';

WITH resolved AS (
    SELECT
        t.task_key, t.task_title, t.task_type, t.task_status,
        t.task_priority, t.assigned_to, t.sprint_start_date,
        t.sprint_end_date, t.planned_end_date, t.parent_task,
        COALESCE( NULLIF( t.task_list, '' ),
                  NULLIF( par.task_list, '' ) ) AS rock,
        COALESCE( NULLIF( t.task_list_status, '' ),
                  NULLIF( par.task_list_status, '' ) ) AS rock_status
    FROM freshservice_extensibility.project_task AS t
        LEFT JOIN freshservice_extensibility.project_task AS par
            ON par.project_key = t.project_key
           AND par.task_title = t.parent_task
           AND par.task_type <> 'Sub Task'
    WHERE t.project_key = @project
)
SELECT
    ISNULL( r.rock, '(no rock goal)' ) AS rock,
    CASE WHEN r.rock IS NULL THEN 1 ELSE 0 END AS rock_sort,
    ISNULL( r.rock_status, '' ) AS rock_status,
    CASE r.task_type
        WHEN 'Project' THEN 'A' WHEN 'Task' THEN 'B'
        WHEN 'Issue' THEN 'C' WHEN 'Sub Task' THEN '.' ELSE '?'
    END AS pri,
    CASE WHEN kid.task_key IS NOT NULL THEN '*' ELSE '' END AS elev,
    r.task_key, r.task_status,
    ISNULL( NULLIF( r.task_priority, '' ), 'Medium' ) AS task_priority,
    NULLIF( r.assigned_to, '' ) AS assigned_to,
    CAST( r.planned_end_date AS DATE ) AS due,
    CASE WHEN r.planned_end_date < GETDATE( )
         THEN DATEDIFF( DAY, r.planned_end_date, GETDATE( ) )
    END AS overdue_days,
    r.parent_task, r.task_title
FROM resolved AS r
    OUTER APPLY (
        SELECT TOP 1 c.task_key
        FROM freshservice_extensibility.project_task AS c
        WHERE c.project_key = @project
          AND c.task_type = 'Sub Task'
          AND c.parent_task = r.task_title
    ) AS kid
WHERE r.task_status <> 'Closed'
  AND CAST( GETDATE( ) AS DATE ) >= CAST( r.sprint_start_date AS DATE )
  AND CAST( GETDATE( ) AS DATE ) < CAST( r.sprint_end_date AS DATE )
ORDER BY rock_sort, rock, pri, r.task_status, r.task_key;
```

For `--sprint <name>`, replace the two `sprint_start_date` /
`sprint_end_date` date predicates with
`r.sprint_name = '<SPRINT>'`.

### Query 3 — Health flags and load

`/tmp/fs-status-flags.sql`:

```sql
DECLARE @project VARCHAR(20) = '<PROJECT>';

WITH t AS (
    SELECT *,
        CASE WHEN CAST( GETDATE( ) AS DATE )
                     >= CAST( sprint_start_date AS DATE )
              AND CAST( GETDATE( ) AS DATE )
                     < CAST( sprint_end_date AS DATE )
             THEN 1 ELSE 0 END AS in_sprint
    FROM freshservice_extensibility.project_task
    WHERE project_key = @project AND task_status <> 'Closed'
)
SELECT 'composition' AS band, 'open tasks (all sprints)' AS metric,
       COUNT(*) AS n FROM t
UNION ALL SELECT 'composition', 'open in current sprint', COUNT(*)
    FROM t WHERE in_sprint = 1
UNION ALL SELECT 'composition', 'under a rock goal (open)', COUNT(*)
    FROM t WHERE ISNULL( task_list, '' ) <> ''
UNION ALL SELECT 'composition', 'outside a rock goal (open)', COUNT(*)
    FROM t WHERE ISNULL( task_list, '' ) = ''
UNION ALL SELECT 'composition', 'unsprinted (open)', COUNT(*)
    FROM t WHERE ISNULL( sprint_name, '' ) = ''
UNION ALL SELECT 'attention', 'unassigned (current sprint)', COUNT(*)
    FROM t WHERE in_sprint = 1 AND ISNULL( assigned_to, '' ) = ''
UNION ALL SELECT 'attention', 'Parking Lot inside current sprint',
       COUNT(*)
    FROM t WHERE in_sprint = 1 AND task_status = 'Parking Lot'
UNION ALL SELECT 'attention', 'Blocked / Waiting (current sprint)',
       COUNT(*)
    FROM t WHERE in_sprint = 1
      AND task_status IN ( 'Blocked', 'Waiting on someone else' )
UNION ALL SELECT 'date hygiene', 'past planned end (current sprint)',
       COUNT(*)
    FROM t WHERE in_sprint = 1 AND planned_end_date < GETDATE( )
UNION ALL SELECT 'date hygiene', 'no due date (current sprint)',
       COUNT(*)
    FROM t WHERE in_sprint = 1 AND planned_end_date IS NULL
UNION ALL SELECT 'date hygiene', 'sprint ended, still open', COUNT(*)
    FROM t WHERE sprint_end_date < GETDATE( );

SELECT
    ISNULL( NULLIF( assigned_to, '' ), '(unassigned)' ) AS assignee,
    COUNT(*) AS open_n,
    SUM( CASE WHEN planned_end_date < GETDATE( )
              THEN 1 ELSE 0 END ) AS stale_date_n,
    SUM( CASE WHEN task_status IN ( 'Blocked', 'Waiting on someone else' )
              THEN 1 ELSE 0 END ) AS stalled_n
FROM freshservice_extensibility.project_task
WHERE project_key = @project AND task_status <> 'Closed'
  AND CAST( GETDATE( ) AS DATE ) >= CAST( sprint_start_date AS DATE )
  AND CAST( GETDATE( ) AS DATE ) < CAST( sprint_end_date AS DATE )
GROUP BY ISNULL( NULLIF( assigned_to, '' ), '(unassigned)' )
ORDER BY open_n DESC;
```

### Query 4 — Movement since N days ago

Daily snapshots run back to Feb 2025. `/tmp/fs-status-move.sql`:

```sql
DECLARE @project VARCHAR(20) = '<PROJECT>';
DECLARE @days INT = <DAYS>;

WITH bounds AS (
    SELECT MAX( CAST( snapshot_datetime AS DATE ) ) AS d_now
    FROM freshservice_extensibility.project_task_snapshot
    WHERE project_key = @project
),
w AS (
    SELECT b.d_now, MAX( CAST( s.snapshot_datetime AS DATE ) ) AS d_then
    FROM freshservice_extensibility.project_task_snapshot AS s
        CROSS JOIN bounds AS b
    WHERE s.project_key = @project
      AND CAST( s.snapshot_datetime AS DATE )
          <= DATEADD( DAY, -@days, b.d_now )
    GROUP BY b.d_now
),
now_snap AS (
    SELECT s.task_key, s.task_title, s.task_status, s.task_list,
           s.sprint_name, s.assigned_to
    FROM freshservice_extensibility.project_task_snapshot AS s
        JOIN w ON CAST( s.snapshot_datetime AS DATE ) = w.d_now
    WHERE s.project_key = @project
),
then_snap AS (
    SELECT s.task_key, s.task_status, s.task_list, s.sprint_name
    FROM freshservice_extensibility.project_task_snapshot AS s
        JOIN w ON CAST( s.snapshot_datetime AS DATE ) = w.d_then
    WHERE s.project_key = @project
)
SELECT
    CASE
        WHEN t.task_key IS NULL THEN 'NEW'
        WHEN n.task_status = 'Closed'
             AND t.task_status <> 'Closed' THEN 'CLOSED'
        WHEN n.task_status <> t.task_status THEN 'STATUS'
        WHEN ISNULL( n.sprint_name, '' )
             <> ISNULL( t.sprint_name, '' ) THEN 'ROLLED'
        WHEN ISNULL( n.task_list, '' )
             <> ISNULL( t.task_list, '' ) THEN 'REROCKED'
    END AS change,
    n.task_key,
    ISNULL( NULLIF( t.task_status, '' ), '-' ) AS was,
    n.task_status AS now_status,
    ISNULL( NULLIF( n.task_list, '' ), '(no rock)' ) AS rock,
    ISNULL( NULLIF( n.assigned_to, '' ), '(unassigned)' ) AS assignee,
    n.task_title
FROM now_snap AS n
    LEFT JOIN then_snap AS t ON t.task_key = n.task_key
WHERE t.task_key IS NULL
   OR n.task_status <> t.task_status
   OR ISNULL( n.sprint_name, '' ) <> ISNULL( t.sprint_name, '' )
   OR ISNULL( n.task_list, '' ) <> ISNULL( t.task_list, '' )
ORDER BY change, n.task_key;
```

## Presenting

Plain text, no tables wider than the terminal. Order:

1. **Header** — project name, today, current sprint and its
   dates, days left in the sprint.
2. **Current sprint by rock goal** — one block per rock, rock
   status in brackets. Within a rock, order A, B, C, then
   subtasks under their parent. Per line: priority letter,
   `*` if the task has subtasks, task key, title, status,
   assignee. Add `date +Nd` when `planned_end_date` has passed,
   phrased as a date-staleness marker, never as "late". Put
   `(no rock goal)` last and never omit it: that work is
   deliberate, so give it the same treatment as a rock.
3. **Movement** — the differentiator, since the Tableau
   dashboard already shows current state. Group as CLOSED /
   STARTED / ROLLED / NEW / REROCKED. `STATUS` rows moving into
   `In Progress` are STARTED; the rest are status changes.
4. **Counts** — Query 3 in its three bands, then the assignee
   load table. Print the band labels. `composition` describes
   the shape of the project and needs no comment.
   `date hygiene` is a known, accepted weakness: show the
   numbers and move on.
5. **Read** — three to five sentences. Draw only on the
   `attention` band, the movement list, and the load table.
   Name the rock carrying the year, any rock with no
   current-sprint activity, and anyone whose stalled count is
   a large share of their open count.

Things that are **not** findings. Do not raise them:

- Tasks with no rock goal. Rock membership is optional by
  design; a high share outside a rock is normal.
- Past planned end dates. Dates drift by acknowledged habit.
- Blank `task_priority`. That is the Medium default.

## Execution notes

- Write SQL to temp files, one per query, to avoid shell
  quoting problems with the single quotes in the SQL.
- Use `-s "|" -W` for pipe-delimited, trimmed output.
- `-y 45` is enough here; task titles are short. Raise it only
  if titles are visibly truncated.
- Run all four queries. Do not skip Query 4 because Query 2
  looked complete: current state without movement cannot tell
  a stalled rock from a finished one.
- **Never filter out blank `task_list`.** The shared queries in
  `SQL-Query-Library/Business-Application/Freshservice/` use
  `task_list != ''` because they are scoped to rock reporting.
  This command is scoped to the whole project, and work outside
  a rock is real work. Dropping it reports a smaller project
  than the one that exists.
- Subtask rock inheritance via `parent_task` is best-effort and
  resolves nothing when the parent also sits outside a rock.
  Keep it: it is correct when the parent has one.
- The Tableau **Freshservice Project Dashboard** (workbook
  `4892d99b-e773-4e12-ae65-301770bb93c1`, views: Current
  Sprint, Planned vs Capacity, Roadmap, Planned - Future
  Sprints, Parking Lot - Not Planned) covers current state
  visually and adds planned-days-vs-capacity per person. That
  capacity figure comes from a separate planning workbook and
  is **not in the warehouse**, so this command cannot compute
  utilization. Point at the dashboard when asked about
  capacity.
- `project_task_snapshot.rock_list` and `.task_rank` are NULL
  for every row. Ignore both columns.
- Read only. Writing quarterly updates is `/1ppp`. Ticket
  detail is `/fs-ticket`. Single-task detail is `/fs-project`.
