"""Write rows to a NEW clean workbook in the department template layout (Status in C).
Never use openpyxl to rewrite a department's existing workbook: Excel rejects the result."""
import openpyxl
from openpyxl.worksheet.table import Table, TableStyleInfo, TableFormula, TableColumn
from openpyxl.worksheet.datavalidation import DataValidation

STATUS = ["Scoping","Open","Backlog","Blocked","Development","UAT","Production","Production - Recent","Production - Dead","Parking Lot"]
HEAD = ["Project Code","Freshservice Ticket","Status","Project Name","Business Area","Owner","Tool",
        "Hours Saved Per Month","Labor $","Savings per Year","Comments"]

def write(rows, outpath, sheet, tbl):
    """rows: dicts keyed by HEAD (Savings per Year is filled with the table formula)."""
    assert all(r["Status"] in STATUS for r in rows)
    codes = [r["Project Code"] for r in rows]
    assert len(set(codes)) == len(codes), "duplicate Project Code"
    f = f"{tbl}[[#This Row],[Hours Saved Per Month]]*{tbl}[[#This Row],[Labor $]]*12"
    wb = openpyxl.Workbook(); ws = wb.active; ws.title = sheet
    ws.append(HEAD)
    for r in rows:
        ws.append([("=" + f) if h == "Savings per Year" else r.get(h) for h in HEAD])
    end = len(rows) + 1
    t = Table(displayName=tbl, ref=f"A1:K{end}",
              tableStyleInfo=TableStyleInfo(name="TableStyleMedium2", showRowStripes=True))
    t.tableColumns = [TableColumn(id=i, name=h) for i, h in enumerate(HEAD, start=1)]  # must match header cells
    t.tableColumns[9].calculatedColumnFormula = TableFormula(attr_text=f)
    ws.add_table(t)
    dv = DataValidation(type="list", formula1='"' + ",".join(STATUS) + '"', allow_blank=True)
    ws.add_data_validation(dv); dv.add(f"C2:C{end+500}")
    for c, w in zip("ABCDEFGHIJK", [11,14,18,44,12,16,14,12,10,14,90]):
        ws.column_dimensions[c].width = w
    for i in range(2, end + 1):
        ws[f"I{i}"].number_format = ws[f"J{i}"].number_format = '"$"#,##0'
    ws.freeze_panes = "A2"
    wb.save(outpath)
