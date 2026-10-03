"""Printable workbook library for the School world.

Renders docs/school/library/index.html from site-src/school/library.json (written by import_library.py).
The PDFs and thumbnails themselves live in docs/school/library/{pdf,thumbs}/ and are committed.

  python3 scripts/build_library.py
"""
import json
from html import escape as esc
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "school" / "library"
MANIFEST = ROOT / "site-src" / "school" / "library.json"

LEVELS = {
    "a": ("Level A", "Kindergarten · starting out", "🌱",
          "Counting to 20, letters A to Z, and first science: living things, senses, weather and seasons. "
          "Six sheets a week per subject, big pictures, very little reading."),
    "b": ("Level B", "Kindergarten", "🌼",
          "Numbers to 50, adding and taking away, CVC words and word families, and life cycles, materials and "
          "magnets. Each week opens with a short lesson page and ends with the solutions."),
    "c": ("Level C", "Kindergarten to Grade 1", "🍎",
          "One illustrated story scene a week — a fruit market, a pond rescue, a camping trip — with Math, English "
          "and Science sheets built around it."),
    "d": ("Level D", "Grade 1", "🕰️",
          "Telling time from hours and half hours to exact minutes, counting by 5s and 10s, pattern logic, "
          "reading and science, all in one weekly booklet."),
    "e": ("Level E", "Grade 1 to 2", "🔭",
          "Elapsed time across the hour, skip counting and growing patterns, plus science that asks for "
          "predictions, evidence and fair tests."),
}
SUBJECT_EMOJI = {"Math": "🔢", "English": "🔤", "Science": "🔬"}

CSS = """
.lib{max-width:1080px;margin:0 auto;padding:28px 20px 64px}
.lib-hero h1{font-size:clamp(28px,4vw,40px);margin:8px 0 10px}
.lib-hero p{color:var(--text2);max-width:720px;line-height:1.6}
.how{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:12px;margin:22px 0 8px}
.how div{background:var(--bg2);border:1px solid var(--border);border-radius:14px;padding:14px 16px;font-size:14px;color:var(--text2);line-height:1.5}
.how b{display:block;color:var(--text);margin-bottom:4px}
.jump{display:flex;flex-wrap:wrap;gap:8px;margin:18px 0 6px}
.jump a{padding:7px 14px;border-radius:999px;border:1px solid var(--border);background:var(--bg2);font-size:14px;color:var(--text);text-decoration:none}
.level{margin-top:44px;scroll-margin-top:80px}
.level-head{display:flex;gap:18px;align-items:flex-start;flex-wrap:wrap}
.level-head h2{margin:0 0 4px;font-size:26px}
.level-head .grade{font-size:13px;font-weight:600;color:var(--accent,#16a34a);text-transform:uppercase;letter-spacing:.04em}
.level-head p{color:var(--text2);margin:6px 0 0;max-width:640px;line-height:1.55}
.books{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:16px;margin-top:18px}
.book{border:1px solid var(--border);border-radius:16px;background:var(--bg);overflow:hidden;display:flex;flex-direction:column}
.book img{width:100%;height:auto;aspect-ratio:17/22;object-fit:cover;object-position:top;border-bottom:1px solid var(--border);background:#fff}
.book .bb{padding:14px 16px 16px;display:flex;flex-direction:column;gap:10px;flex:1}
.book h3{margin:0;font-size:18px}
.book .meta{font-size:13px;color:var(--text3)}
.btn-sm{display:inline-block;padding:8px 14px;border-radius:10px;font-size:14px;font-weight:600;text-decoration:none;border:1px solid var(--border);color:var(--text);background:var(--bg2)}
.btn-sm.primary{background:var(--accent,#16a34a);border-color:transparent;color:#fff}
details.weeks{border-top:1px solid var(--border);padding-top:10px}
details.weeks summary{cursor:pointer;font-size:14px;font-weight:600}
.wk{list-style:none;margin:10px 0 0;padding:0;display:grid;gap:4px}
.wk li{display:flex;justify-content:space-between;gap:10px;font-size:14px;padding:6px 8px;border-radius:8px}
.wk li:nth-child(odd){background:var(--bg2)}
.wk .n{color:var(--text3);min-width:62px}
.wk .f{flex:1;color:var(--text)}
.wk a{white-space:nowrap;font-weight:600}
.weekgrid{display:grid;grid-template-columns:repeat(auto-fill,minmax(240px,1fr));gap:10px;margin-top:18px}
.wcard{border:1px solid var(--border);border-radius:14px;padding:12px 14px;background:var(--bg);display:flex;flex-direction:column;gap:6px}
.wcard .top{display:flex;justify-content:space-between;align-items:baseline;gap:8px}
.wcard .n{font-size:12px;font-weight:700;color:var(--text3);text-transform:uppercase;letter-spacing:.05em}
.wcard h4{margin:0;font-size:16px}
.wcard ul{margin:0;padding-left:18px;font-size:13px;color:var(--text2);line-height:1.5}
.wcard a{font-size:14px;font-weight:600;margin-top:auto}
.preview{display:flex;gap:16px;align-items:center;flex-wrap:wrap;margin-top:14px}
.preview img{width:150px;height:auto;border:1px solid var(--border);border-radius:10px;background:#fff}
.note{font-size:13px;color:var(--text3);margin-top:40px;line-height:1.6}
"""

