/**
 * SpeechTranscriber — wraps the Web Speech API (built into Chromium/Electron).
 * This is the primary, zero-cost transcription path for the user's microphone.
 * No API calls are made; recognition runs locally via the browser engine.
 */
export class SpeechTranscriber {
  private recognition: SpeechRecognition | null = null
  private active = false

  constructor(
    private readonly onFinal: (text: string) => void,
    private readonly onInterim: (text: string) => void,
    private readonly onStatusChange: (status: 'listening' | 'stopped' | 'unsupported') => void
  ) {}

  isSupported(): boolean {
    return !!(
      (window as unknown as { SpeechRecognition?: unknown }).SpeechRecognition ||
      (window as unknown as { webkitSpeechRecognition?: unknown }).webkitSpeechRecognition
    )
  }

  start(): void {
    if (!this.isSupported()) {
      this.onStatusChange('unsupported')
      return
    }

    const SR =
      (window as unknown as { SpeechRecognition: typeof SpeechRecognition }).SpeechRecognition ||
      (window as unknown as { webkitSpeechRecognition: typeof SpeechRecognition }).webkitSpeechRecognition

    this.active = true
    this._startRecognition(SR)
    this.onStatusChange('listening')
  }

  private _startRecognition(SR: typeof SpeechRecognition): void {
    if (!this.active) return

    const r = new SR()
    r.continuous = true
    r.interimResults = true
    r.lang = 'en-US'
    r.maxAlternatives = 1
    this.recognition = r

    r.onresult = (event: SpeechRecognitionEvent) => {
      for (let i = event.resultIndex; i < event.results.length; i++) {
        const result = event.results[i]
        const text = result[0].transcript.trim()
        if (result.isFinal) {
          if (text) this.onFinal(text)
        } else {
          this.onInterim(text)
        }
      }
    }

    r.onerror = (event: SpeechRecognitionErrorEvent) => {
      if (!this.active || event.error === 'aborted') return
      // Auto-restart on recoverable errors
      if (['network', 'service-not-allowed', 'audio-capture'].includes(event.error)) {
        setTimeout(() => this._startRecognition(SR), 1500)
      }
    }

    r.onend = () => {
      // Keep running as long as we're supposed to be active
      if (this.active) {
        setTimeout(() => this._startRecognition(SR), 200)
      }
    }

    r.start()
  }

  stop(): void {
    this.active = false
    if (this.recognition) {
      this.recognition.abort()
      this.recognition = null
    }
    this.onStatusChange('stopped')
  }
}
