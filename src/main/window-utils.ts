// Pure helpers for main-process window/capture logic.
// Intentionally free of any `electron` imports so they can be unit-tested
// in the (jsdom) Vitest environment without mocking Electron.

/**
 * Whether the overlay should be hidden from screen recording.
 * Defaults to `true` (undetectable) unless the user explicitly disabled it,
 * matching the stored `undetectable` setting. Used both at window creation
 * and after a screen-read temporarily drops content protection.
 */
export function isUndetectable(settings: { undetectable?: unknown } | null | undefined): boolean {
  return settings?.undetectable !== false
}

/**
 * Pick the primary screen source for capture, or `null` when none are
 * available (e.g. screen-recording permission was denied). Callers must
 * handle `null` rather than blindly indexing `sources[0]`.
 */
export function pickPrimaryScreenSource<T>(sources: readonly T[] | null | undefined): T | null {
  return sources && sources.length > 0 ? sources[0] : null
}
