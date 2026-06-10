import { ElectronAPI } from '@electron-toolkit/preload'

export interface Session {
  userId: string
  email: string
  name: string | null
  avatarUrl: string | null
  provider: 'google' | 'email'
  expiresAt: number
}

export interface HistoryEntry {
  id: string
  question: string
  answer: string
}

export interface HistorySession {
  id: string
  date: string
  transcript: string
  entries: HistoryEntry[]
  tabContent: { say: string; followup: string; recap: string }
}

interface MeetingAPI {
  getDesktopSources(): Promise<Array<{ id: string; name: string }>>
  transcribeAudio(audioData: ArrayBuffer): Promise<string>

  chatWithClaude(messages: Array<{ role: string; content: string }>, transcript: string): Promise<boolean>
  onChatChunk(callback: (chunk: { text: string; done: boolean }) => void): () => void

  readScreen(transcript: string): Promise<boolean>
  onTriggerScreenRead(callback: () => void): () => void
  onToggleCollapse(callback: () => void): () => void

  hideWindow(): void
  closeWindow(): void
  setWindowHeight(height: number): void
  setWindowSize(width: number, height: number): void

  openExternal(url: string): Promise<void>
  saveNotes(payload: { format: 'pdf' | 'doc' | 'txt'; text: string; html: string; defaultName?: string }): Promise<boolean>
  emailNotes(payload: { html: string }): Promise<boolean>

  // BYOK — bring your own AI provider key
  byokGet(): Promise<{ providerId: string; model: string; hasKey: boolean } | null>
  byokSet(payload: { providerId: string; model?: string; key: string }): Promise<boolean>
  byokClear(): Promise<boolean>
  byokTest(payload: { providerId: string; model?: string; key: string }): Promise<{ ok: boolean; error?: string }>

  saveSession(userId: string, session: HistorySession): Promise<boolean>
  loadHistory(userId: string, days: number): Promise<HistorySession[]>
  clearHistory(userId: string): Promise<boolean>

  loadSettings(): Promise<Record<string, unknown>>
  saveSettings(settings: Record<string, unknown>): Promise<boolean>

  reportIssue(description: string): Promise<boolean>
  deleteAccount(): Promise<boolean>
  exportData(): Promise<boolean>
}

declare global {
  interface Window {
    electron: ElectronAPI
    api: MeetingAPI
  }
}
