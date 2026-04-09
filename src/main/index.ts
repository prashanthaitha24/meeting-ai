import {
  app, shell, BrowserWindow, globalShortcut, ipcMain,
  desktopCapturer, session, systemPreferences, protocol,
} from 'electron'
import { join } from 'path'
import { electronApp, optimizer, is } from '@electron-toolkit/utils'
import * as path from 'path'
import * as os from 'os'
import * as dotenv from 'dotenv'
import * as fs from 'fs'
import {
  emailSignIn, emailSignUp, googleSignIn, appleSignIn, handleOAuthCallback,
  loadSession, logout, getAccessToken, clearTokens,
} from './supabase-auth'

dotenv.config({ path: is.dev ? '.env' : path.join(process.resourcesPath, '.env') })

const BACKEND_URL = process.env.BACKEND_URL || 'https://meeting-ai-three-theta.vercel.app'

// Enable Web Speech API
app.commandLine.appendSwitch('enable-features', 'WebSpeechAPI')
app.commandLine.appendSwitch('enable-speech-dispatcher')

// Register meetingai:// as a privileged scheme so BrowserWindow popup can navigate to it
// Must be called before app is ready
protocol.registerSchemesAsPrivileged([
  { scheme: 'meetingai', privileges: { secure: true, standard: true, supportFetchAPI: true } },
])

// Register custom URL protocol for OAuth + Stripe callbacks
if (process.defaultApp) {
  if (process.argv.length >= 2) {
    app.setAsDefaultProtocolClient('meetingai', process.execPath, [path.resolve(process.argv[1])])
  }
} else {
  app.setAsDefaultProtocolClient('meetingai')
}

// Windows: ensure only one instance runs; pass deep-link URL to the existing instance
const gotLock = app.requestSingleInstanceLock()
if (!gotLock) {
  app.quit()
}

let mainWindow: BrowserWindow | null = null

// ── Window bounds persistence ─────────────────────────────────────────────────
const BOUNDS_FILE = path.join(os.homedir(), '.meeting-ai', 'window-bounds.json')

function loadBounds(): { x?: number; y?: number; width: number; height: number } {
  try {
    if (fs.existsSync(BOUNDS_FILE)) {
      return JSON.parse(fs.readFileSync(BOUNDS_FILE, 'utf8'))
    }
  } catch {}
  return { width: 440, height: 760 }
}

function saveBounds(win: BrowserWindow): void {
  try {
    const b = win.getBounds()
    const dir = path.dirname(BOUNDS_FILE)
    if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true })
    fs.writeFileSync(BOUNDS_FILE, JSON.stringify(b), 'utf8')
  } catch {}
}

function createWindow(): void {
  const bounds = loadBounds()

  mainWindow = new BrowserWindow({
    ...bounds,
    minWidth: 300,
    minHeight: 28,
    frame: false,
    transparent: true,
    alwaysOnTop: true,
    skipTaskbar: false,
    resizable: true,
    webPreferences: {
      preload: join(__dirname, '../preload/index.js'),
      sandbox: false,
      contextIsolation: true,
    },
  })

  const settings = loadSettings()
  mainWindow.setContentProtection(settings.undetectable !== false)
  if (process.platform === 'darwin') {
    mainWindow.setAlwaysOnTop(true, 'screen-saver', 1)
    mainWindow.setVisibleOnAllWorkspaces(true, { visibleOnFullScreen: true })
  } else {
    mainWindow.setAlwaysOnTop(true, 'pop-up-menu')
  }
  mainWindow.on('ready-to-show', () => mainWindow!.show())
  mainWindow.webContents.setWindowOpenHandler((details) => {
    shell.openExternal(details.url)
    return { action: 'deny' }
  })

  // Save bounds when window is moved or resized
  mainWindow.on('resized', () => mainWindow && saveBounds(mainWindow))
  mainWindow.on('moved', () => mainWindow && saveBounds(mainWindow))

  if (is.dev && process.env['ELECTRON_RENDERER_URL']) {
    mainWindow.loadURL(process.env['ELECTRON_RENDERER_URL'])
  } else {
    mainWindow.loadFile(join(__dirname, '../renderer/index.html'))
  }
}

