import { createClient } from '@supabase/supabase-js'
import { safeStorage, shell, BrowserWindow } from 'electron'
import * as fs from 'fs'
import * as path from 'path'
import * as os from 'os'
import * as dotenv from 'dotenv'
import { is } from '@electron-toolkit/utils'

dotenv.config({ path: is.dev ? '.env' : path.join(process.resourcesPath, '.env') })

// These are public-facing keys — safe to hardcode (equivalent to a client-side Supabase config)
const SUPABASE_URL = process.env.SUPABASE_URL || 'https://xmobfykkusdkomxbpjsr.supabase.co'
const SUPABASE_ANON_KEY = process.env.SUPABASE_ANON_KEY || 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inhtb2JmeWtrdXNka29teGJwanNyIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzU2NjQ3ODAsImV4cCI6MjA5MTI0MDc4MH0.D5UaNqxHibyb-mVMG9BiUqQuJZSA512jGapLDcMkMSc'
const TOKENS_FILE = path.join(os.homedir(), '.meeting-ai', 'tokens')

// Supabase client — persistSession:false because we manage storage ourselves
const supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY, {
  auth: { persistSession: false, autoRefreshToken: false, detectSessionInUrl: false },
})

export interface StoredTokens {
  accessToken: string
  refreshToken: string
  expiresAt: number // unix ms
}

export interface AppSession {
  userId: string
  email: string
  name: string | null
  avatarUrl: string | null
  provider: 'google' | 'email'
  expiresAt: number
}

function ensureDir() {
  const dir = path.dirname(TOKENS_FILE)
  if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true })
}

export function storeTokens(tokens: StoredTokens): void {
  ensureDir()
  const json = JSON.stringify(tokens)
  if (safeStorage.isEncryptionAvailable()) {
    const encrypted = safeStorage.encryptString(json)
    fs.writeFileSync(TOKENS_FILE, encrypted)
  } else {
    // Fallback: store plaintext (should not happen on macOS)
    fs.writeFileSync(TOKENS_FILE + '.plain', json, 'utf8')
  }
}

export function loadTokens(): StoredTokens | null {
  try {
    if (safeStorage.isEncryptionAvailable() && fs.existsSync(TOKENS_FILE)) {
      const encrypted = fs.readFileSync(TOKENS_FILE)
      const json = safeStorage.decryptString(Buffer.from(encrypted))
      return JSON.parse(json) as StoredTokens
    }
    const plainPath = TOKENS_FILE + '.plain'
    if (fs.existsSync(plainPath)) {
      return JSON.parse(fs.readFileSync(plainPath, 'utf8')) as StoredTokens
    }
    return null
  } catch {
    return null
  }
}

export function clearTokens(): void {
  try { fs.rmSync(TOKENS_FILE) } catch {}
  try { fs.rmSync(TOKENS_FILE + '.plain') } catch {}
}

/** Returns a valid access token, refreshing if needed. Returns null if not logged in. */
export async function getAccessToken(): Promise<string | null> {
  const tokens = loadTokens()
  if (!tokens) return null

  // Token still valid (5 min buffer)
  if (tokens.expiresAt > Date.now() + 5 * 60 * 1000) {
    return tokens.accessToken
  }

  // Refresh
  try {
    const { data, error } = await supabase.auth.refreshSession({ refresh_token: tokens.refreshToken })
    if (error || !data.session) { clearTokens(); return null }
    storeTokens({
      accessToken: data.session.access_token,
      refreshToken: data.session.refresh_token,
      expiresAt: (data.session.expires_at ?? 0) * 1000,
    })
    return data.session.access_token
  } catch {
    clearTokens()
    return null
  }
}

