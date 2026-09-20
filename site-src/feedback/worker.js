/**
 * thavionai-feedback — Cloudflare Worker that relays the feedback form on thavionai.com
 * into the private GitHub repo `thavionai-feedback`: one Markdown file per submission
 * under feedback/, plus a GitHub Issue labelled "feedback" so it shows up in notifications.
 *
 * Secrets (wrangler secret put ...):  GITHUB_TOKEN  (fine-grained PAT: Contents + Issues, write)
 *                                     TURNSTILE_SECRET (optional; when unset, Turnstile is not checked)
 * Vars (wrangler.toml):               GITHUB_REPO, ALLOWED_ORIGINS, OPEN_ISSUE
 * Optional binding:                   RL (rate limiting), 5 submissions per IP per minute
 */

const LIMITS = { name: 80, email: 120, message: 4000, page: 200, module: 60 };

export default {
  async fetch(request, env) {
    const origin = request.headers.get("Origin") || "";
    const cors = corsHeaders(origin, env);

    if (request.method === "OPTIONS") return new Response(null, { status: 204, headers: cors });
    if (request.method !== "POST" || new URL(request.url).pathname !== "/submit") {
      return json({ ok: false, error: "not found" }, 404, cors);
    }
    if (!cors["Access-Control-Allow-Origin"]) return json({ ok: false, error: "origin not allowed" }, 403, cors);

    const ip = request.headers.get("CF-Connecting-IP") || "0.0.0.0";
    if (env.RL) {
      const { success } = await env.RL.limit({ key: ip });
      if (!success) return json({ ok: false, error: "too many submissions, try again in a minute" }, 429, cors);
    }

    let body;
    try { body = await request.json(); } catch { return json({ ok: false, error: "invalid JSON" }, 400, cors); }

    // Honeypot: real browsers leave this hidden field empty.
    if (body.website) return json({ ok: true }, 200, cors);

    const f = {};
    for (const [k, max] of Object.entries(LIMITS)) f[k] = String(body[k] ?? "").trim().slice(0, max);
    if (f.message.length < 10) return json({ ok: false, error: "message is too short" }, 400, cors);
    if (f.email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(f.email)) return json({ ok: false, error: "email looks invalid" }, 400, cors);
    if (!/^[\w./#?=&%-]*$/.test(f.page)) f.page = "";
    if (!/^[\w-]*$/.test(f.module)) f.module = "";

    if (env.TURNSTILE_SECRET) {
      const ok = await verifyTurnstile(env.TURNSTILE_SECRET, body.turnstile, ip);
      if (!ok) return json({ ok: false, error: "captcha failed, please retry" }, 400, cors);
    }

    const stamp = new Date().toISOString().replace(/\.\d{3}Z$/, "Z");
    const id = crypto.randomUUID().slice(0, 8);
    const slug = (f.module || f.page.replace(/^\//, "").replace(/\.html$/, "").replace(/[^\w-]+/g, "-") || "site").slice(0, 40);
    const path = `feedback/${stamp.replace(/:/g, "-")}-${slug}-${id}.md`;
    const ua = (request.headers.get("User-Agent") || "").slice(0, 160);

    const md = [
      "---",
      `date: ${stamp}`,
      `page: ${f.page || "-"}`,
      `module: ${f.module || "-"}`,
      `name: ${yamlStr(f.name || "-")}`,
      `email: ${f.email || "-"}`,
      `ua: ${yamlStr(ua)}`,
      "---",
      "",
      f.message,
      "",
    ].join("\n");

    const gh = githubClient(env.GITHUB_TOKEN, env.GITHUB_REPO);
    const put = await gh(`contents/${path}`, "PUT", {
      message: `feedback: ${slug} (${stamp})`,
      content: btoa(unescape(encodeURIComponent(md))),
    });
    if (!put.ok) return json({ ok: false, error: "could not store feedback" }, 502, cors);

    if (env.OPEN_ISSUE === "true") {
      const title = `${f.module || f.page || "site"}: ${f.message.slice(0, 60).replace(/\s+/g, " ")}${f.message.length > 60 ? "…" : ""}`;
      const who = f.name ? `${f.name}${f.email ? ` <${f.email}>` : ""}` : (f.email || "anonymous");
      await gh("issues", "POST", {
        title,
        labels: ["feedback"],
        body: `**From:** ${who}\n**Page:** ${f.page || "-"}\n**File:** \`${path}\`\n\n---\n\n${f.message}`,
      });
    }
    return json({ ok: true }, 200, cors);
  },
};

function corsHeaders(origin, env) {
  const allowed = (env.ALLOWED_ORIGINS || "").split(",").map((s) => s.trim()).filter(Boolean);
  const h = { "Access-Control-Allow-Methods": "POST, OPTIONS", "Access-Control-Allow-Headers": "Content-Type", "Vary": "Origin" };
  if (allowed.includes(origin)) h["Access-Control-Allow-Origin"] = origin;
  return h;
}

function json(obj, status, headers) {
  return new Response(JSON.stringify(obj), { status, headers: { ...headers, "Content-Type": "application/json" } });
}

function yamlStr(s) { return JSON.stringify(s); }

async function verifyTurnstile(secret, token, ip) {
  if (!token) return false;
  const r = await fetch("https://challenges.cloudflare.com/turnstile/v0/siteverify", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ secret, response: token, remoteip: ip }),
  });
  const data = await r.json().catch(() => ({}));
  return data.success === true;
}

function githubClient(token, repo) {
  return (path, method, body) =>
    fetch(`https://api.github.com/repos/${repo}/${path}`, {
      method,
      headers: {
        "Authorization": `Bearer ${token}`,
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "thavionai-feedback-worker",
        "Content-Type": "application/json",
      },
      body: JSON.stringify(body),
    });
}
