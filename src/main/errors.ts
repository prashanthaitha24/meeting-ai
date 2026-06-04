// Maps backend/network failures to short, user-facing messages so the UI never
// shows raw text like "HTTP 500" or "Error invoking remote method ...".
// Pure (no Electron imports) so it can be unit-tested.

/** Friendly message for a failed backend response, by HTTP status. */
export function friendlyHttpError(status: number, serverMessage?: string): string {
  if (status === 401 || status === 403) {
    return 'Your session has expired. Please sign out and sign in again.'
  }
  if (status === 429) {
    return 'The AI is handling a lot of requests right now. Please wait a few seconds and try again.'
  }
  if (status >= 500) {
    return 'The AI service is temporarily unavailable. Please try again in a moment.'
  }
  // 4xx other than the above: prefer a human-readable server message if present.
  if (serverMessage && /[a-z]\s[a-z]/i.test(serverMessage)) return serverMessage
  return 'Something went wrong. Please try again.'
}

/** Friendly message when the backend can't be reached at all (offline, DNS, timeout). */
export function friendlyNetworkError(): string {
  return "Couldn't reach the server. Check your internet connection and try again."
}
