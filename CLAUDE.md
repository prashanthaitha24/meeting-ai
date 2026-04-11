# Meeting AI — Claude Code Project Context

## What this project is
Electron 31 desktop app (macOS + Windows) — real-time AI assistant for meetings/interviews.
Floating overlay that transcribes audio, answers questions via Claude, stays invisible to screen recording.

**Website:** thavionai.com (GitHub Pages, docs/)
**Backend:** Next.js on Vercel (backend/)
**Support:** support@thavionai.com

## Stack
- **App:** Electron 31 + electron-vite + TypeScript + React 18 + Tailwind CSS
- **Auth:** Supabase (Google OAuth PKCE, Apple OAuth, email/password)
- **AI:** Anthropic Claude via backend SSE stream
- **Transcription:** OpenAI Whisper (audio chunks) + Web Speech API (live mic)
- **Billing:** Stripe — Monthly $9.99/mo, Yearly $49.99/yr
- **Monitoring:** Sentry + local file logging (~/.meeting-ai/app.log)
- **Packaging:** electron-builder → macOS DMG (arm64 + x64), Windows NSIS

## Key file paths
```
src/main/index.ts          — Electron main process, all IPC handlers
src/main/logger.ts         — File logging with PII redaction (UUIDs, emails, JWTs)
src/main/supabase-auth.ts  — OAuth popup + session handling
src/preload/index.ts       — Context bridge (window.api)
src/preload/index.d.ts     — Type definitions for window.api
src/renderer/src/App.tsx   — Main React shell, all modal state
src/renderer/src/components/
  AuthScreen.tsx            — Login/signup UI
  ConsentScreen.tsx         — First-launch GDPR consent (versioned key: consent_accepted_v1)
  UpgradeModal.tsx          — Plan toggle (monthly/yearly), Stripe checkout
  DeleteAccountModal.tsx    — GDPR erasure confirmation
  HistoryTab.tsx
  TranscriptPanel.tsx
backend/app/api/
  chat/route.ts             — Claude SSE stream
  transcribe/route.ts       — Whisper transcription
  usage/route.ts            — Daily limit check (3/day free)
  stripe/checkout/route.ts  — Creates Stripe session (plan: monthly|yearly)
  stripe/portal/route.ts    — Billing portal
  stripe/redirect/route.ts  — HTTPS bridge → meetingai:// deep link
  stripe/webhook/route.ts   — Subscription status sync
  account/delete/route.ts   — GDPR erasure (Stripe cancel → Supabase delete)
  account/export/route.ts   — GDPR portability (JSON download)
backend/lib/
  usage.ts                  — Daily reset logic (free_calls_reset_date column)
  auth.ts                   — verifyAuth() — JWT verification
  stripe.ts                 — Stripe client
  supabase.ts               — Supabase admin client
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

### Stripe plans
- Monthly: `STRIPE_PRICE_ID` env var
- Yearly: `STRIPE_YEARLY_PRICE_ID` env var
- Both must be set in `.env` (local) and Vercel environment variables

### Deep links
Custom scheme `meetingai://` — macOS: `open-url` event, Windows: `second-instance` argv.
Stripe checkout redirects via `/api/stripe/redirect?to=success|cancel` HTTPS bridge (Stripe rejects custom schemes).

### IPC pattern
All renderer→main calls go through `window.api.*` (context bridge).
Main handlers in `src/main/index.ts` using `ipcMain.handle()`.

### Usage limits
Free: 3 AI calls/day. Reset tracked by `free_calls_reset_date` column in Supabase `profiles` table.
Backend resets count when date changes (UTC).

### Log PII redaction
`logger.ts` redacts UUIDs (hashed), emails, JWT tokens before writing to file.
Console output is NOT redacted (dev use only).

## Supabase schema
```sql
profiles (
  id uuid references auth.users,
  email text, name text, avatar_url text,
  stripe_customer_id text,
  subscription_status text default 'free',
  free_calls_used int default 0,
  free_calls_reset_date date,
  created_at timestamptz
)
```

## Environment variables needed
**Root `.env`:**
```
SUPABASE_URL, SUPABASE_ANON_KEY, BACKEND_URL, SENTRY_DSN (optional)
```
**`backend/.env.local`:**
```
SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY,
ANTHROPIC_API_KEY, OPENAI_API_KEY,
STRIPE_SECRET_KEY, STRIPE_PRICE_ID, STRIPE_YEARLY_PRICE_ID, STRIPE_WEBHOOK_SECRET,
BACKEND_URL
```

## Testing
- Unit/component: Vitest + React Testing Library (`npm test`)
- E2E: Playwright with Electron (`npm run test:e2e`)
- Test files: `src/**/*.test.ts`, `src/**/*.test.tsx`, `e2e/**/*.spec.ts`
