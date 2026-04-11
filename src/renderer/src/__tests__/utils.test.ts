import { describe, it, expect } from 'vitest'

// Copied from App.tsx — extract to lib/utils.ts if this grows
function looksLikeQuestion(text: string): boolean {
  const t = text.trim().replace(/^(so|and|but|well|now|okay|ok|right|alright|um+|uh+|like)[,.]?\s+/i, '').trim()
  if (t.split(' ').length < 4) return false
  if (t.includes('?')) return true
  return /^(what|how|why|when|where|who|which|can you|could you|would you|tell me|explain|describe|walk me|talk about|give me|have you|do you|did you|are you|were you|what's|what are)/i.test(t)
}

describe('looksLikeQuestion', () => {
  it('detects explicit question marks', () => {
    expect(looksLikeQuestion('Can you tell me more about yourself?')).toBe(true)
  })

  it('detects question keywords without ?', () => {
    expect(looksLikeQuestion('What are your main strengths in this role')).toBe(true)
    expect(looksLikeQuestion('How do you handle conflict at work')).toBe(true)
    expect(looksLikeQuestion('Tell me about your experience with React')).toBe(true)
    expect(looksLikeQuestion('Explain your approach to code reviews')).toBe(true)
  })

  it('strips filler words before checking', () => {
    expect(looksLikeQuestion('So what are your thoughts on this approach')).toBe(true)
    expect(looksLikeQuestion('Well, can you walk me through your process')).toBe(true)
    expect(looksLikeQuestion('Okay, how do you prioritize your work')).toBe(true)
  })

  it('returns false for short text', () => {
    expect(looksLikeQuestion('What?')).toBe(false)
    expect(looksLikeQuestion('How are you')).toBe(false) // only 3 words
  })

  it('returns false for statements', () => {
    expect(looksLikeQuestion('I have five years of experience in software engineering')).toBe(false)
    expect(looksLikeQuestion('Thank you for your time today')).toBe(false)
    expect(looksLikeQuestion('That sounds like a great opportunity')).toBe(false)
  })

  it('returns false for empty or whitespace', () => {
    expect(looksLikeQuestion('')).toBe(false)
    expect(looksLikeQuestion('   ')).toBe(false)
  })
})
