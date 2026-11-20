#!/usr/bin/env python3
"""git-watcher: keep personal repos committed and pushed.

Runs every 15 min from launchd (cos.sh watch). For each repo in watch.json:

  1. Skip if git is busy (index.lock, rebase/merge in progress) or not on the branch.
  2. If there are changes:
       - "active" (a changed file was touched within quiet_minutes) -> wait,
         unless changes have been pending >= force_after_hours, then commit anyway.
       - guards: iCloud-evicted files and mass deletions block the commit;
         secret-looking files are left out of the commit.
       - commit with a generated message (summary subject + file list body).
  3. Sync: fetch, rebase onto origin if behind (only with a clean tree), push if ahead.

cos.sh turns stdout into a macOS notification, so the script prints ONLY problems that need a human
(deduped: the same problem is repeated at most every alert_repeat_hours).
Every run is logged to ~/.local/state/cos/repo-watch.jsonl.

Manual use:
  python3 repo_watch.py --dry-run -v          # show what would happen, change nothing
  python3 repo_watch.py -v --repo padnos-obsidian-vault
Stdlib only; Python 3.9+.
"""
import argparse
import datetime as dt
import fcntl
import hashlib
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

CONFIG = Path(__file__).resolve().parent / "watch.json"
STATE_DIR = Path(os.environ.get("COS_STATE") or Path.home() / ".local/state/cos")
STATE_FILE = STATE_DIR / "repo-watch.json"
LOCK_FILE = STATE_DIR / "repo-watch.lock"
LOG_FILE = STATE_DIR / "repo-watch.jsonl"

GIT_ENV = dict(os.environ, GIT_TERMINAL_PROMPT="0", GIT_OPTIONAL_LOCKS="0", LC_ALL="C")
# cron may run with a thin PATH; make sure gh/osxkeychain helpers resolve
GIT_ENV["PATH"] = ":".join([GIT_ENV.get("PATH", ""), "/opt/homebrew/bin", "/usr/local/bin", "/usr/bin", "/bin"])


def now():
    return time.time()


def iso(ts=None):
    return dt.datetime.fromtimestamp(ts or now()).astimezone().isoformat(timespec="seconds")


class GitError(Exception):
    pass


def git(repo, *args, check=True, timeout=120):
    try:
        p = subprocess.run(["git", "-C", str(repo)] + list(args), capture_output=True, text=True,
                           env=GIT_ENV, timeout=timeout)
    except subprocess.TimeoutExpired:
        # network hiccups (e.g. right after wake) are transient; report like a failed command
        p = subprocess.CompletedProcess(args, 124, "", "timed out after %ss" % timeout)
    if check and p.returncode != 0:
        raise GitError("git %s: %s" % (" ".join(args), (p.stderr or p.stdout).strip()[:500]))
    return p


SIGNING_ERR = re.compile(r"1Password|failed to fill whole buffer|gpg failed|signing failed|"
                         r"error: (?:couldn't|could not) sign|ssh-keygen", re.I)


def user_present():
    """(present, reason). Only run with the lid open and the screen unlocked.
    A closed lid means sleep/DarkWake (network flaky, 1Password locked so commit signing fails)."""
    try:
        out = subprocess.run(["ioreg", "-r", "-k", "AppleClamshellState", "-d", "4"],
                             capture_output=True, text=True, timeout=10).stdout
        if re.search(r'"AppleClamshellState" = Yes', out):
            return False, "lid closed"
        out = subprocess.run(["ioreg", "-n", "Root", "-d1"], capture_output=True, text=True, timeout=10).stdout
        if re.search(r'"CGSSessionScreenIsLocked"\s*=\s*Yes', out):
            return False, "screen locked"
    except Exception:
        pass  # can't tell: run normally
    return True, ""


# ---------- change inspection ----------

