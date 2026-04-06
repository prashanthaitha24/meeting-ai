import React, { useEffect, useRef } from 'react'

interface Props {
  transcript: string
  interimText: string
  isRecording: boolean
}

export function TranscriptPanel({ transcript, interimText, isRecording }: Props): JSX.Element {
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [transcript, interimText])

  return (
    <div className="flex-1 overflow-y-auto p-3 text-sm leading-relaxed">
      {transcript || interimText ? (
        <>
          {transcript && (
            <p className="whitespace-pre-wrap text-gray-200">{transcript}</p>
          )}
          {interimText && (
            <p className="whitespace-pre-wrap text-gray-500 italic mt-0.5">
              {interimText}
              <span className="inline-block w-1.5 h-3.5 bg-blue-400 ml-0.5 align-middle animate-pulse rounded-sm" />
            </p>
          )}
          {isRecording && !interimText && (
            <span className="inline-block w-1.5 h-3.5 bg-blue-400 ml-1 align-middle animate-pulse rounded-sm" />
          )}
        </>
      ) : (
        <p className="text-gray-600 text-xs mt-4 text-center">
          {isRecording ? 'Listening… speak to start transcribing' : 'Press Start to begin listening'}
        </p>
      )}
      <div ref={bottomRef} />
    </div>
  )
}
