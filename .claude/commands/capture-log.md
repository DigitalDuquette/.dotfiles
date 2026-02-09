---
description: Add entry to team member capture log
---

Add a factual entry to a team member's capture log file.

**Format:** Each entry follows the 3-line structure (Event, Impact, Evidence)
with today's date as the heading.

**Steps:**

1. **Check conversation context first:**
   - If recent conversation discussed a PR review, incident, or performance issue, summarize it
   - Ask: "I see we discussed [X]. Should I capture this, or provide different details?"
   - If no relevant context, prompt for Event/Impact/Evidence

2. **Determine entry type** (affects Impact framing):
   - PIP-related: Connect to patterns, timelines, prior incidents
   - General performance: Business impact, recovery actions
   - Positive: Value delivered, milestone reached

3. **Read context files:**
   - Read the capture log: `~/obsidian-vaults/padnos/2-areas/management/team/{name}/capture-log.md`
   - Read folder CLAUDE.md if exists: `~/obsidian-vaults/padnos/2-areas/management/team/{name}/CLAUDE.md`
   - Match existing tone/style exactly

4. **Generate draft entry** following scope rules below

5. **Show draft and ask:** "Does this capture the key insight?"
   - Allow iteration before writing
   - User can reply 'yes' to save or request changes

6. **Write final entry** under ## Entries section with today's date (YYYY-MM-DD)

**CRITICAL RULES:**

- Use ONLY the information provided by the user or discussed in conversation
- Keep descriptions factual and neutral (no "failed to", "struggled with")
- Event = concise (1 line), Impact = strategic insight (pattern/consequence)
- Evidence must be specific links (PR numbers, ticket numbers, Teams URLs)
- One entry per date (if multiple events same day, use separate date headings)

**Event vs Impact Scope:**

**Event (1 line, factual, concise):**
- ✅ "PR-54 review identified multiple issues in small refactor"
- ❌ "PR-54 review identified redundant assignment in razor component (line 289), new magic number..." (too technical)

**Impact (strategic insight, not tactical details):**

*For PIP entries:*
- ✅ "Three days after PR-510 success, independent work reverted to same pattern. Process taught did not transfer to new work."
- ❌ "Small refactor introduced regression" (too tactical, misses the pattern)

*For general performance:*
- ✅ "Delivery timeline at risk; manager intervention required to complete"
- ❌ "Code had bugs" (too vague)

*For positive entries:*
- ✅ "Feature delivery milestone reached; 70% success rate achieved"
- ❌ "PR merged" (too minimal)

**HR/Legal Ready Language:**

❌ "Todd failed to apply feedback"
✅ "Feedback from PR-494 not applied to PR-501"

❌ "Todd struggled with the refactor"
✅ "Refactor required manager intervention and rework"

❌ "Same mistakes again"
✅ "Same architectural issues from Jan 13-28 PRs"

**Entry format:**

```markdown
### YYYY-MM-DD

- Event: [Concise, factual - what happened in 1 line]
- Impact: [Strategic insight - pattern/timeline/consequence, not technical details]
- Evidence: [Specific links]
```

**Examples:**

```markdown
### 2026-02-09

- Event: PR-54 review identified multiple issues in small refactor: error handling regression, new hard-coded values introduced while removing others, redundant assignment.
- Impact: Three days after PR-510 success (manager-designed pattern, forced planning document, Claude Code execution), independent work reverted to same pattern: no planning step, regressions introduced, old vs new behavior not compared before submission. Process taught in PR-510 (plan first, understand architecture, think systematically) did not transfer to new work.
- Evidence: [[PR-54]], [GitHub PR-54](https://github.com/PADNOS/Pricing-portal/pull/54)
```

```markdown
### 2026-01-23

- Event: PR-502 completed and merged successfully, adding two reference-based SHIPPER matching patterns to Cass Freight import.
- Impact: REFERENCE-based matching success rate improved to ~70%; feature delivery milestone reached.
- Evidence: [PR-502 merged](https://github.com/PADNOS/RIMAS-extensibility/pull/502#event-22252012338), [[PR-502]]
```
