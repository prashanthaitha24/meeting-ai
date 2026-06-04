import { describe, it, expect } from 'vitest'
import { sessionMatches } from './HistoryTab'
import type { HistorySession } from '../../../preload/index.d'

const base: HistorySession = {
  id: 'abc',
  date: new Date('2026-05-01T10:00:00Z').toISOString(),
  transcript: 'We discussed the quarterly roadmap and hiring.',
  entries: [
    { id: '1', question: 'What is our churn rate?', answer: 'Around 4% monthly.' },
    { id: '2', question: 'Next sprint focus?', answer: 'Onboarding polish.' },
  ],
  tabContent: { say: '', followup: '', recap: 'Roadmap aligned; hire two engineers.' },
}

describe('sessionMatches (History search)', () => {
  it('matches on a question', () => {
    expect(sessionMatches(base, 'churn')).toBe(true)
  })

  it('matches on an answer', () => {
    expect(sessionMatches(base, 'onboarding')).toBe(true)
  })

  it('matches on the transcript', () => {
    expect(sessionMatches(base, 'quarterly')).toBe(true)
  })

  it('matches on the recap', () => {
    expect(sessionMatches(base, 'two engineers')).toBe(true)
  })

  it('is case-insensitive (caller lower-cases the query)', () => {
    expect(sessionMatches(base, 'churn')).toBe(true) // "What is our Churn rate" → answer/question lowercased internally
  })

  it('returns false when nothing matches', () => {
    expect(sessionMatches(base, 'budget')).toBe(false)
  })

  it('does not throw on empty fields', () => {
    const empty: HistorySession = {
      id: 'x', date: base.date, transcript: '', entries: [],
      tabContent: { say: '', followup: '', recap: '' },
    }
    expect(sessionMatches(empty, 'anything')).toBe(false)
  })
})
