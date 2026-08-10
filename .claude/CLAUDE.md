# CLAUDE.md

## Anti-Patterns — Do NOT Do These

- When asked to review something, do NOT generate scripts, spawn parallel
  agents, or create scaffolding unless explicitly requested. Review means
  read and report.
- Do NOT generate speculative or made-up content to fill out documents. Only
  use information the user has provided.
- Do NOT create git commits unless I use the word "commit" in my message. Do
  not infer commit intent from context. I review changes in logical blocks in
  my JetBrains IDE and write the messages myself.

---

## Before You Write Code

For anything beyond a one-line edit, before your first edit tell me in under
10 lines:

1. The files you will change. If you later need one not on that list, stop
   and ask.
2. Assumptions you are making about the environment that you have not
   verified.
3. What you are tempted to add beyond what I literally asked for, and why I
   should say no to each.

Then stop and wait for me.

---

## Stop Conditions

Stop and report rather than continue if any of these become true:

- The change grows past ~150 lines, or touches a file not on your list
- You are about to add a dependency, a new file, or a new abstraction
- An assumption you stated turns out to be false

---

## Development Environment

- IDE: JetBrains (use JetBrains-specific terminology and tooling references
  where relevant — e.g., inspections, changelists, run configurations)
- OS: macOS

---

## Markdown Formatting Rules

When writing markdown files, wrap line at 80 character wide to follow markdown
standards. Exception: GitHub contexts (pull requests, issues, comments) are
exempt from the 80 character rule.

- Do not rely on soft line breaks for structure.
- All multi-line fields should be represented as nested lists.
- Prefer block-level markdown elements (headings, lists) over inline formatting

After writing or editing any .md file, re-check the line wrap before moving on
to anything else, and fix any line that runs past 80.
