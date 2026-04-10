import { NextRequest } from 'next/server'
import { supabaseAdmin } from '@/lib/supabase'
import { verifyAuth } from '@/lib/auth'

export const dynamic = 'force-dynamic'

// GDPR Article 20 / CCPA — Right to data portability
// Returns everything we hold on the user as JSON
export async function GET(req: NextRequest) {
  const auth = await verifyAuth(req)
  if (!auth.ok) return Response.json({ error: 'Unauthorized' }, { status: 401 })

  const { data: profile } = await supabaseAdmin
    .from('profiles')
    .select('email, name, avatar_url, subscription_status, free_calls_used, created_at')
    .eq('id', auth.userId!)
    .single()

  const export_data = {
    exported_at: new Date().toISOString(),
    account: {
      email: profile?.email,
      name: profile?.name,
      created_at: profile?.created_at,
      subscription_status: profile?.subscription_status,
    },
    usage: {
      free_calls_used: profile?.free_calls_used,
    },
    note: 'Meeting transcripts and session history are stored locally on your device only and are not held on our servers.',
  }

  return new Response(JSON.stringify(export_data, null, 2), {
    status: 200,
    headers: {
      'Content-Type': 'application/json',
      'Content-Disposition': `attachment; filename="thavionai-data-export-${new Date().toISOString().slice(0, 10)}.json"`,
    },
  })
}
