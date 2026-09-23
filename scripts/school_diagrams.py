#!/usr/bin/env python3
"""Calm, kid-friendly SVG diagrams for School lessons.

Design rules (gentle on children's eyes):
  - Soft pastel fills with muted strokes; slate ink for text, never pure black.
  - Small, capped size (the page caps figures at ~420px) — no full-bleed graphics.
  - Rounded corners and line caps, generous spacing, one clear idea per figure.
  - Theme-agnostic: works on the light School pages; colours are soft on white.

A lesson section carries `diagram: {kind, caption?, ...params}` (or `diagrams: [...]`).
`render(spec)` returns an <svg> string; build_school wraps it in <figure>.
"""
import html
import math

esc = html.escape

INK = "#475569"          # slate-600 — text and outlines
FAINT = "#94a3b8"        # slate-400 — secondary text
EMPTY = "#eef2f7"        # empty cells
EMPTY_STROKE = "#cbd5e1"

# soft (fill, stroke) pairs
COLORS = {
    "green":  ("#cdeede", "#34c77b"),
    "blue":   ("#d3e6fd", "#5aa2f0"),
    "amber":  ("#fdeabf", "#efb44e"),
    "rose":   ("#fbd7de", "#f2839a"),
    "purple": ("#e4defb", "#9d8ef0"),
    "teal":   ("#cdeeea", "#3bb6a6"),
}


def _svg(w, h, body, label):
    return (f'<svg viewBox="0 0 {w} {h}" role="img" aria-label="{esc(label)}" '
            f'xmlns="http://www.w3.org/2000/svg">{body}</svg>')


def _arrow(x1, y1, x2, y2, color, w=2.4):
    ang = math.atan2(y2 - y1, x2 - x1)
    hl = 9
    bx, by = x2 - hl * math.cos(ang), y2 - hl * math.sin(ang)
    lx, ly = x2 - hl * math.cos(ang - 0.5), y2 - hl * math.sin(ang - 0.5)
    rx, ry = x2 - hl * math.cos(ang + 0.5), y2 - hl * math.sin(ang + 0.5)
    return (f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{bx:.1f}" y2="{by:.1f}" '
            f'stroke="{color}" stroke-width="{w}" stroke-linecap="round"/>'
            f'<polygon points="{x2:.1f},{y2:.1f} {lx:.1f},{ly:.1f} {rx:.1f},{ry:.1f}" fill="{color}"/>')


def _text(x, y, s, size=13, color=INK, anchor="middle", weight="500"):
    return (f'<text x="{x:.1f}" y="{y:.1f}" text-anchor="{anchor}" font-size="{size}" '
            f'font-weight="{weight}" fill="{color}">{esc(str(s))}</text>')


# ---------------------------------------------------------------- maths

def fraction_circle(filled, parts, color="green", **_):
    cx, cy, r = 82, 82, 62
    fillc, strokec = COLORS[color]
    segs = []
    if parts <= 1:
        segs.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{fillc if filled >= 1 else "#fff"}" '
                    f'stroke="{INK}" stroke-width="2"/>')
    else:
        for i in range(parts):
            a0 = math.radians(-90 + i * 360 / parts)
            a1 = math.radians(-90 + (i + 1) * 360 / parts)
            x0, y0 = cx + r * math.cos(a0), cy + r * math.sin(a0)
            x1, y1 = cx + r * math.cos(a1), cy + r * math.sin(a1)
            fill = fillc if i < filled else "#ffffff"
            segs.append(f'<path d="M{cx} {cy} L{x0:.1f} {y0:.1f} A{r} {r} 0 0 1 {x1:.1f} {y1:.1f} Z" '
                        f'fill="{fill}" stroke="{INK}" stroke-width="1.5"/>')
    segs.append(_text(cx, 168, f"{filled}/{parts}", 15, INK, weight="700"))
    return _svg(164, 180, "".join(segs), f"{filled} of {parts} shaded")


