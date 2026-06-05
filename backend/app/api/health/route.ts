import { providerStatus, pingProviders } from '@/lib/ai'

export const dynamic = 'force-dynamic'

// Cache the ping result so repeated hits can't be used to burn provider tokens —
// at most one ping-set per minute regardless of request volume.
let cache: { at: number; data: unknown } | null = null
const TTL_MS = 60_000

export async function GET() {
  const now = Date.now()
  if (cache && now - cache.at < TTL_MS) {
    return Response.json({ cached: true, ...(cache.data as object) })
  }
  const ping = await pingProviders()
  const data = {
    providers: providerStatus(),
    ping,
    activeCount: ping.filter((p) => p.ok).length,
  }
  cache = { at: now, data }
  return Response.json({ cached: false, ...data })
}