def status_entries(repo):
    """[(xy, path)] from porcelain -z, untracked files listed individually."""
    out = git(repo, "status", "--porcelain=v1", "-z", "--untracked-files=all").stdout
    parts = out.split("\0")
    entries, i = [], 0
    while i < len(parts):
        rec = parts[i]
        if not rec:
            i += 1
            continue
        xy, path = rec[:2], rec[3:]
        entries.append((xy, path))
        i += 2 if ("R" in xy or "C" in xy) else 1  # rename/copy carries the old path next
    if not entries:
        return entries
    # status flags files whose size differs from the index even when a clean filter
    # (e.g. cron/jobs.json runtime fields) makes the content identical; confirm with a
    # content-level diff against HEAD, which runs the filters.
    real = set(git(repo, "diff", "HEAD", "--name-only", "-z", "--no-renames").stdout.split("\0"))
    return [(xy, p) for xy, p in entries if xy == "??" or p in real]


def newest_mtime(repo, entries):
    newest = 0.0
    for xy, path in entries:
        if "D" in xy:
            continue
        try:
            newest = max(newest, os.lstat(os.path.join(repo, path)).st_mtime)
        except OSError:
            pass
    return newest


def icloud_evicted(repo, entries):
    """Deleted paths that are really iCloud evictions (.<name>.icloud placeholder present)."""
    hits = []
    for xy, path in entries:
        if "D" in xy:
            d, name = os.path.split(path)
            if os.path.exists(os.path.join(repo, d, "." + name + ".icloud")):
                hits.append(path)
    return hits


def secret_hits(repo, paths, cfg):
    path_res = [re.compile(p) for p in cfg.get("secret_path_patterns", [])]
    content_res = [re.compile(p) for p in cfg.get("secret_content_patterns", [])]
    hits = []
    for path in paths:
        if any(r.search(path) for r in path_res):
            hits.append((path, "filename"))
            continue
        full = os.path.join(repo, path)
        try:
            if os.path.getsize(full) > 2_000_000:
                continue
            with open(full, "rb") as fh:
                data = fh.read()
            if b"\0" in data[:8000]:
                continue
            text = data.decode("utf-8", "replace")
        except OSError:
            continue
        for r in content_res:
            if r.search(text):
                hits.append((path, "content /%s/" % r.pattern[:30]))
                break
    return hits


def staged_name_status(repo):
    out = git(repo, "diff", "--cached", "--name-status", "-z", "-M").stdout.split("\0")
    rows, i = [], 0
    while i < len(out):
        st = out[i]
        if not st:
            i += 1
            continue
        if st[0] in "RC":
            rows.append((st[0], out[i + 2], out[i + 1]))  # (status, new, old)
            i += 3
        else:
            rows.append((st[0], out[i + 1], None))
            i += 2
    return rows


def area_of(path, depth):
    parts = path.split("/")
    if len(parts) == 1:
        return parts[0]
    return "/".join(parts[:min(depth, len(parts) - 1)])


def build_message(rows, rcfg, forced):
    counts = {}
    for st, _, _ in rows:
        counts[st] = counts.get(st, 0) + 1
    labels = {"A": "added", "M": "modified", "D": "deleted", "R": "renamed", "C": "copied", "T": "type changed"}
    count_txt = ", ".join("%d %s" % (n, labels.get(s, s)) for s, n in sorted(counts.items()))
    areas = []
    for _, path, _ in rows:
        a = area_of(path, rcfg["area_depth"])
        if a not in areas:
            areas.append(a)
    area_txt = ", ".join(areas[:3]) + (" +%d more" % (len(areas) - 3) if len(areas) > 3 else "")
    n = len(rows)
    subject = "%s: %s (%d file%s)" % (rcfg["subject_prefix"], area_txt, n, "" if n == 1 else "s")
    body = [count_txt, ""]
    for st, path, old in rows[:200]:
        body.append("%s  %s" % (st, path if not old else "%s -> %s" % (old, path)))
    if n > 200:
        body.append("... and %d more" % (n - 200))
    body.append("")
    if forced:
        body.append("Forced: changes were pending past %dh while files kept changing." % rcfg["force_after_hours"])
    body.append("Committed-by: git-watcher")
    return subject, "\n".join(body)


# ---------- per-repo run ----------

