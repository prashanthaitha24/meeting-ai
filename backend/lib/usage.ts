import { supabaseAdmin } from './supabase'

const FREE_LIMIT = 5

export interface UsageInfo {
  subscriptionStatus: 'free' | 'active' | 'canceled'
  freeCallsUsed: number
  canMakeCall: boolean
}

export async function getUsage(userId: string): Promise<UsageInfo> {
  const { data } = await supabaseAdmin
    .from('profiles')
    .select('subscription_status, free_calls_used')
    .eq('id', userId)
    .single()

  const subscriptionStatus = (data?.subscription_status ?? 'free') as UsageInfo['subscriptionStatus']
  const freeCallsUsed = data?.free_calls_used ?? 0
  const canMakeCall = subscriptionStatus === 'active' || freeCallsUsed < FREE_LIMIT

  return { subscriptionStatus, freeCallsUsed, canMakeCall }
}

export async function incrementUsage(userId: string): Promise<void> {
  await supabaseAdmin.rpc('increment_free_calls', { user_id: userId })
}

export async function checkAndConsume(userId: string): Promise<{ allowed: boolean; freeCallsUsed: number }> {
  const usage = await getUsage(userId)
  if (!usage.canMakeCall) return { allowed: false, freeCallsUsed: usage.freeCallsUsed }

  // Only increment for free-tier users (active subscribers have unlimited)
  if (usage.subscriptionStatus !== 'active') {
    await incrementUsage(userId)
  }

  return { allowed: true, freeCallsUsed: usage.freeCallsUsed + 1 }
}
