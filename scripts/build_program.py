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


# Math is everywhere: story templates across many parts of life.
# Each: (text with {n1}{n2}{a}{b}, optional icon to illustrate small ones).
STORY = {
    "add": [
        ("{n1} and {n2} meet at school. {n1} brings {a} apples and {n2} brings {b}. How many apples do they have altogether?", "apple"),
        ("There are {a} birds on a branch. {b} more birds fly over. How many birds are on the branch now?", None),
        ("A flower has {a} red petals and {b} yellow petals. How many petals does it have in all?", "flower"),
        ("{n1} takes {a} steps to the door, then {b} more steps to the gate. How many steps in all?", None),
        ("{n1} reads {a} pages before dinner and {b} pages after. How many pages did {n1} read?", None),
        ("There are {a} red cars and {b} blue cars in the car park. How many cars are there?", None),
        ("A bag has {a} kg of rice. {n1} adds {b} kg of flour. How many kg are in the bag now?", None),
        ("{n1} counts {a} fingers, then {b} toes. How many did {n1} count in all?", None),
        ("A tree has {a} apples. {n1} picks {b} more from another tree. How many apples in all?", "apple"),
        ("{n1} has {a} balloons and {n2} gives {b} more. How many balloons does {n1} have now?", "balloon"),
        ("There are {a} ducks in the pond and {b} ducks on the grass. How many ducks in all?", None),
        ("{n1} watches {a} minutes of a show, then {b} more minutes. How many minutes in all?", None),
        ("A shelf has {a} books. {n1} puts {b} more books on it. How many books are on the shelf?", None),
        ("{n1} hops {a} times, then {b} more times. How many hops in all?", None),
        ("There are {a} stars in one picture and {b} stars in another. How many stars altogether?", "star"),
        ("{n1} has {a} stickers and earns {b} more at school. How many stickers now?", "star"),
        ("A cake has {a} candles. {n1} adds {b} more candles. How many candles are on the cake?", "cake"),
        ("{a} ants are on a leaf and {b} more come along. How many ants are on the leaf?", None),
        ("{n1} has {a} dollars and finds {b} more. How many dollars does {n1} have?", None),
        ("A garden has {a} flowers. {b} new flowers bloom. How many flowers are there now?", "flower"),
        ("{n1} skips for {a} minutes and {n2} skips for {b} minutes. How many minutes did they skip in all?", None),
        ("A snail crawls {a} cm, then {b} cm more. How far did it crawl in all?", None),
    ],
    "sub": [
        ("{n1} has {a} apples and gives {b} to {n2}. How many apples does {n1} have left?", "apple"),
        ("There are {a} birds on a wire. {b} birds fly away. How many birds are left?", None),
        ("{n1} has {a} balloons, but {b} float away. How many balloons are left?", "balloon"),
        ("A plate has {a} cakes. {n1} eats {b} of them. How many cakes are left?", "cake"),
        ("The shop is {a} blocks away. {n1} has walked {b} blocks. How many blocks are left?", None),
        ("A book has {a} pages. {n1} has read {b} pages. How many pages are left to read?", None),
        ("There are {a} ducks on the pond. {b} ducks swim away. How many ducks are left?", None),
        ("{n1} had {a} dollars and spends {b}. How many dollars are left?", None),
        ("A bag has {a} kg of apples. {n1} takes out {b} kg. How many kg are left?", None),
        ("The film is {a} hours long. {n1} has watched {b} hours. How many hours are left?", None),
        ("A tree has {a} apples. {b} apples fall down. How many apples are still on the tree?", "apple"),
        ("{n1} has {a} stickers and gives {b} to a friend. How many stickers are left?", "star"),
        ("There are {a} flowers in a vase. {b} of them wilt. How many fresh flowers are left?", "flower"),
        ("{n1} has {a} marbles and loses {b}. How many marbles are left?", "ball"),
        ("A box has {a} toys. {n1} gives {b} away. How many toys are left in the box?", "gift"),
        ("There are {a} children in the park. {b} of them go home. How many children are left?", None),
        ("{n1} had {a} sweets and eats {b}. How many sweets are left?", None),
        ("A branch has {a} leaves. {b} leaves blow away in the wind. How many leaves are left?", None),
        ("{n1} takes {a} steps forward and {b} steps back. How many steps ahead is {n1} now?", None),
        ("There are {a} stars in the sky. {b} are hidden by a cloud. How many stars can you still see?", "star"),
        ("A caterpillar has {a} spots. {b} fade away. How many spots are left?", None),
        ("{n1} has {a} minutes to play. {b} minutes go by. How many minutes are left?", None),
    ],
}


