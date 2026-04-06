import {
  app,
  shell,
  BrowserWindow,
  globalShortcut,
  ipcMain,
  desktopCapturer,
  session,
} from 'electron'
import { join } from 'path'
import { electronApp, optimizer, is } from '@electron-toolkit/utils'
import OpenAI from 'openai'
import * as fs from 'fs'
import * as os from 'os'
import * as path from 'path'
import * as dotenv from 'dotenv'

import { loadSession, saveSession, clearSession, buildSession } from './session-store'
import { emailSignIn, emailSignUp } from './email-auth'
import { googleSignIn } from './google-oauth'

dotenv.config({ path: is.dev ? '.env' : path.join(process.resourcesPath, '.env') })

let mainWindow: BrowserWindow | null = null

// ── Cost-saving: attempt local insight before calling GPT-4o ──────────────
function tryLocalInsight(question: string, transcript: string): string | null {
  if (!transcript || transcript.trim().length < 80) return null
  const q = question.toLowerCase().trim()
  const sentences = transcript
    .split(/(?<=[.!?])\s+/)
    .map((s) => s.trim())
    .filter((s) => s.length > 15)

  if (sentences.length === 0) return null

  // Simple summary: spread key sentences across transcript
  if (/^(summarize|summary|tldr|brief|what was (said|discussed)|give me a (summary|recap))/i.test(q)) {
    if (sentences.length <= 4) return `Transcript so far:\n\n${transcript.trim()}`
    const indices = [0, Math.floor(sentences.length * 0.33), Math.floor(sentences.length * 0.66), sentences.length - 1]
    const key = [...new Set(indices)].map((i) => sentences[i])
    return `**Summary** (local):\n\n${key.map((s) => `• ${s}`).join('\n')}\n\n*Ask a specific question for AI-powered insights.*`
  }

  // Action items
  if (/action item|to[- ]?do|follow[- ]?up|next step|who (will|should|is going)/i.test(q)) {
    const pattern = /\b(will|should|going to|need to|have to|must|plan to|action|assigned|follow.?up)\b/i
    const items = sentences.filter((s) => pattern.test(s)).slice(0, 8)
    if (items.length > 0) {
      return `**Action items** (local):\n\n${items.map((s) => `☐ ${s}`).join('\n')}\n\n*Ask for AI analysis for more context.*`
    }
    return 'No clear action items detected yet — the recording may need more time.'
  }

  return null // fall through to GPT-4o
}

function createWindow(): void {
  mainWindow = new BrowserWindow({
    width: 420,
    height: 680,
    minWidth: 320,
    minHeight: 40,
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

app.whenReady().then(() => {
  electronApp.setAppUserModelId('com.meeting-ai')

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

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow()
  })
})

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit()
})

app.on('will-quit', () => globalShortcut.unregisterAll())

// ── Auth: check session ───────────────────────────────────────────────────
ipcMain.handle('auth:check-session', () => loadSession())

// ── Auth: logout ──────────────────────────────────────────────────────────
ipcMain.handle('auth:logout', () => { clearSession(); return true })

// ── Auth: email sign-in ───────────────────────────────────────────────────
ipcMain.handle('auth:email-signin', async (_e, email: string, password: string) => {
  const user = await emailSignIn(email, password)
  const s = buildSession({ userId: user.userId, email: user.email, name: user.name, avatarUrl: null, provider: 'email' })
  saveSession(s)
  return s
})

// ── Auth: email sign-up ───────────────────────────────────────────────────
ipcMain.handle('auth:email-signup', async (_e, email: string, password: string, name: string) => {
  const user = await emailSignUp(email, password, name)
  const s = buildSession({ userId: user.userId, email: user.email, name: user.name, avatarUrl: null, provider: 'email' })
  saveSession(s)
  return s
})

