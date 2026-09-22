#!/usr/bin/env python3
"""Build the thavionai.com landing page and Education hub from the tracks manifest.

Source:  site-src/site/index.html, site-src/site/hub.html   (templates with {{PLACEHOLDERS}})
         site-src/education/tracks.json                      (tracks, stages, modules, projects, resources)
         site-src/education/modules/<id>.json                 (a module is "live" when its JSON exists)
         site-src/education/projects/<id>.json                (a project is "live" when its JSON exists)
Output:  docs/index.html, docs/education.html

Run after scripts/build_education.py (which renders the lessons and projects themselves).
"""
import html
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "site-src"
EDU = SRC / "education"
DOCS = ROOT / "docs"
sys.path.insert(0, str(Path(__file__).resolve().parent))
import diagrams  # noqa: E402

esc = html.escape
tracks_kits = []  # filled by load(): interview prep kits from the manifest


def load():
    data = json.load(open(EDU / "tracks.json"))
    tracks = data["tracks"]
    tracks_kits[:] = data.get("interview", [])
    for tr in tracks:
        tr["modules"] = [m for st in tr["stages"] for m in st["modules"]]
        for m in tr["modules"]:
            m["live"] = (EDU / "modules" / f"{m['id']}.json").exists()
        for p in tr["projects"]:
            p["live"] = (EDU / "projects" / f"{p['id']}.json").exists()
        tr["n_live"] = sum(m["live"] for m in tr["modules"])
        tr["n_total"] = len(tr["modules"])
    return tracks


def count_diagrams(tracks):
    live = {m["id"] for tr in tracks for m in tr["modules"] if m["live"]}
    n = 0
    for f in (EDU / "diagrams").glob("*.json"):
        if f.stem in live:
            n += len(json.load(open(f)))
    return n


def svg_only(mod_id, fig_id):
    """Render one diagram and return just its <svg>, sized by CSS rather than inline style."""
    for d in json.load(open(EDU / "diagrams" / f"{mod_id}.json")):
        if d["id"] == fig_id:
            fig = diagrams.render(d)
            svg = re.search(r"<svg.*?</svg>", fig, re.S).group(0)
            return re.sub(r' style="[^"]*"', "", svg, count=1)
    raise SystemExit(f"diagram {mod_id}/{fig_id} not found")


def module_title(mod_id, tracks):
    for tr in tracks:
        for m in tr["modules"]:
            if m["id"] == mod_id:
                return m["title"], tr
    raise KeyError(mod_id)


# ---------------------------------------------------------------- landing page fragments

def track_tiles(tracks):
    out = []
    for tr in tracks:
        if tr["n_live"] == tr["n_total"]:
            badge, count = '<span class="badge badge-live">Complete</span>', f'<b>{tr["n_total"]}</b> lessons'
        elif tr["n_live"]:
            badge, count = '<span class="badge badge-building">In progress</span>', f'<b>{tr["n_live"]}</b> of {tr["n_total"]} lessons live'
        else:
            badge, count = '<span class="badge badge-soon">Coming soon</span>', f'<b>{tr["n_total"]}</b> lessons planned'
        out.append(f'''      <a class="tile" href="education.html#{tr["id"]}" style="--tc:{tr["accent"]}">
        <div class="tile-top"><span class="icon-box">{tr["emoji"]}</span>{badge}</div>
        <h3>{esc(tr["name"])}</h3>
        <p>{esc(tr["tagline"])}</p>
        <div class="tile-meta"><span>{count}</span><span class="tile-arrow">Open track →</span></div>
      </a>''')
    return "\n".join(out)


def showcase(tracks):
    picks = [("devops-cicd", "cicd-pipeline"), ("sre-slo", "slo-chain"), ("ai-rag", "rag-pipelines")]
    out = []
    for mod_id, fig in picks:
        title, tr = module_title(mod_id, tracks)
        out.append(f'''      <a class="card" href="education/{mod_id}.html#fig-{fig}">
        <div class="mock-diagram">{svg_only(mod_id, fig)}</div>
        <div class="cap"><small style="color:{tr["accent"]}">{esc(tr["short"])}</small><h3>{esc(title)}</h3></div>
      </a>''')
    return "\n".join(out)


