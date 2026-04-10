import React, { useState } from 'react'
import type { Session } from '../../../preload/index.d'

interface Props {
  onLogin: (session: Session) => void
}

type Mode = 'signin' | 'signup'

export function AuthScreen({ onLogin }: Props): JSX.Element {
  const [mode, setMode] = useState<Mode>('signin')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [name, setName] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)
  const [loading, setLoading] = useState<'google' | 'apple' | 'email' | null>(null)

  async function handleEmail(e: React.FormEvent) {
    e.preventDefault()
    setError(null)
    setSuccess(null)
    setLoading('email')
    try {
      const session =
        mode === 'signin'
          ? await window.api.emailSignIn(email, password)
          : await window.api.emailSignUp(email, password, name)
      onLogin(session)
    } catch (err: unknown) {
      const raw = err instanceof Error ? err.message : ''
      const lower = raw.toLowerCase()
      if (mode === 'signup' && (lower.includes('check your email') || lower.includes('confirm'))) {
        setSuccess(`Account created! Check your email and click the confirmation link, then come back and sign in.`)
      } else if (lower.includes('invalid login') || lower.includes('invalid credentials') || lower.includes('wrong password') || lower.includes('user not found') || lower.includes('no user')) {
        setError('Incorrect email or password. Please try again.')
      } else if (lower.includes('email not confirmed') || lower.includes('not confirmed')) {
        setError('Please confirm your email address before signing in.')
      } else if (lower.includes('too many requests') || lower.includes('rate limit')) {
        setError('Too many attempts. Please wait a moment and try again.')
      } else if (lower.includes('network') || lower.includes('fetch') || lower.includes('failed to fetch')) {
        setError('Connection error. Please check your internet and try again.')
      } else {
        setError('Something went wrong. Please try again.')
      }
    } finally {
      setLoading(null)
    }
  }

  async function handleGoogle() {
    setError(null)
    setLoading('google')
    try {
      const session = await window.api.googleSignIn()
      onLogin(session)
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Google sign-in failed')
    } finally {
      setLoading(null)
    }
  }

  async function handleApple() {
    setError(null)
    setLoading('apple')
    try {
      const session = await window.api.appleSignIn()
      onLogin(session)
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Apple sign-in failed')
    } finally {
      setLoading(null)
    }
  }

  return (
    <div className="flex flex-col flex-1 px-5 py-6 overflow-y-auto">
      {/* Branding */}
      <div className="flex flex-col items-center mb-6">
        <div className="w-12 h-12 rounded-full bg-blue-600/20 border border-blue-500/40 flex items-center justify-center mb-3">
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#60a5fa" strokeWidth="1.8" strokeLinecap="round">
            <path d="M12 2a3 3 0 0 1 3 3v7a3 3 0 0 1-6 0V5a3 3 0 0 1 3-3z" />
            <path d="M19 10v2a7 7 0 0 1-14 0v-2" />
            <line x1="12" y1="19" x2="12" y2="22" />
          </svg>
        </div>
        <h1 className="text-base font-semibold text-white">Meeting AI</h1>
        <p className="text-xs text-gray-500 mt-0.5">
          {mode === 'signin' ? 'Sign in to your account' : 'Create your account'}
        </p>
      </div>

      {/* Google button */}
      <button
        onClick={handleGoogle}
        disabled={!!loading}
        className="w-full flex items-center justify-center gap-2 py-2 px-4 rounded-lg border border-white/15 bg-white/5 hover:bg-white/10 text-sm text-gray-200 transition-colors disabled:opacity-50 mb-2"
      >
        {loading === 'google' ? (
          <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
        ) : (
          <svg width="16" height="16" viewBox="0 0 24 24">
            <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
            <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
            <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
            <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
          </svg>
        )}
        Continue with Google
      </button>

      {/* Apple Sign-In */}
      <button
        onClick={handleApple}
        disabled={!!loading}
        className="w-full flex items-center justify-center gap-2 py-2 px-4 rounded-lg border border-white/15 bg-white/5 hover:bg-white/10 text-sm text-gray-200 transition-colors disabled:opacity-50 mb-4"
      >
        {loading === 'apple' ? (
          <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
        ) : (
          <svg width="15" height="15" viewBox="0 0 814 1000" fill="currentColor">
            <path d="M788.1 340.9c-5.8 4.5-108.2 62.2-108.2 190.5 0 148.4 130.3 200.9 134.2 202.2-.6 3.2-20.7 71.9-68.7 141.9-42.8 61.6-87.5 123.1-155.5 123.1s-85.5-39.5-164-39.5c-76 0-103.7 40.8-165.9 40.8s-105-57.8-155.5-127.4C46 790.7 0 663 0 541.8c0-207.5 134.4-317.5 266.5-317.5 49.2 0 101.3 32.3 134.4 32.3 27.9 0 84.5-36.7 147.8-36.7z"/>
            <path d="M580.3 126.7c-23.8 27.2-62.4 48.9-103.8 45.7-3.7-36.5 14.2-74.6 36.5-100.2C535.6 46 576.3 25.5 614.8 24c3.7 37.3-10.9 75-34.5 102.7z"/>
          </svg>
        )}
        Continue with Apple
      </button>

      {/* Divider */}
      <div className="flex items-center gap-3 mb-4">
        <div className="flex-1 h-px bg-white/10" />
        <span className="text-xs text-gray-600">or</span>
        <div className="flex-1 h-px bg-white/10" />
      </div>

      {/* Email form */}
      <form onSubmit={handleEmail} className="flex flex-col gap-2">
        {mode === 'signup' && (
          <input
            type="text"
            placeholder="Full name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            required
            className="w-full rounded-lg px-3 py-2 text-sm outline-none transition-colors"
            style={{ background: 'rgba(255,255,255,0.08)', border: '1px solid rgba(255,255,255,0.12)', color: '#f1f5f9', caretColor: '#60a5fa', WebkitUserSelect: 'text' }}
          />
        )}
        <input
          type="email"
          placeholder="Email address"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
          className="w-full rounded-lg px-3 py-2 text-sm outline-none transition-colors"
          style={{ background: 'rgba(255,255,255,0.08)', border: '1px solid rgba(255,255,255,0.12)', color: '#f1f5f9', caretColor: '#60a5fa', WebkitUserSelect: 'text' }}
        />
        <input
          type="password"
          placeholder="Password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
          minLength={8}
          className="w-full rounded-lg px-3 py-2 text-sm outline-none transition-colors"
          style={{ background: 'rgba(255,255,255,0.08)', border: '1px solid rgba(255,255,255,0.12)', color: '#f1f5f9', caretColor: '#60a5fa', WebkitUserSelect: 'text' }}
        />

        {error && (
          <p className="text-xs text-red-400 bg-red-900/20 border border-red-800/40 rounded-lg px-3 py-2">
            {error}
          </p>
        )}
        {success && (
          <p className="text-xs text-emerald-400 bg-emerald-900/20 border border-emerald-800/40 rounded-lg px-3 py-2 leading-relaxed">
            {success}
          </p>
        )}

        <button
          type="submit"
          disabled={!!loading}
          className="w-full py-2 rounded-lg bg-blue-600 hover:bg-blue-500 text-sm font-medium text-white transition-colors disabled:opacity-50 flex items-center justify-center gap-2"
        >
          {loading === 'email' ? (
            <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
          ) : null}
          {mode === 'signin' ? 'Sign In' : 'Create Account'}
        </button>
      </form>

      {/* Toggle mode */}
      <p className="text-xs text-gray-500 text-center mt-4">
        {mode === 'signin' ? "Don't have an account? " : 'Already have an account? '}
        <button
          onClick={() => { setMode(mode === 'signin' ? 'signup' : 'signin'); setError(null) }}
          className="text-blue-400 hover:text-blue-300 underline transition-colors"
        >
          {mode === 'signin' ? 'Create one' : 'Sign in'}
        </button>
      </p>

      <p className="text-[10px] text-gray-600 text-center mt-3 leading-relaxed">
        Check your email to confirm your account after signing up.
      </p>
    </div>
  )
}
