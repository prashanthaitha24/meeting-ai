import * as fs from 'fs'
import * as path from 'path'
import * as crypto from 'crypto'
import { app } from 'electron'

function logDir(): string  { return app.getPath('userData') }
function logFile(): string { return path.join(logDir(), 'app.log') }

const MAX_LINES = 500

type Level = 'INFO' | 'WARN' | 'ERROR'

// Redact patterns that look like UUIDs (user IDs), email addresses, or JWT tokens
const UUID_RE  = /\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b/gi
const EMAIL_RE = /\b[a-z0-9._%+\-]+@[a-z0-9.\-]+\.[a-z]{2,}\b/gi
const JWT_RE   = /eyJ[a-zA-Z0-9\-_]+\.eyJ[a-zA-Z0-9\-_]+\.[a-zA-Z0-9\-_.+/=]*/g

function redact(text: string): string {
  return text
    .replace(JWT_RE,   '[jwt]')
    .replace(UUID_RE,  (m) => `[uid:${crypto.createHash('sha256').update(m).digest('hex').slice(0, 6)}]`)
    .replace(EMAIL_RE, '[email]')
}

function sanitize(extra: unknown): string {
  if (extra == null) return ''
  const raw = extra instanceof Error ? `${extra.message}\n${extra.stack}` : JSON.stringify(extra)
  return ' ' + redact(raw)
}

function write(level: Level, msg: string, extra?: unknown): void {
  try {
    const dir = logDir()
    if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true })
    const file = logFile()
    const extraStr = extra != null ? sanitize(extra) : ''
    const line = `[${new Date().toISOString()}] [${level}] ${redact(msg)}${extraStr}\n`

    fs.appendFileSync(file, line, 'utf8')

    // Rotate: keep last MAX_LINES lines
    const content = fs.readFileSync(file, 'utf8')
    const lines = content.split('\n').filter(Boolean)
    if (lines.length > MAX_LINES) {
      fs.writeFileSync(file, lines.slice(-MAX_LINES).join('\n') + '\n', 'utf8')
    }
  } catch {
    // never throw from logger
  }
}

export const log = {
  info:  (msg: string, extra?: unknown) => { console.log(`[INFO] ${msg}`, extra ?? '');  write('INFO',  msg, extra) },
  warn:  (msg: string, extra?: unknown) => { console.warn(`[WARN] ${msg}`, extra ?? ''); write('WARN',  msg, extra) },
  error: (msg: string, extra?: unknown) => { console.error(`[ERROR] ${msg}`, extra ?? ''); write('ERROR', msg, extra) },
}
// Note: msg logged to console is NOT redacted (dev use), file log IS redacted.

/** Read last N lines from log file for diagnostic report */
export function readRecentLogs(lines = 100): string {
  try {
    const file = logFile()
    if (!fs.existsSync(file)) return '(no log file yet)'
    const content = fs.readFileSync(file, 'utf8')
    return content.split('\n').filter(Boolean).slice(-lines).join('\n')
  } catch {
    return '(could not read log file)'
  }
}

/** Full path so the user can attach manually if needed */
export function getLogFilePath(): string { return logFile() }

/** @deprecated Use getLogFilePath() — kept for callers that reference the old export */
export const LOG_FILE_PATH = path.join(app.getPath('userData'), 'app.log')
