// Cloudflare Pages Function — single-tenant favorites store backed by KV.
// Route: /api/favorites
// Requires a KV namespace bound as FAVORITES_KV (see README for setup steps).
// Single-tenant by design (no auth): the whole store is one JSON object keyed
// by a fixed KV key, since this app has exactly one user.

const KEY = "favorites";
const MAX_BYTES = 500000; // 500KB safety cap, favorites are tiny in practice

export async function onRequestGet({ env }) {
  const raw = await env.FAVORITES_KV.get(KEY);
  return new Response(raw || "{}", {
    headers: {
      "content-type": "application/json; charset=utf-8",
      "cache-control": "no-store",
    },
  });
}

async function save(request, env) {
  const body = await request.text();
  if (body.length > MAX_BYTES) {
    return new Response(JSON.stringify({ error: "payload too large" }), {
      status: 413,
      headers: { "content-type": "application/json; charset=utf-8" },
    });
  }
  let parsed;
  try {
    parsed = JSON.parse(body);
  } catch {
    return new Response(JSON.stringify({ error: "invalid json" }), {
      status: 400,
      headers: { "content-type": "application/json; charset=utf-8" },
    });
  }
  if (typeof parsed !== "object" || parsed === null || Array.isArray(parsed)) {
    return new Response(JSON.stringify({ error: "expected a JSON object" }), {
      status: 400,
      headers: { "content-type": "application/json; charset=utf-8" },
    });
  }
  await env.FAVORITES_KV.put(KEY, body);
  return new Response(JSON.stringify({ ok: true }), {
    headers: { "content-type": "application/json; charset=utf-8" },
  });
}

export const onRequestPut = ({ request, env }) => save(request, env);
export const onRequestPost = ({ request, env }) => save(request, env);
