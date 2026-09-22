#!/usr/bin/env python3
"""Build the guided project pages: site-src/education/projects/<id>.json -> docs/education/projects/<id>.html

A project is a sequence of phases, each a list of plain numbered steps. Every step has `text`; it may also
carry `code` ({lang, code}), a `note`, and a `check` (how to confirm the step worked). Steps are checkable
in the browser; ticks are stored in localStorage under thavionai-edu-projects.

Usage:  python3 scripts/build_projects.py [--check ID ...] [--strict]
"""
import html
import json
import re
import sys
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "site-src" / "education"
OUT = ROOT / "docs" / "education" / "projects"
sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_education import inline, lint_code, slug  # noqa: E402

esc = html.escape


def validate(pid, p):
    errs = []
    need = lambda c, m: None if c else errs.append(m)  # noqa: E731
    need(p.get("id") == pid, f"'id' must equal the filename ({pid})")
    for k in ("track", "title", "summary", "outcome", "hours", "level"):
        need(p.get(k), f"'{k}' missing")
    need(isinstance(p.get("prereqs"), list) and p["prereqs"], "'prereqs' needs items")
    need(isinstance(p.get("tools"), list) and len(p["tools"]) >= 3, "'tools' needs >= 3 entries")
    for i, t in enumerate(p.get("tools", [])):
        need(t.get("name") and t.get("why"), f"tools[{i}]: needs name and why")
    phases = p.get("phases", [])
    need(isinstance(phases, list) and 4 <= len(phases) <= 12, "'phases' needs 4-12 phases")
    n_steps = 0
    for pi, ph in enumerate(phases):
        need(ph.get("title") and ph.get("goal"), f"phases[{pi}]: needs title and goal")
        steps = ph.get("steps", [])
        need(isinstance(steps, list) and 2 <= len(steps) <= 20, f"phases[{pi}]: needs 2-20 steps")
        for si, s in enumerate(steps):
            n_steps += 1
            need(isinstance(s.get("text"), str) and len(s["text"]) > 12, f"phases[{pi}].steps[{si}]: text too short")
            if s.get("code"):
                c = s["code"]
                need(c.get("lang") and c.get("code"), f"phases[{pi}].steps[{si}]: code needs lang and code")
                if c.get("lang") and c.get("code"):
                    e = lint_code(c["lang"], c["code"])
                    if e:
                        errs.append(f"phases[{pi}].steps[{si}]: code does not parse -> {e}")
    need(n_steps >= 25, f"project needs >= 25 steps in total (has {n_steps})")
    need(isinstance(p.get("troubleshooting"), list) and len(p["troubleshooting"]) >= 3, "'troubleshooting' needs >= 3 items")
    need(isinstance(p.get("next"), list) and p["next"], "'next' needs items")
    return errs, n_steps


PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{title} — {track_short} project | ThavionAI Education</title>
  <meta name="description" content="{summary_attr}" />
  <meta property="og:title" content="{title_attr} — ThavionAI project" />
  <meta property="og:description" content="{summary_attr}" />
  <meta property="og:type" content="article" />
  <meta property="og:image" content="https://thavionai.com/assets/og-education.png" />
  <meta property="og:image:width" content="1200" />
  <meta property="og:image:height" content="630" />
  <meta name="twitter:card" content="summary_large_image" />
  <link rel="canonical" href="https://thavionai.com/education/projects/{id}.html" />
  <link rel="icon" href="../../assets/favicon.ico" sizes="any" />
  <link rel="icon" type="image/png" sizes="32x32" href="../../assets/logo-32.png" />
  <link rel="apple-touch-icon" href="../../assets/apple-touch-icon.png" />
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet" />
  <link rel="stylesheet" href="../lesson.css" />
  <link rel="stylesheet" href="project.css" />
</head>
<body class="track-{track}" data-project="{id}">

