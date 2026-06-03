import { describe, it, expect } from 'vitest'
import { isExamVerdict, EXAM_REFUSAL } from './exam-guard'

describe('isExamVerdict', () => {
  it('treats an explicit YES as an exam', () => {
    expect(isExamVerdict('YES')).toBe(true)
    expect(isExamVerdict('Yes.')).toBe(true)
    expect(isExamVerdict('yes, this is a proctored exam')).toBe(true)
  })

  it('treats NO / empty / null as not an exam (fail-open default)', () => {
    expect(isExamVerdict('NO')).toBe(false)
    expect(isExamVerdict('No — looks like a job interview')).toBe(false)
    expect(isExamVerdict('')).toBe(false)
    expect(isExamVerdict(null)).toBe(false)
    expect(isExamVerdict(undefined)).toBe(false)
  })

  it('does not match "yes" embedded in another word', () => {
    expect(isExamVerdict('yesterday we had a standup meeting')).toBe(false)
  })
})

describe('EXAM_REFUSAL', () => {
  it('clearly states it will not help with exam cheating', () => {
    expect(EXAM_REFUSAL.toLowerCase()).toContain('exam')
    expect(EXAM_REFUSAL.toLowerCase()).toMatch(/won'?t|cannot|can'?t/)
  })
})