def fraction_bar(filled, parts, color="green", **_):
    fillc, strokec = COLORS[color]
    w, h, pad, top = 260, 46, 12, 12
    cellw = w / parts
    cells = []
    for i in range(parts):
        x = pad + i * cellw
        fill = fillc if i < filled else "#ffffff"
        cells.append(f'<rect x="{x:.1f}" y="{top}" width="{cellw:.1f}" height="{h}" '
                     f'fill="{fill}" stroke="{INK}" stroke-width="1.3"/>')
    cells.append(f'<rect x="{pad}" y="{top}" width="{w}" height="{h}" rx="9" fill="none" '
                 f'stroke="{INK}" stroke-width="1.9"/>')
    cells.append(_text(pad + w / 2, top + h + 22, f"{filled}/{parts}", 15, INK, weight="700"))
    return _svg(284, 92, "".join(cells), f"{filled} of {parts} shaded")


def hundred_grid(percent, color="green", **_):
    fillc, _s = COLORS[color]
    n = round(percent)
    cell, gap, pad = 16, 3, 10
    cells, idx = [], 0
    for row in range(10):
        for col in range(10):
            x, y = pad + col * (cell + gap), pad + row * (cell + gap)
            fill = fillc if idx < n else EMPTY
            cells.append(f'<rect x="{x}" y="{y}" width="{cell}" height="{cell}" rx="3" '
                         f'fill="{fill}" stroke="{EMPTY_STROKE}" stroke-width="1"/>')
            idx += 1
    size = pad * 2 + 10 * cell + 9 * gap
    cells.append(_text(size / 2, size + 20, f"{n} out of 100  ({n}%)", 14, INK, weight="700"))
    return _svg(size, size + 30, "".join(cells), f"{n} of 100 shaded")


def number_line(start=0, end=10, mark=None, color="blue", **_):
    fillc, strokec = COLORS[color]
    pad, w = 24, 300
    span = end - start
    y = 44
    step = (w - 2 * pad) / span
    body = [f'<line x1="{pad}" y1="{y}" x2="{w - pad}" y2="{y}" stroke="{INK}" stroke-width="2" stroke-linecap="round"/>']
    for i in range(span + 1):
        x = pad + i * step
        body.append(f'<line x1="{x:.1f}" y1="{y - 6}" x2="{x:.1f}" y2="{y + 6}" stroke="{INK}" stroke-width="1.6"/>')
        body.append(_text(x, y + 24, start + i, 13, INK))
    if mark is not None:
        mx = pad + (mark - start) * step
        body.append(f'<circle cx="{mx:.1f}" cy="{y}" r="8" fill="{fillc}" stroke="{strokec}" stroke-width="2.5"/>')
    return _svg(w, 80, "".join(body), f"number line {start} to {end}")


def counting(n, color="amber", **_):
    fillc, strokec = COLORS[color]
    per_row = 5
    r, gap, pad = 16, 14, 16
    body = []
    for i in range(n):
        row, col = i // per_row, i % per_row
        cx = pad + r + col * (2 * r + gap)
        cy = pad + r + row * (2 * r + gap)
        body.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{fillc}" stroke="{strokec}" stroke-width="2"/>')
    rows = (n + per_row - 1) // per_row
    w = pad * 2 + min(n, per_row) * (2 * r + gap) - gap
    h = pad * 2 + rows * (2 * r + gap) - gap + 26
    body.append(_text(w / 2, h - 6, f"{n}", 17, INK, weight="700"))
    return _svg(max(w, 90), h, "".join(body), f"{n} dots")


# ---------------------------------------------------------------- shapes

