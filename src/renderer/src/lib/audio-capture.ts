export type AudioCaptureStatus = 'idle' | 'initializing' | 'recording' | 'error'

export interface AudioCaptureOptions {
  /** Called with each recorded audio chunk (every chunkDuration ms) */
  onChunk: (blob: Blob) => void
  /** Duration of each chunk in ms. Default: 15000 */
  chunkDuration?: number
  /** Skip microphone capture (use when Web Speech API already handles mic) */
  skipMic?: boolean
}

export class AudioCapture {
  private micStream: MediaStream | null = null
  private systemStream: MediaStream | null = null
  private audioContext: AudioContext | null = null
  private mixedStream: MediaStream | null = null
  private mediaRecorder: MediaRecorder | null = null
  private chunks: Blob[] = []
  private chunkTimer: ReturnType<typeof setTimeout> | null = null
  private isRecording = false
  private onChunk: (blob: Blob) => void
  private chunkDuration: number
  private skipMic: boolean

  constructor({ onChunk, chunkDuration = 15000, skipMic = false }: AudioCaptureOptions) {
    this.onChunk = onChunk
    this.chunkDuration = chunkDuration
    this.skipMic = skipMic
  }

  /**
   * Initialize audio streams. Must be called before startRecording().
   * systemSourceId comes from desktopCapturer sources (via IPC).
   */
  async init(systemSourceId?: string): Promise<void> {
    this.audioContext = new AudioContext()
    const destination = this.audioContext.createMediaStreamDestination()
    let hasAnySource = false

    // Microphone (skip if Web Speech API is already handling it)
    if (!this.skipMic) try {
      this.micStream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          sampleRate: 16000,
        },
        video: false,
      })
      const micSource = this.audioContext.createMediaStreamSource(this.micStream)
      micSource.connect(destination)
      hasAnySource = true
    } catch (e) {
      console.warn('[AudioCapture] Microphone unavailable:', e)
    }

    // System audio via desktopCapturer source ID
    if (systemSourceId) {
      try {
        // chromeMediaSource requires video constraints too; we discard video tracks after
        const stream = await navigator.mediaDevices.getUserMedia({
          audio: {
            // @ts-ignore — Electron-specific constraint
            mandatory: {
              chromeMediaSource: 'desktop',
              chromeMediaSourceId: systemSourceId,
            },
          },
          video: {
            // @ts-ignore
            mandatory: {
              chromeMediaSource: 'desktop',
              chromeMediaSourceId: systemSourceId,
            },
          },
        })

        // Stop video tracks immediately — we only want audio
        stream.getVideoTracks().forEach((t) => t.stop())

        this.systemStream = new MediaStream(stream.getAudioTracks())
        const sysSource = this.audioContext.createMediaStreamSource(this.systemStream)
        sysSource.connect(destination)
        hasAnySource = true
      } catch (e) {
        console.warn('[AudioCapture] System audio unavailable:', e)
      }
    }

    if (!hasAnySource) {
      throw new Error('No audio sources available (mic and system audio both failed)')
    }

    this.mixedStream = destination.stream
  }

  startRecording(): void {
    if (!this.mixedStream || this.isRecording) return
    this.isRecording = true
    this.recordNextChunk()
  }

  private recordNextChunk(): void {
    if (!this.isRecording || !this.mixedStream) return

    this.chunks = []

    const mimeType = MediaRecorder.isTypeSupported('audio/webm;codecs=opus')
      ? 'audio/webm;codecs=opus'
      : 'audio/webm'

    this.mediaRecorder = new MediaRecorder(this.mixedStream, { mimeType })

    this.mediaRecorder.ondataavailable = (e) => {
      if (e.data.size > 0) this.chunks.push(e.data)
    }

    this.mediaRecorder.onstop = () => {
      if (this.chunks.length > 0) {
        const blob = new Blob(this.chunks, { type: 'audio/webm' })
        this.onChunk(blob)
      }
      // Chain next chunk if still recording
      if (this.isRecording) {
        this.recordNextChunk()
      }
    }

    this.mediaRecorder.start()

    // Stop after chunkDuration to flush and send
    this.chunkTimer = setTimeout(() => {
      if (this.mediaRecorder?.state === 'recording') {
        this.mediaRecorder.stop()
      }
    }, this.chunkDuration)
  }

  stop(): void {
    this.isRecording = false
    if (this.chunkTimer) clearTimeout(this.chunkTimer)
    if (this.mediaRecorder?.state === 'recording') {
      this.mediaRecorder.stop()
    }
    this.micStream?.getTracks().forEach((t) => t.stop())
    this.systemStream?.getTracks().forEach((t) => t.stop())
    this.audioContext?.close()
    this.mixedStream = null
    this.micStream = null
    this.systemStream = null
  }

  get recording(): boolean {
    return this.isRecording
  }
}
