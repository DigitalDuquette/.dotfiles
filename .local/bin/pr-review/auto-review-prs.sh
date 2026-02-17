#!/bin/bash
# Auto-generate PR reviews when new PRs are created

# Ensure Homebrew binaries are in PATH
export PATH="/opt/homebrew/bin:$PATH"

# Configuration
SCRIPT_DIR="$HOME/.local/bin/pr-review"
VAULT_DIR=~/obsidian-vaults/padnos
STATE_FILE="$SCRIPT_DIR/reviewed-prs.txt"
LOCK_FILE="$SCRIPT_DIR/auto-review.lock"
LOG_FILE="$SCRIPT_DIR/auto-review-prs.log"

# Prevent concurrent runs
if [[ -f "$LOCK_FILE" ]]; then
  echo "$(date): Another instance is running" >> "$LOG_FILE"
  exit 0
fi
trap "rm -f $LOCK_FILE" EXIT
touch "$LOCK_FILE"

# Initialize state file
mkdir -p "$SCRIPT_DIR"
touch "$STATE_FILE"

cd "$VAULT_DIR" || exit 1

# Find all open PRs in PADNOS org where I'm requested as reviewer
prs=$(gh search prs \
  --owner PADNOS \
  --state open \
  --review-requested @me \
  --json repository,number \
  --jq ".[] | \"\(.repository.name):\(.number)\"" \
  2>> "$LOG_FILE")

# Count and log how many PRs were found
pr_count=$(echo "$prs" | grep -c ":" || echo "0")
echo "$(date): Found $pr_count PRs to check" >> "$LOG_FILE"

[[ -z "$prs" ]] && exit 0

while IFS=: read -r repo_name pr_num; do
  repo="PADNOS/$repo_name"
  review_file="2-areas/software/pr-review/${repo_name}/PR-${pr_num}.md"
  state_key="${repo}:${pr_num}"

  echo "$(date): Checking $state_key..." >> "$LOG_FILE"

  # Get current PR updated timestamp
  pr_updated=$(gh pr view -R "$repo" "$pr_num" --json updatedAt -q .updatedAt 2>> "$LOG_FILE")

  if [[ -z "$pr_updated" ]]; then
    echo "$(date):   ERROR: Could not fetch PR data, skipping" >> "$LOG_FILE"
    continue
  fi

  pr_timestamp=$(date -j -f "%Y-%m-%dT%H:%M:%SZ" "$pr_updated" +%s 2>/dev/null || echo "0")

  # Check if we've reviewed this PR before (just check if PR number exists)
  # If you want to review updates, manually call the code-review skill
  if grep -q "^${state_key}:" "$STATE_FILE" 2>/dev/null; then
    should_review=false
    echo "$(date):   Already reviewed, skipping (call code-review manually for updates)" >> "$LOG_FILE"
  else
    # Not reviewed before
    should_review=true
    echo "$(date):   Not reviewed before, will generate" >> "$LOG_FILE"
  fi

  # Skip if no review needed
  if [[ "$should_review" != "true" ]]; then
    continue
  fi

  {
    echo "$(date): Processing $repo PR #$pr_num..."

    # Create review directory if needed
    mkdir -p "2-areas/software/pr-review/${repo_name}"

    # Generate review (token cost here)
    # Pass full repo name (PADNOS/repo-name) and PR number
    # Use -p flag for non-interactive mode
    if claude -p "/code-review-local $repo $pr_num" 2>&1 | grep -v "^$"; then
      # Verify review file was created
      if [[ -f "$review_file" ]]; then
        echo "$(date): ✓ Completed review for $state_key"
        # Append to log (never delete old entries - this is an audit log)
        echo "${state_key}:${pr_timestamp}" >> "$STATE_FILE"
      else
        echo "$(date): WARNING: Review file not created for $state_key"
      fi
    else
      echo "$(date): ERROR: Claude failed for $state_key"
    fi
  } >> "$LOG_FILE" 2>&1

done <<< "$prs"
