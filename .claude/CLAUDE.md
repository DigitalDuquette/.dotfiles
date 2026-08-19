# CLAUDE.md

## Anti-Patterns — Do NOT Do These

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

---

## Prose Style

Write plainly. This is a list of specific tics, not general advice.

Avoid:

- Preamble. Do not restate my question or announce what you are about to do.
  Answer first.
- Closing summary paragraphs that repeat what you already said.
- "It's not just X, it's Y" and other contrast-and-reveal framing.
- Hedge openers: "It's worth noting", "Importantly", "Note that", "Keep in
  mind", "That said".
- Inflation words: "powerful", "seamless", "robust", "comprehensive",
  "leverage", "delve", "underscore", "crucial", "elevate".
- "This ensures that" and "This allows you to". Say what it does.
- Three-item lists written for rhythm: "clear, consistent, and maintainable".
  Keep the one item that carries weight.
- Bold on nouns mid-sentence. Bold is for headings and list-item labels only.
- A heading over fewer than three sentences of content.
- Em dashes. Use commas, colons, parentheses, or a period.
- Emoji.

Do:

- Lead with the conclusion, then the reasoning.
- Cut any sentence that would not change what I do.
- Use a plain sentence instead of a one-item bulleted list.
- State uncertainty as fact: "I did not verify X", not "it may be worth
  considering whether X".
- Prefer the shorter word when both are exact.
