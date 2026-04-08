import { contextBridge, ipcRenderer } from 'electron'
import { electronAPI } from '@electron-toolkit/preload'

const api = {
  // Auth
  checkSession: () => ipcRenderer.invoke('auth:check-session'),
  emailSignIn: (email: string, password: string) => ipcRenderer.invoke('auth:email-signin', email, password),
  emailSignUp: (email: string, password: string, name: string) => ipcRenderer.invoke('auth:email-signup', email, password, name),
  googleSignIn: () => ipcRenderer.invoke('auth:google-signin'),
  logout: () => ipcRenderer.invoke('auth:logout'),

  // Usage & subscription
  getUsage: () => ipcRenderer.invoke('get-usage'),
  stripeCheckout: () => ipcRenderer.invoke('stripe:checkout'),
  stripePortal: () => ipcRenderer.invoke('stripe:portal'),
  onUsageLimitReached: (cb: (data: { upgradeUrl?: string }) => void): (() => void) => {
    const handler = (_: Electron.IpcRendererEvent, data: { upgradeUrl?: string }) => cb(data)
    ipcRenderer.on('usage-limit-reached', handler)
    return () => ipcRenderer.removeListener('usage-limit-reached', handler)
  },
  onStripeSuccess: (cb: () => void): (() => void) => {
    const handler = () => cb()
    ipcRenderer.on('stripe-success', handler)
    return () => ipcRenderer.removeListener('stripe-success', handler)
  },

  // Audio
  getDesktopSources: () => ipcRenderer.invoke('get-desktop-sources'),
  transcribeAudio: (audioData: ArrayBuffer) => ipcRenderer.invoke('transcribe-audio', audioData),

  // Chat (streams back via chat-chunk events)
  chatWithClaude: (messages: Array<{ role: string; content: string }>, transcript: string) =>
    ipcRenderer.invoke('chat-with-claude', messages, transcript),
  onChatChunk: (callback: (chunk: { text: string; done: boolean }) => void): (() => void) => {
    const handler = (_: Electron.IpcRendererEvent, chunk: { text: string; done: boolean }) => callback(chunk)
    ipcRenderer.on('chat-chunk', handler)
    return () => ipcRenderer.removeListener('chat-chunk', handler)
  },

  // Screen read
  readScreen: (transcript: string) => ipcRenderer.invoke('read-screen', transcript),
  onTriggerScreenRead: (callback: () => void): (() => void) => {
    const handler = () => callback()
    ipcRenderer.on('trigger-screen-read', handler)
    return () => ipcRenderer.removeListener('trigger-screen-read', handler)
  },

  // Window controls
  hideWindow: (): void => ipcRenderer.send('hide-window'),
  closeWindow: (): void => ipcRenderer.send('close-window'),
  setWindowHeight: (height: number): void => ipcRenderer.send('set-window-height', height),
  setWindowSize: (width: number, height: number): void => ipcRenderer.send('set-window-size', width, height),

  // Utilities
  openExternal: (url: string) => ipcRenderer.invoke('open-external', url),
  saveNotes: (content: string) => ipcRenderer.invoke('save-notes', content),
}

if (process.contextIsolated) {
  try {
    contextBridge.exposeInMainWorld('electron', electronAPI)
    contextBridge.exposeInMainWorld('api', api)
  } catch (e) { console.error(e) }
} else {
  // @ts-ignore
  window.electron = electronAPI
  // @ts-ignore
  window.api = api
}
