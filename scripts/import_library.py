"""One-off importer for the printable workbook library (school world).

Takes the source PDFs (default ~/Documents/Thavion_content), and writes:
  docs/school/library/pdf/<level>/<file>.pdf    compressed PDFs (whole books + one PDF per week)
  docs/school/library/thumbs/<level>/<file>.jpg first-page thumbnails
  site-src/school/library.json                  the manifest build_library.py renders

Needs Ghostscript (gs) and poppler (pdftotext, pdftoppm). Re-run only when the source content changes;
the generated PDFs are committed because GitHub Pages has no build step.

  python3 scripts/import_library.py [SRC_DIR]
"""
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = Path(sys.argv[1]).expanduser() if len(sys.argv) > 1 else Path.home() / "Documents" / "Thavion_content"
OUT = ROOT / "docs" / "school" / "library"
MANIFEST = ROOT / "site-src" / "school" / "library.json"

GS = ["gs", "-q", "-sDEVICE=pdfwrite", "-dPDFSETTINGS=/ebook", "-dColorImageResolution=130",
      "-dGrayImageResolution=130", "-dCompatibilityLevel=1.5", "-dNOPAUSE", "-dBATCH"]

# Kindergarten books: one PDF per subject holding all 26 weeks; split per week by the "WEEK n" page header.
BOOKS = {
    "a": {"Math": "ThavionAI_Kindergarten_Level_A_Math_26_Weeks.pdf",
          "English": "ThavionAI_Kindergarten_Level_A_English_Illustrated_26_Weeks.pdf",
          "Science": "ThavionAI_Kindergarten_Level_A_Science_26_Weeks.pdf"},
    "b": {"Math": "ThavionAI_Kindergarten_Level_B_Math_26_Weeks.pdf",
          "English": "ThavionAI_Kindergarten_Level_B_English_26_Weeks.pdf",
          "Science": "ThavionAI_Kindergarten_Level_B_Science_26_Weeks.pdf"},
}
# Levels C–E: already one PDF per week (Math + English + Science), with a text guide listing each week's topics.
PACKAGES = {
    "c": ("ThavionAI_Level_C_Complete_26_Week_Package", "Level_C_26_Week_Story_Roadmap.txt"),
    "d": ("ThavionAI_Level_D_Complete_26_Week_Package", "Level_D_26_Week_Guide.txt"),
    "e": ("ThavionAI_Level_E_Complete_26_Week_Package", "Level_E_26_Week_Guide.txt"),
}
EXTRAS = [("coloring-flowers", "Flowers colouring pack", "ThavionAI_Flowers_Coloring_Pack_01.pdf",
           "12 calm flower pictures to colour in — a gentle break between worksheets.")]

WEEK_RE = re.compile(r"\bWEEK\s+(\d{1,2})\b", re.I)


def run(cmd):
    subprocess.run(cmd, check=True)


def compress(src, dst, first=None, last=None):
    dst.parent.mkdir(parents=True, exist_ok=True)
    rng = [f"-dFirstPage={first}", f"-dLastPage={last}"] if first else []
    run(GS + rng + [f"-sOutputFile={dst}", str(src)])


def thumb(pdf, dst):
    dst.parent.mkdir(parents=True, exist_ok=True)
    base = dst.with_suffix("")
    run(["pdftoppm", "-r", "36", "-jpeg", "-jpegopt", "quality=78", "-f", "1", "-l", "1", "-singlefile",
         str(pdf), str(base)])


def page_count(pdf):
    out = subprocess.run(["pdfinfo", str(pdf)], capture_output=True, text=True, check=True).stdout
    return int(re.search(r"Pages:\s+(\d+)", out).group(1))


def page_text(pdf, p):
    return subprocess.run(["pdftotext", "-f", str(p), "-l", str(p), str(pdf), "-"],
                          capture_output=True, text=True, check=True).stdout


def week_ranges(pdf):
    """[(week, first_page, last_page, first_page_text)] from the WEEK n header on each page."""
    n = page_count(pdf)
    weeks = {}
    for p in range(1, n + 1):
        t = page_text(pdf, p)
        m = WEEK_RE.search(t)
        if not m:
            raise SystemExit(f"{pdf.name} p{p}: no WEEK header")
        w = int(m.group(1))
        lo, hi, txt = weeks.get(w, (p, p, t))
        weeks[w] = (lo, p, txt)
    out = [(w, lo, hi, txt) for w, (lo, hi, txt) in sorted(weeks.items())]
    assert [w for w, *_ in out] == list(range(1, 27)), f"{pdf.name}: weeks {[w for w, *_ in out]}"
    for (_, _, hi, _), (_, lo, _, _) in zip(out, out[1:]):
        assert lo == hi + 1, f"{pdf.name}: weeks not contiguous"
    return out


