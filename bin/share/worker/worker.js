// ops share worker — a pastebin-worker (SharzyL/pastebin-worker semantics) for zero-knowledge shares.
// Stores an opaque blob (ciphertext, or --plain HTML) in KV with a TTL; serves it back; deletes it
// with the admin token. It NEVER sees the AES key — that rides the URL #fragment in the client and
// is decrypted in the browser. This is the ONLY off-machine component; `ops` publishes ciphertext,
// the human sends the link. ~100 lines, no dependencies.
//
// Routes:
//   PUT  /            body = blob, header X-Expire-Seconds = TTL -> { id, admin_token }
//   GET  /<id>        -> the blob (or the viewer HTML if Accept: text/html)
//   DELETE /<id>      header X-Admin-Token -> 204 (admin only)

const ID_ALPHABET = "abcdefghijklmnopqrstuvwxyz0123456789";

function randId(n = 10) {
  const buf = new Uint8Array(n);
  crypto.getRandomValues(buf);
  return Array.from(buf, (b) => ID_ALPHABET[b % ID_ALPHABET.length]).join("");
}

function json(obj, status = 200) {
  return new Response(JSON.stringify(obj), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const id = url.pathname.replace(/^\/+/, "");

    if (request.method === "PUT" && id === "") {
      const ttl = Math.max(60, parseInt(request.headers.get("X-Expire-Seconds") || "604800", 10));
      const body = await request.arrayBuffer();
      if (body.byteLength === 0) return json({ error: "empty body" }, 400);
      if (body.byteLength > 24 * 1024 * 1024) return json({ error: "too large" }, 413);
      const sid = randId();
      const admin = randId(24);
      await env.OPS_SHARE.put("blob:" + sid, body, { expirationTtl: ttl });
      await env.OPS_SHARE.put("admin:" + sid, admin, { expirationTtl: ttl });
      return json({ id: sid, admin_token: admin });
    }

    if (request.method === "GET" && id !== "") {
      const blob = await env.OPS_SHARE.get("blob:" + id, "arrayBuffer");
      if (!blob) return json({ error: "not found" }, 404);
      return new Response(blob, {
        headers: { "Content-Type": "application/octet-stream", "Cache-Control": "no-store" },
      });
    }

    if (request.method === "DELETE" && id !== "") {
      const admin = await env.OPS_SHARE.get("admin:" + id);
      if (!admin) return json({ error: "not found" }, 404);
      if (request.headers.get("X-Admin-Token") !== admin) return json({ error: "forbidden" }, 403);
      await env.OPS_SHARE.delete("blob:" + id);
      await env.OPS_SHARE.delete("admin:" + id);
      return new Response(null, { status: 204 });
    }

    return json({ error: "method not allowed" }, 405);
  },
};
