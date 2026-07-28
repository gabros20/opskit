"""
retrieval.py — model the staged search of §10.2 and measure it, to answer one question with
data: does this system need vector embeddings (gbrain stage-2), or do FTS5 keyword + wikilink
graph cover it?

Three retrievers over the same corpus:
  1. keyword        — BM25 (the §10.2 stage-1 FTS5 stand-in).
  2. keyword+graph  — BM25 then one-hop wikilink expansion (the v3.7 "graph as stage-1" claim).
  3. semantic_proxy — character-trigram cosine. A CONSERVATIVE stand-in for embeddings: it
                      catches morphological/substring closeness but NOT true synonymy, so where
                      it beats keyword it marks a floor on what real vectors could recover.
                      (Plug a real embedder via PLAINKEEP_EMBED_CMD later to tighten the estimate.)

Auto-bucketing: a query is 'lexical' if it shares ≥1 stemmed content token with its relevant
note, else 'semantic'. Keyword search structurally cannot win the semantic bucket; that bucket's
size and the keyword miss-rate on it are the empirical basis for the vector decision.
"""
from __future__ import annotations
import json
import math
import os
import re
import subprocess
import urllib.request
from collections import Counter


# --- real local embedder (philosophy-compatible: offline, no server-of-record, file-cacheable) ---
def ollama_embed(text: str, model: str | None = None, host: str = "http://localhost:11434") -> list[float]:
    model = model or os.environ.get("PLAINKEEP_EMBED_MODEL", "mxbai-embed-large")
    req = urllib.request.Request(
        host + "/api/embeddings",
        data=json.dumps({"model": model, "prompt": text}).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read())["embedding"]


def cmd_embed(text: str) -> list[float]:
    """Generic escape hatch: PLAINKEEP_EMBED_CMD reads text on stdin, prints a JSON float array."""
    cmd = os.environ["PLAINKEEP_EMBED_CMD"]
    out = subprocess.run(cmd, shell=True, input=text, capture_output=True, text=True, timeout=120)
    return json.loads(out.stdout)


def get_embedder():
    """Return (name, fn) for the best available real embedder, or (None, None)."""
    if os.environ.get("PLAINKEEP_EMBED_CMD"):
        try:
            cmd_embed("ping")
            return ("PLAINKEEP_EMBED_CMD", cmd_embed)
        except Exception:
            pass
    try:
        ollama_embed("ping")
        return (f"ollama:{os.environ.get('PLAINKEEP_EMBED_MODEL', 'mxbai-embed-large')}", ollama_embed)
    except Exception:
        return (None, None)


def _cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    return dot / (na * nb + 1e-9)

STOP = set("a an the of for to with and or in on at is are be how who what our we work "
           "that this it its keep keeps not no into over up again been being as by from".split())


def _stem(w: str) -> str:
    w = w.lower()
    for suf in ("ing", "ed", "es", "s", "er", "ion", " "):
        if suf and len(w) > len(suf) + 2 and w.endswith(suf):
            return w[: -len(suf)]
    return w


def tokenize(text: str) -> list[str]:
    raw = re.findall(r"[a-z0-9]+", text.lower())
    return [_stem(w) for w in raw if w not in STOP and len(w) > 1]


def _text_of(note_text: str) -> str:
    # strip frontmatter fences/keys lightly; keep title/body/tags content
    return re.sub(r"---", " ", note_text)


