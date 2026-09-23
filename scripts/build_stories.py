#!/usr/bin/env python3
"""Story Adventures — illustrated, story-driven maths problems for kids.

Each problem is a little story with characters and a picture (a boy and his dog,
a girl baking a cake…), a question, and picture multiple-choice answers (e.g. four
clocks to circle). Built to pull children into the story so they *want* to solve it.

Outputs (docs/school/stories/):
  index.html            the Story Adventures library
  telling-time.html     "What time is it?" — clock stories

Usage:  python3 scripts/build_stories.py
"""
import html
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "school" / "stories"
sys.path.insert(0, str(Path(__file__).resolve().parent))
import school_diagrams as sd  # noqa: E402

esc = html.escape
INK = sd.INK
LET = ["A", "B", "C", "D"]


# ---------------------------------------------------------------- scene drawing

def child(cx, base, color, girl):
    hr, hy = 12, base - 48
    p = [f'<circle cx="{cx}" cy="{hy}" r="{hr}" fill="#ffe0bd" stroke="{INK}" stroke-width="1.8"/>',
         f'<circle cx="{cx-4}" cy="{hy-1}" r="1.6" fill="{INK}"/><circle cx="{cx+4}" cy="{hy-1}" r="1.6" fill="{INK}"/>',
         f'<path d="M{cx-4} {hy+4} Q{cx} {hy+9} {cx+4} {hy+4}" fill="none" stroke="{INK}" stroke-width="1.5" stroke-linecap="round"/>',
         f'<path d="M{cx-hr} {hy-1} A{hr} {hr} 0 0 1 {cx+hr} {hy-1}" fill="{color}"/>']
    if girl:
        p.append(f'<polygon points="{cx},{hy+hr-1} {cx-18},{base} {cx+18},{base}" fill="{color}" stroke="{INK}" stroke-width="1.6" stroke-linejoin="round"/>')
    else:
        p.append(f'<rect x="{cx-12}" y="{hy+hr-1}" width="24" height="24" rx="5" fill="{color}" stroke="{INK}" stroke-width="1.6"/>')
        p.append(f'<line x1="{cx-6}" y1="{base-6}" x2="{cx-6}" y2="{base}" stroke="{INK}" stroke-width="2.8" stroke-linecap="round"/>'
                 f'<line x1="{cx+6}" y1="{base-6}" x2="{cx+6}" y2="{base}" stroke="{INK}" stroke-width="2.8" stroke-linecap="round"/>')
    ay = hy + hr + 6
    p.append(f'<line x1="{cx-12}" y1="{ay}" x2="{cx-24}" y2="{ay+12}" stroke="{INK}" stroke-width="2.4" stroke-linecap="round"/>'
             f'<line x1="{cx+12}" y1="{ay}" x2="{cx+24}" y2="{ay+12}" stroke="{INK}" stroke-width="2.4" stroke-linecap="round"/>')
    return "".join(p)


COL = {"boy": sd.COLORS["blue"][1], "girl": sd.COLORS["rose"][1], "boy2": sd.COLORS["teal"][1]}


def render_scene(items):
    W, H, ground = 330, 152, 128
    parts = [f'<line x1="12" y1="{ground}" x2="{W-12}" y2="{ground}" stroke="#e2e8f0" stroke-width="2"/>']
    for it in items:
        k = it[0]
        if k == "child":
            _, x, who, girl = it
            parts.append(child(x, ground, COL[who], girl))
        elif k == "dog":
            parts.append(sd.icon("dog", it[1], ground - 16, 20))
        elif k == "icon":
            _, kind, x, y, s = it
            parts.append(sd.icon(kind, x, y, s))
    body = "".join(parts)
    return f'<svg viewBox="0 0 {W} {H}" width="{W}" height="{H}" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="story picture" style="max-width:100%">{body}</svg>'


def clock_options(times):
    boxes = []
    for i, (h, m) in enumerate(times):
        boxes.append(f'<div class="opt"><span class="ol">{LET[i]}</span>{sd.clock(h, m, show_time=False)}</div>')
    return '<div class="opts">' + "".join(boxes) + "</div>"


# ---------------------------------------------------------------- the stories

def t(h, m=0):
    return (h, m)


