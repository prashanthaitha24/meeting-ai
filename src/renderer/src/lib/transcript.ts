// On-device transcript preprocessing — runs on the user's Mac before any cloud
// call, to cut input-token cost and latency:
//
//  • cleanTranscript — strip filler words, collapse whitespace, and drop
//    immediately-repeated sentences (Web Speech often re-emits the same phrase).
//  • recentWindow — keep only the most recent slice (a sliding window) so a live
//    question is answered from immediate context, not a 2-hour transcript.
//
// Kept pure (no React) so it is unit-testable.
//
// Token budgets assume ~4 chars/token: 12k chars ≈ 3k tokens (live Q&A),
// 24k chars ≈ 6k tokens (summaries). Sending less recent context is also a
// privacy win — less of the meeting leaves the device per call.

// Conservative filler set: only tokens that are almost never load-bearing.
// We deliberately DON'T strip "like"/"actually"/"basically" — removing those
// corrupts real sentences ("I like this") and hurts answer quality.
const FILLER = /\b(?:u+m+|u+h+|e+r+|a+h+|hmm+|you know|i mean|sort of|kind of|you see)\b/gi

export function cleanTranscript(text: string): string {
  if (!text) return ''
  let out = text.replace(FILLER, ' ')
  out = out.replace(/\s{2,}/g, ' ').replace(/\s+([,.!?;:])/g, '$1').trim()

  // Drop immediately-repeated sentences/clauses.
  const parts = out.split(/(?<=[.!?])\s+/)
  const deduped: string[] = []
  for (const p of parts) {
    const norm = p.trim().toLowerCase()
    if (norm && norm === deduped[deduped.length - 1]?.trim().toLowerCase()) continue
    deduped.push(p)
  }
  return deduped.join(' ').trim()
}

/** Keep the last ~maxChars, cutting on a word boundary so we never split a word. */
export function recentWindow(text: string, maxChars: number): string {
  if (text.length <= maxChars) return text
  const tail = text.slice(-maxChars)
  const sp = tail.indexOf(' ')
  return (sp > 0 ? tail.slice(sp + 1) : tail).trim()
}

/** Live Q&A: clean + recent sliding window (~3k tokens of immediate context). */
export function prepareForQuery(text: string, maxChars = 12000): string {
  return recentWindow(cleanTranscript(text), maxChars)
}

/** Recap / talking points / follow-ups: clean + a larger window for breadth. */
export function prepareForSummary(text: string, maxChars = 24000): string {
  return recentWindow(cleanTranscript(text), maxChars)
}
