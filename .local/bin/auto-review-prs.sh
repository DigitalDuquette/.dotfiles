#!/bin/bash
# Auto-generate PR reviews when new PRs are created

# Configuration
VAULT_DIR=~/obsidian-vaults/padnos
STATE_FILE=~/.claude/reviewed-prs.txt
LOCK_FILE=~/.claude/auto-review.lock
LOG_DIR=~/.claude/logs
LOG_FILE="$LOG_DIR/auto-review-prs.log"

# Prevent concurrent runs
if [[ -f "$LOCK_FILE" ]]; then
  echo "$(date): Another instance is running" >> "$LOG_FILE"
  exit 0
fi
trap "rm -f $LOCK_FILE" EXIT
touch "$LOCK_FILE"

# Initialize state file
mkdir -p ~/.claude "$LOG_DIR"
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

  # Check if PR has been updated since last review
  should_review=false

  if [[ -f "$review_file" ]]; then
    echo "$(date):   Review file exists, checking if PR was updated..." >> "$LOG_FILE"

    # Get PR last updated timestamp
    pr_updated=$(gh pr view -R "$repo" "$pr_num" --json updatedAt -q .updatedAt 2>> "$LOG_FILE")

    if [[ -n "$pr_updated" ]]; then
      # Get review file modification time
      file_mtime=$(stat -f %m "$review_file" 2>/dev/null || echo "0")
      pr_mtime=$(date -j -f "%Y-%m-%dT%H:%M:%SZ" "$pr_updated" +%s 2>/dev/null || echo "0")

      # If PR updated after review file, regenerate
      if [[ $pr_mtime -gt $file_mtime ]]; then
        should_review=true
        echo "$(date):   PR updated after review file, will regenerate" >> "$LOG_FILE"
      else
        echo "$(date):   Review file is up to date, skipping" >> "$LOG_FILE"
      fi
    fi
  else
    # No review file exists, need to review
    should_review=true
    echo "$(date):   No review file exists, will generate" >> "$LOG_FILE"
  fi

  # Skip if no review needed
  if [[ "$should_review" != "true" ]]; then
    # Mark as processed if not already
    grep -qF "$state_key" "$STATE_FILE" || echo "$state_key" >> "$STATE_FILE"
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
        # Mark as reviewed on success
        echo "$state_key" >> "$STATE_FILE"
      else
        echo "$(date): WARNING: Review file not created for $state_key"
      fi
    else
      echo "$(date): ERROR: Claude failed for $state_key"
    fi
  } >> "$LOG_FILE" 2>&1

done <<< "$prs"
