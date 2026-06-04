import { describe, it, expect } from 'vitest'
import { buildExportText, buildExportHtml, type ExportData } from './exportDoc'

const data: ExportData = {
  date: 'May 31, 2026, 4:00 PM',
  transcript: 'Interviewer: tell me about yourself. Candidate: sure.',
  qa: [
    { question: 'What is a closure?', answer: 'A function bundled with its lexical scope.\nIt remembers outer variables.' },
    { question: 'Reverse a linked list?', answer: 'Iterate and flip next pointers.' },
  ],
  recap: 'Strong on fundamentals.',
  say: 'Ask about scaling.',
  followup: 'What about distributed systems?',
}

describe('buildExportText', () => {
  const txt = buildExportText(data)

  it('renders each Q&A as a numbered question with its answer (not one paragraph)', () => {
    expect(txt).toContain('Q1: What is a closure?')
    expect(txt).toContain('A function bundled with its lexical scope.')
    expect(txt).toContain('Q2: Reverse a linked list?')
  })

  it('puts the conversation before the full transcript', () => {
    expect(txt.indexOf('CONVERSATION')).toBeLessThan(txt.indexOf('FULL TRANSCRIPT'))
  })

  it('preserves newlines inside an answer', () => {
    expect(txt).toContain('lexical scope.\nIt remembers outer variables.')
  })

  it('includes recap, talking points and follow-ups', () => {
    expect(txt).toContain('RECAP')
    expect(txt).toContain('TALKING POINTS')
    expect(txt).toContain('FOLLOW-UP QUESTIONS')
  })

  it('omits empty sections', () => {
    const t = buildExportText({ date: 'now', transcript: '', qa: [{ question: 'q', answer: 'a' }] })
    expect(t).not.toContain('FULL TRANSCRIPT')
    expect(t).not.toContain('RECAP')
  })
})

describe('buildExportHtml', () => {
  const html = buildExportHtml(data)

  it('marks questions and answers with distinct classes', () => {
    expect(html).toContain('class="q"')
    expect(html).toContain('class="a"')
    expect(html).toContain('Q1. What is a closure?')
  })

  it('preserves answer formatting via white-space:pre-wrap', () => {
    expect(html).toContain('white-space:pre-wrap')
  })

  it('escapes HTML-special characters to prevent broken markup', () => {
    const h = buildExportHtml({ date: 'now', transcript: '', qa: [{ question: 'a < b && c > d', answer: '<script>x</script>' }] })
    expect(h).toContain('a &lt; b &amp;&amp; c &gt; d')
    expect(h).not.toContain('<script>x</script>')
  })

  it('is a complete HTML document', () => {
    expect(html.startsWith('<!doctype html>')).toBe(true)
    expect(html).toContain('</html>')
  })
})
