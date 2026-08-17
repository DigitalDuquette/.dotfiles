#!/usr/bin/env python3
import json
import re
import sys

data = json.load(sys.stdin)
cmd = (data.get("tool_input") or {}).get("command", "")

if not cmd:
    sys.exit(0)

# Shape check: an optional single leading `cd <path>` then an interpreter
# invocation. Anything else (extra chaining, non-interpreter commands)
# falls through to normal permission prompting.
SHAPE = re.compile(r"^(cd [^\n;&|]+(\n|\s*&&\s*))?(python3?|perl|ruby)\b")
if not SHAPE.match(cmd):
    sys.exit(0)


def find_source_span(cmd):
    """Locate the interpreter's inline-source argument (heredoc body, or a
    quoted -c "..."/'...' argument) so redirection/shell-command checks
    below can exclude it. Returns (start, end), "ambiguous" if a span looks
    like it starts but its end can't be confidently located, or None if
    neither shape is found.
    """
    hd = re.search(r"<<-?\s*(['\"]?)(\w+)\1", cmd)
    if hd:
        delim = hd.group(2)
        close_re = re.compile(r"^[ \t]*" + re.escape(delim) + r"[ \t]*$", re.MULTILINE)
        close_m = close_re.search(cmd, hd.end())
        if close_m:
            return (hd.start(), close_m.end())
        return "ambiguous"

    cm = re.search(r"-c\s*(['\"])", cmd)
    if cm:
        quote = cm.group(1)
        i = cm.end()
        while i < len(cmd):
            ch = cmd[i]
            if ch == "\\" and quote == '"':
                i += 2
                continue
            if ch == quote:
                return (cm.start(), i + 1)
            i += 1
        return "ambiguous"

    return None


span = find_source_span(cmd)
if span == "ambiguous":
    # Can't confidently locate the end of the inline source - don't guess.
    sys.exit(0)
if span:
    start, end = span
    shell_text = cmd[:start] + cmd[end:]
else:
    shell_text = cmd

# Real shell-level redirection/piping outside the inline source means this
# isn't a plain read-and-print script.
SHELL_DENY = [r">>", r"[^<]>[^=>]", r"\|"]
for pat in SHELL_DENY:
    if re.search(pat, shell_text):
        sys.exit(0)

# Bare shell-command names only matter as real invocations - i.e. outside
# the inline source. Checking the whole command would false-positive on
# short Python identifiers that happen to share a name (e.g. `dd = ...`,
# `cp = ...`).
SHELL_CMD_DENY = (
    r"(^|[^A-Za-z0-9_])(rm|mv|cp|dd|mkfs|chmod|chown|kill|sudo|shutdown|"
    r"reboot|curl|wget|ssh|scp|git|npm|pip|brew)(\s|$)"
)
if re.search(SHELL_CMD_DENY, shell_text):
    sys.exit(0)

# Module/API-level risk indicators are specific enough to check across the
# whole command, including inside the inline source (that's the actual
# script body where these calls would occur).
CODE_DENY = [
    r"\bsubprocess\b", r"\bsocket\b", r"\brequests\b", r"\burllib\b",
    r"\bhttp\.client\b", r"\bftplib\b", r"\bsmtplib\b", r"\bparamiko\b",
    r"\bshutil\b", r"\bctypes\b", r"\bpty\b", r"\bmultiprocessing\b",
    r"\bos\.(system|popen|remove|unlink|rmdir|rename|replace|mkdir|makedirs|chmod|chown|kill|utime|exec\w*)\b",
    r"open\([^)]*['\"][wax]",
    r"\.(write_text|write_bytes|unlink|rmdir|touch)\(",
    r"\b(eval|exec|compile|__import__)\(",
]
for pat in CODE_DENY:
    if re.search(pat, cmd, re.MULTILINE):
        sys.exit(0)

print(json.dumps({
    "hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "allow",
        "permissionDecisionReason": "heuristic: read-only interpreter script (cd + python3/perl/ruby), no write/network/subprocess/exec markers found",
    }
}))
