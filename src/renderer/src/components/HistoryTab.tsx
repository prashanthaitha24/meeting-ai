import React, { useState, useEffect, useCallback } from 'react'
import type { HistorySession } from '../../../preload/index.d'

const DAY_OPTIONS = [15, 30, 45, 60, 75, 90]

function formatDate(iso: string): string {
  const d = new Date(iso)
  return d.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric', year: 'numeric' })
}

function formatTime(iso: string): string {
  return new Date(iso).toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' })
}

function groupByDate(sessions: HistorySession[]): Record<string, HistorySession[]> {
  return sessions.reduce((acc, s) => {
    const key = new Date(s.date).toDateString()
    if (!acc[key]) acc[key] = []
    acc[key].push(s)
    return acc
  }, {} as Record<string, HistorySession[]>)
}

function SessionCard({ session }: { session: HistorySession }) {
  const [expanded, setExpanded] = useState(false)
  const qaCount = session.entries.length

  return (
    <div className="rounded-lg overflow-hidden" style={{ border: '1px solid rgba(255,255,255,0.08)' }}>
      <button
        onClick={() => setExpanded((p) => !p)}
        className="w-full flex items-center justify-between px-3 py-2 text-left hover:bg-white/5 transition-colors"
        style={{ background: 'rgba(255,255,255,0.03)' }}>
        <div className="flex items-center gap-2 min-w-0">
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#60a5fa" strokeWidth="2" strokeLinecap="round" className="flex-shrink-0">
            <circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/>
          </svg>
          <span className="text-[11px] text-gray-400">{formatTime(session.date)}</span>
          <span className="text-[10px] text-gray-600">·</span>
          <span className="text-[10px] text-gray-500">{qaCount} Q&amp;A{qaCount !== 1 ? 's' : ''}</span>
        </div>
        <svg
          width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"
          className={`text-gray-600 transition-transform flex-shrink-0 ${expanded ? 'rotate-180' : ''}`}>
          <polyline points="6 9 12 15 18 9"/>
        </svg>
      </button>

      {expanded && (
        <div className="px-3 pb-3 space-y-3" style={{ borderTop: '1px solid rgba(255,255,255,0.06)' }}>
          {session.entries.length === 0 ? (
            <p className="text-[11px] text-gray-600 pt-2">No Q&amp;A recorded in this session.</p>
          ) : (
            session.entries.map((entry, i) => (
              <div key={i} className="pt-2">
                <p className="text-[10px] font-semibold text-blue-400/80 mb-1">Q: {entry.question}</p>
                <p className="text-[11px] text-gray-400 leading-relaxed whitespace-pre-wrap">{entry.answer}</p>
              </div>
            ))
          )}
          {session.tabContent.recap && (
            <div className="pt-1" style={{ borderTop: '1px solid rgba(255,255,255,0.06)' }}>
              <p className="text-[10px] font-semibold text-emerald-400/80 mb-1">Recap</p>
              <p className="text-[11px] text-gray-400 leading-relaxed whitespace-pre-wrap">{session.tabContent.recap}</p>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

interface Props {
  userId: string
}

export function HistoryTab({ userId }: Props): JSX.Element {
  const [days, setDays] = useState(30)
  const [sessions, setSessions] = useState<HistorySession[]>([])
  const [loading, setLoading] = useState(true)
  const [clearing, setClearing] = useState(false)

  const loadHistory = useCallback(async () => {
    setLoading(true)
    const data = await window.api.loadHistory(userId, days)
    setSessions(data)
    setLoading(false)
  }, [userId, days])

  useEffect(() => { loadHistory() }, [loadHistory])

  const handleClear = async () => {
    if (!window.confirm('Clear all history? This cannot be undone.')) return
    setClearing(true)
    await window.api.clearHistory(userId)
    setSessions([])
    setClearing(false)
  }

  const grouped = groupByDate(sessions)
  const dateKeys = Object.keys(grouped)

  return (
    <div className="flex flex-col flex-1 min-h-0 overflow-hidden">
      {/* Toolbar */}
      <div className="flex items-center justify-between px-3 py-2 flex-shrink-0"
        style={{ borderBottom: '1px solid rgba(255,255,255,0.06)' }}>
        <div className="flex items-center gap-1.5">
          <span className="text-[10px] text-gray-500">Show last</span>
          <select
            value={days}
            onChange={(e) => setDays(Number(e.target.value))}
            className="text-[10px] rounded px-1.5 py-0.5 outline-none"
            style={{ background: 'rgba(255,255,255,0.08)', border: '1px solid rgba(255,255,255,0.12)', color: '#e2e8f0' }}>
            {DAY_OPTIONS.map((d) => (
              <option key={d} value={d}>{d} days</option>
            ))}
          </select>
        </div>
        <button
          onClick={handleClear}
          disabled={clearing || sessions.length === 0}
          className="text-[10px] text-red-500/70 hover:text-red-400 disabled:opacity-30 disabled:cursor-not-allowed transition-colors px-2 py-0.5 rounded hover:bg-red-500/10">
          {clearing ? 'Clearing…' : 'Clear Cache'}
        </button>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto min-h-0 p-3">
        {loading ? (
          <div className="flex items-center justify-center h-full">
            <span className="w-4 h-4 border-2 border-white/20 border-t-white rounded-full animate-spin" />
          </div>
        ) : dateKeys.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full gap-2 text-center">
            <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="rgba(255,255,255,0.15)" strokeWidth="1.5">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/>
            </svg>
            <p className="text-[11px] text-gray-600">No sessions in the last {days} days</p>
            <p className="text-[10px] text-gray-700">Sessions are saved when you sign out</p>
          </div>
        ) : (
          <div className="space-y-4">
            {dateKeys.map((dateKey) => (
              <div key={dateKey}>
                <p className="text-[10px] font-semibold text-gray-500 uppercase tracking-wider mb-2">
                  {formatDate(grouped[dateKey][0].date)}
                </p>
                <div className="space-y-1.5">
                  {grouped[dateKey].map((s) => (
                    <SessionCard key={s.id} session={s} />
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