def shapes_row(shapes=None, **_):
    shapes = shapes or ["circle", "square", "triangle"]
    palette = ["green", "blue", "amber", "rose", "purple"]
    cellw, top = 92, 16
    size = 56
    body = []
    for i, name in enumerate(shapes):
        fillc, strokec = COLORS[palette[i % len(palette)]]
        cx = i * cellw + cellw / 2
        cy = top + size / 2
        if name == "circle":
            body.append(f'<circle cx="{cx}" cy="{cy}" r="{size/2}" fill="{fillc}" stroke="{strokec}" stroke-width="2.5"/>')
        elif name == "square":
            body.append(f'<rect x="{cx-size/2}" y="{cy-size/2}" width="{size}" height="{size}" rx="8" fill="{fillc}" stroke="{strokec}" stroke-width="2.5"/>')
        elif name == "triangle":
            body.append(f'<polygon points="{cx},{cy-size/2} {cx+size/2},{cy+size/2} {cx-size/2},{cy+size/2}" fill="{fillc}" stroke="{strokec}" stroke-width="2.5" stroke-linejoin="round"/>')
        elif name == "rectangle":
            body.append(f'<rect x="{cx-size/2}" y="{cy-size/3}" width="{size}" height="{size*2/3}" rx="8" fill="{fillc}" stroke="{strokec}" stroke-width="2.5"/>')
        elif name == "star":
            pts = []
            for k in range(10):
                rr = size/2 if k % 2 == 0 else size/4
                a = math.radians(-90 + k * 36)
                pts.append(f"{cx+rr*math.cos(a):.1f},{cy+rr*math.sin(a):.1f}")
            body.append(f'<polygon points="{" ".join(pts)}" fill="{fillc}" stroke="{strokec}" stroke-width="2.5" stroke-linejoin="round"/>')
        body.append(_text(cx, top + size + 22, name, 13, INK, weight="600"))
    return _svg(len(shapes) * cellw, top + size + 34, "".join(body), "shapes: " + ", ".join(shapes))


# ---------------------------------------------------------------- science

def force_diagram(right=30, left=10, box="sled", **_):
    fillc, strokec = COLORS["blue"]
    k = 2.4
    bx, by, bw, bh = 135, 46, 70, 42
    cx = bx + bw / 2
    body = [f'<rect x="{bx}" y="{by}" width="{bw}" height="{bh}" rx="11" fill="{fillc}" stroke="{INK}" stroke-width="1.8"/>',
            _text(cx, by + bh / 2 + 4, box, 13, INK, weight="600")]
    # right push (green)
    rx_end = bx + bw + right * k
    body.append(_arrow(bx + bw + 4, by + bh / 2, rx_end, by + bh / 2, COLORS["green"][1], 3))
    body.append(_text((bx + bw + rx_end) / 2, by - 6, f"{right} N", 12, COLORS["green"][1], weight="700"))
    # left friction (rose)
    lx_end = bx - left * k
    body.append(_arrow(bx - 4, by + bh / 2, lx_end, by + bh / 2, COLORS["rose"][1], 3))
    body.append(_text((bx + lx_end) / 2, by - 6, f"{left} N", 12, COLORS["rose"][1], weight="700"))
    # resultant below
    net = right - left
    ny = by + bh + 30
    body.append(_text(cx, ny - 8, f"leftover force = {net} N", 12, INK, weight="600"))
    body.append(_arrow(cx, ny, cx + net * k, ny, INK, 2.6))
    return _svg(340, ny + 16, "".join(body), f"push {right} N, friction {left} N, net {net} N")


def flow(steps, loop=False, color="blue", **_):
    fillc, strokec = COLORS[color]
    w, ph, gap, left, pad = 236, 40, 22, 44, 12
    body, y = [], pad
    n = len(steps)
    for i, s in enumerate(steps):
        body.append(f'<rect x="{left}" y="{y}" width="{w}" height="{ph}" rx="12" fill="{fillc}" stroke="{INK}" stroke-width="1.4"/>')
        body.append(_text(left + w / 2, y + ph / 2 + 4, s, 13, INK, weight="600"))
        if i < n - 1:
            body.append(_arrow(left + w / 2, y + ph, left + w / 2, y + ph + gap, INK, 2))
        y += ph + gap
    total_h = y - gap + pad
    if loop:
        top_y = pad + ph / 2
        bot_y = pad + (n - 1) * (ph + gap) + ph / 2
        body.append(f'<path d="M{left} {bot_y} C14 {bot_y} 14 {top_y} {left} {top_y}" fill="none" '
                    f'stroke="{strokec}" stroke-width="2" stroke-dasharray="5 4"/>')
        body.append(f'<polygon points="{left},{top_y} {left-8},{top_y-4} {left-8},{top_y+4}" fill="{strokec}"/>')
    return _svg(left + w + 12, total_h, "".join(body), "flow: " + " then ".join(steps))


# ---------------------------------------------------------------- english

