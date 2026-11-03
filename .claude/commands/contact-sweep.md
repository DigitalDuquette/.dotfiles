---
name: contact-sweep
description: >-
  Scans recent email, including quoted replies, for external contact details
  in signature blocks and writes them to a vCard file for review in macOS
  Contacts. Use during the weekly review or to catch up on missed contacts.
allowed-tools:
  - Read
  - Write
  - Bash
  - mcp__claude_ai_Microsoft_365__outlook_email_search
  - mcp__claude_ai_Microsoft_365__read_resource
---

# Contact Sweep

Finds external people in recent email and writes their contact details to one
`.vcf` file. Jared imports the file into macOS Contacts. The duplicate review in
Contacts.app is the approval step. This command never writes to a contact store.

---

## Instructions for Claude

### 1. Set the Window

`$ARGUMENTS` can give the window start (for example `6 months ago` or
`2026-04-01`). If it is empty, use the most recent Friday before today (same
convention as `/meeting-review`).

Output folder: `~/Downloads/contact-sweep-YYYY-MM-DD/` (today's date), one
`First-Last.vcf` file per person so Jared can review them one at a time.

### 2. Find External Threads

Call `outlook_email_search` with `afterDateTime: <window start>`, `query: "*"`,
`limit: 25`. Page with `nextOffset` or `nextCursor` until no more results.

Keep a message only when:
- The sender domain is not `padnos.com`
- The sender is not automated (`noreply`, `no-reply`, `notifications`,
  `mailer-daemon`, marketing lists, calendar invites, ticket systems)

Group the kept messages by thread (subject without `RE:` / `FW:`). For each
thread, read only the newest message with `read_resource`. It holds the quoted
history of the thread.

For a long window (more than about 200 threads), report the count and ask
before reading them all.

### 3. Extract Contacts

In each message body, split the text into blocks: the top message and each
quoted message. A quoted block starts at a header (`From:` / `Sent:` or
`On <date>, <name> wrote:`).

For each block:
- The person is the `From:` of that block. A signature belongs only to the
  sender of its own block. Never give one person's phone to another person.
- The date is the `Sent:` date of that block.
- Read the signature at the end of the block: full name, title, company,
  email, phone numbers (mark mobile vs office when the label says so).

Skip:
- Anyone at `padnos.com` (Entra already has them)
- Jared's own signature

Keep every real person, even with only a name and email. A real person is a
human who wrote a block in the thread, not a list, bot, or shared inbox.

When the same person appears more than once, keep the values from the block
with the newest date. Do not merge an older phone number over a newer one.

Do not guess. If a value is not in the signature text, leave it out.

### 4. Write the vCard File

One file per person, vCard 3.0, CRLF line endings. Escape `,` `;` and `\` in
values with a backslash.

```
BEGIN:VCARD
VERSION:3.0
N:<Last>;<First>;;;
FN:<First> <Last>
ORG:<Company>
TITLE:<Title>
EMAIL;TYPE=WORK:<email>
TEL;TYPE=CELL:<mobile>
TEL;TYPE=WORK:<office>
NOTE:contact-sweep <YYYY-MM-DD>: "<thread subject>" (<signature date>)
END:VCARD
```

Leave out any line that has no value.

If no contacts are found, do not create the folder. Report that and stop.

### 5. Report Back

Show a short table: name, company, what was found (phone, title), source
thread. Then give the folder path and tell Jared to open it:

```bash
open ~/Downloads/contact-sweep-YYYY-MM-DD/
```

He previews each file with Quick Look (space bar in Finder), deletes the
ones he does not want, then opens the rest in Contacts.app.
