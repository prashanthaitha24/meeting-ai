// Retry a Groq/upstream call on transient failures so brief rate-limits (429)
// or blips (5xx, network) recover automatically instead of surfacing an error
// to the user. Honors a Retry-After header when the provider sends one.
//
// Only transient statuses are retried. A 4xx like 400/401 fails fast — retrying
// a bad request or bad key just wastes time and quota.

const DEFAULT_MAX_ATTEMPTS = 3 // 1 initial + 2 retries

function statusOf(e: unknown): number | undefined {
  const anyE = e as { status?: number; response?: { status?: number } }
  return anyE?.status ?? anyE?.response?.status
}

function retryAfterMs(e: unknown): number | undefined {
  const headers = (e as { response?: { headers?: { get?: (k: string) => string | null } } })?.response?.headers
  const raw = headers?.get?.('retry-after')
  if (!raw) return undefined
  const secs = Number(raw)
  return Number.isFinite(secs) ? Math.min(secs * 1000, 5000) : undefined
}

export async function withRetry<T>(
  fn: () => Promise<T>,
  label: string,
  maxAttempts = DEFAULT_MAX_ATTEMPTS,
): Promise<T> {
  let lastErr: unknown
  for (let attempt = 1; attempt <= maxAttempts; attempt++) {
    try {
      return await fn()
    } catch (e) {
      lastErr = e
      const status = statusOf(e)
      // Retry on rate-limit, server errors, and network errors (no status).
      const transient = status === undefined || status === 429 || status >= 500
      if (!transient || attempt === maxAttempts) break
      const backoff = retryAfterMs(e) ?? 300 * 2 ** (attempt - 1) // 300ms, 600ms
      console.warn(`[${label}] attempt ${attempt}/${maxAttempts} failed (status=${status ?? 'network'}); retrying in ${backoff}ms`)
      await new Promise((r) => setTimeout(r, backoff))
    }
  }
  throw lastErr
}
