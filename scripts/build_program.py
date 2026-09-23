#!/usr/bin/env python3
"""The Home Practice Program — a free, Kumon/BestBrains-style structured workbook.

Levels ramp slowly (Basic -> Medium -> Advanced -> Pro). Each level has 26 weeks
(A-Z); each week has 7 day-worksheets (Days 1-6 new practice, Day 7 revision).
Problems are intuitive and story-based ("Mia and Leo meet at school...") with soft
pictures for small numbers, generated deterministically so builds are reproducible.

Outputs (docs/school/program/):
  index.html                 program overview + the four levels
  basic.html                 the Basic level: 26 weeks, each linking to 7 days
  basic-a-1.html ...         182 day worksheets (print-ready)

Usage:  python3 scripts/build_program.py
"""
import html
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "school" / "program"
sys.path.insert(0, str(Path(__file__).resolve().parent))
import school_diagrams as sd  # noqa: E402

esc = html.escape
INK = sd.INK

NAMES = ["Sam", "Mia", "Aria", "Leo", "Noah", "Zoe", "Ravi", "Ana", "Kai", "Lily",
         "Omar", "Ella", "Tara", "Finn", "Maya", "Jack"]
ITEMS = [("apple", "apples", "apple"), ("cake", "cakes", "cake"),
         ("balloon", "balloons", "balloon"), ("sticker", "stickers", "star"),
         ("flower", "flowers", "flower"), ("present", "presents", "gift"),
         ("ball", "balls", "ball")]
ICONS = ["apple", "balloon", "star", "cake", "flower", "ball", "gift"]

LETTERS = [chr(ord("A") + i) for i in range(26)]

# Basic level: 26 weeks (letter, title, kind, hi). Ramps counting -> +/- within 20.
BASIC = [
    ("Counting to 5", "count", 5), ("Counting to 10", "count", 10),
    ("Writing numbers to 10", "trace", 10), ("More, fewer or equal", "compare", 10),
    ("Number order to 10", "order", 10), ("Adding within 5", "add", 5),
    ("Adding within 6", "add", 6), ("Adding within 8", "add", 8),
    ("Adding within 10", "add", 10), ("Addition stories to 10", "addstory", 10),
    ("Subtracting within 5", "sub", 5), ("Subtracting within 6", "sub", 6),
    ("Subtracting within 8", "sub", 8), ("Subtracting within 10", "sub", 10),
    ("Subtraction stories to 10", "substory", 10), ("Add and subtract to 10", "mixed", 10),
    ("Counting to 20", "count", 20), ("Writing numbers to 20", "trace", 20),
    ("Adding within 15", "add", 15), ("Adding within 20", "add", 20),
    ("Subtracting within 15", "sub", 15), ("Subtracting within 20", "sub", 20),
    ("Add and subtract to 15", "mixed", 15), ("Number order to 20", "order", 20),
    ("Add and subtract to 20", "mixed", 20), ("Big revision to 20", "mixed", 20),
]
LEVELS = [("basic", "Basic", "For beginners — counting up to adding and subtracting within 20.", BASIC)]


# ---------------------------------------------------------------- problem makers

def gab(rnd, op, hi):
    if op == "add":
        a = rnd.randint(1, hi - 1)
        b = rnd.randint(1, hi - a)
    else:
        a = rnd.randint(2, hi)
        b = rnd.randint(1, a - 1)
    return a, b


def p_count(rnd, hi):
    return {"t": "count", "n": rnd.randint(1, hi), "ic": rnd.choice(ICONS)}


def p_trace(rnd, hi):
    return {"t": "trace", "num": rnd.randint(0, hi)}


def p_compare(rnd, hi):
    a, b = rnd.randint(1, hi), rnd.randint(1, hi)
    return {"t": "compare", "a": a, "b": b}


def p_order(rnd, hi):
    start = rnd.randint(1, max(1, hi - 4))
    terms = [start + i for i in range(5)]
    blank = rnd.randint(1, 3)
    return {"t": "order", "terms": terms, "blank": blank}


def p_arith(rnd, op, hi, illus=False):
    a, b = gab(rnd, op, hi)
    return {"t": "arith", "a": a, "b": b, "op": op, "illus": illus, "ic": rnd.choice(ICONS)}


def p_small_illus(rnd, op):
    # illustrated warm-up: operands small so pictures stay tidy
    if op == "add":
        a = rnd.randint(1, 4)
        b = rnd.randint(1, 5 - min(a, 4) + 1)
        b = min(b, 5)
    else:
        a = rnd.randint(2, 6)
        b = rnd.randint(1, a - 1)
    return {"t": "arith", "a": a, "b": b, "op": op, "illus": True, "ic": rnd.choice(ICONS)}


