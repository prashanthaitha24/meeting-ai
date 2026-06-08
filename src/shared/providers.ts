// BYOK provider registry — the AI providers a user can bring their own key for.
// All four speak the OpenAI chat-completions protocol (Anthropic + Gemini via
// their OpenAI-compatible endpoints), so one calling path covers them all.
// Shared between the main process (makes the calls) and the renderer (onboarding
// UI). Keep this pure data — no electron/node/browser imports.

export type ProviderId = 'openai' | 'groq' | 'anthropic' | 'google'

export interface ProviderInfo {
  id: ProviderId
  label: string
  /** Calls go to `${baseURL}/chat/completions`. */
  baseURL: string
  defaultModel: string
  /** Model used for screen-read (vision) requests. */
  visionModel: string
  /** GPT-5-series needs max_completion_tokens; the rest use max_tokens. */
  tokenParam: 'max_tokens' | 'max_completion_tokens'
  keyPlaceholder: string
  /** Where the user gets an API key. */
  signupUrl: string
  /** One-line pitch shown in the picker. */
  blurb: string
}

export const PROVIDERS: Record<ProviderId, ProviderInfo> = {
  groq: {
    id: 'groq',
    label: 'Groq',
    baseURL: 'https://api.groq.com/openai/v1',
    defaultModel: 'llama-3.3-70b-versatile',
    visionModel: 'meta-llama/llama-4-scout-17b-16e-instruct',
    tokenParam: 'max_tokens',
    keyPlaceholder: 'gsk_...',
    signupUrl: 'https://console.groq.com/keys',
    blurb: 'Fast Llama models with a generous free tier — easiest free option.',
  },
  openai: {
    id: 'openai',
    label: 'OpenAI',
    baseURL: 'https://api.openai.com/v1',
    defaultModel: 'gpt-5.4-mini',
    visionModel: 'gpt-5.4-mini',
    tokenParam: 'max_completion_tokens',
    keyPlaceholder: 'sk-...',
    signupUrl: 'https://platform.openai.com/api-keys',
    blurb: 'GPT-5-series. Most widely used; great quality.',
  },
  anthropic: {
    id: 'anthropic',
    label: 'Anthropic (Claude)',
    baseURL: 'https://api.anthropic.com/v1',
    defaultModel: 'claude-haiku-4-5',
    visionModel: 'claude-haiku-4-5',
    tokenParam: 'max_tokens',
    keyPlaceholder: 'sk-ant-...',
    signupUrl: 'https://console.anthropic.com/settings/keys',
    blurb: 'Claude Haiku — strong reasoning, low latency.',
  },
  google: {
    id: 'google',
    label: 'Google Gemini',
    baseURL: 'https://generativelanguage.googleapis.com/v1beta/openai',
    defaultModel: 'gemini-2.5-flash',
    visionModel: 'gemini-2.5-flash',
    tokenParam: 'max_tokens',
    keyPlaceholder: 'AIza...',
    signupUrl: 'https://aistudio.google.com/apikey',
    blurb: 'Gemini Flash — generous free tier.',
  },
}

export const PROVIDER_LIST: ProviderInfo[] = [
  PROVIDERS.groq,
  PROVIDERS.openai,
  PROVIDERS.anthropic,
  PROVIDERS.google,
]