function sessionFromSupabase(supabaseSession: {
  access_token: string; refresh_token: string; expires_at?: number
  user: { id: string; email?: string; user_metadata?: { full_name?: string; name?: string; avatar_url?: string }; app_metadata?: { provider?: string } }
}): AppSession {
  storeTokens({
    accessToken: supabaseSession.access_token,
    refreshToken: supabaseSession.refresh_token,
    expiresAt: (supabaseSession.expires_at ?? 0) * 1000,
  })
  const u = supabaseSession.user
  const provider = (u.app_metadata?.provider === 'google' ? 'google' : 'email') as 'google' | 'email'
  return {
    userId: u.id,
    email: u.email ?? '',
    name: u.user_metadata?.full_name ?? u.user_metadata?.name ?? null,
    avatarUrl: u.user_metadata?.avatar_url ?? null,
    provider,
    expiresAt: (supabaseSession.expires_at ?? 0) * 1000,
  }
}

// ── Email auth ────────────────────────────────────────────────────────────────

export async function emailSignIn(email: string, password: string): Promise<AppSession> {
  const { data, error } = await supabase.auth.signInWithPassword({ email, password })
  if (error) throw new Error(error.message)
  if (!data.session) throw new Error('No session returned')
  return sessionFromSupabase(data.session)
}

export async function emailSignUp(email: string, password: string, name: string): Promise<AppSession> {
  const { data, error } = await supabase.auth.signUp({
    email, password,
    options: { data: { full_name: name } },
  })
  if (error) throw new Error(error.message)
  if (!data.session) throw new Error('Check your email to confirm your account')
  return sessionFromSupabase(data.session)
}

// ── Google OAuth (PKCE) ───────────────────────────────────────────────────────

type OAuthPending = {
  resolve: (s: AppSession) => void
  reject: (e: Error) => void
  timer: ReturnType<typeof setTimeout>
}
let pendingOAuth: OAuthPending | null = null

let oauthWindow: BrowserWindow | null = null

function openOAuthPopup(url: string): void {
  if (oauthWindow && !oauthWindow.isDestroyed()) {
    oauthWindow.close()
  }
  oauthWindow = new BrowserWindow({
    width: 520,
    height: 640,
    title: 'Sign in',
    show: true,
    autoHideMenuBar: true,
    webPreferences: { nodeIntegration: false, contextIsolation: true },
  })
  oauthWindow.loadURL(url)

  const handleDeepLink = (navUrl: string) => {
    if (!navUrl.startsWith('meetingai://')) return false
    handleOAuthCallback(navUrl)
    if (oauthWindow && !oauthWindow.isDestroyed()) oauthWindow.close()
    oauthWindow = null
    return true
  }

  // Catch navigation-based redirects (will-navigate fires before the page loads)
  oauthWindow.webContents.on('will-navigate', (_e, navUrl) => { handleDeepLink(navUrl) })
  // Catch JS-triggered redirects (location.href = 'meetingai://...')
  oauthWindow.webContents.on('did-navigate', (_e, navUrl) => { handleDeepLink(navUrl) })
  // Some OAuth providers redirect via a new window — catch that too
  oauthWindow.webContents.setWindowOpenHandler(({ url: newUrl }) => {
    if (handleDeepLink(newUrl)) return { action: 'deny' }
    return { action: 'allow' }
  })

  oauthWindow.on('closed', () => { oauthWindow = null })
}

export async function googleSignIn(): Promise<AppSession> {
  return new Promise(async (resolve, reject) => {
    const { data, error } = await supabase.auth.signInWithOAuth({
      provider: 'google',
      options: {
        redirectTo: 'meetingai://auth/callback',
        skipBrowserRedirect: true,
        queryParams: { access_type: 'offline', prompt: 'consent' },
        scopes: 'openid email profile',
      },
    })
    if (error || !data.url) { reject(new Error(error?.message ?? 'No OAuth URL')); return }

    const timer = setTimeout(() => {
      pendingOAuth = null
      if (oauthWindow && !oauthWindow.isDestroyed()) { oauthWindow.close(); oauthWindow = null }
      reject(new Error('Sign-in timed out — please try again'))
    }, 5 * 60 * 1000)

    pendingOAuth = { resolve, reject, timer }
    openOAuthPopup(data.url)
  })
}

