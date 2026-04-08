import { NextRequest } from 'next/server'
import { stripe } from '@/lib/stripe'
import { supabaseAdmin } from '@/lib/supabase'
import { verifyAuth } from '@/lib/auth'

export async function POST(req: NextRequest) {
  const auth = await verifyAuth(req)
  if (!auth.ok) return Response.json({ error: 'Unauthorized' }, { status: 401 })

  // Get or create Stripe customer
  const { data: profile } = await supabaseAdmin
    .from('profiles')
    .select('stripe_customer_id, email, name')
    .eq('id', auth.userId)
    .single()

  let customerId = profile?.stripe_customer_id as string | undefined
  if (!customerId) {
    const customer = await stripe.customers.create({
      email: profile?.email ?? auth.email,
      name: profile?.name ?? undefined,
      metadata: { userId: auth.userId! },
    })
    customerId = customer.id
    await supabaseAdmin
      .from('profiles')
      .update({ stripe_customer_id: customerId })
      .eq('id', auth.userId)
  }

  const session = await stripe.checkout.sessions.create({
    customer: customerId,
    line_items: [{ price: process.env.STRIPE_PRICE_ID!, quantity: 1 }],
    mode: 'subscription',
    success_url: 'meetingai://stripe/success',
    cancel_url: 'meetingai://stripe/cancel',
    metadata: { userId: auth.userId! },
    subscription_data: { metadata: { userId: auth.userId! } },
    allow_promotion_codes: true,
  })

  return Response.json({ url: session.url })
}
