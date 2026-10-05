"""Picture problems and story illustrations for the Medium, Advanced and Pro levels.

Every picture here is answer-free (unlike some school_diagrams helpers, which print the
result), uses the same soft palette and icons as the Basic level, and is an inline SVG
with explicit width/height so it never collapses.

pic(kind, rnd) -> {"t": "pic", "svg": ..., "q": "... □ ...", "ans": "..."} or None
story_art(text, rnd) -> svg for a word problem, chosen from the story's own nouns
"""
import math
import re
from fractions import Fraction

import school_diagrams as sd

INK, FAINT = sd.INK, sd.FAINT
C = sd.COLORS
BOX = "□"
FRUIT = ["apple", "orange", "banana", "flower", "star", "balloon", "ball", "cake", "gift"]


def svg(w, h, body, label):
    w, h = int(math.ceil(w)), int(math.ceil(h))
    return (f'<svg viewBox="0 0 {w} {h}" width="{w}" height="{h}" xmlns="http://www.w3.org/2000/svg" '
            f'role="img" aria-label="{label}" style="max-width:100%">{body}</svg>')


def txt(x, y, s, size=13, weight="600", color=INK, anchor="middle"):
    return (f'<text x="{x:.1f}" y="{y:.1f}" text-anchor="{anchor}" font-size="{size}" '
            f'font-weight="{weight}" fill="{color}">{s}</text>')


def P(svg_str, q, ans):
    return {"t": "pic", "svg": svg_str, "q": q, "ans": str(ans)}


def money(c):
    return f"${c // 100}.{c % 100:02d}"


# ------------------------------------------------------------------ extra icons

