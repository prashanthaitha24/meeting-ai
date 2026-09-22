#!/usr/bin/env python3
"""Build the AcadVerify exam question bank from the education module quizzes.

Produces site-src/acadverify/bank.json:
  { "<trackId>": { "name": "<trackName>", "questions": [ {"q","options","answer"}, ... ] }, ... }

The bank is bundled into the Cloudflare issuer Worker, which serves random questions
WITHOUT answers and grades submissions server-side (so the exam can't be gamed client-side).

Usage:  python3 scripts/build_acadverify_bank.py
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "site-src" / "education"
OUT = ROOT / "site-src" / "acadverify" / "bank.json"

# Tracks eligible for certification (skip the 'certs' meta-track).
SKIP_TRACKS = {"certs"}


def main():
    tracks = json.loads((SRC / "tracks.json").read_text())["tracks"]
    bank = {}
    total = 0
    for tr in tracks:
        if tr["id"] in SKIP_TRACKS:
            continue
        questions = []
        for stage in tr.get("stages", []):
            for mod in stage.get("modules", []):
                path = SRC / "modules" / f"{mod['id']}.json"
                if not path.exists():
                    continue
                m = json.loads(path.read_text())
                for item in m.get("quiz", []):
                    opts = item.get("options", [])
                    if not (isinstance(opts, list) and len(opts) == 4):
                        continue
                    ans = item.get("answer")
                    if not isinstance(ans, int) or not (0 <= ans < 4):
                        continue
                    questions.append({"q": item["q"], "options": opts, "answer": ans})
        if questions:
            bank[tr["id"]] = {"name": tr["name"], "questions": questions}
            total += len(questions)
            print(f"  {tr['id']:12s} {len(questions):4d} questions")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(bank, ensure_ascii=False))
    print(f"wrote {OUT.relative_to(ROOT)}  ({total} questions across {len(bank)} tracks)")


if __name__ == "__main__":
    main()
