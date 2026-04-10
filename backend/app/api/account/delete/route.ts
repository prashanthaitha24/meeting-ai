import { NextRequest } from 'next/server'
import { stripe } from '@/lib/stripe'
import { supabaseAdmin } from '@/lib/supabase'
import { verifyAuth } from '@/lib/auth'

export const dynamic = 'force-dynamic'

// GDPR Article 17 / CCPA — Right to erasure
// Deletes all user data: Supabase profile, Supabase auth user, Stripe customer
export async function DELETE(req: NextRequest) {
  const auth = await verifyAuth(req)
  if (!auth.ok) return Response.json({ error: 'Unauthorized' }, { status: 401 })

  const userId = auth.userId!

  try {
    // 1. Get Stripe customer ID before deleting profile
    const { data: profile } = await supabaseAdmin
      .from('profiles')
      .select('stripe_customer_id, subscription_status')
      .eq('id', userId)
      .single()

    // 2. Cancel active Stripe subscription and delete customer
    if (profile?.stripe_customer_id) {
      try {
        // Cancel all active subscriptions first
        const subscriptions = await stripe.subscriptions.list({
          customer: profile.stripe_customer_id,
          status: 'active',
        })
        await Promise.all(
          subscriptions.data.map((sub) =>
            stripe.subscriptions.cancel(sub.id)
          )
        )
        // Delete the Stripe customer record
        await stripe.customers.del(profile.stripe_customer_id)
      } catch {
        // Non-fatal — log but continue deletion
      }
    }

    // 3. Delete profile row (cascades any related rows)
    await supabaseAdmin
      .from('profiles')
      .delete()
      .eq('id', userId)

    // 4. Delete the auth user entirely (removes from auth.users)
    await supabaseAdmin.auth.admin.deleteUser(userId)

    return Response.json({ success: true })
  } catch (err) {
    console.error('[account/delete]', err)
    return Response.json({ error: 'Deletion failed' }, { status: 500 })
  }
}