<nav>
  <a href="../../index.html" class="nav-logo"><img class="nav-logo-icon" src="../../assets/logo.png" alt="" width="32" height="32" />ThavionAI</a>
  <div class="nav-links" id="navLinks">
    <a href="../../index.html">Home</a>
    <a href="../../education.html">Tracks</a>
    <a href="../../engineering.html#projects" class="active">Projects</a>
    <a href="../../education.html#certs">Certifications</a>
    <a href="../../index.html#apps">Apps</a>
    <a href="../../feedback.html?page=/education/projects/{id}.html&amp;title={title_q}">Feedback</a>
    <a href="../../education.html#{track}" class="nav-cta">{track_short} track</a>
  </div>
  <div class="hamburger" id="hamburger"><span></span><span></span><span></span></div>
</nav>

<header class="lesson-hero">
  <div class="wrap">
    <div class="crumbs"><a href="../../education.html">Education</a> › <a href="../../education.html#{track}">{track_name}</a> › Guided project</div>
    <h1>{title}</h1>
    <p class="lede">{summary}</p>
    <div class="meta">
      <span class="chip">{level}</span>
      <span class="chip">about {hours} hours</span>
      <span class="chip">{n_phases} phases · {n_steps} steps</span>
      <span class="chip chip-quiz" id="progressChip">0 / {n_steps} done</span>
    </div>
  </div>
</header>

<div class="subnav">
  <div class="wrap">
{subnav}
  </div>
</div>

<main class="wrap">
  <section class="pj-intro" id="overview">
    <div class="objectives">
      <div class="box-label">What you will have at the end</div>
      <p class="pj-outcome">{outcome}</p>
    </div>
    <div class="pj-grid">
      <div class="pj-box">
        <div class="box-label">Before you start</div>
        <ul>{prereqs}</ul>
      </div>
      <div class="pj-box">
        <div class="box-label">Tools you will install</div>
        <ul class="pj-tools">{tools}</ul>
      </div>
    </div>
    {layout}
    <p class="pj-hint">Tick each step as you finish it — your progress is saved in this browser only (<a href="../../education.html#progressPanel">back up or restore</a> on the hub). Every code block has a copy button. If something goes wrong, the <a href="#troubleshooting">troubleshooting</a> section at the end covers the usual suspects.</p>
  </section>

{phases}

  <section id="troubleshooting" class="pj-phase">
    <div class="pj-phase-head"><span class="pj-phase-num">Help</span><h2>Troubleshooting</h2></div>
    <dl class="pj-trouble">{troubleshooting}</dl>
  </section>

  <section id="next" class="pj-phase">
    <div class="pj-phase-head"><span class="pj-phase-num">Next</span><h2>Where to go from here</h2></div>
    <ul class="pj-next">{next}</ul>
  </section>

  <p class="feedback-row">Did a step fail or feel unclear? <a href="../../feedback.html?page=/education/projects/{id}.html&amp;title={title_q}">Tell me which one →</a></p>
</main>

<footer>
  <div class="wrap footer-row">
    <p>© 2025–2026 ThavionAI. All rights reserved.</p>
    <div class="footer-legal">
      <a href="../../education.html">Education</a>
      <a href="https://buy.stripe.com/3cIeVceBc1ZRbyLdVIdZ601" target="_blank" rel="noopener">☕ Buy me a coffee</a>
      <a href="../../privacy.html">Privacy</a>
      <a href="../../terms.html">Terms</a>
      <a href="../../feedback.html?page=/education/projects/{id}.html&amp;title={title_q}">Report an error</a>
    </div>
  </div>
</footer>

