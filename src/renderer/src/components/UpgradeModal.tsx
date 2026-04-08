import React from 'react'

interface Props {
  onClose: () => void
  freeCallsUsed: number
}

export function UpgradeModal({ onClose, freeCallsUsed }: Props): JSX.Element {
  const handleUpgrade = async () => {
    await window.api.stripeCheckout()
    onClose()
  }

  return (
    <div
      className="absolute inset-0 flex items-center justify-center z-50 rounded-xl"
      style={{ background: 'rgba(0,0,0,0.75)', backdropFilter: 'blur(8px)' }}
    >
      <div
        className="mx-4 rounded-2xl border border-white/15 overflow-hidden"
        style={{ background: 'rgba(20,20,20,0.98)', width: 360 }}
      >
        {/* Header */}
        <div className="px-5 pt-5 pb-4 text-center border-b border-white/10">
          <div className="w-12 h-12 rounded-full bg-amber-500/15 border border-amber-500/30 flex items-center justify-center mx-auto mb-3">
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#f59e0b" strokeWidth="1.8">
              <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2" />
            </svg>
          </div>
          <h2 className="text-base font-semibold text-white">Upgrade to Pro</h2>
          <p className="text-xs text-gray-400 mt-1">
            You've used all {freeCallsUsed} of your free AI answers
          </p>
        </div>

        {/* Features */}
        <div className="px-5 py-4 space-y-2.5">
          {[
            'Unlimited AI answers during interviews',
            'All tabs: Say This, Follow-up, Recap',
            'Screen read (⌘↵) unlimited',
            'Export notes & email summaries',
            'Priority response speed',
          ].map((f) => (
            <div key={f} className="flex items-center gap-2.5">
              <span className="w-4 h-4 rounded-full bg-emerald-500/20 flex items-center justify-center flex-shrink-0">
                <svg width="9" height="9" viewBox="0 0 24 24" fill="none" stroke="#10b981" strokeWidth="3">
                  <polyline points="20 6 9 17 4 12" />
                </svg>
              </span>
              <span className="text-xs text-gray-300">{f}</span>
            </div>
          ))}
        </div>

        {/* Pricing */}
        <div className="px-5 pb-5 space-y-2.5">
          <button
            onClick={handleUpgrade}
            className="w-full py-2.5 rounded-xl bg-blue-600 hover:bg-blue-500 text-sm font-semibold text-white transition-colors flex items-center justify-center gap-2"
          >
            Upgrade — $9.99 / month
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
              <line x1="5" y1="12" x2="19" y2="12" /><polyline points="12 5 19 12 12 19" />
            </svg>
          </button>
          <button
            onClick={onClose}
            className="w-full py-2 rounded-xl text-xs text-gray-600 hover:text-gray-400 transition-colors"
          >
            Maybe later
          </button>
          <p className="text-[10px] text-gray-700 text-center">
            Cancel anytime · Billed monthly via Stripe
          </p>
        </div>
      </div>
    </div>
  )
}