def p_story(rnd, op, hi):
    n1, n2 = rnd.sample(NAMES, 2)
    _sing, plur, ic = rnd.choice(ITEMS)
    a, b = gab(rnd, op, hi)
    if op == "add":
        tpl = rnd.choice([
            "{n1} has {a} {plur}. {n2} gives {n1} {b} more. How many {plur} does {n1} have now?",
            "{a} {plur} are on the plate. {n1} puts {b} more {plur} on it. How many {plur} are there now?",
            "{n1} and {n2} meet at school. {n1} brings {a} {plur} and {n2} brings {b} {plur}. How many {plur} do they have altogether?",
            "{n1} sees {a} {plur} in the garden, then {b} more grow. How many {plur} are there in all?",
        ])
        ans = a + b
    else:
        tpl = rnd.choice([
            "{n1} has {a} {plur}. {n1} gives {b} {plur} to {n2}. How many {plur} are left?",
            "There are {a} {plur} in the basket. {n1} takes {b} out. How many {plur} are left?",
            "{n1} had {a} {plur} and ate {b} of them. How many {plur} are left?",
            "{n1} had {a} {plur}, but {b} floated away. How many {plur} does {n1} have now?",
        ])
        ans = a - b
    text = tpl.format(n1=n1, n2=n2, a=a, b=b, plur=plur)
    return {"t": "story", "text": text, "a": a, "b": b, "op": op,
            "illus": (a <= 6 and b <= 6), "ic": ic, "ans": ans}


def practice_block(rnd, kind, hi, count):
    """Return (grid_class, [problem dicts]) for a block of the given skill."""
    if kind == "count":
        return "illus", [p_count(rnd, hi) for _ in range(count)]
    if kind == "trace":
        return "trace", [p_trace(rnd, hi) for _ in range(count)]
    if kind == "compare":
        return "num", [p_compare(rnd, hi) for _ in range(count)]
    if kind == "order":
        return "seq", [p_order(rnd, hi) for _ in range(count)]
    if kind in ("add", "addstory"):
        return "num", [p_arith(rnd, "add", hi) for _ in range(count)]
    if kind in ("sub", "substory"):
        return "num", [p_arith(rnd, "sub", hi) for _ in range(count)]
    # mixed
    return "num", [p_arith(rnd, rnd.choice(["add", "sub"]), hi) for _ in range(count)]


def story_op(kind):
    if kind in ("add", "addstory"):
        return "add"
    if kind in ("sub", "substory"):
        return "sub"
    return None  # mixed picks per-problem


