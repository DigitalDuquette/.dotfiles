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

# Carve out the heredoc body (if any) so shell-redirection checks below
# don't false-positive on `>` characters that are just script text (XML
# tags, comparisons, f-strings) rather than real shell syntax.
heredoc_re = re.compile(r"<<-?\s*(['\"]?)(\w+)\1")
hd = heredoc_re.search(cmd)

if hd:
    delim = hd.group(2)
    close_re = re.compile(r"^[ \t]*" + re.escape(delim) + r"[ \t]*$", re.MULTILINE)
    close_m = close_re.search(cmd, hd.end())
    if not close_m:
        # Can't confidently locate the end of the heredoc body - don't guess.
        sys.exit(0)
    shell_text = cmd[:hd.start()] + cmd[close_m.end():]
else:
    shell_text = cmd

# Real shell-level redirection/piping outside the heredoc body means this
# isn't a plain read-and-print script.
SHELL_DENY = [r">>", r"[^<]>[^=>]", r"\|"]
for pat in SHELL_DENY:
    if re.search(pat, shell_text):
        sys.exit(0)

# Risk keywords matter wherever they appear (including inside the heredoc
# body, since that's the actual script source).
CODE_DENY = [
    r"\bsubprocess\b", r"\bsocket\b", r"\brequests\b", r"\burllib\b",
    r"\bhttp\.client\b", r"\bftplib\b", r"\bsmtplib\b", r"\bparamiko\b",
    r"\bshutil\b", r"\bctypes\b", r"\bpty\b", r"\bmultiprocessing\b",
    r"\bos\.(system|popen|remove|unlink|rmdir|rename|replace|mkdir|makedirs|chmod|chown|kill|utime|exec\w*)\b",
    r"open\([^)]*['\"][wax]",
    r"\.(write_text|write_bytes|unlink|rmdir|touch)\(",
    r"\b(eval|exec|compile|__import__)\(",
    r"(^|[^A-Za-z0-9_])(rm|mv|cp|dd|mkfs|chmod|chown|kill|sudo|shutdown|reboot|curl|wget|ssh|scp|git|npm|pip|brew)(\s|$)",
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
