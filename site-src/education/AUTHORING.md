# Writing an Education module

Each module on thavionai.com/education is one JSON file: `site-src/education/modules/<id>.json`.
`scripts/build_education.py` validates it and renders `docs/education/<id>.html` (lesson + practice + cheat sheet + quiz).
The module's title, one-line description, stage and level come from `tracks.json` — do not repeat or change them.

**The reference example is `modules/devops-linux.json`. Read it fully first and match its depth, tone and structure.**

## Reader and voice

- The reader is a working or aspiring engineer who wants to be able to *do* the thing on Monday. Practical over academic.
- Explain the mental model first, then show real commands/config, then say what goes wrong in practice.
- Plain, direct sentences. No hype, no filler ("In today's fast-paced world…"), no emoji, no em-dash-heavy prose.
- Second person ("you"). Present tense. Define a term the first time it appears, in **bold**.
- Tie the topic to production reality: why it matters during a deploy, an incident, a cost review, an interview.
- Where natural, connect to neighbouring modules in the track (e.g. "you will use this in the Kubernetes module"), without linking.

## Accuracy rules (non-negotiable)

- Every command, flag, field name, API name and default value must be correct for current stable versions. If you are
  not certain of a detail, leave it out or phrase it generally — never guess a flag or a number.
- Prefer tool-agnostic truths and long-stable syntax over version-specific trivia.
- No invented statistics, studies, quotes, company anecdotes, or URLs. **Do not include any URLs at all.**
- Do not name or recommend paid products unless the module title already names the tool.
- For AI modules: describe provider-neutral concepts. If you show API code, keep it clearly illustrative/pseudocode
  in style unless you are certain of the exact current SDK surface. Never state model names, prices, or context sizes.

## JSON schema

```
{
  "id": "<same as filename>",
  "minutes": 20-40,                      // honest reading time, int
  "intro": "2-4 sentences: why this matters and what the module covers (>= 25 words)",
  "objectives": ["3-5 concrete abilities, each starting with a verb"],
  "sections": [                          // 4-7 sections; total prose 700-1200 words (hard minimum 550)
    { "heading": "Short heading", "blocks": [ ...blocks... ] }
  ],
  "practice": { "title": "...", "steps": ["3-8 concrete hands-on steps the reader can really do for free"] },
  "cheatsheet": {
    "focus":    ["4-8 'main things to focus on' - the ideas that matter most / interviewers ask / incidents hinge on"],
    "groups":   [ { "title": "...", "items": [ { "syntax": "exact command or syntax", "desc": "what it does" } ] } ],
                                         // 3-6 groups, 3-10 items each, >= 15 items in total
    "pitfalls": ["3-6 common mistakes, each one sentence"]
  },
  "quiz": [                              // exactly 5 questions
    { "q": "...", "options": ["4 options"], "answer": 0, "explain": "why the right answer is right (>= 8 words)" }
  ]
}
```

### Blocks

| type | fields | notes |
|---|---|---|
| `p` | `text` | a paragraph |
| `list` | `items[]` | bullets |
| `steps` | `items[]` | numbered |
| `code` | `lang`, `code`, optional `caption` | `lang`: bash, yaml, python, json, hcl, dockerfile, ini, promql, sql, text, … |
| `callout` | `kind` (`tip` \| `warning` \| `note`), `text` | at most one or two per section |
| `table` | `headers[]` (2-4), `rows[][]` | for comparisons |

Inline formatting inside any text field: `` `code` `` and `**bold**` only. No links, no HTML, no markdown headings,
and no single-asterisk `*italics*` (they render literally).

Limits the validator enforces, which are easy to trip over: tables have at most **4 columns**, `practice.steps` has
at most **8 steps**, and the quiz has exactly **5 questions** with **4 options** each.

## Building and previewing

```
python3 scripts/build_education.py --strict      # rebuild every page; fails if any module is missing or invalid
cd docs && python3 -m http.server 8765           # then open http://localhost:8765/education.html
```

