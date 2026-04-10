import React, { useState } from 'react'

interface Props {
  onAccept: () => void
  onDecline: () => void
}

export function ConsentScreen({ onAccept, onDecline }: Props): JSX.Element {
  const [checked, setChecked] = useState(false)

  return (
    <div className="flex flex-col flex-1 px-5 py-6 overflow-y-auto">
      {/* Logo */}
      <div className="flex flex-col items-center mb-5">
        <div className="w-12 h-12 rounded-full bg-blue-600/20 border border-blue-500/40 flex items-center justify-center mb-3">
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#60a5fa" strokeWidth="1.8" strokeLinecap="round">
            <path d="M12 2a3 3 0 0 1 3 3v7a3 3 0 0 1-6 0V5a3 3 0 0 1 3-3z" />
            <path d="M19 10v2a7 7 0 0 1-14 0v-2" />
            <line x1="12" y1="19" x2="12" y2="22" />
          </svg>
        </div>
        <h1 className="text-sm font-bold text-white">Before You Begin</h1>
        <p className="text-[11px] text-gray-500 mt-0.5">Please read and accept the following</p>
      </div>

      {/* Disclaimer box */}
      <div
        className="rounded-xl p-4 mb-4 flex-1 overflow-y-auto"
        style={{ background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.1)' }}>

        <p className="text-[11px] font-semibold text-blue-400 uppercase tracking-wider mb-3">
          Terms of Use &amp; Disclaimer
        </p>

        <div className="space-y-3 text-[11px] text-gray-400 leading-relaxed">
          <p>
            Meeting AI by ThavionAI is an AI-powered assistant for meetings and interviews.
            Please read the following carefully before using the app.
          </p>

          <div>
            <p className="text-gray-300 font-medium mb-1">1. Data We Collect</p>
            <p>
              We collect your email address and name (for your account) and usage counts.
              Meeting transcripts and session history are stored <strong className="text-gray-300">locally on your device only</strong> — never on our servers.
            </p>
          </div>

          <div>
            <p className="text-gray-300 font-medium mb-1">2. Third-Party Data Processors</p>
            <p>
              Audio is sent to <strong className="text-gray-300">OpenAI Whisper</strong> for transcription and is not retained after processing.
              AI responses are generated via <strong className="text-gray-300">Anthropic Claude</strong>.
              Accounts are managed by <strong className="text-gray-300">Supabase</strong>.
              Payments are handled by <strong className="text-gray-300">Stripe</strong>.
              Crash reports may be sent to <strong className="text-gray-300">Sentry</strong>.
              None of your meeting content is sold or shared for advertising.
            </p>
          </div>

          <div>
            <p className="text-gray-300 font-medium mb-1">3. Recording &amp; Consent</p>
            <p>
              You are solely responsible for complying with all applicable recording laws.
              Many jurisdictions require all-party consent before recording a conversation.
              Ensure you have consent from all participants before using transcription features.
            </p>
          </div>

          <div>
            <p className="text-gray-300 font-medium mb-1">4. Your Rights (GDPR / CCPA)</p>
            <p>
              You have the right to access, export, and permanently delete your data at any time
              from Settings → Account. California residents have the right to know we do not sell
              personal information.
            </p>
          </div>

          <div>
            <p className="text-gray-300 font-medium mb-1">5. Limitation of Liability</p>
            <p>
              AI responses are for informational purposes only and do not constitute professional
              advice. ThavionAI is not liable for decisions made based on app output.
            </p>
          </div>

          <div>
            <p className="text-gray-300 font-medium mb-1">6. Legal</p>
            <p>
              By continuing you agree to our{' '}
              <button onClick={() => window.api.openExternal('https://thavionai.com/privacy.html')}
                className="text-blue-400 underline hover:text-blue-300">Privacy Policy</button>
              {' '}and{' '}
              <button onClick={() => window.api.openExternal('https://thavionai.com/terms.html')}
                className="text-blue-400 underline hover:text-blue-300">Terms of Service</button>.
            </p>
          </div>
        </div>
      </div>

      {/* Checkbox */}
      <label className="flex items-start gap-2.5 mb-4 cursor-pointer"
        style={{ WebkitUserSelect: 'none' } as React.CSSProperties}>
        <input
          type="checkbox"
          checked={checked}
          onChange={(e) => setChecked(e.target.checked)}
          className="mt-0.5 accent-blue-500 cursor-pointer flex-shrink-0"
          style={{ width: 14, height: 14 }}
        />
        <span className="text-[11px] text-gray-400 leading-relaxed">
          I have read and understood the above disclaimer. I accept full responsibility for how
          I use Meeting AI and agree to the Terms of Service and Privacy Policy.
        </span>
      </label>

      {/* Buttons */}
      <div className="flex gap-2">
        <button
          onClick={onDecline}
          className="flex-1 py-2 rounded-lg text-xs text-gray-500 hover:text-gray-300 transition-colors"
          style={{ border: '1px solid rgba(255,255,255,0.1)' }}>
          Decline &amp; Quit
        </button>
        <button
          onClick={onAccept}
          disabled={!checked}
          className="flex-1 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 disabled:opacity-40 disabled:cursor-not-allowed text-xs font-semibold text-white transition-colors">
          Accept &amp; Continue
        </button>
      </div>
    </div>
  )
}
