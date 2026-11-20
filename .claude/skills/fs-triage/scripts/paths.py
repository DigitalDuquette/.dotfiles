"""Where fs-triage keeps things. Code is public (dotfiles); data is not.

DATA   private, in the vault (git-backed): config.json, decisions.jsonl,
       PUNCHLIST.md, preferences.md
STATE  local runtime, not in git: triage/ (sweeps, review prep, deck inbox)
ENV    FRESH_KEY, rendered once with `op inject`
"""
import json
import os
from pathlib import Path

VAULT = Path.home() / "Library/Mobile Documents/iCloud~md~obsidian/Documents/padnos"
DATA = Path(os.environ.get("COS_DATA") or VAULT / "2-areas/chief-of-staff")
STATE = Path(os.environ.get("COS_STATE") or Path.home() / ".local/state/cos")
ENV = Path(os.environ.get("FS_ENV_FILE") or Path.home() / ".config/cos/.env")
TRIAGE = STATE / "triage"
DECISIONS = DATA / "decisions.jsonl"
CONFIG = json.loads((DATA / "config.json").read_text())
TRIAGE.mkdir(parents=True, exist_ok=True)
