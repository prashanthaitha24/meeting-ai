import { supabaseAdmin } from './supabase'

export interface AuthResult {
  ok: boolean
  userId?: string
  email?: string
}

export async function verifyAuth(req: Request): Promise<AuthResult> {
  const token = req.headers.get('Authorization')?.replace('Bearer ', '').trim()
  if (!token) return { ok: false }

  const { data: { user }, error } = await supabaseAdmin.auth.getUser(token)
  if (error || !user) return { ok: false }

  return { ok: true, userId: user.id, email: user.email ?? '' }
}
