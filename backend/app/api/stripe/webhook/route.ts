import { NextRequest } from 'next/server'
import { stripe } from '@/lib/stripe'
import { supabaseAdmin } from '@/lib/supabase'
import Stripe from 'stripe'

export const dynamic = 'force-dynamic'

export async function POST(req: NextRequest) {
  const body = await req.text()
  const sig = req.headers.get('stripe-signature')
  if (!sig) return Response.json({ error: 'No signature' }, { status: 400 })

  let event: Stripe.Event
  try {
    event = stripe.webhooks.constructEvent(body, sig, process.env.STRIPE_WEBHOOK_SECRET!)
  } catch {
    return Response.json({ error: 'Invalid signature' }, { status: 400 })
  }

  const getUserId = (obj: { metadata?: { userId?: string } | null }) => obj.metadata?.userId

  switch (event.type) {
    case 'checkout.session.completed': {
      const session = event.data.object as Stripe.Checkout.Session
      const userId = getUserId(session)
      if (!userId) break
      await supabaseAdmin
        .from('profiles')
        .update({
          subscription_status: 'active',
          subscription_id: session.subscription as string,
        })
        .eq('id', userId)
      break
    }
    case 'customer.subscription.updated': {
      const sub = event.data.object as Stripe.Subscription
      const userId = getUserId(sub)
      if (!userId) break
      const status = sub.status === 'active' ? 'active' : 'past_due'
      await supabaseAdmin
        .from('profiles')
        .update({ subscription_status: status })
        .eq('id', userId)
      break
    }
    case 'customer.subscription.deleted': {
      const sub = event.data.object as Stripe.Subscription
      const userId = getUserId(sub)
      if (!userId) break
      await supabaseAdmin
        .from('profiles')
        .update({ subscription_status: 'canceled', subscription_id: null })
        .eq('id', userId)
      break
    }
  }

  return Response.json({ received: true })
}
