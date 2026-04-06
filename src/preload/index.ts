import { contextBridge, ipcRenderer } from 'electron'
import { electronAPI } from '@electron-toolkit/preload'

const api = {
  // ── Auth ──────────────────────────────────────────────────────────────────
  checkSession: (): Promise<import('../main/session-store').Session | null> =>
    ipcRenderer.invoke('auth:check-session'),

  emailSignIn: (email: string, password: string) =>
    ipcRenderer.invoke('auth:email-signin', email, password) as Promise<import('../main/session-store').Session>,

  emailSignUp: (email: string, password: string, name: string) =>
    ipcRenderer.invoke('auth:email-signup', email, password, name) as Promise<import('../main/session-store').Session>,

  googleSignIn: () =>
    ipcRenderer.invoke('auth:google-signin') as Promise<import('../main/session-store').Session>,

  logout: () => ipcRenderer.invoke('auth:logout') as Promise<boolean>,

  // ── Audio / transcription ─────────────────────────────────────────────────
  getDesktopSources: (): Promise<Array<{ id: string; name: string }>> =>
    ipcRenderer.invoke('get-desktop-sources'),

  transcribeAudio: (audioData: ArrayBuffer): Promise<string> =>
    ipcRenderer.invoke('transcribe-audio', audioData),

  // ── Chat (GPT-4o, streams back via chat-chunk events) ────────────────────
  chatWithClaude: (
    messages: Array<{ role: string; content: string }>,
    transcript: string
  ): Promise<boolean> => ipcRenderer.invoke('chat-with-claude', messages, transcript),

  onChatChunk: (callback: (chunk: { text: string; done: boolean }) => void): (() => void) => {
    const handler = (_: Electron.IpcRendererEvent, chunk: { text: string; done: boolean }) =>
      callback(chunk)
    ipcRenderer.on('chat-chunk', handler)
    return () => ipcRenderer.removeListener('chat-chunk', handler)
  },

  // ── Window controls ───────────────────────────────────────────────────────
  hideWindow: (): void => ipcRenderer.send('hide-window'),
  closeWindow: (): void => ipcRenderer.send('close-window'),
  setWindowHeight: (height: number): void => ipcRenderer.send('set-window-height', height),
}

if (process.contextIsolated) {
  try {
    contextBridge.exposeInMainWorld('electron', electronAPI)
    contextBridge.exposeInMainWorld('api', api)
  } catch (e) {
    console.error(e)
  }
} else {
  // @ts-ignore
  window.electron = electronAPI
  // @ts-ignore
  window.api = api
}
