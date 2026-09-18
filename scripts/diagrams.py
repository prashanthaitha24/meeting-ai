"""Render declarative architecture diagrams to inline SVG for the Education pages.

A diagram is a JSON object (see site-src/education/diagrams/*.json):

  {
    "id": "k8s-cluster",                        # unique per module; used for SVG marker ids
    "caption": "One sentence stating what the picture shows",
    "alt": "Optional longer description for screen readers (defaults to the caption)",
    "place": {"section": 0, "after": 1},        # insert after block 1 of section 0 (-1 = before the first block)
    "nodes": [ {"id": "api", "label": "API server", "sub": "kube-apiserver",
                "col": 1, "row": 0, "w": 1, "kind": "accent"} ],
    "groups": [ {"label": "Control plane", "col": 0, "row": 0, "w": 3, "h": 1, "outer": false} ],
    "edges": [ {"from": "kubectl", "to": "api", "label": "apply", "route": "auto",
                "style": "solid", "dir": "forward", "color": "default", "offset": 0} ]
  }

Layout is a grid of cells; every node occupies one cell (or `w` cells across). Edges are routed
straight when the nodes share a row or column, otherwise as an elbow (horizontal then vertical, or
"vh" for the reverse). Colours come from the page's CSS variables so diagrams follow the track accent.
"""
import html

CELL_W, CELL_H = 170, 108
BOX_H = 56
MARGIN = 16
KINDS = {"box", "accent", "muted", "store", "actor", "danger", "ok", "text"}
COLORS = {"default", "accent", "danger", "ok", "muted"}
ROUTES = {"auto", "hv", "vh", "straight", "over", "under"}
STROKE = {
    "default": "currentColor",
    "accent": "var(--accent)",
    "danger": "#f87171",
    "ok": "#34d399",
    "muted": "rgba(148,163,184,0.55)",
}


def validate(d, where):
    errs = []
    need = lambda c, m: errs.append(f"{where}: {m}") if not c else None
    need(isinstance(d.get("id"), str) and d["id"], "diagram needs an 'id'")
    need(isinstance(d.get("caption"), str) and len(d.get("caption", "").split()) >= 6, "'caption' needs >= 6 words")
    place = d.get("place", {})
    need(isinstance(place.get("section"), int) and isinstance(place.get("after"), int), "'place' needs section and after")
    nodes = d.get("nodes", [])
    need(isinstance(nodes, list) and 2 <= len(nodes) <= 24, "needs 2-24 nodes")
    ids, cells = set(), set()
    for n in nodes if isinstance(nodes, list) else []:
        nid = n.get("id")
        need(isinstance(nid, str) and nid not in ids, f"node id {nid!r} missing or duplicated")
        ids.add(nid)
        need(isinstance(n.get("label"), str) and n["label"], f"node {nid}: needs a label")
        need(n.get("kind", "box") in KINDS, f"node {nid}: unknown kind {n.get('kind')!r}")
        need(isinstance(n.get("col"), int) and isinstance(n.get("row"), int) and n["col"] >= 0 and n["row"] >= 0,
             f"node {nid}: needs non-negative col and row")
        w = n.get("w", 1)
        need(isinstance(w, int) and 1 <= w <= 4, f"node {nid}: w must be 1-4")
        for k in range(w if isinstance(w, int) else 1):
            cell = (n.get("col", 0) + k, n.get("row", 0))
            need(cell not in cells, f"node {nid}: overlaps another node at col {cell[0]}, row {cell[1]}")
            cells.add(cell)
        cap = int((CELL_W * w - 30 - 16) / 7.3)
        for line in n["label"].split("\n") if isinstance(n.get("label"), str) else []:
            if len(line) > cap:
                errs.append(f"{where}: node {nid}: label line {line!r} is longer than {cap} chars for its width")
        if n.get("sub") and len(n["sub"]) > cap + 6:
            errs.append(f"{where}: node {nid}: 'sub' is too long")
    for g in d.get("groups", []):
        need(isinstance(g.get("label"), str), "group needs a label")
        if isinstance(g.get("label"), str) and isinstance(g.get("w"), int) and len(g["label"]) * 7.4 > g["w"] * CELL_W - 24:
            errs.append(f"{where}: group label {g['label']!r} is wider than the group")
        for k in ("col", "row", "w", "h"):
            need(isinstance(g.get(k), int) and g[k] >= (1 if k in "wh" else 0), f"group {g.get('label')!r}: bad {k}")
    gids = {g.get("id") for g in d.get("groups", []) if g.get("id")}
    for e in d.get("edges", []):
        need(e.get("from") in ids | gids and e.get("to") in ids | gids,
             f"edge {e.get('from')}->{e.get('to')}: unknown node or group")
        need(e.get("from") != e.get("to"), f"edge {e.get('from')}: self-loops are not supported")
        need(e.get("route", "auto") in ROUTES, f"edge {e.get('from')}->{e.get('to')}: bad route")
        need(e.get("color", "default") in COLORS, f"edge {e.get('from')}->{e.get('to')}: bad color")
        need(e.get("style", "solid") in {"solid", "dashed"}, f"edge {e.get('from')}->{e.get('to')}: bad style")
        need(e.get("dir", "forward") in {"forward", "both", "none"}, f"edge {e.get('from')}->{e.get('to')}: bad dir")
        if e.get("label") and len(e["label"]) > 26:
            errs.append(f"{where}: edge {e['from']}->{e['to']}: label longer than 26 chars")
    return errs


