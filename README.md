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
- **Session history** — last 90 days of meetings saved locally; captured whenever you save notes, email, or switch provider, and searchable by question, answer, transcript, or recap
- **Save / share conversation** — export the conversation as a formatted Q&A document in **PDF, Word (.doc), or Text**, or email it as a PDF attachment
- **Report Issue** — one-click bug report with logs sent to support
- **Free & unlimited** — no subscription, no account; you only pay your own AI provider for what you use. Optional “buy me a coffee” tip if you'd like to support development

---

## Architecture

```
Microphone  ──► Web Speech API (Chromium built-in)       ──► Live transcript (free)
Audio chunks ──► your provider's Whisper (OpenAI/Groq, direct) ──► Participant transcript

User question ──► your AI provider (direct, on-device)  ──► Streamed answer
Screen capture ──► your provider's vision model (direct)  ──► Streamed answer

No login   ──► device-local identity; history & settings stored on-device only
Key        ──► stored encrypted on-device (Electron safeStorage / OS keychain)
Support    ──► Stripe one-time "buy me a coffee" (optional)
Logs       ──► ~/.meeting-ai/app.log + Sentry (crash monitoring)
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Desktop app | Electron 31 + electron-vite + TypeScript |
| UI | React 18 + Tailwind CSS |
| Auth | None — login-less; a device-local identity, no account or server |
| AI | Bring your own key — OpenAI / Groq / Claude / Gemini, called directly from the app (OpenAI-compatible) |
| Transcription | Web Speech API (mic) + your provider's Whisper (OpenAI / Groq), direct |
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
│   │   ├── ai-direct.ts     # Direct BYOK calls (chat / vision / transcription)
│   │   ├── byok.ts          # Encrypted on-device key store (safeStorage)
│   │   └── logger.ts   # File-based logging (PII-redacted)
│   ├── shared/         # Code shared by main + renderer
│   │   └── providers.ts     # BYOK provider registry (OpenAI/Groq/Claude/Gemini)
│   ├── preload/        # Context bridge (renderer ↔ main)
│   └── renderer/       # React frontend
│       └── src/
│           ├── App.tsx              # Main shell, all modal state
│           └── components/
│               ├── ProviderSetup.tsx    # First-run: pick provider + enter key
│               ├── ConsentScreen.tsx
│               ├── TranscriptPanel.tsx
│               └── HistoryTab.tsx
├── backend/            # Next.js API — LEGACY, no longer used by the app.
│                       # AI, vision and transcription now run BYOK-direct.
│                       # Kept only for the optional Stripe "coffee" link / webhooks.
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

The app is **login-less and backend-free** — there's nothing to configure to run
it. You bring your own AI provider key in-app on first launch (stored encrypted
on-device). The only optional root `.env` value is crash monitoring:

```env
# Optional
SENTRY_DSN=your-sentry-dsn
```

> The `backend/` folder is legacy and no longer required by the app. You only
> need `backend/.env.local` if you're running the optional Stripe "buy me a
> coffee" endpoints:

```env
# Only for the optional "buy me a coffee" Stripe endpoints
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_PAYMENT_LINK=https://buy.stripe.com/...   # the coffee link
```

### 3. Run

```bash
npm run dev   # Electron app — no backend needed
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

## No backend or database

There is **no account system and no server-side data**. The app runs entirely
on-device: your meeting history and settings live in the app's local userData
folder, and your AI provider key is encrypted with the OS keychain
(`safeStorage`). Nothing is synced, and there is no Supabase/Postgres to set up.

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
- **Data export** — Settings → My Data → Export: saves all local meeting history to a JSON file
- **Erase my data** — Settings → My Data → Delete: wipes the stored API key and all local history, returning to the setup screen
- **Log PII redaction** — `logger.ts` redacts UUIDs, emails, and JWT tokens before writing to `app.log`
- **No data on servers** — there is no account; transcripts, history and your key never leave the device

> To force all users to re-accept the consent screen (e.g. after a privacy policy update), increment `CONSENT_VERSION` in `src/renderer/src/App.tsx`.

---

## Monitoring & Logs

- **Local logs:** `~/.meeting-ai/app.log` — last 500 lines, auto-rotated
- **Sentry:** Set `SENTRY_DSN` in `.env` to enable automatic crash reporting
- **Report Issue:** Settings gear → Report — sends logs + system info to support@thavionai.com

---

## AI Providers (bring your own key)

| Provider | Chat | Vision (screen) | Transcription |
|---|---|---|---|
| Groq | ✅ Llama 3.3 70B | ✅ Llama 4 Scout | ✅ Whisper v3 Turbo |
| OpenAI | ✅ GPT-5-series | ✅ | ✅ Whisper |
| Anthropic (Claude) | ✅ Haiku | ✅ | — (uses Web Speech) |
| Google Gemini | ✅ Flash | ✅ | — (uses Web Speech) |

You pick one on first launch and paste your own key — stored encrypted on-device
via `safeStorage`. Switch provider anytime from the panel header.

---

## Testing on Mac (before every release)

### Prerequisites
- macOS 13+ (Ventura or later)
- Node 18+ installed
- An AI provider API key to paste on first launch (no env/backend needed)

### 1. Automated tests
```bash
npm run typecheck        # must be zero errors
npm test                 # unit/component tests must pass
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
| 1 | Launch app cold (no prior setup) | Consent screen appears |
| 2 | Accept consent, pick a provider + paste key, Validate | Key validates, main panel shows |
| 3 | Speak into mic | Live transcript populates in real time |
| 4 | Ask an AI question | Streamed answer appears in panel |
| 5 | Ask several more questions | No limits — all answered |
| 6 | Press `⌘↵` (screen read) | Screenshot captured + AI answer streams |
| 7 | Press `⌘ Shift Space` | Panel hides/shows |
| 8 | Header → Switch | Returns to provider-setup screen |
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
