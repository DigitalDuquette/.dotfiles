-- Jared's Freshservice ticket work on one day (UTC bounds from the caller):
-- tickets he opened, and every reply or private note he wrote.
SET NOCOUNT ON;
DECLARE @me BIGINT = 23000197753;

SELECT t.id AS ticket, 'opened' AS kind, t.subject,
    LEFT(REPLACE(REPLACE(t.description_text, CHAR(13), ' '), CHAR(10), ' '), 800) AS text
FROM freshservice.ticket AS t
WHERE t.requester_id = @me AND t.deleted = 0
    AND t.created_at >= '$(START)' AND t.created_at < '$(END)'
UNION ALL
SELECT c.ticket_id, CASE c.private WHEN 1 THEN 'note' ELSE 'reply' END, t.subject,
    LEFT(REPLACE(REPLACE(c.body_text, CHAR(13), ' '), CHAR(10), ' '), 600)
FROM freshservice.ticket_conversation AS c
    JOIN freshservice.ticket AS t ON t.id = c.ticket_id
WHERE c.user_id = @me
    AND c.created_at >= '$(START)' AND c.created_at < '$(END)'
ORDER BY ticket;
