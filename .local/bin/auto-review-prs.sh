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

# Pull latest changes before starting
git pull --rebase --quiet || {
  echo "$(date): ERROR: git pull failed" >> "$LOG_FILE"
  exit 1
}

# Find all open PRs in PADNOS org where I'm involved
# This includes: assigned, mentioned, review requested, or authored
prs=$(gh search prs \
  --owner PADNOS \
  --state open \
  --involves @me \
  --json repository,number \
  --jq ".[] | \"\(.repository.name):\(.number)\"" \
  2>> "$LOG_FILE")

[[ -z "$prs" ]] && exit 0

while IFS=: read -r repo_name pr_num; do
  repo="PADNOS/$repo_name"
  review_file="2-areas/software/pr-review/${repo_name}/PR-${pr_num}.md"
  state_key="${repo}:${pr_num}"

  # Check if PR has been updated since last review
  should_review=false

  if [[ -f "$review_file" ]]; then
    # Get PR last updated timestamp
    pr_updated=$(gh pr view -R "$repo" "$pr_num" --json updatedAt -q .updatedAt 2>> "$LOG_FILE")

    if [[ -n "$pr_updated" ]]; then
      # Get review file modification time
      file_mtime=$(stat -f %m "$review_file" 2>/dev/null || echo "0")
      pr_mtime=$(date -j -f "%Y-%m-%dT%H:%M:%SZ" "$pr_updated" +%s 2>/dev/null || echo "0")

      # If PR updated after review file, regenerate
      if [[ $pr_mtime -gt $file_mtime ]]; then
        should_review=true
        echo "$(date): PR updated, regenerating review for $state_key..." >> "$LOG_FILE"
      fi
    fi
  else
    # No review file exists, need to review
    should_review=true
  fi

  # Skip if no review needed
  if [[ "$should_review" != "true" ]]; then
    # Mark as processed if not already
    grep -qF "$state_key" "$STATE_FILE" || echo "$state_key" >> "$STATE_FILE"
    continue
  fi

  echo "$(date): Processing $repo PR #$pr_num..." >> "$LOG_FILE"

  # Create review directory if needed
  mkdir -p "2-areas/software/pr-review/${repo_name}"

  # Generate review (token cost here)
  # Pass full repo name (PADNOS/repo-name) and PR number
  if claude /code-review-local "$repo" "$pr_num" --headless 2>> "$LOG_FILE"; then
    # Mark as reviewed on success
    echo "$state_key" >> "$STATE_FILE"

    # Commit and push
    if [[ -f "$review_file" ]]; then
      git add "$review_file"
      # Check if this is an update (file was already tracked)
      if git ls-files --error-unmatch "$review_file" >/dev/null 2>&1; then
        commit_msg="Update review: PR-${pr_num} from ${repo_name}"
      else
        commit_msg="Auto-review: PR-${pr_num} from ${repo_name}"
      fi
      git commit -m "$commit_msg" --quiet
      git push --quiet || {
        echo "$(date): WARNING: git push failed for $state_key" >> "$LOG_FILE"
      }
      echo "$(date): ✓ Completed review for $state_key" >> "$LOG_FILE"
    else
      echo "$(date): WARNING: Review file not created for $state_key" >> "$LOG_FILE"
    fi
  else
    echo "$(date): ERROR: Claude failed for $state_key" >> "$LOG_FILE"
  fi

done <<< "$prs"
