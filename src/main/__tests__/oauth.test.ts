import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'

// ── Mocks for the Electron + Supabase + http boundary ─────────────────────────
const openExternal = vi.fn()
const signInWithOAuth = vi.fn()

// http.createServer is mocked so the loopback server never binds a real port.
const { fakeServer, createServer, listen, close } = vi.hoisted(() => {
  const listen = vi.fn()
  const close = vi.fn()
  const fakeServer = { listen, close, on: vi.fn() }
  return { fakeServer, createServer: vi.fn(() => fakeServer), listen, close }
})

vi.mock('http', () => ({ createServer }))
vi.mock('electron', () => ({
  shell: { openExternal: (...args: unknown[]) => openExternal(...args) },
  safeStorage: {
    isEncryptionAvailable: () => false,
    encryptString: (s: string) => Buffer.from(s),
    decryptString: (b: Buffer) => b.toString(),
  },
}))
vi.mock('@supabase/supabase-js', () => ({
  createClient: () => ({ auth: { signInWithOAuth: (...a: unknown[]) => signInWithOAuth(...a) } }),
}))
vi.mock('@electron-toolkit/utils', () => ({ is: { dev: true } }))
vi.mock('dotenv', () => ({ config: () => ({}) }))

import { googleSignIn, cancelOAuth, oauthRedirectUrl } from '../supabase-auth'

// Let the async promise executor reach startOAuth() before we act.
const flush = () => new Promise((r) => setTimeout(r, 0))

beforeEach(() => {
  openExternal.mockReset()
  signInWithOAuth.mockReset()
  createServer.mockClear(); listen.mockClear(); close.mockClear()
  fakeServer.on.mockClear()
  signInWithOAuth.mockResolvedValue({ data: { url: 'https://supabase.example/authorize' }, error: null })
})

afterEach(() => {
  // Settle any attempt still pending so its 5-min timer can't leak.
  cancelOAuth()
})

describe('oauthRedirectUrl', () => {
  it('uses the loopback server in dev and the custom scheme in prod', () => {
    expect(oauthRedirectUrl(true)).toBe('http://127.0.0.1:9847/callback')
    expect(oauthRedirectUrl(false)).toBe('meetingai://auth/callback')
  })
})

describe('googleSignIn (system-browser flow)', () => {
  it('opens the OAuth URL in the external browser, not an embedded window', async () => {
    const p = googleSignIn()
    await flush()
    expect(openExternal).toHaveBeenCalledWith('https://supabase.example/authorize')
    cancelOAuth()
    await expect(p).rejects.toThrow(/cancelled/i)
  })

  it('starts a local loopback server in dev before opening the browser', async () => {
    const p = googleSignIn()
    await flush()
    expect(createServer).toHaveBeenCalledTimes(1)
    expect(listen).toHaveBeenCalledWith(9847, '127.0.0.1')
    cancelOAuth()
    await expect(p).rejects.toThrow(/cancelled/i)
    // Cancelling tears the server down so the port is released.
    expect(close).toHaveBeenCalled()
  })

  it('cancelOAuth rejects the pending promise instead of hanging forever', async () => {
    // Regression: closing the sign-in window used to leave the promise
    // unsettled, so the UI spun on "checking for sign-in" indefinitely.
    const p = googleSignIn()
    await flush()
    cancelOAuth()
    await expect(p).rejects.toThrow(/cancelled/i)
  })

  it('starting a new attempt rejects the previous one', async () => {
    const first = googleSignIn()
    // Attach the rejection handler before the restart so the (expected)
    // rejection isn't briefly flagged as unhandled.
    const firstRejected = expect(first).rejects.toThrow(/restarted/i)
    await flush()
    const second = googleSignIn()
    await flush()
    await firstRejected
    cancelOAuth()
    await expect(second).rejects.toThrow(/cancelled/i)
  })

  it('rejects when Supabase returns no URL', async () => {
    signInWithOAuth.mockResolvedValueOnce({ data: { url: null }, error: null })
    await expect(googleSignIn()).rejects.toThrow(/No OAuth URL/i)
    expect(openExternal).not.toHaveBeenCalled()
    expect(createServer).not.toHaveBeenCalled()
  })
})