// macOS: deep link via open-url event
app.on('open-url', (event, url) => {
  event.preventDefault()
  if (url.startsWith('meetingai://auth')) {
    handleOAuthCallback(url)
  } else if (url.startsWith('meetingai://stripe/success')) {
    mainWindow?.webContents.send('stripe-success')
  }
  mainWindow?.show()
  mainWindow?.focus()
})

// Windows: deep link arrives as a second-instance command-line argument
app.on('second-instance', (_event, commandLine) => {
  const url = commandLine.find((arg) => arg.startsWith('meetingai://'))
  if (url) {
    if (url.startsWith('meetingai://auth')) handleOAuthCallback(url)
    else if (url.startsWith('meetingai://stripe/success')) mainWindow?.webContents.send('stripe-success')
  }
  if (mainWindow) { mainWindow.show(); mainWindow.focus() }
})

app.whenReady().then(async () => {
  electronApp.setAppUserModelId('com.meeting-ai')

  // Handle meetingai:// URLs navigated to inside a BrowserWindow (OAuth popup)
  protocol.handle('meetingai', (request) => {
    const url = request.url
    if (url.startsWith('meetingai://auth')) {
      handleOAuthCallback(url)
    } else if (url.startsWith('meetingai://stripe/success')) {
      mainWindow?.webContents.send('stripe-success')
    }
    mainWindow?.show()
    mainWindow?.focus()
    return new Response('OK', { status: 200 })
  })

  // macOS requires explicit microphone permission prompt
  if (process.platform === 'darwin') {
    const micAccess = await systemPreferences.askForMediaAccess('microphone')
    if (!micAccess) console.warn('[Permissions] Microphone access denied')
  }

  // Windows: handle deep link from startup command-line argument
  if (process.platform === 'win32') {
    const deepLinkUrl = process.argv.find((arg) => arg.startsWith('meetingai://'))
    if (deepLinkUrl) {
      if (deepLinkUrl.startsWith('meetingai://auth')) handleOAuthCallback(deepLinkUrl)
      else if (deepLinkUrl.startsWith('meetingai://stripe/success')) {
        mainWindow?.webContents.send('stripe-success')
      }
    }
  }

  session.defaultSession.setPermissionRequestHandler((_webContents, permission, callback) => {
    callback(['media', 'audioCapture', 'microphone'].includes(permission))
  })

  session.defaultSession.setDisplayMediaRequestHandler((_request, callback) => {
    desktopCapturer.getSources({ types: ['screen'] }).then((sources) => {
      callback({ video: sources[0], audio: 'loopback' })
    })
  })

  app.on('browser-window-created', (_, window) => {
    optimizer.watchWindowShortcuts(window)
  })

  createWindow()

  globalShortcut.register('CommandOrControl+Shift+Space', () => {
    if (!mainWindow) return
    if (mainWindow.isVisible()) mainWindow.hide()
    else { mainWindow.show(); mainWindow.focus() }
  })

  globalShortcut.register('CommandOrControl+Return', async () => {
    if (!mainWindow) return
    mainWindow.show(); mainWindow.focus()
    mainWindow.webContents.send('trigger-screen-read')
  })

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow()
  })
})

app.on('window-all-closed', () => {
  app.quit() // quit on all platforms when window is closed
})

app.on('before-quit', () => {
  clearTokens() // clear session so next launch requires login
})

app.on('will-quit', () => globalShortcut.unregisterAll())

// ── Auth IPCs ─────────────────────────────────────────────────────────────────
ipcMain.handle('auth:check-session', () => loadSession())
ipcMain.handle('auth:logout', () => { logout(); return true })
ipcMain.handle('auth:email-signin', async (_e, email: string, password: string) => emailSignIn(email, password))
ipcMain.handle('auth:email-signup', async (_e, email: string, password: string, name: string) => emailSignUp(email, password, name))
ipcMain.handle('auth:google-signin', async () => googleSignIn())
ipcMain.handle('auth:apple-signin', async () => appleSignIn())

// ── Usage IPC ─────────────────────────────────────────────────────────────────
ipcMain.handle('get-usage', async () => {
  const token = await getAccessToken()
  if (!token) return null
  try {
    const res = await fetch(`${BACKEND_URL}/api/usage`, {
      headers: { Authorization: `Bearer ${token}` },
    })
    return res.ok ? await res.json() : null
  } catch { return null }
})

