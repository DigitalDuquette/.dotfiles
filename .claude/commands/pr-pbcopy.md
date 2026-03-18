Prepare a populated pull request description for the current branch and copy it
to the clipboard.

## Workflow

Run two agents in parallel:

**Agent 1 — Fetch PR template**

Use the gh CLI to fetch the latest PR template from the dev-guidelines repo:

```
gh api repos/padnos/dev-guidelines/contents/templates/PULL-REQUEST-example.md \
  --jq '.content' | base64 -d
```

Return the raw template content.

**Agent 2 — Analyze branch diff**

Detect the base branch:

```
git symbolic-ref refs/remotes/origin/HEAD | sed 's@^refs/remotes/origin/@@'
```

Then collect the full picture of changes:

```
git log <base>...HEAD --oneline
git diff <base>...HEAD
```

Read every changed file carefully. Produce a detailed analysis covering:
- What each change does
- Why it exists, inferred from the code and commit messages
- Categories of change (bug fix, feature, refactor, config change, schema
  migration, etc.)

## Synthesis

Once both agents return:

1. Map the diff analysis onto every section of the template
2. Populate each section with content grounded in the actual diff — no
   speculation, no placeholder text
3. If a section is not applicable, write 'N/A' rather than leaving empty
4. Do not invent issue numbers, ticket IDs, or deployment steps not evident in
   the diff. ASK.

## Output

Print the final populated PR description, then run it through pbcopy:

```
echo "<populated content>" | pbcopy
```

Confirm to the user that the PR description is on the clipboard.