NAV = """<nav class="site-nav no-print"><div class="nav-inner">
  <a href="../../index.html" class="nav-logo"><img src="../../assets/logo.png" alt="" /><span>ThavionAI<small>Learn. Build. Ship.</small></span></a>
  <button class="nav-toggle" aria-label="Menu" aria-expanded="false" aria-controls="navLinks" onclick="toggleNav()"><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="4" y1="7" x2="20" y2="7"/><line x1="4" y1="12" x2="20" y2="12"/><line x1="4" y1="17" x2="20" y2="17"/></svg></button>
  <div class="nav-links" id="navLinks"><a href="../../index.html">Home</a><a href="../../school.html">School</a><a href="index.html">Workbooks</a><a href="../program/index.html">Practice program</a><a href="../worksheets/index.html">Worksheets</a></div>
</div></nav>"""

FOOTER = """<footer class="site-footer no-print"><div class="max-w"><div class="footer-grid">
  <div class="footer-brand"><a href="../../index.html" class="nav-logo"><img src="../../assets/logo.png" alt="" /><span>ThavionAI</span></a><p>Free education for everyone.</p></div>
  <div class="footer-col"><h4>School</h4><a href="../../school.html">All subjects</a><a href="index.html">Printable workbooks</a><a href="../program/index.html">Practice program</a><a href="../stories/index.html">Story Adventures</a></div>
  <div class="footer-col"><h4>Company</h4><a href="../../index.html#about">About</a><a href="../../feedback.html">Feedback</a><a href="../../privacy.html">Privacy</a><a href="../../terms.html">Terms</a></div>
</div><div class="footer-bottom"><span>© 2025–2026 ThavionAI.</span><span><a href="../../privacy.html">Privacy</a><a href="../../terms.html">Terms</a></span></div></div></footer>"""

SCRIPT = """<script>document.documentElement.classList.add('js');function toggleNav(){var n=document.getElementById('navLinks');var o=n.classList.toggle('open');document.querySelector('.nav-toggle').setAttribute('aria-expanded',o?'true':'false');}document.querySelectorAll('#navLinks a').forEach(function(a){a.addEventListener('click',function(){document.getElementById('navLinks').classList.remove('open');});});</script>"""


def mb(n):
    return f"{n / 1e6:.1f} MB" if n >= 1e5 else f"{max(1, round(n / 1e3))} KB"


def size_of(rel):
    return (OUT / rel).stat().st_size


def book_card(level, b):
    weeks = "".join(
        f'<li><span class="n">Week {w["week"]}</span><span class="f">{esc(w["focus"])}</span>'
        f'<a href="{w["file"]}" target="_blank" rel="noopener">PDF · {w["pages"]} pp</a></li>'
        for w in b["weeks"])
    return f"""<article class="book">
  <img src="{b["thumb"]}" alt="First page of the {LEVELS[level][0]} {esc(b["subject"])} workbook" width="306" height="396" loading="lazy" />
  <div class="bb">
    <h3>{SUBJECT_EMOJI.get(b["subject"], "")} {esc(b["subject"])}</h3>
    <div class="meta">26 weeks · {b["pages"]} pages · {mb(b["size"])}</div>
    <div><a class="btn-sm primary" href="{b["file"]}" target="_blank" rel="noopener">Download the whole book</a></div>
    <details class="weeks"><summary>Print one week at a time</summary><ul class="wk">{weeks}</ul></details>
  </div>
</article>"""


def week_card(w):
    topics = "".join(f"<li>{esc(t)}</li>" for t in w["topics"])
    return f"""<div class="wcard"><div class="top"><span class="n">Week {w["week"]}</span><span class="n">{w["pages"]} pp</span></div>
  <h4>{esc(w["scene"])}</h4><ul>{topics}</ul>
  <a href="{w["file"]}" target="_blank" rel="noopener">Open week {w["week"]} PDF · {mb(w["size"])}</a></div>"""


