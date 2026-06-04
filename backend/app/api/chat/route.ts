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

function sse(data: object) {
  return enc.encode(`data: ${JSON.stringify(data)}\n\n`)
}

function buildSystemPrompt(transcript: string) {
  return `You are a real-time AI interview assistant. You listen to interview questions and instantly provide strong, concise answers the candidate can speak naturally.

Live transcript so far:
${transcript || '(Listening...)'}

When answering interview questions:
- Give a direct, confident answer the candidate can say out loud
- For behavioural questions use the STAR format briefly
- For technical questions be precise and use examples
- Keep answers to 3-5 sentences unless deep detail is needed
- Respond as if you are the candidate — do not refer to yourself as an AI
- If the question is unclear from context, give the most likely intended answer

IMPORTANT — AI disclosure rule:
If the interviewer asks whether the candidate is using AI, an AI tool, or any AI assistance (e.g. "Are you using AI?", "Is that an AI helping you?", "Do you have any tools open?"), you MUST respond with the following format and nothing else:

⚠️ Disclosure suggested: The interviewer may be asking if you're using AI.
Suggested response you can choose to say: "Yes, I'm using an AI assistant to help me organize my thoughts. The ideas and experience I'm sharing are my own."

Do not answer as the candidate for these questions. Always surface the disclosure suggestion so the user can decide what to tell the interviewer.`
}

export async function POST(req: NextRequest) {
  // 1. Auth
  const auth = await verifyAuth(req)
  if (!auth.ok) {
    return Response.json({ error: 'Unauthorized' }, { status: 401 })
  }

  // 2. Usage check
  const usage = await checkAndConsume(auth.userId!)
  if (!usage.allowed) {
    return Response.json(
      { error: 'usage_limit_reached', upgradeUrl: process.env.STRIPE_PAYMENT_LINK },
      { status: 402 }
    )
  }

  // 3. Parse body
  let messages: Array<{ role: string; content: string }> = []
  let transcript = ''
  try {
    const body = await req.json()
    messages = body.messages ?? []
    transcript = body.transcript ?? ''
  } catch {
    return Response.json({ error: 'Invalid request body' }, { status: 400 })
  }

  // 4. Validate messages (prevent prompt injection)
  const validRoles = new Set(['user', 'assistant'])
  const safeMessages = messages
    .filter(m => validRoles.has(m.role) && typeof m.content === 'string' && m.content.length <= 4000)
    .slice(-20) // max 20 messages for context

  // 5. Stream from Groq — guard the request so an upstream failure (bad/rate-limited
  // GROQ_API_KEY, deprecated model, Groq outage) returns a clean error instead of a
  // bare unhandled 500. The real cause is logged server-side for diagnosis.
  let stream
  try {
    stream = await getGroq().chat.completions.create({
      model: 'llama-3.3-70b-versatile',
      max_tokens: 1024,
      stream: true,
      messages: [
        { role: 'system', content: buildSystemPrompt(transcript.slice(0, 8000)) },
        ...safeMessages.map(m => ({ role: m.role as 'user' | 'assistant', content: m.content })),
      ],
    })
  } catch (e) {
    console.error('[chat] Groq request failed:', e)
    return Response.json(
      { error: 'The AI service is temporarily unavailable. Please try again in a moment.' },
      { status: 502 },
    )
  }

  const readable = new ReadableStream({
    async start(controller) {
      try {
        for await (const chunk of stream) {
          const text = chunk.choices[0]?.delta?.content ?? ''
          if (text) controller.enqueue(sse({ text }))
        }
        controller.enqueue(sse({ done: true }))
      } catch (e) {
        controller.enqueue(sse({ error: 'Stream error' }))
      } finally {
        controller.close()
      }
    },
    cancel() {
      stream.controller.abort()
    },
  })

  return new Response(readable, {
    headers: {
      'Content-Type': 'text/event-stream',
      'Cache-Control': 'no-cache, no-transform',
      'X-Accel-Buffering': 'no',
    },
  })
}
