#!/usr/bin/env python3
"""Story Adventures — illustrated, story-driven maths problems for kids.

Little stories with characters and pictures, and picture multiple-choice answers
kids circle. Three problem shapes:
  - elapsed-time word problems (pick the clock)
  - quick "read the clock" drills (see a clock, pick the time) — builds speed
  - addition stories (pick the number)

Outputs (docs/school/stories/):
  index.html            the Story Adventures library
  telling-time.html     time word problems (Krish & Roxy, cakes, parties…)
  quick-clocks.html     fast clock-reading practice
  addition.html         addition adventures

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
COL = {"boy": sd.COLORS["blue"][1], "girl": sd.COLORS["rose"][1], "boy2": sd.COLORS["teal"][1]}


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


def basket(cx, cy):
    return (f'<path d="M{cx-27} {cy} L{cx-21} {cy+24} L{cx+21} {cy+24} L{cx+27} {cy} Z" fill="#e6c79c" stroke="#b98b4e" stroke-width="2" stroke-linejoin="round"/>'
            f'<line x1="{cx-27}" y1="{cy}" x2="{cx+27}" y2="{cy}" stroke="#b98b4e" stroke-width="2.5"/>'
            f'<path d="M{cx-19} {cy} A19 14 0 0 1 {cx+19} {cy}" fill="none" stroke="#b98b4e" stroke-width="2"/>')


def render_scene(items):
    W, H, ground = 330, 152, 128
    parts = [f'<line x1="12" y1="{ground}" x2="{W-12}" y2="{ground}" stroke="#e2e8f0" stroke-width="2"/>']
    for it in items:
        k = it[0]
        if k == "child":
            parts.append(child(it[1], ground, COL[it[2]], it[3]))
        elif k == "dog":
            parts.append(sd.icon("dog", it[1], ground - 16, 20))
        elif k == "icon":
            parts.append(sd.icon(it[1], it[2], it[3], it[4]))
        elif k == "cluster":
            _, kind, x, y, n, s = it
            for i in range(n):
                parts.append(sd.icon(kind, x + (i % 3) * (2 * s + 4), y + (i // 3) * (2 * s + 4), s))
        elif k == "basket":
            parts.append(basket(it[1], it[2]))
    return f'<svg viewBox="0 0 {W} {H}" width="{W}" height="{H}" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="story picture" style="max-width:100%">{"".join(parts)}</svg>'


# ---------------------------------------------------------------- time helpers

def add_time(h, m, dmin):
    total = ((h % 12) * 60 + m + dmin) % (12 * 60)
    hh, mm = total // 60, total % 60
    return (12 if hh == 0 else hh, mm)


def fmt(h, m):
    return f"{h}:{m:02d}"


def four_clocks(ans, i):
    h, m = ans
    cands = [(h, (m + 30) % 60), add_time(h, m, 60), add_time(h, m, -60), add_time(h, m, 15), add_time(h, m, -30)]
    seen, dl = {ans}, []
    for c in cands:
        if c not in seen:
            dl.append(c); seen.add(c)
        if len(dl) == 3:
            break
    idx = i % 4
    opts = [None] * 4
    opts[idx] = ans
    j = 0
    for k in range(4):
        if opts[k] is None:
            opts[k] = dl[j]; j += 1
    return opts, idx


# ---------------------------------------------------------------- scene shortcuts

def boy_dog():
    return [("child", 74, "boy", False), ("dog", 210), ("icon", "ball", 150, 118, 10)]


def girl_prop(kind, x=220, y=108, s=20):
    return [("child", 100, "girl", True), ("icon", kind, x, y, s)]


def boy_prop(kind, who="boy2", x=220, y=108, s=20):
    return [("child", 100, who, False), ("icon", kind, x, y, s)]


def two_kids_ball():
    return [("child", 74, "boy", False), ("child", 236, "girl", True), ("icon", "ball", 155, 118, 11)]


# ---------------------------------------------------------------- elapsed-time stories

# (scene, story-lines, question, start(h,m), duration-min, how)
ELAPSED = [
    (boy_dog(),
     ["Krish loves his dog, Roxy. Every day he can't wait to play fetch with her in the garden.",
      "But Mum has one rule: <b>homework first, then play</b>."],
     "Krish gets home at <b>3:00</b>. His homework takes <b>1 hour</b>. As soon as he finishes, he runs out to play with Roxy. <b>What time does Krish start playing?</b>",
     (3, 0), 60, "3:00 plus 1 hour of homework is 4:00 — that's when the play begins."),
    (girl_prop("cake", y=108, s=22),
     ["Aria is baking a birthday cake for her best friend. She measures everything carefully.",
      "The cake must bake for exactly <b>1 hour</b>."],
     "Aria puts the cake in the oven at <b>2:00</b>. <b>What time will it be ready?</b>",
     (2, 0), 60, "2:00 plus 1 hour of baking is 3:00."),
    (boy_prop("book"),
     ["Leo has a new book about a brave little robot. He can't put it down!",
      "He reads one chapter before bed, and it takes <b>30 minutes</b>."],
     "Leo starts reading at <b>7:00</b>. <b>What time does he finish?</b>",
     (7, 0), 30, "7:00 plus 30 minutes is half past seven — 7:30."),
    ([("child", 96, "girl", True), ("icon", "sun", 258, 52, 16), ("icon", "apple", 190, 116, 10)],
     ["It's a bright morning! Zoe wakes to the sun shining through her window.",
      "She sits down for breakfast, which takes <b>30 minutes</b>."],
     "Zoe starts breakfast at <b>8:00</b>. <b>What time does she finish?</b>",
     (8, 0), 30, "8:00 plus 30 minutes is 8:30."),
    (two_kids_ball(),
     ["Noah and Mia meet at the park after school to play football together.",
      "They play for <b>2 hours</b>, then head home for dinner."],
     "They start at <b>4:00</b>. <b>What time do they stop for dinner?</b>",
     (4, 0), 120, "4:00 plus 2 hours is 6:00."),
    ([("child", 100, "girl", True), ("icon", "balloon", 214, 84, 14), ("icon", "balloon", 248, 92, 14), ("icon", "cake", 190, 112, 16)],
     ["It's Lily's birthday party! Balloons are up, the cake is ready, and friends are arriving.",
      "The party lasts <b>3 hours</b> of games, cake and fun."],
     "The party begins at <b>1:00</b>. <b>What time does it end?</b>",
     (1, 0), 180, "1:00 plus 3 hours is 4:00."),
    (girl_prop("flower", y=110, s=18),
     ["Aria helps in the garden, planting bright flowers with her grandma.",
      "They water and plant for <b>1 hour</b> together."],
     "They start gardening at <b>10:00</b>. <b>What time do they finish?</b>",
     (10, 0), 60, "10:00 plus 1 hour is 11:00."),
    (boy_prop("star", who="boy", y=100, s=16),
     ["Ravi's favourite cartoon is about to start. He gets his cushion and settles down.",
      "The cartoon is <b>30 minutes</b> long."],
     "The cartoon starts at <b>4:00</b>. <b>What time does it finish?</b>",
     (4, 0), 30, "4:00 plus 30 minutes is 4:30."),
    (boy_dog(),
     ["After dinner, Krish takes Roxy for a walk around the block. Roxy loves sniffing everything!",
      "The walk takes <b>30 minutes</b>."],
     "They set off at <b>6:00</b>. <b>What time do they get back home?</b>",
     (6, 0), 30, "6:00 plus 30 minutes is 6:30."),
    (girl_prop("book"),
     ["Ella has swimming practice at the pool, then a snack with her friends.",
      "The swimming lesson lasts <b>1 hour</b>."],
     "The lesson starts at <b>5:00</b>. <b>What time does it end?</b>",
     (5, 0), 60, "5:00 plus 1 hour is 6:00."),
    ([("child", 100, "boy2", False), ("icon", "sun", 258, 52, 15), ("icon", "ball", 205, 116, 10)],
     ["Finn wakes up early on Saturday, excited for his football match in the park.",
      "He gets ready, which takes <b>30 minutes</b>."],
     "Finn starts getting ready at <b>7:00</b>. <b>What time is he ready to go?</b>",
     (7, 0), 30, "7:00 plus 30 minutes is 7:30."),
    (girl_prop("cake", y=108, s=20),
     ["The cake is baked and smells wonderful! Now it must cool before Aria can add the icing.",
      "It needs to cool for <b>30 minutes</b>."],
     "The cake comes out at <b>3:00</b>. <b>What time can Aria add the icing?</b>",
     (3, 0), 30, "3:00 plus 30 minutes is 3:30."),
]


def build_elapsed():
    out = []
    for i, (scene, lines, q, start, dur, how) in enumerate(ELAPSED):
        ans = add_time(*start, dur)
        opts, idx = four_clocks(ans, i)
        out.append({"visual": ("scene", scene), "story": lines, "q": q,
                    "opt_type": "clock", "options": opts, "ans": idx, "how": how})
    return out


# ---------------------------------------------------------------- quick clock reading

def gen_reads(times):
    out = []
    for i, (h, m) in enumerate(times):
        c = (h, m)
        cands = [(h, 30 if m != 30 else 0), (h + 1 if h < 12 else 1, m), (h - 1 if h > 1 else 12, m), (h, (m + 15) % 60)]
        seen, dl = {c}, []
        for d in cands:
            if d not in seen:
                dl.append(d); seen.add(d)
            if len(dl) == 3:
                break
        idx = i % 4
        opts = [None] * 4
        opts[idx] = c
        j = 0
        for k in range(4):
            if opts[k] is None:
                opts[k] = dl[j]; j += 1
        out.append({"visual": ("clock", h, m), "story": [],
                    "q": "Look at the clock. <b>What time does it show?</b>",
                    "opt_type": "time", "options": [fmt(hh, mm) for (hh, mm) in opts],
                    "ans": idx, "how": f"The hands point to {fmt(h, m)}."})
    return out


READ_TIMES = [(2, 0), (3, 30), (5, 15), (7, 45), (9, 0), (11, 30), (1, 15), (4, 45),
              (6, 0), (8, 30), (10, 15), (12, 45), (3, 0), (5, 30), (7, 15), (2, 45),
              (9, 45), (6, 15), (4, 0), (10, 30)]


# ---------------------------------------------------------------- addition stories

# (scene, story-lines, question, a, b, how)
ADD = [
    ([("child", 56, "boy", False), ("cluster", "apple", 24, 34, 4, 8), ("child", 274, "girl", True), ("cluster", "banana", 250, 34, 3, 8), ("basket", 160, 92)],
     ["Krish carries a basket of apples and his friend Mia brings bananas to the picnic."],
     "Krish drops in <b>4 apples</b> and Mia drops in <b>3 bananas</b>. <b>How many fruits are in the basket now?</b>", 4, 3, "4 apples + 3 bananas = 7 fruits."),
    (boy_dog(),
     ["Krish is teaching Roxy to fetch. He throws the ball, and Roxy brings it back every time!"],
     "Krish throws the ball <b>5 times</b> before lunch and <b>2 times</b> after. <b>How many throws in all?</b>", 5, 2, "5 + 2 = 7 throws."),
    ([("child", 100, "girl", True), ("cluster", "balloon", 200, 66, 6, 12)],
     ["Lily is decorating for her party. She blows up balloons and ties them to the chairs."],
     "Lily puts up <b>6 balloons</b>, then <b>3 more</b>. <b>How many balloons in all?</b>", 6, 3, "6 + 3 = 9 balloons."),
    ([("child", 100, "boy2", False), ("cluster", "star", 200, 60, 4, 11)],
     ["Finn earns gold stars at school for helping his classmates."],
     "Finn gets <b>4 stars</b> on Monday and <b>4 more</b> on Tuesday. <b>How many stars altogether?</b>", 4, 4, "4 + 4 = 8 stars."),
    ([("child", 100, "girl", True), ("icon", "cake", 210, 108, 18), ("cluster", "flower", 40, 60, 3, 12)],
     ["Aria makes little cakes and puts a flower on each one for the party table."],
     "There are <b>3 cakes</b> on one plate and <b>2 cakes</b> on another. <b>How many cakes in all?</b>", 3, 2, "3 + 2 = 5 cakes."),
    ([("child", 56, "boy", False), ("cluster", "apple", 24, 44, 3, 9), ("child", 274, "girl", True), ("cluster", "orange", 252, 44, 4, 9), ("basket", 160, 92)],
     ["Noah picks apples and Zoe picks oranges from the trees, sharing one big basket."],
     "Noah adds <b>3 apples</b> and Zoe adds <b>4 oranges</b>. <b>How many fruits are in the basket?</b>", 3, 4, "3 + 4 = 7 fruits."),
    (boy_dog(),
     ["Roxy has hidden her toy balls all around the garden. Krish goes on a hunt to find them!"],
     "Krish finds <b>2 balls</b> under the bush and <b>3 balls</b> by the tree. <b>How many balls did he find?</b>", 2, 3, "2 + 3 = 5 balls."),
    ([("child", 100, "girl", True), ("cluster", "star", 200, 58, 5, 11)],
     ["Ella collects shiny stickers in her sticker book. She loves the star ones best."],
     "Ella has <b>5 star stickers</b> and buys <b>4 more</b>. <b>How many star stickers now?</b>", 5, 4, "5 + 4 = 9 stickers."),
    ([("child", 100, "boy2", False), ("cluster", "balloon", 200, 66, 3, 12)],
     ["It's a windy day and Kai is holding tight to his balloons at the fair."],
     "Kai has <b>3 balloons</b> and his uncle gives him <b>2 more</b>. <b>How many balloons does Kai have?</b>", 3, 2, "3 + 2 = 5 balloons."),
    ([("child", 56, "boy", False), ("cluster", "banana", 24, 44, 2, 9), ("child", 274, "girl", True), ("cluster", "apple", 252, 44, 5, 9), ("basket", 160, 92)],
     ["Sam brings bananas and Mia brings apples for the fruit salad."],
     "Sam adds <b>2 bananas</b> and Mia adds <b>5 apples</b>. <b>How many fruits are in the bowl?</b>", 2, 5, "2 + 5 = 7 fruits."),
]


def build_add():
    out = []
    for i, (scene, lines, q, a, b, how) in enumerate(ADD):
        ans = a + b
        cands = [ans + 1, ans - 1, ans + 2, ans - 2]
        seen, dl = {ans}, []
        for c in cands:
            if c > 0 and c not in seen:
                dl.append(c); seen.add(c)
            if len(dl) == 3:
                break
        idx = i % 4
        opts = [None] * 4
        opts[idx] = ans
        j = 0
        for k in range(4):
            if opts[k] is None:
                opts[k] = dl[j]; j += 1
        out.append({"visual": ("scene", scene), "story": lines, "q": q,
                    "opt_type": "number", "options": opts, "ans": idx, "how": how})
    return out


BOOKS = [
    {"id": "telling-time", "title": "What time is it?", "emoji": "\U0001f550",
     "intro": "Little stories about Krish and Roxy, cakes in the oven and birthday parties — read what happens, then circle the clock that shows the right time.",
     "note": "Circle the clock (A, B, C or D) that shows the right time.",
     "build": build_elapsed},
    {"id": "quick-clocks", "title": "Quick clock reading", "emoji": "⏱️",
     "intro": "Speed practice! Look at each clock and circle the time it shows — as fast as you can. The more you do, the quicker you get.",
     "note": "Circle the time (A, B, C or D) that the clock shows.",
     "build": lambda: gen_reads(READ_TIMES)},
    {"id": "addition", "title": "Addition adventures", "emoji": "➕",
     "intro": "Fun little stories about friends, fruit and pets — read the story, count the pictures, and circle how many there are altogether.",
     "note": "Circle the number (A, B, C or D) that answers the question.",
     "build": build_add},
]


# ---------------------------------------------------------------- rendering

def render_visual(v):
    if v[0] == "scene":
        return render_scene(v[1])
    return sd.clock(v[1], v[2], show_time=False)  # ("clock", h, m)


def render_options(opt_type, options):
    boxes = []
    for i, o in enumerate(options):
        if opt_type == "clock":
            inner = sd.clock(o[0], o[1], show_time=False)
        elif opt_type == "time":
            inner = f'<div class="bigopt">{esc(o)}</div>'
        else:
            inner = f'<div class="bigopt">{o}</div>'
        boxes.append(f'<div class="opt"><span class="ol">{LET[i]}</span>{inner}</div>')
    return f'<div class="opts {opt_type}">' + "".join(boxes) + "</div>"


def answer_text(p):
    o = p["options"][p["ans"]]
    return fmt(*o) if p["opt_type"] == "clock" else str(o)


CSS = """
    .ws { max-width: 780px; margin: 0 auto; padding: 0 22px 70px; }
    .ws-hero { padding: 46px 0 12px; }
    .ws-hero h1 { font-size: clamp(26px,4.4vw,38px); font-weight: 800; letter-spacing: -1px; margin: 8px 0 10px; }
    .ws-hero p { color: var(--text2); font-size: 16px; max-width: 640px; }
    .ws-actions { display: flex; flex-wrap: wrap; gap: 10px; margin-top: 16px; }
    .story-card { border: 1px solid var(--border); border-radius: 16px; background: #fff; padding: 18px 22px; margin-top: 20px; break-inside: avoid; }
    .story-card .snum { font-size: 12px; font-weight: 800; letter-spacing: 0.08em; text-transform: uppercase; color: var(--accent); }
    .story-scene { text-align: center; margin: 8px 0 6px; }
    .story-scene svg { max-width: 100%; height: auto; }
    .story-text p { font-size: 15.5px; color: var(--text); line-height: 1.6; margin: 6px 0; }
    .story-q { font-size: 15.5px; color: var(--text); line-height: 1.6; background: rgba(2,132,199,0.06); border-left: 3px solid var(--accent); border-radius: 8px; padding: 10px 14px; margin: 12px 0; }
    .opts { display: grid; gap: 10px; margin-top: 8px; }
    .opts.clock { grid-template-columns: repeat(4, 1fr); }
    .opts.time, .opts.number { grid-template-columns: repeat(4, 1fr); }
    .opt { border: 1.5px solid var(--border2); border-radius: 12px; padding: 8px 6px 10px; text-align: center; }
    .opt .ol { display: inline-block; font-weight: 800; font-size: 13px; color: var(--text2); border: 1.5px solid var(--border2); border-radius: 50%; width: 22px; height: 22px; line-height: 20px; margin-bottom: 4px; }
    .opt svg { max-width: 100%; height: auto; }
    .bigopt { font-size: 26px; font-weight: 800; color: var(--text); padding: 14px 0; letter-spacing: -0.5px; }
    .circle-note { font-size: 13px; color: var(--text3); margin-top: 6px; }
    .answers { margin-top: 34px; border-top: 2px dashed var(--border); padding-top: 16px; }
    .akey p { font-size: 13.5px; color: var(--text2); margin: 4px 0; }
    .ws-foot { margin-top: 26px; font-size: 12px; color: var(--text3); text-align: center; }
    @media (max-width: 560px) { .opts.clock { grid-template-columns: repeat(2, 1fr); } }
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


def page(title, desc, body, css=CSS):
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
  <style>{css}</style>
</head>
<body class="theme-light theme-school">
{NAV}
{body}
{FOOTER}
{SCRIPT}
</body>
</html>"""


def build_book(book):
    problems = book["build"]()
    cards, keys = [], []
    for i, p in enumerate(problems, 1):
        story = "".join(f"<p>{s}</p>" for s in p["story"])
        story_html = f'<div class="story-text">{story}</div>' if story else ""
        cards.append(
            f'<section class="story-card"><div class="snum">{i}</div>'
            f'<div class="story-scene">{render_visual(p["visual"])}</div>'
            f'{story_html}<div class="story-q">{p["q"]}</div>{render_options(p["opt_type"], p["options"])}'
            f'<p class="circle-note">{esc(book["note"])}</p></section>')
        keys.append(f'<p><b>{i}:</b> {LET[p["ans"]]} — {esc(answer_text(p))}. {esc(p["how"])}</p>')
    body = f"""<div class="ws">
  <section class="ws-hero">
    <div class="crumbs no-print" style="font-size:13px;color:var(--text3)"><a href="../../index.html" style="color:var(--text2)">Home</a> › <a href="../../school.html" style="color:var(--text2)">School</a> › <a href="index.html" style="color:var(--text2)">Story Adventures</a> › {esc(book["title"])}</div>
    <h1>{book["emoji"]} {esc(book["title"])}</h1>
    <p>{esc(book["intro"])}</p>
    <div class="ws-actions no-print">
      <button class="btn btn-primary" onclick="window.print()">\U0001f5a8️ Print these</button>
      <a class="btn btn-secondary" href="index.html">More stories</a>
    </div>
  </section>
{"".join(cards)}
  <section class="answers"><h2 style="font-size:15px;font-weight:800">Answer key <span style="font-weight:500;color:var(--text3);font-size:12px">(for grown-ups)</span></h2><div class="akey">{"".join(keys)}</div></section>
  <p class="ws-foot">Free illustrated story problems from ThavionAI · thavionai.com · print and share freely.</p>
</div>"""
    (OUT / f"{book['id']}.html").write_text(page(f"{book['title']} — story problems", book["intro"], body))
    return len(problems)


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
    .bk .cnt { font-size: 12px; color: var(--text3); margin: 6px 0 10px; }
    .bk a { display: block; text-align: center; font-weight: 600; border-radius: 10px; padding: 10px; background: var(--accent); color: #fff; }
"""


def build_index(counts):
    cards = "".join(
        f'<div class="bk"><span class="em">{b["emoji"]}</span><h3>{esc(b["title"])}</h3><p>{esc(b["intro"])}</p>'
        f'<div class="cnt">{counts[b["id"]]} problems · illustrated · answer key</div>'
        f'<a href="{b["id"]}.html">Read &amp; solve →</a></div>'
        for b in BOOKS)
    body = f"""<div class="pg">
  <section class="pg-hero">
    <div class="crumbs" style="font-size:13px;color:var(--text3)"><a href="../../index.html" style="color:var(--text2)">Home</a> › <a href="../../school.html" style="color:var(--text2)">School</a> › Story Adventures</div>
    <span class="chip"><span class="dot"></span> Free · Illustrated · Printable</span>
    <h1>Story Adventures</h1>
    <p>Maths wrapped in little stories, with characters and pictures kids love. Read what happens, then circle the right answer. New adventures are added often.</p>
  </section>
  <div class="cards">{cards}</div>
</div>"""
    (OUT / "index.html").write_text(page("Story Adventures — illustrated maths stories", "Free illustrated, story-driven maths problems for kids.", body, css=INDEX_CSS))


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    counts = {b["id"]: build_book(b) for b in BOOKS}
    build_index(counts)
    print(f"built Story Adventures: {len(BOOKS)} books, {sum(counts.values())} problems -> docs/school/stories/  (" +
          ", ".join(f"{k} {v}" for k, v in counts.items()) + ")")


if __name__ == "__main__":
    main()
