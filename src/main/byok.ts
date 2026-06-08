// Bring-Your-Own-Key storage. The user's API key is encrypted with Electron
// safeStorage (backed by the OS keychain) and written to userData/byok.json.
// The raw key never leaves the main process — the renderer only ever learns
// which provider is configured and whether a key is present.

import { app, safeStorage } from 'electron'
import * as fs from 'fs'
import * as path from 'path'
import { PROVIDERS, type ProviderId } from '../shared/providers'

interface StoredByok {
  providerId: ProviderId
  model?: string
  key: string // base64 of safeStorage-encrypted bytes
}

function file(): string {
  return path.join(app.getPath('userData'), 'byok.json')
}

function read(): StoredByok | null {
  try {
    const raw = JSON.parse(fs.readFileSync(file(), 'utf8')) as StoredByok
    if (!raw?.providerId || !PROVIDERS[raw.providerId]) return null
    return raw
  } catch {
    return null
  }
}

/** Public status for the renderer — never includes the key itself. */
export function byokStatus(): { providerId: ProviderId; model: string; hasKey: boolean } | null {
  const raw = read()
  if (!raw) return null
  return {
    providerId: raw.providerId,
    model: raw.model || PROVIDERS[raw.providerId].defaultModel,
    hasKey: !!raw.key,
  }
}

/** Main-process only — returns the decrypted key for making provider calls. */
export function byokCredentials(): { providerId: ProviderId; model: string; key: string } | null {
  const raw = read()
  if (!raw?.key) return null
  try {
    const bytes = Buffer.from(raw.key, 'base64')
    const key = safeStorage.isEncryptionAvailable()
      ? safeStorage.decryptString(bytes)
      : bytes.toString('utf8') // fallback if OS encryption unavailable
    return { providerId: raw.providerId, model: raw.model || PROVIDERS[raw.providerId].defaultModel, key }
  } catch {
    return null
  }
}

export function saveByok(providerId: ProviderId, model: string | undefined, key: string): void {
  const enc = safeStorage.isEncryptionAvailable()
    ? safeStorage.encryptString(key).toString('base64')
    : Buffer.from(key, 'utf8').toString('base64')
  const data: StoredByok = { providerId, model: model || PROVIDERS[providerId].defaultModel, key: enc }
  fs.writeFileSync(file(), JSON.stringify(data), 'utf8')
}

export function clearByok(): void {
  try {
    fs.rmSync(file())
  } catch {
    /* already gone */
  }
}