TELLING_TIME = [
    {
        "scene": [("child", 74, "boy", False), ("dog", 210), ("icon", "ball", 150, 118, 10)],
        "story": ["Krish loves his dog, Roxy. Every day he can't wait to play fetch with her in the garden.",
                  "But Mum has one rule: <b>homework first, then play</b>."],
        "q": "Krish gets home from school at <b>3:00</b>. His homework takes <b>1 hour</b>. As soon as he finishes, he runs out to play with Roxy. <b>What time does Krish start playing?</b>",
        "options": [t(3, 30), t(4, 0), t(4, 30), t(5, 0)],
        "ans": 1,
        "how": "Homework starts at 3:00 and takes 1 hour, so it finishes at 4:00. That is when Krish starts playing."},
    {
        "scene": [("child", 100, "girl", True), ("icon", "cake", 220, 108, 22)],
        "story": ["Aria is baking a birthday cake for her friend. She reads the recipe very carefully.",
                  "The cake must bake in the oven for exactly <b>1 hour</b>."],
        "q": "Aria puts the cake in the oven at <b>2:00</b>. <b>What time will the cake be ready?</b>",
        "options": [t(2, 30), t(3, 0), t(3, 30), t(4, 0)],
        "ans": 1,
        "how": "2:00 plus 1 hour of baking is 3:00."},
    {
        "scene": [("child", 100, "boy2", False), ("icon", "book", 220, 106, 20)],
        "story": ["Leo has a new story book about a brave little robot. He can't put it down!",
                  "He decides to read one chapter before bed. It takes him <b>30 minutes</b>."],
        "q": "Leo starts reading at <b>7:00</b>. <b>What time does he finish his chapter?</b>",
        "options": [t(7, 15), t(7, 30), t(8, 0), t(7, 45)],
        "ans": 1,
        "how": "7:00 plus 30 minutes is half past seven — 7:30."},
    {
        "scene": [("child", 96, "girl", True), ("icon", "sun", 258, 52, 16), ("icon", "apple", 190, 116, 10)],
        "story": ["It's a bright morning! Zoe wakes up to the sun shining through her window.",
                  "She gets ready and sits down for breakfast, which takes <b>30 minutes</b>."],
        "q": "Zoe starts her breakfast at <b>8:00</b>. <b>What time does she finish?</b>",
        "options": [t(8, 30), t(9, 0), t(8, 15), t(8, 45)],
        "ans": 0,
        "how": "8:00 plus 30 minutes is 8:30."},
    {
        "scene": [("child", 74, "boy", False), ("child", 236, "girl", True), ("icon", "ball", 155, 118, 11)],
        "story": ["Noah and Mia meet at the park after school to play football together.",
                  "They agree to play for <b>2 hours</b>, then head home for dinner."],
        "q": "They start playing at <b>4:00</b>. <b>What time do they stop for dinner?</b>",
        "options": [t(5, 0), t(5, 30), t(6, 0), t(7, 0)],
        "ans": 2,
        "how": "4:00 plus 2 hours is 6:00."},
    {
        "scene": [("child", 100, "girl", True), ("icon", "balloon", 214, 84, 14), ("icon", "balloon", 248, 92, 14), ("icon", "cake", 190, 112, 16)],
        "story": ["It's Lily's birthday party! Balloons are up, the cake is ready, and friends are on the way.",
                  "The party lasts <b>3 hours</b> of games, cake and fun."],
        "q": "The party begins at <b>1:00</b>. <b>What time does the party end?</b>",
        "options": [t(3, 0), t(4, 0), t(4, 30), t(5, 0)],
        "ans": 1,
        "how": "1:00 plus 3 hours is 4:00."},
]


BOOKS = [
    {"id": "telling-time", "title": "What time is it?", "emoji": "\U0001f550",
     "intro": "Little stories about Krish, Aria, Leo and friends — read what happens, then circle the clock that shows the right time. A fun way to learn to read a clock.",
     "stories": TELLING_TIME},
]


# ---------------------------------------------------------------- pages

