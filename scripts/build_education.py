#!/usr/bin/env python3
"""Build the thavionai.com Education lesson pages.

Source:  site-src/education/tracks.json          (track -> stage -> module order, titles)
         site-src/education/modules/<id>.json    (lesson, cheat sheet, quiz for one module)
Output:  docs/education/<id>.html                (static pages served by GitHub Pages)

Usage:
  python3 scripts/build_education.py               build every module that has a JSON file
  python3 scripts/build_education.py --check ID..  validate specific modules only (no output)
  python3 scripts/build_education.py --strict      fail if any module in tracks.json is missing
"""
import ast
import html
import json
import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import quote

try:
    import yaml
except ImportError:  # linting YAML blocks is best-effort
    yaml = None

sys.path.insert(0, str(Path(__file__).resolve().parent))
import diagrams  # noqa: E402  (scripts/diagrams.py)

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "site-src" / "education"
OUT = ROOT / "docs" / "education"

BLOCK_TYPES = {"p", "list", "steps", "code", "callout", "table"}
CALLOUT_KINDS = {"tip", "warning", "note"}
BANNED_OPTIONS = ("all of the above", "none of the above", "both a and b", "all of these")


# ---------------------------------------------------------------- validation

def lint_code(lang, code):
    """Return an error string if a code block is syntactically broken, else None."""
    lang = (lang or "").lower()
    if lang in ("bash", "sh", "shell"):
        r = subprocess.run(["bash", "-n"], input=code, text=True, capture_output=True)
        if r.returncode != 0:
            return "bash -n: " + r.stderr.strip().splitlines()[-1]
    elif lang in ("yaml", "yml") and yaml:
        try:
            list(yaml.safe_load_all(code))
        except yaml.YAMLError as e:
            return "yaml: " + str(e).replace("\n", " ")[:200]
    elif lang == "python":
        try:
            ast.parse(code)
        except SyntaxError as e:
            return f"python: {e.msg} (line {e.lineno})"
    elif lang == "json":
        try:
            json.loads(code)
        except ValueError as e:
            return f"json: {e}"
    return None


def words(text):
    return len(re.findall(r"[A-Za-z0-9']+", text or ""))


