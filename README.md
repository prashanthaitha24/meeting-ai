# Meeting AI

A real-time AI assistant for meetings and interviews. Runs as a transparent floating overlay on macOS and Windows — listens, transcribes, and answers questions instantly while staying invisible to screen recording.

**Free and unlimited — bring your own AI key.** You connect your own provider key (OpenAI, Groq, Claude, or Gemini) and the app calls it directly from your machine. Your conversations and key never pass through our servers.

**Website:** [thavionai.com](https://thavionai.com) · **Support:** support@thavionai.com

---

## Features

- **Real-time transcription** — continuous mic transcription via Web Speech API (free, no API calls)
- **AI answers** — ask questions mid-meeting and get instant streamed answers from your chosen provider
- **Say This / Follow-up / Recap tabs** — generate talking points, follow-up questions, and meeting summaries
- **Screen reading** — capture and analyze anything on screen with `⌘↵`
- **Stealth mode** — invisible to screen recording and screenshots (`setContentProtection`)
- **Silence auto-stop** — after 5 min with no voice, prompts "still there?" and stops recording if ignored
- **On-device transcript trimming** — strips filler words and sends only the recent context window per question (lower cost, less data leaves the device)
- **Bring your own key** — choose **OpenAI, Groq, Claude, or Gemini** on first launch; requests go directly from your machine to your provider. Your key is encrypted on-device (OS keychain) and never uploaded
- **Always on top** — floats above full-screen apps and all workspaces
- **Session history** — last 90 days of meetings saved locally; captured whenever you save notes, email, or sign out, and searchable by question, answer, transcript, or recap
- **Save / share conversation** — export the conversation as a formatted Q&A document in **PDF, Word (.doc), or Text**, or email it as a PDF attachment
- **Report Issue** — one-click bug report with logs sent to support
- **Free & unlimited** — no subscription, no account; you only pay your own AI provider for what you use. Optional “buy me a coffee” tip if you'd like to support development

---

## Architecture

```
Microphone  ──► Web Speech API (Chromium built-in)       ──► Live transcript (free)
System audio ──► Groq Whisper (whisper-large-v3-turbo)   ──► Participant transcript

User question ──► your AI provider (direct, on-device)  ──► Streamed answer
Screen capture ──► your provider's vision model (direct)  ──► Streamed answer

Key     ──► stored encrypted on-device (Electron safeStorage / OS keychain)
Support ──► Stripe one-time "buy me a coffee" (optional)
Logs    ──► ~/.meeting-ai/app.log + Sentry (crash monitoring)
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Desktop app | Electron 31 + electron-vite + TypeScript |
| UI | React 18 + Tailwind CSS |
| Auth | Supabase (Google OAuth, Apple OAuth, email/password) |
| AI | Bring your own key — OpenAI / Groq / Claude / Gemini, called directly from the app (OpenAI-compatible) |
| Transcription | Web Speech API (mic) + optional provider Whisper |
| Support | Stripe one-time "buy me a coffee" (optional) |
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
│   │   ├── chat/           # Groq Llama 3.3 70B streaming
│   │   ├── screen/         # Groq Llama 4 Scout vision streaming
│   │   ├── transcribe/     # Groq Whisper transcription
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
# AI provider pool (round-robin + failover) — at least one key required:
GROQ_API_KEY=gsk_...
OPENAI_API_KEY=sk-...          # optional pool member
ANTHROPIC_API_KEY=sk-ant-...   # optional pool member (Claude via OpenAI-compat)
CEREBRAS_API_KEY=csk-...       # optional pool member
GEMINI_API_KEY=...             # optional pool member (Google)
TOGETHER_API_KEY=...           # optional pool member
XAI_API_KEY=xai-...            # optional pool member (Grok)
# optional per-provider model overrides: GROQ_MODEL, OPENAI_MODEL, CEREBRAS_MODEL, GEMINI_MODEL, ...
STRIPE_SECRET_KEY=sk_test_...
STRIPE_PRICE_ID=price_...
STRIPE_YEARLY_PRICE_ID=price_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_PAYMENT_LINK=https://...    # shown on usage-limit error
BACKEND_URL=http://localhost:3000  # or your Vercel URL
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
- `Meeting AI-1.0.4-arm64.dmg` — Apple Silicon (M1/M2/M3)
- `Meeting AI-1.0.4.dmg` — Intel

### Windows (run on Windows or via GitHub Actions)

```bash
npm run dist:win
```

Outputs to `dist/`:
- `Meeting.AI-Setup-1.0.4-x64.exe` — Windows 10/11

### Automated releases (recommended)

Push a git tag to trigger a full cross-platform build via GitHub Actions:

```bash
git tag v1.0.6 && git push --tags
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
| `⌘ Shift E` | Expand / collapse the overlay |

---

## Pricing & limits

Meeting AI is **free and unlimited**. There's no subscription and no usage cap from us — on first launch you choose an AI provider and paste **your own API key**, which is stored encrypted on-device and used to call the provider directly. Your only "limit" is whatever your provider's own plan allows.

An optional **“Buy me a coffee”** one-time tip (via Stripe) supports development — entirely voluntary.

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

## Testing on Mac (before every release)

### Prerequisites
- macOS 13+ (Ventura or later)
- Node 18+ installed
- All env files configured (see Local Development above)
- Backend running locally (`cd backend && npm run dev`)

### 1. Automated tests
```bash
npm run typecheck        # must be zero errors
npm test                 # 26 unit/component tests must pass
npm run test:e2e         # Playwright E2E against Electron
```

### 2. Build the DMG
```bash
npm run dist:mac
# Produces: dist/Meeting AI-X.Y.Z-arm64.dmg (Apple Silicon)
#           dist/Meeting AI-X.Y.Z.dmg        (Intel)
```

### 3. Manual smoke test checklist
Install the DMG and run through each item before tagging:

| # | Test | Expected |
|---|------|----------|
| 1 | Launch app cold (no prior session) | Consent screen appears |
| 2 | Accept consent, sign in with Google | Auth succeeds, main panel shows |
| 3 | Speak into mic | Live transcript populates in real time |
| 4 | Ask an AI question (free tier) | Streamed answer appears in panel |
| 5 | Ask 3 more questions | Usage limit screen shown on 4th |
| 6 | Press `⌘↵` (screen read) | Screenshot captured + AI answer streams |
| 7 | Press `⌘ Shift Space` | Panel hides/shows |
| 8 | Open Settings → upgrade flow | Stripe checkout opens in browser |
| 9 | Settings → Report Issue | No crash; logs sent |
| 10 | Settings → My Data → Export | JSON download works |
| 11 | Take a screenshot with another tool | App window is invisible in screenshot |
| 12 | Open Activity Monitor | App is listed as "Meeting AI" not "Electron" |

### 4. Notarization check (signed builds only)
```bash
spctl --assess --type exec "dist/mac-arm64/Meeting AI.app"
# Should print: "dist/mac-arm64/Meeting AI.app: accepted"
```

---

## Shipping to ThavionAI

### Step 1 — Bump version
Edit `package.json` and change `"version"`:
```bash
# e.g. 1.0.4 → 1.0.5
```
Update the DMG filenames in this README's Building section to match.

### Step 2 — Run all checks locally
```bash
npm run typecheck && npm test && npm run dist:mac
```
Install the DMG and run the smoke test checklist above.

### Step 3 — Commit and tag
```bash
git add package.json README.md
git commit -m "chore: release vX.Y.Z"
git tag vX.Y.Z
git push origin main --tags
```

### Step 4 — Monitor GitHub Actions
Go to `https://github.com/prashanthaitha24/meeting-ai/actions` — the `release.yml` workflow triggers on the tag push. It runs 4 jobs:
- `test` — typecheck + unit tests
- `build-mac` — arm64 + x64 DMGs (Developer ID, direct download)
- `build-mas` — Mac App Store `.pkg` (requires MAS secrets below)
- `build-win` — NSIS installer

All artifacts are attached to a GitHub Release automatically.

### Step 5 — Verify the release
1. Open `https://github.com/prashanthaitha24/meeting-ai/releases`
2. Confirm Mac DMGs, MAS `.pkg`, and Windows EXE are all attached
3. Download and install the arm64 DMG as a final sanity check
4. Update `thavionai.com` download links if needed (edit `docs/index.html`)
5. Upload the `.pkg` to App Store Connect (see Mac App Store submission section)

### Required GitHub secrets (CI)

| Secret | Used by | Description |
|---|---|---|
| `DOTENV` | all | Full contents of root `.env` |
| `MAC_CERT_P12` | build-mac | Base64-encoded Developer ID cert |
| `MAC_CERT_PASSWORD` | build-mac | Developer ID cert password |
| `MAS_CERT_P12` | build-mas | Base64-encoded Mac App Distribution cert |
| `MAS_CERT_PASSWORD` | build-mas | MAS cert password |
| `MAS_PROVISIONING_PROFILE` | build-mas | Base64-encoded `.provisionprofile` |
| `APPLE_ID` | build-mac, build-mas | Apple ID email |
| `APPLE_APP_PASSWORD` | build-mac, build-mas | App-specific password |
| `APPLE_TEAM_ID` | build-mac, build-mas | 10-character team ID |

---

## Mac App Store submission

The app is fully configured for MAS. Follow these steps once to get it listed.

### One-time account setup

1. Enroll in [Apple Developer Program](https://developer.apple.com/programs/) ($99/yr)
2. In [App Store Connect](https://appstoreconnect.apple.com), create a new macOS app:
   - Bundle ID: `com.meeting-ai`
   - Name: `Meeting AI`
   - Category: Productivity
3. In [Certificates, IDs & Profiles](https://developer.apple.com/account/resources/certificates/list):
   - Create a **Mac App Distribution** certificate
   - Create a **Mac Installer Distribution** certificate
   - Create a **Mac App Store** provisioning profile for bundle ID `com.meeting-ai`
   - Download the profile → save as `resources/MeetingAI.provisionprofile` locally and as the `MAS_PROVISIONING_PROFILE` secret (base64)

### Build MAS package locally

```bash
# Place your provisioning profile at resources/MeetingAI.provisionprofile first
npm run dist:mas
# Outputs: dist/Meeting AI-X.Y.Z.pkg
```

### Upload to App Store Connect

```bash
xcrun altool --upload-app \
  --type osx \
  --file "dist/Meeting AI-X.Y.Z.pkg" \
  --username "$APPLE_ID" \
  --password "$APPLE_APP_PASSWORD"
```

Or drag the `.pkg` into the [Transporter app](https://apps.apple.com/app/transporter/id1450874784).

### App Review notes (include these to avoid rejection)

Apple reviewers will see `setContentProtection` and `alwaysOnTop`. Add this to App Store Connect → App Review Information:

> This app is a real-time AI meeting assistant overlay. `setContentProtection` prevents the assistant panel from appearing in meeting participants' screen recordings — this is a privacy feature users control in Settings → Privacy. The always-on-top window is required for the overlay to remain visible above full-screen video call windows. A walkthrough video is available at thavionai.com.

---

## License

Private — © 2025 ThavionAI. All rights reserved.