export async function appleSignIn(): Promise<AppSession> {
  return new Promise(async (resolve, reject) => {
    const { data, error } = await supabase.auth.signInWithOAuth({
      provider: 'apple',
      options: {
        redirectTo: 'meetingai://auth/callback',
        skipBrowserRedirect: true,
        scopes: 'name email',
      },
    })
    if (error || !data.url) { reject(new Error(error?.message ?? 'No OAuth URL')); return }

    const timer = setTimeout(() => {
      pendingOAuth = null
      if (oauthWindow && !oauthWindow.isDestroyed()) { oauthWindow.close(); oauthWindow = null }
      reject(new Error('Sign-in timed out — please try again'))
    }, 5 * 60 * 1000)

    pendingOAuth = { resolve, reject, timer }
    openOAuthPopup(data.url)
  })
}

/** Called from main process when open-url event fires */
export async function handleOAuthCallback(url: string): Promise<void> {
  if (!pendingOAuth) return
  try {
    const parsed = new URL(url)

    // PKCE flow: code comes as a query param (?code=xxx)
    const code = parsed.searchParams.get('code')
    if (code) {
      const { data, error } = await supabase.auth.exchangeCodeForSession(code)
      if (error || !data.session) {
        pendingOAuth.reject(new Error(error?.message ?? 'Failed to exchange code'))
        clearTimeout(pendingOAuth.timer)
        pendingOAuth = null
        return
      }
      const session = sessionFromSupabase(data.session)
      clearTimeout(pendingOAuth.timer)
      pendingOAuth.resolve(session)
      pendingOAuth = null
      return
    }

    // Implicit flow: tokens come in the hash fragment (#access_token=xxx&refresh_token=xxx)
    const hash = parsed.hash.startsWith('#') ? parsed.hash.slice(1) : parsed.hash
    const params = new URLSearchParams(hash)
    const accessToken = params.get('access_token')
    const refreshToken = params.get('refresh_token')
    if (accessToken && refreshToken) {
      const { data, error } = await supabase.auth.setSession({ access_token: accessToken, refresh_token: refreshToken })
      if (error || !data.session) {
        pendingOAuth.reject(new Error(error?.message ?? 'Failed to set session'))
        clearTimeout(pendingOAuth.timer)
        pendingOAuth = null
        return
      }
      const session = sessionFromSupabase(data.session)
      clearTimeout(pendingOAuth.timer)
      pendingOAuth.resolve(session)
      pendingOAuth = null
      return
    }

    pendingOAuth.reject(new Error('No auth code or tokens in callback URL'))
    clearTimeout(pendingOAuth.timer)
    pendingOAuth = null
  } catch (e) {
    pendingOAuth?.reject(e instanceof Error ? e : new Error(String(e)))
    clearTimeout(pendingOAuth?.timer!)
    pendingOAuth = null
  }
}

export async function loadSession(): Promise<AppSession | null> {
  const tokens = loadTokens()
  if (!tokens) return null

  // Validate / refresh token
  const accessToken = await getAccessToken()
  if (!accessToken) return null

  // Re-fetch user info from Supabase to get fresh data
  const { data: { user }, error } = await supabase.auth.getUser(accessToken)
  if (error || !user) { clearTokens(); return null }

  return {
    userId: user.id,
    email: user.email ?? '',
    name: user.user_metadata?.full_name ?? user.user_metadata?.name ?? null,
    avatarUrl: user.user_metadata?.avatar_url ?? null,
    provider: user.app_metadata?.provider === 'google' ? 'google' : 'email',
    expiresAt: tokens.expiresAt,
  }
}

export function logout(): void {
  clearTokens()
  supabase.auth.signOut().catch(() => {})
}
