#!/usr/bin/env python
"""IT Planning Scorecard: clone the last slide onto a working copy of the deck.

Usage: build_slide.py peek          print the deck's last slide (no writes)
       build_slide.py <spec.json>   build the slide on a working copy

Spec keys:
  workdir  session scratchpad; gets it-scorecard-backup.pptx (untouched)
           and it-scorecard-work.pptx (edited)
  mode     "add" (clone a new slide) or "update" (refresh the last slide)
  roadmap  path to a fresh Tableau Roadmap PNG, or null to keep the picture
  date     YYYY-MM-DD for the label, default today
  title    list of lines for the Top Goals box, or null to keep it
  bullets  list of [text, bold] for the status box, or null to keep it

Never writes the real deck; deploy.sh does that after PowerPoint validation.

Cloning is python-pptx library-native on purpose (copied from ai-scorecard's
update_slide.py). NEVER hand-edit package XML/rels at the zip level: slides
carry notesSlide and tags relationships, and sharing a notes part between two
slides corrupts the package.
"""
import copy
import datetime
import json
import shutil
import sys
import warnings

warnings.filterwarnings("ignore")

from pptx import Presentation
from pptx.oxml.ns import qn

DECK = ("/Users/jjduqu/Library/CloudStorage/OneDrive-SharedLibraries-PADNOS/"
        "Information Solutions - General/IT Planning Scorecard.pptx")
TITLE_ID, LABEL_ID, BULLETS_ID, ROADMAP_ID = 4, 5, 3, 10
# shortcut: fixed crop of the 2200x2500 dashboard render down to the chart area
# (drops title + filter panel), redo if the dashboard size or layout changes
RENDER_SIZE = (2200, 2500)
CROP = dict(left=550 / 2200, right=10 / 2200, top=169 / 2500, bottom=625 / 2500)


def clone_last_slide(prs):
    src = prs.slides[-1]
    new = prs.slides.add_slide(src.slide_layout)
    for shp in list(new.shapes):  # drop layout placeholders
        shp._element.getparent().remove(shp._element)
    skip = {qn("p:nvGrpSpPr"), qn("p:grpSpPr")}
    for child in src.shapes._spTree:  # copy shapes only (no notes/tags)
        if child.tag not in skip:
            new.shapes._spTree.append(copy.deepcopy(child))
    rid_map = {rId: new.part.relate_to(rel.target_part, rel.reltype)
               for rId, rel in src.part.rels.items() if "image" in rel.reltype}
    for el in new.shapes._spTree.iter():  # remap image refs
        for attr in (qn("r:embed"), qn("r:link")):
            if el.get(attr) in rid_map:
                el.set(attr, rid_map[el.get(attr)])
    valid = set(new.part.rels)  # no dangling relationship ids may remain
    for el in new.shapes._spTree.iter():
        for name, value in el.attrib.items():
            if name.startswith("{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"):
                assert value in valid, f"dangling relationship {value}"
    return new


def swap_roadmap(slide, old, png):
    """Add the new picture at the old one's spot and z-order, then drop the old."""
    pic = slide.shapes.add_picture(png, old.left, old.top, height=old.height)
    assert pic.image.size == RENDER_SIZE, (
        f"render is {pic.image.size}, crop assumes {RENDER_SIZE}: dashboard changed")
    for side, frac in CROP.items():
        setattr(pic, f"crop_{side}", frac)
    w = (1 - CROP["left"] - CROP["right"]) * RENDER_SIZE[0]
    h = (1 - CROP["top"] - CROP["bottom"]) * RENDER_SIZE[1]
    pic.width = int(old.height * w / h)  # keep height and left edge, fix aspect
    pic.name = old.name
    old_rid = old._element.blip_rId
    old._element.addprevious(pic._element)
    old._element.getparent().remove(old._element)
    pic._element.nvPicPr.cNvPr.id = ROADMAP_ID  # next run finds it by id
    slide.part.drop_rel(old_rid)  # drops only once nothing references it


def set_lines(shape, lines):
    """Rewrite a text box one paragraph per line. Line i takes paragraph i's
    formatting (the goals title is a heading then a numbered list); extra
    lines reuse the last one. lines: list of (text, bold or None)."""
    txBody = shape.text_frame._txBody
    tmpls = [copy.deepcopy(p._p) for p in shape.text_frame.paragraphs]
    for para in list(shape.text_frame.paragraphs):
        txBody.remove(para._p)
    for i, (text, bold) in enumerate(lines):
        txBody.append(copy.deepcopy(tmpls[min(i, len(tmpls) - 1)]))
        para = shape.text_frame.paragraphs[-1]
        for r in para.runs[1:]:
            r._r.getparent().remove(r._r)
        para.runs[0].text = text
        para.runs[0].font.bold = bold


def dump(slide):
    for sh in slide.shapes:
        if sh.has_text_frame:
            print(f"--- shape {sh.shape_id}")
            for pi, p in enumerate(sh.text_frame.paragraphs):
                print(f"  p{pi}: {p.text}")
        elif sh.shape_type == 13:
            print(f"--- picture {sh.shape_id} {sh.name}: {sh.image.size}, "
                  f"{sh.width / 914400:.2f}x{sh.height / 914400:.2f} in")


def main():
    if sys.argv[1] == "peek":
        prs = Presentation(DECK)
        print(f"slides: {len(prs.slides)}")
        dump(prs.slides[-1])
        return
    spec = json.load(open(sys.argv[1]))
    day = datetime.date.fromisoformat(spec["date"]) if spec.get("date") else datetime.date.today()
    work = f"{spec['workdir']}/it-scorecard-work.pptx"
    shutil.copy2(DECK, f"{spec['workdir']}/it-scorecard-backup.pptx")
    shutil.copy2(DECK, work)

    prs = Presentation(work)
    slide = clone_last_slide(prs) if spec["mode"] == "add" else prs.slides[-1]
    shapes = {sh.shape_id: sh for sh in slide.shapes}
    missing = {TITLE_ID, LABEL_ID, BULLETS_ID, ROADMAP_ID} - set(shapes)
    assert not missing, f"layout drifted: shape ids {missing} not found"

    set_lines(shapes[LABEL_ID], [(f"{day.year} Plan – {day:%b} {day.day} {day.year} Update", None)])
    if spec.get("title") is not None:
        set_lines(shapes[TITLE_ID], [(t, None) for t in spec["title"]])
    if spec.get("bullets") is not None:
        set_lines(shapes[BULLETS_ID], [(t, b or None) for t, b in spec["bullets"]])
    if spec.get("roadmap"):
        swap_roadmap(slide, shapes[ROADMAP_ID], spec["roadmap"])
    prs.save(work)

    verify = Presentation(work)
    print(f"slides: {len(verify.slides)}")
    dump(verify.slides[-1])
    print(f"\nworking copy: {work}")


if __name__ == "__main__":
    main()
