#!/bin/bash
# PostToolUse (Write|Edit) hook: enforce 80-char line wrap on markdown files.
# Exempt: .github/**/*.md (GitHub-rendered content — PR/issue templates, etc.)
# Exempt: fenced code blocks within the file.
input=$(cat)
file=$(jq -r '.tool_input.file_path // .tool_response.filePath // empty' <<<"$input")

[[ "$file" == *.md ]] || exit 0
case "$file" in
  *".github/"*) exit 0 ;;
esac
[[ -f "$file" ]] || exit 0

violations=$(awk '
  /^[[:space:]]*```/ { infence = !infence; next }
  !infence && length($0) > 80 { print FNR": "length($0)" chars" }
' "$file")

if [[ -n "$violations" ]]; then
  reason="Lines over 80 chars in $file:"$'\n'"$violations"
  jq -n --arg reason "$reason" \
    '{"decision":"block","reason":$reason,"hookSpecificOutput":{"hookEventName":"PostToolUse","additionalContext":$reason}}'
fi
