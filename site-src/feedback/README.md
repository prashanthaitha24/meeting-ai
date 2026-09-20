# Feedback form relay

`docs/feedback.html` posts to a Cloudflare Worker (`worker.js`) which stores every submission in the
private repo `prashanthaitha24/thavionai-feedback` as `feedback/<timestamp>-<page>-<id>.md` and opens a
GitHub Issue labelled `feedback`. Lesson pages link to the form with `?module=<id>&page=<path>` so
course feedback arrives tagged with the module.

## Deploy / update

```bash
cd site-src/feedback
npx wrangler login                          # once per machine
npx wrangler secret put GITHUB_TOKEN        # fine-grained PAT, thavionai-feedback repo only: Contents RW, Issues RW
npx wrangler secret put TURNSTILE_SECRET    # from Cloudflare Turnstile widget (optional but recommended)
npx wrangler deploy
```

The Worker URL (`https://thavionai-feedback.<account>.workers.dev/submit`) and the Turnstile site key are set at the
top of the script in `docs/feedback.html`.

## Abuse controls

Origin allow-list, honeypot field, Turnstile check when the secret is set, 5 submissions per IP per minute,
message length 10–4000 characters. Nothing is stored anywhere except the private repo.
