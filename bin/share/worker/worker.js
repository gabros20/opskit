// ops share worker — a pastebin-worker (SharzyL/pastebin-worker semantics) for zero-knowledge shares.
// Stores an opaque blob (ciphertext, or --plain HTML) in KV with a TTL; serves it back; deletes it
// with the admin token. It NEVER sees the AES key — that rides the URL #fragment in the client and
// is decrypted in the browser. This is the ONLY off-machine component; `ops` publishes ciphertext,
// the human sends the link. ~100 lines, no dependencies.
//
// Routes:
//   PUT  /            body = blob, header X-Expire-Seconds = TTL -> { id, admin_token }
//   GET  /<id>        browser (Accept: text/html) -> the viewer page; else -> the raw blob
//   GET  /<id>?raw=1  -> the raw blob (what the viewer fetches, then decrypts client-side)
//   DELETE /<id>      header X-Admin-Token -> 204 (admin only)

const ID_ALPHABET = "abcdefghijklmnopqrstuvwxyz0123456789";

// Self-contained decrypt viewer (no deps, no external refs). Served for browser navigations; it
// fetches the raw blob (?raw=1), decrypts with the AES key from the URL #fragment via Web Crypto —
// byte-compatible with bin/lib/sharelib.py encrypt(): blob = b64url(nonce[12] || ct || tag[16]),
// key = b64url(32). The decrypted note renders inside a scriptless sandboxed iframe, so it can never
// read the key, and the #fragment is stripped from the address bar after load.
const VIEWER = `<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta name="color-scheme" content="light dark">
<meta name="theme-color" media="(prefers-color-scheme:light)" content="#FFFCF0">
<meta name="theme-color" media="(prefers-color-scheme:dark)" content="#100F0F">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="default">
<title>ops share</title>
<style>:root{color-scheme:light dark;--bg:#FFFCF0;--mut:#6F6E69;--st:#100F0F;--cd:#F2F0E5}
@media (prefers-color-scheme:dark){:root{--bg:#100F0F;--mut:#878580;--st:#CECDC3;--cd:#1C1B1A}}
html,body{margin:0;height:100%;background:var(--bg)}
/* iOS 26 "Liquid Glass" ignores theme-color and samples fixed edge elements (must be 100%
   wide, >=6px tall). These inert 12px strips + the matching bg feed that sampler so the URL
   bar/status bar blend with the page. */
.cs{position:fixed;left:0;right:0;height:12px;background:var(--bg);pointer-events:none;z-index:0}
#f{position:fixed;inset:0;width:100%;height:100%;border:0;display:none;background:var(--bg);z-index:1}
#m{position:relative;z-index:2;font:16px/1.6 -apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;
color:var(--mut);max-width:34rem;margin:0 auto;padding:16vh 1.4rem;text-align:center}
#m b{color:var(--st)}#m code{background:var(--cd);padding:.1em .35em;border-radius:5px}</style></head>
<body><div class="cs" style="top:0" aria-hidden="true"></div>
<div class="cs" style="bottom:0" aria-hidden="true"></div>
<div id="m">Decrypting…</div><iframe id="f" sandbox referrerpolicy="no-referrer"></iframe>
<script>
function b64uDec(s){s=s.replace(/-/g,"+").replace(/_/g,"/");s+="=".repeat((4-s.length%4)%4);
var bin=atob(s),out=new Uint8Array(bin.length);for(var i=0;i<bin.length;i++)out[i]=bin.charCodeAt(i);return out;}
async function decrypt(b64,keyB64){var raw=b64uDec(b64),nonce=raw.slice(0,12),data=raw.slice(12);
var key=await crypto.subtle.importKey("raw",b64uDec(keyB64),{name:"AES-GCM"},false,["decrypt"]);
var pt=await crypto.subtle.decrypt({name:"AES-GCM",iv:nonce,tagLength:128},key,data);
return new TextDecoder().decode(pt);}
function msg(h){document.getElementById("m").innerHTML=h;}
function show(html){var f=document.getElementById("f");f.srcdoc=html;
document.getElementById("m").style.display="none";f.style.display="block";}
(async function(){try{
var key=location.hash.slice(1);
var res=await fetch(location.pathname+"?raw=1",{headers:{Accept:"application/octet-stream"}});
if(res.status===404)return msg("<b>This share has expired or was revoked.</b>");
if(!res.ok)return msg("<b>Could not load this share.</b><br>HTTP "+res.status+".");
var text=await res.text();var html;
if(key){html=await decrypt(text,key);}
else if(text.indexOf("<")>=0){html=text;}
else return msg("<b>This encrypted link is missing its key.</b><br>The <code>#…</code> part after the id was probably dropped when the link was forwarded — ask the sender for the full link.");
history.replaceState(null,"",location.pathname);
show(html);
}catch(e){msg("<b>Could not decrypt this share.</b><br>The key in the link may be wrong or truncated.");}})();
</script></body></html>`;

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
      const raw = url.searchParams.has("raw");
      const wantsHtml = (request.headers.get("Accept") || "").includes("text/html");
      // Browser navigation → the static viewer (no KV read; it surfaces 404/expiry via its own
      // ?raw=1 fetch). Everything else (the viewer's fetch, curl, programmatic) → the raw blob.
      if (wantsHtml && !raw) {
        return new Response(VIEWER, {
          headers: { "Content-Type": "text/html; charset=utf-8", "Cache-Control": "no-store" },
        });
      }
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