def validate(mod_id, m):
    errs, warns = [], []

    def need(cond, msg):
        if not cond:
            errs.append(msg)

    need(m.get("id") == mod_id, f"'id' must equal the filename ({mod_id})")
    need(isinstance(m.get("minutes"), int) and 10 <= m["minutes"] <= 90, "'minutes' must be an int 10-90")
    need(isinstance(m.get("intro"), str) and words(m.get("intro")) >= 25, "'intro' needs at least 25 words")
    obj = m.get("objectives", [])
    need(isinstance(obj, list) and 3 <= len(obj) <= 5, "'objectives' needs 3-5 items")

    total_words = words(m.get("intro"))
    sections = m.get("sections", [])
    need(isinstance(sections, list) and 4 <= len(sections) <= 7, "'sections' needs 4-7 sections")
    n_code = 0
    for si, s in enumerate(sections if isinstance(sections, list) else []):
        where = f"sections[{si}]"
        need(isinstance(s.get("heading"), str) and s["heading"].strip(), f"{where}: missing heading")
        blocks = s.get("blocks", [])
        need(isinstance(blocks, list) and blocks, f"{where}: needs blocks")
        for bi, b in enumerate(blocks if isinstance(blocks, list) else []):
            bw = f"{where}.blocks[{bi}]"
            t = b.get("type")
            need(t in BLOCK_TYPES, f"{bw}: unknown type {t!r}")
            if t == "p":
                need(isinstance(b.get("text"), str) and b["text"].strip(), f"{bw}: empty text")
                total_words += words(b.get("text"))
            elif t in ("list", "steps"):
                items = b.get("items", [])
                need(isinstance(items, list) and len(items) >= 2 and all(isinstance(i, str) for i in items),
                     f"{bw}: needs >=2 string items")
                total_words += sum(words(i) for i in items if isinstance(i, str))
            elif t == "code":
                n_code += 1
                need(isinstance(b.get("lang"), str) and b["lang"], f"{bw}: code needs 'lang'")
                need(isinstance(b.get("code"), str) and b["code"].strip(), f"{bw}: empty code")
                if isinstance(b.get("code"), str):
                    e = lint_code(b.get("lang"), b["code"])
                    if e:
                        errs.append(f"{bw}: code does not parse -> {e}")
                    if max((len(l) for l in b["code"].splitlines()), default=0) > 100:
                        warns.append(f"{bw}: code line longer than 100 chars (will scroll on mobile)")
            elif t == "callout":
                need(b.get("kind") in CALLOUT_KINDS, f"{bw}: kind must be one of {sorted(CALLOUT_KINDS)}")
                need(isinstance(b.get("text"), str) and b["text"].strip(), f"{bw}: empty text")
                total_words += words(b.get("text"))
            elif t == "table":
                hdr, rows = b.get("headers", []), b.get("rows", [])
                need(isinstance(hdr, list) and 2 <= len(hdr) <= 4, f"{bw}: table needs 2-4 headers")
                need(isinstance(rows, list) and rows and all(isinstance(r, list) and len(r) == len(hdr) for r in rows),
                     f"{bw}: every row must have {len(hdr)} cells")
    need(total_words >= 550, f"lesson is too thin: {total_words} words of prose (need >= 550)")
    if total_words > 1500:
        warns.append(f"lesson is long: {total_words} words (aim for 700-1200)")
    need(n_code >= 1, "lesson needs at least one code/config example")

    pr = m.get("practice", {})
    need(isinstance(pr, dict) and isinstance(pr.get("title"), str) and pr.get("title"), "'practice.title' missing")
    need(isinstance(pr.get("steps"), list) and 3 <= len(pr.get("steps", [])) <= 8, "'practice.steps' needs 3-8 steps")

    cs = m.get("cheatsheet", {})
    focus = cs.get("focus", [])
    need(isinstance(focus, list) and 4 <= len(focus) <= 8, "'cheatsheet.focus' needs 4-8 items")
    groups = cs.get("groups", [])
    need(isinstance(groups, list) and 3 <= len(groups) <= 6, "'cheatsheet.groups' needs 3-6 groups")
    n_items = 0
    for gi, g in enumerate(groups if isinstance(groups, list) else []):
        need(isinstance(g.get("title"), str) and g["title"], f"cheatsheet.groups[{gi}]: missing title")
        items = g.get("items", [])
        need(isinstance(items, list) and 3 <= len(items) <= 10, f"cheatsheet.groups[{gi}]: needs 3-10 items")
        for ii, it in enumerate(items if isinstance(items, list) else []):
            need(isinstance(it.get("syntax"), str) and it["syntax"].strip() and isinstance(it.get("desc"), str)
                 and it["desc"].strip(), f"cheatsheet.groups[{gi}].items[{ii}]: needs 'syntax' and 'desc'")
            n_items += 1
    need(n_items >= 15, f"cheat sheet needs >= 15 entries in total (has {n_items})")
    pit = cs.get("pitfalls", [])
    need(isinstance(pit, list) and 3 <= len(pit) <= 6, "'cheatsheet.pitfalls' needs 3-6 items")

    quiz = m.get("quiz", [])
    need(isinstance(quiz, list) and len(quiz) == 5, "'quiz' needs exactly 5 questions")
    longest_is_right = 0
    for qi, q in enumerate(quiz if isinstance(quiz, list) else []):
        where = f"quiz[{qi}]"
        opts = q.get("options", [])
        need(isinstance(q.get("q"), str) and q["q"].strip(), f"{where}: missing question")
        ok_opts = isinstance(opts, list) and len(opts) == 4 and all(isinstance(o, str) and o.strip() for o in opts)
        need(ok_opts, f"{where}: needs exactly 4 non-empty options")
        need(isinstance(q.get("answer"), int) and not isinstance(q.get("answer"), bool) and 0 <= q["answer"] <= 3,
             f"{where}: 'answer' must be an index 0-3")
        need(isinstance(q.get("explain"), str) and words(q.get("explain")) >= 8, f"{where}: 'explain' needs >= 8 words")
        if ok_opts:
            need(len(set(o.strip().lower() for o in opts)) == 4, f"{where}: duplicate options")
            for o in opts:
                if any(bad in o.lower() for bad in BANNED_OPTIONS):
                    errs.append(f"{where}: options are shuffled at runtime, so {o!r} is not allowed")
            if isinstance(q.get("answer"), int) and 0 <= q["answer"] <= 3:
                if len(opts[q["answer"]]) == max(len(o) for o in opts) and \
                        sorted(len(o) for o in opts)[-1] > 1.35 * sorted(len(o) for o in opts)[-2]:
                    longest_is_right += 1
    if longest_is_right >= 3:
        warns.append(f"in {longest_is_right}/5 questions the correct option is clearly the longest - "
                     "rebalance option lengths so the answer can't be guessed")
    return errs, warns


# ---------------------------------------------------------------- rendering