// ── Stripe IPCs ───────────────────────────────────────────────────────────────
ipcMain.handle('stripe:checkout', async () => {
  const token = await getAccessToken()
  if (!token) throw new Error('Not authenticated')
  const res = await fetch(`${BACKEND_URL}/api/stripe/checkout`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${token}` },
  })
  const { url } = await res.json()
  if (url) shell.openExternal(url)
})

ipcMain.handle('stripe:portal', async () => {
  const token = await getAccessToken()
  if (!token) throw new Error('Not authenticated')
  const res = await fetch(`${BACKEND_URL}/api/stripe/portal`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${token}` },
  })
  if (!res.ok) throw new Error('No active subscription')
  const { url } = await res.json()
  if (url) shell.openExternal(url)
})

// ── Desktop sources ───────────────────────────────────────────────────────────
ipcMain.handle('get-desktop-sources', async () => {
  const sources = await desktopCapturer.getSources({ types: ['screen'], fetchWindowIcons: false })
  return sources.map((s) => ({ id: s.id, name: s.name }))
})

// ── Transcribe audio (NOT counted against free limit) ─────────────────────────
ipcMain.handle('transcribe-audio', async (_event, audioData: ArrayBuffer) => {
  const token = await getAccessToken()
  if (!token) return ''
  const audioBuffer = Buffer.from(audioData)
  if (audioBuffer.length < 1000) return ''

  try {
    const formData = new FormData()
    formData.append('file', new Blob([audioBuffer], { type: 'audio/webm' }), 'audio.webm')
    const res = await fetch(`${BACKEND_URL}/api/transcribe`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}` },
      body: formData,
    })
    if (!res.ok) return ''
    const { text } = await res.json()
    return text ?? ''
  } catch { return '' }
})

// ── Helper: read SSE stream from backend and forward chunks to renderer ────────
async function streamFromBackend(url: string, token: string, body: object): Promise<void> {
  const res = await fetch(url, {
    method: 'POST',
    headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })

  if (!res.ok) {
    let errData: Record<string, unknown> = {}
    try { errData = await res.json() } catch {}
    if (res.status === 402 && errData.error === 'usage_limit_reached') {
      mainWindow?.webContents.send('usage-limit-reached', { upgradeUrl: errData.upgradeUrl })
      mainWindow?.webContents.send('chat-chunk', { text: '', done: true }) // clean up streaming state
      return
    }
    throw new Error((errData.error as string) ?? `HTTP ${res.status}`)
  }

  const reader = res.body!.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })
    const lines = buffer.split('\n')
    buffer = lines.pop() ?? ''
    for (const line of lines) {
      if (!line.startsWith('data: ')) continue
      try {
        const data = JSON.parse(line.slice(6)) as { text?: string; done?: boolean; error?: string }
        if (data.done) {
          mainWindow?.webContents.send('chat-chunk', { text: '', done: true })
        } else if (data.text) {
          mainWindow?.webContents.send('chat-chunk', { text: data.text, done: false })
        }
      } catch {}
    }
  }
}

// ── Chat ──────────────────────────────────────────────────────────────────────
ipcMain.handle('chat-with-claude', async (_event, messages: Array<{ role: string; content: string }>, transcript: string) => {
  const token = await getAccessToken()
  if (!token) throw new Error('Not authenticated')
  await streamFromBackend(`${BACKEND_URL}/api/chat`, token, { messages, transcript })
  return true
})

// ── Screen read ───────────────────────────────────────────────────────────────
ipcMain.handle('read-screen', async (_event, transcript: string) => {
  const token = await getAccessToken()
  if (!token) throw new Error('Not authenticated')

  mainWindow?.setContentProtection(false)
  await new Promise((r) => setTimeout(r, 80))
  const sources = await desktopCapturer.getSources({
    types: ['screen'],
    thumbnailSize: { width: 1920, height: 1080 },
  })
  mainWindow?.setContentProtection(true)

  const base64 = sources[0]?.thumbnail.toPNG().toString('base64')
  if (!base64) throw new Error('Could not capture screen')

  await streamFromBackend(`${BACKEND_URL}/api/screen`, token, { base64, transcript })
  return true
})

// ── Window controls ───────────────────────────────────────────────────────────
ipcMain.on('set-window-height', (_event, height: number) => {
  if (!mainWindow) return
  const [width] = mainWindow.getSize()
  mainWindow.setMinimumSize(100, 28)
  mainWindow.setSize(width, height, true)
})

ipcMain.on('set-window-size', (_event, width: number, height: number) => {
  if (!mainWindow) return
  mainWindow.setMinimumSize(100, 28)
  mainWindow.setSize(width, height, true)
})

ipcMain.on('hide-window', () => mainWindow?.hide())
ipcMain.on('close-window', () => app.quit())

// ── Settings ──────────────────────────────────────────────────────────────────
const SETTINGS_FILE = path.join(os.homedir(), '.meeting-ai', 'settings.json')

function loadSettings(): Record<string, unknown> {
  try {
    if (fs.existsSync(SETTINGS_FILE)) return JSON.parse(fs.readFileSync(SETTINGS_FILE, 'utf8'))
  } catch {}
  return { undetectable: true }
}

function saveSettings(settings: Record<string, unknown>): void {
  try {
    const dir = path.dirname(SETTINGS_FILE)
    if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true })
    fs.writeFileSync(SETTINGS_FILE, JSON.stringify(settings), 'utf8')
  } catch {}
}

ipcMain.handle('settings:load', () => loadSettings())
ipcMain.handle('settings:save', (_e, settings: Record<string, unknown>) => {
  saveSettings(settings)
  // Apply undetectable immediately
  if (typeof settings.undetectable === 'boolean') {
    mainWindow?.setContentProtection(settings.undetectable)
  }
  return true
})

// ── Open external URL (mailto:, etc.) ─────────────────────────────────────────
ipcMain.handle('open-external', (_event, url: string) => shell.openExternal(url))

// ── History ───────────────────────────────────────────────────────────────────
const HISTORY_DIR = path.join(os.homedir(), '.meeting-ai', 'history')

ipcMain.handle('history:save', (_e, userId: string, sessionData: object) => {
  try {
    if (!fs.existsSync(HISTORY_DIR)) fs.mkdirSync(HISTORY_DIR, { recursive: true })
    const file = path.join(HISTORY_DIR, `${userId}.json`)
    let sessions: object[] = []
    if (fs.existsSync(file)) {
      try { sessions = JSON.parse(fs.readFileSync(file, 'utf8')) } catch {}
    }
    sessions.unshift(sessionData)
    // Prune anything older than 90 days
    const cutoff = Date.now() - 90 * 24 * 60 * 60 * 1000
    sessions = sessions.filter((s: any) => new Date(s.date).getTime() > cutoff)
    fs.writeFileSync(file, JSON.stringify(sessions), 'utf8')
    return true
  } catch { return false }
})

ipcMain.handle('history:load', (_e, userId: string, days: number) => {
  try {
    const file = path.join(HISTORY_DIR, `${userId}.json`)
    if (!fs.existsSync(file)) return []
    const sessions: any[] = JSON.parse(fs.readFileSync(file, 'utf8'))
    const cutoff = Date.now() - days * 24 * 60 * 60 * 1000
    return sessions.filter((s) => new Date(s.date).getTime() > cutoff)
  } catch { return [] }
})

ipcMain.handle('history:clear', (_e, userId: string) => {
  try {
    const file = path.join(HISTORY_DIR, `${userId}.json`)
    if (fs.existsSync(file)) fs.rmSync(file)
    return true
  } catch { return false }
})

// ── Save notes ────────────────────────────────────────────────────────────────
ipcMain.handle('save-notes', async (_event, content: string) => {
  const { dialog } = await import('electron')
  const result = await dialog.showSaveDialog({
    defaultPath: `meeting-notes-${new Date().toISOString().slice(0, 10)}.txt`,
    filters: [{ name: 'Text Files', extensions: ['txt'] }, { name: 'All Files', extensions: ['*'] }],
  })
  if (!result.canceled && result.filePath) {
    fs.writeFileSync(result.filePath, content, 'utf8')
    return true
  }
  return false
})