<script src="project.js"></script>
</body>
</html>
"""


def render_step(pi, si, s):
    n = f"{pi + 1}.{si + 1}"
    key = f"{pi + 1}-{si + 1}"
    parts = [f'<div class="pj-step-text">{inline(s["text"])}</div>']
    if s.get("code"):
        c = s["code"]
        parts.append(f'<div class="code"><div class="code-head"><span>{esc(c["lang"])}</span><button type="button" class="copy" data-copy>Copy</button></div>'
                     f'<pre><code>{esc(c["code"].rstrip(), quote=False)}</code></pre></div>')
    if s.get("note"):
        parts.append(f'<div class="pj-note">{inline(s["note"])}</div>')
    if s.get("check"):
        parts.append(f'<div class="pj-check"><strong>Check:</strong> {inline(s["check"])}</div>')
    return (f'<li class="pj-step" id="step-{key}"><label class="pj-step-tick"><input type="checkbox" data-step="{key}" aria-label="Done: step {n}" />'
            f'<span class="pj-step-num">{n}</span></label><div class="pj-step-body">{"".join(parts)}</div></li>')


def render(p, tracks):
    track = next(t for t in tracks if t["id"] == p["track"])
    phases_html, subnav = [], ['    <a href="#overview">Overview</a>']
    n_steps = 0
    for pi, ph in enumerate(p["phases"]):
        sid = f"phase-{pi + 1}"
        subnav.append(f'    <a href="#{sid}">{pi + 1}. {esc(ph["title"])}</a>')
        steps = "".join(render_step(pi, si, s) for si, s in enumerate(ph["steps"]))
        n_steps += len(ph["steps"])
        phases_html.append(f'''  <section id="{sid}" class="pj-phase">
    <div class="pj-phase-head"><span class="pj-phase-num">Phase {pi + 1}</span><h2>{esc(ph["title"])}</h2></div>
    <p class="pj-goal">{inline(ph["goal"])}</p>
    <ol class="pj-steps">{steps}</ol>
  </section>''')
    subnav.append('    <a href="#troubleshooting">Troubleshooting</a>')
    layout = ""
    if p.get("layout"):
        layout = (f'<div class="pj-box pj-layout"><div class="box-label">Repository layout at the end</div>'
                  f'<pre><code>{esc(p["layout"].rstrip(), quote=False)}</code></pre></div>')
    return PAGE.format(
        id=p["id"], track=track["id"], track_short=esc(track["short"]), track_name=esc(track["name"]),
        title=esc(p["title"], quote=False), title_attr=esc(p["title"]), title_q=quote(p["title"]),
        summary=inline(p["summary"]), summary_attr=esc(p["summary"]), outcome=inline(p["outcome"]),
        level=esc(p["level"]), hours=p["hours"], n_phases=len(p["phases"]), n_steps=n_steps,
        subnav="\n".join(subnav),
        prereqs="".join(f"<li>{inline(x)}</li>" for x in p["prereqs"]),
        tools="".join(f'<li><strong>{esc(t["name"])}</strong> — {inline(t["why"])}' + (f' <a href="{esc(t["url"])}" target="_blank" rel="noopener">↗</a>' if t.get("url") else "") + "</li>" for t in p["tools"]),
        layout=layout,
        phases="\n\n".join(phases_html),
        troubleshooting="".join(f'<dt>{inline(t["symptom"])}</dt><dd>{inline(t["fix"])}</dd>' for t in p["troubleshooting"]),
        next="".join(f"<li>{inline(x)}</li>" for x in p["next"]),
    )


def main(argv):
    check_only = "--check" in argv
    wanted = [a for a in argv if not a.startswith("--")]
    tracks = json.loads((SRC / "tracks.json").read_text())["tracks"]
    listed = {pr["id"]: t for t in tracks for pr in t["projects"]}
    files = [SRC / "projects" / f"{w}.json" for w in wanted] if wanted else sorted((SRC / "projects").glob("*.json"))
    failed = built = 0
    for f in files:
        pid = f.stem
        if not f.exists():
            print(f"MISSING {pid}"); failed += 1; continue
        if pid not in listed:
            print(f"FAIL {pid}: not listed under any track's projects in tracks.json"); failed += 1; continue
        try:
            p = json.loads(f.read_text())
        except ValueError as e:
            print(f"FAIL {pid}: invalid JSON - {e}"); failed += 1; continue
        errs, n = validate(pid, p)
        if p.get("track") != listed[pid]["id"]:
            errs.append(f"'track' is {p.get('track')!r} but tracks.json lists it under {listed[pid]['id']!r}")
        if errs:
            failed += 1
            print(f"FAIL {pid}:")
            for e in errs:
                print(f"   - {e}")
            continue
        if check_only:
            print(f"OK   {pid} ({n} steps)")
        else:
            OUT.mkdir(parents=True, exist_ok=True)
            (OUT / f"{pid}.html").write_text(render(p, tracks))
            built += 1
    if not check_only:
        print(f"built {built} project page(s) -> {OUT.relative_to(ROOT)}/")
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main(sys.argv[1:])
