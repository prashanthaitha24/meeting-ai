import React, { useState, useEffect, useRef, useCallback } from 'react'
import type { Session } from '../../preload/index.d'
import { SpeechTranscriber } from './lib/speech'
import { TranscriptPanel, TranscriptEntry } from './components/TranscriptPanel'
import { AuthScreen } from './components/AuthScreen'

const EXPANDED_WIDTH   = 440
const EXPANDED_HEIGHT  = 760
const COLLAPSED_WIDTH  = 210
const COLLAPSED_HEIGHT = 30

// VAD settings
const SILENCE_RMS_THRESHOLD = 0.01
const SILENCE_FLUSH_MS      = 1200
const MIN_SPEECH_MS         = 1000
const MAX_CHUNK_MS          = 12000

type Tab = 'assist' | 'say' | 'followup' | 'recap'
type Mode = 'listening' | 'ask'
type StreamTarget =
  | { kind: 'entry'; id: string }
  | { kind: 'tab'; tab: Exclude<Tab, 'assist'> }

function looksLikeQuestion(text: string): boolean {
  // Strip common filler words Whisper prepends (So, And, Well, Now, Okay…)
  const t = text.trim().replace(/^(so|and|but|well|now|okay|ok|right|alright|um+|uh+|like)[,.]?\s+/i, '').trim()
  if (t.split(' ').length < 4) return false
  if (t.includes('?')) return true
  return /^(what|how|why|when|where|who|which|can you|could you|would you|tell me|explain|describe|walk me|talk about|give me|have you|do you|did you|are you|were you|what's|what are)/i.test(t)
}

function uid() { return Math.random().toString(36).slice(2) }

// ── Auth shell ────────────────────────────────────────────────────────────────
function AuthShell({ onLogin }: { onLogin: (s: Session) => void }) {
  return (
    <div className="flex flex-col select-none overflow-hidden rounded-2xl border border-white/15"
      style={{ background: 'rgba(15,15,15,0.95)', backdropFilter: 'blur(16px)', height: EXPANDED_HEIGHT, width: EXPANDED_WIDTH }}>
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

// ── Tab bar ───────────────────────────────────────────────────────────────────
const TABS: { id: Tab; label: string }[] = [
  { id: 'assist',   label: 'Assist' },
  { id: 'say',      label: 'Say This' },
  { id: 'followup', label: 'Follow-up' },
  { id: 'recap',    label: 'Recap' },
]

// ── Generated content panel ────────────────────────────────────────────────────
function GeneratedPanel({
  content, streaming, placeholder, onGenerate, disabled,
}: {
  content: string
  streaming: boolean
  placeholder: string
  onGenerate: () => void
  disabled: boolean
}): JSX.Element {
  const bottomRef = useRef<HTMLDivElement>(null)
  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: 'smooth' }) }, [content])

  return (
    <div className="flex flex-col flex-1 min-h-0 overflow-hidden">
      <div className="flex-1 overflow-y-auto min-h-0 p-3">
        {!content && !streaming ? (
          <div className="flex flex-col items-center justify-center h-full gap-3 text-center">
            <p className="text-gray-500 text-xs">{placeholder}</p>
            <button
              onClick={onGenerate}
              disabled={disabled}
              className="px-4 py-2 rounded-lg bg-blue-600/80 hover:bg-blue-500 disabled:opacity-40 text-xs font-semibold text-white transition-colors">
              Generate
            </button>
          </div>
        ) : (
          <div className="space-y-2">
            <p className="text-gray-100 text-xs leading-relaxed whitespace-pre-wrap">
              {content}
              {streaming && (
                <span className="inline-block w-1.5 h-3 bg-emerald-400 ml-0.5 align-middle animate-pulse rounded-sm" />
              )}
            </p>
            <div ref={bottomRef} />
          </div>
        )}
      </div>
      {content && !streaming && (
        <div className="flex justify-end px-3 pb-2 gap-2 flex-shrink-0">
          <button
            onClick={onGenerate}
            disabled={disabled}
            className="px-3 py-1 rounded-lg bg-white/8 hover:bg-white/15 disabled:opacity-40 text-[11px] text-gray-400 hover:text-gray-200 transition-colors">
            Regenerate
          </button>
        </div>
      )}
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

  const [isRecording, setIsRecording] = useState(false)
  const [isCollapsed, setIsCollapsed] = useState(false)
  const [status, setStatus]           = useState('Ready')
  const [isStreaming, setIsStreaming] = useState(false)
  const [interimText, setInterimText] = useState('')
  const [activeTab, setActiveTab]     = useState<Tab>('assist')
  const [activeMode, setActiveMode]   = useState<Mode>('listening')

  // Inline Q&A feed
  const [entries, setEntries] = useState<TranscriptEntry[]>([])

  // Generated tab content
  const [tabContent, setTabContent] = useState<Record<Exclude<Tab, 'assist'>, string>>({
    say: '', followup: '', recap: '',
  })
  const [tabStreaming, setTabStreaming] = useState<Record<Exclude<Tab, 'assist'>, boolean>>({
    say: false, followup: false, recap: false,
  })

  // Refs
  const transcriptRef     = useRef('')
  const streamTargetRef   = useRef<StreamTarget | null>(null)
  const streamingTextRef  = useRef('')
  const lastQuestionRef   = useRef('')
  const captureRef        = useRef<{ stop: () => void } | null>(null)
  const speechRef         = useRef<SpeechTranscriber | null>(null)

  // ── Stable refs so recorder closures always see latest values ────────────
  // (recorder.onstop is set up once; without refs it captures stale state)
  const isStreamingRef  = useRef(false)
  const entriesRef      = useRef<TranscriptEntry[]>([])
  isStreamingRef.current = isStreaming
  entriesRef.current     = entries

  // ── Screen read ─────────────────────────────────────────────────────────────
  const triggerScreenRead = useCallback(() => {
    if (isStreaming) return
    const id = uid()
    streamTargetRef.current = { kind: 'entry', id }
    streamingTextRef.current = ''
    setIsStreaming(true)
    setActiveTab('assist')
    setEntries((prev) => [...prev, { id, type: 'qa', question: 'Reading screen…', answer: '', streaming: true }])
    window.api.readScreen(transcriptRef.current).catch((err: unknown) => {
      setIsStreaming(false)
      setEntries((prev) => prev.map((e) =>
        e.id === id && e.type === 'qa'
          ? { ...e, answer: `Error: ${err instanceof Error ? err.message : String(err)}`, streaming: false }
          : e
      ))
    })
  }, [isStreaming])

  // Global shortcuts
  useEffect(() => {
    const unsubGlobal = window.api.onTriggerScreenRead(() => triggerScreenRead())
    const onKey = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && !e.shiftKey && e.key === 'Enter') {
        e.preventDefault(); triggerScreenRead()
      }
    }
    window.addEventListener('keydown', onKey)
    return () => { unsubGlobal(); window.removeEventListener('keydown', onKey) }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isStreaming, entries])

  // ── Chunk handler ────────────────────────────────────────────────────────────
  useEffect(() => {
    return window.api.onChatChunk(({ text, done }) => {
      const target = streamTargetRef.current
      if (!target) return

      if (done) {
        const finalText = streamingTextRef.current
        setIsStreaming(false)
        if (target.kind === 'entry') {
          const id = target.id
          setEntries((prev) => prev.map((e) =>
            e.id === id && e.type === 'qa' ? { ...e, answer: finalText, streaming: false } : e
          ))
          // Clear Say This so it auto-refreshes for the next question
          setTabContent((prev) => ({ ...prev, say: '' }))
        } else {
          const t = target.tab
          setTabContent((prev) => ({ ...prev, [t]: finalText }))
          setTabStreaming((prev) => ({ ...prev, [t]: false }))
        }
        streamingTextRef.current = ''
        streamTargetRef.current = null
      } else {
        streamingTextRef.current += text
        const snap = streamingTextRef.current
        if (target.kind === 'entry') {
          const id = target.id
          setEntries((prev) => prev.map((e) =>
            e.id === id && e.type === 'qa' ? { ...e, answer: snap, streaming: true } : e
          ))
        } else {
          const t = target.tab
          setTabContent((prev) => ({ ...prev, [t]: snap }))
        }
      }
    })
  }, [])

  const toggleCollapse = useCallback(() => {
    setIsCollapsed((prev) => {
      const next = !prev
      if (next) {
        window.api.setWindowSize(COLLAPSED_WIDTH, COLLAPSED_HEIGHT)
      } else {
        window.api.setWindowSize(EXPANDED_WIDTH, EXPANDED_HEIGHT)
      }
      return next
    })
  }, [])

  // Focus the follow-up input (used when switching to Ask Mode)
  const focusInput = () => {
    setTimeout(() => {
      document.querySelector<HTMLInputElement>('input[placeholder="Ask a follow-up…"]')?.focus()
    }, 100)
  }

  const switchToAskMode = useCallback(() => {
    if (isRecording) {
      speechRef.current?.stop(); speechRef.current = null
      captureRef.current?.stop(); captureRef.current = null
      setInterimText('')
      setIsRecording(false)
      setStatus('Stopped')
    }
    setActiveMode('ask')
    setActiveTab('assist')
    focusInput()
  }, [isRecording])

  // ── Send question to Assist tab ─────────────────────────────────────────────
  // Uses refs for isStreaming/entries so recorder closures are never stale.
  // skipDedup=true for manual typed questions; false for auto speech detection.
  const sendQuestion = useCallback((question: string, skipDedup = false) => {
    if (isStreamingRef.current) return
    if (!skipDedup && question === lastQuestionRef.current) return
    lastQuestionRef.current = question

    const id = uid()
    streamTargetRef.current = { kind: 'entry', id }
    streamingTextRef.current = ''
    setIsStreaming(true)
    setActiveTab('assist') // always show the answer when auto-detected
    setEntries((prev) => [...prev, { id, type: 'qa', question, answer: '', streaming: true }])

    // Use entriesRef so we always have the latest conversation history
    const messages = entriesRef.current
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
  }, []) // stable — all live values come from refs

  // ── Generate tab content ────────────────────────────────────────────────────
  const generateTabContent = useCallback((tab: Exclude<Tab, 'assist'>) => {
    if (isStreaming) return
    const transcript = transcriptRef.current
    if (!transcript.trim()) return

    const prompts: Record<Exclude<Tab, 'assist'>, string> = {
      say: 'Review the transcript and give 3-5 short, confident statements the candidate can say out loud right now. Number each one. Be direct — no fluff.',
      followup: 'Review the transcript and write 5 smart questions the candidate or interviewer should raise next. Number each one. Be specific to what was discussed.',
      recap: 'Write a structured summary of the conversation so far. Include: (1) Key topics covered, (2) Important points made, (3) Decisions or outcomes, (4) What to expect next. Keep each section to 2-3 bullet points.',
    }

    streamTargetRef.current = { kind: 'tab', tab }
    streamingTextRef.current = ''
    setIsStreaming(true)
    setTabContent((prev) => ({ ...prev, [tab]: '' }))
    setTabStreaming((prev) => ({ ...prev, [tab]: true }))
    setActiveTab(tab)

    window.api.chatWithClaude(
      [{ role: 'user', content: prompts[tab] }],
      transcript
    ).catch((err: unknown) => {
      setIsStreaming(false)
      setTabStreaming((prev) => ({ ...prev, [tab]: false }))
      setTabContent((prev) => ({
        ...prev,
        [tab]: `Error: ${err instanceof Error ? err.message : String(err)}`
      }))
      streamTargetRef.current = null
    })
  }, [isStreaming])

  // ── Append transcribed speech ───────────────────────────────────────────────
  const appendSpeech = useCallback((text: string) => {
    if (!text) return
    transcriptRef.current = transcriptRef.current ? `${transcriptRef.current} ${text}` : text
    setEntries((prev) => {
      const last = prev[prev.length - 1]
      if (last?.type === 'speech') {
        return [...prev.slice(0, -1), { ...last, text: `${last.text} ${text}` }]
      }
      return [...prev, { id: uid(), type: 'speech', text }]
    })
    if (looksLikeQuestion(text)) sendQuestion(text)
  }, [sendQuestion])

  // Stable ref so the recorder closure always calls the latest appendSpeech
  const appendSpeechRef = useRef(appendSpeech)
  appendSpeechRef.current = appendSpeech

  // ── Recording ───────────────────────────────────────────────────────────────
  const startRecording = async () => {
    setStatus('Initializing…')
    try {
      const micStream = await navigator.mediaDevices.getUserMedia({ audio: true, video: false })
      const audioCtx  = new AudioContext()
      const source    = audioCtx.createMediaStreamSource(micStream)
      const analyser  = audioCtx.createAnalyser()
      analyser.fftSize = 1024
      source.connect(analyser)
      const vadBuf = new Float32Array(analyser.fftSize)

      const mimeType = MediaRecorder.isTypeSupported('audio/webm;codecs=opus')
        ? 'audio/webm;codecs=opus' : 'audio/webm'
      const recorder = new MediaRecorder(micStream, { mimeType })
      let chunks: Blob[] = []
      let active         = true
      let silenceMs      = 0
      let speechMs       = 0
      let chunkStartTime = Date.now()

      recorder.ondataavailable = (e) => { if (e.data.size > 0) chunks.push(e.data) }

      recorder.onstop = () => {
        if (active) { recorder.start(); chunkStartTime = Date.now() }
        if (chunks.length === 0) return
        const blob = new Blob(chunks, { type: mimeType })
        chunks = []
        blob.arrayBuffer()
          .then((ab) => window.api.transcribeAudio(ab))
          .then((text) => { if (text) { setInterimText(''); appendSpeechRef.current(text) } })
          .catch(() => {})
      }

      recorder.start()
      chunkStartTime = Date.now()

      const vadTimer = setInterval(() => {
        if (!active) return
        analyser.getFloatTimeDomainData(vadBuf)
        const rms = Math.sqrt(vadBuf.reduce((s, v) => s + v * v, 0) / vadBuf.length)
        const elapsed = Date.now() - chunkStartTime

        if (rms > SILENCE_RMS_THRESHOLD) {
          speechMs += 100; silenceMs = 0
        } else {
          silenceMs += 100
          const shouldFlush =
            (silenceMs >= SILENCE_FLUSH_MS && speechMs >= MIN_SPEECH_MS) ||
            elapsed >= MAX_CHUNK_MS
          if (shouldFlush && recorder.state === 'recording') {
            silenceMs = 0; speechMs = 0; recorder.stop()
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
      }

      const speech = new SpeechTranscriber(
        () => setInterimText(''),
        (interim) => setInterimText(interim),
        () => {}
      )
      if (speech.isSupported()) { speech.start(); speechRef.current = speech }

      setIsRecording(true)
      setStatus('Listening')
      setActiveMode('listening')
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
    setActiveMode('ask')
    setActiveTab('assist')
    focusInput()
  }

  // ── Export helpers ──────────────────────────────────────────────────────────
  const buildExportText = (): string => {
    const lines: string[] = [
      `Meeting Notes — ${new Date().toLocaleString()}`,
      '='.repeat(50),
      '',
    ]
    if (transcriptRef.current) {
      lines.push('TRANSCRIPT', '-'.repeat(30), transcriptRef.current, '')
    }
    entries.filter((e) => e.type === 'qa').forEach((e) => {
      if (e.type === 'qa') {
        lines.push(`Q: ${e.question}`, `A: ${e.answer}`, '')
      }
    })
    if (tabContent.recap) {
      lines.push('RECAP', '-'.repeat(30), tabContent.recap, '')
    }
    if (tabContent.say) {
      lines.push('TALKING POINTS', '-'.repeat(30), tabContent.say, '')
    }
    if (tabContent.followup) {
      lines.push('FOLLOW-UP QUESTIONS', '-'.repeat(30), tabContent.followup, '')
    }
    return lines.join('\n')
  }

  const handleExportNotes = async () => {
    const content = buildExportText()
    await window.api.saveNotes(content)
  }

  const handleEmail = () => {
    const content = buildExportText()
    const subject = encodeURIComponent('Meeting Notes')
    const body = encodeURIComponent(content.slice(0, 1800))
    window.api.openExternal(`mailto:?subject=${subject}&body=${body}`)
  }

  const handleLogout = async () => {
    stopRecording()
    await window.api.logout()
    setSession(null)
  }

  // ── Loading ─────────────────────────────────────────────────────────────────
  if (session === 'loading') {
    return (
      <div className="flex items-center justify-center border border-white/10"
        style={{ background: 'rgba(15,15,15,0.9)', height: COLLAPSED_HEIGHT, width: COLLAPSED_WIDTH, borderRadius: 999 }}>
        <span className="w-3 h-3 border-2 border-white/20 border-t-white rounded-full animate-spin" />
      </div>
    )
  }

  if (!session) return <AuthShell onLogin={setSession} />

  // ── Main app ────────────────────────────────────────────────────────────────
  return (
    <div
      className="flex flex-col overflow-hidden border border-white/15"
      style={{
        background: isCollapsed ? 'rgba(14,14,14,0.92)' : 'rgba(18,18,18,0.82)',
        backdropFilter: 'blur(20px)',
        borderRadius: isCollapsed ? 999 : 14,
        height: isCollapsed ? COLLAPSED_HEIGHT : EXPANDED_HEIGHT,
        width: isCollapsed ? COLLAPSED_WIDTH : EXPANDED_WIDTH,
        transition: 'border-radius 0.25s ease',
        boxShadow: isCollapsed
          ? '0 4px 24px rgba(0,0,0,0.5)'
          : '0 8px 32px rgba(0,0,0,0.4)',
      }}>

      {/* ── Header / collapsed pill ── */}
      {isCollapsed ? (
        /* Pill view — minimal, clean */
        <div
          className="flex items-center justify-between flex-1 px-3"
          style={{ WebkitAppRegion: 'drag' } as React.CSSProperties}>
          <div className="flex items-center gap-2 min-w-0">
            <span className={`w-1.5 h-1.5 rounded-full flex-shrink-0 ${isRecording ? 'bg-red-500 animate-pulse' : 'bg-gray-600'}`} />
            <span className="text-[11px] font-semibold text-gray-300 tracking-wide truncate">Meeting AI</span>
            {isStreaming && <span className="text-[9px] text-emerald-400 animate-pulse">●</span>}
          </div>
          <div className="flex items-center gap-1 flex-shrink-0" style={{ WebkitAppRegion: 'no-drag' } as React.CSSProperties}>
            <button
              onClick={toggleCollapse}
              title="Expand"
              className="w-5 h-5 rounded-full flex items-center justify-center text-gray-600 hover:text-gray-300 hover:bg-white/10 transition-colors">
              <svg width="9" height="9" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                <polyline points="6 9 12 15 18 9" />
              </svg>
            </button>
          </div>
        </div>
      ) : (
        /* Full header */
        <div
          className="flex items-center justify-between px-3 border-b border-white/10 flex-shrink-0"
          style={{ height: 40, background: 'rgba(8,8,8,0.5)', WebkitAppRegion: 'drag', borderRadius: '14px 14px 0 0' } as React.CSSProperties}>
          <div className="flex items-center gap-2 min-w-0">
            <span className={`w-2 h-2 rounded-full flex-shrink-0 transition-colors ${isRecording ? 'bg-red-500 animate-pulse' : 'bg-gray-600'}`} />
            <span className="text-xs font-semibold text-gray-200 tracking-wide">Meeting AI</span>
            <span className="text-[10px] text-gray-600 truncate ml-0.5">
              {isStreaming ? '• answering…' : status}
            </span>
          </div>

          <div className="flex items-center gap-1 flex-shrink-0" style={{ WebkitAppRegion: 'no-drag' } as React.CSSProperties}>
            <button onClick={toggleCollapse} title="Collapse to pill"
              className="w-6 h-6 rounded flex items-center justify-center text-gray-500 hover:text-gray-200 hover:bg-white/10 transition-colors">
              <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
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
      )}

      {!isCollapsed && (
        <>
          {/* ── Mode toggle ── */}
          <div className="flex items-center px-3 py-2 gap-2 flex-shrink-0 border-b border-white/8"
            style={{ background: 'rgba(8,8,8,0.4)' }}>
            <div className="flex flex-1 rounded-lg overflow-hidden border border-white/10 p-0.5 gap-0.5"
              style={{ background: 'rgba(255,255,255,0.04)' }}>
              <button
                onClick={() => setActiveMode('listening')}
                className={`flex-1 py-1 rounded-md text-[11px] font-medium transition-all flex items-center justify-center gap-1.5 ${
                  activeMode === 'listening'
                    ? 'bg-red-600/90 text-white shadow-sm'
                    : 'text-gray-500 hover:text-gray-300'
                }`}>
                <span className={`w-1.5 h-1.5 rounded-full ${activeMode === 'listening' && isRecording ? 'bg-white animate-pulse' : 'bg-current opacity-60'}`} />
                Listening
              </button>
              <button
                onClick={switchToAskMode}
                className={`flex-1 py-1 rounded-md text-[11px] font-medium transition-all flex items-center justify-center gap-1.5 ${
                  activeMode === 'ask'
                    ? 'bg-blue-600/90 text-white shadow-sm'
                    : 'text-gray-500 hover:text-gray-300'
                }`}>
                <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                  <circle cx="12" cy="12" r="10" /><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3" /><line x1="12" y1="17" x2="12.01" y2="17" />
                </svg>
                Ask Mode
              </button>
            </div>
            <div className="text-[10px] text-gray-700">⌘↵ screen</div>
          </div>

          {/* ── Tab bar ── */}
          <div className="flex flex-shrink-0 border-b border-white/8"
            style={{ background: 'rgba(8,8,8,0.3)' }}>
            {TABS.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex-1 py-2 text-[11px] font-medium transition-colors relative ${
                  activeTab === tab.id
                    ? 'text-blue-400'
                    : 'text-gray-600 hover:text-gray-400'
                }`}>
                {tab.label}
                {activeTab === tab.id && (
                  <span className="absolute bottom-0 left-2 right-2 h-0.5 bg-blue-500 rounded-full" />
                )}
                {tab.id !== 'assist' && tabStreaming[tab.id] && (
                  <span className="absolute top-1.5 right-1.5 w-1 h-1 rounded-full bg-emerald-400 animate-pulse" />
                )}
              </button>
            ))}
          </div>

          {/* ── Tab content ── */}
          <div className="flex flex-col flex-1 min-h-0 overflow-hidden">
            {activeTab === 'assist' && (
              <TranscriptPanel
                entries={entries}
                interimText={interimText}
                isRecording={isRecording}
                isStreaming={isStreaming}
                onManualSend={(q) => sendQuestion(q, true)}
              />
            )}

            {activeTab === 'say' && (
              <GeneratedPanel
                content={tabContent.say}
                streaming={tabStreaming.say}
                placeholder={transcriptRef.current
                  ? 'Generate talking points based on the current conversation.'
                  : 'Start recording to capture the conversation first.'}
                onGenerate={() => generateTabContent('say')}
                disabled={isStreaming || !transcriptRef.current.trim()}
              />
            )}

            {activeTab === 'followup' && (
              <GeneratedPanel
                content={tabContent.followup}
                streaming={tabStreaming.followup}
                placeholder={transcriptRef.current
                  ? 'Generate follow-up questions based on the conversation.'
                  : 'Start recording to capture the conversation first.'}
                onGenerate={() => generateTabContent('followup')}
                disabled={isStreaming || !transcriptRef.current.trim()}
              />
            )}

            {activeTab === 'recap' && (
              <GeneratedPanel
                content={tabContent.recap}
                streaming={tabStreaming.recap}
                placeholder={transcriptRef.current
                  ? 'Generate a structured recap of the conversation so far.'
                  : 'Start recording to capture the conversation first.'}
                onGenerate={() => generateTabContent('recap')}
                disabled={isStreaming || !transcriptRef.current.trim()}
              />
            )}
          </div>

          {/* ── Action bar ── */}
          <div className="flex items-center gap-2 px-3 py-2 border-t border-white/10 rounded-b-xl flex-shrink-0"
            style={{ background: 'rgba(8,8,8,0.6)' }}>
            {/* Record / Stop */}
            {!isRecording ? (
              <button onClick={startRecording}
                className="flex items-center justify-center gap-1.5 px-3 py-1.5 rounded-lg bg-red-600/90 hover:bg-red-500 text-xs font-semibold transition-colors">
                <span className="w-2 h-2 rounded-full bg-white" />
                Start
              </button>
            ) : (
              <button onClick={stopRecording}
                className="flex items-center justify-center gap-1.5 px-3 py-1.5 rounded-lg bg-white/10 hover:bg-white/20 text-xs font-semibold transition-colors">
                <span className="w-2 h-2 rounded-sm bg-gray-300" />
                Stop
              </button>
            )}

            {/* Spacer */}
            <div className="flex-1" />

            {/* Clear */}
            {(entries.length > 0 || transcriptRef.current) && (
              <button
                onClick={() => {
                  setEntries([])
                  transcriptRef.current = ''
                  lastQuestionRef.current = ''
                  setTabContent({ say: '', followup: '', recap: '' })
                }}
                className="px-2.5 py-1.5 rounded-lg bg-white/5 hover:bg-white/10 text-[11px] text-gray-500 hover:text-gray-300 transition-colors">
                Clear
              </button>
            )}

            {/* Export PDF / Notes */}
            <button
              onClick={handleExportNotes}
              disabled={entries.length === 0 && !transcriptRef.current}
              title="Save notes to file"
              className="w-7 h-7 rounded-lg bg-white/8 hover:bg-white/15 disabled:opacity-30 flex items-center justify-center text-gray-400 hover:text-gray-200 transition-colors">
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                <polyline points="14 2 14 8 20 8" />
                <line x1="16" y1="13" x2="8" y2="13" />
                <line x1="16" y1="17" x2="8" y2="17" />
                <polyline points="10 9 9 9 8 9" />
              </svg>
            </button>

            {/* Email */}
            <button
              onClick={handleEmail}
              disabled={entries.length === 0 && !transcriptRef.current}
              title="Send via email"
              className="w-7 h-7 rounded-lg bg-white/8 hover:bg-white/15 disabled:opacity-30 flex items-center justify-center text-gray-400 hover:text-gray-200 transition-colors">
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z" />
                <polyline points="22,6 12,13 2,6" />
              </svg>
            </button>
          </div>
        </>
      )}
    </div>
  )
}
