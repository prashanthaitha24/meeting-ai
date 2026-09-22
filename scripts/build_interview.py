#!/usr/bin/env python3
"""Build the interview prep kit pages: site-src/education/interview/<id>.json -> docs/education/interview/<id>.html

A kit is a role's interview guide: the rounds you will face, sections of questions (each with what it tests
and a model answer revealed on click), a take-home style task, how to stand out, and links back to the
tracks and projects that prepare you. Model answers are in <details> so the page is a self-test.

Usage:  python3 scripts/build_interview.py [--check ID ...]
"""
import html
import json
import sys
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "site-src" / "education"
OUT = ROOT / "docs" / "education" / "interview"
sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_education import inline, lint_code  # noqa: E402

esc = html.escape


def validate(kid, k, track_ids):
    errs = []
    need = lambda c, m: None if c else errs.append(m)  # noqa: E731
    need(k.get("id") == kid, f"'id' must equal the filename ({kid})")
    for key in ("role", "summary"):
        need(k.get(key), f"'{key}' missing")
    need(isinstance(k.get("tracks"), list) and k["tracks"], "'tracks' needs items")
    for t in k.get("tracks", []):
        need(t in track_ids, f"tracks references unknown track {t!r}")
    rounds = k.get("rounds", [])
    need(isinstance(rounds, list) and 3 <= len(rounds) <= 8, "'rounds' needs 3-8 entries")
    for i, r in enumerate(rounds):
        need(r.get("name") and r.get("what"), f"rounds[{i}]: needs name and what")
    sections = k.get("sections", [])
    need(isinstance(sections, list) and 3 <= len(sections) <= 8, "'sections' needs 3-8 sections")
    n_q = 0
    for si, s in enumerate(sections):
        need(s.get("title"), f"sections[{si}]: needs a title")
        qs = s.get("questions", [])
        need(isinstance(qs, list) and 3 <= len(qs) <= 8, f"sections[{si}]: needs 3-8 questions")
        for qi, q in enumerate(qs):
            n_q += 1
            need(q.get("q") and q.get("tests") and q.get("answer"),
                 f"sections[{si}].questions[{qi}]: needs q, tests, answer")
            if q.get("code"):
                c = q["code"]
                need(c.get("lang") and c.get("code"), f"sections[{si}].questions[{qi}]: code needs lang and code")
                if c.get("lang") and c.get("code"):
                    e = lint_code(c["lang"], c["code"])
                    if e:
                        errs.append(f"sections[{si}].questions[{qi}]: code does not parse -> {e}")
    need(n_q >= 20, f"kit needs >= 20 questions in total (has {n_q})")
    task = k.get("task", {})
    need(task.get("title") and task.get("brief") and isinstance(task.get("checklist"), list) and task["checklist"],
         "'task' needs title, brief and a checklist")
    need(isinstance(k.get("standout"), list) and len(k["standout"]) >= 3, "'standout' needs >= 3 items")
    need(isinstance(k.get("resources"), list) and k["resources"], "'resources' needs items")
    return errs, n_q


PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{role} interview prep | ThavionAI Education</title>
  <meta name="description" content="{summary_attr}" />
  <meta property="og:title" content="{role_attr} interview prep — ThavionAI" />
  <meta property="og:description" content="{summary_attr}" />
  <meta property="og:type" content="article" />
  <meta property="og:image" content="https://thavionai.com/assets/og-education.png" />
  <meta property="og:image:width" content="1200" />
  <meta property="og:image:height" content="630" />
  <meta name="twitter:card" content="summary_large_image" />
  <link rel="canonical" href="https://thavionai.com/education/interview/{id}.html" />
  <link rel="icon" href="../../assets/favicon.ico" sizes="any" />
  <link rel="icon" type="image/png" sizes="32x32" href="../../assets/logo-32.png" />
  <link rel="apple-touch-icon" href="../../assets/apple-touch-icon.png" />
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet" />
  <link rel="stylesheet" href="../lesson.css" />
  <link rel="stylesheet" href="../projects/project.css" />
  <link rel="stylesheet" href="interview.css" />
</head>
<body class="track-{track}" data-kit="{id}">

