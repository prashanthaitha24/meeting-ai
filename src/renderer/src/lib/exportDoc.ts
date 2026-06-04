// Builds the saved "meeting notes" document in two representations:
//   • plain text  → .txt
//   • HTML        → .doc (Word opens HTML) and the source for the PDF render
// Kept pure (no React/Electron) so the formatting is unit-testable.

export interface ExportData {
  date: string // human-readable timestamp
  transcript: string
  qa: { question: string; answer: string }[]
  recap?: string
  say?: string
  followup?: string
}

const RULE = '-'.repeat(30)

/** Plain-text export — conversation first as Q&A, transcript last. */
export function buildExportText(d: ExportData): string {
  const out: string[] = ['Meeting Notes', d.date, '='.repeat(50), '']

  if (d.qa.length) {
    out.push('CONVERSATION', RULE, '')
    d.qa.forEach((e, i) => {
      out.push(`Q${i + 1}: ${e.question.trim()}`, '', e.answer.trim(), '', RULE, '')
    })
  }
  if (d.recap?.trim()) out.push('RECAP', RULE, d.recap.trim(), '')
  if (d.say?.trim()) out.push('TALKING POINTS', RULE, d.say.trim(), '')
  if (d.followup?.trim()) out.push('FOLLOW-UP QUESTIONS', RULE, d.followup.trim(), '')
  if (d.transcript?.trim()) out.push('FULL TRANSCRIPT', RULE, d.transcript.trim(), '')

  return out.join('\n').replace(/\n{3,}/g, '\n\n').trimEnd() + '\n'
}

function esc(s: string): string {
  return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
}

/** HTML export — used directly for .doc and rendered to PDF in the main process. */
export function buildExportHtml(d: ExportData): string {
  const parts: string[] = []

  if (d.qa.length) {
    parts.push('<h2>Conversation</h2>')
    d.qa.forEach((e, i) => {
      parts.push(
        `<div class="qa"><p class="q">Q${i + 1}. ${esc(e.question.trim())}</p>` +
          `<p class="a">${esc(e.answer.trim())}</p></div>`,
      )
    })
  }
  if (d.recap?.trim()) parts.push(`<h2>Recap</h2><p class="block">${esc(d.recap.trim())}</p>`)
  if (d.say?.trim()) parts.push(`<h2>Talking Points</h2><p class="block">${esc(d.say.trim())}</p>`)
  if (d.followup?.trim())
    parts.push(`<h2>Follow-up Questions</h2><p class="block">${esc(d.followup.trim())}</p>`)
  if (d.transcript?.trim())
    parts.push(`<h2>Full Transcript</h2><p class="transcript">${esc(d.transcript.trim())}</p>`)

  return `<!doctype html><html><head><meta charset="utf-8"><title>Meeting Notes</title><style>
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;font-size:13px;color:#1a1a1a;line-height:1.55;max-width:720px;margin:32px auto;padding:0 20px}
h1{font-size:22px;margin:0 0 2px}
.meta{color:#666;font-size:12px;margin:0 0 24px}
h2{font-size:14px;color:#111;border-bottom:1px solid #e2e2e2;padding-bottom:5px;margin:26px 0 12px}
.qa{margin:0 0 18px;page-break-inside:avoid}
.q{font-weight:700;color:#1d4ed8;margin:0 0 5px}
.a,.block{white-space:pre-wrap;margin:0}
.transcript{white-space:pre-wrap;color:#333;background:#f6f7f8;padding:12px 14px;border-radius:6px;font-size:12px}
</style></head><body>
<h1>Meeting Notes</h1><p class="meta">${esc(d.date)}</p>
${parts.join('\n')}
</body></html>`
}