def focus_of(txt):
    """Week topic from the first page's text, e.g. 'Count 0 to 5 - Learn' -> 'Count 0 to 5'."""
    lines = [l.strip() for l in txt.splitlines() if l.strip()]
    for l in lines:
        if WEEK_RE.search(l) or "•" in l or l.lower().startswith(("name", "date")):
            continue
        l = re.sub(r"^Meet the Letter\s+", "Letter ", l)
        return l.split(" - ")[0].strip()
    return ""


def import_book(level, subject, fname):
    src = SRC / fname
    sub = subject.lower()
    full = OUT / "pdf" / level / f"level-{level}-{sub}-all-weeks.pdf"
    print(f"  {fname} -> {full.name}", flush=True)
    compress(src, full)
    weeks = []
    for w, lo, hi, txt in week_ranges(src):
        f = OUT / "pdf" / level / f"level-{level}-{sub}-week-{w:02d}.pdf"
        compress(src, f, lo, hi)
        weeks.append({"week": w, "focus": focus_of(txt), "pages": hi - lo + 1, "file": rel(f)})
    t = OUT / "thumbs" / level / f"level-{level}-{sub}.jpg"
    thumb(full, t)
    return {"subject": subject, "pages": page_count(src), "file": rel(full), "size": full.stat().st_size,
            "thumb": rel(t), "weeks": weeks}


def parse_guide(txt):
    """'Week 01: Fruit market | Math: add | ...' -> {1: 'Fruit market | Math: add | ...'} plus the intro lines."""
    weeks, intro = {}, []
    for line in txt.splitlines():
        m = re.match(r"Week\s+(\d+):\s*(.+)", line.strip())
        if m:
            weeks[int(m.group(1))] = m.group(2).strip()
        elif line.strip() and not weeks:
            intro.append(line.strip())
    return weeks, intro[1:]  # first intro line is the title


def import_package(level, folder, guide):
    base = SRC / folder
    topics, intro = parse_guide((base / guide).read_text())
    weeks = []
    for w in range(1, 27):
        srcs = sorted((base / f"week_{w:02d}").glob("*.pdf"))
        assert len(srcs) == 1, f"{folder} week {w}: {srcs}"
        f = OUT / "pdf" / level / f"level-{level}-week-{w:02d}.pdf"
        print(f"  {srcs[0].name} -> {f.name}", flush=True)
        compress(srcs[0], f)
        parts = [p.strip() for p in topics[w].split("|")]
        weeks.append({"week": w, "scene": parts[0], "topics": parts[1:], "pages": page_count(srcs[0]),
                      "file": rel(f), "size": f.stat().st_size})
    t = OUT / "thumbs" / level / f"level-{level}.jpg"
    thumb(OUT / "pdf" / level / f"level-{level}-week-01.pdf", t)
    return {"intro": intro, "thumb": rel(t), "weeks": weeks}


def rel(p):
    return str(p.relative_to(OUT))


def main():
    manifest = {"levels": {}, "extras": []}
    for level, subjects in BOOKS.items():
        print(f"Level {level.upper()}", flush=True)
        manifest["levels"][level] = {"books": [import_book(level, s, f) for s, f in subjects.items()]}
    for level, (folder, guide) in PACKAGES.items():
        print(f"Level {level.upper()}", flush=True)
        manifest["levels"][level] = import_package(level, folder, guide)
    for eid, title, fname, blurb in EXTRAS:
        f = OUT / "pdf" / "extras" / f"{eid}.pdf"
        compress(SRC / fname, f)
        t = OUT / "thumbs" / "extras" / f"{eid}.jpg"
        thumb(f, t)
        manifest["extras"].append({"id": eid, "title": title, "blurb": blurb, "pages": page_count(f),
                                   "file": rel(f), "size": f.stat().st_size, "thumb": rel(t)})
    MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"wrote {MANIFEST.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
