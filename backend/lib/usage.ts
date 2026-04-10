import { supabaseAdmin } from './supabase'

const FREE_LIMIT = 3

export interface UsageInfo {
  subscriptionStatus: 'free' | 'active' | 'canceled'
  freeCallsUsed: number
  canMakeCall: boolean
}

/** Returns today's date as YYYY-MM-DD in UTC */
function todayUTC(): string {
  return new Date().toISOString().slice(0, 10)
}

export async function getUsage(userId: string): Promise<UsageInfo> {
  const { data } = await supabaseAdmin
    .from('profiles')
    .select('subscription_status, free_calls_used, free_calls_reset_date')
    .eq('id', userId)
    .single()

  const subscriptionStatus = (data?.subscription_status ?? 'free') as UsageInfo['subscriptionStatus']
  const today = todayUTC()
  const isNewDay = data?.free_calls_reset_date !== today

  // If it's a new day, treat count as 0 and reset in DB (non-blocking)
  let freeCallsUsed = isNewDay ? 0 : (data?.free_calls_used ?? 0)
  if (isNewDay) {
    supabaseAdmin
      .from('profiles')
      .update({ free_calls_used: 0, free_calls_reset_date: today })
      .eq('id', userId)
      .then(() => {})
  }

  const canMakeCall = subscriptionStatus === 'active' || freeCallsUsed < FREE_LIMIT
  return { subscriptionStatus, freeCallsUsed, canMakeCall }
}

export async function checkAndConsume(userId: string): Promise<{ allowed: boolean; freeCallsUsed: number }> {
  const today = todayUTC()

  const { data } = await supabaseAdmin
    .from('profiles')
    .select('subscription_status, free_calls_used, free_calls_reset_date')
    .eq('id', userId)
    .single()

  const subscriptionStatus = (data?.subscription_status ?? 'free') as UsageInfo['subscriptionStatus']

  // Reset count if it's a new day
  const isNewDay = data?.free_calls_reset_date !== today
  const currentCount = isNewDay ? 0 : (data?.free_calls_used ?? 0)

  if (subscriptionStatus !== 'active' && currentCount >= FREE_LIMIT) {
    return { allowed: false, freeCallsUsed: currentCount }
  }

  // Increment for free-tier users, also writing the reset date
  if (subscriptionStatus !== 'active') {
    await supabaseAdmin
      .from('profiles')
      .update({ free_calls_used: currentCount + 1, free_calls_reset_date: today })
      .eq('id', userId)
  }

  return { allowed: true, freeCallsUsed: currentCount + 1 }
}
