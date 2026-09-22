"""Site-wide invariants for thavionai.com, tested against a freshly built docs/.

Run from the repo root:  python3 -m pytest tests/ -q
The build runs first (via the session fixture), so the tests check exactly what ships.

These tests complement the per-file validators in the build scripts: they check
cross-page invariants those scripts do not — nav consistency, link integrity, and
that no template placeholder leaked into the output.
"""
import re
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
SCRIPTS = ROOT / "scripts"

NAV = re.compile(r"<nav\b.*?</nav>", re.S | re.I)
ANCHOR = re.compile(r'<a\b[^>]*?href="([^"]+)"[^>]*?>(.*?)</a>', re.S | re.I)
LINK = re.compile(r'(?:href|src)="([^"]+)"', re.I)
PLACEHOLDER = re.compile(r"\{\{[A-Z_]+\}\}")
TAGS = re.compile(r"<[^>]+>")
REFRESH = re.compile(r'http-equiv="refresh"', re.I)
SCRIPT_OR_STYLE = re.compile(r"<script\b.*?</script>|<style\b.*?</style>", re.S | re.I)

# Pages that legitimately have no top <nav> (standalone utility/legal pages we don't own the chrome of).
NAV_EXEMPT = {"feedback.html", "privacy.html", "terms.html"}


def is_redirect(html: str) -> bool:
    return bool(REFRESH.search(html))


@pytest.fixture(scope="session", autouse=True)
def built_site():
    """Rebuild the whole site before the tests run; fail loudly if any build step breaks."""
    for cmd in (
        [sys.executable, str(SCRIPTS / "build_education.py"), "--strict"],
        [sys.executable, str(SCRIPTS / "build_projects.py")],
        [sys.executable, str(SCRIPTS / "build_interview.py")],
        [sys.executable, str(SCRIPTS / "build_site.py")],
    ):
        r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
        assert r.returncode == 0, f"build failed: {' '.join(cmd)}\n{r.stdout}\n{r.stderr}"
    return DOCS


def all_pages():
    return sorted(DOCS.rglob("*.html"))


def rel_to_index(page: Path) -> str:
    """The href a page must use to reach docs/index.html."""
    depth = len(page.relative_to(DOCS).parts) - 1
    return ("../" * depth) + "index.html"


def text_of(anchor_html: str) -> str:
    return TAGS.sub("", anchor_html).strip()


def test_key_pages_exist(built_site):
    for name in ("index.html", "engineering.html", "education.html", "exams.html", "school.html"):
        assert (DOCS / name).is_file(), f"missing key page: {name}"


def test_every_page_has_a_nav(built_site):
    missing = [str(p.relative_to(DOCS)) for p in all_pages()
               if p.name not in NAV_EXEMPT and not is_redirect(p.read_text()) and not NAV.search(p.read_text())]
    assert not missing, "pages with no <nav>:\n  " + "\n  ".join(missing)


def test_home_link_on_every_page(built_site):
    """Every page's nav links to index.html; every non-home page shows a visible 'Home' link."""
    no_index, no_home_text = [], []
    for page in all_pages():
        html = page.read_text()
        if page.name in NAV_EXEMPT or is_redirect(html):
            continue
        nav = NAV.search(html)
        if not nav:
            continue  # covered by test_every_page_has_a_nav
        anchors = ANCHOR.findall(nav.group(0))
        want = rel_to_index(page)
        hrefs = {h.split("#")[0].split("?")[0] for h, _ in anchors}
        if want not in hrefs:
            no_index.append(f"{page.relative_to(DOCS)} (want a nav link to {want})")
            continue
        has_home = any(
            h.split("#")[0].split("?")[0] == want and text_of(t) == "Home"
            for h, t in anchors
        )
        if not has_home:
            no_home_text.append(str(page.relative_to(DOCS)))
    msg = ""
    if no_index:
        msg += "pages whose nav has no link to index.html:\n  " + "\n  ".join(no_index) + "\n"
    if no_home_text:
        msg += "non-home pages missing a visible 'Home' nav link:\n  " + "\n  ".join(no_home_text)
    assert not msg, msg


def test_no_broken_internal_links(built_site):
    broken = []
    for page in all_pages():
        html = SCRIPT_OR_STYLE.sub("", page.read_text())  # ignore JS/CSS-built strings
        for target in LINK.findall(html):
            if re.match(r"^(https?:|mailto:|tel:|data:|javascript:|#|//)", target):
                continue
            path = target.split("#")[0].split("?")[0]
            if not path:
                continue
            resolved = (page.parent / path).resolve()
            if not resolved.exists():
                broken.append(f"{page.relative_to(DOCS)} -> {target}")
    assert not broken, "broken internal links:\n  " + "\n  ".join(broken)


def test_no_unfilled_placeholders(built_site):
    leaked = []
    for page in all_pages():
        found = set(PLACEHOLDER.findall(page.read_text()))
        if found:
            leaked.append(f"{page.relative_to(DOCS)}: {sorted(found)}")
    assert not leaked, "template placeholders leaked into output:\n  " + "\n  ".join(leaked)
