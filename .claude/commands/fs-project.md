---
description: Look up a Freshservice project task and its notes
argument-hint: <task_key>
---

Look up a Freshservice project task by its display key from the
SQ2 data warehouse. Show task details and notes.

**Task key:** `$ARGUMENTS`

## Connection

- Credentials: `~/.config/padsql/.env.sq2` (1Password CLI)
- Server: `SQ2`
- Database: `Fivetran`
- Resolve credentials with `op run`:
  ```
  op run --env-file ~/.config/padsql/.env.sq2 -- \
    bash -c 'sqlcmd -S SQ2 -d Fivetran \
      -U "$PADSQL_USER" -P "$PADSQL_PASSWORD" \
      -s "|" -W -i /tmp/fs-project-query.sql'
  ```

## Workflow

1. Validate that a task key was provided (e.g., IS26-123).
   If missing or invalid, ask for one.

2. **Query 1 — Task details.** Write this SQL to a temp
   file and execute via sqlcmd. Replace `<KEY>` with the
   task key:
   ```sql
   SELECT *
   FROM freshservice_extensibility.project_task
   WHERE task_key = '<KEY>'
   ```

3. **Query 2 — Task notes.** Write this SQL to a temp
   file and execute via sqlcmd. Replace `<KEY>` with the
   task key:
   ```sql
   SELECT
       p.[key] AS project_key,
       n.user_email_id AS note_author,
       n.body AS note_body,
       n.attachments AS note_attachments,
       n.created_at AS note_created_at
   FROM freshservice.custom_stage_project_task AS pt
       INNER JOIN freshservice.custom_stage_project AS p
           ON pt.project_id = p.id
       LEFT JOIN freshservice.custom_stage_project_task_note AS n
           ON pt.id = n.task_id
   WHERE pt.display_key = '<KEY>'
   ORDER BY n.created_at
   ```

## Execution notes

- Write SQL to `/tmp/fs-project-details.sql` and
  `/tmp/fs-project-notes.sql` to avoid shell quoting
  issues with single quotes in SQL
- Use `-s "|" -W` flags for pipe-delimited, trimmed output
- Run both queries — task details first, then notes
- Strip HTML tags from note_body