def process_repo(rcfg, cfg, rstate, args):
    repo = Path(os.path.expanduser(rcfg["path"]))
    res = {"repo": rcfg["name"], "actions": [], "problems": []}
    act, prob = res["actions"].append, res["problems"].append
    dry = args.dry_run

    if not (repo / ".git").exists():
        prob("not a git repo: %s" % repo)
        return res
    gitdir = repo / ".git"
    lock = gitdir / "index.lock"
    if lock.exists():
        age = (now() - lock.stat().st_mtime) / 60
        if age > 30:
            prob("stale .git/index.lock (%d min old); remove it if no git process is running" % age)
        else:
            act("git busy (index.lock); skipped")
        return res
    for marker, what in (("rebase-merge", "rebase"), ("rebase-apply", "rebase/am"), ("MERGE_HEAD", "merge"),
                         ("CHERRY_PICK_HEAD", "cherry-pick")):
        if (gitdir / marker).exists():
            # our own rebase, cut off mid-run (lid closed, killed)? We record the exact commit we
            # rebase onto BEFORE starting; only a rebase onto that same commit is ours to abort.
            # A rebase you started yourself is never touched.
            mine = rstate.get("rebasing")
            if marker == "rebase-merge" and mine and not dry:
                try:
                    onto = (gitdir / marker / "onto").read_text().strip()
                except OSError:
                    onto = ""
                if onto and onto == mine.get("onto"):
                    git(repo, "rebase", "--abort", check=False)
                    if not (gitdir / marker).exists():
                        rstate.pop("rebasing", None)
                        act("aborted the rebase our interrupted run left behind")
                        continue
            prob("%s in progress; needs a human to finish or abort" % what)
            return res
    rstate.pop("rebasing", None)  # no rebase in progress: any old record is stale
    branch = git(repo, "rev-parse", "--abbrev-ref", "HEAD").stdout.strip()
    if branch != rcfg["branch"]:
        prob("on branch '%s', expected '%s'; not touching it" % (branch, rcfg["branch"]))
        return res

    # ---- commit ----
    skip_sync = False
    entries = status_entries(repo)
    if entries:
        rstate.setdefault("pending_since", now())
        pending_h = (now() - rstate["pending_since"]) / 3600
        idle_min = (now() - newest_mtime(repo, entries)) / 60
        forced = False
        if idle_min < rcfg["quiet_minutes"]:
            if pending_h >= rcfg["force_after_hours"]:
                forced = True
                act("active editing but changes pending %.1fh; forcing commit" % pending_h)
            else:
                act("active editing (last change %.1f min ago); waiting" % idle_min)
        if idle_min >= rcfg["quiet_minutes"] or forced:
            evicted = icloud_evicted(repo, entries)
            deletions = [p for xy, p in entries if "D" in xy]
            if evicted:
                prob("%d file(s) look iCloud-evicted (placeholder .icloud present), not committing their "
                     "deletion: %s. Download them in Finder (or turn off Optimize Mac Storage)."
                     % (len(evicted), ", ".join(evicted[:5])))
            elif len(deletions) > rcfg["max_deletions"]:
                prob("%d deleted files (limit %d); not auto-committing. Commit by hand if intended. e.g. %s"
                     % (len(deletions), rcfg["max_deletions"], ", ".join(deletions[:5])))
            else:
                candidates = [p for xy, p in entries if "D" not in xy]
                bad = secret_hits(repo, candidates, cfg)
                bad_paths = [p for p, _ in bad]
                if bad:
                    prob("left out of commit (looks like a secret): " +
                         "; ".join("%s [%s]" % (p, why) for p, why in bad[:5]))
                if dry:
                    act("DRY RUN: would commit %d path(s)" % (len(entries) - len(bad_paths)))
                else:
                    git(repo, "add", "-A")
                    if bad_paths:
                        git(repo, "reset", "-q", "--", *bad_paths)
                    rows = staged_name_status(repo)
                    if rows:
                        subject, body = build_message(rows, rcfg, forced)
                        c = git(repo, "commit", "-q", "--no-verify", "-m", subject, "-m", body, check=False)
                        if c.returncode != 0:
                            git(repo, "reset", "-q", check=False)  # leave the index as we found it
                            err = (c.stderr or c.stdout).strip()
                            if SIGNING_ERR.search(err):
                                act("commit signing unavailable (1Password locked?); retry next run")
                                skip_sync = True  # nothing new to push; try again next run
                            else:
                                raise GitError("git commit: %s" % err[:300])
                        else:
                            sha = git(repo, "rev-parse", "--short", "HEAD").stdout.strip()
                            act("committed %s %s" % (sha, subject))
                            res["committed"] = sha
                            if not bad_paths:
                                rstate.pop("pending_since", None)
                    elif not bad_paths:
                        rstate.pop("pending_since", None)
        # the daily-backup promise: say so if changes have been stuck uncommitted too long
        if "pending_since" in rstate:
            stuck_h = (now() - rstate["pending_since"]) / 3600
            if stuck_h >= rcfg["force_after_hours"] + 2:
                prob("changes uncommitted for %.0fh (last attempt: %s)"
                     % (stuck_h, res["actions"][-1] if res["actions"] else "n/a"))
        if skip_sync:
            return res
    else:
        rstate.pop("pending_since", None)

    # ---- sync ----
    remote, br = rcfg["remote"], rcfg["branch"]
    upstream = "%s/%s" % (remote, br)
    f = git(repo, "fetch", "-q", remote, br, check=False, timeout=90)
    if f.returncode != 0:
        act("fetch failed: %s" % f.stderr.strip()[:200])
        _stale_push_check(repo, upstream, rstate, prob)
        return res
    ahead, behind = (int(x) for x in git(repo, "rev-list", "--left-right", "--count",
                                          "HEAD...%s" % upstream).stdout.split())
    # untracked leftovers (e.g. a held-back secret file) don't block a rebase; tracked edits do
    clean = not [p for xy, p in status_entries(repo) if xy != "??"]
    if behind:
        if not clean:
            act("behind %s by %d but tree has uncommitted edits; rebase next run" % (upstream, behind))
        elif dry:
            act("DRY RUN: would rebase onto %s (behind %d)" % (upstream, behind))
        else:
            onto = git(repo, "rev-parse", upstream).stdout.strip()
            rstate["rebasing"] = {"onto": onto, "at": now()}
            args.persist()  # on disk before we start, so an interrupted run can be recognised
            r = git(repo, "rebase", "-q", upstream, check=False, timeout=120)
            if r.returncode != 0:
                git(repo, "rebase", "--abort", check=False)
                rstate.pop("rebasing", None)
                msg = [l for l in (r.stderr + r.stdout).splitlines() if l.strip() and not l.startswith("hint:")]
                prob("rebase onto %s conflicted; aborted, local commits kept (ahead %d, behind %d). "
                     "Resolve by hand with `git pull --rebase`. %s"
                     % (upstream, ahead, behind, " | ".join(msg[:3])[:300]))
                return res
            rstate.pop("rebasing", None)
            act("rebased onto %s (+%d from remote)" % (upstream, behind))
            ahead, behind = (int(x) for x in git(repo, "rev-list", "--left-right", "--count",
                                                  "HEAD...%s" % upstream).stdout.split())
    if ahead and not behind:
        if dry:
            act("DRY RUN: would push %d commit(s)" % ahead)
        else:
            p = git(repo, "push", "-q", remote, "HEAD:%s" % br, check=False, timeout=120)
            if p.returncode != 0:
                act("push failed: %s" % (p.stderr or p.stdout).strip()[:200])
            else:
                act("pushed %d commit(s)" % ahead)
                rstate["last_push"] = now()
                res["in_sync"] = True
    if not ahead and not behind:
        rstate["last_in_sync"] = now()
        res["in_sync"] = True
    _stale_push_check(repo, upstream, rstate, prob)
    return res


