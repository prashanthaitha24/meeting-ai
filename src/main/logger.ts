import * as fs from 'fs'
import * as path from 'path'
import * as os from 'os'
import * as crypto from 'crypto'

const LOG_DIR  = path.join(os.homedir(), '.meeting-ai')
const LOG_FILE = path.join(LOG_DIR, 'app.log')
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
    if (!fs.existsSync(LOG_DIR)) fs.mkdirSync(LOG_DIR, { recursive: true })
    const extraStr = extra != null ? sanitize(extra) : ''
    const line = `[${new Date().toISOString()}] [${level}] ${redact(msg)}${extraStr}\n`

    // Append to file
    fs.appendFileSync(LOG_FILE, line, 'utf8')

    // Rotate: keep last MAX_LINES lines
    const content = fs.readFileSync(LOG_FILE, 'utf8')
    const lines = content.split('\n').filter(Boolean)
    if (lines.length > MAX_LINES) {
      fs.writeFileSync(LOG_FILE, lines.slice(-MAX_LINES).join('\n') + '\n', 'utf8')
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
    if (!fs.existsSync(LOG_FILE)) return '(no log file yet)'
    const content = fs.readFileSync(LOG_FILE, 'utf8')
    return content.split('\n').filter(Boolean).slice(-lines).join('\n')
  } catch {
    return '(could not read log file)'
  }
}

/** Full path so the user can attach manually if needed */
export const LOG_FILE_PATH = LOG_FILE
