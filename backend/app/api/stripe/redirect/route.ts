import { NextRequest } from 'next/server'

export const dynamic = 'force-dynamic'

// Stripe requires HTTPS success/cancel URLs.
// This endpoint acts as a bridge — Stripe lands here, then we
// redirect the browser to the meetingai:// deep link which Electron intercepts.
export async function GET(req: NextRequest) {
  const to = req.nextUrl.searchParams.get('to')
  const deepLink = to === 'cancel' ? 'meetingai://stripe/cancel' : 'meetingai://stripe/success'

  const html = `<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8" />
  <title>Redirecting…</title>
  <style>
    body { font-family: -apple-system, sans-serif; display: flex; align-items: center;
           justify-content: center; height: 100vh; margin: 0; background: #0a0a0f; color: #94a3b8; }
    p { font-size: 14px; }
  </style>
</head>
<body>
  <p>Returning to Meeting AI…</p>
  <script>
    window.location.href = '${deepLink}';
    // Fallback: close tab after 2s if deep link opens the app
    setTimeout(() => window.close(), 2000);
  </script>
</body>
</html>`

  return new Response(html, {
    status: 200,
    headers: { 'Content-Type': 'text/html' },
  })
}
