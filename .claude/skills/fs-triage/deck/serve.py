#!/usr/bin/env python3
"""Local server for the fs-triage review deck. Binds 127.0.0.1 only.

  GET  /             the deck (index.html, with this run's token)
  GET  /review.json  triage/review-latest.json (written by review_deck.py)
  GET  /outbox.json  today's card conversation (triage/outbox.jsonl, see say.py)
  POST /send         append one "Review deck, SR-<id>: ..." line to triage/inbox.log

The Claude session tails inbox.log with its Monitor tool, so each button click
arrives in the session as Duq's reply on that ticket. Nothing
here writes to Freshservice; posting still waits for "post" in the terminal.

Guards: the Host header must be this server (blocks DNS rebinding), and POST
needs the per-run token in X-Token (a custom header other sites can't send
without a CORS preflight, which this server never answers).

Usage: serve.py [--open]      FS_DECK_PORT overrides the port (default 8765)
"""
import argparse
import http.server
import os
import pathlib
import secrets
import sys
import webbrowser

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "scripts"))
import datetime  # noqa: E402
import json  # noqa: E402
import re  # noqa: E402

import paths  # noqa: E402
import say  # noqa: E402

PORT = int(os.environ.get("FS_DECK_PORT", "8765"))
HOSTS = {f"127.0.0.1:{PORT}", f"localhost:{PORT}"}
TOKEN = secrets.token_urlsafe(18)
PAGE = (pathlib.Path(__file__).resolve().parent / "index.html").read_text().replace("__TOKEN__", TOKEN)
INBOX = paths.TRIAGE / "inbox.log"
REVIEW = paths.TRIAGE / "review-latest.json"


def outbox_today():
    today = datetime.date.today().isoformat()
    rows = []
    if say.OUTBOX.exists():
        for line in say.OUTBOX.read_text(encoding="utf-8").splitlines():
            try:
                row = json.loads(line)
            except ValueError:
                continue
            if row.get("at", "").startswith(today):
                rows.append(row)
    return json.dumps(rows)


class Handler(http.server.BaseHTTPRequestHandler):
    def reply(self, code, body, ctype="text/plain"):
        data = body.encode()
        self.send_response(code)
        self.send_header("Content-Type", f"{ctype}; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.headers.get("Host") not in HOSTS:
            return self.reply(403, "forbidden")
        if self.path == "/":
            return self.reply(200, PAGE, "text/html")
        if self.path == "/review.json":
            if not REVIEW.exists():
                return self.reply(404, "no review yet")
            return self.reply(200, REVIEW.read_text(), "application/json")
        if self.path == "/outbox.json":
            return self.reply(200, outbox_today(), "application/json")
        self.reply(404, "not found")

    def do_POST(self):
        if (self.path != "/send" or self.headers.get("Host") not in HOSTS
                or not secrets.compare_digest(self.headers.get("X-Token", ""), TOKEN)):
            return self.reply(403, "forbidden")
        n = int(self.headers.get("Content-Length") or 0)
        if n > 8000:
            return self.reply(413, "too long")
        text = " ".join(self.rfile.read(n).decode("utf-8", "replace").split())  # one line per click
        if not text.startswith("Review deck, SR-"):
            return self.reply(400, "bad message")
        with open(INBOX, "a", encoding="utf-8") as fh:
            fh.write(text + "\n")
        m = re.match(r"Review deck, SR-(\d+):\s*(.*)", text)
        if m:
            say.append(m[1], "duq", m[2])
        self.reply(200, "ok")

    def log_message(self, *args):
        pass


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--open", action="store_true", help="open the deck in the browser")
    args = ap.parse_args()
    INBOX.touch()
    try:
        server = http.server.ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    except OSError:
        sys.exit(f"port {PORT} is busy: is a deck already running? (lsof -i :{PORT})")
    url = f"http://127.0.0.1:{PORT}/"
    print(f"review deck: {url}  inbox: {INBOX}", flush=True)
    if args.open:
        webbrowser.open(url)
    server.serve_forever()


if __name__ == "__main__":
    main()
