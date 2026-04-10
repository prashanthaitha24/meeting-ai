# Meeting AI

A real-time AI assistant for meetings and interviews. Runs as a transparent floating overlay on macOS and Windows — listens, transcribes, and answers questions instantly while staying invisible to screen recording.

**Website:** [thavionai.com](https://thavionai.com) · **Support:** support@thavionai.com

---

## Features

- **Real-time transcription** — continuous mic transcription via Web Speech API (free, no API calls)
- **AI answers** — ask questions mid-meeting and get instant answers via Claude
- **Say This / Follow-up / Recap tabs** — generate talking points, follow-up questions, and meeting summaries
- **Screen reading** — capture and analyze anything on screen with `⌘↵`
- **Stealth mode** — invisible to screen recording and screenshots (`setContentProtection`)
- **Always on top** — floats above full-screen apps and all workspaces
- **Session history** — last 90 days of meetings saved locally
- **Report Issue** — one-click bug report with logs sent to support
- **Free tier** — 3 AI responses per day; Pro ($9.99/mo) for unlimited

---

## Architecture

```
Microphone  ──► Web Speech API (Chromium built-in) ──► Live transcript (free)
System audio ──► Whisper API (chunked)              ──► Participant transcript

User question ──► Claude (via backend SSE stream) ──► Streamed answer
Screen capture ──► Backend vision API             ──► Streamed answer

Auth    ──► Supabase (Google OAuth PKCE / Apple OAuth / Email)
Billing ──► Stripe (subscription, webhooks)
Backend ──► Next.js on Vercel
Logs    ──► ~/.meeting-ai/app.log + Sentry (crash monitoring)
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Desktop app | Electron 31 + electron-vite + TypeScript |
| UI | React 18 + Tailwind CSS |
| Auth | Supabase (Google OAuth, Apple OAuth, email/password) |
| AI backend | Next.js (Vercel) — Claude via Anthropic API |
| Transcription | OpenAI Whisper (audio chunks) + Web Speech API (mic) |
| Billing | Stripe subscriptions + webhooks |
| Monitoring | Sentry + local file logging |
| Packaging | electron-builder (macOS DMG, Windows NSIS) |
| CI/CD | GitHub Actions — builds Mac + Windows on tag push |

---

## Project Structure

```
meeting-ai/
├── src/
│   ├── main/           # Electron main process
│   │   ├── index.ts    # App entry, IPCs, window management
│   │   ├── supabase-auth.ts  # OAuth + session handling
│   │   └── logger.ts   # File-based logging (PII-redacted)
│   ├── preload/        # Context bridge (renderer ↔ main)
│   └── renderer/       # React frontend
│       └── src/
│           ├── App.tsx              # Main shell, all modal state
│           └── components/
│               ├── AuthScreen.tsx
│               ├── ConsentScreen.tsx
│               ├── TranscriptPanel.tsx
│               ├── HistoryTab.tsx
│               └── UpgradeModal.tsx
├── backend/            # Next.js API (deployed to Vercel)
│   ├── app/api/
│   │   ├── chat/           # Claude streaming
│   │   ├── screen/         # Screen vision
│   │   ├── transcribe/     # Whisper
│   │   ├── usage/          # Daily limit tracking
│   │   ├── stripe/         # Checkout, portal, redirect, webhooks
│   │   └── account/        # GDPR delete + export endpoints
│   └── lib/
│       ├── usage.ts    # Daily reset logic
│       ├── stripe.ts
│       └── supabase.ts
├── docs/               # GitHub Pages (thavionai.com)
│   ├── index.html      # Landing page
│   ├── privacy.html    # Privacy Policy
│   └── terms.html      # Terms of Service
├── .github/workflows/
│   └── release.yml     # Cross-platform build on git tag
└── electron-builder.yml
```

---

## Local Development

### 1. Clone & install

```bash
git clone https://github.com/prashanthaitha24/meeting-ai.git
cd meeting-ai
npm install
```

### 2. Configure environment

Create `.env` in the project root:

```env
# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key

# Backend
BACKEND_URL=http://localhost:3000   # or your Vercel URL
```

For the backend, create `backend/.env.local`:

```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
STRIPE_SECRET_KEY=sk_test_...
STRIPE_PRICE_ID=price_...
STRIPE_WEBHOOK_SECRET=whsec_...
SENTRY_DSN=https://...@sentry.io/...   # optional
```

### 3. Run

```bash
# Terminal 1 — backend
cd backend && npm run dev

# Terminal 2 — Electron app
npm run dev
```

---

## Building

### macOS (run on macOS)

```bash
npm run dist:mac
```

Outputs to `dist/`:
- `Meeting AI-1.0.3-arm64.dmg` — Apple Silicon (M1/M2/M3)
- `Meeting AI-1.0.3.dmg` — Intel

### Windows (run on Windows or via GitHub Actions)

```bash
npm run dist:win
```

Outputs to `dist/`:
- `Meeting.AI-Setup-1.0.3-x64.exe` — Windows 10/11

### Automated releases (recommended)

Push a git tag to trigger a full cross-platform build via GitHub Actions:

```bash
git tag v1.0.3 && git push --tags
```

GitHub Actions builds Mac DMGs on `macos-latest` and the Windows installer on `windows-latest`, then attaches both to a GitHub Release automatically.

**Required GitHub secrets:**

| Secret | Description |
|---|---|
| `DOTENV` | Contents of your `.env` file |
| `MAC_CERT_P12` | Base64-encoded Developer ID certificate (once Apple account is active) |
| `MAC_CERT_PASSWORD` | Certificate export password |
| `APPLE_ID` | Your Apple ID email |
| `APPLE_APP_PASSWORD` | App-specific password from appleid.apple.com |
| `APPLE_TEAM_ID` | 10-character team ID from Apple Developer portal |

---

## Supabase Setup

Run these in Supabase → SQL Editor:

```sql
-- Profiles table
create table profiles (
  id uuid primary key references auth.users(id),
  email text,
  name text,
  avatar_url text,
  stripe_customer_id text,
  subscription_status text default 'free',
  free_calls_used int default 0,
  free_calls_reset_date date,   -- daily reset tracker
  created_at timestamptz default now()
);

-- Auto-create profile on signup
create or replace function handle_new_user()
returns trigger as $$
begin
  insert into profiles (id, email, name, avatar_url)
  values (
    new.id,
    new.email,
    new.raw_user_meta_data->>'full_name',
    new.raw_user_meta_data->>'avatar_url'
  );
  return new;
end;
$$ language plpgsql security definer;

create trigger on_auth_user_created
  after insert on auth.users
  for each row execute procedure handle_new_user();
```

---

## Keyboard Shortcuts

| Shortcut | Action |
|---|---|
| `⌘ Shift Space` | Toggle panel visibility |
| `⌘ ↵` | Read screen and analyze |

---

## Usage Limits

Free users get **3 AI responses per day** (resets at midnight UTC). Pro subscribers get unlimited responses at $9.99/month via Stripe.

---

## GDPR / CCPA Compliance

- **Consent screen** shown on first launch and re-shown whenever `CONSENT_VERSION` is bumped in `App.tsx` (version-stamped localStorage key — survives reinstalls correctly)
- **Data export** — Settings → My Data → Export: downloads account data as JSON
- **Account deletion** — Settings → My Data → Delete: cancels Stripe subscription, deletes Supabase profile + auth user, clears local history
- **Log PII redaction** — `logger.ts` redacts UUIDs, emails, and JWT tokens before writing to `app.log`
- **No meeting data on servers** — transcripts and session history are local-only

> To force all users to re-accept the consent screen (e.g. after a privacy policy update), increment `CONSENT_VERSION` in `src/renderer/src/App.tsx`.

---

## Monitoring & Logs

- **Local logs:** `~/.meeting-ai/app.log` — last 500 lines, auto-rotated
- **Sentry:** Set `SENTRY_DSN` in `.env` to enable automatic crash reporting
- **Report Issue:** Settings gear → Report — sends logs + system info to support@thavionai.com

---

## Auth Providers

| Provider | Status |
|---|---|
| Google OAuth | Supported (PKCE flow via Supabase) |
| Apple OAuth | Supported (PKCE flow via Supabase) |
| Email / Password | Supported |

Sessions are stored encrypted on-device via `safeStorage`. Cleared on app close.

---

## License

Private — © 2025 ThavionAI. All rights reserved.
