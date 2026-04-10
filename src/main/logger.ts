import * as fs from 'fs'
import * as path from 'path'
import * as os from 'os'

const LOG_DIR  = path.join(os.homedir(), '.meeting-ai')
const LOG_FILE = path.join(LOG_DIR, 'app.log')
const MAX_LINES = 500

type Level = 'INFO' | 'WARN' | 'ERROR'

function write(level: Level, msg: string, extra?: unknown): void {
  try {
    if (!fs.existsSync(LOG_DIR)) fs.mkdirSync(LOG_DIR, { recursive: true })
    const extraStr = extra != null
      ? ' ' + (extra instanceof Error ? `${extra.message}\n${extra.stack}` : JSON.stringify(extra))
      : ''
    const line = `[${new Date().toISOString()}] [${level}] ${msg}${extraStr}\n`

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
