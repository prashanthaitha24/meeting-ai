import { describe, it, expect } from 'vitest'
import { friendlyHttpError, friendlyNetworkError } from '../errors'

describe('friendlyHttpError', () => {
  it('maps 5xx to a temporary-unavailable message (the HTTP 500 case)', () => {
    expect(friendlyHttpError(500)).toMatch(/temporarily unavailable/i)
    expect(friendlyHttpError(502)).toMatch(/temporarily unavailable/i)
    expect(friendlyHttpError(503)).toMatch(/temporarily unavailable/i)
  })

  it('maps auth failures to a re-sign-in message', () => {
    expect(friendlyHttpError(401)).toMatch(/sign in again/i)
    expect(friendlyHttpError(403)).toMatch(/sign in again/i)
  })

  it('maps 429 to a rate-limit message', () => {
    expect(friendlyHttpError(429)).toMatch(/lot of requests|try again/i)
  })

  it('never leaks a raw status code or "HTTP"', () => {
    for (const s of [400, 401, 429, 500, 502]) {
      expect(friendlyHttpError(s)).not.toMatch(/HTTP|\b500\b|\b502\b/)
    }
  })

  it('passes through a human-readable 4xx server message, but not a bare code', () => {
    expect(friendlyHttpError(400, 'Image is too large to process')).toBe('Image is too large to process')
    expect(friendlyHttpError(400, 'invalid_body')).toMatch(/something went wrong/i) // code, not prose → generic
  })
})

describe('friendlyNetworkError', () => {
  it('mentions connectivity', () => {
    expect(friendlyNetworkError()).toMatch(/internet|connection|reach/i)
  })
})