CSS = """
    .ws { max-width: 780px; margin: 0 auto; padding: 0 22px 70px; }
    .ws-hero { padding: 46px 0 12px; }
    .ws-hero h1 { font-size: clamp(26px,4.4vw,38px); font-weight: 800; letter-spacing: -1px; margin: 8px 0 10px; }
    .ws-hero p { color: var(--text2); font-size: 16px; max-width: 640px; }
    .ws-actions { display: flex; flex-wrap: wrap; gap: 10px; margin-top: 16px; }
    .story-card { border: 1px solid var(--border); border-radius: 16px; background: #fff; padding: 20px 22px; margin-top: 22px; break-inside: avoid; }
    .story-card .snum { font-size: 12px; font-weight: 800; letter-spacing: 0.08em; text-transform: uppercase; color: var(--accent); }
    .story-scene { text-align: center; margin: 10px 0 6px; }
    .story-scene svg { max-width: 100%; height: auto; }
    .story-text p { font-size: 15.5px; color: var(--text); line-height: 1.6; margin: 6px 0; }
    .story-q { font-size: 15.5px; color: var(--text); line-height: 1.6; background: rgba(2,132,199,0.06); border-left: 3px solid var(--accent); border-radius: 8px; padding: 10px 14px; margin: 12px 0; }
    .opts { display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; margin-top: 8px; }
    .opt { border: 1.5px solid var(--border2); border-radius: 12px; padding: 8px 6px 10px; text-align: center; }
    .opt .ol { display: inline-block; font-weight: 800; font-size: 13px; color: var(--text2); border: 1.5px solid var(--border2); border-radius: 50%; width: 22px; height: 22px; line-height: 20px; margin-bottom: 4px; }
    .opt svg { max-width: 100%; height: auto; }
    .circle-note { font-size: 13px; color: var(--text3); margin-top: 6px; }
    .answers { margin-top: 34px; border-top: 2px dashed var(--border); padding-top: 16px; }
    .akey p { font-size: 13.5px; color: var(--text2); margin: 4px 0; }
    .ws-foot { margin-top: 26px; font-size: 12px; color: var(--text3); text-align: center; }
    @media (max-width: 560px) { .opts { grid-template-columns: repeat(2, 1fr); } }
    @media print { .site-nav, .site-footer, .no-print { display: none !important; } body { background: #fff; } .story-card { break-inside: avoid; } .answers { break-before: page; } }
"""

NAV = """<nav class="site-nav no-print"><div class="nav-inner">
  <a href="../../index.html" class="nav-logo"><img src="../../assets/logo.png" alt="" /><span>ThavionAI<small>Learn. Build. Ship.</small></span></a>
  <button class="nav-toggle" aria-label="Menu" aria-expanded="false" aria-controls="navLinks" onclick="toggleNav()"><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="4" y1="7" x2="20" y2="7"/><line x1="4" y1="12" x2="20" y2="12"/><line x1="4" y1="17" x2="20" y2="17"/></svg></button>
  <div class="nav-links" id="navLinks"><a href="../../index.html">Home</a><a href="../../school.html">School</a><a href="index.html">Story Adventures</a><a href="../worksheets/index.html">Worksheets</a></div>
</div></nav>"""

FOOTER = """<footer class="site-footer no-print"><div class="max-w"><div class="footer-grid">
  <div class="footer-brand"><a href="../../index.html" class="nav-logo"><img src="../../assets/logo.png" alt="" /><span>ThavionAI</span></a><p>Free education for everyone.</p></div>
  <div class="footer-col"><h4>School</h4><a href="../../school.html">All subjects</a><a href="index.html">Story Adventures</a><a href="../program/index.html">Practice program</a></div>
  <div class="footer-col"><h4>Company</h4><a href="../../index.html#about">About</a><a href="../../feedback.html">Feedback</a><a href="../../privacy.html">Privacy</a><a href="../../terms.html">Terms</a></div>
</div><div class="footer-bottom"><span>© 2025–2026 ThavionAI.</span><span><a href="../../privacy.html">Privacy</a><a href="../../terms.html">Terms</a></span></div></div></footer>"""

SCRIPT = """<script>document.documentElement.classList.add('js');function toggleNav(){var n=document.getElementById('navLinks');var o=n.classList.toggle('open');document.querySelector('.nav-toggle').setAttribute('aria-expanded',o?'true':'false');}document.querySelectorAll('#navLinks a').forEach(function(a){a.addEventListener('click',function(){document.getElementById('navLinks').classList.remove('open');});});</script>"""


def page(title, desc, body):
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <link rel="icon" href="../../assets/favicon.ico" sizes="any" />
  <link rel="icon" type="image/png" sizes="32x32" href="../../assets/logo-32.png" />
  <title>{esc(title)} | ThavionAI School</title>
  <meta name="description" content="{esc(desc)}" />
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


