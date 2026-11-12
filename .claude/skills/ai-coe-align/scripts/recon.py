"""Read-only weekly recon: department AI@PADNOS trackers -> master rpa_ai.
Reports only two things:
  1. ADD: department rows in Production that are not in master (newly completed work).
  2. HOURS: matched rows whose Hours Saved Per Month differs from master Hours per Month.
Everything else (status drift, backlog ideas, master-only rows) is ignored by design.
Prints a prompt for Claude in Excel (open the master workbook, paste it).\nUsage: python recon.py [dept folder] [master.xlsx] [out.md]   (copies the prompt to the clipboard)"""
import os, sys, glob, re, subprocess, openpyxl

CLOUD = os.path.expanduser("~/Library/CloudStorage/OneDrive-SharedLibraries-PADNOS")
DEPT_DIR = f"{CLOUD}/Information Solutions - ai-coe/AI@PADNOS"
MASTER = f"{CLOUD}/Information Solutions-aisc - Documents/Artificial Intelligence/AI @ PADNOS.xlsx"

DONE = {"Production", "Production - Recent"}

def norm(s): return re.sub(r"[^a-z0-9 ]", "", str(s or "").lower()).strip()
def num(v): return round(float(v), 2) if isinstance(v, (int, float)) else None
def clean(s): return re.sub(r"\s+", " ", str(s or "")).strip()

def dept_rows(path):
    wb = openpyxl.load_workbook(path, data_only=True)
    for ws in wb:
        if ws.sheet_state != "visible": continue
        for name in ws.tables:
            rng = list(ws[ws.tables[name].ref]); hdr = [c.value for c in rng[0]]
            if "Project Code" in hdr and "Status" in hdr:
                return [dict(zip(hdr, [c.value for c in r])) for r in rng[1:] if r[0].value]
    return None

def main(folder=DEPT_DIR, master=MASTER, out=None):
    M = [m for m in (dict(zip([c.value for c in ws[1]], r)) for ws in
         [openpyxl.load_workbook(master, data_only=True)["rpa_ai"]]
         for r in ws.iter_rows(min_row=2, values_only=True)) if m["Project Code"] or m["Project Name"]]
    by_code, by_name = {}, {}
    for m in M:
        by_code.setdefault(clean(m["Project Code"]), []).append(m)  # master has duplicate codes
        by_name.setdefault((clean(m["Business Area"]), norm(m["Project Name"])), []).append(m)

    adds, hours, skipped = [], [], []
    for f in sorted(glob.glob(folder + "/*.xlsx")):
        dept = f.rsplit(" - ", 1)[-1][:-5]
        D = dept_rows(f)
        if D is None: skipped.append(dept); continue
        for d in D:
            code, ticket = clean(d.get("Project Code")), clean(d.get("Freshservice Ticket"))
            ms = by_code.get(ticket) or by_code.get(code) or by_name.get((dept, norm(d.get("Project Name"))))
            dh = num(d.get("Hours Saved Per Month"))
            if ms:
                mhs = [num(m["Hours per Month"]) for m in ms]
                if dh is not None and dh not in mhs:
                    old = mhs[0] if len(mhs) == 1 else "/".join(map(str, mhs))
                    hours.append((dept, clean(ms[0]["Project Code"]), code, clean(ms[0]["Project Name"]), old, dh))
            elif d.get("Status") in DONE:
                ai = "Skill" if "claude" in str(d.get("Tool") or "").lower() else ""  # shortcut: Claude tools default to Skill; confirm per row
                adds.append((dept, [ticket or code, "", clean(next((v for k, v in d.items() if k and "Owner" in k), "")), clean(d["Project Name"]),
                                    clean(d.get("Comments")), dept, ai, "Production - Recent",
                                    "" if dh is None else dh, d.get("Labor $") or "", ""]))

    COLS = ["Project Code", "o", "Primary", "Project Name", "Description", "Business Area", "AI",
            "Status", "Hours per Month", "Labor $", "Software Opp Cost"]
    tsv = lambda v: clean(v).replace("\t", " ")
    L = ["Update the master AI tracker in this workbook. Sheet `rpa_ai`, table `tbl_rpa_ai`.",
         "Do only the two steps below. Do not change any other cell, row, or column.", ""]
    L += [f"## Step 1: update Hours per Month on {len(hours)} existing rows", ""]
    if hours:
        L += ["Find each row by Project Code AND Project Name. If the code appears more than once, use the row",
              "whose current Hours per Month equals Old. If no row matches, skip it and tell me. Change only",
              "Hours per Month to New. Leave Status and every other column as they are.", "",
              "| Project Code | Project Name (master) | Old | New |", "|---|---|---|---|"]
        L += [f"| {c} | {mn} | {mh} | {dh} |" for _, c, _, mn, mh, dh in hours]
    else:
        L += ["Nothing to update."]
    L += ["", f"## Step 2: add {len(adds)} new rows at the bottom of `tbl_rpa_ai`", ""]
    if adds:
        L += ["Add them inside the table so it grows and calculated columns (like Savings per Year) fill",
              "themselves. Before adding, skip any row whose Project Code already exists in the table and tell me.",
              "Columns are tab-separated, in this order: " + ", ".join(COLS) + ". Blank means leave empty.", "", "```"]
        L += ["\t".join(tsv(v) for v in row) for _, row in adds] + ["```"]
    else:
        L += ["Nothing to add."]
    L += ["", "When done, list: rows updated, rows added, and anything skipped with the reason."]
    text = "\n".join(L) + "\n"
    if out: open(out, "w").write(text)
    subprocess.run(["pbcopy"], input=text.encode(), check=True)
    print(text)
    print("[copied to clipboard] ", end="", file=sys.stderr)
    print(f"[{len(hours)} hour updates, {len(adds)} adds; skipped depts: {', '.join(skipped) or 'none'}]", file=sys.stderr)

if __name__ == "__main__":
    main(*sys.argv[1:4])
