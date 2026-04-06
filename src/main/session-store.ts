import { safeStorage, app } from 'electron'
import * as fs from 'fs'
import * as path from 'path'

export interface Session {
  userId: string
  email: string
  name: string | null
  avatarUrl: string | null
  provider: 'google' | 'email'
  expiresAt: number
}

const SESSION_DURATION_MS = 24 * 60 * 60 * 1000 // 24 hours

function sessionFilePath(): string {
  return path.join(app.getPath('userData'), 'session.enc')
}

export function buildSession(data: Omit<Session, 'expiresAt'>): Session {
  return { ...data, expiresAt: Date.now() + SESSION_DURATION_MS }
}

export function saveSession(session: Session): void {
  const json = JSON.stringify(session)
  if (safeStorage.isEncryptionAvailable()) {
    fs.writeFileSync(sessionFilePath(), safeStorage.encryptString(json))
  } else {
    fs.writeFileSync(sessionFilePath(), Buffer.from(json).toString('base64'))
  }
}

export function loadSession(): Session | null {
  try {
    const file = sessionFilePath()
    if (!fs.existsSync(file)) return null
    const raw = fs.readFileSync(file)
    let json: string
    if (safeStorage.isEncryptionAvailable()) {
      json = safeStorage.decryptString(raw)
    } else {
      json = Buffer.from(raw.toString(), 'base64').toString('utf-8')
    }
    const session: Session = JSON.parse(json)
    if (session.expiresAt < Date.now()) {
      clearSession()
      return null
    }
    return session
  } catch {
    return null
  }
}

export function clearSession(): void {
  try {
    const file = sessionFilePath()
    if (fs.existsSync(file)) fs.unlinkSync(file)
  } catch {
    // ignore
  }
}
