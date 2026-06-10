# Meeting AI — Claude Code Project Context

## What this project is
Electron 31 desktop app (macOS + Windows) — real-time AI assistant for meetings/interviews.
Floating overlay that transcribes audio, answers questions via Claude, stays invisible to screen recording.

**Website:** thavionai.com (GitHub Pages, docs/)
**Backend:** Next.js on Vercel (backend/) — **LEGACY, no longer used by the app.** AI/vision/transcription now run BYOK-direct; kept only for the optional Stripe "coffee" link.
**Support:** support@thavionai.com

## Stack
- **App:** Electron 31 + electron-vite + TypeScript + React 18 + Tailwind CSS
- **Auth:** None — login-less (Stage 4). Device-local identity in `localStorage` (`local_user_id`); no Supabase, no accounts.
- **AI (BYOK):** User brings their own key (OpenAI / Groq / Anthropic / Google), called **directly** from the main process — `src/main/ai-direct.ts` + `src/shared/providers.ts`. No backend, no founder key.
- **Transcription:** Web Speech API (live mic) + the user's own provider Whisper (`/audio/transcriptions`, OpenAI/Groq only; Anthropic/Google fall back to Web Speech).
- **Billing:** Free. Optional one-time Stripe "buy me a coffee" tip (no subscriptions).
- **Monitoring:** Sentry + local file logging (~/.meeting-ai/app.log)
- **Packaging:** electron-builder → macOS DMG (arm64 + x64), Windows NSIS

## Key file paths
```
src/main/index.ts          — Electron main process, all IPC handlers
src/main/ai-direct.ts      — BYOK direct calls: streamProviderChat/Screen, transcribeProviderAudio, testProviderKey
src/main/byok.ts           — Encrypted on-device key store (safeStorage)
src/shared/providers.ts    — BYOK provider registry (shared main+renderer)
src/main/logger.ts         — File logging with PII redaction (UUIDs, emails, JWTs)
src/preload/index.ts       — Context bridge (window.api)
src/preload/index.d.ts     — Type definitions for window.api
src/renderer/src/App.tsx   — Main React shell, all modal state; login-less gating (consent → BYOK setup → app)
src/renderer/src/components/
  ProviderSetup.tsx         — First-run BYOK onboarding (pick provider + validate key)
  ConsentScreen.tsx         — First-launch GDPR consent (versioned key: consent_accepted_v1)
  DeleteAccountModal.tsx    — "Erase my data" (local wipe: key + history)
  HistoryTab.tsx
  TranscriptPanel.tsx
backend/ (LEGACY — not called by the app; AI/transcription are BYOK-direct now)
  app/api/stripe/*          — Optional "buy me a coffee" checkout/webhook
docs/
  index.html                — Landing page (thavionai.com)
  privacy.html              — Privacy Policy (GDPR/CCPA compliant)
  terms.html                — Terms of Service
```

## Dev commands
```bash
npm run dev          # Electron + Vite HMR
npm run build        # Production build (out/)
npm run typecheck    # tsc --noEmit (both node + web tsconfigs)
npm run dist:mac     # macOS DMGs → dist/
npm run dist:win     # Windows NSIS → dist/
npm test             # Vitest unit tests
npm run test:e2e     # Playwright E2E (Electron)
cd backend && npm run dev   # Next.js backend on :3000
```

## Release process
```bash
git tag v1.x.x && git push origin v1.x.x
# GitHub Actions builds Mac DMGs + Windows EXE → GitHub Release automatically
```

## Critical patterns

### Consent versioning
`CONSENT_VERSION = '1'` in App.tsx. Key: `consent_accepted_v1`.
Bump version number to force all users (including existing) to re-accept after policy changes.

### BYOK (bring your own key) — the core AI model
On first launch (after consent) `ProviderSetup.tsx` asks the user to pick a
provider and paste their key. `byok:test` validates it; `byok:set` stores it
**encrypted** via `safeStorage` at `userData/byok.json`. The key is NEVER
returned to the renderer — `byok:get` returns only `{providerId, model, hasKey}`.
All AI runs main-side in `ai-direct.ts` (chat, vision, transcription) using the
decrypted key, direct to the provider. Add a provider by extending
`src/shared/providers.ts` (`PROVIDERS` / `PROVIDER_LIST`).

### Login-less identity
No accounts. `getLocalSession()` in App.tsx mints a stable device-local id
(`localStorage.local_user_id`) once a key is configured; history/settings key off
it. "Switch" in the header → `byok:clear` → back to `ProviderSetup`.

### Deep links
Custom scheme `meetingai://` — macOS: `open-url` event, Windows: `second-instance` argv.
Only `stripe/success|cancel` branches remain (coffee link). OAuth deep links removed.

### IPC pattern
All renderer→main calls go through `window.api.*` (context bridge).
Main handlers in `src/main/index.ts` using `ipcMain.handle()`.

### No usage limits
Fully free — there is no per-day cap and no usage tracking. The user's only limit
is their own provider plan.

### Log PII redaction
`logger.ts` redacts UUIDs (hashed), emails, JWT tokens before writing to file.
Console output is NOT redacted (dev use only).

## Environment variables needed
The **app needs no env vars** to run (login-less, BYOK). Optional root `.env`:
`SENTRY_DSN` (crash monitoring).

The legacy `backend/.env.local` is only for the optional Stripe coffee endpoints:
`STRIPE_SECRET_KEY, STRIPE_WEBHOOK_SECRET, STRIPE_PAYMENT_LINK`.

## Testing
- Unit/component: Vitest + React Testing Library (`npm test`)
- E2E: Playwright with Electron (`npm run test:e2e`)
- Test files: `src/**/*.test.ts`, `src/**/*.test.tsx`, `e2e/**/*.spec.ts`
