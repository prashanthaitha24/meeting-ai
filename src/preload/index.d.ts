import { ElectronAPI } from '@electron-toolkit/preload'

export interface Session {
  userId: string
  email: string
  name: string | null
  avatarUrl: string | null
  provider: 'google' | 'email'
  expiresAt: number
}

export interface UsageInfo {
  subscriptionStatus: 'free' | 'active' | 'canceled' | 'past_due'
  freeCallsUsed: number
  freeLimit: number
  canMakeCall: boolean
}

interface MeetingAPI {
  checkSession(): Promise<Session | null>
  emailSignIn(email: string, password: string): Promise<Session>
  emailSignUp(email: string, password: string, name: string): Promise<Session>
  googleSignIn(): Promise<Session>
  logout(): Promise<boolean>

  getUsage(): Promise<UsageInfo | null>
  stripeCheckout(): Promise<void>
  stripePortal(): Promise<void>
  onUsageLimitReached(cb: (data: { upgradeUrl?: string }) => void): () => void
  onStripeSuccess(cb: () => void): () => void

  getDesktopSources(): Promise<Array<{ id: string; name: string }>>
  transcribeAudio(audioData: ArrayBuffer): Promise<string>

  chatWithClaude(messages: Array<{ role: string; content: string }>, transcript: string): Promise<boolean>
  onChatChunk(callback: (chunk: { text: string; done: boolean }) => void): () => void

  readScreen(transcript: string): Promise<boolean>
  onTriggerScreenRead(callback: () => void): () => void

  hideWindow(): void
  closeWindow(): void
  setWindowHeight(height: number): void
  setWindowSize(width: number, height: number): void

  openExternal(url: string): Promise<void>
  saveNotes(content: string): Promise<boolean>
}

declare global {
  interface Window {
    electron: ElectronAPI
    api: MeetingAPI
  }
}
