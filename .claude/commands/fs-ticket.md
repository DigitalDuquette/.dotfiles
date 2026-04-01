---
description: Look up a Freshservice ticket and its conversations
argument-hint: <ticket_number>
---

Look up a Freshservice ticket by number from the SQ2 data
warehouse. Show ticket details and conversation history.

**Ticket number:** `$ARGUMENTS`

## Connection

- Credentials: `~/.config/padsql/.env.sq2` (1Password CLI)
- Server: `SQ2`
- Database: `Fivetran`
- Resolve credentials with `op run`:
  ```
  op run --env-file ~/.config/padsql/.env.sq2 -- \
    bash -c 'sqlcmd -S SQ2 -d Fivetran \
      -U "$PADSQL_USER" -P "$PADSQL_PASSWORD" \
      -s "|" -W -i /tmp/fs-ticket-query.sql'
  ```

## Workflow

1. Validate that a ticket number was provided and is
   numeric. If missing or invalid, ask for one.

2. **Query 1 — Ticket details.** Write this SQL to a temp
   file and execute via sqlcmd. Replace `<N>` with the
   ticket number:
   ```sql
   SELECT
       ticket_number, workspace, subject, status, priority,
       type, category, sub_category, source,
       requestor, requested_for, responder,
       created_date, updated_at, due_by,
       resolved_at, closed_at, first_responded_at,
       time_to_resolve_minutes, time_spent_minutes
   FROM freshservice_extensibility.v_ticket
   WHERE ticket_number = <N>
   ```

3. **Query 2 — Conversations.** Write this SQL to a temp
   file and execute via sqlcmd. Replace `<N>` with the
   ticket number:
   ```sql
   SELECT
       c.id,
       COALESCE(
           CONCAT(r.last_name, ', ', r.first_name),
           CONCAT(a.last_name, ', ', a.first_name),
           CAST(c.user_id AS VARCHAR)
       ) AS author,
       c.body_text,
       CASE c.incoming
           WHEN 1 THEN 'Incoming' ELSE 'Outgoing'
       END AS direction,
       CASE c.private
           WHEN 1 THEN 'Private' ELSE 'Public'
       END AS visibility,
       c.created_at
   FROM freshservice.custom_ticket_conversation AS c
       LEFT JOIN freshservice.custom_stage_requester AS r
           ON c.user_id = r.id
       LEFT JOIN freshservice.custom_stage_agent AS a
           ON c.user_id = a.id
   WHERE c.ticket_id = <N>
   ORDER BY c.created_at
   ```

4. **Present results:**
   - Show ticket details as a structured summary, not a
     raw table — pull out key fields clearly
   - Show conversations in chronological order with
     author, direction (incoming/outgoing), visibility
     (public/private), and timestamp
   - Strip HTML tags from body_text if present
   - If no ticket found, say so
   - If no conversations found, note that only
     Information Solutions workspace conversations are
     synced to the warehouse

## Execution notes

- Write SQL to `/tmp/fs-ticket-details.sql` and
  `/tmp/fs-ticket-conversations.sql` to avoid shell
  quoting issues with single quotes in SQL
- Use `-s "|" -W` flags for pipe-delimited, trimmed output
- Run both queries — ticket details first, then
  conversations