// ── Auth: Google OAuth PKCE ───────────────────────────────────────────────
ipcMain.handle('auth:google-signin', async () => {
  const clientId = process.env.GOOGLE_CLIENT_ID
  const clientSecret = process.env.GOOGLE_CLIENT_SECRET
  if (!clientId || !clientSecret) {
    throw new Error('GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET must be set in .env')
  }
  const user = await googleSignIn(clientId, clientSecret)
  const s = buildSession({ userId: user.id, email: user.email, name: user.name, avatarUrl: user.picture, provider: 'google' })
  saveSession(s)
  return s
})

// ── IPC: Get screen sources ───────────────────────────────────────────────
ipcMain.handle('get-desktop-sources', async () => {
  const sources = await desktopCapturer.getSources({ types: ['screen'], fetchWindowIcons: false })
  return sources.map((s) => ({ id: s.id, name: s.name }))
})

// ── IPC: Transcribe audio via Whisper (system audio fallback) ─────────────
ipcMain.handle('transcribe-audio', async (_event, audioData: ArrayBuffer) => {
  const apiKey = process.env.OPENAI_API_KEY
  if (!apiKey) throw new Error('OPENAI_API_KEY not set in .env')

  const openai = new OpenAI({ apiKey })
  const tmpFile = path.join(os.tmpdir(), `meeting-ai-${Date.now()}.webm`)
  try {
    fs.writeFileSync(tmpFile, Buffer.from(audioData))
    const transcription = await openai.audio.transcriptions.create({
      file: fs.createReadStream(tmpFile),
      model: 'whisper-1',
      response_format: 'text',
    })
    return transcription as unknown as string
  } finally {
    if (fs.existsSync(tmpFile)) fs.unlinkSync(tmpFile)
  }
})

// ── IPC: Chat — local insight first, GPT-4o as fallback ──────────────────
ipcMain.handle(
  'chat-with-claude',
  async (_event, messages: Array<{ role: string; content: string }>, transcript: string) => {
    const lastUserMsg = [...messages].reverse().find((m) => m.role === 'user')?.content ?? ''

    // Try answering locally before spending API credits
    const localAnswer = tryLocalInsight(lastUserMsg, transcript)
    if (localAnswer) {
      mainWindow?.webContents.send('chat-chunk', { text: localAnswer, done: false })
      mainWindow?.webContents.send('chat-chunk', { text: '', done: true })
      return true
    }

    // Cloud LLM path
    const apiKey = process.env.OPENAI_API_KEY
    if (!apiKey) throw new Error('OPENAI_API_KEY not set in .env')
    const openai = new OpenAI({ apiKey })

    const systemPrompt = `You are an intelligent real-time meeting assistant. You listen to meetings and help the user understand discussions, answer questions, summarize points, and provide insights.

Live meeting transcript so far:
${transcript || '(Recording just started — nothing transcribed yet)'}

Guidelines:
- Be concise and direct
- Reference specific parts of the transcript when relevant
- If asked to summarize, highlight key decisions and action items
- If the transcript is empty, say the recording just started`

    const stream = await openai.chat.completions.create({
      model: 'gpt-4o',
      max_tokens: 1024,
      stream: true,
      messages: [
        { role: 'system', content: systemPrompt },
        ...messages.map((m) => ({ role: m.role as 'user' | 'assistant', content: m.content })),
      ],
    })

    for await (const chunk of stream) {
      const text = chunk.choices[0]?.delta?.content ?? ''
      if (text) mainWindow?.webContents.send('chat-chunk', { text, done: false })
    }
    mainWindow?.webContents.send('chat-chunk', { text: '', done: true })
    return true
  }
)

// ── IPC: Window sizing (collapse / expand) ────────────────────────────────
ipcMain.on('set-window-height', (_event, height: number) => {
  if (!mainWindow) return
  const [width] = mainWindow.getSize()
  mainWindow.setMinimumSize(320, 40)
  mainWindow.setSize(width, height, true)
})

ipcMain.on('hide-window', () => mainWindow?.hide())
ipcMain.on('close-window', () => mainWindow?.close())
