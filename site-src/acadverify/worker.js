// AcadVerify issuer Worker — serves randomized exams and issues signed certificates.
//
// It grades on the server (answers never leave here) and, on a pass, signs a
// certificate with an ECDSA P-256 private key. Anyone can verify the certificate
// client-side with the matching public key on acadverify.html.
//
// Secrets (set with `wrangler secret put`):
//   EXAM_SECRET  — any long random string; used to sign the stateless exam token.
//   SIGNING_KEY  — the issuer ECDSA P-256 PRIVATE key as a JWK string (from keygen).
// Optional var (wrangler.toml [vars]):
//   ALLOW_ORIGIN — the site origin allowed to call this, e.g. https://thavionai.com
//
// See README.md in this folder for full deploy steps.

import BANK from "./bank.json";

const EXAM_SIZE = 20;        // questions per exam
const PASS_PCT = 80;         // percent needed to pass
const SEC_PER_Q = 75;        // time budget per question
const TOKEN_TTL = 45 * 60;   // exam token valid for 45 minutes

const enc = new TextEncoder();
const dec = new TextDecoder();

function b64urlFromBytes(bytes) {
  let s = btoa(String.fromCharCode(...new Uint8Array(bytes)));
  return s.replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
}
function bytesFromB64url(s) {
  s = s.replace(/-/g, "+").replace(/_/g, "/");
  while (s.length % 4) s += "=";
  const bin = atob(s);
  const out = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i++) out[i] = bin.charCodeAt(i);
  return out;
}

function cors(env) {
  return {
    "Access-Control-Allow-Origin": (env && env.ALLOW_ORIGIN) || "*",
    "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
  };
}
function json(body, env, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json", ...cors(env) },
  });
}

async function hmacKey(secret) {
  return crypto.subtle.importKey("raw", enc.encode(secret), { name: "HMAC", hash: "SHA-256" }, false, ["sign", "verify"]);
}
async function signToken(payloadObj, secret) {
  const payload = b64urlFromBytes(enc.encode(JSON.stringify(payloadObj)));
  const key = await hmacKey(secret);
  const sig = await crypto.subtle.sign("HMAC", key, enc.encode(payload));
  return payload + "." + b64urlFromBytes(sig);
}
async function verifyToken(token, secret) {
  const [payload, sig] = String(token || "").split(".");
  if (!payload || !sig) return null;
  const key = await hmacKey(secret);
  const ok = await crypto.subtle.verify("HMAC", key, bytesFromB64url(sig), enc.encode(payload));
  if (!ok) return null;
  try { return JSON.parse(dec.decode(bytesFromB64url(payload))); } catch { return null; }
}

async function signCertificate(payloadObj, jwkString) {
  const jwk = JSON.parse(jwkString);
  const key = await crypto.subtle.importKey("jwk", jwk, { name: "ECDSA", namedCurve: "P-256" }, false, ["sign"]);
  const payloadStr = JSON.stringify(payloadObj);
  const sig = await crypto.subtle.sign({ name: "ECDSA", hash: "SHA-256" }, key, enc.encode(payloadStr));
  return b64urlFromBytes(enc.encode(payloadStr)) + "." + b64urlFromBytes(sig);
}

function randInt(n) {
  return Math.floor((crypto.getRandomValues(new Uint32Array(1))[0] / 2 ** 32) * n);
}
function pickIds(count, poolSize) {
  const ids = [...Array(poolSize).keys()];
  for (let i = ids.length - 1; i > 0; i--) { const j = randInt(i + 1); [ids[i], ids[j]] = [ids[j], ids[i]]; }
  return ids.slice(0, Math.min(count, poolSize));
}
function randomCertId(track) {
  const bytes = crypto.getRandomValues(new Uint8Array(4));
  const hex = [...bytes].map((b) => b.toString(16).padStart(2, "0")).join("");
  return "TVN-" + track.toUpperCase().slice(0, 4) + "-" + hex.toUpperCase();
}

async function handleExam(url, env) {
  const track = url.searchParams.get("track") || "";
  const t = BANK[track];
  if (!t) return json({ ok: false, error: "unknown track" }, env, 400);
  const ids = pickIds(EXAM_SIZE, t.questions.length);
  const token = await signToken({ track, ids, exp: Math.floor(Date.now() / 1000) + TOKEN_TTL }, env.EXAM_SECRET);
  const questions = ids.map((i) => ({ q: t.questions[i].q, options: t.questions[i].options }));
  return json({
    ok: true, track, trackName: t.name, count: questions.length,
    timeLimitSec: questions.length * SEC_PER_Q, passPct: PASS_PCT, token, questions,
  }, env);
}

async function handleGrade(request, env) {
  let body;
  try { body = await request.json(); } catch { return json({ ok: false, error: "bad body" }, env, 400); }
  const claim = await verifyToken(body.token, env.EXAM_SECRET);
  if (!claim) return json({ ok: false, error: "invalid or tampered exam token" }, env, 400);
  if (claim.exp < Math.floor(Date.now() / 1000)) return json({ ok: false, error: "exam expired" }, env, 400);
  const t = BANK[claim.track];
  if (!t) return json({ ok: false, error: "unknown track" }, env, 400);

  const answers = Array.isArray(body.answers) ? body.answers : [];
  let correct = 0;
  claim.ids.forEach((qid, i) => { if (answers[i] === t.questions[qid].answer) correct++; });
  const total = claim.ids.length;
  const pct = Math.round((correct / total) * 100);
  const passed = pct >= PASS_PCT;

  if (!passed) return json({ ok: true, passed: false, score: correct, total, pct }, env);

  const name = String(body.name || "").trim().slice(0, 60).replace(/[<>]/g, "") || "Anonymous";
  const date = new Date().toISOString().slice(0, 10);
  const certId = randomCertId(claim.track);
  const payload = {
    v: 1, name, track: claim.track, trackName: t.name,
    level: "Certified", score: pct, date, certId, issuer: "ThavionAI AcadVerify",
  };
  const certificate = await signCertificate(payload, env.SIGNING_KEY);
  return json({ ok: true, passed: true, score: correct, total, pct, certId, date, certificate }, env);
}

export default {
  async fetch(request, env) {
    if (request.method === "OPTIONS") return new Response(null, { headers: cors(env) });
    const url = new URL(request.url);
    try {
      if (url.pathname === "/exam" && request.method === "GET") return await handleExam(url, env);
      if (url.pathname === "/grade" && request.method === "POST") return await handleGrade(request, env);
      if (url.pathname === "/" ) return json({ ok: true, service: "AcadVerify issuer", tracks: Object.keys(BANK) }, env);
      return json({ ok: false, error: "not found" }, env, 404);
    } catch (e) {
      return json({ ok: false, error: "server error" }, env, 500);
    }
  },
};
