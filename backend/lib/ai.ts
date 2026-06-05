// Chat answer streaming with provider failover.
//
// Groq (Llama 3.3 70B) is fast and cheap, but a single key on a shared rate
// limit goes down under load. To stay reliable we try Groq first and, if it's
// rate-limited or down (after retries), fall back to OpenAI so the answer still
// streams. Both providers speak the OpenAI chat-completions protocol, so the
// same client SDK and the same stream-to-text normalizer handle both.
//
// Failover happens only at CONNECT time. If Groq starts streaming then dies
// mid-answer, we don't switch providers (the user already saw partial text);
// that case is rare and handled by ending the stream.

import OpenAI from 'openai'
import { withRetry } from './retry'

const GROQ_MODEL = 'llama-3.3-70b-versatile'
// Fast, cheap OpenAI model for low-latency answers (override via OPENAI_MODEL).
const OPENAI_MODEL = process.env.OPENAI_MODEL || 'gpt-5.4-mini'
const DEFAULT_MAX_TOKENS = 1024

let _groq: OpenAI | undefined
function getGroq() {
  if (!_groq) _groq = new OpenAI({ apiKey: process.env.GROQ_API_KEY, baseURL: 'https://api.groq.com/openai/v1' })
  return _groq
}

let _openai: OpenAI | undefined
function getOpenAI() {
  if (!_openai) _openai = new OpenAI({ apiKey: process.env.OPENAI_API_KEY })
  return _openai
}

export interface ChatTurn { role: 'user' | 'assistant'; content: string }

// eslint-disable-next-line @typescript-eslint/no-explicit-any
async function* toText(stream: AsyncIterable<any>): AsyncGenerator<string> {
  for await (const chunk of stream) {
    const t = chunk.choices?.[0]?.delta?.content ?? ''
    if (t) yield t
  }
}

/**
 * Stream a chat answer, failing over from Groq to OpenAI. Resolves to an async
 * iterable of text chunks. Throws only if BOTH providers fail to connect — the
 * caller turns that into a friendly 502. If OPENAI_API_KEY is unset there is no
 * fallback and a Groq failure is surfaced directly.
 */
export async function streamChat(opts: {
  system: string
  messages: ChatTurn[]
  maxTokens?: number
}): Promise<AsyncIterable<string>> {
  const maxTokens = opts.maxTokens ?? DEFAULT_MAX_TOKENS
  const messages = [{ role: 'system' as const, content: opts.system }, ...opts.messages]

  try {
    const stream = await withRetry(
      () => getGroq().chat.completions.create({ model: GROQ_MODEL, max_tokens: maxTokens, stream: true, messages }),
      'chat:groq',
    )
    return toText(stream)
  } catch (groqErr) {
    if (!process.env.OPENAI_API_KEY) throw groqErr // no fallback configured
    console.error('[ai] Groq unavailable, falling back to OpenAI:', groqErr)
  }

  const stream = await getOpenAI().chat.completions.create({
    model: OPENAI_MODEL,
    // GPT-5-series chat completions use max_completion_tokens, not max_tokens.
    max_completion_tokens: maxTokens,
    stream: true,
    messages,
  })
  return toText(stream)
}
