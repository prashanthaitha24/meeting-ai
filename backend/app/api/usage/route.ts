import { NextRequest } from 'next/server'
import { verifyAuth } from '@/lib/auth'
import { getUsage } from '@/lib/usage'

export const dynamic = 'force-dynamic'

export async function GET(req: NextRequest) {
  const auth = await verifyAuth(req)
  if (!auth.ok) return Response.json({ error: 'Unauthorized' }, { status: 401 })

  const usage = await getUsage(auth.userId!)
  return Response.json({
    subscriptionStatus: usage.subscriptionStatus,
    freeCallsUsed: usage.freeCallsUsed,
    freeLimit: 3,
    canMakeCall: usage.canMakeCall,
  })
}