<nav>
  <a href="../../index.html" class="nav-logo"><img class="nav-logo-icon" src="../../assets/logo.png" alt="" width="32" height="32" />ThavionAI</a>
  <div class="nav-links" id="navLinks">
    <a href="../../index.html">Home</a>
    <a href="../../education.html">Tracks</a>
    <a href="../../engineering.html#projects">Projects</a>
    <a href="../../engineering.html#interview" class="active">Interview prep</a>
    <a href="../../education.html#certs">Certifications</a>
    <a href="../../feedback.html?page=/education/interview/{id}.html&amp;title={role_q}">Feedback</a>
    <a href="../../education.html#{track}" class="nav-cta">{track_short} track</a>
  </div>
  <div class="hamburger" id="hamburger"><span></span><span></span><span></span></div>
</nav>

<header class="lesson-hero">
  <div class="wrap">
    <div class="crumbs"><a href="../../education.html">Education</a> › <a href="../../engineering.html#interview">Interview prep</a> › {role}</div>
    <h1>{role} — interview prep kit</h1>
    <p class="lede">{summary}</p>
    <div class="meta">
      <span class="chip">{n_sections} topics</span>
      <span class="chip">{n_questions} questions with model answers</span>
      <span class="chip chip-quiz" id="progressChip">0 / {n_questions} marked known</span>
    </div>
  </div>
</header>

<div class="subnav">
  <div class="wrap">
{subnav}
  </div>
</div>

<main class="wrap">
  <section class="iv-intro" id="rounds">
    <div class="pj-box">
      <div class="box-label">The rounds you will face</div>
      <ol class="iv-rounds">{rounds}</ol>
    </div>
    <p class="pj-hint">Read each question, answer it out loud <em>before</em> you open the model answer, then compare. Mark the ones you can answer confidently — your progress is saved in this browser only (<a href="../../education.html#progressPanel">back up or restore</a> on the hub).</p>
  </section>

{sections}

  <section id="task" class="pj-phase">
    <div class="pj-phase-head"><span class="pj-phase-num">Task</span><h2>{task_title}</h2></div>
    <p class="pj-goal">{task_brief}</p>
    <div class="pj-box"><div class="box-label">What a strong submission shows</div><ul>{task_checklist}</ul></div>
  </section>

  <section id="standout" class="pj-phase">
    <div class="pj-phase-head"><span class="pj-phase-num">Edge</span><h2>How to stand out</h2></div>
    <ul class="pj-next">{standout}</ul>
  </section>

  <section id="resources" class="pj-phase">
    <div class="pj-phase-head"><span class="pj-phase-num">Prep</span><h2>Build the evidence first</h2></div>
    <p class="pj-goal">Interviewers trust what you have shipped. Every claim in your answers is stronger if you can point at one of these.</p>
    <ul class="iv-resources">{resources}</ul>
  </section>

  <p class="feedback-row">A question phrased in a way you have not seen, or a model answer you would push back on? <a href="../../feedback.html?page=/education/interview/{id}.html&amp;title={role_q}">Tell me →</a></p>
</main>

<footer>
  <div class="wrap footer-row">
    <p>© 2025–2026 ThavionAI. All rights reserved.</p>
    <div class="footer-legal">
      <a href="../../education.html">Education</a>
      <a href="https://buy.stripe.com/3cIeVceBc1ZRbyLdVIdZ601" target="_blank" rel="noopener">☕ Buy me a coffee</a>
      <a href="../../privacy.html">Privacy</a>
      <a href="../../terms.html">Terms</a>
      <a href="../../feedback.html?page=/education/interview/{id}.html&amp;title={role_q}">Report an error</a>
    </div>
  </div>
</footer>

