import {
  app,
  shell,
  BrowserWindow,
  globalShortcut,
  ipcMain,
  desktopCapturer,
  session,
  systemPreferences,
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

// Enable Web Speech API in Electron's Chromium
app.commandLine.appendSwitch('enable-features', 'WebSpeechAPI')
app.commandLine.appendSwitch('enable-speech-dispatcher')

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
    width: 440,
    height: 760,
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

app.whenReady().then(async () => {
  electronApp.setAppUserModelId('com.meeting-ai')

  // Request macOS microphone permission upfront
  if (process.platform === 'darwin') {
    const micAccess = await systemPreferences.askForMediaAccess('microphone')
    if (!micAccess) console.warn('[Permissions] Microphone access denied by user')
  }

  // Allow microphone access for Web Speech API and getUserMedia
  session.defaultSession.setPermissionRequestHandler((_webContents, permission, callback) => {
    const allowed = ['media', 'audioCapture', 'microphone']
    callback(allowed.includes(permission))
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

  // Cmd+Enter — capture screen and answer whatever is visible
  globalShortcut.register('CommandOrControl+Return', async () => {
    if (!mainWindow) return
    mainWindow.show()
    mainWindow.focus()
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

// ── IPC: Transcribe audio via Groq Whisper (free tier, native fetch) ─────────
ipcMain.handle('transcribe-audio', async (_event, audioData: ArrayBuffer) => {
  const apiKey = process.env.GROQ_API_KEY
  if (!apiKey) return ''

  const audioBuffer = Buffer.from(audioData)
  if (audioBuffer.length < 1000) return ''

  try {
    const formData = new FormData()
    formData.append('file', new Blob([audioBuffer], { type: 'audio/webm' }), 'audio.webm')
    formData.append('model', 'whisper-large-v3-turbo')
    formData.append('response_format', 'text')
    formData.append('language', 'en')

    const response = await fetch('https://api.groq.com/openai/v1/audio/transcriptions', {
      method: 'POST',
      headers: { Authorization: `Bearer ${apiKey}` },
      body: formData,
    })

    if (!response.ok) {
      console.warn('[Groq Whisper] error:', response.status, await response.text())
      return ''
    }
    return (await response.text()).trim()
  } catch (e) {
    console.warn('[Groq Whisper] failed:', (e as Error).message)
    return ''
  }
})

// ── IPC: Chat — local insight first, GPT-4o as fallback ──────────────────
ipcMain.handle(
  'chat-with-claude',
  async (_event, messages: Array<{ role: string; content: string }>, transcript: string) => {
    // Cloud LLM path — Groq (free tier, fast)
    const apiKey = process.env.GROQ_API_KEY
    if (!apiKey) throw new Error('GROQ_API_KEY not set in .env — get a free key at console.groq.com')
    const groq = new OpenAI({ apiKey, baseURL: 'https://api.groq.com/openai/v1' })

    const systemPrompt = `You are a real-time AI interview assistant. You listen to interview questions and instantly provide strong, concise answers the candidate can speak naturally.

Live transcript so far:
${transcript || '(Listening...)'}

When answering interview questions:
- Give a direct, confident answer the candidate can say out loud
- For behavioural questions use the STAR format briefly
- For technical questions be precise and use examples
- Keep answers to 3-5 sentences unless deep detail is needed
- Never say "As an AI..." — respond as if you are the candidate
- If the question is unclear from context, give the most likely intended answer`

    const stream = await groq.chat.completions.create({
      model: 'llama-3.3-70b-versatile',
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

// ── IPC: Screen capture → Groq vision → answer ───────────────────────────
ipcMain.handle('read-screen', async (_event, transcript: string) => {
  const apiKey = process.env.GROQ_API_KEY
  if (!apiKey) throw new Error('GROQ_API_KEY not set')

  // Temporarily disable content protection so the screenshot includes everything
  mainWindow?.setContentProtection(false)
  await new Promise((r) => setTimeout(r, 80))

  const sources = await desktopCapturer.getSources({
    types: ['screen'],
    thumbnailSize: { width: 1920, height: 1080 },
  })

  mainWindow?.setContentProtection(true)

  const base64 = sources[0]?.thumbnail.toPNG().toString('base64')
  if (!base64) throw new Error('Could not capture screen')

  const groq = new OpenAI({ apiKey, baseURL: 'https://api.groq.com/openai/v1' })

  const stream = await groq.chat.completions.create({
    model: 'meta-llama/llama-4-scout-17b-16e-instruct',
    max_tokens: 1024,
    stream: true,
    messages: [
      {
        role: 'user',
        content: [
          { type: 'image_url', image_url: { url: `data:image/png;base64,${base64}` } },
          {
            type: 'text',
            text: `You are a real-time AI interview assistant. Look at this screenshot carefully.
Identify any interview question, coding problem, or task visible on the screen and provide a strong, concise answer the candidate can use immediately.

${transcript ? `Meeting transcript so far:\n${transcript}\n` : ''}
Be direct and answer as if you are the candidate. If it's a coding problem, provide working code with a brief explanation.`,
          },
        ],
      },
    ],
  })

  for await (const chunk of stream) {
    const text = chunk.choices[0]?.delta?.content ?? ''
    if (text) mainWindow?.webContents.send('chat-chunk', { text, done: false })
  }
  mainWindow?.webContents.send('chat-chunk', { text: '', done: true })
  return true
})

// ── IPC: Window sizing (collapse / expand) ────────────────────────────────
ipcMain.on('set-window-height', (_event, height: number) => {
  if (!mainWindow) return
  const [width] = mainWindow.getSize()
  mainWindow.setMinimumSize(320, 40)
  mainWindow.setSize(width, height, true)
})

ipcMain.on('hide-window', () => mainWindow?.hide())
ipcMain.on('close-window', () => mainWindow?.close())

// ── IPC: Open external URL (for mailto:, etc.) ────────────────────────────
ipcMain.handle('open-external', (_event, url: string) => shell.openExternal(url))

// ── IPC: Save notes as PDF via save dialog ────────────────────────────────
ipcMain.handle('save-notes', async (_event, content: string) => {
  const { dialog } = await import('electron')
  const result = await dialog.showSaveDialog({
    defaultPath: `meeting-notes-${new Date().toISOString().slice(0, 10)}.txt`,
    filters: [
      { name: 'Text Files', extensions: ['txt'] },
      { name: 'All Files', extensions: ['*'] },
    ],
  })
  if (!result.canceled && result.filePath) {
    fs.writeFileSync(result.filePath, content, 'utf8')
    return true
  }
  return false
})
