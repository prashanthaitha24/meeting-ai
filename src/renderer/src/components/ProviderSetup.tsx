import React, { useState } from 'react'
import { PROVIDER_LIST, type ProviderId } from '../../../shared/providers'

interface Props {
  /** Called after a key is validated and saved. */
  onDone: () => void
}

type TestState =
  | { kind: 'idle' }
  | { kind: 'testing' }
  | { kind: 'error'; message: string }

export function ProviderSetup({ onDone }: Props): JSX.Element {
  const [providerId, setProviderId] = useState<ProviderId>(PROVIDER_LIST[0].id)
  const [key, setKey] = useState('')
  const [test, setTest] = useState<TestState>({ kind: 'idle' })

  const provider = PROVIDER_LIST.find((p) => p.id === providerId)!
  const busy = test.kind === 'testing'

  const handleSave = async () => {
    const trimmed = key.trim()
    if (!trimmed) {
      setTest({ kind: 'error', message: 'Paste your API key first.' })
      return
    }
    setTest({ kind: 'testing' })
    const result = await window.api.byokTest({ providerId, key: trimmed })
    if (!result.ok) {
      setTest({ kind: 'error', message: result.error || 'That key was rejected. Double-check and try again.' })
      return
    }
    await window.api.byokSet({ providerId, key: trimmed })
    onDone()
  }

  const selectProvider = (id: ProviderId) => {
    setProviderId(id)
    setKey('')
    setTest({ kind: 'idle' })
  }

  return (
    <div className="flex flex-col flex-1 px-5 py-5 overflow-y-auto">
      {/* Heading */}
      <div className="mb-4">
        <h1 className="text-sm font-bold text-white">Connect your AI</h1>
        <p className="text-[11px] text-gray-500 mt-1 leading-relaxed">
          Meeting AI is free — you bring your own API key. Your key is encrypted and stored only on
          this device; requests go straight to the provider, never through us.
        </p>
      </div>

      {/* Provider cards */}
      <div className="space-y-2 mb-4">
        {PROVIDER_LIST.map((p) => {
          const active = p.id === providerId
          return (
            <button
              key={p.id}
              onClick={() => selectProvider(p.id)}
              className="w-full text-left rounded-xl p-3 transition-colors"
              style={{
                background: active ? 'rgba(37,99,235,0.14)' : 'rgba(255,255,255,0.04)',
                border: active ? '1px solid rgba(96,165,250,0.55)' : '1px solid rgba(255,255,255,0.1)',
              }}>
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-white">{p.label}</span>
                <span
                  className="w-3.5 h-3.5 rounded-full flex-shrink-0 flex items-center justify-center"
                  style={{
                    border: active ? '4px solid #60a5fa' : '1px solid rgba(255,255,255,0.25)',
                  }}
                />
              </div>
              <p className="text-[10.5px] text-gray-400 mt-1 leading-snug">{p.blurb}</p>
            </button>
          )
        })}
      </div>

      {/* Key entry */}
      <div className="mb-3">
        <div className="flex items-center justify-between mb-1.5">
          <label className="text-[11px] font-medium text-gray-300">{provider.label} API key</label>
          <button
            onClick={() => window.api.openExternal(provider.signupUrl)}
            className="text-[10.5px] text-blue-400 hover:text-blue-300 underline">
            Get a key →
          </button>
        </div>
        <input
          type="password"
          value={key}
          onChange={(e) => {
            setKey(e.target.value)
            if (test.kind === 'error') setTest({ kind: 'idle' })
          }}
          placeholder={provider.keyPlaceholder}
          spellCheck={false}
          autoComplete="off"
          className="w-full rounded-lg px-3 py-2 text-xs text-white placeholder-gray-600 outline-none focus:border-blue-500/60"
          style={{ background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.12)' }}
        />
        {test.kind === 'error' && (
          <p className="text-[10.5px] text-red-400 mt-1.5">{test.message}</p>
        )}
      </div>

      {/* Save */}
      <button
        onClick={handleSave}
        disabled={busy}
        className="w-full py-2 rounded-lg bg-blue-600 hover:bg-blue-500 disabled:opacity-50 disabled:cursor-not-allowed text-xs font-semibold text-white transition-colors flex items-center justify-center gap-2">
        {busy ? (
          <>
            <span className="w-3 h-3 border-2 border-white/30 border-t-white rounded-full animate-spin" />
            Checking…
          </>
        ) : (
          'Validate & Continue'
        )}
      </button>

      <p className="text-[10px] text-gray-600 mt-3 text-center leading-snug">
        You can change provider or key anytime in Settings.
      </p>
    </div>
  )
}