def p_story(rnd, op, hi):
    n1, n2 = rnd.sample(NAMES, 2)
    a, b = gab(rnd, op, hi)
    text, ic = rnd.choice(STORY[op])
    text = text.format(n1=n1, n2=n2, a=a, b=b)
    ans = a + b if op == "add" else a - b
    return {"t": "story", "text": text, "a": a, "b": b, "op": op,
            "illus": (ic is not None and a <= 6 and b <= 6), "ic": ic or "apple", "ans": ans}


DAY_INTROS = [
    "Today, {n1} and {n2} spend the day at the park. There are birds to count, petals to add and snacks to share — maths is all around them. Grab a pencil and help!",
    "It's a busy morning at {n1}'s house. Cakes on the table, balloons in the air, toys everywhere. Let's do the maths together, one sheet at a time.",
    "{n1} and {n2} go on a nature walk. Ducks on the pond, apples on the trees, flowers in the grass — can you find the maths hiding everywhere?",
    "It's a school day! {n1} and {n2} count books, share stickers and read pages. Every little thing has a number in it. Ready to solve them?",
    "{n1} is helping in the kitchen and the garden today. Counting, adding and taking away pop up in everything. Let's help {n1} work it out!",
    "A trip to the shop with {n1} and {n2}! Coins to count, steps to walk, things to carry home. Maths really is everywhere — let's practise it.",
    "{n1} is having a birthday party! Friends arrive, presents pile up and cakes get shared. There's a lot of maths in one happy day.",
    "Rainy-day fun indoors for {n1} and {n2}: board games, marbles and drawing. Count, add and take away as you play along.",
]


def day_intro(rnd):
    n1, n2 = rnd.sample(NAMES, 2)
    return rnd.choice(DAY_INTROS).format(n1=n1, n2=n2)


FRUITS = [("apples", "apple"), ("bananas", "banana"), ("oranges", "orange")]


def p_scene(rnd, hi):
    n1, n2 = rnd.sample(NAMES, 2)
    (pa, ica), (pb, icb) = rnd.sample(FRUITS, 2)
    cap = min(hi, 6)
    a, b = rnd.randint(1, cap), rnd.randint(1, cap)
    tpl = rnd.choice([
        "{n1} carries {a} {pa} and {n2} carries {b} {pb}. They drop them all into the same basket. How many fruits are in the basket now?",
        "{n1} picks {a} {pa} and {n2} picks {b} {pb}. They put every fruit into one basket. How many fruits are in the basket altogether?",
        "{n1} brings {a} {pa} to the picnic and {n2} brings {b} {pb}. They tip them into one basket to share. How many fruits are in the basket?",
    ])
    return {"t": "scene", "a": a, "b": b, "ica": ica, "icb": icb,
            "text": tpl.format(n1=n1, n2=n2, a=a, b=b, pa=pa, pb=pb), "ans": a + b}


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


HEADS = {"count": "Count the pictures and write the number",
         "trace": "Trace the numbers, then write your own",
         "compare": "Write &gt;, &lt; or = in the box",
         "order": "Fill in the missing number",
         "add": "Add", "sub": "Subtract", "addstory": "Add", "substory": "Subtract",
         "mixed": "Add and subtract"}
ARITH = ("add", "sub", "addstory", "substory", "mixed")


def count_for(kind):
    return 10 if kind == "order" else (12 if kind in ("count", "trace", "compare") else 16)


def skill_sheet(rnd, kind, hi, count, label):
    g, probs = practice_block(rnd, kind, hi, count)
    return (label, [(HEADS[kind], g, probs)])


