#!/usr/bin/env python3
"""Build the School world: subject lessons + the school hub.

Sources:
  site-src/school/subjects.json         subjects (id, name, emoji, accent, blurb)
  site-src/school/lessons/<id>.json      one lesson each
  site-src/site/school.html              hub template (with {{SUBJECT_SECTIONS}})

Outputs:
  docs/school/<id>.html                  lesson pages (interactive practice, tick-as-you-go)
  docs/school.html                       the hub, listing subjects and their lessons

Lesson JSON schema:
  { id, subject, title, grade, minutes, intro,
    sections: [ { heading, body:[para,...], example?: {problem, steps:[...], answer} } ],
    practice: [ { q, options:[4], answer:int, explain } ],
    summary: [ point, ... ] }

Usage:  python3 scripts/build_school.py [--check ID ...]
"""
import html
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "site-src" / "school"
SITE = ROOT / "site-src" / "site"
OUT = ROOT / "docs"
LOUT = OUT / "school"

esc = html.escape


def inline(text):
    """Escape HTML, then render **bold** and `code` and $math$ (kept literal in <span>)."""
    t = esc(text)
    t = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", t)
    t = re.sub(r"`(.+?)`", r"<code>\1</code>", t)
    return t


def validate(lid, lesson, subject_ids):
    errs = []
    need = lambda c, m: None if c else errs.append(m)  # noqa: E731
    need(lesson.get("id") == lid, f"'id' must equal the filename ({lid})")
    need(lesson.get("subject") in subject_ids, f"'subject' must be one of {sorted(subject_ids)}")
    for k in ("title", "grade", "intro"):
        need(lesson.get(k), f"'{k}' missing")
    need(isinstance(lesson.get("minutes"), int) and 5 <= lesson["minutes"] <= 60, "'minutes' must be 5-60")
    secs = lesson.get("sections", [])
    need(isinstance(secs, list) and 2 <= len(secs) <= 8, "'sections' needs 2-8 entries")
    words = len((lesson.get("intro") or "").split())
    for i, s in enumerate(secs if isinstance(secs, list) else []):
        need(s.get("heading"), f"sections[{i}]: missing heading")
        body = s.get("body", [])
        need(isinstance(body, list) and body and all(isinstance(p, str) for p in body), f"sections[{i}]: body needs paragraphs")
        words += sum(len(p.split()) for p in body if isinstance(p, str))
        ex = s.get("example")
        if ex:
            need(ex.get("problem") and isinstance(ex.get("steps"), list) and ex["steps"] and ex.get("answer"),
                 f"sections[{i}].example: needs problem, steps, answer")
    need(words >= 250, f"lesson is thin: {words} words (need >= 250)")
    pr = lesson.get("practice", [])
    need(isinstance(pr, list) and 2 <= len(pr) <= 8, "'practice' needs 2-8 questions")
    for i, q in enumerate(pr if isinstance(pr, list) else []):
        need(q.get("q"), f"practice[{i}]: missing q")
        opts = q.get("options", [])
        need(isinstance(opts, list) and len(opts) == 4, f"practice[{i}]: needs 4 options")
        need(isinstance(q.get("answer"), int) and 0 <= q.get("answer", -1) < 4, f"practice[{i}]: answer must be 0-3")
        need(q.get("explain"), f"practice[{i}]: missing explain")
    need(isinstance(lesson.get("summary"), list) and len(lesson.get("summary", [])) >= 2, "'summary' needs >= 2 points")
    return errs


