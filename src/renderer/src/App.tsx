import React, { useState, useEffect, useRef, useCallback } from 'react'
import type { Session } from '../../preload/index.d'
import { AudioCapture } from './lib/audio-capture'
import { transcribeBlob } from './lib/transcription'
import { SpeechTranscriber } from './lib/speech'
import { TranscriptPanel } from './components/TranscriptPanel'
import { ChatPanel, ChatMessage } from './components/ChatPanel'
import { AuthScreen } from './components/AuthScreen'

type Tab = 'transcript' | 'chat'
const EXPANDED_HEIGHT = 680
const COLLAPSED_HEIGHT = 40

// ── Auth shell (header + auth form) ──────────────────────────────────────────
function AuthShell({ onLogin }: { onLogin: (s: Session) => void }) {
  return (
    <div
      className="flex flex-col select-none overflow-hidden rounded-xl border border-white/15"
      style={{ background: 'rgba(15,15,15,0.95)', backdropFilter: 'blur(16px)', height: EXPANDED_HEIGHT }}
    >
      {/* Drag header */}
      <div
        className="flex items-center justify-between px-3 border-b border-white/10 flex-shrink-0"
        style={{ height: COLLAPSED_HEIGHT, WebkitAppRegion: 'drag' } as React.CSSProperties}
      >
        <div className="flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-gray-700" />
          <span className="text-xs font-semibold text-gray-300 tracking-wide">Meeting AI</span>
        </div>
        <div style={{ WebkitAppRegion: 'no-drag' } as React.CSSProperties}>
          <button
            onClick={() => window.api.closeWindow()}
            className="w-6 h-6 rounded flex items-center justify-center text-gray-600 hover:text-red-400 hover:bg-white/10 transition-colors"
          >
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
  // ── Auth state ──────────────────────────────────────────────────────────────
  const [session, setSession] = useState<Session | null | 'loading'>('loading')

  useEffect(() => {
    window.api.checkSession().then(setSession)
    // Re-check every 5 min to catch expiry
    const interval = setInterval(() => window.api.checkSession().then(setSession), 5 * 60 * 1000)
    return () => clearInterval(interval)
  }, [])

  // ── App state ───────────────────────────────────────────────────────────────
  const [tab, setTab] = useState<Tab>('transcript')
  const [isRecording, setIsRecording] = useState(false)
  const [isCollapsed, setIsCollapsed] = useState(false)
  const [status, setStatus] = useState('Ready')
  const [transcript, setTranscript] = useState('')
  const [interimText, setInterimText] = useState('')
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [streamingContent, setStreamingContent] = useState('')
  const [isStreaming, setIsStreaming] = useState(false)
  const [systemSourceId, setSystemSourceId] = useState<string | null>(null)

  const captureRef = useRef<AudioCapture | null>(null)
  const speechRef = useRef<SpeechTranscriber | null>(null)
  const transcriptRef = useRef('')
  const streamingContentRef = useRef('')

  useEffect(() => { transcriptRef.current = transcript }, [transcript])

  // Get system audio source once
  useEffect(() => {
    window.api.getDesktopSources().then((sources) => {
      if (sources.length > 0) setSystemSourceId(sources[0].id)
    })
  }, [])

  // Stream chat chunks from main process
  useEffect(() => {
    const unsub = window.api.onChatChunk(({ text, done }) => {
      if (done) {
        setIsStreaming(false)
        setMessages((prev) => [...prev, { role: 'assistant', content: streamingContentRef.current }])
        setStreamingContent('')
        streamingContentRef.current = ''
      } else {
        setStreamingContent((prev) => {
          const next = prev + text
          streamingContentRef.current = next
          return next
        })
      }
    })
    return unsub
  }, [])

  const toggleCollapse = useCallback(() => {
    setIsCollapsed((prev) => {
      const next = !prev
      window.api.setWindowHeight(next ? COLLAPSED_HEIGHT : EXPANDED_HEIGHT)
      return next
    })
  }, [])

  // System-audio chunk → Whisper (fallback cloud path, every 30s)
  const handleSystemAudioChunk = useCallback(async (blob: Blob) => {
    const text = await transcribeBlob(blob)
    if (text) {
      setTranscript((prev) => {
        const updated = prev ? `${prev}\n[Others]: ${text}` : `[Others]: ${text}`
        transcriptRef.current = updated
        return updated
      })
    }
  }, [])

  const startRecording = async (): Promise<void> => {
    setStatus('Initializing…')
    try {
      // ── Primary: Web Speech API for mic (local, free) ────────────────────
      const speech = new SpeechTranscriber(
        (finalText) => {
          setInterimText('')
          setTranscript((prev) => {
            const line = prev ? `${prev}\n[You]: ${finalText}` : `[You]: ${finalText}`
            transcriptRef.current = line
            return line
          })
        },
        (interim) => setInterimText(interim),
        (s) => { if (s === 'unsupported') setStatus('Speech API unavailable') }
      )
      speech.start()
      speechRef.current = speech

      // ── Secondary: AudioCapture for system audio → Whisper (cloud fallback) ─
      if (systemSourceId) {
        const capture = new AudioCapture({
          onChunk: handleSystemAudioChunk,
          chunkDuration: 30000, // 30s chunks to minimise Whisper API costs
        })
        await capture.init(systemSourceId)
        capture.startRecording()
        captureRef.current = capture
      }

      setIsRecording(true)
      setStatus('Listening')
    } catch (e: unknown) {
      setStatus(`Error: ${e instanceof Error ? e.message : String(e)}`)
    }
  }

  const stopRecording = (): void => {
    speechRef.current?.stop()
    speechRef.current = null
    captureRef.current?.stop()
    captureRef.current = null
    setInterimText('')
    setIsRecording(false)
    setStatus('Stopped')
  }

  const sendMessage = async (text: string): Promise<void> => {
    const userMsg: ChatMessage = { role: 'user', content: text }
    const updated = [...messages, userMsg]
    setMessages(updated)
    setIsStreaming(true)
    setStreamingContent('')
    streamingContentRef.current = ''
    try {
      await window.api.chatWithClaude(
        updated.map((m) => ({ role: m.role, content: m.content })),
        transcriptRef.current
      )
    } catch (e: unknown) {
      setIsStreaming(false)
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: `Error: ${e instanceof Error ? e.message : String(e)}` },
      ])
    }
  }

  const handleLogout = async () => {
    stopRecording()
    await window.api.logout()
    setSession(null)
  }

  // ── Render: loading ─────────────────────────────────────────────────────────
  if (session === 'loading') {
    return (
      <div
        className="flex items-center justify-center rounded-xl border border-white/10"
        style={{ background: 'rgba(15,15,15,0.9)', height: COLLAPSED_HEIGHT }}
      >
        <span className="w-4 h-4 border-2 border-white/20 border-t-white rounded-full animate-spin" />
      </div>
    )
  }

  // ── Render: auth ────────────────────────────────────────────────────────────
  if (!session) return <AuthShell onLogin={setSession} />

  // ── Render: main app ────────────────────────────────────────────────────────
  return (
    <div
      className="flex flex-col select-none overflow-hidden rounded-xl border border-white/15"
      style={{ background: 'rgba(18,18,18,0.82)', backdropFilter: 'blur(14px)' }}
    >
      {/* Header */}
      <div
        className="flex items-center justify-between px-3 border-b border-white/10 flex-shrink-0"
        style={{
          height: COLLAPSED_HEIGHT,
          background: 'rgba(8,8,8,0.6)',
          WebkitAppRegion: 'drag',
        } as React.CSSProperties}
      >
        <div className="flex items-center gap-2 min-w-0">
          <span
            className={`w-2 h-2 rounded-full flex-shrink-0 ${
              isRecording ? 'bg-red-500 animate-pulse' : 'bg-gray-600'
            }`}
          />
          <span className="text-xs font-semibold text-gray-200 tracking-wide truncate">Meeting AI</span>
          {!isCollapsed && <span className="text-xs text-gray-500 truncate">{status}</span>}
        </div>

        <div
          className="flex items-center gap-1 flex-shrink-0"
          style={{ WebkitAppRegion: 'no-drag' } as React.CSSProperties}
        >
          {/* Collapse */}
          <button
            onClick={toggleCollapse}
            title={isCollapsed ? 'Expand' : 'Collapse'}
            className="w-6 h-6 rounded flex items-center justify-center text-gray-500 hover:text-gray-200 hover:bg-white/10 transition-colors"
          >
            <svg
              width="11" height="11" viewBox="0 0 24 24" fill="none"
              stroke="currentColor" strokeWidth="2.5"
              style={{ transform: isCollapsed ? 'rotate(180deg)' : 'none', transition: 'transform 0.2s' }}
            >
              <polyline points="18 15 12 9 6 15" />
            </svg>
          </button>

          {/* User avatar / logout */}
          <button
            onClick={handleLogout}
            title={`Signed in as ${session.email}\nClick to sign out`}
            className="w-6 h-6 rounded-full flex items-center justify-center text-[10px] font-semibold bg-blue-600/40 text-blue-300 hover:bg-red-600/40 hover:text-red-300 transition-colors overflow-hidden"
          >
            {session.avatarUrl ? (
              <img src={session.avatarUrl} alt="" className="w-full h-full object-cover rounded-full" />
            ) : (
              (session.name ?? session.email)[0].toUpperCase()
            )}
          </button>

          <span className="text-[10px] text-gray-700">⌘⇧Space</span>

          <button
            onClick={() => window.api.hideWindow()}
            className="w-6 h-6 rounded flex items-center justify-center text-gray-500 hover:text-gray-200 hover:bg-white/10 transition-colors"
            title="Hide"
          >
            <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
              <line x1="5" y1="12" x2="19" y2="12" />
            </svg>
          </button>
          <button
            onClick={() => window.api.closeWindow()}
            className="w-6 h-6 rounded flex items-center justify-center text-gray-500 hover:text-red-400 hover:bg-white/10 transition-colors"
            title="Close"
          >
            <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
              <line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" />
            </svg>
          </button>
        </div>
      </div>

      {/* Expanded content */}
      {!isCollapsed && (
        <>
          {/* Tabs */}
          <div className="flex border-b border-white/10 flex-shrink-0" style={{ background: 'rgba(10,10,10,0.5)' }}>
            {(['transcript', 'chat'] as Tab[]).map((t) => (
              <button
                key={t}
                onClick={() => setTab(t)}
                className={`flex-1 py-2 text-xs font-medium capitalize transition-colors ${
                  tab === t ? 'text-white border-b-2 border-blue-400' : 'text-gray-500 hover:text-gray-300'
                }`}
              >
                {t}
              </button>
            ))}
          </div>

          {/* Content */}
          <div className="flex flex-col flex-1 min-h-0" style={{ height: EXPANDED_HEIGHT - COLLAPSED_HEIGHT - 36 - 44 }}>
            {tab === 'transcript' ? (
              <TranscriptPanel
                transcript={transcript}
                interimText={interimText}
                isRecording={isRecording}
              />
            ) : (
              <ChatPanel
                messages={messages}
                streamingContent={streamingContent}
                isStreaming={isStreaming}
                onSend={sendMessage}
              />
            )}
          </div>

          {/* Controls */}
          <div
            className="flex items-center gap-2 px-3 py-2 border-t border-white/10 rounded-b-xl flex-shrink-0"
            style={{ height: 44, background: 'rgba(8,8,8,0.6)' }}
          >
            {!isRecording ? (
              <button
                onClick={startRecording}
                className="flex-1 py-1.5 rounded-lg bg-red-600/90 hover:bg-red-500 text-xs font-semibold flex items-center justify-center gap-1.5 transition-colors"
              >
                <span className="w-2 h-2 rounded-full bg-white" />
                Start Listening
              </button>
            ) : (
              <button
                onClick={stopRecording}
                className="flex-1 py-1.5 rounded-lg bg-white/10 hover:bg-white/20 text-xs font-semibold flex items-center justify-center gap-1.5 transition-colors"
              >
                <span className="w-2 h-2 rounded-sm bg-gray-300" />
                Stop
              </button>
            )}
            {transcript && (
              <button
                onClick={() => { setTranscript(''); setInterimText('') }}
                className="px-2 py-1.5 rounded-lg bg-white/5 hover:bg-white/10 text-xs text-gray-500 hover:text-gray-300 transition-colors"
                title="Clear transcript"
              >
                Clear
              </button>
            )}
          </div>
        </>
      )}
    </div>
  )
}