def warmup_sheet(rnd, kind, hi):
    so = story_op(kind)
    small = [p_small_illus(rnd, so if so else rnd.choice(["add", "sub"])) for _ in range(6)]
    g, probs = practice_block(rnd, kind, hi, 8)
    return ("Warm up with pictures", [("Count the pictures", "illus", small), (HEADS[kind], g, probs)])


def story_sheet(rnd, kind, hi, count, label):
    so = story_op(kind)
    probs = []
    if so in (None, "add"):  # lead with a picture-scene when adding is in play
        probs.append(p_scene(rnd, hi))
        count -= 1
    for _ in range(count):
        probs.append(p_story(rnd, so if so else rnd.choice(["add", "sub"]), hi))
    return (label, [("Maths all around us — read and solve", "story", probs)])


def challenge_sheet(rnd, kind, hi, label):
    so = story_op(kind)
    def op():
        return so if so else rnd.choice(["add", "sub"])
    drills = [p_arith(rnd, op(), hi) for _ in range(10)]
    stories = [p_story(rnd, op(), hi) for _ in range(3)]
    return (label, [("Practice", "num", drills), ("Story problems", "story", stories)])


def pick_earlier(wk_ix):
    return [e for e in sorted({max(0, wk_ix - 1), wk_ix // 2}) if e < wk_ix][:2]


def build_day(level, wk_ix, day):
    """Return (subtitle, [ (sheet_label, [ (section_title, grid_class, [probs]) ]) ]) — five sheets."""
    _lid, _lname, _ldesc, weeks = level
    title, kind, hi = weeks[wk_ix]
    rnd = random.Random(100000 + wk_ix * 1000 + day * 37)
    arithmetic = kind in ARITH

    if day == 7:  # revision packet
        sheets = [skill_sheet(rnd, kind, hi, count_for(kind), f"This week: {title}")]
        earlier = pick_earlier(wk_ix)
        for e in earlier:
            et, ek, eh = weeks[e]
            sheets.append(skill_sheet(rnd, ek, eh, count_for(ek), f"Revision: {et}"))
        if arithmetic:
            sheets.append(story_sheet(rnd, kind, hi, 7, "Maths all around us"))
            sheets.append(challenge_sheet(rnd, kind, hi, "Mixed challenge"))
        else:
            sheets.append(skill_sheet(rnd, kind, hi, count_for(kind), "More practice"))
            if earlier:
                et, ek, eh = weeks[earlier[0]]
                sheets.append(skill_sheet(rnd, ek, eh, count_for(ek), f"Revision: {et}"))
        while len(sheets) < 5:
            sheets.append(skill_sheet(rnd, kind, hi, count_for(kind), "Extra practice"))
        return "Revision — this week and earlier weeks", sheets[:5]

    if arithmetic:
        sheets = [
            warmup_sheet(rnd, kind, hi),
            skill_sheet(rnd, kind, hi, 16, "Number practice"),
            skill_sheet(rnd, kind, hi, 16, "More number practice"),
            story_sheet(rnd, kind, hi, 7, "Maths all around us"),
            story_sheet(rnd, kind, hi, 6, "Story challenge"),
        ]
        return title, sheets

    # count / trace / compare / order — five varied practice sheets
    sheets = [skill_sheet(rnd, kind, hi, count_for(kind), f"Practice — set {i+1}") for i in range(5)]
    return title, sheets


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


def _child(cx, base, color, girl):
    hr = 11
    hy = base - 44
    p = [f'<circle cx="{cx}" cy="{hy}" r="{hr}" fill="#ffe0bd" stroke="{INK}" stroke-width="1.6"/>',
         f'<circle cx="{cx-4}" cy="{hy-1}" r="1.5" fill="{INK}"/><circle cx="{cx+4}" cy="{hy-1}" r="1.5" fill="{INK}"/>',
         f'<path d="M{cx-4} {hy+4} Q{cx} {hy+8} {cx+4} {hy+4}" fill="none" stroke="{INK}" stroke-width="1.4" stroke-linecap="round"/>',
         f'<path d="M{cx-hr} {hy-1} A{hr} {hr} 0 0 1 {cx+hr} {hy-1}" fill="{color}"/>']
    if girl:
        p.append(f'<polygon points="{cx},{hy+hr-1} {cx-16},{base} {cx+16},{base}" fill="{color}" stroke="{INK}" stroke-width="1.4" stroke-linejoin="round"/>')
    else:
        p.append(f'<rect x="{cx-11}" y="{hy+hr-1}" width="22" height="22" rx="5" fill="{color}" stroke="{INK}" stroke-width="1.4"/>')
        p.append(f'<line x1="{cx-5}" y1="{base-6}" x2="{cx-5}" y2="{base}" stroke="{INK}" stroke-width="2.6" stroke-linecap="round"/>'
                 f'<line x1="{cx+5}" y1="{base-6}" x2="{cx+5}" y2="{base}" stroke="{INK}" stroke-width="2.6" stroke-linecap="round"/>')
    ay = hy + hr + 5
    p.append(f'<line x1="{cx-10}" y1="{ay}" x2="{cx-22}" y2="{ay+12}" stroke="{INK}" stroke-width="2.2" stroke-linecap="round"/>'
             f'<line x1="{cx+10}" y1="{ay}" x2="{cx+22}" y2="{ay+12}" stroke="{INK}" stroke-width="2.2" stroke-linecap="round"/>')
    return "".join(p)


def _basket(cx, cy):
    return (f'<path d="M{cx-27} {cy} L{cx-21} {cy+26} L{cx+21} {cy+26} L{cx+27} {cy} Z" fill="#e6c79c" stroke="#b98b4e" stroke-width="2" stroke-linejoin="round"/>'
            f'<line x1="{cx-27}" y1="{cy}" x2="{cx+27}" y2="{cy}" stroke="#b98b4e" stroke-width="2.5"/>'
            f'<path d="M{cx-19} {cy} A19 15 0 0 1 {cx+19} {cy}" fill="none" stroke="#b98b4e" stroke-width="2"/>')


def scene(a, ica, b, icb):
    W, base = 320, 118
    p = [_child(46, base, sd.COLORS["blue"][1], girl=False),
         _child(274, base, sd.COLORS["rose"][1], girl=True)]
    for i in range(a):
        p.append(sd.icon(ica, 24 + (i % 3) * 20, 34 + (i // 3) * 19, 8))
    for i in range(b):
        p.append(sd.icon(icb, 252 + (i % 3) * 20, 34 + (i // 3) * 19, 8))
    p.append(_basket(160, 92))
    p.append(f'<path d="M74 52 Q120 64 146 90" fill="none" stroke="{sd.FAINT}" stroke-width="1.6" stroke-dasharray="4 3"/>')
    p.append(f'<path d="M246 52 Q200 64 174 90" fill="none" stroke="{sd.FAINT}" stroke-width="1.6" stroke-dasharray="4 3"/>')
    h = base + 24
    return f'<svg viewBox="0 0 {W} {h}" width="{W}" height="{h}" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="two children putting fruit in a basket" style="max-width:100%">{"".join(p)}</svg>'


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
    if t == "scene":
        art = '<div class="art">' + scene(p["a"], p["ica"], p["b"], p["icb"]) + "</div>"
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
    if t in ("story", "scene"):
        return p["ans"]
    return None


PROGRAM_CSS = """
    .ws { max-width: 820px; margin: 0 auto; padding: 0 22px 60px; }
    .ws-hero { padding: 40px 0 10px; }
    .ws-hero .tag { font-size: 12px; font-weight: 700; letter-spacing: 0.1em; text-transform: uppercase; color: var(--accent); }
    .ws-hero h1 { font-size: clamp(24px, 4vw, 34px); font-weight: 800; letter-spacing: -0.8px; margin: 6px 0 8px; }
    .ws-hero p { color: var(--text2); font-size: 15px; }
    .ws-actions { display: flex; flex-wrap: wrap; gap: 10px; margin-top: 14px; align-items: center; }
    .today { display: flex; gap: 12px; align-items: flex-start; background: rgba(22,163,74,0.07); border: 1px solid rgba(22,163,74,0.22); border-radius: 14px; padding: 16px 18px; margin-top: 14px; }
    .today .ic { font-size: 24px; line-height: 1; }
    .today b { display: block; font-size: 12px; text-transform: uppercase; letter-spacing: 0.08em; color: #15803d; margin-bottom: 3px; }
    .today p { margin: 0; font-size: 15px; color: var(--text); line-height: 1.55; }
    .sheet { margin-top: 26px; }
    .sheet.brk { border-top: 3px dashed var(--border2); padding-top: 22px; }
    .sheet-head { display: flex; align-items: center; gap: 12px; margin-bottom: 8px; flex-wrap: wrap; }
    .sheet-head .sh-num { font-size: 11px; font-weight: 800; letter-spacing: 0.08em; text-transform: uppercase; color: var(--accent); background: rgba(22,163,74,0.10); border-radius: 6px; padding: 3px 8px; }
    .sheet-head .sh-lbl { font-size: 17px; font-weight: 800; color: var(--text); flex: 1; }
    .sheet-head .sh-print { padding: 5px 12px; font-size: 12px; }
    .ws-section { margin-top: 16px; }
    .ws-section h2 { font-size: 15px; font-weight: 700; color: var(--text2); border-bottom: 1px solid var(--border); padding-bottom: 5px; margin-bottom: 11px; }
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
      .prob { break-inside: avoid; }
      .sheet.brk { break-before: page; }
      .answers { break-before: page; }
      .sheet-head { border-bottom: 2px solid #000; padding-bottom: 6px; }
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
    <p class="no-print">{nsheets} sheets today · {count} problems in all. Print all {nsheets} pages, or do one sheet at a time. Grown-ups: the answer key is at the end.</p>
    <div class="ws-actions no-print">
      <button class="btn btn-primary" onclick="window.print()">\U0001f5a8️ Print all {nsheets} sheets</button>
      <a class="btn btn-secondary" href="{lid}.html">All weeks</a>
    </div>
  </section>
  <div class="today"><span class="ic">\U0001f4d6</span><div><b>Today's story</b><p>{intro}</p></div></div>
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
    sub, sheets = build_day(level, wk_ix, day)
    total = 0
    sheet_html, akey_parts = [], []
    for si, (sheet_label, sections) in enumerate(sheets, 1):
        idx = 0
        sec_html, keys = [], []
        for title, gcls, probs in sections:
            cells = []
            for p in probs:
                idx += 1
                total += 1
                cells.append(render_problem(idx, p))
                av = answer_of(p)
                if av is not None:
                    keys.append(f'<span>{idx}) {av}</span>')
            sec_html.append(f'<section class="ws-section"><h2>{title}</h2><div class="grid {gcls}">{"".join(cells)}</div></section>')
        brk = "" if si == 1 else " brk"
        sheet_html.append(
            f'<section class="sheet{brk}"><div class="sheet-head no-print-border"><span class="sh-num">Sheet {si} of {len(sheets)}</span>'
            f'<span class="sh-lbl">{esc(sheet_label)}</span>'
            f'<button class="btn btn-secondary sh-print no-print" onclick="window.print()">\U0001f5a8️ Print</button></div>'
            + "\n".join(sec_html) + "</section>")
        if keys:
            akey_parts.append(f'<div style="margin-bottom:8px"><b style="font-size:12.5px">Sheet {si}: {esc(sheet_label)}</b><div class="akey">{"".join(keys)}</div></div>')
    prev_btn = f'<a class="btn btn-secondary" href="{prev_href}">← Previous</a>' if prev_href else '<span></span>'
    next_btn = f'<a class="btn btn-primary" href="{next_href}">Next →</a>' if next_href else '<span></span>'
    intro = day_intro(random.Random(200000 + wk_ix * 1000 + day))
    page = DAY_PAGE.format(
        css=PROGRAM_CSS, nav=NAV, footer=FOOTER, script=SCRIPT,
        lid=lid, lname=lname, letter=letter, lletter=letter.lower(), day=day,
        sub=esc(sub), count=total, nsheets=len(sheets), sections="\n".join(sheet_html),
        answers="".join(akey_parts), prev=prev_btn, next=next_btn, intro=esc(intro),
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
