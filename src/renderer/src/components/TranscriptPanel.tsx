import React, { useEffect, useRef } from 'react'

export type TranscriptEntry =
  | { id: string; type: 'speech'; text: string }
  | { id: string; type: 'qa'; question: string; answer: string; streaming: boolean }

interface Props {
  entries: TranscriptEntry[]
  interimText: string
  isRecording: boolean
  onManualSend: (text: string) => void
  isStreaming: boolean
}

export function TranscriptPanel({ entries, interimText, isRecording, onManualSend, isStreaming }: Props): JSX.Element {
  const bottomRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [entries, interimText])

  const handleKey = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !isStreaming) {
      const val = (e.target as HTMLInputElement).value.trim()
      if (val) { onManualSend(val); (e.target as HTMLInputElement).value = '' }
    }
  }

  const isEmpty = entries.length === 0 && !interimText

  return (
    <div className="flex flex-col flex-1 min-h-0 overflow-hidden">
      {/* Feed — scrollable */}
      <div className="flex-1 overflow-y-auto min-h-0 p-3 space-y-2 text-sm">
        {isEmpty && (
          <p className="text-gray-600 text-xs mt-4 text-center">
            {isRecording ? 'Listening… speak to start' : 'Press Start to begin'}
          </p>
        )}

        {entries.map((entry) =>
          entry.type === 'speech' ? (
            <p key={entry.id} className="text-gray-300 leading-relaxed">{entry.text}</p>
          ) : (
            <div key={entry.id} className="rounded-lg overflow-hidden border border-white/10">
              {/* Question */}
              <div className="px-3 py-2" style={{ background: 'rgba(59,130,246,0.12)' }}>
                <p className="text-[11px] text-blue-400 font-semibold mb-0.5">Question</p>
                <p className="text-blue-200 text-xs leading-relaxed">{entry.question}</p>
              </div>
              {/* Answer */}
              <div className="px-3 py-2" style={{ background: 'rgba(255,255,255,0.04)' }}>
                <p className="text-[11px] text-emerald-400 font-semibold mb-0.5">Answer</p>
                {entry.answer ? (
                  <p className="text-gray-100 text-xs leading-relaxed whitespace-pre-wrap">
                    {entry.answer}
                    {entry.streaming && (
                      <span className="inline-block w-1.5 h-3 bg-emerald-400 ml-0.5 align-middle animate-pulse rounded-sm" />
                    )}
                  </p>
                ) : (
                  <span className="text-gray-600 text-xs">
                    <span className="inline-block w-1.5 h-3 bg-emerald-400 mr-1 align-middle animate-pulse rounded-sm" />
                    Thinking…
                  </span>
                )}
              </div>
            </div>
          )
        )}

        {/* Interim speech (real-time from Web Speech API) */}
        {interimText && (
          <p className="text-gray-500 italic text-xs">
            {interimText}
            <span className="inline-block w-1.5 h-3 bg-blue-400 ml-0.5 align-middle animate-pulse rounded-sm" />
          </p>
        )}

        <div ref={bottomRef} />
      </div>

      {/* Follow-up input */}
      <div className="border-t border-white/10 px-3 py-2 flex gap-2 items-center flex-shrink-0"
        style={{ background: 'rgba(8,8,8,0.4)' }}>
        <input
          ref={inputRef}
          type="text"
          placeholder="Ask a follow-up…"
          disabled={isStreaming}
          onKeyDown={handleKey}
          className="flex-1 bg-white/8 border border-white/10 rounded-lg px-3 py-1.5 text-xs text-gray-100 placeholder-gray-600 outline-none focus:border-blue-500/50 disabled:opacity-40 transition-colors"
        />
        <button
          disabled={isStreaming}
          onClick={() => {
            const val = inputRef.current?.value.trim()
            if (val && !isStreaming) { onManualSend(val); if (inputRef.current) inputRef.current.value = '' }
          }}
          className="w-7 h-7 rounded-lg bg-blue-600/80 hover:bg-blue-500 disabled:opacity-40 flex items-center justify-center transition-colors"
        >
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round">
            <line x1="22" y1="2" x2="11" y2="13" />
            <polygon points="22 2 15 22 11 13 2 9 22 2" />
          </svg>
        </button>
      </div>
    </div>
  )
}
