#!/usr/bin/env bash
# Claude Code status line — combined prompt info + session info

input=$(cat)

user=$(whoami)
host=$(hostname -s)
cwd=$(echo "$input" | jq -r '.workspace.current_dir // .cwd // empty')
# Fall back to $HOME-relative display
if [ -n "$cwd" ]; then
  display_cwd="${cwd/#$HOME/~}"
else
  display_cwd="~"
fi

model=$(echo "$input" | jq -r '.model.display_name // empty')
used=$(echo "$input" | jq -r '.context_window.used_percentage // empty')

# Build prompt segment (cyan)
prompt_seg=$(printf "\033[36m%s@%s\033[0m:\033[34m%s\033[0m" "$user" "$host" "$display_cwd")

# Build session segment
if [ -n "$model" ] && [ -n "$used" ]; then
  session_seg=$(printf "\033[33m%s\033[0m ctx:\033[32m%.0f%%\033[0m" "$model" "$used")
elif [ -n "$model" ]; then
  session_seg=$(printf "\033[33m%s\033[0m" "$model")
else
  session_seg=""
fi

if [ -n "$session_seg" ]; then
  printf "%s  |  %s\n" "$prompt_seg" "$session_seg"
else
  printf "%s\n" "$prompt_seg"
fi
