import { describe, it, expect } from 'vitest'
import { isUndetectable, pickPrimaryScreenSource } from '../window-utils'

describe('isUndetectable', () => {
  it('defaults to true when no settings exist', () => {
    expect(isUndetectable(undefined)).toBe(true)
    expect(isUndetectable(null)).toBe(true)
    expect(isUndetectable({})).toBe(true)
  })

  it('stays true unless explicitly disabled', () => {
    expect(isUndetectable({ undetectable: true })).toBe(true)
    // Regression: a screen-read used to hardcode protection back to `true`,
    // overriding a user who turned undetectable mode off.
    expect(isUndetectable({ undetectable: false })).toBe(false)
  })

  it('treats non-boolean values as the default (on)', () => {
    expect(isUndetectable({ undetectable: undefined })).toBe(true)
    expect(isUndetectable({ undetectable: 0 as unknown })).toBe(true)
    expect(isUndetectable({ undetectable: 'no' as unknown })).toBe(true)
  })
})

describe('pickPrimaryScreenSource', () => {
  it('returns the first source when available', () => {
    expect(pickPrimaryScreenSource(['a', 'b'])).toBe('a')
    expect(pickPrimaryScreenSource([{ id: 1 }, { id: 2 }])).toEqual({ id: 1 })
  })

  it('returns null instead of undefined when there are no sources', () => {
    // Regression: callers used to index sources[0] blindly, handing back
    // `{ video: undefined }` / crashing when capture was denied.
    expect(pickPrimaryScreenSource([])).toBeNull()
    expect(pickPrimaryScreenSource(null)).toBeNull()
    expect(pickPrimaryScreenSource(undefined)).toBeNull()
  })
})
