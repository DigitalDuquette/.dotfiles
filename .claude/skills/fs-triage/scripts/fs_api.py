"""Minimal Freshservice API v2 client. Stdlib only, read-only (GET).

Credentials: FRESH_KEY read from $FS_ENV_FILE or ~/.config/cos/.env (paths.py)
(KEY=value lines; the file is parsed, never executed).
Rate limits: this account allows 160 credits/min; `include=` adds credits.
On 429 we sleep for Retry-After and retry.
"""
import base64
import json
import os
import pathlib
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import paths  # noqa: E402


def load_key(name: str = "FRESH_KEY") -> str:
    env_file = str(paths.ENV)
    for line in pathlib.Path(env_file).read_text().splitlines():
        line = line.strip().removeprefix("export ").strip()
        if line.startswith(f"{name}="):
            val = line.split("=", 1)[1].strip().strip('"').strip("'")
            if val and not val.startswith(("op://", "{{")):
                return val
    sys.exit(f"{name} missing (or still an op reference) in {env_file}")


class Freshservice:
    def __init__(self, domain: str):
        self.base = f"https://{domain}/api/v2"
        self.auth = "Basic " + base64.b64encode(f"{load_key()}:X".encode()).decode()
        self.calls = 0

    def get(self, path: str, **params) -> dict:
        qs = urllib.parse.urlencode(params, safe=":,")
        url = f"{self.base}/{path}" + (f"?{qs}" if qs else "")
        req = urllib.request.Request(url, headers={"Authorization": self.auth, "Content-Type": "application/json"})  # /pm/ endpoints reject GETs without it
        for attempt in range(6):
            try:
                with urllib.request.urlopen(req, timeout=30) as r:
                    self.calls += 1
                    return json.load(r)
            except urllib.error.HTTPError as e:
                if e.code == 429 and attempt < 5:
                    wait = int(e.headers.get("Retry-After") or 30)
                    print(f"  rate limited; sleeping {wait}s", file=sys.stderr)
                    time.sleep(wait + 1)
                    continue
                raise RuntimeError(f"GET {url} -> HTTP {e.code}: {e.read().decode()[:300]}") from None
        raise RuntimeError(f"GET {url} -> gave up after retries")

    def filter_tickets(self, query: str) -> list:
        """/tickets/filter: 30 per page, max 10 pages (300 tickets). Fails loudly past that."""
        out = []
        for page in range(1, 11):
            r = self.get("tickets/filter", query=f'"{query}"', page=page)
            out += r["tickets"]
            if len(out) >= r.get("total", 0) or len(r["tickets"]) < 30:
                if len(out) < r.get("total", 0):
                    raise RuntimeError(f"filter returned {len(out)} of {r['total']} tickets")
                return out
        raise RuntimeError("filter hit the 300-ticket cap; sweep would be incomplete")

    def ticket(self, ticket_id: int) -> dict:
        """Ticket with stats + the FULL thread. include=conversations stops at 10,
        so longer threads are re-read from /conversations (paged)."""
        t = self.get(f"tickets/{ticket_id}", include="stats,conversations")["ticket"]
        if len(t.get("conversations") or []) >= 10:
            t["conversations"] = self.conversations(ticket_id)
        return t

    def conversations(self, ticket_id: int) -> list:
        out = []
        for page in range(1, 20):
            batch = self.get(f"tickets/{ticket_id}/conversations", per_page=100, page=page)["conversations"]
            out += batch
            if len(batch) < 100:
                return out
        return out

    def agents(self) -> dict:
        names = {}
        for page in range(1, 20):
            r = self.get("agents", per_page=100, page=page)
            for a in r["agents"]:
                names[a["id"]] = f"{a.get('first_name') or ''} {a.get('last_name') or ''}".strip()
            if len(r["agents"]) < 100:
                return names
        return names
