# Meeting AI

A real-time AI meeting assistant for macOS. Captures audio from you and other participants, transcribes continuously, and lets you ask questions about the conversation — all in a transparent, collapsible overlay that stays out of your way.

## Features

- **Real-time transcription** — your microphone is transcribed instantly using the Web Speech API (free, built into the browser engine, no API calls)
- **System audio transcription** — other participants are transcribed via OpenAI Whisper every 30 seconds (cloud fallback only)
- **AI chat** — ask questions about the meeting; simple queries (summarize, action items) are answered locally before touching the API
- **Transparent overlay** — frosted-glass UI sits above all windows, invisible to screen-sharing (`setContentProtection`)
- **Collapsible** — click `^` to collapse to a 40 px strip; drag the header to reposition anywhere
- **Authentication** — Google OAuth (PKCE), email/password (local, bcrypt-hashed), Apple placeholder
- **24-hour sessions** — stored encrypted on-device via macOS `safeStorage`; you are prompted to re-login after expiry
- **Always-on-top** — visible above full-screen apps and on all spaces

## Architecture & cost optimisation

```
Microphone  ──► Web Speech API (Chromium built-in)  ──► Transcript (free, real-time)
System audio ──► AudioCapture → Whisper API (30 s)   ──► Transcript (cloud, minimised)

Chat question
  └─► Local keyword analysis (summarise / action items) ──► Answer (free)
  └─► GPT-4o streaming                                  ──► Answer (cloud, only if needed)
```

Cloud LLM is only called when local analysis is insufficient. Whisper chunks are every 30 s (vs. 15 s previously).

## Setup

### 1. Clone & install

```bash
git clone https://github.com/prashanthaitha24/meeting-ai.git
cd meeting-ai
npm install
```

### 2. Configure environment

```bash
cp .env.example .env
```

Edit `.env`:

```env
OPENAI_API_KEY=sk-...          # Required: Whisper + GPT-4o

# Optional — enables "Continue with Google":
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
```

#### Getting a Google OAuth client (optional)

1. Open [Google Cloud Console](https://console.cloud.google.com) → APIs & Services → Credentials
2. Create **OAuth 2.0 Client ID** → type: **Desktop app**
3. Add `http://localhost:43821/callback` as an authorised redirect URI
4. Copy the Client ID and Secret into `.env`

### 3. Run in development

```bash
npm run dev
```

### 4. Package as a macOS app

```bash
npm run dist:mac
```

DMGs are written to `dist/`:
- `Meeting AI-1.0.0-arm64.dmg` — Apple Silicon
- `Meeting AI-1.0.0.dmg` — Intel

> **Gatekeeper:** The app is not signed with an Apple Developer certificate. On first launch, right-click → Open.

## Keyboard shortcut

`⌘ Shift Space` — toggle panel visibility from anywhere.

## Auth notes

| Provider | Status | Storage |
|---|---|---|
| Email / Password | Fully supported | Encrypted locally via macOS `safeStorage` |
| Google | Fully supported (requires `.env` config) | Session token encrypted locally |
| Apple | UI present, disabled | Requires Apple Developer Program + entitlements |

Sessions expire after **24 hours**. The app checks every 5 minutes and shows the login screen when the session lapses.

## Tech stack

- **Electron 31** + **electron-vite** + **TypeScript**
- **React 18** + **Tailwind CSS**
- **OpenAI SDK** — Whisper (audio) + GPT-4o (chat)
- **Web Speech API** — primary mic transcription (no cost)
- **bcryptjs** — password hashing for local email auth
- **electron-builder** — macOS DMG packaging