def project_cards(tracks):
    out = []
    for tr in tracks:
        p = tr["projects"][0]
        badge = '<span class="badge badge-live">Available</span>' if p["live"] else '<span class="badge badge-soon">Coming soon</span>'
        body = f'''        {badge}
        <h3>{esc(p["title"])}</h3>
        <p>{esc(p["desc"])}</p>
        <div class="meta"><span>{tr["emoji"]} {esc(tr["short"])}</span><span>⏱ about {p["hours"]} h</span><span>{esc(p["level"])}</span></div>'''
        if p["live"]:
            out.append(f'      <a class="card" href="education/projects/{p["id"]}.html" style="--tc:{tr["accent"]}">\n{body}\n      </a>')
        else:
            out.append(f'      <div class="card" style="--tc:{tr["accent"]}">\n{body}\n      </div>')
    return "\n".join(out)


def cert_cards(tracks):
    tr = next(t for t in tracks if t["id"] == "certs")
    out = []
    for st in tr["stages"]:
        for m in st["modules"]:
            badge = '<span class="badge badge-live">Guide available</span>' if m["live"] else '<span class="badge badge-soon">Guide coming</span>'
            body = f'''        {badge}
        <h3>{esc(m["title"])}</h3>
        <p>{esc(m["desc"])}</p>
        <div class="meta"><span>{esc(st["title"])}</span><span>{esc(st["level"])}</span></div>'''
            if m["live"]:
                out.append(f'      <a class="card" href="education/{m["id"]}.html" style="--tc:{tr["accent"]}">\n{body}\n      </a>')
            else:
                out.append(f'      <div class="card" style="--tc:{tr["accent"]}">\n{body}\n      </div>')
    return "\n".join(out)


def interview_cards(kits, tracks):
    by_id = {tr["id"]: tr for tr in tracks}
    out = []
    for k in kits:
        live = (EDU / "interview" / f"{k['id']}.json").exists()
        badge = '<span class="badge badge-live">Kit available</span>' if live else '<span class="badge badge-soon">Kit coming</span>'
        rel = " · ".join(esc(by_id[t]["short"]) for t in k["tracks"])
        body = f"""        {badge}
        <h3>{esc(k["role"])}</h3>
        <p>{esc(k["desc"])}</p>
        <div class="meta"><span>Related: {rel}</span></div>"""
        accent = by_id[k["tracks"][0]]["accent"]
        if live:
            out.append(f'      <a class="card" href="education/interview/{k["id"]}.html" style="--tc:{accent}">\n{body}\n      </a>')
        else:
            out.append(f'      <div class="card" style="--tc:{accent}">\n{body}\n      </div>')
    return "\n".join(out)


def footer_tracks(tracks):
    return "\n".join(f'        <a href="education.html#{tr["id"]}">{esc(tr["name"])}</a>' for tr in tracks)


# ---------------------------------------------------------------- hub fragments

def tabs(tracks):
    out = []
    for i, tr in enumerate(tracks):
        sel = "true" if i == 0 else "false"
        ti = "" if i == 0 else ' tabindex="-1"'
        out.append(f'      <button class="track-tab" role="tab" id="tab-{tr["id"]}" aria-controls="{tr["id"]}" aria-selected="{sel}" data-track="{tr["id"]}"{ti} style="--tc:{tr["accent"]}">{tr["emoji"]} {esc(tr["short"])} <span class="n">{tr["n_live"]}/{tr["n_total"]}</span></button>')
    return "\n".join(out)


def module_row(m):
    title, desc = esc(m["title"]), esc(m["desc"])
    if m["live"]:
        return (f'            <li class="module"><input type="checkbox" data-id="{m["id"]}" aria-label="Mark {title} complete" />'
                f'<a class="module-body" href="education/{m["id"]}.html"><span class="module-title">{title}</span>'
                f'<span class="module-desc">{desc}</span><span class="module-cta"><span class="module-quiz" data-quiz="{m["id"]}" hidden></span>'
                f'Lesson · Cheat sheet · Quiz →</span></a></li>')
    return (f'            <li class="module soon"><input type="checkbox" disabled aria-hidden="true" />'
            f'<span class="module-body"><span class="module-title">{title}</span><span class="module-desc">{desc}</span>'
            f'<span class="module-cta">Coming soon</span></span></li>')


