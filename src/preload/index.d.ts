import { ElectronAPI } from '@electron-toolkit/preload'

export interface Session {
  userId: string
  email: string
  name: string | null
  avatarUrl: string | null
  provider: 'google' | 'email'
  expiresAt: number
}

interface MeetingAPI {
  // Auth
  checkSession(): Promise<Session | null>
  emailSignIn(email: string, password: string): Promise<Session>
  emailSignUp(email: string, password: string, name: string): Promise<Session>
  googleSignIn(): Promise<Session>
  logout(): Promise<boolean>

  // Audio
  getDesktopSources(): Promise<Array<{ id: string; name: string }>>
  transcribeAudio(audioData: ArrayBuffer): Promise<string>

  // Chat
  chatWithClaude(
    messages: Array<{ role: string; content: string }>,
    transcript: string
  ): Promise<boolean>
  onChatChunk(callback: (chunk: { text: string; done: boolean }) => void): () => void

  // Window
  readScreen(transcript: string): Promise<boolean>
  onTriggerScreenRead(callback: () => void): () => void
  hideWindow(): void
  closeWindow(): void
  setWindowHeight(height: number): void

  // Utilities
  openExternal(url: string): Promise<void>
  saveNotes(content: string): Promise<boolean>
}

declare global {
  interface Window {
    electron: ElectronAPI
    api: MeetingAPI
  }
}
