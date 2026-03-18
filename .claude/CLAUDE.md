# CLAUDE.md

## Anti-Patterns — Do NOT Do These

- Do NOT over-engineer or over-automate. When asked to review something, do
  NOT generate scripts, spawn parallel agents, or create scaffolding unless
  explicitly requested.
- Do NOT start any substantial work — editing files, running commands, writing
  content — until the user confirms scope and direction. Default to discussing
  first.
- Do NOT generate speculative or made-up content to fill out documents. Only
  use information the user has provided.
- Do NOT create git commits. The user reviews changes in logical development
  blocks in their JetBrains IDE and crafts commit messages themselves to follow
  their development process. This applies to new code only.

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
