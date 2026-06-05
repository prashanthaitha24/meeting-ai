// Multi-provider round-robin + failover for chat answers.
//
// A single provider on a shared key hits rate limits under load. Instead we keep
// a POOL of OpenAI-compatible providers and:
//   • round-robin — each request starts at the next provider, so each one only
//     sees ~1/N of traffic and stays under its own rate limit;
//   • failover — if the chosen provider errors (after retries), we fall through
//     the rest of the pool so the answer still streams.
//
// A provider is ACTIVE only if its API key env var is set, so you scale the pool
// by adding keys (and optional *_MODEL overrides) — no code change. Almost every
// fast provider speaks the OpenAI protocol, so one SDK + one normalizer covers
// all of them (Google Gemini via its OpenAI-compatible endpoint).
//
// Note: the round-robin cursor lives in module memory, so it rotates within a
// warm serverless instance; across instances each has its own cursor. That still
// spreads load well. True global round-robin would need shared state (e.g. KV).

import OpenAI from 'openai'
import { withRetry } from './retry'

const DEFAULT_MAX_TOKENS = 1024

interface ProviderSpec {
  name: string
  apiKeyEnv: string
  baseURL?: string // omitted = OpenAI default
  defaultModel: string
  modelEnv: string
  // GPT-5-series chat completions require max_completion_tokens; others use max_tokens.
  tokenParam: 'max_tokens' | 'max_completion_tokens'
}

// Order = default rotation order. Add a row + set its key env to grow the pool.
const PROVIDER_SPECS: ProviderSpec[] = [
  { name: 'groq', apiKeyEnv: 'GROQ_API_KEY', baseURL: 'https://api.groq.com/openai/v1', defaultModel: 'llama-3.3-70b-versatile', modelEnv: 'GROQ_MODEL', tokenParam: 'max_tokens' },
  { name: 'openai', apiKeyEnv: 'OPENAI_API_KEY', defaultModel: 'gpt-5.4-mini', modelEnv: 'OPENAI_MODEL', tokenParam: 'max_completion_tokens' },
  // Anthropic via its OpenAI-compatible endpoint (streaming + max_tokens supported).
  { name: 'anthropic', apiKeyEnv: 'ANTHROPIC_API_KEY', baseURL: 'https://api.anthropic.com/v1/', defaultModel: 'claude-haiku-4-5', modelEnv: 'ANTHROPIC_MODEL', tokenParam: 'max_tokens' },
  { name: 'cerebras', apiKeyEnv: 'CEREBRAS_API_KEY', baseURL: 'https://api.cerebras.ai/v1', defaultModel: 'gpt-oss-120b', modelEnv: 'CEREBRAS_MODEL', tokenParam: 'max_tokens' },
  { name: 'google', apiKeyEnv: 'GEMINI_API_KEY', baseURL: 'https://generativelanguage.googleapis.com/v1beta/openai/', defaultModel: 'gemini-2.5-flash', modelEnv: 'GEMINI_MODEL', tokenParam: 'max_tokens' },
  { name: 'together', apiKeyEnv: 'TOGETHER_API_KEY', baseURL: 'https://api.together.xyz/v1', defaultModel: 'meta-llama/Llama-3.3-70B-Instruct-Turbo', modelEnv: 'TOGETHER_MODEL', tokenParam: 'max_tokens' },
  { name: 'xai', apiKeyEnv: 'XAI_API_KEY', baseURL: 'https://api.x.ai/v1', defaultModel: 'grok-4.3', modelEnv: 'XAI_MODEL', tokenParam: 'max_tokens' },
]

interface ActiveProvider {
  name: string
  client: OpenAI
  model: string
  tokenParam: 'max_tokens' | 'max_completion_tokens'
}

let _active: ActiveProvider[] | null = null
function getActiveProviders(): ActiveProvider[] {
  if (_active) return _active
  _active = PROVIDER_SPECS.flatMap((s) => {
    const apiKey = process.env[s.apiKeyEnv]
    if (!apiKey) return []
    return [{
      name: s.name,
      client: new OpenAI({ apiKey, baseURL: s.baseURL }),
      model: process.env[s.modelEnv] || s.defaultModel,
      tokenParam: s.tokenParam,
    }]
  })
  return _active
}

let _cursor = 0

export interface ChatTurn { role: 'user' | 'assistant'; content: string }

// eslint-disable-next-line @typescript-eslint/no-explicit-any
async function* toText(stream: AsyncIterable<any>): AsyncGenerator<string> {
  for await (const chunk of stream) {
    const t = chunk.choices?.[0]?.delta?.content ?? ''
    if (t) yield t
  }
}

async function openStream(
  p: ActiveProvider,
  system: string,
  messages: ChatTurn[],
  maxTokens: number,
): Promise<AsyncIterable<string>> {
  const params = {
    model: p.model,
    stream: true,
    messages: [{ role: 'system', content: system }, ...messages],
    [p.tokenParam]: maxTokens, // max_tokens or max_completion_tokens, per provider
  }
  // Cast: the token-param key is dynamic, and stream:true guarantees an
  // async-iterable Stream at runtime regardless of the static union type.
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const stream = await withRetry(() => p.client.chat.completions.create(params as any), `chat:${p.name}`)
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  return toText(stream as any)
}

/**
 * Stream a chat answer using the provider pool: start at the next provider in
 * rotation, fall through the rest on failure. Resolves to an async iterable of
 * text chunks. Throws only if every configured provider fails to connect — the
 * caller turns that into a friendly 502.
 */
export async function streamChat(opts: {
  system: string
  messages: ChatTurn[]
  maxTokens?: number
}): Promise<AsyncIterable<string>> {
  const providers = getActiveProviders()
  if (providers.length === 0) throw new Error('No AI providers configured (set at least GROQ_API_KEY)')

  const maxTokens = opts.maxTokens ?? DEFAULT_MAX_TOKENS
  const n = providers.length
  const start = _cursor % n
  _cursor = (_cursor + 1) % n // advance so the next request starts on the next provider

  let lastErr: unknown
  for (let i = 0; i < n; i++) {
    const p = providers[(start + i) % n]
    try {
      return await openStream(p, opts.system, opts.messages, maxTokens)
    } catch (e) {
      lastErr = e
      console.error(`[ai] provider "${p.name}" failed, trying next:`, e)
    }
  }
  throw lastErr ?? new Error('All AI providers failed')
}
