import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import * as http from 'http'

// This file uses the REAL `http` module (no mock) to prove the dev loopback
// server actually binds, receives the provider redirect, and completes sign-in.
const signInWithOAuth = vi.fn()
const exchangeCodeForSession = vi.fn()

vi.mock('electron', () => ({
  shell: { openExternal: vi.fn() },
  safeStorage: { isEncryptionAvailable: () => false, encryptString: (s: string) => Buffer.from(s), decryptString: (b: Buffer) => b.toString() },
}))
vi.mock('@supabase/supabase-js', () => ({
  createClient: () => ({ auth: {
    signInWithOAuth: (...a: unknown[]) => signInWithOAuth(...a),
    exchangeCodeForSession: (...a: unknown[]) => exchangeCodeForSession(...a),
  } }),
}))
vi.mock('@electron-toolkit/utils', () => ({ is: { dev: true } }))
vi.mock('dotenv', () => ({ config: () => ({}) }))
// Keep token persistence off the real home directory.
vi.mock('fs', () => ({
  existsSync: () => false, mkdirSync: () => undefined, writeFileSync: () => undefined,
  readFileSync: () => '', rmSync: () => undefined,
}))

import { googleSignIn, cancelOAuth } from '../supabase-auth'

const flush = () => new Promise((r) => setTimeout(r, 0))
const httpGet = (url: string) =>
  new Promise<number>((resolve, reject) => {
    http.get(url, (res) => { res.resume(); resolve(res.statusCode ?? 0) }).on('error', reject)
  })

beforeEach(() => {
  signInWithOAuth.mockResolvedValue({ data: { url: 'https://supabase.example/authorize' }, error: null })
  exchangeCodeForSession.mockResolvedValue({
    data: { session: {
      access_token: 'at', refresh_token: 'rt', expires_at: 9999999999,
      user: { id: 'u1', email: 'me@example.com', user_metadata: { full_name: 'Me' }, app_metadata: { provider: 'google' } },
    } },
    error: null,
  })
})
afterEach(() => cancelOAuth())

describe('dev loopback OAuth (real http server)', () => {
  it('completes sign-in from a genuine GET /callback?code=…', async () => {
    const p = googleSignIn()
    await flush() // server is now listening on 127.0.0.1:9847

    const status = await httpGet('http://127.0.0.1:9847/callback?code=abc123')
    expect(status).toBe(200)

    const session = await p
    expect(exchangeCodeForSession).toHaveBeenCalledWith('abc123')
    expect(session.email).toBe('me@example.com')
    expect(session.provider).toBe('google')
  })

  it('releases the port after a completed sign-in (a second attempt can rebind)', async () => {
    const p1 = googleSignIn()
    await flush()
    await httpGet('http://127.0.0.1:9847/callback?code=first')
    await p1

    // If the server didn't close, this second listen would EADDRINUSE → reject.
    const p2 = googleSignIn()
    await flush()
    const status = await httpGet('http://127.0.0.1:9847/callback?code=second')
    expect(status).toBe(200)
    await expect(p2).resolves.toMatchObject({ email: 'me@example.com' })
  })
})
