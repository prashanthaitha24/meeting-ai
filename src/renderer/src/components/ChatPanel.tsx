import React, { useEffect, useRef, useState } from 'react'

export interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
}

interface Props {
  messages: ChatMessage[]
  streamingContent: string
  isStreaming: boolean
  onSend: (text: string) => void
}

export function ChatPanel({ messages, streamingContent, isStreaming, onSend }: Props): JSX.Element {
  const [input, setInput] = useState('')
  const bottomRef = useRef<HTMLDivElement>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, streamingContent])

  const handleSend = (): void => {
    const text = input.trim()
    if (!text || isStreaming) return
    setInput('')
    onSend(text)
  }

  const handleKeyDown = (e: React.KeyboardEvent): void => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <div className="flex flex-col flex-1 min-h-0">
      {/* Message list */}
      <div className="flex-1 overflow-y-auto p-3 space-y-3">
        {messages.length === 0 && !isStreaming && (
          <p className="text-gray-500 text-xs mt-4 text-center">
            Ask anything about the meeting…
          </p>
        )}

        {messages.map((msg, i) => (
          <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div
              className={`max-w-[85%] rounded-xl px-3 py-2 text-sm leading-relaxed ${
                msg.role === 'user'
                  ? 'bg-blue-600 text-white rounded-br-sm'
                  : 'bg-[#333] text-gray-100 rounded-bl-sm'
              }`}
            >
              {msg.content}
            </div>
          </div>
        ))}

        {/* Streaming assistant message */}
        {(isStreaming || streamingContent) && (
          <div className="flex justify-start">
            <div className="max-w-[85%] rounded-xl rounded-bl-sm px-3 py-2 text-sm leading-relaxed bg-[#333] text-gray-100">
              {streamingContent || <span className="text-gray-500">Thinking…</span>}
              {isStreaming && (
                <span className="inline-block w-1.5 h-3.5 bg-blue-400 ml-0.5 animate-pulse rounded-sm" />
              )}
            </div>
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div className="border-t border-[#333] p-2 flex gap-2 items-end">
        <textarea
          ref={textareaRef}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask about the meeting…"
          rows={1}
          disabled={isStreaming}
          className="flex-1 bg-[#333] text-gray-100 text-sm rounded-lg px-3 py-2 resize-none outline-none placeholder-gray-500 disabled:opacity-50 max-h-24"
          style={{ minHeight: '36px' }}
        />
        <button
          onClick={handleSend}
          disabled={!input.trim() || isStreaming}
          className="flex-shrink-0 w-8 h-8 rounded-lg bg-blue-600 hover:bg-blue-500 disabled:opacity-40 disabled:cursor-not-allowed flex items-center justify-center transition-colors"
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <line x1="22" y1="2" x2="11" y2="13" />
            <polygon points="22 2 15 22 11 13 2 9 22 2" />
          </svg>
        </button>
      </div>
    </div>
  )
}
