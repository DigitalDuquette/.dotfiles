#!/usr/bin/env python3
"""Turn the claude.ai admin Usage page text into the weekly spend handoff.

Input: TSV pulled from claude.ai/admin-settings/usage by the friday-packet JS snippet:
  TOTAL<TAB>6,585.71          (page header "$X spent")
  email<TAB>name<TAB>1,174.33 (one line per user with MTD > 0)
  ROWS<TAB>33                 (row count the page reported, guards a dropped line)
Output:
  - clipboard: a Claude in Excel prompt (points at G1) plus the export as TSV
  - ~/Downloads/claude-overage-YYYY-MM-DD.png: table image for the email body
Exits 1 if the per-user sum is more than $1 away from the page header total.

Usage: claude_spend.py <page.txt> | --selftest
"""
import datetime
import html
import pathlib
import subprocess
import sys
import tempfile

CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"


def money(s):
    return float(s.replace(",", "").lstrip("$"))


def parse(text):
    """Return (header_total, [(email, name, mtd)]) with mtd > 0, highest first."""
    header, expected, rows = None, None, []
    for line in text.strip().splitlines():
        f = line.split("\t")
        if f[0] == "TOTAL":
            header = money(f[1])
        elif f[0] == "ROWS":
            expected = int(f[1])
        elif len(f) == 3 and "@" in f[0] and money(f[2]) > 0:
            rows.append((f[0].strip(), f[1].strip(), money(f[2])))
        else:
            sys.exit(f"error: unexpected line: {line!r}")
    if header is None or expected != len(rows):
        sys.exit(f"error: need TOTAL and ROWS lines; got {len(rows)} rows, ROWS={expected}")
    rows.sort(key=lambda r: -r[2])
    return header, rows


def check(header, rows):
    total = round(sum(r[2] for r in rows), 2)
    if not rows or abs(total - header) > 1.00:
        sys.exit(f"error: users sum to ${total:,.2f} but header says ${header:,.2f}. "
                 "Page may be paged or still loading. Stop and look.")
    return total


def prompt(rows, today):
    tsv = "\n".join(f"{e}\t{n}\t${m:,.2f}" for e, n, m in rows)
    return (f"Use the instructions in cell G1 of the claude-overage sheet. "
            f"Export date: {today:%Y-%m-%d} ({today:%B %Y}).\n---\n"
            f"Email\tName\tMTD Spend\n{tsv}\n")


def render(rows, total, today, out):
    trs = "".join(
        f"<tr><td>{html.escape(e)}</td><td>{html.escape(n)}</td><td class=n>${m:,.2f}</td></tr>"
        for e, n, m in rows)
    page = f"""<!doctype html><meta charset=utf-8><style>
body{{margin:0;padding:16px;font:14px Calibri,Arial,sans-serif;background:#fff}}
h1{{font-size:16px;margin:0 0 8px}}table{{border-collapse:collapse;width:100%}}
th{{background:#4472c4;color:#fff;text-align:left;padding:4px 8px}}
td{{padding:3px 8px}}tr:nth-child(even) td{{background:#d9d9d9}}.n{{text-align:right}}
tfoot td{{font-weight:bold;border-top:2px solid #000}}</style>
<h1>Claude usage overage, {today:%B %Y} MTD as of {today:%b %-d}</h1>
<table><thead><tr><th>Email</th><th>Name</th><th class=n>MTD Spend</th></tr></thead>
<tbody>{trs}</tbody><tfoot><tr><td></td><td>Total ({len(rows)} users)</td>
<td class=n>${total:,.2f}</td></tr></tfoot></table>"""
    with tempfile.TemporaryDirectory() as tmp:
        src = pathlib.Path(tmp, "t.html")
        src.write_text(page)
        height = 70 + 22 * (len(rows) + 2)
        subprocess.run([CHROME, "--headless=new", f"--user-data-dir={tmp}/p", "--hide-scrollbars",
                        "--force-device-scale-factor=2", f"--window-size=620,{height}",
                        f"--screenshot={out}", src.as_uri()],
                       check=True, capture_output=True, timeout=60)


def selftest():
    sample = "TOTAL\t12.50\nsandy@x.com\tSandy Gregory\t2.50\npaul@x.com\tPaul\t10.00\nROWS\t2\n"
    header, rows = parse(sample)
    assert header == 12.50
    assert rows == [("paul@x.com", "Paul", 10.0), ("sandy@x.com", "Sandy Gregory", 2.5)], rows
    assert check(header, rows) == 12.50
    print("selftest ok")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    if sys.argv[1] == "--selftest":
        selftest()
        sys.exit()
    today = datetime.date.today()
    header, rows = parse(pathlib.Path(sys.argv[1]).read_text())
    total = check(header, rows)
    subprocess.run(["pbcopy"], input=prompt(rows, today).encode(), check=True)
    out = pathlib.Path.home() / "Downloads" / f"claude-overage-{today:%Y-%m-%d}.png"
    render(rows, total, today, out)
    print(f"{len(rows)} users, ${total:,.2f} (header ${header:,.2f})")
    print(f"clipboard: Claude in Excel prompt + export")
    print(f"image: {out}")