def build_day(level, wk_ix, day):
    """Return (subtitle, [ (section_title, grid_class, [problem dicts]) ])."""
    _lid, _lname, _ldesc, weeks = level
    title, kind, hi = weeks[wk_ix]
    seed = 100000 + wk_ix * 1000 + day * 37
    rnd = random.Random(seed)
    secs = []

    if day == 7:  # revision
        sub = "Revision — this week and earlier weeks"
        g, probs = practice_block(rnd, kind, hi, 6)
        secs.append((f"This week: {title}", g, probs))
        earlier = sorted({max(0, wk_ix - 1), wk_ix // 2, max(0, wk_ix - 3)})
        earlier = [e for e in earlier if e < wk_ix][:2]
        for e in earlier:
            et, ek, eh = weeks[e]
            g2, p2 = practice_block(rnd, ek, eh, 5)
            secs.append((f"Revision: {et}", g2, p2))
        if kind in ("add", "sub", "mixed", "addstory", "substory"):
            op = story_op(kind) or "add"
            secs.append(("Story problems", "story", [p_story(rnd, op, hi) for _ in range(2)]))
        return sub, secs

    sub = title
    if kind in ("count", "trace", "compare", "order"):
        g, probs = practice_block(rnd, kind, hi, 12 if kind != "order" else 10)
        head = {"count": "Count the pictures and write the number",
                "trace": "Trace the numbers, then write your own",
                "compare": "Write &gt;, &lt; or = in the box",
                "order": "Fill in the missing number"}[kind]
        secs.append((head, g, probs))
        return sub, secs

    # arithmetic weeks
    if kind in ("addstory", "substory"):
        op = "add" if kind == "addstory" else "sub"
        secs.append(("Warm up — count the pictures", "illus", [p_small_illus(rnd, op) for _ in range(3)]))
        secs.append(("Practice", "num", [p_arith(rnd, op, hi) for _ in range(8)]))
        secs.append(("Story problems", "story", [p_story(rnd, op, hi) for _ in range(5)]))
        return sub, secs
    if kind == "mixed":
        secs.append(("Practice — add and subtract", "num",
                     [p_arith(rnd, rnd.choice(["add", "sub"]), hi) for _ in range(14)]))
        secs.append(("Story problems", "story",
                     [p_story(rnd, rnd.choice(["add", "sub"]), hi) for _ in range(3)]))
        return sub, secs
    # plain add / sub
    op = "add" if kind == "add" else "sub"
    secs.append(("Warm up — count the pictures", "illus", [p_small_illus(rnd, op) for _ in range(4)]))
    secs.append(("Practice", "num", [p_arith(rnd, op, hi) for _ in range(12)]))
    secs.append(("Story problems", "story", [p_story(rnd, op, hi) for _ in range(3)]))
    return sub, secs


# ---------------------------------------------------------------- rendering

def illus_group(n, ic, per_row=10):
    s, cw, pad = 13, 26, 6
    parts = []
    for i in range(n):
        r, c = divmod(i, per_row)
        parts.append(sd.icon(ic, pad + s + c * cw, pad + s + r * cw, s))
    cols, rows = min(n, per_row), (n + per_row - 1) // per_row
    w = pad * 2 + cols * cw - (cw - 2 * s)
    h = pad * 2 + rows * cw - (cw - 2 * s)
    return f'<svg viewBox="0 0 {w} {h}" width="{w}" height="{h}" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="{n} things" style="max-width:100%">{"".join(parts)}</svg>'


def illus_two(a, b, op, ic):
    s, cw, y = 13, 30, 24
    parts, x = [], 6
    for _ in range(a):
        parts.append(sd.icon(ic, x + s, y, s)); x += cw
    if op == "add":
        parts.append(f'<text x="{x+5}" y="{y+6}" font-size="18" font-weight="700" fill="{INK}">+</text>'); x += 22
        for _ in range(b):
            parts.append(sd.icon(ic, x + s, y, s)); x += cw
    w, h = x + 6, y + s + 8
    return f'<svg viewBox="0 0 {w} {h}" width="{w}" height="{h}" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="pictures" style="max-width:100%">{"".join(parts)}</svg>'


def trace_strip(num):
    s = str(num)
    dw = 28 * len(s) + 8
    parts, x, y = [], 6, 42
    blue = sd.COLORS["blue"][1]
    for _ in range(4):
        parts.append(f'<text x="{x + dw/2:.0f}" y="{y}" text-anchor="middle" font-size="40" font-weight="800" fill="#eef2f7" stroke="{blue}" stroke-width="1.2" stroke-dasharray="3 3">{s}</text>')
        x += dw + 6
    for _ in range(3):
        parts.append(f'<rect x="{x}" y="8" width="{dw-4}" height="42" rx="6" fill="none" stroke="#d5dde6" stroke-width="1.4" stroke-dasharray="4 4"/>')
        x += dw + 6
    w = x + 6
    return f'<svg viewBox="0 0 {w} 60" width="{w}" height="60" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="trace {num}" style="max-width:100%">{"".join(parts)}</svg>'


OP_SYM = {"add": "+", "sub": "−"}


def render_problem(idx, p):
    t = p["t"]
    if t == "count":
        art = '<div class="art">' + illus_group(p["n"], p["ic"]) + "</div>"
        return f'<div class="prob pic"><span class="n">{idx})</span>{art}<div class="eq">How many? <span class="abox"></span></div></div>'
    if t == "trace":
        word = ""
        return f'<div class="prob pic tracep"><span class="n">{idx})</span><div class="tracehead"><span class="bignum">{p["num"]}</span>{word}</div><div class="art">{trace_strip(p["num"])}</div></div>'
    if t == "compare":
        return f'<div class="prob"><span class="n">{idx})</span><div class="eq">{p["a"]} <span class="abox sq"></span> {p["b"]}</div></div>'
    if t == "order":
        chips = []
        for i, term in enumerate(p["terms"]):
            chips.append('<span class="seqbox"></span>' if i == p["blank"] else f'<span class="seqn">{term}</span>')
        return f'<div class="prob seqp"><span class="n">{idx})</span><div class="seq">{" ".join(chips)}</div></div>'
    if t == "arith":
        art = ""
        if p["illus"]:
            art = '<div class="art">' + illus_two(p["a"], p["b"], p["op"], p["ic"]) + "</div>"
        eq = f'{p["a"]} {OP_SYM[p["op"]]} {p["b"]} = <span class="abox"></span>'
        cls = "prob pic" if p["illus"] else "prob"
        return f'<div class="{cls}"><span class="n">{idx})</span>{art}<div class="eq">{eq}</div></div>'
    if t == "story":
        art = '<div class="art">' + illus_two(p["a"], p["b"], p["op"], p["ic"]) + "</div>" if p["illus"] else ""
        return f'<div class="prob story"><span class="n">{idx})</span><p class="stx">{esc(p["text"])}</p>{art}<div class="eq">Answer: <span class="abox"></span></div></div>'
    return ""


def answer_of(p):
    t = p["t"]
    if t == "count":
        return p["n"]
    if t == "compare":
        return ">" if p["a"] > p["b"] else ("<" if p["a"] < p["b"] else "=")
    if t == "order":
        return p["terms"][p["blank"]]
    if t == "arith":
        return p["a"] + p["b"] if p["op"] == "add" else p["a"] - p["b"]
    if t == "story":
        return p["ans"]
    return None


PROGRAM_CSS = """
    .ws { max-width: 820px; margin: 0 auto; padding: 0 22px 60px; }
    .ws-hero { padding: 40px 0 10px; }
    .ws-hero .tag { font-size: 12px; font-weight: 700; letter-spacing: 0.1em; text-transform: uppercase; color: var(--accent); }
    .ws-hero h1 { font-size: clamp(24px, 4vw, 34px); font-weight: 800; letter-spacing: -0.8px; margin: 6px 0 8px; }
    .ws-hero p { color: var(--text2); font-size: 15px; }
    .ws-actions { display: flex; flex-wrap: wrap; gap: 10px; margin-top: 14px; align-items: center; }
    .ws-section { margin-top: 26px; }
    .ws-section h2 { font-size: 16px; font-weight: 800; color: var(--text); border-bottom: 2px solid var(--border); padding-bottom: 6px; margin-bottom: 12px; }
    .grid { display: grid; gap: 11px; }
    .grid.illus { grid-template-columns: repeat(auto-fill, minmax(230px, 1fr)); }
    .grid.num { grid-template-columns: repeat(auto-fill, minmax(140px, 1fr)); }
    .grid.trace { grid-template-columns: 1fr; }
    .grid.seq { grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); }
    .grid.story { grid-template-columns: 1fr; }
    .prob { display: flex; align-items: center; gap: 10px; border: 1px solid var(--border); border-radius: 12px; padding: 11px 13px; background: #fff; break-inside: avoid; }
    .prob.pic { flex-direction: column; align-items: flex-start; gap: 7px; position: relative; }
    .prob.pic .n { position: absolute; top: 8px; right: 8px; background: rgba(255,255,255,0.88); padding: 0 4px; border-radius: 5px; }
    .prob.story { flex-direction: column; align-items: flex-start; gap: 8px; }
    .prob .n { font-weight: 700; color: var(--text3); font-size: 13px; min-width: 22px; }
    .prob .art svg { display: block; }
    .prob .eq { font-size: 19px; font-weight: 700; color: var(--text); white-space: nowrap; }
    .prob .stx { font-size: 15px; color: var(--text); line-height: 1.5; margin: 0; padding-right: 26px; }
    .abox { display: inline-block; width: 42px; height: 26px; border: 2px solid var(--text3); border-radius: 6px; vertical-align: middle; }
    .abox.sq { width: 30px; }
    .tracehead .bignum { font-size: 28px; font-weight: 800; color: var(--accent); }
    .seqp { align-items: center; }
    .seq { display: flex; flex-wrap: wrap; align-items: center; gap: 10px; font-size: 19px; font-weight: 700; }
    .seqn { min-width: 24px; text-align: center; }
    .seqbox { display: inline-block; width: 38px; height: 28px; border: 2px solid var(--text3); border-radius: 6px; }
    .answers { margin-top: 34px; border-top: 2px dashed var(--border); padding-top: 16px; }
    .akey { display: grid; grid-template-columns: repeat(auto-fill, minmax(88px, 1fr)); gap: 4px 12px; font-size: 12.5px; color: var(--text2); }
    .ws-nav { display: flex; justify-content: space-between; gap: 10px; margin-top: 28px; }
    .ws-foot { margin-top: 26px; font-size: 12px; color: var(--text3); text-align: center; }
    @media print {
      .site-nav, .site-footer, .no-print { display: none !important; }
      body { background: #fff; }
      .ws { padding: 0; max-width: none; }
      .prob { break-inside: avoid; } .answers { break-before: page; }
    }
"""

NAV = """<nav class="site-nav no-print">
  <div class="nav-inner">
    <a href="../../index.html" class="nav-logo"><img src="../../assets/logo.png" alt="" /><span>ThavionAI<small>Learn. Build. Ship.</small></span></a>
    <button class="nav-toggle" aria-label="Menu" aria-expanded="false" aria-controls="navLinks" onclick="toggleNav()">
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="4" y1="7" x2="20" y2="7"/><line x1="4" y1="12" x2="20" y2="12"/><line x1="4" y1="17" x2="20" y2="17"/></svg>
    </button>
    <div class="nav-links" id="navLinks">
      <a href="../../index.html">Home</a>
      <a href="../../school.html">School</a>
      <a href="index.html">Program</a>
      <a href="../worksheets/index.html">Worksheets</a>
    </div>
  </div>
</nav>"""

FOOTER = """<footer class="site-footer no-print">
  <div class="max-w"><div class="footer-grid">
    <div class="footer-brand"><a href="../../index.html" class="nav-logo"><img src="../../assets/logo.png" alt="" /><span>ThavionAI</span></a><p>Free education for everyone. Learn. Build. Ship.</p></div>
    <div class="footer-col"><h4>School</h4><a href="../../school.html">All subjects</a><a href="index.html">Practice program</a><a href="../worksheets/index.html">Worksheets</a></div>
    <div class="footer-col"><h4>Company</h4><a href="../../index.html#about">About</a><a href="../../feedback.html">Feedback</a><a href="../../privacy.html">Privacy</a><a href="../../terms.html">Terms</a></div>
  </div><div class="footer-bottom"><span>© 2025–2026 ThavionAI.</span><span><a href="../../privacy.html">Privacy</a><a href="../../terms.html">Terms</a></span></div></div>
</footer>"""

SCRIPT = """<script>
  document.documentElement.classList.add('js');
  function toggleNav(){{var n=document.getElementById('navLinks');var o=n.classList.toggle('open');document.querySelector('.nav-toggle').setAttribute('aria-expanded',o?'true':'false');}}
  document.querySelectorAll('#navLinks a').forEach(function(a){{a.addEventListener('click',function(){{document.getElementById('navLinks').classList.remove('open');}});}});
</script>"""

DAY_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <link rel="icon" href="../../assets/favicon.ico" sizes="any" />
  <link rel="icon" type="image/png" sizes="32x32" href="../../assets/logo-32.png" />
  <title>{lname} · Week {letter} · Day {day} — {sub} | ThavionAI</title>
  <meta name="description" content="Free printable practice: {lname} level, Week {letter}, Day {day} — {sub}. Part of ThavionAI's free home-practice program." />
  <link rel="canonical" href="https://thavionai.com/school/program/{lid}-{lletter}-{day}.html" />
  <link rel="preconnect" href="https://fonts.googleapis.com" /><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet" />
  <link rel="stylesheet" href="../../site.css" />
  <style>{css}</style>
</head>
<body class="theme-light theme-school">
{nav}
<div class="ws">
  <section class="ws-hero">
    <div class="crumbs no-print" style="font-size:13px;color:var(--text3)"><a href="../../index.html" style="color:var(--text2)">Home</a> › <a href="../../school.html" style="color:var(--text2)">School</a> › <a href="index.html" style="color:var(--text2)">Program</a> › <a href="{lid}.html" style="color:var(--text2)">{lname}</a> › Week {letter}</div>
    <div class="tag">{lname} · Week {letter} · Day {day} of 7</div>
    <h1>{sub}</h1>
    <p class="no-print">Practice sheet {count} problems. Trace or write the answers in the boxes. Grown-ups: the answer key is at the end.</p>
    <div class="ws-actions no-print">
      <button class="btn btn-primary" onclick="window.print()">\U0001f5a8️ Print this sheet</button>
      <a class="btn btn-secondary" href="{lid}.html">All weeks</a>
    </div>
  </section>
{sections}
  <section class="answers">
    <h2 style="font-size:15px;font-weight:800">Answer key <span style="font-weight:500;color:var(--text3);font-size:12px">(for grown-ups)</span></h2>
    {answers}
  </section>
  <div class="ws-nav no-print">{prev}{next}</div>
  <p class="ws-foot">Free home-practice program from ThavionAI · thavionai.com · print and share freely.</p>
</div>
{footer}
{script}
</body>
</html>"""


def render_day(level, wk_ix, day, prev_href, next_href):
    lid, lname, _ldesc, weeks = level
    letter = LETTERS[wk_ix]
    sub, secs = build_day(level, wk_ix, day)
    idx = 0
    sec_html, akey_parts = [], []
    for title, gcls, probs in secs:
        cells, keys = [], []
        for p in probs:
            idx += 1
            cells.append(render_problem(idx, p))
            av = answer_of(p)
            if av is not None:
                keys.append(f'<span>{idx}) {av}</span>')
        sec_html.append(f'<section class="ws-section"><h2>{title}</h2><div class="grid {gcls}">{"".join(cells)}</div></section>')
        if keys:
            akey_parts.append(f'<div style="margin-bottom:8px"><b style="font-size:12.5px">{esc(title)}</b><div class="akey">{"".join(keys)}</div></div>')
    prev_btn = f'<a class="btn btn-secondary" href="{prev_href}">← Previous</a>' if prev_href else '<span></span>'
    next_btn = f'<a class="btn btn-primary" href="{next_href}">Next →</a>' if next_href else '<span></span>'
    page = DAY_PAGE.format(
        css=PROGRAM_CSS, nav=NAV, footer=FOOTER, script=SCRIPT,
        lid=lid, lname=lname, letter=letter, lletter=letter.lower(), day=day,
        sub=esc(sub), count=idx, sections="\n".join(sec_html),
        answers="".join(akey_parts), prev=prev_btn, next=next_btn,
    )
    (OUT / f"{lid}-{letter.lower()}-{day}.html").write_text(page)


LEVEL_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <link rel="icon" href="../../assets/favicon.ico" sizes="any" />
  <link rel="icon" type="image/png" sizes="32x32" href="../../assets/logo-32.png" />
  <title>{lname} level — free home-practice program | ThavionAI School</title>
  <meta name="description" content="{ldesc} 26 weeks, 7 worksheets each — free printable practice, like Kumon but free." />
  <link rel="canonical" href="https://thavionai.com/school/program/{lid}.html" />
  <link rel="preconnect" href="https://fonts.googleapis.com" /><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet" />
  <link rel="stylesheet" href="../../site.css" />
  <style>
    .lv {{ max-width: 860px; margin: 0 auto; padding: 0 22px 70px; }}
    .lv-hero {{ padding: 50px 0 12px; }}
    .lv-hero h1 {{ font-size: clamp(28px,4.6vw,40px); font-weight: 800; letter-spacing: -1px; margin: 10px 0 10px; }}
    .lv-hero p {{ color: var(--text2); font-size: 16px; max-width: 640px; }}
    .wk {{ background: var(--surface); border: 1px solid var(--border); border-radius: 14px; padding: 16px 18px; margin-top: 12px; display: flex; flex-wrap: wrap; align-items: center; gap: 12px; }}
    .wk .lt {{ width: 40px; height: 40px; flex: 0 0 auto; border-radius: 10px; background: rgba(22,163,74,0.12); color: #15803d; font-weight: 800; font-size: 18px; display: grid; place-items: center; }}
    .wk .info {{ flex: 1 1 200px; }}
    .wk .info b {{ font-size: 15px; }}
    .wk .info span {{ display: block; font-size: 12.5px; color: var(--text3); }}
    .days {{ display: flex; flex-wrap: wrap; gap: 6px; }}
    .days a {{ width: 34px; height: 34px; border-radius: 8px; border: 1px solid var(--border2); display: grid; place-items: center; font-size: 13px; font-weight: 700; color: var(--text2); }}
    .days a:hover {{ border-color: var(--accent); color: var(--accent); }}
    .days a.rev {{ background: rgba(2,132,199,0.08); }}
  </style>
</head>
<body class="theme-light theme-school">
<nav class="site-nav"><div class="nav-inner">
  <a href="../../index.html" class="nav-logo"><img src="../../assets/logo.png" alt="" /><span>ThavionAI<small>Learn. Build. Ship.</small></span></a>
  <button class="nav-toggle" aria-label="Menu" aria-expanded="false" aria-controls="navLinks" onclick="toggleNav()"><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="4" y1="7" x2="20" y2="7"/><line x1="4" y1="12" x2="20" y2="12"/><line x1="4" y1="17" x2="20" y2="17"/></svg></button>
  <div class="nav-links" id="navLinks"><a href="../../index.html">Home</a><a href="../../school.html">School</a><a href="index.html">Program</a><a href="../worksheets/index.html">Worksheets</a></div>
</div></nav>
<div class="lv">
  <section class="lv-hero">
    <div class="crumbs" style="font-size:13px;color:var(--text3)"><a href="../../index.html" style="color:var(--text2)">Home</a> › <a href="../../school.html" style="color:var(--text2)">School</a> › <a href="index.html" style="color:var(--text2)">Program</a> › {lname}</div>
    <span class="chip"><span class="dot"></span> Free · 26 weeks · 7 sheets a week</span>
    <h1>{lname} level</h1>
    <p>{ldesc} Each week has 6 new practice sheets and a revision (Day 7). Do about one sheet a day. Pick a week, open a day, and print.</p>
  </section>
{weeks}
</div>
<footer class="site-footer"><div class="max-w"><div class="footer-grid">
  <div class="footer-brand"><a href="../../index.html" class="nav-logo"><img src="../../assets/logo.png" alt="" /><span>ThavionAI</span></a><p>Free education for everyone.</p></div>
  <div class="footer-col"><h4>School</h4><a href="../../school.html">All subjects</a><a href="index.html">Practice program</a><a href="../worksheets/index.html">Worksheets</a></div>
  <div class="footer-col"><h4>Company</h4><a href="../../index.html#about">About</a><a href="../../feedback.html">Feedback</a><a href="../../privacy.html">Privacy</a><a href="../../terms.html">Terms</a></div>
</div><div class="footer-bottom"><span>© 2025–2026 ThavionAI.</span><span><a href="../../privacy.html">Privacy</a><a href="../../terms.html">Terms</a></span></div></div></footer>
<script>document.documentElement.classList.add('js');function toggleNav(){{var n=document.getElementById('navLinks');var o=n.classList.toggle('open');document.querySelector('.nav-toggle').setAttribute('aria-expanded',o?'true':'false');}}document.querySelectorAll('#navLinks a').forEach(function(a){{a.addEventListener('click',function(){{document.getElementById('navLinks').classList.remove('open');}});}});</script>
</body>
</html>"""


def render_level(level):
    lid, lname, ldesc, weeks = level
    rows = []
    for i, (title, _kind, _hi) in enumerate(weeks):
        letter = LETTERS[i]
        days = "".join(
            f'<a href="{lid}-{letter.lower()}-{d}.html"{" class=rev" if d == 7 else ""} title="Day {d}">{d}</a>'
            for d in range(1, 8))
        rows.append(
            f'<div class="wk"><div class="lt">{letter}</div>'
            f'<div class="info"><b>Week {letter}: {esc(title)}</b><span>7 sheets · Day 7 is revision</span></div>'
            f'<div class="days">{days}</div></div>')
    (OUT / f"{lid}.html").write_text(LEVEL_PAGE.format(lid=lid, lname=lname, ldesc=esc(ldesc), weeks="\n".join(rows)))


INDEX_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <link rel="icon" href="../../assets/favicon.ico" sizes="any" />
  <link rel="icon" type="image/png" sizes="32x32" href="../../assets/logo-32.png" />
  <title>Free home-practice program — like Kumon, but free | ThavionAI School</title>
  <meta name="description" content="A free, structured maths practice program you can print at home: levels that ramp slowly, 26 weeks each, 7 worksheets a week, with intuitive story problems and pictures. No sign-up." />
  <link rel="canonical" href="https://thavionai.com/school/program/index.html" />
  <link rel="preconnect" href="https://fonts.googleapis.com" /><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet" />
  <link rel="stylesheet" href="../../site.css" />
  <style>
    .pg {{ max-width: 820px; margin: 0 auto; padding: 0 22px 70px; }}
    .pg-hero {{ padding: 54px 0 14px; }}
    .pg-hero h1 {{ font-size: clamp(28px,4.8vw,44px); font-weight: 800; letter-spacing: -1.2px; margin: 10px 0 12px; }}
    .pg-hero p {{ color: var(--text2); font-size: 17px; max-width: 660px; }}
    .how {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px,1fr)); gap: 14px; margin: 26px 0; }}
    .how div {{ background: var(--surface); border: 1px solid var(--border); border-radius: 12px; padding: 16px; }}
    .how b {{ display: block; font-size: 14px; margin-bottom: 4px; }}
    .how p {{ font-size: 13px; color: var(--text2); margin: 0; line-height: 1.6; }}
    .lvls {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(240px,1fr)); gap: 16px; margin-top: 12px; }}
    .lvl {{ background: var(--surface); border: 1px solid var(--border); border-radius: 16px; padding: 22px; display: flex; flex-direction: column; }}
    .lvl h3 {{ font-size: 19px; font-weight: 800; margin: 0 0 4px; }}
    .lvl p {{ font-size: 13.5px; color: var(--text2); flex: 1; line-height: 1.6; }}
    .lvl .st {{ font-size: 12px; color: var(--text3); margin: 8px 0 12px; }}
    .lvl a.go {{ display: block; text-align: center; font-weight: 600; border-radius: 10px; padding: 10px; background: var(--accent); color: #fff; }}
    .lvl.soon {{ opacity: 0.75; }}
    .lvl.soon .go {{ background: rgba(15,23,42,0.08); color: var(--text3); pointer-events: none; }}
  </style>
</head>
<body class="theme-light theme-school">
<nav class="site-nav"><div class="nav-inner">
  <a href="../../index.html" class="nav-logo"><img src="../../assets/logo.png" alt="" /><span>ThavionAI<small>Learn. Build. Ship.</small></span></a>
  <button class="nav-toggle" aria-label="Menu" aria-expanded="false" aria-controls="navLinks" onclick="toggleNav()"><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="4" y1="7" x2="20" y2="7"/><line x1="4" y1="12" x2="20" y2="12"/><line x1="4" y1="17" x2="20" y2="17"/></svg></button>
  <div class="nav-links" id="navLinks"><a href="../../index.html">Home</a><a href="../../school.html">School</a><a href="../worksheets/index.html">Worksheets</a><a href="../../exams.html">Exams</a></div>
</div></nav>
<div class="pg">
  <section class="pg-hero">
    <div class="crumbs" style="font-size:13px;color:var(--text3)"><a href="../../index.html" style="color:var(--text2)">Home</a> › <a href="../../school.html" style="color:var(--text2)">School</a> › Practice program</div>
    <span class="chip"><span class="dot"></span> Free forever · No sign-up · Print at home</span>
    <h1>The home-practice program</h1>
    <p>A gentle, structured way to build maths — the kind of daily practice families pay a lot for, made free for everyone. Levels rise slowly, one small step at a time, with intuitive story problems and pictures kids relate to.</p>
  </section>
  <div class="how">
    <div><b>Levels that ramp slowly</b><p>Basic, then Medium, Advanced and Pro. Each level is 26 weeks, so difficulty creeps up gently, never in big jumps.</p></div>
    <div><b>7 sheets a week</b><p>Six new practice sheets plus a revision on Day 7 — about one sheet a day, just like the paid programs.</p></div>
    <div><b>Story problems &amp; pictures</b><p>Friends sharing cakes, apples in a basket — problems that make sense to a child, with soft pictures to count.</p></div>
  </div>
  <div class="lvls">
{levels}
  </div>
</div>
<footer class="site-footer"><div class="max-w"><div class="footer-grid">
  <div class="footer-brand"><a href="../../index.html" class="nav-logo"><img src="../../assets/logo.png" alt="" /><span>ThavionAI</span></a><p>Free education for everyone.</p></div>
  <div class="footer-col"><h4>School</h4><a href="../../school.html">All subjects</a><a href="../worksheets/index.html">Worksheets</a></div>
  <div class="footer-col"><h4>Company</h4><a href="../../index.html#about">About</a><a href="../../feedback.html">Feedback</a><a href="../../privacy.html">Privacy</a><a href="../../terms.html">Terms</a></div>
</div><div class="footer-bottom"><span>© 2025–2026 ThavionAI.</span><span><a href="../../privacy.html">Privacy</a><a href="../../terms.html">Terms</a></span></div></div></footer>
<script>document.documentElement.classList.add('js');function toggleNav(){{var n=document.getElementById('navLinks');var o=n.classList.toggle('open');document.querySelector('.nav-toggle').setAttribute('aria-expanded',o?'true':'false');}}document.querySelectorAll('#navLinks a').forEach(function(a){{a.addEventListener('click',function(){{document.getElementById('navLinks').classList.remove('open');}});}});</script>
</body>
</html>"""


def render_index(built_levels):
    cards = []
    live_ids = {lid for lid, *_ in built_levels}
    plan = [("basic", "Basic", "Counting through adding and subtracting within 20."),
            ("medium", "Medium", "Larger numbers, place value, times tables and money."),
            ("advanced", "Advanced", "Multiplication, division, fractions and multi-step problems."),
            ("pro", "Pro", "Decimals, ratios, and pre-algebra thinking.")]
    for lid, name, desc in plan:
        if lid in live_ids:
            cards.append(f'<div class="lvl"><h3>{name}</h3><p>{esc(desc)}</p><div class="st">26 weeks · 7 sheets a week · live</div><a class="go" href="{lid}.html">Start {name} →</a></div>')
        else:
            cards.append(f'<div class="lvl soon"><h3>{name}</h3><p>{esc(desc)}</p><div class="st">Coming soon</div><a class="go">Coming soon</a></div>')
    (OUT / "index.html").write_text(INDEX_PAGE.format(levels="\n".join(cards)))


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    total = 0
    for level in LEVELS:
        lid, _lname, _ldesc, weeks = level
        seq = [(wk, d) for wk in range(len(weeks)) for d in range(1, 8)]
        for pos, (wk, d) in enumerate(seq):
            prev_href = None
            if pos > 0:
                pw, pd = seq[pos - 1]
                prev_href = f"{lid}-{LETTERS[pw].lower()}-{pd}.html"
            next_href = None
            if pos < len(seq) - 1:
                nw, nd = seq[pos + 1]
                next_href = f"{lid}-{LETTERS[nw].lower()}-{nd}.html"
            render_day(level, wk, d, prev_href, next_href)
            total += 1
        render_level(level)
    render_index(LEVELS)
    print(f"built home-practice program: {len(LEVELS)} level(s), {total} day worksheets -> docs/school/program/")


if __name__ == "__main__":
    main()
