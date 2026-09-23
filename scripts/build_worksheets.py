#!/usr/bin/env python3
"""Printable exercise books for early maths.

Generates one print-ready book per concept (addition, subtraction, multiplication…),
each with 50+ problems that grow from illustrated 1+1 up to big numbers like 99+98.
Small problems show soft object pictures to count; bigger ones are numeric. Each book
ends with an answer key, and has a "Print" button plus print-clean CSS.

Outputs:
  docs/school/worksheets/<id>.html     one book per concept
  docs/school/worksheets/index.html    the worksheets library

Usage:  python3 scripts/build_worksheets.py
"""
import html
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "school" / "worksheets"
sys.path.insert(0, str(Path(__file__).resolve().parent))
import school_diagrams as sd  # noqa: E402

esc = html.escape
INK = sd.INK
ICONS = ["gift", "apple", "balloon", "star", "ball"]
OP_SYM = {"add": "+", "sub": "−", "mul": "×"}


def answer(a, b, op):
    return a + b if op == "add" else (a - b if op == "sub" else a * b)


# ---------------------------------------------------------------- problem sets

def gen_addition():
    illus = [(1, 1), (2, 1), (2, 2), (3, 2), (3, 3), (4, 2), (4, 3), (4, 4),
             (5, 1), (5, 2), (5, 3), (5, 4), (5, 5), (2, 4), (3, 4), (1, 5)]
    teens = [(a, b) for a in (6, 7, 8, 9) for b in (3, 4, 5)]
    twod, a, b = [], 10, 10
    for _ in range(22):
        twod.append((a, b)); a += 4; b += 3
        a = min(a, 99); b = min(b, 98)
    twod[-1] = (99, 98)
    return [("Count the pictures and add", illus, True),
            ("Adding up to 20", teens, False),
            ("Bigger numbers", twod, False)]


def gen_subtraction():
    illus = [(2, 1), (3, 1), (3, 2), (4, 1), (4, 2), (4, 3), (5, 1), (5, 2),
             (5, 3), (5, 4), (6, 2), (6, 3), (7, 3), (8, 4), (9, 5), (10, 4)]
    teens = [(12, 5), (14, 6), (15, 7), (16, 8), (18, 9), (13, 4),
             (17, 8), (11, 6), (19, 5), (20, 7), (16, 9), (14, 8)]
    twod, a, b = [], 20, 10
    for _ in range(22):
        twod.append((a, b)); a += 4; b += 3
        a = min(a, 99)
        if b >= a:
            b = a - 1
    twod[-1] = (99, 98)
    return [("Count the pictures and take away", illus, True),
            ("Taking away up to 20", teens, False),
            ("Bigger numbers", twod, False)]


def gen_multiplication():
    illus = [(2, 1), (2, 2), (2, 3), (3, 2), (3, 3), (2, 4), (4, 2), (3, 4),
             (4, 3), (5, 2), (2, 5), (4, 4), (5, 3), (3, 5), (5, 4), (5, 5)]
    tables = [(6, 3), (6, 4), (7, 3), (7, 4), (8, 3), (8, 5), (9, 4), (9, 6), (7, 7),
              (8, 8), (9, 9), (6, 7), (8, 6), (9, 7), (11, 3), (12, 4), (11, 11), (12, 12)]
    twod = [(13, 3), (14, 5), (21, 4), (23, 3), (32, 4), (45, 2), (52, 3), (24, 6),
            (36, 5), (48, 2), (63, 3), (72, 4), (84, 2), (91, 5), (76, 4), (99, 9)]
    return [("Count the groups and multiply", illus, True),
            ("Times tables", tables, False),
            ("Bigger numbers", twod, False)]


CONCEPTS = {
    "addition": {"title": "Addition", "op": "add", "emoji": "➕",
                 "intro": "Add the two groups together and write how many there are altogether. The first problems have pictures to count; later ones use bigger numbers.",
                 "gen": gen_addition},
    "subtraction": {"title": "Subtraction", "op": "sub", "emoji": "➖",
                    "intro": "Start with the first number and take the second away. Cross out the pictures to help, then write how many are left.",
                    "gen": gen_subtraction},
    "multiplication": {"title": "Multiplication", "op": "mul", "emoji": "✖️",
                       "intro": "Multiplication is equal groups. Count the rows and columns of pictures, then write the total. Later problems use bigger numbers.",
                       "gen": gen_multiplication},
}


