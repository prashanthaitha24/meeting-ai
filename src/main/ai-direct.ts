// Direct (BYOK) provider calls from the main process. The user's chosen provider
// is OpenAI-protocol compatible, so chat + screen both POST to
// `${baseURL}/chat/completions` and we parse the standard streaming SSE.
// No backend, no founder key — the user's key calls the provider directly.

import { PROVIDERS, type ProviderId } from '../shared/providers'

export interface Creds {
  providerId: ProviderId
  model: string
  key: string
}

export interface StreamCallbacks {
  onChunk: (text: string) => void
  onDone: () => void
  onError: (message: string) => void
}

const CHAT_SYSTEM = `You are a real-time AI interview assistant. You listen to interview questions and instantly provide strong, concise answers the candidate can speak naturally.

When answering interview questions:
- Give a direct, confident answer the candidate can say out loud
- For behavioural questions use the STAR format briefly
- For technical questions be precise and use examples
- Keep answers to 3-5 sentences unless deep detail is needed
- Respond as if you are the candidate — do not refer to yourself as an AI
- If the question is unclear from context, give the most likely intended answer`

function chatSystemPrompt(transcript: string): string {
  return `${CHAT_SYSTEM}\n\nLive transcript so far:\n${transcript || '(Listening...)'}`
}

function screenPrompt(transcript: string): string {
  return `You are a real-time AI interview assistant. Look at this screenshot carefully.
Identify any interview question, coding problem, or task visible on the screen and provide a strong, concise answer the candidate can use immediately.
${transcript ? `\nMeeting transcript so far:\n${transcript.slice(-4000)}\n` : ''}
Be direct and answer as if you are the candidate. If it's a coding problem, provide working code with a brief explanation.`
}

/** Map an upstream provider failure to a short, BYOK-aware message. */
function friendlyProviderError(status: number, serverMessage?: string): string {
  if (status === 401 || status === 403) return 'Your API key was rejected. Check it in Settings → AI Provider.'
  if (status === 429) return "You've hit your provider's rate limit. Wait a few seconds and try again."
  if (/quota|insufficient|billing|credit/i.test(serverMessage || '')) {
    return 'Your provider account is out of credits. Add billing on the provider, then try again.'
  }
  if (status >= 500) return 'The AI provider is having issues right now. Please try again shortly.'
  if (serverMessage && /[a-z]\s[a-z]/i.test(serverMessage)) return serverMessage
  return 'Something went wrong talking to the AI provider. Please try again.'
}

async function streamCompletion(
  url: string,
  key: string,
  body: object,
  cb: StreamCallbacks,
): Promise<void> {
  let res: Response
  try {
    res = await fetch(url, {
      method: 'POST',
      headers: { Authorization: `Bearer ${key}`, 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    })
  } catch {
    cb.onError("Couldn't reach the AI provider. Check your internet connection.")
    return
  }

  if (!res.ok || !res.body) {
    let msg = ''
    try {
      const j = (await res.json()) as { error?: { message?: string } | string }
      msg = typeof j.error === 'string' ? j.error : j.error?.message ?? ''
    } catch {
      /* non-JSON error body */
    }
    cb.onError(friendlyProviderError(res.status, msg))
    return
  }

  try {
    const reader = res.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''
    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() ?? ''
      for (const line of lines) {
        const t = line.trim()
        if (!t.startsWith('data:')) continue
        const payload = t.slice(5).trim()
        if (payload === '[DONE]') {
          cb.onDone()
          return
        }
        try {
          const j = JSON.parse(payload) as { choices?: { delta?: { content?: string } }[] }
          const content = j.choices?.[0]?.delta?.content
          if (content) cb.onChunk(content)
        } catch {
          /* keepalive / partial line */
        }
      }
    }
    cb.onDone()
  } catch {
    cb.onError('The AI provider stream failed. Please try again.')
  }
}

export async function streamProviderChat(
  creds: Creds,
  messages: Array<{ role: 'user' | 'assistant'; content: string }>,
  transcript: string,
  cb: StreamCallbacks,
): Promise<void> {
  const p = PROVIDERS[creds.providerId]
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const body: Record<string, any> = {
    model: creds.model,
    stream: true,
    messages: [{ role: 'system', content: chatSystemPrompt(transcript) }, ...messages],
  }
  body[p.tokenParam] = 1024
  await streamCompletion(`${p.baseURL}/chat/completions`, creds.key, body, cb)
}

export async function streamProviderScreen(
  creds: Creds,
  base64: string,
  transcript: string,
  cb: StreamCallbacks,
): Promise<void> {
  const p = PROVIDERS[creds.providerId]
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const body: Record<string, any> = {
    model: p.visionModel,
    stream: true,
    messages: [
      {
        role: 'user',
        content: [
          { type: 'image_url', image_url: { url: `data:image/png;base64,${base64}` } },
          { type: 'text', text: screenPrompt(transcript) },
        ],
      },
    ],
  }
  body[p.tokenParam] = 1024
  await streamCompletion(`${p.baseURL}/chat/completions`, creds.key, body, cb)
}

/**
 * Transcribe an audio chunk with the user's own key via the provider's
 * Whisper-style endpoint. Returns '' if the provider has no transcription
 * endpoint (caller falls back to the on-device Web Speech API) or on any error.
 */
export async function transcribeProviderAudio(creds: Creds, audio: Buffer): Promise<string> {
  const p = PROVIDERS[creds.providerId]
  if (!p.transcribeModel) return ''
  try {
    const form = new FormData()
    form.append('file', new Blob([audio], { type: 'audio/webm' }), 'audio.webm')
    form.append('model', p.transcribeModel)
    const res = await fetch(`${p.baseURL}/audio/transcriptions`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${creds.key}` },
      body: form,
    })
    if (!res.ok) return ''
    const j = (await res.json()) as { text?: string }
    return j.text ?? ''
  } catch {
    return ''
  }
}

/** Validate a key with a tiny non-streaming request. */
export async function testProviderKey(
  providerId: ProviderId,
  model: string | undefined,
  key: string,
): Promise<{ ok: boolean; error?: string }> {
  const p = PROVIDERS[providerId]
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const body: Record<string, any> = { model: model || p.defaultModel, messages: [{ role: 'user', content: 'ping' }] }
  body[p.tokenParam] = 1
  try {
    const res = await fetch(`${p.baseURL}/chat/completions`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${key}`, 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    })
    if (res.ok) return { ok: true }
    let msg = ''
    try {
      const j = (await res.json()) as { error?: { message?: string } | string }
      msg = typeof j.error === 'string' ? j.error : j.error?.message ?? ''
    } catch {
      /* ignore */
    }
    return { ok: false, error: friendlyProviderError(res.status, msg) }
  } catch {
    return { ok: false, error: "Couldn't reach the provider. Check your internet connection." }
  }
}