class Index:
    def __init__(self, corpus_notes: dict, link_map: dict[str, list[str]]):
        self.keys = list(corpus_notes.keys())
        self.raw = {k: _text_of(v) for k, v in corpus_notes.items()}
        self.docs = {k: tokenize(v) for k, v in self.raw.items()}
        self.links = link_map
        self.N = len(self.keys)
        self.avgdl = sum(len(d) for d in self.docs.values()) / max(1, self.N)
        df: Counter = Counter()
        for d in self.docs.values():
            for t in set(d):
                df[t] += 1
        self.df = df

    # ---- BM25 ----
    def bm25(self, query: str, k1=1.5, b=0.75) -> list[tuple[str, float]]:
        q = tokenize(query)
        scores: dict[str, float] = {}
        for key in self.keys:
            d = self.docs[key]
            if not d:
                continue
            tf = Counter(d)
            s = 0.0
            for t in q:
                if t not in tf:
                    continue
                idf = math.log(1 + (self.N - self.df[t] + 0.5) / (self.df[t] + 0.5))
                denom = tf[t] + k1 * (1 - b + b * len(d) / self.avgdl)
                s += idf * (tf[t] * (k1 + 1)) / denom
            if s > 0:
                scores[key] = s
        return sorted(scores.items(), key=lambda x: -x[1])

    # ---- keyword + one-hop graph expansion ----
    def keyword_graph(self, query: str) -> list[tuple[str, float]]:
        base = dict(self.bm25(query))
        boosted = dict(base)
        for key, sc in base.items():
            for nbr in self.links.get(key, []):
                boosted[nbr] = max(boosted.get(nbr, 0.0), sc * 0.5)
        return sorted(boosted.items(), key=lambda x: -x[1])

    # ---- character-trigram cosine (conservative semantic proxy) ----
    @staticmethod
    def _trigrams(text: str) -> Counter:
        s = re.sub(r"\s+", " ", text.lower())
        return Counter(s[i:i + 3] for i in range(len(s) - 2))

    # ---- real vector retrieval (local embeddings) ----
    def build_vectors(self, embed_fn) -> None:
        self.vecs = {k: embed_fn(self.raw[k]) for k in self.keys}

    def vector(self, query: str, embed_fn) -> list[tuple[str, float]]:
        q = embed_fn(query)
        out = {k: _cosine(q, v) for k, v in self.vecs.items()}
        return sorted(out.items(), key=lambda x: -x[1])

    @staticmethod
    def _rrf(rankings: list[list[tuple[str, float]]], k: int = 60) -> list[tuple[str, float]]:
        scores: dict[str, float] = {}
        for ranking in rankings:
            for rank, (key, _) in enumerate(ranking, 1):
                scores[key] = scores.get(key, 0.0) + 1.0 / (k + rank)
        return sorted(scores.items(), key=lambda x: -x[1])

    def hybrid_rrf(self, query: str, embed_fn) -> list[tuple[str, float]]:
        """BM25 + vector fused with reciprocal-rank fusion (the §10.2 stage-2 hybrid)."""
        return self._rrf([self.bm25(query), self.vector(query, embed_fn)])

    def hybrid_graph_vec(self, query: str, embed_fn) -> list[tuple[str, float]]:
        """keyword + wikilink-graph + vector — the full local hybrid."""
        return self._rrf([self.keyword_graph(query), self.vector(query, embed_fn)])

    def semantic_proxy(self, query: str) -> list[tuple[str, float]]:
        qg = self._trigrams(query)
        qn = math.sqrt(sum(v * v for v in qg.values())) or 1.0
        out = {}
        for key in self.keys:
            dg = self._trigrams(self.raw[key])
            dn = math.sqrt(sum(v * v for v in dg.values())) or 1.0
            common = set(qg) & set(dg)
            dot = sum(qg[t] * dg[t] for t in common)
            sc = dot / (qn * dn)
            if sc > 0:
                out[key] = sc
        return sorted(out.items(), key=lambda x: -x[1])


def lexical_overlap(query: str, relevant_text: str) -> bool:
    return bool(set(tokenize(query)) & set(tokenize(relevant_text)))


def rank_of(results: list[tuple[str, float]], target: str) -> int | None:
    for i, (k, _) in enumerate(results, 1):
        if k == target:
            return i
    return None


def metrics(results: list[tuple[str, float]], target: str, ks=(1, 3, 5)) -> dict:
    r = rank_of(results, target)
    m = {f"recall@{k}": (1.0 if (r is not None and r <= k) else 0.0) for k in ks}
    m["rr"] = (1.0 / r) if r else 0.0
    m["rank"] = r
    return m
