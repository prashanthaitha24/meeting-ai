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
}


def render(spec):
    kind = spec.get("kind")
    fn = KINDS.get(kind)
    if not fn:
        raise ValueError(f"unknown diagram kind: {kind!r}")
    params = {k: v for k, v in spec.items() if k not in ("kind", "caption")}
    return fn(**params)
