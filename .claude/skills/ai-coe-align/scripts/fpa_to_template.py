"""One-time: reconcile FP&A's 'FP&A 2.0' and 'FP&A' sheets into one template sheet.
Usage: python fpa_to_template.py <source.xlsx> <out.xlsx>   (source is only read)"""
import os, re, sys, openpyxl
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # -I drops the script dir
from template_writer import write

FS = re.compile(r"^(IS|IS26|SR)-\d+$")

def main(src, out):
    vals = openpyxl.load_workbook(src, data_only=True)
    fmls = openpyxl.load_workbook(src)
    v2, f2 = vals["FP&A 2.0"], fmls["FP&A 2.0"]
    hdr = [str(c.value).strip() if c.value else None for c in v2[3]]
    ix = {h: i for i, h in enumerate(hdr) if h}
    summ = {r[0]: r[2] for r in vals["FP&A"].iter_rows(min_row=4, values_only=True) if r[0]}

    src_rows = [(r, row) for r, row in enumerate(v2.iter_rows(min_row=4, values_only=True), start=4) if row[0]]
    nxt = max(int(row[0][4:]) for _, row in src_rows if row[0].startswith("FPA-")) + 1
    rows, review = [], []
    for r, row in src_rows:
        g = lambda h: row[ix[h]]
        code, ticket = g("Code"), g("Fresh Service Ticket")
        if FS.match(code): ticket, code, nxt = ticket or code, f"FPA-{nxt:02d}", nxt + 1
        st0, pct = (g("Status") or "").strip(), g("% Complete")
        status = {"Completed": "Production", "On-going": "Production"}.get(st0, "Backlog")
        hrs = g("Monthly Hrs Saved")
        hf = f2.cell(r, ix["Monthly Hrs Saved"] + 1).value
        hours = hf if isinstance(hf, str) and hf.startswith("=") else (hrs if isinstance(hrs, (int, float)) else None)
        notes = [str(g("Description") or "").strip()]
        if g("Notes"): notes.append(str(g("Notes")).strip())
        partial = isinstance(pct, (int, float)) and pct < 1
        if partial: notes.append(f"{pct:.0%} complete.")
        orig = row[0]
        if orig in summ and isinstance(hrs, (int, float)) and abs(summ[orig] - hrs) > 0.5:
            notes.append(f"Summary sheet said {summ[orig]:g} hrs/month; 2.0 sheet said {hrs:g}.")
            if partial:  # 2.0 hours on partial builds read as full-build targets; summary looks like realized
                notes.append(f"Target {hrs:g} hrs/month at full build.")
                hours = summ[orig]
            review.append((code, g("Project Name"), summ[orig], hrs, f"{pct:.0%}" if isinstance(pct,(int,float)) else pct))
        if status == "Backlog":
            if isinstance(hrs, (int, float)): notes.append(f"Est. {hrs:g} hrs/month.")
            hours = None
        if st0 not in ("Completed", "On-going"): notes.append(f"FP&A status: {st0}.")
        rows.append({"Project Code": code, "Freshservice Ticket": ticket, "Status": status,
                     "Project Name": g("Project Name"), "Business Area": "FP&A", "Owner": g("Owner"),
                     "Tool": g("AI Tool / Method"), "Hours Saved Per Month": hours, "Labor $": 50,
                     "Comments": " ".join(n.rstrip(".") + "." for n in notes if n)})
    missing = set(summ) - {row[0] for _, row in src_rows}
    assert not missing, f"summary rows not on 2.0 sheet: {missing}"
    write(rows, out, "FP&A (template)", "tbl_fpa")
    from collections import Counter
    print(len(rows), "rows;", Counter(r["Status"] for r in rows))
    print("partial builds (2.0 hours may be targets):",
          [(r["Project Code"], r["Comments"].split(" complete")[0].split()[-1]) for r in rows if " complete." in r["Comments"]])
    print("summary vs 2.0 conflicts (code, name, summary, 2.0, pct):"); [print("  ", x) for x in review]

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
