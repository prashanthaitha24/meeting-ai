import { NextRequest } from 'next/server'
import OpenAI from 'openai'
import { verifyAuth } from '@/lib/auth'
import { checkAndConsume } from '@/lib/usage'

export const dynamic = 'force-dynamic'

const enc = new TextEncoder()
let _groq: OpenAI | undefined
function getGroq() {
  if (!_groq) _groq = new OpenAI({ apiKey: process.env.GROQ_API_KEY, baseURL: 'https://api.groq.com/openai/v1' })
  return _groq
}
function sse(data: object) { return enc.encode(`data: ${JSON.stringify(data)}\n\n`) }

export async function POST(req: NextRequest) {
  const auth = await verifyAuth(req)
  if (!auth.ok) return Response.json({ error: 'Unauthorized' }, { status: 401 })

  const usage = await checkAndConsume(auth.userId!)
  if (!usage.allowed) {
    return Response.json(
      { error: 'usage_limit_reached', upgradeUrl: process.env.STRIPE_PAYMENT_LINK },
      { status: 402 }
    )
  }

  let base64 = ''
  let transcript = ''
  try {
    const body = await req.json()
    base64 = body.base64 ?? ''
    transcript = body.transcript ?? ''
  } catch {
    return Response.json({ error: 'Invalid body' }, { status: 400 })
  }

  if (!base64 || base64.length > 10 * 1024 * 1024) {
    return Response.json({ error: 'Invalid image' }, { status: 400 })
  }

  const stream = await getGroq().chat.completions.create({
    model: 'meta-llama/llama-4-scout-17b-16e-instruct',
    max_tokens: 1024,
    stream: true,
    messages: [
      {
        role: 'user',
        content: [
          { type: 'image_url', image_url: { url: `data:image/png;base64,${base64}` } },
          {
            type: 'text',
            text: `You are a real-time AI interview assistant. Look at this screenshot carefully.
Identify any interview question, coding problem, or task visible on the screen and provide a strong, concise answer the candidate can use immediately.
${transcript ? `\nMeeting transcript so far:\n${transcript.slice(0, 4000)}\n` : ''}
Be direct and answer as if you are the candidate. If it's a coding problem, provide working code with a brief explanation.`,
          },
        ],
      },
    ],
  })

  const readable = new ReadableStream({
    async start(controller) {
      try {
        for await (const chunk of stream) {
          const text = chunk.choices[0]?.delta?.content ?? ''
          if (text) controller.enqueue(sse({ text }))
        }
        controller.enqueue(sse({ done: true }))
      } finally {
        controller.close()
      }
    },
    cancel() { stream.controller.abort() },
  })

  return new Response(readable, {
    headers: { 'Content-Type': 'text/event-stream', 'Cache-Control': 'no-cache, no-transform', 'X-Accel-Buffering': 'no' },
  })
}