def _stale_push_check(repo, upstream, rstate, prob):
    """Alert if commits have sat unpushed for over a day (push/fetch keeps failing)."""
    p = git(repo, "log", "--format=%ct", "%s..HEAD" % upstream, check=False)
    times = [int(t) for t in p.stdout.split()] if p.returncode == 0 else []
    if times and (now() - min(times)) > 24 * 3600:
        prob("%d commit(s) unpushed for over 24h (oldest %s); check network/auth"
             % (len(times), iso(min(times))[:16]))


# ---------- main ----------

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true", help="inspect only; no commit/rebase/push")
    ap.add_argument("-v", "--verbose", action="store_true", help="print all actions, not just problems")
    ap.add_argument("--repo", help="only this repo (name from watch.json)")
    ap.add_argument("--force", action="store_true", help="run even with the lid closed / screen locked")
    args = ap.parse_args()

    cfg = json.loads(CONFIG.read_text())
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

    lockfh = open(LOCK_FILE, "w")
    try:
        fcntl.flock(lockfh, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        if args.verbose:
            print("another repo_watch run is in progress; exiting")
        return 0

    present, why = user_present()
    if not present and not args.force:
        # lid closed / screen locked: DarkWake or away. Skip silently; the next
        # run after the lid opens catches up (the 24h force is measured from then).
        if args.verbose:
            print("skipped: %s" % why)
        with open(LOG_FILE, "a") as fh:
            fh.write(json.dumps({"skipped": why, "ts": iso()}) + "\n")
        return 0

    # GitHub reachable? (just woke, captive portal, offline): skip quietly instead of hanging
    if not args.force and not github_reachable():
        if args.verbose:
            print("skipped: github.com unreachable")
        with open(LOG_FILE, "a") as fh:
            fh.write(json.dumps({"skipped": "github.com unreachable", "ts": iso()}) + "\n")
        return 0

    state = json.loads(STATE_FILE.read_text()) if STATE_FILE.exists() else {}

    # run ledger: started -> done. A "started" newer than "done" means the last run was
    # cut off (lid closed, killed); process_repo cleans up a rebase that run left behind
    # (recognised by the per-repo "rebasing" record, not by timing).
    run = state.setdefault("_run", {})
    if run.get("started", 0) > run.get("done", 0):
        with open(LOG_FILE, "a") as fh:
            fh.write(json.dumps({"interrupted_run_started": iso(run["started"]), "ts": iso()}) + "\n")
        if args.verbose:
            print("previous run (started %s) never finished; checking for leftovers" % iso(run["started"]))
    args.persist = (lambda: None) if args.dry_run else (lambda: save_state(state))
    if not args.dry_run:
        run["started"] = now()
        save_state(state)

    out, all_good = [], True
    for r in cfg["repos"]:
        if args.repo and r["name"] != args.repo:
            continue
        rcfg = dict(cfg.get("defaults", {}), **r)
        rstate = state.setdefault(r["name"], {})
        try:
            res = process_repo(rcfg, cfg, rstate, args)
        except Exception as e:  # keep going with the other repos
            res = {"repo": r["name"], "actions": [], "problems": ["error: %s" % e]}
        res["ts"] = iso()
        if res["problems"] or not res.get("in_sync") or "pending_since" in rstate:
            all_good = False
        if not args.dry_run:
            with open(LOG_FILE, "a") as fh:
                fh.write(json.dumps(res) + "\n")

        # dedupe alerts: same problem set -> repeat at most every alert_repeat_hours
        if res["problems"]:
            h = hashlib.sha1("\n".join(res["problems"]).encode()).hexdigest()
            last = rstate.get("alert", {})
            if args.verbose or last.get("hash") != h or now() - last.get("at", 0) > rcfg["alert_repeat_hours"] * 3600:
                out.append("**%s**" % r["name"])
                out.extend("- %s" % p for p in res["problems"])
                if not args.dry_run:
                    rstate["alert"] = {"hash": h, "at": now()}
        else:
            rstate.pop("alert", None)
        if args.verbose:
            out.append("%s: %s" % (r["name"], "; ".join(res["actions"]) or "clean, in sync"))

    if not args.dry_run:
        run["done"] = now()
        if all_good and not args.repo:
            # every repo committed, pushed and in sync: today's backup is done
            run["day_done"] = dt.date.today().isoformat()
            run["day_done_at"] = iso()
        save_state(state)
    if out:
        if not args.verbose:
            print("git-watcher needs a hand:")
        print("\n".join(out))
    return 0


def save_state(state):
    tmp = STATE_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(state, indent=2))
    tmp.replace(STATE_FILE)


def github_reachable(timeout=8):
    import socket
    try:
        socket.create_connection(("github.com", 443), timeout=timeout).close()
        return True
    except OSError:
        return False


if __name__ == "__main__":
    sys.exit(main())