def panel(tr, first):
    levels = [st["level"] for st in tr["stages"]]
    level_range = levels[0] if levels[0] == levels[-1] else f'{levels[0].split("–")[0].strip()} → {levels[-1]}'
    lessons = f'{tr["n_total"]} lessons' if tr["n_live"] == tr["n_total"] else f'{tr["n_live"]} of {tr["n_total"]} lessons live'
    stages = []
    for st in tr["stages"]:
        rows = "\n".join(module_row(m) for m in st["modules"])
        stages.append(f'''        <div class="stage">
          <div class="stage-top"><span class="stage-num">Stage {st["num"]}</span><span class="stage-level">{esc(st["level"])}</span></div>
          <h4>{esc(st["title"])}</h4>
          <ul class="modules">
{rows}
          </ul>
        </div>''')
    projects = []
    for p in tr["projects"]:
        meta = f'<span class="m">about {p["hours"]} h<br />{esc(p["level"])}</span>'
        if p["live"]:
            projects.append(f'            <a href="education/projects/{p["id"]}.html"><span><span class="t">{esc(p["title"])}</span><span class="d">{esc(p["desc"])}</span></span>{meta}</a>')
        else:
            projects.append(f'            <a class="soon-item" tabindex="-1" aria-disabled="true"><span><span class="t">{esc(p["title"])}</span><span class="d">{esc(p["desc"])}</span></span><span class="m">Coming soon</span></a>')
    resources = "\n".join(f'            <a href="{r["url"]}" target="_blank" rel="noopener">{esc(r["title"])}<span>{esc(r["note"])}</span></a>' for r in tr["resources"])
    hidden = "" if first else " hidden"
    return f'''    <div class="track-panel" id="{tr["id"]}" role="tabpanel" aria-labelledby="tab-{tr["id"]}" style="--tc:{tr["accent"]}"{hidden}>
      <div class="track-head">
        <div class="track-logo">{tr["emoji"]}</div>
        <div style="flex:1;min-width:0">
          <h3>{esc(tr["name"])}</h3>
          <p>{esc(tr["blurb"])}</p>
          <div class="track-meta">
            <span class="chip">{esc(level_range)}</span>
            <span class="chip">{len(tr["stages"])} stages</span>
            <span class="chip">{lessons}</span>
            <span class="chip">{len(tr["projects"])} projects</span>
          </div>
          <div class="progress">
            <div class="progress-row"><span>Your progress</span><span data-progress-text>0 / {tr["n_live"]} complete</span></div>
            <div class="progress-bar"><div class="progress-fill" data-progress-fill></div></div>
          </div>
        </div>
      </div>
      <div class="stages">
{chr(10).join(stages)}
      </div>
      <div class="track-foot">
        <div class="box">
          <div class="box-label">Guided projects</div>
          <div class="proj-list">
{chr(10).join(projects)}
          </div>
        </div>
        <div class="box">
          <div class="box-label">Best free resources</div>
          <div class="res-list">
{resources}
          </div>
        </div>
      </div>
    </div>'''


def fit_tiles(tracks):
    out = []
    for tr in tracks:
        out.append(f'''      <a class="tile" href="#{tr["id"]}" data-goto="{tr["id"]}" style="--tc:{tr["accent"]}">
        <div class="tile-top"><span class="icon-box">{tr["emoji"]}</span></div>
        <h3>{esc(tr["name"])}</h3>
        <p>{esc(tr["fit"])}</p>
        <div class="tile-meta"><span>{tr["n_live"]} of {tr["n_total"]} lessons live</span><span class="tile-arrow">Start →</span></div>
      </a>''')
    return "\n".join(out)


# ---------------------------------------------------------------- main

# Certification guides most directly related to each track (used by the study planner).
# ai and data have no cert on the site, so they get none.
RELATED_CERTS = {
    "devops": ["cert-terraform", "cert-cka"],
    "sre": ["cert-cka"],
    "security": ["cert-security-plus", "cert-cissp"],
}

_minutes_cache = {}


def module_minutes(mod_id):
    if mod_id not in _minutes_cache:
        try:
            _minutes_cache[mod_id] = int(json.load(open(EDU / "modules" / f"{mod_id}.json")).get("minutes", 30))
        except Exception:
            _minutes_cache[mod_id] = 30
    return _minutes_cache[mod_id]


