import '@testing-library/jest-dom'

// Mock window.api (Electron context bridge) so renderer tests work in jsdom
const mockApi = {
  checkSession: vi.fn().mockResolvedValue(null),
  emailSignIn: vi.fn(),
  emailSignUp: vi.fn(),
  googleSignIn: vi.fn(),
  appleSignIn: vi.fn(),
  logout: vi.fn().mockResolvedValue(true),
  getUsage: vi.fn().mockResolvedValue(null),
  stripeCheckout: vi.fn().mockResolvedValue(undefined),
  stripePortal: vi.fn().mockResolvedValue(undefined),
  onUsageLimitReached: vi.fn().mockReturnValue(() => {}),
  onStripeSuccess: vi.fn().mockReturnValue(() => {}),
  onStripeCancel: vi.fn().mockReturnValue(() => {}),
  getDesktopSources: vi.fn().mockResolvedValue([]),
  transcribeAudio: vi.fn().mockResolvedValue(''),
  chatWithClaude: vi.fn().mockResolvedValue(true),
  onChatChunk: vi.fn().mockReturnValue(() => {}),
  readScreen: vi.fn().mockResolvedValue(true),
  onTriggerScreenRead: vi.fn().mockReturnValue(() => {}),
  hideWindow: vi.fn(),
  closeWindow: vi.fn(),
  setWindowHeight: vi.fn(),
  setWindowSize: vi.fn(),
  openExternal: vi.fn().mockResolvedValue(undefined),
  saveNotes: vi.fn().mockResolvedValue(true),
  saveSession: vi.fn().mockResolvedValue(true),
  loadHistory: vi.fn().mockResolvedValue([]),
  clearHistory: vi.fn().mockResolvedValue(true),
  loadSettings: vi.fn().mockResolvedValue({}),
  saveSettings: vi.fn().mockResolvedValue(true),
  reportIssue: vi.fn().mockResolvedValue(true),
  deleteAccount: vi.fn().mockResolvedValue(true),
  exportData: vi.fn().mockResolvedValue(true),
}

Object.defineProperty(window, 'api', { value: mockApi, writable: true })