def icon(kind, cx, cy, s=12):
    if kind == "coin":
        return (f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{s:.1f}" fill="{C["amber"][0]}" stroke="{C["amber"][1]}" stroke-width="2"/>'
                f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{s*0.68:.1f}" fill="none" stroke="{C["amber"][1]}" stroke-width="1.2"/>')
    if kind == "pizza":
        return (f'<path d="M{cx:.1f} {cy-s:.1f} L{cx+s:.1f} {cy+s:.1f} L{cx-s:.1f} {cy+s:.1f} Z" fill="#fde6b8" stroke="#e0a64a" stroke-width="2" stroke-linejoin="round"/>'
                f'<circle cx="{cx:.1f}" cy="{cy+s*0.3:.1f}" r="{s*0.22:.1f}" fill="#f2839a"/>'
                f'<circle cx="{cx-s*0.35:.1f}" cy="{cy+s*0.7:.1f}" r="{s*0.18:.1f}" fill="#f2839a"/>')
    if kind == "pencil":
        return (f'<rect x="{cx-s:.1f}" y="{cy-s*0.25:.1f}" width="{s*1.6:.1f}" height="{s*0.5:.1f}" fill="{C["amber"][0]}" stroke="{C["amber"][1]}" stroke-width="1.6"/>'
                f'<path d="M{cx+s*0.6:.1f} {cy-s*0.25:.1f} L{cx+s:.1f} {cy:.1f} L{cx+s*0.6:.1f} {cy+s*0.25:.1f} Z" fill="#f7d9c4" stroke="{C["amber"][1]}" stroke-width="1.4"/>')
    if kind == "egg":
        return f'<ellipse cx="{cx:.1f}" cy="{cy:.1f}" rx="{s*0.7:.1f}" ry="{s*0.9:.1f}" fill="#fff8ec" stroke="#d9c4a3" stroke-width="2"/>'
    if kind == "cookie":
        dots = "".join(f'<circle cx="{cx+dx*s:.1f}" cy="{cy+dy*s:.1f}" r="{s*0.12:.1f}" fill="#7a5230"/>'
                       for dx, dy in [(-0.35, -0.2), (0.3, -0.3), (0.05, 0.3), (-0.3, 0.35)])
        return f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{s*0.9:.1f}" fill="#f2d3a2" stroke="#c9995a" stroke-width="2"/>' + dots
    if kind == "bottle":
        return (f'<rect x="{cx-s*0.45:.1f}" y="{cy-s*0.5:.1f}" width="{s*0.9:.1f}" height="{s*1.5:.1f}" rx="4" fill="{C["teal"][0]}" stroke="{C["teal"][1]}" stroke-width="2"/>'
                f'<rect x="{cx-s*0.2:.1f}" y="{cy-s:.1f}" width="{s*0.4:.1f}" height="{s*0.5:.1f}" fill="{C["teal"][1]}"/>')
    return sd.icon(kind, cx, cy, s)


THEMES = [
    (r"apple|fruit|orchard", "apple"), (r"orange", "orange"), (r"banana", "banana"),
    (r"pizza|cake|party|recipe", "pizza"), (r"cookie|biscuit|sandwich|roll", "cookie"),
    (r"egg", "egg"), (r"bottle|juice|lemonade|drink|water|jug|litre|\bL\b", "bottle"),
    (r"pen|pencil|school|pupil|class", "pencil"), (r"book|page|library|read", "book"),
    (r"\$|dollar|price|cost|money|save|change|shop|sale|jacket|ticket", "coin"),
    (r"marble|ball|football|game|score|point|team", "ball"), (r"balloon", "balloon"),
    (r"sticker|star", "star"), (r"flower|garden|petal|seed", "flower"),
    (r"gift|present|birthday", "gift"), (r"dog|pet|animal|sheep|goat|farm", "dog"),
    (r"km|metre|train|run|walk|trip|travel|distance|temperature|degree|noon|midnight", "sun"),
]


def theme_of(text):
    for pat, ic in THEMES:
        if re.search(pat, text, re.I):
            return ic
    return "star"


# ------------------------------------------------------------------ building blocks

def kid(cx, base, color, girl):
    hr, hy = 11, base - 44
    p = [f'<circle cx="{cx}" cy="{hy}" r="{hr}" fill="#ffe0bd" stroke="{INK}" stroke-width="1.6"/>',
         f'<circle cx="{cx-4}" cy="{hy-1}" r="1.5" fill="{INK}"/><circle cx="{cx+4}" cy="{hy-1}" r="1.5" fill="{INK}"/>',
         f'<path d="M{cx-4} {hy+4} Q{cx} {hy+8} {cx+4} {hy+4}" fill="none" stroke="{INK}" stroke-width="1.4" stroke-linecap="round"/>',
         f'<path d="M{cx-hr} {hy-1} A{hr} {hr} 0 0 1 {cx+hr} {hy-1}" fill="{color}"/>']
    if girl:
        p.append(f'<polygon points="{cx},{hy+hr-1} {cx-16},{base} {cx+16},{base}" fill="{color}" stroke="{INK}" stroke-width="1.4" stroke-linejoin="round"/>')
    else:
        p.append(f'<rect x="{cx-11}" y="{hy+hr-1}" width="22" height="22" rx="5" fill="{color}" stroke="{INK}" stroke-width="1.4"/>'
                 f'<line x1="{cx-5}" y1="{base-6}" x2="{cx-5}" y2="{base}" stroke="{INK}" stroke-width="2.6" stroke-linecap="round"/>'
                 f'<line x1="{cx+5}" y1="{base-6}" x2="{cx+5}" y2="{base}" stroke="{INK}" stroke-width="2.6" stroke-linecap="round"/>')
    ay = hy + hr + 5
    p.append(f'<line x1="{cx-10}" y1="{ay}" x2="{cx-22}" y2="{ay+12}" stroke="{INK}" stroke-width="2.2" stroke-linecap="round"/>'
             f'<line x1="{cx+10}" y1="{ay}" x2="{cx+22}" y2="{ay+12}" stroke="{INK}" stroke-width="2.2" stroke-linecap="round"/>')
    return "".join(p)


def basket(cx, cy, w=58):
    h = w * 0.42
    return (f'<path d="M{cx-w/2:.1f} {cy:.1f} L{cx-w/2+6:.1f} {cy+h:.1f} L{cx+w/2-6:.1f} {cy+h:.1f} L{cx+w/2:.1f} {cy:.1f} Z" '
            f'fill="#e6c79c" stroke="#b98b4e" stroke-width="2" stroke-linejoin="round"/>'
            f'<line x1="{cx-w/2:.1f}" y1="{cy:.1f}" x2="{cx+w/2:.1f}" y2="{cy:.1f}" stroke="#b98b4e" stroke-width="2.5"/>')


def story_art(text, rnd):
    """Two friends with a basket of things from the story.

    The picture sets the scene but is deliberately not countable (a basket with a few
    items peeking out), so it never disagrees with the numbers in the problem.
    """
    ic = theme_of(text)
    girl_first = rnd.random() < 0.5
    cols = [C["blue"][1], C["rose"][1], C["teal"][1], C["purple"][1]]
    c1, c2 = rnd.sample(cols, 2)
    W, base = 330, 104
    p = [kid(40, base, c1, girl_first), kid(290, base, c2, not girl_first)]
    for dx, dy in [(-22, 0), (0, -10), (22, 0)]:
        p.append(icon(ic, 165 + dx, 58 + dy, 13))
    p.append(basket(165, 62, 96))
    return svg(W, base + 10, "".join(p), "two friends with a basket of things from the story")


def icon_grid(n, ic, per_row, s=12, gap=30, pad=8):
    p = []
    for i in range(n):
        r, c = divmod(i, per_row)
        p.append(icon(ic, pad + s + c * gap, pad + s + r * gap, s))
    rows = (n + per_row - 1) // per_row
    return p, pad * 2 + min(n, per_row) * gap - (gap - 2 * s), pad * 2 + rows * gap - (gap - 2 * s)


# ------------------------------------------------------------------ picture problems

def pic_array(rnd, rows=None, cols=None):
    r, c = rows or rnd.randint(2, 5), cols or rnd.randint(2, 6)
    ic = rnd.choice(FRUIT)
    p, w, h = icon_grid(r * c, ic, c)
    return P(svg(w, h, "".join(p), f"{r} rows of {c}"), f"{r} rows of {c} = {BOX}", r * c)


def pic_groups(rnd, groups=None, each=None):
    g, e = groups or rnd.randint(2, 4), each or rnd.randint(2, 5)
    ic = rnd.choice(["apple", "orange", "cookie", "egg", "ball"])
    p, x = [], 6
    for _ in range(g):
        p.append(basket(x + 40, 62, 74))
        for i in range(e):
            r, c = divmod(i, 3)
            p.append(icon(ic, x + 18 + c * 22, 22 + r * 20, 9))
        x += 92
    return P(svg(x, 96, "".join(p), f"{g} baskets of {e}"), f"{g} groups of {e} = {BOX}", g * e)


def pic_share(rnd, remainder=False):
    g, e = rnd.randint(2, 4), rnd.randint(2, 5)
    r = rnd.randint(1, g - 1) if remainder and g > 1 else 0
    total = g * e + r
    ic = rnd.choice(["apple", "cookie", "orange", "star"])
    p, w, h = icon_grid(total, ic, 8)
    for i in range(g):
        cx = 40 + i * 80
        p.append(f'<ellipse cx="{cx}" cy="{h + 30}" rx="32" ry="11" fill="#fff" stroke="{FAINT}" stroke-width="2"/>')
    W = max(w, 80 * g + 10)
    if remainder:
        return P(svg(W, h + 50, "".join(p), "share between plates"),
                 f"Share {total} between {g} plates: {BOX} each, {BOX} left over", f"{e} r {r}")
    return P(svg(W, h + 50, "".join(p), "share between plates"), f"Share {total} between {g} plates: {BOX} each", e)


def blocks(n, x0=6, y0=8):
    h, t, o = n // 100, n // 10 % 10, n % 10
    p, x = [], x0
    for _ in range(h):
        p.append(f'<rect x="{x}" y="{y0}" width="50" height="50" rx="3" fill="{C["rose"][0]}" stroke="{C["rose"][1]}" stroke-width="1.6"/>')
        for k in range(1, 10):
            p.append(f'<line x1="{x+k*5}" y1="{y0}" x2="{x+k*5}" y2="{y0+50}" stroke="{C["rose"][1]}" stroke-width="0.5"/>'
                     f'<line x1="{x}" y1="{y0+k*5}" x2="{x+50}" y2="{y0+k*5}" stroke="{C["rose"][1]}" stroke-width="0.5"/>')
        x += 58
    for _ in range(t):
        p.append(f'<rect x="{x}" y="{y0}" width="7" height="50" rx="2" fill="{C["amber"][0]}" stroke="{C["amber"][1]}" stroke-width="1.4"/>')
        x += 11
    x += 6 if t else 0
    for i in range(o):
        r, c = divmod(i, 3)
        p.append(f'<rect x="{x + c*10}" y="{y0 + 20 + r*10}" width="7" height="7" rx="1.5" fill="{C["green"][0]}" stroke="{C["green"][1]}" stroke-width="1.2"/>')
    x += 32 if o else 0
    return p, x


def pic_blocks(rnd, big=False):
    n = rnd.randint(101, 349) if big else rnd.randint(12, 99)
    p, w = blocks(n)
    return P(svg(w + 6, 66, "".join(p), "base-ten blocks"), f"The blocks show {BOX}", n)


def pic_blocks_add(rnd, big=False, sub=False):
    if sub:
        a = rnd.randint(130, 349) if big else rnd.randint(25, 89)
        b = rnd.randint(11, a - 10) if not big else rnd.randint(101, a - 20)
        p, w = blocks(a)
        return P(svg(w + 6, 66, "".join(p), "base-ten blocks"), f"Take {b} away from the blocks: {BOX}", a - b)
    a = rnd.randint(101, 249) if big else rnd.randint(12, 59)
    b = rnd.randint(101, 249) if big else rnd.randint(11, 39)
    p1, w1 = blocks(a)
    p2, w2 = blocks(b, x0=w1 + 26)
    plus = txt(w1 + 13, 40, "+", 22, "800")
    return P(svg(w2 + 6, 66, "".join(p1 + [plus] + p2), "base-ten blocks"), f"How many altogether? {BOX}", a + b)


COIN_SET = [(1, "1c", 9), (5, "5c", 11), (10, "10c", 10), (25, "25c", 13), (100, "$1", 15)]


def pic_coins(rnd):
    picks = sorted(rnd.choices(COIN_SET, k=rnd.randint(3, 6)), key=lambda c: -c[0])
    p, x = [], 6
    for val, lab, r in picks:
        if val == 100:
            p.append(f'<rect x="{x}" y="10" width="54" height="30" rx="4" fill="{C["green"][0]}" stroke="{C["green"][1]}" stroke-width="2"/>')
            p.append(txt(x + 27, 30, lab, 13, "800"))
            x += 62
        else:
            p.append(f'<circle cx="{x + r}" cy="25" r="{r}" fill="{C["amber"][0]}" stroke="{C["amber"][1]}" stroke-width="2"/>')
            p.append(txt(x + r, 29, lab, 9 if r < 12 else 10, "800"))
            x += 2 * r + 8
    total = sum(v for v, _l, _r in picks)
    return P(svg(x + 4, 50, "".join(p), "coins"), f"How much money? {BOX}", money(total))


def pic_prices(rnd):
    items = rnd.sample([("apple", "apple"), ("book", "book"), ("ball", "ball"), ("cookie", "cookie"),
                        ("bottle", "drink"), ("pencil", "pencil")], 2)
    prices = [rnd.randint(1, 16) * 25 for _ in items]
    p, x = [], 8
    for (ic, _name), pr in zip(items, prices):
        p.append(icon(ic, x + 22, 30, 16))
        p.append(f'<rect x="{x}" y="56" width="58" height="22" rx="5" fill="#fff" stroke="{FAINT}" stroke-width="1.6"/>')
        p.append(txt(x + 29, 72, money(pr), 12.5, "800"))
        x += 90
    return P(svg(x, 86, "".join(p), "price tags"), f"Buy both: {BOX}", money(sum(prices)))


def clock_face(h, m, cx=60, cy=60, r=52):
    p = [f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="#fff" stroke="{INK}" stroke-width="2.4"/>']
    for n in range(1, 13):
        a = math.radians(-90 + n * 30)
        p.append(txt(cx + (r - 13) * math.cos(a), cy + (r - 13) * math.sin(a) + 4, n, 10.5, "700"))
    ma = math.radians(-90 + m * 6)
    ha = math.radians(-90 + (h % 12) * 30 + m * 0.5)
    p.append(f'<line x1="{cx}" y1="{cy}" x2="{cx + (r-12)*math.cos(ma):.1f}" y2="{cy + (r-12)*math.sin(ma):.1f}" stroke="{C["blue"][1]}" stroke-width="2.6" stroke-linecap="round"/>')
    p.append(f'<line x1="{cx}" y1="{cy}" x2="{cx + (r-26)*math.cos(ha):.1f}" y2="{cy + (r-26)*math.sin(ha):.1f}" stroke="{INK}" stroke-width="3.6" stroke-linecap="round"/>')
    p.append(f'<circle cx="{cx}" cy="{cy}" r="3.5" fill="{INK}"/>')
    return p


def pic_clock(rnd):
    h, m = rnd.randint(1, 12), rnd.choice(range(0, 60, 5))
    return P(svg(120, 120, "".join(clock_face(h, m)), "clock"), f"What time is it? {BOX}", f"{h}:{m:02d}")


def pic_elapsed(rnd):
    h, m = rnd.randint(1, 10), rnd.choice(range(0, 60, 5))
    d = rnd.choice([10, 15, 20, 25, 30, 35, 40, 45, 50])
    t = h * 60 + m + d
    h2, m2 = (t // 60 - 1) % 12 + 1, t % 60
    p = clock_face(h, m) + [txt(150, 64, "→", 22, "800")] + clock_face(h2, m2, cx=240)
    return P(svg(300, 120, "".join(p), "two clocks"), f"How many minutes passed? {BOX}", d)


def pie(n, d, cx, cy, r, color="green"):
    fillc = C[color][0]
    if d == 1:
        return [f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{fillc if n else "#fff"}" stroke="{INK}" stroke-width="1.8"/>']
    p = []
    for i in range(d):
        a0, a1 = math.radians(-90 + i * 360 / d), math.radians(-90 + (i + 1) * 360 / d)
        p.append(f'<path d="M{cx} {cy} L{cx + r*math.cos(a0):.1f} {cy + r*math.sin(a0):.1f} A{r} {r} 0 0 1 '
                 f'{cx + r*math.cos(a1):.1f} {cy + r*math.sin(a1):.1f} Z" fill="{fillc if i < n else "#fff"}" stroke="{INK}" stroke-width="1.4"/>')
    return p


def bar(n, d, x, y, w=220, h=34, color="green"):
    cw = w / d
    p = [f'<rect x="{x + i*cw:.1f}" y="{y}" width="{cw:.1f}" height="{h}" fill="{C[color][0] if i < n else "#fff"}" stroke="{INK}" stroke-width="1.3"/>' for i in range(d)]
    p.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="6" fill="none" stroke="{INK}" stroke-width="1.8"/>')
    return p


def pic_fraction(rnd):
    d = rnd.choice([2, 3, 4, 5, 6, 8])
    n = rnd.randint(1, d - 1)
    if rnd.random() < 0.5:
        return P(svg(110, 110, "".join(pie(n, d, 55, 55, 48, rnd.choice(["green", "amber", "rose"]))), "pizza"),
                 f"What fraction is shaded? {BOX}", f"{n}/{d}")
    return P(svg(236, 46, "".join(bar(n, d, 8, 6)), "bar"), f"What fraction is shaded? {BOX}", f"{n}/{d}")


def pic_frac_cmp(rnd):
    d1, d2 = rnd.sample([2, 3, 4, 5, 6, 8], 2)
    n1, n2 = rnd.randint(1, d1 - 1), rnd.randint(1, d2 - 1)
    f1, f2 = Fraction(n1, d1), Fraction(n2, d2)
    p = bar(n1, d1, 8, 6, color="blue") + bar(n2, d2, 8, 50, color="amber")
    sign = ">" if f1 > f2 else ("<" if f1 < f2 else "=")
    return P(svg(236, 90, "".join(p), "two bars"), f"{n1}/{d1} {BOX} {n2}/{d2}   (>, < or =)", sign)


def pic_frac_add(rnd):
    d = rnd.choice([4, 5, 6, 8])
    a, b = rnd.randint(1, d // 2), rnd.randint(1, d // 2)
    p = pie(a, d, 50, 50, 42, "blue") + [txt(110, 56, "+", 22, "800")] + pie(b, d, 170, 50, 42, "amber")
    s = Fraction(a + b, d)
    return P(svg(220, 100, "".join(p), "two pizzas"), f"{a}/{d} + {b}/{d} = {BOX}", frac_str(s))


def frac_str(f):
    if f.denominator == 1:
        return str(f.numerator)
    w, r = divmod(f.numerator, f.denominator)
    return f"{w} {r}/{f.denominator}" if w else f"{f.numerator}/{f.denominator}"


def pic_frac_of(rnd):
    d = rnd.choice([2, 3, 4, 5])
    per = rnd.randint(2, 4)
    n = rnd.randint(1, d - 1)
    total = d * per
    ic = rnd.choice(["apple", "star", "cookie", "balloon"])
    p, w, h = icon_grid(total, ic, per)
    return P(svg(w, h, "".join(p), f"{total} things"), f"{n}/{d} of these {total} = {BOX}", n * per)


def pic_mixed(rnd):
    d = rnd.choice([2, 3, 4])
    w, n = rnd.randint(1, 2), rnd.randint(1, d - 1)
    p = []
    for i in range(w):
        p += pie(d, d, 46 + i * 96, 48, 40)
    p += pie(n, d, 46 + w * 96, 48, 40)
    return P(svg(96 * (w + 1) + 4, 96, "".join(p), "pizzas"), f"How many pizzas? {BOX}", f"{w} {n}/{d}")


def grid100(k, color="green"):
    p, cell, gap, pad = [], 14, 2, 6
    for i in range(100):
        r, c = divmod(i, 10)
        p.append(f'<rect x="{pad + c*(cell+gap)}" y="{pad + r*(cell+gap)}" width="{cell}" height="{cell}" rx="2" '
                 f'fill="{C[color][0] if i < k else sd.EMPTY}" stroke="{sd.EMPTY_STROKE}" stroke-width="1"/>')
    size = pad * 2 + 10 * cell + 9 * gap
    return svg(size, size, "".join(p), "hundred grid")


def pic_hundred(rnd, mode):
    k = rnd.randint(5, 95)
    if mode == "pct":
        return P(grid100(k), f"What percent is shaded? {BOX}%", k)
    s = f"0.{k:02d}".rstrip("0") if k % 10 else f"0.{k // 10}"
    return P(grid100(k, "blue"), f"Write the shaded part as a decimal: {BOX}", s)


def rect_grid(w, h, cell=18, show_dims=True):
    p = []
    for r in range(h):
        for c in range(w):
            p.append(f'<rect x="{8 + c*cell}" y="{8 + r*cell}" width="{cell}" height="{cell}" fill="{C["teal"][0]}" stroke="{C["teal"][1]}" stroke-width="1"/>')
    return p, 16 + w * cell, 16 + h * cell


def pic_rect(rnd, mode):
    w, h = rnd.randint(3, 9), rnd.randint(2, 6)
    p, W, H = rect_grid(w, h)
    if mode == "area":
        return P(svg(W, H, "".join(p), "rectangle on a grid"), f"Area = {BOX} squares", w * h)
    return P(svg(W, H, "".join(p), "rectangle on a grid"), f"Perimeter = {BOX} units (each square is 1 unit)", 2 * (w + h))


def pic_triangle(rnd):
    b, h = rnd.choice([4, 6, 8]), rnd.randint(2, 6)
    cell = 18
    p, W, H = rect_grid(b, h, cell)
    p = [x.replace(C["teal"][0], "#fff") for x in p]
    p.append(f'<polygon points="8,{8 + h*cell} {8 + b*cell},{8 + h*cell} {8 + b*cell},8" fill="{C["rose"][0]}" '
             f'fill-opacity="0.85" stroke="{C["rose"][1]}" stroke-width="2"/>')
    return P(svg(W, H, "".join(p), "triangle on a grid"), f"Area of the triangle = {BOX} squares", b * h // 2)


def pic_cuboid(rnd):
    l, w, h = rnd.randint(2, 4), rnd.randint(2, 3), rnd.randint(2, 3)
    s, dx, dy = 22, 11, 8
    p = []

    def cube(x, y):
        return (f'<polygon points="{x},{y} {x+s},{y} {x+s},{y+s} {x},{y+s}" fill="{C["blue"][0]}" stroke="{C["blue"][1]}" stroke-width="1.2"/>'
                f'<polygon points="{x},{y} {x+dx},{y-dy} {x+s+dx},{y-dy} {x+s},{y}" fill="#e8f1fd" stroke="{C["blue"][1]}" stroke-width="1.2"/>'
                f'<polygon points="{x+s},{y} {x+s+dx},{y-dy} {x+s+dx},{y+s-dy} {x+s},{y+s}" fill="#bcd6f8" stroke="{C["blue"][1]}" stroke-width="1.2"/>')
    for z in range(w - 1, -1, -1):
        for yy in range(h):
            for xx in range(l):
                p.append(cube(10 + xx * s + z * dx, 10 + w * dy + (h - 1 - yy) * s - z * dy))
    W, H = 20 + l * s + w * dx + 4, 20 + h * s + w * dy
    return P(svg(W, H, "".join(p), "cuboid made of cubes"), f"How many cubes? {BOX}", l * w * h)


def pic_bars(rnd, which):
    names = rnd.sample(["Mon", "Tue", "Wed", "Thu", "Fri"], 4) if rnd.random() < 0.5 else ["Ana", "Leo", "Mia", "Kai"]
    vals = [rnd.randint(2, 12) for _ in range(4)]
    while which == "mean" and sum(vals) % 4:
        vals[rnd.randrange(4)] += 1
    p, unit = [], 12
    top = 12 * unit + 14
    for i, (nm, v) in enumerate(zip(names, vals)):
        x = 30 + i * 52
        p.append(f'<rect x="{x}" y="{top - v*unit}" width="34" height="{v*unit}" rx="4" fill="{C["purple"][0]}" stroke="{C["purple"][1]}" stroke-width="1.8"/>')
        p.append(txt(x + 17, top - v * unit - 5, v, 11, "800"))
        p.append(txt(x + 17, top + 15, nm, 11))
    p.append(f'<line x1="22" y1="{top}" x2="{30 + 4*52}" y2="{top}" stroke="{INK}" stroke-width="1.6"/>')
    lab = {"mean": f"Mean of the bars = {BOX}", "range": f"Range (biggest - smallest) = {BOX}",
           "total": f"Total of all bars = {BOX}"}[which]
    ans = {"mean": sum(vals) // 4, "range": max(vals) - min(vals), "total": sum(vals)}[which]
    return P(svg(30 + 4 * 52 + 6, top + 24, "".join(p), "bar chart"), lab, ans)


def number_line(lo, hi, step_px, marks=None, labels_every=1):
    p = [f'<line x1="12" y1="40" x2="{12 + (hi - lo) * step_px}" y2="40" stroke="{INK}" stroke-width="2"/>']
    for v in range(lo, hi + 1):
        x = 12 + (v - lo) * step_px
        p.append(f'<line x1="{x}" y1="34" x2="{x}" y2="46" stroke="{INK}" stroke-width="1.4"/>')
        if (v - lo) % labels_every == 0:
            p.append(txt(x, 62, v, 10.5))
    return p, 24 + (hi - lo) * step_px


def pic_jump(rnd):
    start = rnd.randint(-8, 8)
    move = rnd.choice([-1, 1]) * rnd.randint(3, 9)
    end = start + move
    lo, hi = -10, 10
    p, W = number_line(lo, hi, 15)
    x0 = 12 + (start - lo) * 15
    p.append(f'<circle cx="{x0}" cy="40" r="6" fill="{C["rose"][1]}"/>')
    word = "right" if move > 0 else "left"
    return P(svg(W, 70, "".join(p), "number line"), f"Start at {start} and jump {abs(move)} to the {word}: {BOX}", end)


def pic_thermo(rnd):
    t = rnd.randint(-10, 15)
    drop = rnd.randint(3, 12)
    p = [f'<rect x="40" y="10" width="20" height="160" rx="10" fill="#fff" stroke="{INK}" stroke-width="2"/>']
    for v in range(-10, 21, 5):
        y = 150 - (v + 10) * 4.5
        p.append(f'<line x1="60" y1="{y}" x2="68" y2="{y}" stroke="{INK}" stroke-width="1.4"/>' + txt(84, y + 4, v, 10.5))
    y = 150 - (t + 10) * 4.5
    p.append(f'<rect x="45" y="{y}" width="10" height="{165 - y}" rx="5" fill="#f2839a"/>')
    p.append(f'<circle cx="50" cy="176" r="14" fill="#f2839a" stroke="{INK}" stroke-width="2"/>')
    return P(svg(110, 196, "".join(p), "thermometer"), f"It is {t} degrees. It gets {drop} degrees colder: {BOX}", t - drop)


def pic_balance(rnd, two_step=False):
    x = rnd.randint(2, 9)
    a = rnd.randint(1, 6)
    k = rnd.randint(2, 3) if two_step else 1
    total = k * x + a
    p = [f'<polygon points="160,150 145,175 175,175" fill="{FAINT}"/>',
         f'<line x1="40" y1="100" x2="280" y2="100" stroke="{INK}" stroke-width="3" stroke-linecap="round"/>',
         f'<line x1="160" y1="100" x2="160" y2="152" stroke="{INK}" stroke-width="3"/>',
         f'<path d="M30 100 Q80 132 130 100" fill="none" stroke="{INK}" stroke-width="2"/>',
         f'<path d="M190 100 Q240 132 290 100" fill="none" stroke="{INK}" stroke-width="2"/>']
    for i in range(k):
        p.append(f'<rect x="{38 + i*30}" y="{60 - (0)}" width="26" height="26" rx="4" fill="{C["purple"][0]}" stroke="{C["purple"][1]}" stroke-width="2"/>'
                 + txt(51 + i * 30, 78, "x", 13, "800"))
    for i in range(a):
        r, c = divmod(i, 3)
        p.append(f'<circle cx="{40 + k*30 + 10 + c*15}" cy="{79 - r*15}" r="6.5" fill="{C["amber"][0]}" stroke="{C["amber"][1]}" stroke-width="1.6"/>')
    for i in range(total):
        r, c = divmod(i, 6)
        p.append(f'<circle cx="{198 + c*15}" cy="{89 - r*15}" r="6.5" fill="{C["amber"][0]}" stroke="{C["amber"][1]}" stroke-width="1.6"/>')
    eq = f"{k}x + {a} = {total}" if k > 1 else f"x + {a} = {total}"
    return P(svg(320, 185, "".join(p), "balance scale"), f"The scale balances: {eq}, so x = {BOX}", x)


def pic_ratio(rnd, share=False):
    a, b = rnd.randint(1, 3), rnd.randint(1, 3)
    reps = rnd.randint(2, 3)
    ic1, ic2 = rnd.sample(["apple", "orange", "banana", "star", "flower"], 2)
    seq = ([ic1] * a + [ic2] * b) * reps
    p = [icon(ic, 18 + i * 30, 22, 11) for i, ic in enumerate(seq)]
    W = 18 + len(seq) * 30
    if share:
        return P(svg(W, 44, "".join(p), "pattern of fruit"), f"How many of the first fruit in this row? {BOX}", a * reps)
    from math import gcd
    g = gcd(a * reps, b * reps)
    return P(svg(W, 44, "".join(p), "pattern of fruit"), f"Ratio first fruit : second fruit (simplest) = {BOX}",
             f"{a * reps // g}:{b * reps // g}")


def pic_ruler(rnd):
    n = rnd.randint(3, 14)
    p = [f'<rect x="10" y="40" width="{15*30+10}" height="26" rx="3" fill="#fdf3d7" stroke="#d6b45c" stroke-width="1.6"/>']
    for v in range(0, 16):
        x = 15 + v * 30
        p.append(f'<line x1="{x}" y1="40" x2="{x}" y2="52" stroke="{INK}" stroke-width="1.3"/>' + txt(x, 63, v, 9.5))
    p.append(f'<rect x="15" y="16" width="{n*30}" height="14" rx="5" fill="{C["amber"][0]}" stroke="{C["amber"][1]}" stroke-width="2"/>'
             f'<path d="M{15 + n*30} 16 l12 7 l-12 7 z" fill="#f7d9c4" stroke="{C["amber"][1]}" stroke-width="1.6"/>')
    return P(svg(15 * 30 + 30, 74, "".join(p), "pencil on a ruler"), f"How long is the pencil? {BOX} cm", n)


def pic_area_model(rnd, big=False):
    a = rnd.randint(12, 49) if not big else rnd.randint(102, 249)
    b = rnd.randint(3, 9)
    parts = [int(d) * 10 ** i for i, d in enumerate(reversed(str(a))) if d != "0"][::-1]
    total_w = 280
    p, x = [], 30
    for pt in parts:
        w = max(50, total_w * pt / a)
        p.append(f'<rect x="{x:.1f}" y="20" width="{w:.1f}" height="70" fill="{C["green"][0]}" stroke="{C["green"][1]}" stroke-width="2"/>'
                 + txt(x + w / 2, 14, pt, 12, "800") + txt(x + w / 2, 60, f"{pt} x {b}", 12))
        x += w
    p.append(txt(16, 60, b, 13, "800"))
    return P(svg(x + 10, 100, "".join(p), "area model"), f"{a} x {b} = {BOX}", a * b)


def pic_square(rnd):
    n = rnd.randint(2, 7)
    p, w, h = icon_grid(n * n, rnd.choice(["star", "flower", "ball"]), n, s=9, gap=22)
    return P(svg(w, h, "".join(p), "square of dots"), f"{n} squared ({n} x {n}) = {BOX}", n * n)


def pic_growing(rnd):
    start, step = rnd.randint(1, 3), rnd.randint(1, 3)
    p, x = [], 8
    for k in range(3):
        n = start + step * k
        for i in range(n):
            p.append(f'<rect x="{x}" y="{70 - i*14}" width="12" height="12" rx="2" fill="{C["teal"][0]}" stroke="{C["teal"][1]}" stroke-width="1.4"/>')
        p.append(txt(x + 6, 98, f"#{k + 1}", 10))
        x += 40
    p.append(f'<rect x="{x}" y="40" width="30" height="42" rx="6" fill="none" stroke="{FAINT}" stroke-width="2" stroke-dasharray="4 3"/>' + txt(x + 15, 66, "?", 16, "800", FAINT))
    return P(svg(x + 40, 104, "".join(p), "growing pattern"), f"How many squares in pattern #4? {BOX}", start + step * 3)


def pic_round(rnd):
    lo = rnd.randint(1, 9) * 100
    n = lo + rnd.choice([i for i in range(5, 100, 5) if i != 50])
    p, W = number_line(0, 10, 32)
    p = [x for x in p if "<text" not in x]
    p += [txt(12, 62, lo, 10.5), txt(12 + 5 * 32, 62, lo + 50, 10.5), txt(12 + 10 * 32, 62, lo + 100, 10.5)]
    xn = 12 + (n - lo) / 10 * 32
    p.append(f'<circle cx="{xn:.1f}" cy="40" r="6" fill="{C["rose"][1]}"/>' + txt(xn, 26, n, 11, "800"))
    ans = lo + 100 if n - lo > 50 else lo
    return P(svg(W, 70, "".join(p), "number line"), f"{n} rounded to the nearest hundred = {BOX}", ans)


def pic_skip(rnd):
    step = rnd.choice([2, 5, 10])
    g = rnd.randint(3, 6)
    ic = {2: "cookie", 5: "star", 10: "coin"}[step]
    p, x = [], 6
    for _ in range(g):
        for i in range(step):
            r, c = divmod(i, 5)
            p.append(icon(ic, x + 10 + c * 15, 14 + r * 16, 6.5))
        p.append(f'<rect x="{x}" y="4" width="{min(step, 5)*15 + 6}" height="{16 * ((step + 4)//5) + 6}" rx="6" fill="none" stroke="{FAINT}" stroke-width="1.4"/>')
        x += min(step, 5) * 15 + 16
    return P(svg(x, 16 * ((step + 4) // 5) + 18, "".join(p), "groups"), f"Count in {step}s: how many? {BOX}", g * step)


def pic_factors(rnd):
    r, c = rnd.choice([(2, 6), (3, 4), (2, 8), (3, 6), (4, 5), (2, 9), (3, 5)])
    out = pic_array(rnd, r, c)
    out["q"] = f"{r * c} = {r} x {BOX}"
    out["ans"] = str(c)
    return out


def pic_bodmas(rnd):
    r, c, extra = rnd.randint(2, 4), rnd.randint(2, 5), rnd.randint(1, 4)
    ic = rnd.choice(["apple", "star", "cookie"])
    p, w, h = icon_grid(r * c, ic, c)
    for i in range(extra):
        p.append(icon(ic, w + 24 + i * 28, 20, 12))
    p.append(txt(w + 10, 26, "+", 18, "800"))
    return P(svg(w + 28 + extra * 28, max(h, 44), "".join(p), "array plus extras"),
             f"{r} x {c} + {extra} = {BOX}", r * c + extra)


def pic_decimal_strip(rnd):
    t = rnd.randint(1, 9)
    p = bar(t, 10, 8, 8, 260, 34, "blue")
    return P(svg(276, 50, "".join(p), "tenths strip"), f"Shaded part as a decimal: {BOX}", f"0.{t}")


PICS = {
    "skip": pic_skip, "pv2": lambda r: pic_blocks(r), "pv3": lambda r: pic_blocks(r, True),
    "cmp100": lambda r: pic_blocks(r), "cmp1000": lambda r: pic_blocks(r, True),
    "addtens": lambda r: pic_blocks_add(r), "add_nc": lambda r: pic_blocks_add(r), "add_c": lambda r: pic_blocks_add(r),
    "sub_nb": lambda r: pic_blocks_add(r, sub=True), "sub_b": lambda r: pic_blocks_add(r, sub=True),
    "mix2": lambda r: pic_blocks_add(r, sub=r.random() < 0.5), "add3": lambda r: pic_blocks_add(r, True),
    "sub3": lambda r: pic_blocks_add(r, True, True), "dbl": lambda r: pic_array(r, 2, None),
    "t2510": lambda r: pic_groups(r, None, r.choice([2, 5])), "t34": lambda r: pic_array(r, r.choice([3, 4]), None),
    "tmix": lambda r: pic_groups(r), "coins": pic_coins, "money": pic_prices, "time": pic_clock,
    "measure": pic_ruler, "t67": lambda r: pic_array(r, r.choice([3, 4]), r.choice([6, 7])),
    "t89": lambda r: pic_array(r, r.choice([2, 3]), r.choice([8, 9])), "t12": lambda r: pic_array(r),
    "mul21": lambda r: pic_area_model(r), "mul31": lambda r: pic_area_model(r, True), "mul22": lambda r: pic_area_model(r),
    "div": lambda r: pic_share(r), "divr": lambda r: pic_share(r, True), "longdiv": lambda r: pic_share(r),
    "ms_md": lambda r: pic_groups(r), "fracname": pic_fraction, "fracof": pic_frac_of, "fracequiv": pic_fraction,
    "fraccmp": pic_frac_cmp, "fracadd": pic_frac_add, "fracsub": pic_fraction, "mixednum": pic_mixed,
    "ms_as": lambda r: pic_blocks_add(r, True), "areaper": lambda r: pic_rect(r, r.choice(["area", "per"])),
    "factors": pic_factors, "round": pic_round, "pattern": pic_growing, "elapsed": pic_elapsed,
    "decpv": lambda r: pic_hundred(r, "dec"), "decadd": pic_decimal_strip, "decsub": lambda r: pic_hundred(r, "dec"),
    "decmul": pic_decimal_strip, "pow10": lambda r: pic_hundred(r, "dec"), "fracdec": lambda r: pic_hundred(r, "dec"),
    "fracunlike": pic_frac_cmp, "fracmul": pic_frac_of, "fracdiv": lambda r: pic_share(r), "pct": lambda r: pic_hundred(r, "pct"),
    "pctconv": lambda r: pic_hundred(r, "pct"), "ratiosimp": lambda r: pic_ratio(r), "ratioshare": lambda r: pic_ratio(r, True),
    "rate": pic_prices, "bodmas": pic_bodmas, "neg": lambda r: (pic_jump if r.random() < 0.5 else pic_thermo)(r),
    "evalx": lambda r: pic_balance(r), "eq1": lambda r: pic_balance(r), "eq2": lambda r: pic_balance(r, True),
    "pow": pic_square, "hcflcm": pic_factors, "area2": lambda r: (pic_triangle if r.random() < 0.5 else (lambda q: pic_rect(q, "area")))(r),
    "volume": pic_cuboid, "stats": lambda r: pic_bars(r, r.choice(["mean", "range", "total"])),
}


def pic(kind, rnd):
    fn = PICS.get(kind)
    return fn(rnd) if fn else None
