import { NextRequest } from 'next/server'
import { stripe } from '@/lib/stripe'
import { supabaseAdmin } from '@/lib/supabase'
import { verifyAuth } from '@/lib/auth'

export const dynamic = 'force-dynamic'

export async function POST(req: NextRequest) {
  const auth = await verifyAuth(req)
  if (!auth.ok) {
    console.warn('[stripe/checkout] Unauthorized request')
    return Response.json({ error: 'Unauthorized' }, { status: 401 })
  }

  const body = await req.json().catch(() => ({})) as Record<string, unknown>
  const plan = body.plan === 'yearly' ? 'yearly' : 'monthly'
  console.log(`[stripe/checkout] userId=${auth.userId} plan=${plan}`)

  const priceId = plan === 'yearly'
    ? process.env.STRIPE_YEARLY_PRICE_ID!
    : process.env.STRIPE_PRICE_ID!

  try {
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
      console.log(`[stripe/checkout] Created Stripe customer for userId=${auth.userId}`)
    }

    const base = process.env.BACKEND_URL ?? 'https://meeting-ai-three-theta.vercel.app'
    const session = await stripe.checkout.sessions.create({
      customer: customerId,
      line_items: [{ price: priceId, quantity: 1 }],
      mode: 'subscription',
      success_url: `${base}/api/stripe/redirect?to=success`,
      cancel_url: `${base}/api/stripe/redirect?to=cancel`,
      metadata: { userId: auth.userId!, plan },
      subscription_data: { metadata: { userId: auth.userId!, plan } },
      allow_promotion_codes: true,
    })

    console.log(`[stripe/checkout] Session created sessionId=${session.id} plan=${plan}`)
    return Response.json({ url: session.url })
  } catch (err) {
    console.error('[stripe/checkout] Error creating checkout session', err)
    return Response.json({ error: 'Failed to create checkout session' }, { status: 500 })
  }
}
