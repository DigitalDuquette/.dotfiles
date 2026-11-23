---
name: fs-triage
description: >-
  Duq's Freshservice queue triage for the Information Solutions workspace.
  Sweep, drill, brief, then the review deck (local HTML) where Duq makes a
  call per ticket and Claude executes it. Use for /fs-triage, "triage the
  queue", "review the deck", or a "Review deck, SR-…" message.
argument-hint: "[morning | review]  (default: review)"
allowed-tools: >-
  Read, Write, Edit, Glob, Grep, Monitor,
  Bash(python3 ~/.claude/skills/fs-triage/scripts/sweep.py:*),
  Bash(python3 ~/.claude/skills/fs-triage/scripts/at_risk.py:*),
  Bash(python3 ~/.claude/skills/fs-triage/scripts/precedents.py:*),
  Bash(python3 ~/.claude/skills/fs-triage/scripts/drill.py:*),
  Bash(python3 ~/.claude/skills/fs-triage/scripts/review_deck.py:*),
  Bash(python3 ~/.claude/skills/fs-triage/scripts/log_decision.py:*),
  Bash(python3 ~/.claude/skills/fs-triage/scripts/punchlist.py:*),
  Bash(python3 ~/.claude/skills/fs-triage/scripts/cleanup_automated.py:*),
  Bash(python3 ~/.claude/skills/fs-triage/deck/serve.py:*),
  Bash(tail -n0 -F ~/.local/state/cos/triage/inbox.log),
  Bash(gh issue view:*), Bash(gh pr view:*), Bash(gh api:*)
---

# fs-triage

**Triage and escalate. Duq decides. Claude executes.** Give Duq (IT Manager,
Data and Software, PADNOS) the tickets that need him, with enough context
to decide without opening Freshservice. Never pick the action for him.
When he decides, make the update exactly as approved. No ticket is missed
or left to rot.

Before any queue or ticket work, read these private files from the vault
(`2-areas/chief-of-staff/`, see `scripts/paths.py`):

- `preferences.md`: what needs his eyes, his usual calls, note style.
  This is the most important file. Follow it.
- `PUNCHLIST.md`: known gaps in the scripts. Do not report a known gap
  as news.

API facts, IDs and dashboard rules: `references/freshservice-api.md`.

---

## Files

- Scripts: `~/.claude/skills/fs-triage/scripts/` (stdlib Python, live
  API). Flags come from `sweep.py` and `at_risk.py`, not from your
  judgment. If a rule is wrong, change the code or `config.json` and say
  so. Do not work around it in the brief.
- Private data: `2-areas/chief-of-staff/` in the vault (`config.json`,
  `decisions.jsonl`, `PUNCHLIST.md`, `preferences.md`). The vault
  watcher commits changes there. Do not commit by hand.
- Runtime: `~/.local/state/cos/triage/` (`latest.json`, sweep history,
  `review-<date>.json` prep, `review-latest.json`, `inbox.log`,
  `brief-<date>.md`).
- Key: `~/.config/cos/.env` (`FRESH_KEY`). Never use `op run` here.
- Never use the SQ2/Fivetran warehouse for triage. It lags.
- Keep `&` out of shell commands, including inside quoted text.

---

## Mode: morning (headless, from cos.sh)

Runs with no human present. **Never post, reply or change status, except
step 1.** Do not start the deck or Monitor.

1. `cleanup_automated.py --post` (standing order: resolve old DBA
   checklists). Note the count.
2. `sweep.py > ~/.local/state/cos/triage/sweep-<date>.md` (3 to 5 min).
   Check that the totals look sane. Diff against the previous
   `sweep-*.json`: what is gone, new, or changed (`public_replies`,
   `private_notes`, `status`, `agent`). Drill only new or changed tickets.