def plan_data(tracks):
    """Per-track ordered study items (lessons → projects → related cert) for the client-side planner."""
    certs_tr = next(t for t in tracks if t["id"] == "certs")
    cert_lookup = {m["id"]: m for m in certs_tr["modules"]}
    out_tracks = []
    for tr in tracks:
        items = []
        for m in tr["modules"]:
            if m["live"]:
                items.append({"type": "lesson", "title": m["title"], "key": m["id"],
                              "url": f"education/{m['id']}.html", "min": module_minutes(m["id"])})
        for p in tr["projects"]:
            if p.get("live"):
                items.append({"type": "project", "title": p["title"], "key": p["id"],
                              "url": f"education/projects/{p['id']}.html", "min": int(round(p["hours"] * 60))})
        if tr["id"] != "certs":
            for cid in RELATED_CERTS.get(tr["id"], []):
                cm = cert_lookup.get(cid)
                if cm and cm["live"]:
                    items.append({"type": "cert", "title": cm["title"], "key": cid,
                                  "url": f"education/{cid}.html", "min": module_minutes(cid)})
        out_tracks.append({"id": tr["id"], "name": tr["name"], "short": tr["short"],
                           "accent": tr["accent"], "emoji": tr["emoji"], "items": items})
    payload = {
        "tracks": out_tracks,
        "intensities": [
            {"id": "intense", "label": "Intense", "maxItems": 4, "perDay": 180, "everyDays": 1, "blurb": "~2 hrs a day"},
            {"id": "steady", "label": "Steady", "maxItems": 2, "perDay": 100, "everyDays": 1, "blurb": "~1 hr a day"},
            {"id": "relaxed", "label": "Relaxed", "maxItems": 1, "perDay": 60, "everyDays": 1, "blurb": "a lesson a day"},
            {"id": "casual", "label": "Casual", "maxItems": 1, "perDay": 60, "everyDays": 2, "blurb": "a lesson every 2 days"},
        ],
    }
    return json.dumps(payload, ensure_ascii=False)


def fill(template, values):
    out = template
    for k, v in values.items():
        out = out.replace("{{" + k + "}}", str(v))
    left = re.findall(r"\{\{[A-Z_]+\}\}", out)
    if left:
        raise SystemExit(f"unfilled placeholders: {sorted(set(left))}")
    return out


def main():
    tracks = load()
    n_live = sum(tr["n_live"] for tr in tracks)
    n_planned = sum(tr["n_total"] - tr["n_live"] for tr in tracks)
    stats = {
        "STAT_TRACKS": len(tracks), "STAT_LESSONS": n_live, "STAT_PLANNED": n_planned,
        "STAT_QUIZ": n_live * 5, "STAT_DIAGRAMS": count_diagrams(tracks),
        "STAT_PROJECTS": sum(p["live"] for tr in tracks for p in tr["projects"]),
        "STAT_CERTS": sum(m["live"] for tr in tracks if tr["id"] == "certs" for m in tr["modules"]),
    }
    eng = fill((SRC / "site" / "engineering.html").read_text(), {
        **stats,
        "HERO_DIAGRAM": svg_only("devops-k8s", "k8s-traffic"),
        "MOCK_DIAGRAM": svg_only("devops-gitops", json.load(open(EDU / "diagrams" / "devops-gitops.json"))[0]["id"]),
        "TRACK_TILES": track_tiles(tracks), "SHOWCASE": showcase(tracks),
        "PROJECT_CARDS": project_cards(tracks), "CERT_CARDS": cert_cards(tracks),
        "FOOTER_TRACKS": footer_tracks(tracks), "INTERVIEW_CARDS": interview_cards(tracks_kits, tracks),
    })
    (DOCS / "engineering.html").write_text(eng)
    (DOCS / "index.html").write_text(fill((SRC / "site" / "home.html").read_text(), stats))
    (DOCS / "exams.html").write_text(fill((SRC / "site" / "exams.html").read_text(), {}))
    (DOCS / "school.html").write_text(fill((SRC / "site" / "school.html").read_text(), {}))
    hub = fill((SRC / "site" / "hub.html").read_text(), {
        **stats,
        "TABS": tabs(tracks),
        "PANELS": "\n".join(panel(tr, i == 0) for i, tr in enumerate(tracks)),
        "FIT_TILES": fit_tiles(tracks),
        "FOOTER_TRACKS": footer_tracks(tracks),
        "TRACK_IDS": json.dumps([tr["id"] for tr in tracks]),
        "PLAN_DATA": plan_data(tracks),
    })
    (DOCS / "education.html").write_text(hub)
    print(f"built home, engineering, exams, school, education: {stats}")


if __name__ == "__main__":
    main()