def _rect(n, ox, oy):
    if "h" in n and "w" in n and n.get("_group"):      # a group used as an edge endpoint
        pad = 22 if n.get("outer") else 0
        return (ox + n["col"] * CELL_W + 4 - pad, oy + n["row"] * CELL_H + 3 - pad,
                n["w"] * CELL_W - 8 + 2 * pad, n["h"] * CELL_H - 6 + 2 * pad)
    w = n.get("w", 1)
    x = ox + n["col"] * CELL_W + 15
    y = oy + n["row"] * CELL_H + (CELL_H - BOX_H) / 2
    return x, y, CELL_W * w - 30, BOX_H


def _side_point(r, side, offset=0.0):
    x, y, w, h = r
    return {
        "left": (x, y + h / 2 + offset), "right": (x + w, y + h / 2 + offset),
        "top": (x + w / 2 + offset, y), "bottom": (x + w / 2 + offset, y + h),
    }[side]


def _clip_to_rect(cx, cy, tx, ty, r):
    """Point where the segment from the rect centre (cx, cy) towards (tx, ty) leaves the rect."""
    x, y, w, h = r
    dx, dy = tx - cx, ty - cy
    if dx == 0 and dy == 0:
        return cx, cy
    tx_ = abs((w / 2) / dx) if dx else float("inf")
    ty_ = abs((h / 2) / dy) if dy else float("inf")
    t = min(tx_, ty_)
    return cx + dx * t, cy + dy * t


def _route(e, rs, rt):
    route = e.get("route", "auto")
    off = float(e.get("offset", 0))
    sx, sy, sw, sh = rs
    tx, ty, tw, th = rt
    scx, scy, tcx, tcy = sx + sw / 2, sy + sh / 2, tx + tw / 2, ty + th / 2
    same_row = abs(scy - tcy) < 1
    same_col = abs(scx - tcx) < 1
    if route == "auto":
        route = "straight" if (same_row or same_col) else "hv"
    if route == "straight":
        if same_row:
            a, b = ("right", "left") if tcx > scx else ("left", "right")
            return [_side_point(rs, a, off), _side_point(rt, b, off)]
        if same_col:
            a, b = ("bottom", "top") if tcy > scy else ("top", "bottom")
            return [_side_point(rs, a, off), _side_point(rt, b, off)]
        if sx <= tcx <= sx + sw or tx <= scx <= tx + tw:   # one centre lies over the other: vertical
            x = tcx if sx <= tcx <= sx + sw else scx
            x += off
            if tcy > scy:
                return [(x, sy + sh), (x, ty)]
            return [(x, sy), (x, ty + th)]
        if sy <= tcy <= sy + sh or ty <= scy <= ty + th:   # side by side: horizontal
            y = tcy if sy <= tcy <= sy + sh else scy
            y += off
            if tcx > scx:
                return [(sx + sw, y), (tx, y)]
            return [(sx, y), (tx + tw, y)]
        p0 = _clip_to_rect(scx, scy, tcx, tcy, rs)
        p1 = _clip_to_rect(tcx, tcy, scx, scy, rt)
        return [p0, p1]
    if route in ("over", "under"):                 # hop through the gap above or below the row(s)
        if route == "over":
            lane = min(sy, ty) - 22
            p0, p3 = _side_point(rs, "top", off), _side_point(rt, "top", off)
        else:
            lane = max(sy + sh, ty + th) + 22
            p0, p3 = _side_point(rs, "bottom", off), _side_point(rt, "bottom", off)
        return [p0, (p0[0], lane), (p3[0], lane), p3]
    if route == "hv":
        a = "right" if tcx > scx else "left"
        b = "top" if tcy > scy else "bottom"
        p0 = _side_point(rs, a, off)
        p2 = _side_point(rt, b, off)
        return [p0, (p2[0], p0[1]), p2]
    # vh
    a = "bottom" if tcy > scy else "top"
    b = "left" if tcx > scx else "right"
    p0 = _side_point(rs, a, off)
    p2 = _side_point(rt, b, off)
    return [p0, (p0[0], p2[1]), p2]


