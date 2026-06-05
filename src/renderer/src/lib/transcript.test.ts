import { describe, it, expect } from 'vitest'
import { cleanTranscript, recentWindow, prepareForQuery } from './transcript'

describe('cleanTranscript', () => {
  it('strips common filler words', () => {
    const out = cleanTranscript('So um, you know, we uh need to, I mean, ship it')
    expect(out).not.toMatch(/\bum\b/i)
    expect(out).not.toMatch(/you know/i)
    expect(out).not.toMatch(/i mean/i)
    expect(out).toContain('ship it')
  })

  it('does NOT strip load-bearing words like "like" or "actually"', () => {
    const out = cleanTranscript('I actually like this approach')
    expect(out).toContain('actually')
    expect(out).toContain('like')
  })

  it('collapses extra whitespace and fixes spacing before punctuation', () => {
    expect(cleanTranscript('hello    world ,  ok')).toBe('hello world, ok')
  })

  it('drops immediately-repeated sentences (Web Speech double-emit)', () => {
    expect(cleanTranscript('What is your name? What is your name? Tell me.')).toBe(
      'What is your name? Tell me.',
    )
  })

  it('returns empty string for empty input', () => {
    expect(cleanTranscript('')).toBe('')
  })
})

describe('recentWindow', () => {
  it('returns text unchanged when under the limit', () => {
    expect(recentWindow('short text', 100)).toBe('short text')
  })

  it('keeps the most recent slice, not the beginning', () => {
    const text = 'START ' + 'x '.repeat(100) + 'END'
    const out = recentWindow(text, 20)
    expect(out).toContain('END')
    expect(out).not.toContain('START')
  })

  it('cuts on a word boundary (no split words)', () => {
    const out = recentWindow('alpha bravo charlie delta', 12)
    expect(out.startsWith('bravo') || out.startsWith('charlie') || out.startsWith('delta')).toBe(true)
  })
})

describe('prepareForQuery', () => {
  it('cleans then windows to recent context', () => {
    const long = 'old stuff. '.repeat(2000) + 'um what is the latest question'
    const out = prepareForQuery(long, 200)
    expect(out.length).toBeLessThanOrEqual(200)
    expect(out).toContain('what is the latest question')
    expect(out).not.toMatch(/\bum\b/i)
  })
})