def inline(text):
    """Escape HTML, then apply the two inline marks we allow: `code` and **bold**."""
    out = html.escape(text, quote=False)
    out = re.sub(r"`([^`]+)`", r"<code>\1</code>", out)
    out = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", out)
    return out


def render_block(b):
    t = b["type"]
    if t == "p":
        return f"<p>{inline(b['text'])}</p>"
    if t in ("list", "steps"):
        tag = "ol" if t == "steps" else "ul"
        return f"<{tag}>" + "".join(f"<li>{inline(i)}</li>" for i in b["items"]) + f"</{tag}>"
    if t == "code":
        cap = f'<div class="code-cap">{inline(b["caption"])}</div>' if b.get("caption") else ""
        return (f'<div class="code">{cap}<div class="code-head"><span>{html.escape(b["lang"])}</span>'
                f'<button type="button" class="copy" data-copy>Copy</button></div>'
                f'<pre><code>{html.escape(b["code"].rstrip(), quote=False)}</code></pre></div>')
    if t == "callout":
        label = {"tip": "Tip", "warning": "Watch out", "note": "Note"}[b["kind"]]
        return f'<div class="callout callout-{b["kind"]}"><strong>{label}</strong><p>{inline(b["text"])}</p></div>'
    if t == "table":
        head = "".join(f"<th>{inline(h)}</th>" for h in b["headers"])
        rows = "".join("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in r) + "</tr>" for r in b["rows"])
        return f'<div class="table-wrap"><table><thead><tr>{head}</tr></thead><tbody>{rows}</tbody></table></div>'
    raise ValueError(t)


def slug(text):
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{title} — {track_short} | ThavionAI Education</title>
  <meta name="description" content="{desc_attr}" />
  <meta property="og:title" content="{title_attr} — ThavionAI Education" />
  <meta property="og:description" content="{desc_attr}" />
  <meta property="og:type" content="article" />
  <meta property="og:image" content="https://thavionai.com/assets/og-education.png" />
  <meta property="og:image:width" content="1200" />
  <meta property="og:image:height" content="630" />
  <meta name="twitter:card" content="summary_large_image" />
  <link rel="canonical" href="https://thavionai.com/education/{id}.html" />
  <link rel="icon" href="../assets/favicon.ico" sizes="any" />
  <link rel="icon" type="image/png" sizes="32x32" href="../assets/logo-32.png" />
  <link rel="apple-touch-icon" href="../assets/apple-touch-icon.png" />
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet" />
  <link rel="stylesheet" href="lesson.css" />
</head>
<body class="track-{track}" data-module="{id}">

<nav>
  <a href="../index.html" class="nav-logo"><img class="nav-logo-icon" src="../assets/logo.png" alt="" width="32" height="32" />ThavionAI</a>
  <div class="nav-links" id="navLinks">
    <a href="../education.html" class="active">Tracks</a>
    <a href="../index.html#projects">Projects</a>
    <a href="../education.html#certs">Certifications</a>
    <a href="../index.html#apps">Apps</a>
    <a href="../feedback.html?module={id}&amp;page=/education/{id}.html&amp;title={title_q}">Feedback</a>
    <a href="../education.html#{track}" class="nav-cta">All {track_short} modules</a>
  </div>
  <div class="hamburger" id="hamburger"><span></span><span></span><span></span></div>
</nav>

<header class="lesson-hero">
  <div class="wrap">
    <div class="crumbs"><a href="../education.html">Education</a> › <a href="../education.html#{track}">{track_short}</a> › Stage {stage_num}: {stage_title}</div>
    <h1>{title}</h1>
    <p class="lede">{desc}</p>
    <div class="meta">
      <span class="chip">{level}</span>
      <span class="chip">~{minutes} min read</span>
      <span class="chip">Module {pos} of {total}</span>
      <span class="chip chip-quiz" data-quiz-badge hidden></span>
    </div>
  </div>
</header>

<div class="subnav" id="subnav">
  <div class="wrap">
    <a href="#lesson" class="on">Lesson</a>
    <a href="#practice">Practice</a>
    <a href="#cheatsheet">Cheat sheet</a>
    <a href="#quiz">Quiz</a>
  </div>
</div>

<main class="wrap">
  <article id="lesson" class="lesson">
    <p class="intro">{intro}</p>
    <div class="objectives">
      <div class="box-label">After this module you can</div>
      <ul>{objectives}</ul>
    </div>
    {sections}
  </article>

  <section id="practice" class="panel practice">
    <div class="box-label">Hands-on practice</div>
    <h2>{practice_title}</h2>
    <ol>{practice_steps}</ol>
  </section>

  <section id="cheatsheet" class="panel cheats">
    <div class="panel-head">
      <div>
        <div class="box-label">Cheat sheet</div>
        <h2>{title} — at a glance</h2>
      </div>
      <button type="button" class="ghost" data-print>Print cheat sheet</button>
    </div>
    <div class="focus">
      <h3>Main things to focus on</h3>
      <ul>{focus}</ul>
    </div>
    <div class="cheat-grid">{groups}</div>
    <div class="pitfalls">
      <h3>Common pitfalls</h3>
      <ul>{pitfalls}</ul>
    </div>
  </section>

  <section id="quiz" class="panel quiz">
    <div class="box-label">Quiz</div>
    <h2>Check your understanding</h2>
    <p class="quiz-sub">5 questions · 4 to pass · answers are explained as you go. Your best score is saved on this device only.</p>
    <noscript><p class="quiz-sub">The quiz needs JavaScript enabled.</p></noscript>
    <div id="quizRoot"></div>
    <script type="application/json" id="quizData">{quiz_json}</script>
  </section>

  <section class="done-row">
    <label class="done"><input type="checkbox" id="doneBox" /> <span>Mark this module complete</span></label>
    <p class="save-hint">Progress and quiz scores are saved in this browser only. <a href="../education.html#progressPanel">Back up or restore</a> on the hub.</p>
  </section>

  <nav class="pager" aria-label="Module navigation">
    {prev_link}
    <a class="pager-up" href="../education.html#{track}">All {track_short} modules</a>
    {next_link}
  </nav>

  <p class="feedback-row">Was this lesson useful? <a href="../feedback.html?module={id}&amp;page=/education/{id}.html&amp;title={title_q}">Tell me what to improve →</a></p>
</main>

<footer>
  <div class="wrap footer-row">
    <p>© 2025–2026 ThavionAI. All rights reserved.</p>
    <div class="footer-legal">
      <a href="../education.html">Education</a>
      <a href="../privacy.html">Privacy</a>
      <a href="../terms.html">Terms</a>
      <a href="../feedback.html?module={id}&amp;page=/education/{id}.html&amp;title={title_q}">Report an error</a>
    </div>
  </div>
</footer>

<script src="lesson.js"></script>
</body>
</html>
"""


def load_diagrams(mod_id, n_sections, section_lengths):
    """Diagrams live beside the module: site-src/education/diagrams/<id>.json (a list). Returns (specs, errors)."""
    path = SRC / "diagrams" / f"{mod_id}.json"
    if not path.exists():
        return [], []
    try:
        specs = json.loads(path.read_text())
    except ValueError as e:
        return [], [f"diagrams file is invalid JSON - {e}"]
    errs = []
    if not isinstance(specs, list):
        return [], ["diagrams file must contain a list"]
    seen = set()
    for i, d in enumerate(specs):
        where = f"diagram[{i}]"
        errs += diagrams.validate(d, where)
        if d.get("id") in seen:
            errs.append(f"{where}: duplicate diagram id {d.get('id')!r}")
        seen.add(d.get("id"))
        place = d.get("place", {})
        si, after = place.get("section"), place.get("after")
        if isinstance(si, int) and isinstance(after, int):
            if not 0 <= si < n_sections:
                errs.append(f"{where}: place.section {si} is out of range (module has {n_sections} sections)")
            elif not -1 <= after < section_lengths[si]:
                errs.append(f"{where}: place.after {after} is out of range for section {si}")
    return specs, errs


def render(m, ctx, figures=()):
    placed = {}
    for d in figures:
        placed.setdefault((d["place"]["section"], d["place"]["after"]), []).append(diagrams.render(d))
    sections = []
    for si, s in enumerate(m["sections"]):
        pieces = list(placed.get((si, -1), []))
        for bi, b in enumerate(s["blocks"]):
            pieces.append(render_block(b))
            pieces += placed.get((si, bi), [])
        body = "\n    ".join(pieces)
        sections.append(f'<section id="{slug(s["heading"])}"><h2>{inline(s["heading"])}</h2>\n    {body}</section>')
    groups = []
    for g in m["cheatsheet"]["groups"]:
        rows = "".join(
            f'<tr><td><code>{html.escape(i["syntax"], quote=False)}</code></td><td>{inline(i["desc"])}</td></tr>'
            for i in g["items"])
        groups.append(f'<div class="cheat-group"><h3>{inline(g["title"])}</h3><table><tbody>{rows}</tbody></table></div>')

    def pager(mod, cls, label):
        if not mod:
            return f'<span class="pager-link {cls} is-empty"></span>'
        return (f'<a class="pager-link {cls}" href="{mod["id"]}.html"><span>{label}</span>'
                f'<strong>{html.escape(mod["title"], quote=False)}</strong></a>')

    quiz_json = json.dumps(m["quiz"], ensure_ascii=False).replace("</", "<\\/")
    return PAGE.format(
        id=m["id"], track=ctx["track"]["id"], track_short=html.escape(ctx["track"]["short"]),
        title=html.escape(ctx["mod"]["title"], quote=False), title_attr=html.escape(ctx["mod"]["title"]), title_q=quote(ctx["mod"]["title"]),
        desc=html.escape(ctx["mod"]["desc"], quote=False), desc_attr=html.escape(ctx["mod"]["desc"]),
        stage_num=ctx["stage"]["num"], stage_title=html.escape(ctx["stage"]["title"], quote=False),
        level=html.escape(ctx["stage"]["level"]), minutes=m["minutes"], pos=ctx["pos"], total=ctx["total"],
        intro=inline(m["intro"]),
        objectives="".join(f"<li>{inline(o)}</li>" for o in m["objectives"]),
        sections="\n  ".join(sections),
        practice_title=inline(m["practice"]["title"]),
        practice_steps="".join(f"<li>{inline(s)}</li>" for s in m["practice"]["steps"]),
        focus="".join(f"<li>{inline(f)}</li>" for f in m["cheatsheet"]["focus"]),
        groups="".join(groups),
        pitfalls="".join(f"<li>{inline(p)}</li>" for p in m["cheatsheet"]["pitfalls"]),
        quiz_json=quiz_json,
        prev_link=pager(ctx["prev"], "pager-prev", "← Previous"),
        next_link=pager(ctx["next"], "pager-next", "Next →"),
    )


# ---------------------------------------------------------------- main

def main(argv):
    check_only = "--check" in argv
    strict = "--strict" in argv
    wanted = [a for a in argv if not a.startswith("--")]

    tracks = json.loads((SRC / "tracks.json").read_text())["tracks"]
    index = {}
    for t in tracks:
        flat = [(s, mod) for s in t["stages"] for mod in s["modules"]]
        # prev/next only link to modules that have content, so a half-written track never 404s
        live = [mod for _, mod in flat if (SRC / "modules" / f"{mod['id']}.json").exists()]
        for i, (s, mod) in enumerate(flat):
            k = next((j for j, l in enumerate(live) if l["id"] == mod["id"]), None)
            index[mod["id"]] = {"track": t, "stage": s, "mod": mod, "pos": i + 1, "total": len(flat),
                                "prev": live[k - 1] if k else None,
                                "next": live[k + 1] if k is not None and k + 1 < len(live) else None}

    ids = wanted or list(index)
    failed = built = missing = 0
    for mod_id in ids:
        if mod_id not in index:
            print(f"FAIL {mod_id}: not listed in tracks.json")
            failed += 1
            continue
        path = SRC / "modules" / f"{mod_id}.json"
        if not path.exists():
            # tracks marked "building" in tracks.json are allowed to be incomplete, even under --strict
            if index[mod_id]["track"].get("status", "live") == "live":
                missing += 1
                if wanted or strict:
                    print(f"MISSING {mod_id}: {path.relative_to(ROOT)} does not exist")
            continue
        try:
            m = json.loads(path.read_text())
        except ValueError as e:
            print(f"FAIL {mod_id}: invalid JSON - {e}")
            failed += 1
            continue
        errs, warns = validate(mod_id, m)
        figures, fig_errs = load_diagrams(
            mod_id, len(m.get("sections", [])),
            [len(s.get("blocks", [])) for s in m.get("sections", []) if isinstance(s, dict)])
        errs += fig_errs
        for w in warns:
            print(f"warn {mod_id}: {w}")
        if errs:
            failed += 1
            print(f"FAIL {mod_id}:")
            for e in errs:
                print(f"   - {e}")
            continue
        if check_only:
            print(f"OK   {mod_id}")
        else:
            OUT.mkdir(parents=True, exist_ok=True)
            (OUT / f"{mod_id}.html").write_text(render(m, index[mod_id], figures))
            built += 1
    if not check_only:
        print(f"built {built} page(s) -> {OUT.relative_to(ROOT)}/   ({missing} module(s) have no content yet)")
    if failed or (missing and (strict or wanted)):
        sys.exit(1)


if __name__ == "__main__":
    main(sys.argv[1:])
