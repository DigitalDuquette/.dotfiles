# CLAUDE.md

## Anti-Patterns — Do NOT Do These

- Do NOT generate speculative or made-up content to fill out documents. Only
  use information the user has provided.
- Do NOT create git commits unless I use the word "commit" in my message. Do
  not infer commit intent from context. I review changes in logical blocks in
  my JetBrains IDE and write the messages myself.

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

---

## Prose Style

Write plainly. 

Follow ASD-STE100 Simplified Technical English.

