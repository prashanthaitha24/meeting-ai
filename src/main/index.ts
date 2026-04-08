import {
  app, shell, BrowserWindow, globalShortcut, ipcMain,
  desktopCapturer, session, systemPreferences,
} from 'electron'
import { join } from 'path'
import { electronApp, optimizer, is } from '@electron-toolkit/utils'
import * as path from 'path'
import * as dotenv from 'dotenv'
import * as fs from 'fs'
import {
  emailSignIn, emailSignUp, googleSignIn, handleOAuthCallback,
  loadSession, logout, getAccessToken,
} from './supabase-auth'

dotenv.config({ path: is.dev ? '.env' : path.join(process.resourcesPath, '.env') })

const BACKEND_URL = process.env.BACKEND_URL!

// Enable Web Speech API
app.commandLine.appendSwitch('enable-features', 'WebSpeechAPI')
app.commandLine.appendSwitch('enable-speech-dispatcher')

// Register custom URL protocol for OAuth + Stripe callbacks
if (process.defaultApp) {
  if (process.argv.length >= 2) {
    app.setAsDefaultProtocolClient('meetingai', process.execPath, [path.resolve(process.argv[1])])
  }
} else {
  app.setAsDefaultProtocolClient('meetingai')
}

let mainWindow: BrowserWindow | null = null

function createWindow(): void {
  mainWindow = new BrowserWindow({
    width: 440,
    height: 760,
    minWidth: 100,
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

  mainWindow.setContentProtection(true)
  mainWindow.setAlwaysOnTop(true, 'screen-saver', 1)
  mainWindow.setVisibleOnAllWorkspaces(true, { visibleOnFullScreen: true })
  mainWindow.on('ready-to-show', () => mainWindow!.show())
  mainWindow.webContents.setWindowOpenHandler((details) => {
    shell.openExternal(details.url)
    return { action: 'deny' }
  })

  if (is.dev && process.env['ELECTRON_RENDERER_URL']) {
    mainWindow.loadURL(process.env['ELECTRON_RENDERER_URL'])
  } else {
    mainWindow.loadFile(join(__dirname, '../renderer/index.html'))
  }
}

// Handle OAuth and Stripe callbacks from the custom URL scheme
app.on('open-url', (event, url) => {
  event.preventDefault()
  if (url.startsWith('meetingai://auth/callback')) {
    handleOAuthCallback(url)
  } else if (url.startsWith('meetingai://stripe/success')) {
    mainWindow?.webContents.send('stripe-success')
  }
  // Bring app to front
  mainWindow?.show()
  mainWindow?.focus()
})

app.whenReady().then(async () => {
  electronApp.setAppUserModelId('com.meeting-ai')

  if (process.platform === 'darwin') {
    const micAccess = await systemPreferences.askForMediaAccess('microphone')
    if (!micAccess) console.warn('[Permissions] Microphone access denied')
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
  if (process.platform !== 'darwin') app.quit()
})

app.on('will-quit', () => globalShortcut.unregisterAll())

// ── Auth IPCs ─────────────────────────────────────────────────────────────────
ipcMain.handle('auth:check-session', () => loadSession())
ipcMain.handle('auth:logout', () => { logout(); return true })
ipcMain.handle('auth:email-signin', async (_e, email: string, password: string) => emailSignIn(email, password))
ipcMain.handle('auth:email-signup', async (_e, email: string, password: string, name: string) => emailSignUp(email, password, name))
ipcMain.handle('auth:google-signin', async () => googleSignIn())

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
ipcMain.on('close-window', () => mainWindow?.close())

// ── Open external URL (mailto:, etc.) ─────────────────────────────────────────
ipcMain.handle('open-external', (_event, url: string) => shell.openExternal(url))

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
