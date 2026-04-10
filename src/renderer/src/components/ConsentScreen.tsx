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
            Meeting AI ("the App") is an AI-powered assistant designed to support users during
            meetings and interviews. By using the App, you acknowledge and agree to the following:
          </p>

          <div>
            <p className="text-gray-300 font-medium mb-1">1. No Guarantee of Accuracy</p>
            <p>
              AI-generated responses are provided for informational and assistive purposes only.
              They may contain errors, omissions, or inaccuracies. You are solely responsible for
              evaluating and verifying any content before acting on it.
            </p>
          </div>

          <div>
            <p className="text-gray-300 font-medium mb-1">2. Professional Responsibility</p>
            <p>
              The App does not constitute legal, financial, medical, or professional advice of any
              kind. AI-Empire and its developers are not liable for any decisions made, outcomes
              achieved, or consequences arising from use of the App or its generated content.
            </p>
          </div>

          <div>
            <p className="text-gray-300 font-medium mb-1">3. Recording &amp; Consent</p>
            <p>
              You are solely responsible for complying with all applicable laws regarding the
              recording and transcription of conversations. In many jurisdictions, all-party consent
              is required before recording. Ensure you have obtained all necessary consents before
              using the App's transcription features.
            </p>
          </div>

          <div>
            <p className="text-gray-300 font-medium mb-1">4. Limitation of Liability</p>
            <p>
              To the maximum extent permitted by law, AI-Empire shall not be liable for any
              indirect, incidental, consequential, or punitive damages arising from your use of
              the App, including but not limited to interview outcomes, employment decisions, or
              business results.
            </p>
          </div>

          <div>
            <p className="text-gray-300 font-medium mb-1">5. Data &amp; Privacy</p>
            <p>
              Audio is processed in real time and is not retained after transcription. Your account
              data is stored securely. By using the App, you agree to our{' '}
              <button
                onClick={() => window.api.openExternal('https://prashanthaitha24.github.io/meeting-ai/privacy.html')}
                className="text-blue-400 underline hover:text-blue-300">
                Privacy Policy
              </button>
              {' '}and{' '}
              <button
                onClick={() => window.api.openExternal('https://prashanthaitha24.github.io/meeting-ai/terms.html')}
                className="text-blue-400 underline hover:text-blue-300">
                Terms of Service
              </button>.
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