LESSON_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <link rel="icon" href="../assets/favicon.ico" sizes="any" />
  <link rel="icon" type="image/png" sizes="32x32" href="../assets/logo-32.png" />
  <link rel="apple-touch-icon" href="../assets/apple-touch-icon.png" />
  <title>{title} — {subject_name} | ThavionAI School</title>
  <meta name="description" content="{desc}" />
  <meta property="og:title" content="{title} — ThavionAI School" />
  <meta property="og:description" content="{desc}" />
  <meta property="og:type" content="article" />
  <meta property="og:url" content="https://thavionai.com/school/{id}.html" />
  <meta property="og:image" content="https://thavionai.com/assets/og-image.png" />
  <meta name="twitter:card" content="summary_large_image" />
  <link rel="canonical" href="https://thavionai.com/school/{id}.html" />
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet" />
  <link rel="stylesheet" href="../site.css" />
  <link rel="stylesheet" href="../guide.css" />
  <style>
    .doc .example {{ background: var(--surface); border: 1px solid var(--border); border-left: 3px solid var(--sc, var(--accent)); border-radius: 12px; padding: 16px 18px; margin: 16px 0; }}
    .doc .example .lbl {{ font-size: 12px; font-weight: 700; letter-spacing: 0.08em; text-transform: uppercase; color: var(--sc, var(--accent)); margin-bottom: 6px; }}
    .doc .example .prob {{ font-weight: 700; color: var(--text); margin-bottom: 8px; }}
    .doc .example ol {{ margin: 0 0 8px 0; }}
    .doc .example .ans {{ font-weight: 700; color: var(--text); }}
    .sc-q {{ background: var(--surface); border: 1px solid var(--border); border-radius: 12px; padding: 16px 18px; margin-bottom: 12px; }}
    .sc-q .qt {{ font-weight: 600; margin-bottom: 10px; }}
    .sc-opt {{ display: block; width: 100%; text-align: left; font: inherit; font-size: 14.5px; color: var(--text); background: var(--bg); border: 1.5px solid var(--border); border-radius: 10px; padding: 10px 12px; margin-bottom: 8px; cursor: pointer; }}
    .sc-opt:hover:not(:disabled) {{ border-color: var(--sc, var(--accent)); }}
    .sc-opt.right {{ border-color: #16a34a; background: rgba(22,163,74,0.10); }}
    .sc-opt.wrong {{ border-color: #e11d48; background: rgba(225,29,72,0.08); }}
    .sc-exp {{ font-size: 13.5px; color: var(--text2); margin-top: 6px; display: none; }}
    .sc-exp.show {{ display: block; }}
    .sc-done {{ display: flex; align-items: center; gap: 10px; margin-top: 24px; padding: 14px 16px; border: 1px solid var(--border); border-radius: 12px; background: var(--surface); }}
    .sc-done button {{ font: inherit; font-weight: 600; cursor: pointer; border-radius: 9px; border: 1px solid var(--sc, var(--accent)); background: var(--sc, var(--accent)); color: #fff; padding: 9px 16px; }}
    .sc-done.ok {{ border-color: #16a34a; }}
  </style>
</head>
<body class="theme-light theme-school">

<nav class="site-nav">
  <div class="nav-inner">
    <a href="../index.html" class="nav-logo"><img src="../assets/logo.png" alt="" /><span>ThavionAI<small>Learn. Build. Ship.</small></span></a>
    <button class="nav-toggle" aria-label="Menu" aria-expanded="false" aria-controls="navLinks" onclick="toggleNav()">
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="4" y1="7" x2="20" y2="7"/><line x1="4" y1="12" x2="20" y2="12"/><line x1="4" y1="17" x2="20" y2="17"/></svg>
    </button>
    <div class="nav-links" id="navLinks">
      <a href="../index.html">Home</a>
      <a href="../engineering.html">Engineering</a>
      <a href="../exams.html">Exams &amp; Admissions</a>
      <a href="../school.html">School</a>
      <a href="../careers.html">Careers</a>
    </div>
  </div>
</nav>

<div class="doc" style="--sc:{accent}">
  <section class="doc-hero">
    <div class="crumbs"><a href="../index.html">Home</a> › <a href="../school.html">School</a> › {subject_name}</div>
    <span class="chip"><span class="dot"></span> {grade} · about {minutes} min · Free</span>
    <h1>{title}</h1>
    <p class="lead">{intro}</p>
  </section>
{sections}
  <h2>Check yourself</h2>
  <p>Try these. Pick an answer to see whether it's right and why.</p>
  <div id="practice">
{practice}
  </div>

  <h2>In a nutshell</h2>
  <ul>
{summary}
  </ul>

  <div class="sc-done" id="doneBox">
    <span id="doneText" style="flex:1;color:var(--text2);font-size:14px">Finished? Mark this lesson done — it's saved in this browser.</span>
    <button id="doneBtn">Mark done</button>
  </div>

  <div class="related">
    <h4>More {subject_name}</h4>
    {siblings}
    <a href="../school.html">All subjects →</a>
  </div>
</div>

<footer class="site-footer">
  <div class="max-w">
    <div class="footer-grid">
      <div class="footer-brand">
        <a href="../index.html" class="nav-logo"><img src="../assets/logo.png" alt="" /><span>ThavionAI</span></a>
        <p>Free education for everyone. Learn. Build. Ship.</p>
      </div>
      <div class="footer-col"><h4>Learn</h4>
        <a href="../engineering.html">Engineering</a>
        <a href="../exams.html">Exams &amp; Admissions</a>
        <a href="../school.html">School</a>
      </div>
      <div class="footer-col"><h4>School</h4>
        <a href="../school.html#maths">Maths</a>
        <a href="../school.html#science">Science</a>
        <a href="../school.html#english">English</a>
      </div>
      <div class="footer-col"><h4>Company</h4>
        <a href="../index.html#about">About</a>
        <a href="../feedback.html">Feedback</a>
        <a href="../privacy.html">Privacy</a>
        <a href="../terms.html">Terms</a>
      </div>
    </div>
    <div class="footer-bottom">
      <span>© 2025–2026 ThavionAI. All rights reserved.</span>
      <span><a href="../privacy.html">Privacy</a><a href="../terms.html">Terms</a><a href="../feedback.html">Feedback</a></span>
    </div>
  </div>
</footer>

<script>
  document.documentElement.classList.add('js');
  function toggleNav() {{
    var n = document.getElementById('navLinks'); var open = n.classList.toggle('open');
    document.querySelector('.nav-toggle').setAttribute('aria-expanded', open ? 'true' : 'false');
  }}
  document.querySelectorAll('#navLinks a').forEach(function (a) {{ a.addEventListener('click', function () {{ document.getElementById('navLinks').classList.remove('open'); }}); }});

  document.querySelectorAll('.sc-q').forEach(function (q) {{
    var ans = +q.dataset.answer;
    var opts = q.querySelectorAll('.sc-opt');
    opts.forEach(function (o, i) {{
      o.addEventListener('click', function () {{
        opts.forEach(function (x) {{ x.disabled = true; }});
        opts[ans].classList.add('right');
        if (i !== ans) o.classList.add('wrong');
        q.querySelector('.sc-exp').classList.add('show');
      }});
    }});
  }});

  var KEY = 'thavionai-school';
  var LID = '{id}';
  function load() {{ try {{ return JSON.parse(localStorage.getItem(KEY)) || {{}}; }} catch (e) {{ return {{}}; }} }}
  function save(s) {{ try {{ localStorage.setItem(KEY, JSON.stringify(s)); }} catch (e) {{}} }}
  var done = load();
  function reflect() {{
    var box = document.getElementById('doneBox');
    if (done[LID]) {{ box.classList.add('ok'); document.getElementById('doneText').textContent = '✓ You marked this lesson done.'; document.getElementById('doneBtn').textContent = 'Undo'; }}
    else {{ box.classList.remove('ok'); document.getElementById('doneText').textContent = "Finished? Mark this lesson done — it's saved in this browser."; document.getElementById('doneBtn').textContent = 'Mark done'; }}
  }}
  document.getElementById('doneBtn').addEventListener('click', function () {{ done[LID] = !done[LID]; save(done); reflect(); }});
  reflect();
</script>
</body>
</html>
"""


def render_sections(sections):
    out = []
    for s in sections:
        parts = [f'  <h2>{esc(s["heading"])}</h2>']
        for p in s.get("body", []):
            parts.append(f"  <p>{inline(p)}</p>")
        ex = s.get("example")
        if ex:
            steps = "".join(f"<li>{inline(st)}</li>" for st in ex["steps"])
            parts.append(
                '  <div class="example"><div class="lbl">Worked example</div>'
                f'<div class="prob">{inline(ex["problem"])}</div>'
                f"<ol>{steps}</ol>"
                f'<div class="ans">Answer: {inline(ex["answer"])}</div></div>'
            )
        out.append("\n".join(parts))
    return "\n".join(out)


def render_practice(practice):
    out = []
    letters = ["A", "B", "C", "D"]
    for q in practice:
        opts = "".join(
            f'<button class="sc-opt">{letters[i]}. {esc(o)}</button>'
            for i, o in enumerate(q["options"])
        )
        out.append(
            f'    <div class="sc-q" data-answer="{q["answer"]}">'
            f'<div class="qt">{inline(q["q"])}</div>{opts}'
            f'<div class="sc-exp">{inline(q["explain"])}</div></div>'
        )
    return "\n".join(out)


def build(check=None):
    subjects = json.loads((SRC / "subjects.json").read_text())["subjects"]
    subj_by_id = {s["id"]: s for s in subjects}
    lesson_files = sorted((SRC / "lessons").glob("*.json"))
    lessons = []
    failed = 0
    for f in lesson_files:
        lid = f.stem
        if check and lid not in check:
            pass
        data = json.loads(f.read_text())
        errs = validate(lid, data, set(subj_by_id))
        if errs:
            failed += 1
            print(f"FAIL {lid}:")
            for e in errs:
                print(f"   - {e}")
            continue
        lessons.append(data)
        if check:
            print(f"OK   {lid}")
    if check:
        return failed == 0
    if failed:
        print(f"\n{failed} lesson(s) failed — not building.")
        return False

    LOUT.mkdir(parents=True, exist_ok=True)
    by_subject = {s["id"]: [] for s in subjects}
    for les in lessons:
        by_subject[les["subject"]].append(les)

    # lesson pages
    for les in lessons:
        subj = subj_by_id[les["subject"]]
        sibs = [l for l in by_subject[les["subject"]] if l["id"] != les["id"]][:3]
        siblings = "".join(f'<a href="{l["id"]}.html">{esc(l["title"])}</a>' for l in sibs)
        desc = esc(les["intro"][:150])
        page = LESSON_PAGE.format(
            id=les["id"], title=esc(les["title"]), subject_name=esc(subj["name"]),
            accent=subj["accent"], grade=esc(les["grade"]), minutes=les["minutes"],
            intro=esc(les["intro"]), desc=desc,
            sections=render_sections(les["sections"]),
            practice=render_practice(les["practice"]),
            summary="".join(f"    <li>{inline(pt)}</li>\n" for pt in les["summary"]),
            siblings=siblings,
        )
        (LOUT / f"{les['id']}.html").write_text(page)

    # hub
    sections_html = []
    for s in subjects:
        items = by_subject.get(s["id"], [])
        if items:
            cards = "\n".join(
                f'        <a class="module-body" href="school/{l["id"]}.html" style="border-left:3px solid {s["accent"]}">'
                f'<span class="t" style="font-weight:700">{esc(l["title"])}</span>'
                f'<span class="d" style="display:block;color:var(--text3);font-size:13px;margin-top:2px">{esc(l["grade"])} · {esc(l["intro"][:90])}…</span></a>'
                for l in items
            )
            lessons_block = f'      <div class="stage-modules" style="display:flex;flex-direction:column;gap:8px;margin-top:14px">\n{cards}\n      </div>'
        else:
            lessons_block = '      <p class="soon" style="margin-top:14px">Lessons publishing soon.</p>'
        sections_html.append(
            f'    <div class="stage" id="{s["id"]}" style="--tc:{s["accent"]}">\n'
            f'      <div style="display:flex;align-items:center;gap:12px">'
            f'<span style="font-size:30px">{s["emoji"]}</span>'
            f'<div><h3 style="margin:0;font-size:20px">{esc(s["name"])}</h3>'
            f'<p style="margin:2px 0 0;color:var(--text2);font-size:14px">{esc(s["blurb"])}</p></div></div>\n'
            f"{lessons_block}\n"
            f"    </div>"
        )
    total = len(lessons)
    hub_tmpl = (SITE / "school.html").read_text()
    hub = hub_tmpl.replace("{{SUBJECT_SECTIONS}}", "\n".join(sections_html)).replace("{{SCHOOL_COUNT}}", str(total))
    (OUT / "school.html").write_text(hub)
    print(f"built {total} school lesson(s) across {len(subjects)} subjects -> docs/school/")
    return True


if __name__ == "__main__":
    args = sys.argv[1:]
    if args and args[0] == "--check":
        ok = build(check=set(args[1:]) or None)
        sys.exit(0 if ok else 1)
    sys.exit(0 if build() else 1)
