# Freshservice API v2 — PADNOS facts (verified against live data)

Domain `padnos.freshservice.com`. Auth: HTTP Basic, API key as username, `X` as password.

## Scope IDs

- Information Solutions `workspace_id = 3` (others: 2 IT, 6 Finance, 7 FP&A, 8 Security, 9 HR, 10 OES, 11 Op Support, 12 Marketing).
- IS agent groups: 23000071556 App Devs, 23000073825 CRM System Analyst, 23000071557 Data Devs, 23000071555 DBA, 23000287536 ERP System Analyst, 23000115068 Management, 23000071558 Report Devs.
- Status IDs (custom set; get labels from `GET ticket_form_fields?workspace_id=3`): 2 Open, 8 Open - Assigned, 6 In Progress, 3 Pending, 9 On Hold, 4 Resolved, 5 Closed. Unresolved = 2,8,6,3,9.
- Priority 1 Low, 2 Medium, 3 High, 4 Urgent. Agent names: `GET agents?per_page=100` (paged).

## Listing the queue

- Use `GET tickets/filter?query="workspace_id:3 AND (status:2 OR status:8 OR status:6 OR status:3 OR status:9)"` — returns `total`, 30 per page, max 10 pages (300). Fail loudly if `total` exceeds what was fetched.
- `GET tickets` without `updated_since` returns only tickets **created in the last 30 days** — a naive list silently drops old open tickets.
- Filter results have no `stats` or conversations; fetch each ticket with `GET tickets/<id>?include=stats,conversations`.
- `include=conversations` returns at most 10 conversations. For full threads use `GET tickets/<id>/conversations?per_page=100` (paged; returned newest-first).

## Rate limits

- Budget is per minute (headers `X-Ratelimit-Total/Remaining/Used-CurrentRequest`); the ticket endpoints report 160/min and a ticket fetch with `include=stats,conversations` costs 3 credits → ~50 tickets/min. Retry 429 after `Retry-After`. A full IS sweep (~110 tickets) takes 2–3 minutes.

## Rules that reproduce the dashboard exactly

| Dashboard tile | Rule |
|---|---|
| IS – Open Tickets | unresolved statuses in workspace 3 |
| IS – First Response Overdue | `stats.first_responded_at` is null AND `fr_due_by` < now (equivalently `fr_escalated` AND no first response) |
| IS – Overdue Tickets | `is_escalated` true |
| IS – Stale Tickets by Assigned to | not reproducible from API fields tried (updated_at, created_at, status_updated_at, agent_responded_at × thresholds × status sets); use the explicit IDLE rule instead |

`fr_due_by < now` alone over-counts (it includes tickets already answered).

## Field notes

- `stats` keys: first_responded_at, agent_responded_at, status_updated_at, pending_since, opened_at, assigned_at, inbound_count, outbound_count, … — there is **no** requester_responded_at; derive it from conversations.
- Conversation: `incoming` (from requester side), `private` (note), `user_id`, `source` (0 reply, 2 note), `body` HTML, `created_at`. Description is not a conversation.
- Agent activity for IDLE = any conversation by an agent who isn't the requester (public or private) or a status change (`stats.status_updated_at`).
- Inline images are on `attachment.freshservice.com/inline/attachment?token=…` and need the API auth to download.
- A `user_id` that 404s on `agents/<id>` may be a former agent now stored as a requester — try `requesters/<id>`.
- Ticket views/filters (`/a/tickets/view/<id>`) are not exposed by the API (`ticket_filters`, `ticket_views` 404); ask Duq for a view's filter criteria instead.
- Ticket → project task: no endpoint (`tickets/<id>/associations|project_tasks|projects` 404; `tickets/<id>/tasks` is ticket to-dos, not project tasks). Use the automatic conversation notes that name the task key.

## Projects (`/pm/`)

- Every `/pm/` request, including GETs, must send `Content-Type: application/json` or it fails with `invalid_content_type`.
- Projects: `GET pm/projects?filter=all` (filter values: all, completed, archived, open, in_progress, incomplete). IS keys: IS27 (2027), IS26 (2026), IS (legacy); also OPS26, SLG, ITMGMT.
- Tasks: `GET pm/projects/<pid>/tasks?per_page=100&page=N&filter=all` (filter: all, unresolved, open). Status/type/priority IDs are per project — resolve by name via `task-statuses` / `task-types` / `task-priorities`.
- Deleted tasks are absent from every task list; a missing key is not a paging bug.

## Writes (only after Duq's explicit approval)

- Private note to the agent: `POST tickets/<id>/notes` with `{"body": "<html>", "private": true, "notify_emails": ["<agent email>"]}`. An `@Name` in the body doesn't notify anyone; `notify_emails` does.
- Public reply to the requester: `POST tickets/<id>/reply` with `{"body": "<html>", "cc_emails": [...]}`. It sends from the IS mailbox under the API key owner and sets `stats.first_responded_at` if the ticket had none.
- Both return `{"conversation": {...}}`. Confirm by re-reading `tickets/<id>/conversations`.
- Attachments: `ticket.attachments[].attachment_url` downloads with the same Basic auth.
