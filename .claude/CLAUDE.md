# CLAUDE.md

## Anti-Patterns — Do NOT Do These

- Do NOT over-engineer or over-automate. When asked to review something, do
  NOT generate scripts, spawn parallel agents, or create scaffolding unless
  explicitly requested.
- Do NOT start editing files until the user confirms they are ready. Default
  to discussing first.
- Do NOT generate speculative or made-up content to fill out documents. Only
  use information the user has provided.

---

## Markdown Formatting Rules

When writing markdown files, wrap line at 80 character wide to follow markdown
standards.

- Do not rely on soft line breaks for structure.
- All multi-line fields should be represented as nested lists.
- Prefer block-level markdown elements (headings, lists) over inline formatting
