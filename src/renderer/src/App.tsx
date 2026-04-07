import React, { useState, useEffect, useRef, useCallback } from 'react'
import type { Session } from '../../preload/index.d'
import { AudioCapture } from './lib/audio-capture'
import { SpeechTranscriber } from './lib/speech'
import { TranscriptPanel, TranscriptEntry } from './components/TranscriptPanel'
import { AuthScreen } from './components/AuthScreen'

const EXPANDED_HEIGHT = 680
const COLLAPSED_HEIGHT = 40

// VAD settings
const SILENCE_RMS_THRESHOLD = 0.01   // below this = silence
const SILENCE_FLUSH_MS      = 1200   // flush after 1.2s of silence
const MIN_SPEECH_MS         = 1000   // don't flush if < 1s of speech
const MAX_CHUNK_MS          = 12000  // force-flush after 12s regardless

function looksLikeQuestion(text: string): boolean {
  const t = text.trim()
  if (t.split(' ').length < 4) return false
  if (t.includes('?')) return true
  return /^(what|how|why|when|where|who|which|can you|could you|would you|tell me|explain|describe|walk me through|talk about|give me an example|have you|do you|did you|are you|were you|what's your|what are your)/i.test(t)
}

function uid() { return Math.random().toString(36).slice(2) }

// ── Auth shell ────────────────────────────────────────────────────────────────
function AuthShell({ onLogin }: { onLogin: (s: Session) => void }) {
  return (
    <div className="flex flex-col select-none overflow-hidden rounded-xl border border-white/15"
      style={{ background: 'rgba(15,15,15,0.95)', backdropFilter: 'blur(16px)', height: EXPANDED_HEIGHT }}>
      <div className="flex items-center justify-between px-3 border-b border-white/10 flex-shrink-0"
        style={{ height: COLLAPSED_HEIGHT, WebkitAppRegion: 'drag' } as React.CSSProperties}>
        <div className="flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-gray-700" />
          <span className="text-xs font-semibold text-gray-300 tracking-wide">Meeting AI</span>
        </div>
        <div style={{ WebkitAppRegion: 'no-drag' } as React.CSSProperties}>
          <button onClick={() => window.api.closeWindow()}
            className="w-6 h-6 rounded flex items-center justify-center text-gray-600 hover:text-red-400 hover:bg-white/10 transition-colors">
            <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
              <line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" />
            </svg>
          </button>
        </div>
      </div>
      <AuthScreen onLogin={onLogin} />
    </div>
  )
}

// ── Main app ──────────────────────────────────────────────────────────────────
export default function App(): JSX.Element {
  const [session, setSession] = useState<Session | null | 'loading'>('loading')
  useEffect(() => {
    window.api.checkSession().then(setSession)
    const t = setInterval(() => window.api.checkSession().then(setSession), 5 * 60 * 1000)
    return () => clearInterval(t)
  }, [])

  const [isRecording, setIsRecording]   = useState(false)
  const [isCollapsed, setIsCollapsed]   = useState(false)
  const [status, setStatus]             = useState('Ready')
  const [isStreaming, setIsStreaming]   = useState(false)
  const [interimText, setInterimText]   = useState('')

  // Inline Q&A feed — single source of truth for display
  const [entries, setEntries] = useState<TranscriptEntry[]>([])
  // Full transcript string for AI context
  const transcriptRef        = useRef('')
  // Currently streaming QA entry ID
  const streamingEntryRef    = useRef<string | null>(null)
  const streamingTextRef     = useRef('')
  // Dedup: avoid re-answering same question
  const lastQuestionRef      = useRef('')

  const captureRef = useRef<AudioCapture | null>(null)
  const speechRef  = useRef<SpeechTranscriber | null>(null)

  // Global shortcut: Cmd+Shift+Enter → read screen and answer
  useEffect(() => {
    // From global shortcut (main process)
    const unsubGlobal = window.api.onTriggerScreenRead(() => triggerScreenRead())
    // From keyboard while app is focused
    const onKey = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.shiftKey && e.key === 'Enter') {
        e.preventDefault()
        triggerScreenRead()
      }
    }
    window.addEventListener('keydown', onKey)
    return () => { unsubGlobal(); window.removeEventListener('keydown', onKey) }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isStreaming, entries])

  const triggerScreenRead = useCallback(() => {
    if (isStreaming) return
    const id = uid()
    streamingEntryRef.current = id
    streamingTextRef.current  = ''
    setIsStreaming(true)
    setEntries((prev) => [...prev, {
      id, type: 'qa',
      question: '📸 Reading screen…',
      answer: '', streaming: true,
    }])
    window.api.readScreen(transcriptRef.current).catch((err: unknown) => {
      setIsStreaming(false)
      setEntries((prev) => prev.map((e) =>
        e.id === id && e.type === 'qa'
          ? { ...e, answer: `Error: ${err instanceof Error ? err.message : String(err)}`, streaming: false }
          : e
      ))
    })
  }, [isStreaming])

  // Receive streaming answer chunks
  useEffect(() => {
    return window.api.onChatChunk(({ text, done }) => {
      const id = streamingEntryRef.current
      if (!id) return
      if (done) {
        setIsStreaming(false)
        const finalAnswer = streamingTextRef.current
        setEntries((prev) => prev.map((e) =>
          e.id === id && e.type === 'qa' ? { ...e, answer: finalAnswer, streaming: false } : e
        ))
        streamingTextRef.current = ''
        streamingEntryRef.current = null
      } else {
        streamingTextRef.current += text
        const snap = streamingTextRef.current
        setEntries((prev) => prev.map((e) =>
          e.id === id && e.type === 'qa' ? { ...e, answer: snap, streaming: true } : e
        ))
      }
    })
  }, [])

  const toggleCollapse = useCallback(() => {
    setIsCollapsed((prev) => {
      const next = !prev
      window.api.setWindowHeight(next ? COLLAPSED_HEIGHT : EXPANDED_HEIGHT)
      return next
    })
  }, [])

  // Send a question (auto or manual) to AI and add inline QA entry
  const sendQuestion = useCallback((question: string) => {
    if (isStreaming) return
    if (question === lastQuestionRef.current) return
    lastQuestionRef.current = question

    const id = uid()
    streamingEntryRef.current = id
    streamingTextRef.current  = ''
    setIsStreaming(true)

    // Add QA entry immediately
    setEntries((prev) => [...prev, { id, type: 'qa', question, answer: '', streaming: true }])

    // Collect current messages from entries for context
    const messages = entries
      .filter((e): e is Extract<TranscriptEntry, { type: 'qa' }> => e.type === 'qa' && !!e.answer)
      .flatMap((e) => [
        { role: 'user', content: e.question },
        { role: 'assistant', content: e.answer },
      ])
    messages.push({ role: 'user', content: question })

    window.api.chatWithClaude(messages, transcriptRef.current).catch((err: unknown) => {
      setIsStreaming(false)
      setEntries((prev) => prev.map((e) =>
        e.id === id && e.type === 'qa'
          ? { ...e, answer: `Error: ${err instanceof Error ? err.message : String(err)}`, streaming: false }
          : e
      ))
    })
  }, [isStreaming, entries])

  // Append transcribed speech to feed + transcript string
  const appendSpeech = useCallback((text: string) => {
    if (!text) return
    transcriptRef.current = transcriptRef.current
      ? `${transcriptRef.current} ${text}`
      : text

    setEntries((prev) => {
      const last = prev[prev.length - 1]
      // Merge into previous speech bubble if recent
      if (last?.type === 'speech') {
        return [...prev.slice(0, -1), { ...last, text: `${last.text} ${text}` }]
      }
      return [...prev, { id: uid(), type: 'speech', text }]
    })

    if (looksLikeQuestion(text)) sendQuestion(text)
  }, [sendQuestion])

  const startRecording = async () => {
    setStatus('Initializing…')
    try {
      const micStream = await navigator.mediaDevices.getUserMedia({ audio: true, video: false })

      // ── Voice Activity Detection ──────────────────────────────────────────
      const audioCtx  = new AudioContext()
      const source    = audioCtx.createMediaStreamSource(micStream)
      const analyser  = audioCtx.createAnalyser()
      analyser.fftSize = 1024
      source.connect(analyser)
      const vadBuf = new Float32Array(analyser.fftSize)

      const mimeType = MediaRecorder.isTypeSupported('audio/webm;codecs=opus')
        ? 'audio/webm;codecs=opus' : 'audio/webm'
      const recorder = new MediaRecorder(micStream, { mimeType })
      let chunks: Blob[]  = []
      let active          = true
      let silenceMs       = 0
      let speechMs        = 0
      let chunkStartTime  = Date.now()

      recorder.ondataavailable = (e) => { if (e.data.size > 0) chunks.push(e.data) }

      recorder.onstop = () => {
        // Restart immediately for continuous capture
        if (active) { recorder.start(); chunkStartTime = Date.now() }

        if (chunks.length === 0) return
        const blob = new Blob(chunks, { type: mimeType })
        chunks = []
        blob.arrayBuffer()
          .then((ab) => window.api.transcribeAudio(ab))
          .then((text) => { if (text) { setInterimText(''); appendSpeech(text) } })
          .catch(() => {})
      }

      recorder.start()
      chunkStartTime = Date.now()

      // VAD loop — check audio level every 100 ms
      const vadTimer = setInterval(() => {
        if (!active) return
        analyser.getFloatTimeDomainData(vadBuf)
        const rms = Math.sqrt(vadBuf.reduce((s, v) => s + v * v, 0) / vadBuf.length)
        const elapsed = Date.now() - chunkStartTime

        if (rms > SILENCE_RMS_THRESHOLD) {
          speechMs  += 100
          silenceMs  = 0
        } else {
          silenceMs += 100
          // Flush on natural pause (silence after speech, or max duration hit)
          const shouldFlush =
            (silenceMs >= SILENCE_FLUSH_MS && speechMs >= MIN_SPEECH_MS) ||
            elapsed >= MAX_CHUNK_MS
          if (shouldFlush && recorder.state === 'recording') {
            silenceMs = 0; speechMs = 0
            recorder.stop()
          }
        }
      }, 100)

      captureRef.current = {
        stop: () => {
          active = false
          clearInterval(vadTimer)
          if (recorder.state !== 'inactive') recorder.stop()
          audioCtx.close()
          micStream.getTracks().forEach((t) => t.stop())
        },
      } as unknown as AudioCapture

      // Web Speech API for interim text (visual bonus)
      const speech = new SpeechTranscriber(
        () => setInterimText(''),
        (interim) => setInterimText(interim),
        () => {}
      )
      if (speech.isSupported()) { speech.start(); speechRef.current = speech }

      setIsRecording(true)
      setStatus('Listening')
    } catch (e: unknown) {
      setStatus(`Mic error: ${e instanceof Error ? e.message : String(e)}`)
    }
  }

  const stopRecording = () => {
    speechRef.current?.stop(); speechRef.current = null
    captureRef.current?.stop(); captureRef.current = null
    setInterimText('')
    setIsRecording(false)
    setStatus('Stopped')
  }

  const handleLogout = async () => {
    stopRecording()
    await window.api.logout()
    setSession(null)
  }

  // ── Loading ─────────────────────────────────────────────────────────────────
  if (session === 'loading') {
    return (
      <div className="flex items-center justify-center rounded-xl border border-white/10"
        style={{ background: 'rgba(15,15,15,0.9)', height: COLLAPSED_HEIGHT }}>
        <span className="w-4 h-4 border-2 border-white/20 border-t-white rounded-full animate-spin" />
      </div>
    )
  }

  if (!session) return <AuthShell onLogin={setSession} />

  // ── Main app ────────────────────────────────────────────────────────────────
  return (
    <div className="flex flex-col select-none overflow-hidden rounded-xl border border-white/15"
      style={{ background: 'rgba(18,18,18,0.82)', backdropFilter: 'blur(14px)', height: isCollapsed ? COLLAPSED_HEIGHT : EXPANDED_HEIGHT }}>

      {/* Header */}
      <div className="flex items-center justify-between px-3 border-b border-white/10 flex-shrink-0"
        style={{ height: COLLAPSED_HEIGHT, background: 'rgba(8,8,8,0.6)', WebkitAppRegion: 'drag' } as React.CSSProperties}>
        <div className="flex items-center gap-2 min-w-0">
          <span className={`w-2 h-2 rounded-full flex-shrink-0 ${isRecording ? 'bg-red-500 animate-pulse' : 'bg-gray-600'}`} />
          <span className="text-xs font-semibold text-gray-200 tracking-wide">Meeting AI</span>
          {!isCollapsed && <span className="text-xs text-gray-500 truncate">{status}</span>}
          {!isCollapsed && isStreaming && <span className="text-[10px] text-emerald-400 animate-pulse">answering…</span>}
        </div>

        <div className="flex items-center gap-1 flex-shrink-0" style={{ WebkitAppRegion: 'no-drag' } as React.CSSProperties}>
          <button onClick={toggleCollapse} title={isCollapsed ? 'Expand' : 'Collapse'}
            className="w-6 h-6 rounded flex items-center justify-center text-gray-500 hover:text-gray-200 hover:bg-white/10 transition-colors">
            <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"
              style={{ transform: isCollapsed ? 'rotate(180deg)' : 'none', transition: 'transform 0.2s' }}>
              <polyline points="18 15 12 9 6 15" />
            </svg>
          </button>
          <button onClick={handleLogout} title={`${session.email} — click to sign out`}
            className="w-6 h-6 rounded-full flex items-center justify-center text-[10px] font-semibold bg-blue-600/40 text-blue-300 hover:bg-red-600/40 hover:text-red-300 transition-colors overflow-hidden">
            {session.avatarUrl
              ? <img src={session.avatarUrl} alt="" className="w-full h-full object-cover rounded-full" />
              : (session.name ?? session.email)[0].toUpperCase()}
          </button>
          <button onClick={() => window.api.hideWindow()}
            className="w-6 h-6 rounded flex items-center justify-center text-gray-500 hover:text-gray-200 hover:bg-white/10 transition-colors">
            <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
              <line x1="5" y1="12" x2="19" y2="12" />
            </svg>
          </button>
          <button onClick={() => window.api.closeWindow()}
            className="w-6 h-6 rounded flex items-center justify-center text-gray-500 hover:text-red-400 hover:bg-white/10 transition-colors">
            <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
              <line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" />
            </svg>
          </button>
        </div>
      </div>

      {!isCollapsed && (
        <>
          {/* Single inline feed — transcript + answers together */}
          <TranscriptPanel
            entries={entries}
            interimText={interimText}
            isRecording={isRecording}
            isStreaming={isStreaming}
            onManualSend={sendQuestion}
          />

          {/* Controls */}
          <div className="flex items-center gap-2 px-3 py-2 border-t border-white/10 rounded-b-xl flex-shrink-0"
            style={{ height: 44, background: 'rgba(8,8,8,0.6)' }}>
            {!isRecording ? (
              <button onClick={startRecording}
                className="flex-1 py-1.5 rounded-lg bg-red-600/90 hover:bg-red-500 text-xs font-semibold flex items-center justify-center gap-1.5 transition-colors">
                <span className="w-2 h-2 rounded-full bg-white" />
                Start Listening
              </button>
            ) : (
              <button onClick={stopRecording}
                className="flex-1 py-1.5 rounded-lg bg-white/10 hover:bg-white/20 text-xs font-semibold flex items-center justify-center gap-1.5 transition-colors">
                <span className="w-2 h-2 rounded-sm bg-gray-300" />
                Stop
              </button>
            )}
            {entries.length > 0 && (
              <button onClick={() => { setEntries([]); transcriptRef.current = ''; lastQuestionRef.current = '' }}
                className="px-2 py-1.5 rounded-lg bg-white/5 hover:bg-white/10 text-xs text-gray-500 hover:text-gray-300 transition-colors">
                Clear
              </button>
            )}
          </div>
        </>
      )}
    </div>
  )
}