# ---------------------------------------------------------------- illustrations

def illus_addsub(a, b, op, ic):
    s, cw, y = 14, 32, 26
    parts, x = [], 8
    for _ in range(a):
        parts.append(sd.icon(ic, x + s, y, s)); x += cw
    if op == "add":
        parts.append(f'<text x="{x+6}" y="{y+7}" font-size="20" font-weight="700" fill="{INK}">+</text>'); x += 24
        for _ in range(b):
            parts.append(sd.icon(ic, x + s, y, s)); x += cw
    w, h = x + 8, y + s + 8
    return f'<svg viewBox="0 0 {w} {h}" width="{w}" height="{h}" role="img" aria-label="objects to count" xmlns="http://www.w3.org/2000/svg" style="max-width:100%">{"".join(parts)}</svg>'


def illus_mul(a, b, ic):
    s, cw, pad = 12, 28, 8
    parts = []
    for r in range(a):
        for c in range(b):
            parts.append(sd.icon(ic, pad + s + c * cw, pad + s + r * cw, s))
    w, h = pad * 2 + b * cw - (cw - 2 * s), pad * 2 + a * cw - (cw - 2 * s)
    return f'<svg viewBox="0 0 {w} {h}" width="{w}" height="{h}" role="img" aria-label="{a} rows of {b}" xmlns="http://www.w3.org/2000/svg" style="max-width:100%">{"".join(parts)}</svg>'


def problem_cell(n, a, b, op, illustrate, ic):
    art = ""
    if illustrate:
        art = '<div class="art">' + (illus_mul(a, b, ic) if op == "mul" else illus_addsub(a, b, op, ic)) + "</div>"
    eq = f'{a} {OP_SYM[op]} {b} = <span class="box"></span>'
    cls = "prob pic" if illustrate else "prob"
    return f'<div class="{cls}"><span class="n">{n})</span>{art}<div class="eq">{eq}</div></div>'


# ---------------------------------------------------------------- page render

PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <link rel="icon" href="../../assets/favicon.ico" sizes="any" />
  <link rel="icon" type="image/png" sizes="32x32" href="../../assets/logo-32.png" />
  <title>{title} worksheets — free printable practice | ThavionAI School</title>
  <meta name="description" content="{intro_attr}" />
  <meta property="og:title" content="{title} worksheets — ThavionAI School" />
  <meta property="og:description" content="{intro_attr}" />
  <meta property="og:type" content="article" />
  <link rel="canonical" href="https://thavionai.com/school/worksheets/{id}.html" />
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet" />
  <link rel="stylesheet" href="../../site.css" />
  <style>
    .ws {{ max-width: 820px; margin: 0 auto; padding: 0 22px 60px; }}
    .ws-hero {{ padding: 44px 0 12px; }}
    .ws-hero h1 {{ font-size: clamp(26px, 4.4vw, 38px); font-weight: 800; letter-spacing: -1px; margin: 8px 0 10px; }}
    .ws-hero p {{ color: var(--text2); font-size: 16px; max-width: 640px; }}
    .ws-actions {{ display: flex; flex-wrap: wrap; gap: 10px; margin-top: 16px; }}
    .ws-tip {{ font-size: 13px; color: var(--text3); margin-top: 10px; }}
    .ws-section {{ margin-top: 30px; }}
    .ws-section h2 {{ font-size: 17px; font-weight: 800; color: var(--text); border-bottom: 2px solid var(--border); padding-bottom: 6px; margin-bottom: 14px; }}
    .grid {{ display: grid; gap: 12px; }}
    .grid.illus {{ grid-template-columns: repeat(auto-fill, minmax(240px, 1fr)); }}
    .grid.num {{ grid-template-columns: repeat(auto-fill, minmax(150px, 1fr)); }}
    .prob {{ display: flex; align-items: center; gap: 10px; border: 1px solid var(--border); border-radius: 12px; padding: 12px 14px; background: #fff; break-inside: avoid; }}
    .prob.pic {{ flex-direction: column; align-items: flex-start; gap: 8px; position: relative; }}
    .prob.pic .n {{ position: absolute; top: 10px; right: 12px; }}
    .prob .n {{ font-weight: 700; color: var(--text3); font-size: 13px; min-width: 24px; }}
    .prob .art {{ flex: 0 0 auto; }}
    .prob .art svg {{ display: block; }}
    .prob .eq {{ font-size: 20px; font-weight: 700; color: var(--text); white-space: nowrap; }}
    .box {{ display: inline-block; width: 42px; height: 26px; border: 2px solid var(--text3); border-radius: 6px; vertical-align: middle; }}
    .answers {{ margin-top: 40px; border-top: 2px dashed var(--border); padding-top: 18px; }}
    .answers h2 {{ font-size: 16px; font-weight: 800; }}
    .akey {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(92px, 1fr)); gap: 4px 12px; font-size: 13px; color: var(--text2); }}
    .ws-foot {{ margin-top: 30px; font-size: 12px; color: var(--text3); text-align: center; }}
    @media print {{
      .site-nav, .site-footer, .no-print {{ display: none !important; }}
      body {{ background: #fff; }}
      .ws {{ padding: 0; max-width: none; }}
      .prob {{ break-inside: avoid; }}
      .answers {{ break-before: page; }}
      a[href]:after {{ content: ""; }}
    }}
  </style>
</head>
<body class="theme-light theme-school">

<nav class="site-nav no-print">
  <div class="nav-inner">
    <a href="../../index.html" class="nav-logo"><img src="../../assets/logo.png" alt="" /><span>ThavionAI<small>Learn. Build. Ship.</small></span></a>
    <button class="nav-toggle" aria-label="Menu" aria-expanded="false" aria-controls="navLinks" onclick="toggleNav()">
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="4" y1="7" x2="20" y2="7"/><line x1="4" y1="12" x2="20" y2="12"/><line x1="4" y1="17" x2="20" y2="17"/></svg>
    </button>
    <div class="nav-links" id="navLinks">
      <a href="../../index.html">Home</a>
      <a href="../../engineering.html">Engineering</a>
      <a href="../../school.html">School</a>
      <a href="index.html">All worksheets</a>
    </div>
  </div>
</nav>

<div class="ws">
  <section class="ws-hero">
    <div class="crumbs no-print" style="font-size:13px;color:var(--text3)"><a href="../../index.html" style="color:var(--text2)">Home</a> › <a href="../../school.html" style="color:var(--text2)">School</a> › <a href="index.html" style="color:var(--text2)">Worksheets</a> › {title}</div>
    <h1>{emoji} {title} — practice book</h1>
    <p>{intro}</p>
    <div class="ws-actions no-print">
      <button class="btn btn-primary" onclick="window.print()">\U0001f5a8️ Print this book</button>
      <a class="btn btn-secondary" href="index.html">More worksheets</a>
    </div>
    <p class="ws-tip no-print">Tip: press Print, then choose “Save as PDF” to keep a copy, or print on paper for the kids. {count} problems inside, plus an answer key at the end.</p>
  </section>

{sections}

  <section class="answers">
    <h2>Answer key</h2>
    <p style="font-size:12.5px;color:var(--text3);margin-bottom:10px">For grown-ups to check the work.</p>
    {answers}
  </section>

  <p class="ws-foot">Free printable worksheets from ThavionAI · thavionai.com · print and share freely.</p>
</div>

<footer class="site-footer no-print">
  <div class="max-w">
    <div class="footer-grid">
      <div class="footer-brand">
        <a href="../../index.html" class="nav-logo"><img src="../../assets/logo.png" alt="" /><span>ThavionAI</span></a>
        <p>Free education for everyone. Learn. Build. Ship.</p>
      </div>
      <div class="footer-col"><h4>School</h4>
        <a href="../../school.html">All subjects</a>
        <a href="index.html">Worksheets</a>
      </div>
      <div class="footer-col"><h4>Company</h4>
        <a href="../../index.html#about">About</a>
        <a href="../../feedback.html">Feedback</a>
        <a href="../../privacy.html">Privacy</a>
        <a href="../../terms.html">Terms</a>
      </div>
    </div>
    <div class="footer-bottom"><span>© 2025–2026 ThavionAI.</span><span><a href="../../privacy.html">Privacy</a><a href="../../terms.html">Terms</a></span></div>
  </div>
</footer>

<script>
  document.documentElement.classList.add('js');
  function toggleNav() {{
    var n = document.getElementById('navLinks'); var open = n.classList.toggle('open');
    document.querySelector('.nav-toggle').setAttribute('aria-expanded', open ? 'true' : 'false');
  }}
  document.querySelectorAll('#navLinks a').forEach(function (a) {{ a.addEventListener('click', function () {{ document.getElementById('navLinks').classList.remove('open'); }}); }});
</script>
</body>
</html>
"""


def build_book(cid, cfg):
    op = cfg["op"]
    sections = cfg["gen"]()
    n = 0
    sec_html, ans_html = [], []
    for title, pairs, illustrate in sections:
        cells = []
        akey = []
        for a, b in pairs:
            n += 1
            ic = ICONS[n % len(ICONS)]
            cells.append(problem_cell(n, a, b, op, illustrate, ic))
            akey.append(f'<span>{n}) {answer(a, b, op)}</span>')
        grid_cls = "illus" if illustrate else "num"
        sec_html.append(f'<section class="ws-section"><h2>{esc(title)}</h2><div class="grid {grid_cls}">{"".join(cells)}</div></section>')
        ans_html.append(f'<div style="margin-bottom:10px"><b style="font-size:13px">{esc(title)}</b><div class="akey">{"".join(akey)}</div></div>')
    page = PAGE.format(
        id=cid, title=cfg["title"], emoji=cfg["emoji"], intro=esc(cfg["intro"]),
        intro_attr=esc(cfg["intro"]), count=n,
        sections="\n".join(sec_html), answers="".join(ans_html),
    )
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / f"{cid}.html").write_text(page)
    return n


INDEX = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <link rel="icon" href="../../assets/favicon.ico" sizes="any" />
  <link rel="icon" type="image/png" sizes="32x32" href="../../assets/logo-32.png" />
  <title>Free printable maths worksheets | ThavionAI School</title>
  <meta name="description" content="Free printable maths practice books — addition, subtraction and multiplication — each with 50+ illustrated problems from 1+1 to big numbers. Print at home, no sign-up." />
  <meta property="og:title" content="Free printable maths worksheets — ThavionAI School" />
  <meta property="og:description" content="Illustrated practice books for addition, subtraction and multiplication. Print and share freely." />
  <meta property="og:type" content="website" />
  <link rel="canonical" href="https://thavionai.com/school/worksheets/index.html" />
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet" />
  <link rel="stylesheet" href="../../site.css" />
  <style>
    .ws {{ max-width: 820px; margin: 0 auto; padding: 0 22px 70px; }}
    .ws-hero {{ padding: 52px 0 14px; }}
    .ws-hero h1 {{ font-size: clamp(28px, 4.6vw, 42px); font-weight: 800; letter-spacing: -1.1px; margin: 10px 0 12px; }}
    .ws-hero p {{ color: var(--text2); font-size: 17px; max-width: 640px; }}
    .book-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(240px, 1fr)); gap: 16px; margin-top: 28px; }}
    .book {{ display: flex; flex-direction: column; background: var(--surface); border: 1px solid var(--border); border-radius: 16px; padding: 22px; box-shadow: var(--shadow); }}
    .book .em {{ font-size: 32px; }}
    .book h3 {{ font-size: 19px; font-weight: 800; margin: 8px 0 4px; }}
    .book p {{ font-size: 13.5px; color: var(--text2); flex: 1; line-height: 1.6; }}
    .book .cnt {{ font-size: 12px; color: var(--text3); margin: 8px 0 12px; }}
    .book a {{ display: block; text-align: center; font-weight: 600; border-radius: 10px; padding: 10px; background: var(--accent); color: #fff; }}
  </style>
</head>
<body class="theme-light theme-school">

<nav class="site-nav">
  <div class="nav-inner">
    <a href="../../index.html" class="nav-logo"><img src="../../assets/logo.png" alt="" /><span>ThavionAI<small>Learn. Build. Ship.</small></span></a>
    <button class="nav-toggle" aria-label="Menu" aria-expanded="false" aria-controls="navLinks" onclick="toggleNav()">
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="4" y1="7" x2="20" y2="7"/><line x1="4" y1="12" x2="20" y2="12"/><line x1="4" y1="17" x2="20" y2="17"/></svg>
    </button>
    <div class="nav-links" id="navLinks">
      <a href="../../index.html">Home</a>
      <a href="../../engineering.html">Engineering</a>
      <a href="../../school.html">School</a>
      <a href="../../exams.html">Exams</a>
    </div>
  </div>
</nav>

<div class="ws">
  <section class="ws-hero">
    <div class="crumbs" style="font-size:13px;color:var(--text3)"><a href="../../index.html" style="color:var(--text2)">Home</a> › <a href="../../school.html" style="color:var(--text2)">School</a> › Worksheets</div>
    <span class="chip"><span class="dot"></span> Free · Printable · No sign-up</span>
    <h1>Printable maths worksheets</h1>
    <p>Practice books you can print at home. Each has 50+ problems that grow from picture-and-count basics up to big numbers, with an answer key for grown-ups. Open a book and press Print.</p>
  </section>

  <div class="book-grid">
{books}
  </div>
</div>

<footer class="site-footer">
  <div class="max-w">
    <div class="footer-grid">
      <div class="footer-brand">
        <a href="../../index.html" class="nav-logo"><img src="../../assets/logo.png" alt="" /><span>ThavionAI</span></a>
        <p>Free education for everyone. Learn. Build. Ship.</p>
      </div>
      <div class="footer-col"><h4>School</h4>
        <a href="../../school.html">All subjects</a>
        <a href="index.html">Worksheets</a>
      </div>
      <div class="footer-col"><h4>Company</h4>
        <a href="../../index.html#about">About</a>
        <a href="../../feedback.html">Feedback</a>
        <a href="../../privacy.html">Privacy</a>
        <a href="../../terms.html">Terms</a>
      </div>
    </div>
    <div class="footer-bottom"><span>© 2025–2026 ThavionAI.</span><span><a href="../../privacy.html">Privacy</a><a href="../../terms.html">Terms</a></span></div>
  </div>
</footer>

<script>
  document.documentElement.classList.add('js');
  function toggleNav() {{
    var n = document.getElementById('navLinks'); var open = n.classList.toggle('open');
    document.querySelector('.nav-toggle').setAttribute('aria-expanded', open ? 'true' : 'false');
  }}
  document.querySelectorAll('#navLinks a').forEach(function (a) {{ a.addEventListener('click', function () {{ document.getElementById('navLinks').classList.remove('open'); }}); }});
</script>
</body>
</html>
"""


def build_index(counts):
    cards = []
    for cid, cfg in CONCEPTS.items():
        cards.append(
            f'    <div class="book"><span class="em">{cfg["emoji"]}</span>'
            f'<h3>{esc(cfg["title"])}</h3><p>{esc(cfg["intro"])}</p>'
            f'<div class="cnt">{counts[cid]} problems · illustrated · answer key</div>'
            f'<a href="{cid}.html">Open &amp; print →</a></div>'
        )
    (OUT / "index.html").write_text(INDEX.format(books="\n".join(cards)))


def main():
    counts = {}
    for cid, cfg in CONCEPTS.items():
        counts[cid] = build_book(cid, cfg)
    build_index(counts)
    total = sum(counts.values())
    print(f"built {len(CONCEPTS)} worksheet book(s) -> docs/school/worksheets/  ({total} problems: " +
          ", ".join(f"{k} {v}" for k, v in counts.items()) + ")")


if __name__ == "__main__":
    main()