def level_section(level, data):
    name, grade, emoji, blurb = LEVELS[level]
    answers = "" if level == "a" else " with answers"
    if "books" in data:
        inner = f'<div class="books">{"".join(book_card(level, b) for b in data["books"])}</div>'
        pages = sum(b["pages"] for b in data["books"])
    else:
        intro = " ".join(esc(x) for x in data["intro"])
        inner = (f'<div class="preview"><img src="{data["thumb"]}" alt="First page of {name} week 1" width="306" '
                 f'height="396" loading="lazy" /><p style="color:var(--text2);max-width:560px;line-height:1.55;margin:0">'
                 f'{intro}</p></div><div class="weekgrid">{"".join(week_card(w) for w in data["weeks"])}</div>')
        pages = sum(w["pages"] for w in data["weeks"])
    return f"""<div class="level" id="level-{level}">
  <div class="level-head"><div style="font-size:40px;line-height:1">{emoji}</div><div>
    <div class="grade">{esc(grade)}</div><h2>{name}</h2><p>{esc(blurb)}</p>
    <div class="meta" style="font-size:13px;color:var(--text3);margin-top:6px">26 weeks · Math, English and Science · {pages} printable pages{answers}</div>
  </div></div>
  {inner}
</div>"""


def extras_section(extras):
    if not extras:
        return ""
    cards = "".join(f"""<article class="book">
  <img src="{e["thumb"]}" alt="First page of {esc(e["title"])}" width="306" height="396" loading="lazy" />
  <div class="bb"><h3>🎨 {esc(e["title"])}</h3><div class="meta">{e["pages"]} pages · {mb(e["size"])}</div>
  <p style="margin:0;color:var(--text2);font-size:14px;line-height:1.5">{esc(e["blurb"])}</p>
  <div><a class="btn-sm primary" href="{e["file"]}" target="_blank" rel="noopener">Download</a></div></div>
</article>""" for e in extras)
    return f"""<div class="level" id="extras"><div class="level-head"><div><div class="grade">Any age</div>
  <h2>Colouring and quiet time</h2><p>For the end of a session, or a rainy afternoon.</p></div></div>
  <div class="books">{cards}</div></div>"""


def main():
    m = json.loads(MANIFEST.read_text())
    for level, data in m["levels"].items():  # every linked file must exist
        files = [b["file"] for b in data.get("books", [])] + [w["file"] for b in data.get("books", []) for w in b["weeks"]]
        files += [w["file"] for w in data.get("weeks", [])] + [data.get("thumb")] * ("thumb" in data)
        files += [b["thumb"] for b in data.get("books", [])]
        missing = [f for f in files if not (OUT / f).exists()]
        assert not missing, f"level {level}: missing {missing[:3]}"
    n_pdf = sum(1 for _ in (OUT / "pdf").rglob("*.pdf"))
    n_pages = sum(b["pages"] for d in m["levels"].values() for b in d.get("books", [])) + \
        sum(w["pages"] for d in m["levels"].values() for w in d.get("weeks", []))
    jump = "".join(f'<a href="#level-{k}">{LEVELS[k][2]} {LEVELS[k][0]}</a>' for k in m["levels"]) + \
        ('<a href="#extras">🎨 Colouring</a>' if m["extras"] else "")
    body = f"""<main class="lib">
  <div class="lib-hero">
    <div class="crumbs no-print" style="font-size:13px;color:var(--text3)"><a href="../../index.html" style="color:var(--text2)">Home</a> › <a href="../../school.html" style="color:var(--text2)">School</a> › Printable workbooks</div>
    <h1>📚 Printable workbooks, Levels A to E</h1>
    <p>Five 26-week levels of Math, English and Science worksheets — {n_pages:,} pages, with answer pages for every week from Level B up.
      Download a whole book, or print just this week. Free, no sign-up, nothing to install.</p>
    <div class="how">
      <div><b>Pick a level</b>Start where the work feels easy. Confidence first, speed later.</div>
      <div><b>One week at a time</b>About a sheet per subject a day, six days a week. From Level B, the answers follow each week.</div>
      <div><b>Print at home</b>A4 or US Letter, colour or black and white. Choose "fit to page" if margins get cut.</div>
    </div>
    <div class="jump">{jump}</div>
  </div>
  {"".join(level_section(k, v) for k, v in m["levels"].items())}
  {extras_section(m["extras"])}
  <p class="note">{n_pdf} PDF files. The workbooks are free to print for your family or classroom. Spotted a mistake on a
    sheet? Tell us through the <a href="../../feedback.html">feedback form</a> with the level, week and page number.</p>
</main>"""
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <link rel="icon" href="../../assets/favicon.ico" sizes="any" />
  <link rel="icon" type="image/png" sizes="32x32" href="../../assets/logo-32.png" />
  <title>Printable workbooks, Levels A–E | ThavionAI School</title>
  <meta name="description" content="Free printable Math, English and Science workbooks for kindergarten to grade 2: five 26-week levels, {n_pages:,} pages. Download a whole book or one week at a time." />
  <link rel="preconnect" href="https://fonts.googleapis.com" /><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet" />
  <link rel="stylesheet" href="../../site.css" />
  <style>{CSS}</style>
</head>
<body class="theme-light theme-school">
{NAV}
{body}
{FOOTER}
{SCRIPT}
</body>
</html>"""
    (OUT / "index.html").write_text(html)
    print(f"built docs/school/library/index.html ({n_pdf} PDFs, {n_pages} pages)")


if __name__ == "__main__":
    main()