def build_book(book):
    cards, keys = [], []
    for i, s in enumerate(book["stories"], 1):
        scene = render_scene(s["scene"])
        story = "".join(f"<p>{p}</p>" for p in s["story"])
        opts = clock_options(s["options"])
        cards.append(
            f'<section class="story-card"><div class="snum">Story {i}</div>'
            f'<div class="story-scene">{scene}</div>'
            f'<div class="story-text">{story}</div>'
            f'<div class="story-q">{s["q"]}</div>{opts}'
            f'<p class="circle-note">Circle the clock (A, B, C or D) that shows the right time.</p></section>')
        h, m = s["options"][s["ans"]]
        keys.append(f'<p><b>Story {i}:</b> {LET[s["ans"]]} — {h}:{m:02d}. {esc(s["how"])}</p>')
    body = f"""<div class="ws">
  <section class="ws-hero">
    <div class="crumbs no-print" style="font-size:13px;color:var(--text3)"><a href="../../index.html" style="color:var(--text2)">Home</a> › <a href="../../school.html" style="color:var(--text2)">School</a> › <a href="index.html" style="color:var(--text2)">Story Adventures</a> › {esc(book["title"])}</div>
    <h1>{book["emoji"]} {esc(book["title"])}</h1>
    <p>{esc(book["intro"])}</p>
    <div class="ws-actions no-print">
      <button class="btn btn-primary" onclick="window.print()">\U0001f5a8️ Print these stories</button>
      <a class="btn btn-secondary" href="index.html">More stories</a>
    </div>
  </section>
{"".join(cards)}
  <section class="answers"><h2 style="font-size:15px;font-weight:800">Answer key <span style="font-weight:500;color:var(--text3);font-size:12px">(for grown-ups)</span></h2><div class="akey">{"".join(keys)}</div></section>
  <p class="ws-foot">Free illustrated story problems from ThavionAI · thavionai.com · print and share freely.</p>
</div>"""
    (OUT / f"{book['id']}.html").write_text(page(f"{book['title']} — story problems", book["intro"], body))


INDEX_CSS = """
    .pg { max-width: 780px; margin: 0 auto; padding: 0 22px 70px; }
    .pg-hero { padding: 52px 0 14px; }
    .pg-hero h1 { font-size: clamp(28px,4.6vw,42px); font-weight: 800; letter-spacing: -1.1px; margin: 10px 0 12px; }
    .pg-hero p { color: var(--text2); font-size: 17px; max-width: 640px; }
    .cards { display: grid; grid-template-columns: repeat(auto-fill, minmax(240px,1fr)); gap: 16px; margin-top: 24px; }
    .bk { background: var(--surface); border: 1px solid var(--border); border-radius: 16px; padding: 22px; display: flex; flex-direction: column; }
    .bk .em { font-size: 30px; }
    .bk h3 { font-size: 18px; font-weight: 800; margin: 8px 0 4px; }
    .bk p { font-size: 13.5px; color: var(--text2); flex: 1; line-height: 1.6; }
    .bk a { display: block; text-align: center; font-weight: 600; border-radius: 10px; padding: 10px; background: var(--accent); color: #fff; margin-top: 12px; }
"""


def build_index():
    cards = "".join(
        f'<div class="bk"><span class="em">{b["emoji"]}</span><h3>{esc(b["title"])}</h3><p>{esc(b["intro"])}</p><a href="{b["id"]}.html">Read &amp; solve →</a></div>'
        for b in BOOKS)
    body = f"""<div class="pg">
  <section class="pg-hero">
    <div class="crumbs" style="font-size:13px;color:var(--text3)"><a href="../../index.html" style="color:var(--text2)">Home</a> › <a href="../../school.html" style="color:var(--text2)">School</a> › Story Adventures</div>
    <span class="chip"><span class="dot"></span> Free · Illustrated · Printable</span>
    <h1>Story Adventures</h1>
    <p>Maths wrapped in little stories, with characters and pictures kids love. Read what happens, then pick the right answer. New adventures are added often.</p>
  </section>
  <div class="cards">{cards}</div>
</div>"""
    html_out = page("Story Adventures — illustrated maths stories", "Free illustrated, story-driven maths problems for kids.", body).replace(f"<style>{CSS}</style>", f"<style>{INDEX_CSS}</style>")
    (OUT / "index.html").write_text(html_out)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for book in BOOKS:
        build_book(book)
    build_index()
    print(f"built Story Adventures: {len(BOOKS)} book(s), {sum(len(b['stories']) for b in BOOKS)} stories -> docs/school/stories/")


if __name__ == "__main__":
    main()
