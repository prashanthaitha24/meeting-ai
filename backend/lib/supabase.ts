import { createClient, SupabaseClient } from '@supabase/supabase-js'

// Admin client — only used server-side, never exposed to client
let _supabaseAdmin: SupabaseClient | undefined

export const supabaseAdmin = new Proxy({} as SupabaseClient, {
  get(_target, prop: string | symbol) {
    if (!_supabaseAdmin) {
      _supabaseAdmin = createClient(
        process.env.SUPABASE_URL!,
        process.env.SUPABASE_SERVICE_ROLE_KEY!,
        { auth: { autoRefreshToken: false, persistSession: false } }
      )
    }
    const val = (_supabaseAdmin as unknown as Record<string | symbol, unknown>)[prop]
    return typeof val === 'function' ? (val as Function).bind(_supabaseAdmin) : val
  },
})