3. `at_risk.py`, then `precedents.py` and `precedents.py --digest`.
4. For each ticket that needs Duq, run `drill.py <id>` (several ids per
   call). Read the whole thread. Follow GitHub links with `gh`. Then write
   the prep to `~/.local/state/cos/triage/review-<date>.json`:

   ```json
   {"date": "YYYY-MM-DD", "tickets": {"<id>": {
     "requester": "Name", "requester_title": "Title", "senior": true,
     "ask": "one sentence",
     "discussion": ["MM/DD: what happened"],
     "blocker": "your read on the real blocker or delay",
     "holder": "who holds the ball",
     "responses": [{"label": "short", "channel": "note|reply",
                    "text": "exact wording"}]
   }}}
   ```

   Responses follow the note rules in `preferences.md`. Keep `decided`
   from any earlier prep for the same day.
5. `review_deck.py` (writes `review-latest.json`, prints "N need you").
6. Write `brief-<date>.md`: totals and change since the last brief, the
   DBA cleanup count, then **Needs you** (FOLLOW-UP first; one line each:
   SR link, requester with title if senior, the fact, who holds the ball,
   "Your usual call:" or "no precedent"), **Recently decided, agent's
   turn**, **Moving, no action**, and the rest as counts.
7. Print only: `N need you` on the last line.

---

## Mode: review (interactive, default)

1. If today's `review-latest.json` is missing or older than today, run the
   morning steps 1 to 6 first. Say so; it takes a few minutes.
2. Start the deck in the background:
   `python3 ~/.claude/skills/fs-triage/deck/serve.py --open`
   (Bash, `run_in_background`). If the port is busy, a deck is already
   running; just open `http://127.0.0.1:8765/`.
3. Start a Monitor on the deck inbox, max timeout, and re-arm it whenever
   it expires while the review is open:
   `tail -n0 -F ~/.local/state/cos/triage/inbox.log`
4. Show today's brief in short form: totals, then the Needs-you list (link
   and one-line fact each). Say the deck is open.
5. Handle each deck message (`Review deck, SR-<id>: …`) as Duq's reply on
   that ticket, one at a time. Typed messages in the terminal count the
   same.
6. Answer on the card, not only in the terminal: `say.py <id> "<text>"`
   (or pipe a dry run: `post_note.py … | say.py <id> -`). Duq reads the
   deck; the terminal gets the same text, short. `serve.py` logs his deck
   messages to the same `outbox.jsonl`, so the card shows both sides.

### Handling a call

- **Note or reply requests** ("Draft this", "add the note", shorthand like
  "request first response"): `post_note.py <id> "<text>"` dry run
  (`--reply` for a public reply as Duq). Text: his wording, else the
  prepared `responses[].text`, else the standard short forms in
  `preferences.md`. Show the recipient and text on the card (`say.py`).
  Post with `--post` only
  after he types "post" in the terminal. A deck click is never a "post".
- **No-write calls** ("No action", "I handled it", "I'll follow up"): no
  dry run.
- **Status changes**: `set_status.py` only when he asks. Dry run first.
- **Log every outcome the same turn:**
  `log_decision.py --ticket <id> --agent "<name>" --flags A,B`
  `--facts "…" --reason "…" --decision "…" --action "…" --why "…"`
  `--decided "<short>"`.
  It appends to `decisions.jsonl`, marks the ticket Decided and refreshes
  the deck.
- Reply in one or two lines (card via `say.py`, and terminal): what
  landed, and how many still need him.
  When three or fewer remain, list them.
- Add one clause, never a second draft, when: his call differs from the
  usual call (a new pattern, record it); the call leaves a senior
  requester with no answer or ETA; the same agent has a related open
  question.

`post_note.py` and `set_status.py` need permission each time on purpose.

---

## Learning from feedback

When Duq corrects you or makes a call, update the files the same turn:

- A preference or new rule: `preferences.md`.
- The call itself: `log_decision.py` (above).
- Something missed, wrong or impossible: `PUNCHLIST.md`.
- A threshold or scope change: `config.json`.
- A script bug: fix it in `scripts/`, run `python3 -m py_compile`, and
  tell Duq (the scripts live in his public dotfiles).

Chat history does not carry between sessions. Files do.