def _esc(s):
    return html.escape(s, quote=True)


def _text_lines(x, y, lines, size, weight, fill, anchor="middle", extra=""):
    lh = size * 1.25
    total = lh * (len(lines) - 1)
    out = []
    for i, line in enumerate(lines):
        yy = y - total / 2 + i * lh
        out.append(f'<text x="{x:.1f}" y="{yy:.1f}" text-anchor="{anchor}" dominant-baseline="middle" '
                   f'font-size="{size}" font-weight="{weight}" fill="{fill}"{extra}>{_esc(line)}</text>')
    return "".join(out)


def render(d):
    nodes = {n["id"]: n for n in d["nodes"]}
    groups = d.get("groups", [])
    for g in groups:
        if g.get("id"):
            nodes[g["id"]] = {**g, "_group": True}
    edges = d.get("edges", [])
    cols = max(n["col"] + n.get("w", 1) for n in d["nodes"])
    rows = max(n["row"] for n in d["nodes"]) + 1
    for g in groups:
        cols = max(cols, g["col"] + g["w"])
        rows = max(rows, g["row"] + g["h"])
    outer = any(g.get("outer") for g in groups)
    ox, oy = MARGIN, MARGIN + (30 if outer else 0)
    W = cols * CELL_W + 2 * MARGIN + 28          # extra room on the right for labels beside the last column
    H = rows * CELL_H + oy + MARGIN
    did = d["id"]
    parts = []

    # markers
    defs = []
    for name, stroke in STROKE.items():
        defs.append(f'<marker id="{did}-arrow-{name}" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" '
                    f'markerHeight="7" orient="auto-start-reverse"><path d="M0,1 L9,5 L0,9 z" '
                    f'style="fill:{stroke};stroke:none"/></marker>')
    parts.append("<defs>" + "".join(defs) + "</defs>")

    # groups (behind everything)
    for g in groups:
        pad = 22 if g.get("outer") else 0
        x = ox + g["col"] * CELL_W + 4 - pad
        y = oy + g["row"] * CELL_H + 3 - pad
        w = g["w"] * CELL_W - 8 + 2 * pad
        h = g["h"] * CELL_H - 6 + 2 * pad
        parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="10" class="dg-group"/>')
        ly = y - 6 if g.get("outer") else y + h - 7      # inside groups: bottom-left, clear of arrow labels
        parts.append(f'<text x="{x + 10}" y="{ly}" font-size="10" font-weight="700" letter-spacing="1" '
                     f'class="dg-group-label">{_esc(g["label"].upper())}</text>')

    # edges
    for e in edges:
        rs, rt = _rect(nodes[e["from"]], ox, oy), _rect(nodes[e["to"]], ox, oy)
        pts = _route(e, rs, rt)
        color = e.get("color", "default")
        stroke = STROKE[color]
        dash = ' stroke-dasharray="6 5"' if e.get("style") == "dashed" else ""
        d_attr = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
        markers = ""
        if e.get("dir", "forward") in ("forward", "both"):
            markers += f' marker-end="url(#{did}-arrow-{color})"'
        if e.get("dir") == "both":
            markers += f' marker-start="url(#{did}-arrow-{color})"'
        parts.append(f'<polyline points="{d_attr}" fill="none" style="stroke:{stroke}" stroke-width="1.6"{dash}{markers}/>')
        if e.get("label"):
            # label on the longest segment
            best, blen = None, -1
            for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
                ln = abs(x1 - x0) + abs(y1 - y0)
                if ln > blen:
                    best, blen = ((x0, y0), (x1, y1)), ln
            (x0, y0), (x1, y1) = best
            mx, my = (x0 + x1) / 2, (y0 + y1) / 2
            label = e["label"]
            tw = len(label) * 6.1 + 10
            if abs(y1 - y0) < 1:                       # horizontal
                straight_row = len(pts) == 2
                if e.get("route") == "under":
                    ly, lx, anchor, bx = my + 11, mx, "middle", mx - tw / 2
                    parts.append(f'<rect x="{bx:.1f}" y="{ly - 8:.1f}" width="{tw:.1f}" height="16" rx="4" class="dg-label-bg"/>')
                    fill = stroke if color in ("accent", "danger", "ok") else "var(--text2)"
                    parts.append(f'<text x="{lx:.1f}" y="{ly:.1f}" text-anchor="{anchor}" dominant-baseline="middle" '
                                 f'font-size="10.5" font-weight="600" style="fill:{fill}">{_esc(label)}</text>')
                    continue
                # a straight edge between neighbours has no room: put the label above the boxes
                lx, ly, anchor = mx, my - (BOX_H / 2 + 10 if straight_row else 11), "middle"
                bx = mx - tw / 2
            elif e.get("label_side") == "left":        # vertical: label to the left
                lx, ly, anchor = mx - 7, my, "end"
                bx = mx - 3 - tw
            else:                                      # vertical: label to the right
                lx, ly, anchor = mx + 7, my, "start"
                bx = mx + 3
            fill = stroke if color in ("accent", "danger", "ok") else "var(--text2)"
            parts.append(f'<rect x="{bx:.1f}" y="{ly - 8:.1f}" width="{tw:.1f}" height="16" rx="4" class="dg-label-bg"/>')
            parts.append(f'<text x="{lx:.1f}" y="{ly:.1f}" text-anchor="{anchor}" dominant-baseline="middle" '
                         f'font-size="10.5" font-weight="600" style="fill:{fill}">{_esc(label)}</text>')

    # nodes
    for n in d["nodes"]:
        x, y, w, h = _rect(n, ox, oy)
        kind = n.get("kind", "box")
        cx, cy = x + w / 2, y + h / 2
        lines = n["label"].split("\n")
        sub = n.get("sub")
        if kind == "text":
            parts.append(_text_lines(cx, cy, lines, 12.5, 500, "var(--text2)"))
            continue
        if kind == "store":
            ry = 7
            parts.append(f'<path d="M{x},{y + ry} a{w / 2},{ry} 0 0 1 {w},0 v{h - 2 * ry} a{w / 2},{ry} 0 0 1 -{w},0 z" class="dg-node dg-{kind}"/>')
            parts.append(f'<path d="M{x},{y + ry} a{w / 2},{ry} 0 0 0 {w},0" class="dg-node-line dg-{kind}"/>')
        elif kind == "actor":
            parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{h / 2}" class="dg-node dg-{kind}"/>')
        else:
            parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="8" class="dg-node dg-{kind}"/>')
        text_fill = {"accent": "var(--accent)", "danger": "#fca5a5", "ok": "#6ee7b7", "muted": "var(--text2)"}.get(kind, "var(--text)")
        if sub:
            parts.append(_text_lines(cx, cy - 7 - (len(lines) - 1) * 7, lines, 13, 600, text_fill))
            parts.append(_text_lines(cx, cy + 11 + (len(lines) - 1) * 6, [sub], 10.5, 400, "var(--text3)",
                                     extra=' font-family="var(--mono)"'))
        else:
            parts.append(_text_lines(cx, cy, lines, 13, 600, text_fill))

    alt = d.get("alt") or d["caption"]
    min_w = min(W, 540)
    svg = (f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="{_esc(alt)}" '
           f'style="width:100%;max-width:{W}px;min-width:{min_w}px;height:auto;display:block">'
           + "".join(parts) + "</svg>")
    return (f'<figure class="diagram" id="fig-{_esc(did)}"><div class="diagram-scroll">{svg}</div>'
            f'<figcaption>{html.escape(d["caption"], quote=False)}</figcaption></figure>')