The module list, titles and one-line descriptions live in `tracks.json` and are duplicated in the hand-written hub
page `docs/education.html`. If you add, rename or reorder a module, change both, and update the counts on the hub
(the tab badges, each track's "0 / N complete", and the hero figures for lessons and quiz questions).

### Code blocks are linted

`bash`/`sh` blocks go through `bash -n`, `yaml` through a YAML parser, `python` through `ast.parse`, `json` through `json.loads`.
- No shell prompts (`$ `) and no raw command output in bash blocks — put output in `# comments`.
- No `<placeholder>` angle brackets in bash blocks (they parse as redirection). Use realistic values or UPPER_CASE names.
- Templated YAML that is not valid YAML (Helm `{{ }}` control flow etc.) must use a different `lang` such as `helm` or `text`.
- Keep lines <= 100 characters. Keep each block focused: 5-20 lines is ideal.
- The cheat sheet `syntax` field is NOT linted — placeholders like `NAME`, `FILE` are fine there. It is rendered as code, so
  do not wrap it in backticks.

Every module needs real syntax in its cheat sheet, even conceptual ones. For a conceptual module (e.g. "Embracing risk",
"Blameless postmortems") the cheat sheet groups hold formulas, templates, checklists, definitions, decision rules or
key numbers — e.g. `syntax`: `error budget = 1 - SLO`, `desc`: what it means. Make it something worth printing.

### Quiz rules

- Test understanding and judgement, not trivia: scenarios ("a deploy fails with X, what is the most likely cause?"),
  reading a snippet, choosing between approaches. At most one pure-recall question per quiz.
- Every question must be answerable from the lesson content.
- Options are **shuffled at runtime**: never write "all of the above", "none of the above", "both A and B", or refer to
  option positions. Exactly one option is unambiguously correct; the three distractors are plausible misconceptions.
- Keep the four options similar in length and style so the right one can't be spotted by shape. (The validator warns when
  the correct option is clearly the longest in 3+ questions.)
- `answer` is the zero-based index in your `options` array. Its position does not matter to readers, because options
  are shuffled in the browser; the existing modules simply put the correct option first.
- `explain` teaches: say why the right answer is right and, where useful, why the tempting wrong one is wrong.

## Architecture diagrams

Diagrams are optional and live beside the module in `diagrams/<id>.json`: a JSON **list** of figures. Each figure is a
declarative spec that `scripts/diagrams.py` renders to inline SVG (grid layout, theme-aware, scrolls horizontally on phones).
One figure per module is typical; two at most. Draw the mechanism the lesson hinges on (where data flows, who talks to whom,
what changes between two options), not a labelled inventory of everything. If an existing ASCII-art block says the same thing,
delete the block.

```json
[
  {
    "id": "k8s-cluster",
    "caption": "One sentence, at least 6 words, stating the claim the picture makes.",
    "alt": "A fuller prose description for screen readers, covering every node and the direction of the arrows.",
    "place": {"section": 0, "after": 1},
    "groups": [ {"id": "workers", "label": "Worker nodes", "col": 4, "row": 0, "w": 1, "h": 3} ],
    "nodes": [
      {"id": "api", "label": "API server", "sub": "the only door", "col": 1, "row": 0, "kind": "accent"},
      {"id": "etcd", "label": "etcd", "col": 2, "row": 0, "kind": "store"}
    ],
    "edges": [
      {"from": "api", "to": "etcd", "label": "reads, writes", "route": "straight"},
      {"from": "workers", "to": "api", "label": "watch, report", "style": "dashed", "color": "muted"}
    ]
  }
]
```

- `place` inserts the figure in `sections[section]` after block index `after` (`-1` = before the first block).
- Nodes sit on a grid: `col`/`row` (0-based), optional `w`/`h` in cells (default 1). No two nodes may share a cell.
  `kind` is one of `box` (default), `accent` (the thing under discussion), `muted`, `store` (cylinder), `actor` (pill),
  `danger`, `ok`, `text` (bare label). `label` fits in about 16 characters per cell of width; `sub` a little more.
- Groups are dashed rectangles with a caption; give one an `id` to use it as an edge endpoint. `outer: true` draws the
  label above the group instead of inside it.
- Edges: `route` is `auto` (default: straight when aligned, else an elbow), `hv`, `vh`, `straight`, or `over`/`under`
  (a lane above/below the rows, for arrows that would otherwise cross boxes). `style: "dashed"`, `color` in
  `accent|danger|ok|muted`, `offset` shifts the attachment point in px, `label_side: "left"` moves a vertical edge's
  label to the other side. Labels are at most 26 characters.
- The validator checks ids, cell overlap, label lengths, that edges reference real nodes or groups, and that `place`
  points at an existing block. It cannot see arrows crossing boxes, so **look at the rendered figure**: build, serve, open
  the lesson, and check that no line runs through a box and no label sits on another label. Reroute with `hv`/`vh`/`over`/
  `under`, move a node, or drop a label until it is clean.

## Validate before you finish

```
python3 scripts/build_education.py --check <id> [<id> ...]
```

Fix every `FAIL` line and every `warn` line, and re-run until each module prints `OK`. Then re-read your own JSON once more
purely for technical accuracy.
