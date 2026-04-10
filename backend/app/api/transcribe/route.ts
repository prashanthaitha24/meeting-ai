import { NextRequest } from 'next/server'
import { verifyAuth } from '@/lib/auth'

export const dynamic = 'force-dynamic'

export async function POST(req: NextRequest) {
  const auth = await verifyAuth(req)
  if (!auth.ok) return Response.json({ error: 'Unauthorized' }, { status: 401 })

  let formData: FormData
  try {
    formData = await req.formData()
  } catch {
    return Response.json({ text: '' })
  }

  const file = formData.get('file')
  if (!file || !(file instanceof Blob)) return Response.json({ text: '' })

  // Size limit: 25MB
  if (file.size > 25 * 1024 * 1024) return Response.json({ text: '' })

  const groqForm = new FormData()
  groqForm.append('file', file, 'audio.webm')
  groqForm.append('model', 'whisper-large-v3-turbo')
  groqForm.append('response_format', 'text')
  groqForm.append('language', 'en')

  try {
    const res = await fetch('https://api.groq.com/openai/v1/audio/transcriptions', {
      method: 'POST',
      headers: { Authorization: `Bearer ${process.env.GROQ_API_KEY}` },
      body: groqForm,
    })
    if (!res.ok) return Response.json({ text: '' })
    const text = (await res.text()).trim()
    return Response.json({ text })
  } catch {
    return Response.json({ text: '' })
  }
}
