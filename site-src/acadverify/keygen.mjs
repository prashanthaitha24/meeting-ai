// Generate a fresh ECDSA P-256 issuer keypair for AcadVerify.
//
//   node keygen.mjs
//
// - PUBLIC_JWK  -> paste into PUBLIC_JWK in docs/acadverify.html (and site-src copy)
// - PRIVATE_JWK -> set as the Worker secret SIGNING_KEY (never commit it)
//
// Run this once for production so you control the private key. The value the
// pages ship with is a DEMO key only; replace it before issuing real certificates.

const subtle = globalThis.crypto.subtle;

const kp = await subtle.generateKey({ name: "ECDSA", namedCurve: "P-256" }, true, ["sign", "verify"]);
const pub = await subtle.exportKey("jwk", kp.publicKey);
const priv = await subtle.exportKey("jwk", kp.privateKey);

// The pages only need these four public fields.
const publicJwk = { kty: pub.kty, crv: pub.crv, x: pub.x, y: pub.y };

console.log("\n--- PUBLIC_JWK (paste into acadverify.html) ---");
console.log(JSON.stringify(publicJwk));
console.log("\n--- PRIVATE_JWK (set as Worker secret SIGNING_KEY; keep secret) ---");
console.log(JSON.stringify(priv));
console.log("");