<script src="interview.js"></script>
</body>
</html>
"""


def render_question(si, qi, q):
    key = f"{si + 1}-{qi + 1}"
    code = ""
    if q.get("code"):
        c = q["code"]
        code = (f'<div class="code"><div class="code-head"><span>{esc(c["lang"])}</span>'
                f'<button type="button" class="copy" data-copy>Copy</button></div>'
                f'<pre><code>{esc(c["code"].rstrip(), quote=False)}</code></pre></div>')
    followups = ""
    if q.get("followups"):
        followups = ('<div class="iv-followups"><strong>Likely follow-ups:</strong><ul>'
                     + "".join(f"<li>{inline(f)}</li>" for f in q["followups"]) + "</ul></div>")
    return (f'<li class="iv-q" id="q-{key}">'
            f'<label class="iv-tick"><input type="checkbox" data-q="{key}" aria-label="I can answer this" />'
            f'<span class="iv-tick-label">known</span></label>'
            f'<div class="iv-q-body">'
            f'<p class="iv-question">{inline(q["q"])}</p>'
            f'<p class="iv-tests"><span class="iv-tests-label">What it tests</span> {inline(q["tests"])}</p>'
            f'<details class="iv-answer"><summary>Model answer</summary>'
            f'<div class="iv-answer-body">{inline(q["answer"])}{code}{followups}</div></details>'
            f'</div></li>')


def render(k, tracks):
    track = next(t for t in tracks if t["id"] == k["tracks"][0])
    by_id = {t["id"]: t for t in tracks}
    subnav = ['    <a href="#rounds">The rounds</a>']
    sections_html = []
    n_q = 0
    for si, s in enumerate(k["sections"]):
        sid = f"topic-{si + 1}"
        subnav.append(f'    <a href="#{sid}">{esc(s["title"])}</a>')
        qs = "".join(render_question(si, qi, q) for qi, q in enumerate(s["questions"]))
        n_q += len(s["questions"])
        intro = f'<p class="pj-goal">{inline(s["intro"])}</p>' if s.get("intro") else ""
        sections_html.append(f'''  <section id="{sid}" class="pj-phase iv-topic">
    <div class="pj-phase-head"><span class="pj-phase-num">Topic {si + 1}</span><h2>{esc(s["title"])}</h2></div>
    {intro}
    <ol class="iv-questions">{qs}</ol>
  </section>''')
    subnav.append('    <a href="#task">Take-home task</a>')
    subnav.append('    <a href="#standout">Stand out</a>')

    def res_link(r):
        return f'<li><a href="{esc(r["href"])}">{esc(r["label"])}</a>{" — " + inline(r["note"]) if r.get("note") else ""}</li>'

    return PAGE.format(
        id=k["id"], track=track["id"], track_short=esc(track["short"]),
        role=esc(k["role"], quote=False), role_attr=esc(k["role"]), role_q=quote(k["role"]),
        summary=inline(k["summary"]), summary_attr=esc(k["summary"]),
        n_sections=len(k["sections"]), n_questions=n_q,
        subnav="\n".join(subnav),
        rounds="".join(f'<li><strong>{esc(r["name"])}</strong> — {inline(r["what"])}'
                       + (f' <span class="iv-tip">{inline(r["tip"])}</span>' if r.get("tip") else "") + "</li>"
                       for r in k["rounds"]),
        sections="\n\n".join(sections_html),
        task_title=esc(k["task"]["title"], quote=False), task_brief=inline(k["task"]["brief"]),
        task_checklist="".join(f"<li>{inline(x)}</li>" for x in k["task"]["checklist"]),
        standout="".join(f"<li>{inline(x)}</li>" for x in k["standout"]),
        resources="".join(res_link(r) for r in k["resources"]),
    )


def main(argv):
    check_only = "--check" in argv
    wanted = [a for a in argv if not a.startswith("--")]
    manifest = json.loads((SRC / "tracks.json").read_text())
    tracks = manifest["tracks"]
    track_ids = {t["id"] for t in tracks}
    listed = {kit["id"] for kit in manifest.get("interview", [])}
    src_dir = SRC / "interview"
    files = [src_dir / f"{w}.json" for w in wanted] if wanted else sorted(src_dir.glob("*.json"))
    failed = built = 0
    for f in files:
        kid = f.stem
        if not f.exists():
            print(f"MISSING {kid}"); failed += 1; continue
        if kid not in listed:
            print(f"FAIL {kid}: not listed under manifest 'interview'"); failed += 1; continue
        try:
            k = json.loads(f.read_text())
        except ValueError as e:
            print(f"FAIL {kid}: invalid JSON - {e}"); failed += 1; continue
        errs, n = validate(kid, k, track_ids)
        if errs:
            failed += 1
            print(f"FAIL {kid}:")
            for e in errs:
                print(f"   - {e}")
            continue
        if check_only:
            print(f"OK   {kid} ({n} questions)")
        else:
            OUT.mkdir(parents=True, exist_ok=True)
            (OUT / f"{kid}.html").write_text(render(k, tracks))
            built += 1
    if not check_only:
        print(f"built {built} interview kit page(s) -> {OUT.relative_to(ROOT)}/")
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main(sys.argv[1:])
