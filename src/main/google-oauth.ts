import { BrowserWindow } from 'electron'
import * as crypto from 'crypto'
import * as http from 'http'
import { URL } from 'url'

export interface GoogleUser {
  id: string
  email: string
  name: string
  picture: string | null
}

function generatePKCE(): { verifier: string; challenge: string } {
  const verifier = crypto.randomBytes(32).toString('base64url')
  const challenge = crypto.createHash('sha256').update(verifier).digest('base64url')
  return { verifier, challenge }
}

function waitForAuthCode(port: number): Promise<{ code: string; state: string }> {
  return new Promise((resolve, reject) => {
    const server = http.createServer((req, res) => {
      if (!req.url) return
      const parsed = new URL(req.url, `http://localhost:${port}`)
      if (parsed.pathname !== '/callback') return

      const code = parsed.searchParams.get('code')
      const state = parsed.searchParams.get('state')
      const error = parsed.searchParams.get('error')

      res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8' })
      res.end(`<!DOCTYPE html><html><body style="font-family:system-ui;text-align:center;
        padding:60px 30px;background:#111;color:#eee;">
        <h2 style="color:${error ? '#ef4444' : '#22c55e'}">${error ? 'Sign-in failed' : 'Signed in!'}</h2>
        <p>${error ? `Error: ${error}` : 'You can close this window and return to Meeting AI.'}</p>
      </body></html>`)

      server.close()
      if (error || !code || !state) {
        reject(new Error(error || 'Missing auth code'))
      } else {
        resolve({ code, state })
      }
    })

    server.listen(port, '127.0.0.1')
    server.on('error', reject)

    // 5-minute timeout
    const timer = setTimeout(() => {
      server.close()
      reject(new Error('Google sign-in timed out. Please try again.'))
    }, 5 * 60 * 1000)

    server.on('close', () => clearTimeout(timer))
  })
}

export async function googleSignIn(clientId: string, clientSecret: string): Promise<GoogleUser> {
  const PORT = 43821
  const redirectUri = `http://localhost:${PORT}/callback`
  const { verifier, challenge } = generatePKCE()
  const state = crypto.randomBytes(16).toString('hex')

  const authUrl = new URL('https://accounts.google.com/o/oauth2/v2/auth')
  authUrl.searchParams.set('client_id', clientId)
  authUrl.searchParams.set('redirect_uri', redirectUri)
  authUrl.searchParams.set('response_type', 'code')
  authUrl.searchParams.set('scope', 'openid email profile')
  authUrl.searchParams.set('code_challenge', challenge)
  authUrl.searchParams.set('code_challenge_method', 'S256')
  authUrl.searchParams.set('state', state)
  authUrl.searchParams.set('prompt', 'select_account')

  const win = new BrowserWindow({
    width: 460,
    height: 640,
    show: true,
    alwaysOnTop: true,
    title: 'Sign in with Google',
    webPreferences: { nodeIntegration: false, contextIsolation: true },
  })
  win.loadURL(authUrl.toString())

  let result: { code: string; state: string }
  try {
    result = await waitForAuthCode(PORT)
  } finally {
    if (!win.isDestroyed()) win.close()
  }

  if (result.state !== state) throw new Error('Invalid OAuth state — possible CSRF')

  // Exchange code for tokens
  const tokenRes = await fetch('https://oauth2.googleapis.com/token', {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: new URLSearchParams({
      client_id: clientId,
      client_secret: clientSecret,
      code: result.code,
      code_verifier: verifier,
      grant_type: 'authorization_code',
      redirect_uri: redirectUri,
    }),
  })

  const tokens = (await tokenRes.json()) as Record<string, string>
  if (tokens.error) throw new Error(tokens.error_description || tokens.error)

  // Fetch user profile
  const userRes = await fetch('https://www.googleapis.com/oauth2/v2/userinfo', {
    headers: { Authorization: `Bearer ${tokens.access_token}` },
  })
  const user = (await userRes.json()) as Record<string, string>

  return {
    id: user.id,
    email: user.email,
    name: user.name ?? user.email,
    picture: user.picture ?? null,
  }
}