ROLE_COLORS = {
    "subject": COLORS["green"][1],
    "verb": COLORS["blue"][1],
    "object": COLORS["amber"][1],
    "adjective": COLORS["purple"][1],
    "adverb": COLORS["rose"][1],
}


def labeled_phrase(words, **_):
    x, fs, charw = 16, 18, 10.2
    body, labels = [], []
    for wd in words:
        t = wd.get("text", "")
        role = wd.get("role", "other")
        wpx = len(t) * charw + 8
        body.append(_text(x, 34, t, fs, INK, anchor="start", weight="600"))
        if role in ROLE_COLORS:
            c = ROLE_COLORS[role]
            body.append(f'<rect x="{x-2:.1f}" y="42" width="{wpx-4:.1f}" height="6" rx="3" fill="{c}"/>')
            labels.append(_text(x + (wpx - 4) / 2 - 2, 64, role, 11, c, weight="700"))
        x += wpx
    return _svg(x + 12, 76, "".join(body) + "".join(labels), "labelled sentence")


def blocks(items, **_):
    # vertical stack of labelled role-blocks (e.g. essay structure)
    palette = {"intro": "amber", "body": "green", "conclusion": "blue", "point": "green"}
    w, left, pad, gap = 250, 30, 12, 10
    body, y = [], pad
    for it in items:
        label = it.get("label", "")
        role = it.get("role", "body")
        h = it.get("h", 40)
        fillc, strokec = COLORS[palette.get(role, "green")]
        body.append(f'<rect x="{left}" y="{y}" width="{w}" height="{h}" rx="11" fill="{fillc}" stroke="{INK}" stroke-width="1.4"/>')
        body.append(_text(left + w / 2, y + h / 2 + 4, label, 13, INK, weight="600"))
        y += h + gap
    return _svg(left + w + 12, y - gap + pad, "".join(body), "structure: " + ", ".join(i.get("label", "") for i in items))


def equation_dots(a, b, op="add", color="green", **_):
    fillc, strokec = COLORS[color]
    r, gap, sgap = 12, 7, 22
    y = 32
    parts, x = [], 10

    def dots(n, cross_from=None):
        nonlocal x
        for i in range(n):
            cx = x + r
            parts.append(f'<circle cx="{cx}" cy="{y}" r="{r}" fill="{fillc}" stroke="{strokec}" stroke-width="2"/>')
            if cross_from is not None and i >= cross_from:
                parts.append(f'<line x1="{cx-r}" y1="{y-r}" x2="{cx+r}" y2="{y+r}" stroke="{COLORS["rose"][1]}" stroke-width="2.6" stroke-linecap="round"/>')
            x += 2 * r + gap
        x += sgap - gap

    def sign(s):
        nonlocal x
        parts.append(_text(x + 4, y + 7, s, 22, INK, weight="700"))
        x += 24

    if op == "add":
        dots(a); sign("+"); dots(b); sign("="); dots(a + b)
        label = f"{a} + {b} = {a + b}"
    else:
        dots(a, cross_from=a - b); sign("="); dots(a - b)
        label = f"{a} take away {b} = {a - b}"
    w = x + 6
    parts.append(_text(w / 2, y + 38, label, 15, INK, weight="700"))
    return _svg(w, y + 50, "".join(parts), label)


def array(rows, cols, color="blue", **_):
    fillc, strokec = COLORS[color]
    r, gap, pad = 11, 8, 14
    parts = []
    for row in range(rows):
        for col in range(cols):
            cx = pad + r + col * (2 * r + gap)
            cy = pad + r + row * (2 * r + gap)
            parts.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{fillc}" stroke="{strokec}" stroke-width="2"/>')
    w = pad * 2 + cols * (2 * r + gap) - gap
    h = pad * 2 + rows * (2 * r + gap) - gap
    parts.append(_text(w / 2, h + 22, f"{rows} × {cols} = {rows * cols}", 15, INK, weight="700"))
    return _svg(max(w, 110), h + 34, "".join(parts), f"{rows} rows of {cols} = {rows * cols}")


