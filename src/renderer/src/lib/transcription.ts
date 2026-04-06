/**
 * Sends an audio blob to the main process, which transcribes it via Whisper.
 * Returns the transcribed text (empty string on error or silence).
 */
export async function transcribeBlob(blob: Blob): Promise<string> {
  try {
    const arrayBuffer = await blob.arrayBuffer()
    const text: string = await window.api.transcribeAudio(arrayBuffer)
    return typeof text === 'string' ? text.trim() : ''
  } catch (e) {
    console.error('[Transcription] Error:', e)
    return ''
  }
}
