#!/usr/bin/env python3
"""Put one tbl_rpa_ai row (columns A-K) on the macOS clipboard.

HTML flavor carries the Project Code hyperlink; plain-text TSV is the
fallback. Paste in Excel at column A of the first empty row under the
table: the table grows and fills its formula columns (L, P).

Usage: clip_row.py <row.json>
row.json: {"key", "url", "name", "description", "area", "ai",
           "status", "hours", "labor", "opp_cost"} (missing = blank)
"""
import html
import json
import subprocess
import sys

COLS = ["key", "o", "primary", "name", "description", "area", "ai",
        "status", "hours", "labor", "opp_cost"]


def build(row):
    vals = [str(row.get(c) or "").replace("\t", " ").replace("\n", " ") for c in COLS]
    cells = [f'<a href="{html.escape(row["url"])}">{html.escape(vals[0])}</a>']
    cells += [html.escape(v) for v in vals[1:]]
    page = "<table><tr>" + "".join(f"<td>{c}</td>" for c in cells) + "</tr></table>"
    return page, "\t".join(vals)


def to_applescript_str(s):
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'


def main():
    row = json.load(open(sys.argv[1]))
    page, tsv = build(row)
    script = (f"set the clipboard to {{«class HTML»:«data HTML{page.encode().hex()}», "
              f"string:{to_applescript_str(tsv)}}}")
    subprocess.run(["osascript", "-e", script], check=True)
    print(tsv)


if __name__ == "__main__":
    if sys.argv[1:] == ["--test"]:
        page, tsv = build({"key": "IS26-1", "url": "https://x/?a=1&b=2",
                           "name": "A & B <C>", "ai": "RPA"})
        assert 'href="https://x/?a=1&amp;b=2"' in page
        assert "A &amp; B &lt;C&gt;" in page
        assert tsv.split("\t") == ["IS26-1", "", "", "A & B <C>", "", "", "RPA",
                                   "", "", "", ""]
        assert to_applescript_str('say "hi"') == '"say \\"hi\\""'
        print("ok")
    else:
        main()
