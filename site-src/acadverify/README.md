# AcadVerify — authentic certification for ThavionAI

Two site pages plus one tiny backend give ThavionAI **certificates you actually earn and
anyone can verify**:

- **`certify.html`** — a randomized, timed exam per track. Questions and grading live on
  the server, so the exam can't be gamed from the browser (no click-through completion).
- **issuer Worker** (`worker.js`) — serves the exam, grades it, and on a pass **signs** a
  certificate with an ECDSA P-256 private key.
- **`acadverify.html`** — pastes a certificate code and verifies its signature **in the
  browser** against the issuer's public key. Genuine, or forged, in a second. Editing a
  single character (name, score, track) breaks the signature.

The site is static (GitHub Pages), so only the **issuance/grading** needs a backend. The
Worker is stateless: the exam token is an HMAC-signed list of question ids, and the answer
key lives only in the bundled `bank.json`.

## Files

| File | What it is |
|---|---|
| `worker.js` | the Cloudflare Worker (exam + grade + sign) |
| `bank.json` | the exam question bank, generated from the course quizzes |
| `wrangler.toml` | Worker config |
| `keygen.mjs` | generates a fresh issuer keypair |

Regenerate the bank whenever lessons change:

```bash
python3 scripts/build_acadverify_bank.py
```

## Deploy (one-time)

You need the Cloudflare `wrangler` CLI and a (free) Cloudflare account — the same setup as
the feedback Worker.

```bash
cd site-src/acadverify
npm install -g wrangler          # if not already installed
wrangler login                   # opens the browser to authorize
```

**1. Generate the issuer keypair** (do this yourself so you hold the private key):

```bash
node keygen.mjs
```

Copy the two JWKs it prints.

**2. Put the PUBLIC key in the verifier page.** In `docs/acadverify.html` **and**
`site-src/site/acadverify.html`, replace the `PUBLIC_JWK` value with the PUBLIC_JWK printed
above (also update `PUBLIC_JWK` in `site-src/site/certify.html` if you add local preview).
Rebuild the site (`python3 scripts/build_site.py`) and push.

**3. Set the Worker secrets:**

```bash
wrangler secret put SIGNING_KEY     # paste the PRIVATE_JWK line
wrangler secret put EXAM_SECRET     # paste any long random string
```

**4. Deploy the Worker:**

```bash
wrangler deploy
```

Wrangler prints the Worker URL, e.g. `https://acadverify.<your-subdomain>.workers.dev`.

**5. Point the site at the Worker.** In `site-src/site/certify.html`, set:

```js
var WORKER_URL = "https://acadverify.<your-subdomain>.workers.dev";
```

Rebuild (`python3 scripts/build_site.py`) and push. The exam now runs end to end, and the
certificates it issues verify on `acadverify.html`.

## Notes

- The values shipped in the pages use a **demo** keypair so the verifier's "Try a sample"
  works out of the box. Once you swap in your production `PUBLIC_JWK`, the demo sample stops
  verifying (expected) and real issued certificates verify instead.
- Tighten `ALLOW_ORIGIN` in `wrangler.toml` to your domain so only your site can call the
  issuer.
- The private key only signs certificates — it moves no money. Still, keep it secret and
  rotate it (re-run `keygen.mjs`, update the page + secret) if it's ever exposed.