def two_bars(a, b, a_label="A", b_label="B", **_):
    maxv = max(a, b) or 1
    W = 210
    parts = []
    for i, (val, label, color) in enumerate([(a, a_label, "blue"), (b, b_label, "amber")]):
        y = 26 + i * 56
        col = COLORS[color]
        parts.append(_text(14, y - 6, label, 12.5, INK, anchor="start", weight="600"))
        parts.append(f'<rect x="14" y="{y}" width="{max(12, (val/maxv)*W):.1f}" height="24" rx="8" fill="{col[0]}" stroke="{col[1]}" stroke-width="2"/>')
    total_h = 26 + 2 * 56
    msg = f"{a_label} is longer" if a > b else (f"{b_label} is longer" if b > a else "same length")
    parts.append(_text((14 + W) / 2, total_h + 4, msg, 13, INK, weight="600"))
    return _svg(W + 28, total_h + 16, "".join(parts), "comparing lengths")


def clock(hour=3, minute=0, **_):
    cx, cy, r = 90, 90, 78
    parts = [f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="#fff" stroke="{INK}" stroke-width="2.5"/>']
    for n in range(1, 13):
        a = math.radians(-90 + n * 30)
        x1, y1 = cx + (r - 7) * math.cos(a), cy + (r - 7) * math.sin(a)
        x2, y2 = cx + r * math.cos(a), cy + r * math.sin(a)
        parts.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{INK}" stroke-width="1.6"/>')
        nx, ny = cx + (r - 18) * math.cos(a), cy + (r - 18) * math.sin(a)
        parts.append(_text(nx, ny + 5, n, 14, INK, weight="600"))
    ma = math.radians(-90 + minute * 6)
    parts.append(f'<line x1="{cx}" y1="{cy}" x2="{cx + (r-20)*math.cos(ma):.1f}" y2="{cy + (r-20)*math.sin(ma):.1f}" stroke="{COLORS["blue"][1]}" stroke-width="3" stroke-linecap="round"/>')
    ha = math.radians(-90 + (hour % 12) * 30 + minute * 0.5)
    parts.append(f'<line x1="{cx}" y1="{cy}" x2="{cx + (r-40)*math.cos(ha):.1f}" y2="{cy + (r-40)*math.sin(ha):.1f}" stroke="{INK}" stroke-width="4" stroke-linecap="round"/>')
    parts.append(f'<circle cx="{cx}" cy="{cy}" r="4" fill="{INK}"/>')
    parts.append(_text(cx, 2 * cy + 24, f"{hour}:{minute:02d}", 15, INK, weight="700"))
    return _svg(180, 2 * cy + 36, "".join(parts), f"clock showing {hour}:{minute:02d}")


def coins(values, symbol="¢", **_):
    r, gap, pad = 22, 12, 14
    parts = []
    for i, v in enumerate(values):
        cx = pad + r + i * (2 * r + gap)
        parts.append(f'<circle cx="{cx}" cy="{pad+r}" r="{r}" fill="{COLORS["amber"][0]}" stroke="{COLORS["amber"][1]}" stroke-width="2.5"/>')
        parts.append(_text(cx, pad + r + 5, f"{v}{symbol}", 12.5, INK, weight="700"))
    w = pad * 2 + len(values) * (2 * r + gap) - gap
    parts.append(_text(w / 2, pad + 2 * r + 28, f"total = {sum(values)}{symbol}", 14, INK, weight="700"))
    return _svg(max(w, 120), pad + 2 * r + 40, "".join(parts), f"coins totalling {sum(values)}{symbol}")


def compare(a, b, **_):
    r, gap = 13, 8
    fa, fb = COLORS["blue"], COLORS["amber"]
    parts = []

    def row(n, y, col):
        for i in range(n):
            cx = 16 + r + i * (2 * r + gap)
            parts.append(f'<circle cx="{cx}" cy="{y}" r="{r}" fill="{col[0]}" stroke="{col[1]}" stroke-width="2"/>')
    row(a, 30, fa)
    row(b, 74, fb)
    sym = ">" if a > b else ("<" if a < b else "=")
    word = "more than" if a > b else ("fewer than" if a < b else "the same as")
    w = 16 + max(a, b) * (2 * r + gap) + 60
    parts.append(_text(w - 30, 56, sym, 26, INK, weight="800"))
    parts.append(_text((w - 40) / 2, 108, f"{a} is {word} {b}   ({a} {sym} {b})", 14, INK, weight="600"))
    return _svg(w, 122, "".join(parts), f"{a} {sym} {b}")


def pattern(items, **_):
    cell, size, top = 52, 34, 14
    parts = []
    for i, it in enumerate(items):
        cx, cy = i * cell + cell / 2, top + size / 2
        if it.get("q"):
            parts.append(f'<rect x="{cx-size/2}" y="{cy-size/2}" width="{size}" height="{size}" rx="8" fill="none" stroke="{EMPTY_STROKE}" stroke-width="2" stroke-dasharray="4 4"/>')
            parts.append(_text(cx, cy + 9, "?", 28, FAINT, weight="700"))
            continue
        col = COLORS[it.get("color", "green")]
        shp = it.get("shape", "circle")
        if shp == "circle":
            parts.append(f'<circle cx="{cx}" cy="{cy}" r="{size/2}" fill="{col[0]}" stroke="{col[1]}" stroke-width="2.5"/>')
        elif shp == "square":
            parts.append(f'<rect x="{cx-size/2}" y="{cy-size/2}" width="{size}" height="{size}" rx="7" fill="{col[0]}" stroke="{col[1]}" stroke-width="2.5"/>')
        elif shp == "triangle":
            parts.append(f'<polygon points="{cx},{cy-size/2} {cx+size/2},{cy+size/2} {cx-size/2},{cy+size/2}" fill="{col[0]}" stroke="{col[1]}" stroke-width="2.5" stroke-linejoin="round"/>')
    return _svg(len(items) * cell, top + size + 16, "".join(parts), "repeating pattern")


def place_value(number, **_):
    s = str(int(number)).rjust(3, "0")
    cols = [("Hundreds", int(s[0]), "rose"), ("Tens", int(s[1]), "amber"), ("Ones", int(s[2]), "green")]
    cw, parts = 100, []
    for i, (name, d, color) in enumerate(cols):
        x = i * cw
        col = COLORS[color]
        parts.append(f'<rect x="{x+8}" y="14" width="{cw-16}" height="88" rx="12" fill="{col[0]}" stroke="{col[1]}" stroke-width="2"/>')
        parts.append(_text(x + cw / 2, 34, name, 12, INK, weight="700"))
        parts.append(_text(x + cw / 2, 82, d, 34, INK, weight="800"))
    parts.append(_text(1.5 * cw, 126, f"{int(number)} = {cols[0][1]} hundreds, {cols[1][1]} tens, {cols[2][1]} ones", 13, INK, weight="600"))
    return _svg(3 * cw, 138, "".join(parts), f"place value of {int(number)}")


def line_graph(m=1, b=0, color="blue", **_):
    fillc, strokec = COLORS[color]
    W, O, step = 240, 120, 20
    parts = []
    for i in range(-5, 6):
        g = O + i * step
        parts.append(f'<line x1="{g}" y1="0" x2="{g}" y2="{W}" stroke="{EMPTY}" stroke-width="1"/>')
        parts.append(f'<line x1="0" y1="{g}" x2="{W}" y2="{g}" stroke="{EMPTY}" stroke-width="1"/>')
    parts.append(f'<line x1="0" y1="{O}" x2="{W}" y2="{O}" stroke="{INK}" stroke-width="1.6"/>')
    parts.append(f'<line x1="{O}" y1="0" x2="{O}" y2="{W}" stroke="{INK}" stroke-width="1.6"/>')

    def px(x, y):
        return (O + x * step, O - y * step)
    p1, p2 = px(-5, m * -5 + b), px(5, m * 5 + b)
    parts.append(f'<line x1="{p1[0]:.1f}" y1="{p1[1]:.1f}" x2="{p2[0]:.1f}" y2="{p2[1]:.1f}" stroke="{strokec}" stroke-width="3" stroke-linecap="round"/>')
    sign = "+" if b >= 0 else "−"
    parts.append(_text(W / 2, W + 20, f"y = {m}x {sign} {abs(b)}", 14, strokec, weight="700"))
    return _svg(W, W + 30, "".join(parts), f"line y = {m}x + {b}")


def right_triangle(opp=3, adj=4, **_):
    hyp = math.hypot(opp, adj)
    scale = 150 / max(opp, adj)
    ax, ay = 112, 176           # right-angle corner (bottom-left), left margin for the label
    bx, by = ax + adj * scale, ay   # bottom-right (angle theta here)
    cx, cy = ax, ay - opp * scale   # top-left
    parts = [f'<polygon points="{ax},{ay} {bx:.1f},{by} {cx},{cy:.1f}" fill="{COLORS["blue"][0]}" stroke="{INK}" stroke-width="2" stroke-linejoin="round"/>']
    parts.append(f'<rect x="{ax}" y="{ay-14}" width="14" height="14" fill="none" stroke="{INK}" stroke-width="1.4"/>')  # right angle
    parts.append(f'<path d="M{bx-26:.1f} {by} A26 26 0 0 0 {bx-24:.1f} {by-11:.1f}" fill="none" stroke="{COLORS["rose"][1]}" stroke-width="2"/>')
    parts.append(_text(bx - 34, by - 6, "θ", 15, COLORS["rose"][1], weight="700"))
    parts.append(_text((ax + bx) / 2, ay + 20, f"adjacent = {adj}", 12.5, INK, weight="600"))
    parts.append(_text(ax - 10, (ay + cy) / 2, f"opposite = {opp}", 12, INK, anchor="end", weight="600"))
    parts.append(_text((bx + cx) / 2 + 14, (by + cy) / 2 - 6, f"hyp = {hyp:g}", 12.5, COLORS["blue"][1], weight="700"))
    return _svg(bx + 20, ay + 34, "".join(parts), f"right triangle {opp}, {adj}, {hyp:g}")


def curve_tangent(color="purple", **_):
    fillc, strokec = COLORS[color]
    W, H = 240, 150

    def fy(x):
        return H - 22 - 105 * (x / W) ** 2
    pts = [(i, fy(i)) for i in range(0, W + 1, 8)]
    d = "M" + " L".join(f"{x:.0f} {y:.0f}" for x, y in pts)
    parts = [f'<line x1="0" y1="{H-22}" x2="{W}" y2="{H-22}" stroke="{EMPTY_STROKE}" stroke-width="1.4"/>',
             f'<path d="{d}" fill="none" stroke="{strokec}" stroke-width="3" stroke-linecap="round"/>']
    tx = 150
    ty = fy(tx)
    slope = (fy(tx + 1) - fy(tx - 1)) / 2
    x1, x2 = tx - 55, tx + 55
    parts.append(f'<line x1="{x1}" y1="{ty+slope*(x1-tx):.1f}" x2="{x2}" y2="{ty+slope*(x2-tx):.1f}" stroke="{INK}" stroke-width="2" stroke-dasharray="5 4"/>')
    parts.append(f'<circle cx="{tx}" cy="{ty:.1f}" r="5" fill="{strokec}"/>')
    parts.append(_text(W / 2, H + 16, "the tangent's steepness is the rate of change", 12, INK, weight="600"))
    return _svg(W, H + 26, "".join(parts), "curve with a tangent line showing slope")


KINDS = {
    "fraction_circle": fraction_circle,
    "fraction_bar": fraction_bar,
    "hundred_grid": hundred_grid,
    "number_line": number_line,
    "counting": counting,
    "shapes": shapes_row,
    "force": force_diagram,
    "flow": flow,
    "phrase": labeled_phrase,
    "blocks": blocks,
    "equation_dots": equation_dots,
    "array": array,
    "two_bars": two_bars,
    "clock": clock,
    "coins": coins,
    "compare": compare,
    "pattern": pattern,
    "place_value": place_value,
    "line_graph": line_graph,
    "right_triangle": right_triangle,
    "curve_tangent": curve_tangent,
}


def render(spec):
    kind = spec.get("kind")
    fn = KINDS.get(kind)
    if not fn:
        raise ValueError(f"unknown diagram kind: {kind!r}")
    params = {k: v for k, v in spec.items() if k not in ("kind", "caption")}
    return fn(**params)
