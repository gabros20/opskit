"""
rerank.py — stage-3 precision layer (ADR-006): a local cross-encoder that re-scores the top
fused candidates by true query↔document relevance. This is what fixes "generic attractor" notes
that rank high in stages 1–2 by broad similarity but aren't actually the best answer.

Pluggable + local-only, lightest backend first:
  1. fastembed TextCrossEncoder  — ONNX runtime, no torch (preferred; multilingual model picked)
  2. sentence-transformers CrossEncoder — if you'd rather use torch / bge-reranker-v2-m3
  3. passthrough — no reranker installed → stages 1–2 order is kept (graceful degrade)

Opt-in via OPS_RERANK=1. Model via OPS_RERANK_MODEL (else a multilingual default is auto-picked).
"""
from __future__ import annotations
import os

_encoder = None
_backend = None  # None=unloaded, "fastembed"/"sentence-transformers"=ready, "none"=unavailable

# Prefer multilingual rerankers (Hungarian/German matter) then strong English ones.
_PREF = [
    "jina-reranker-v2-base-multilingual",
    "bge-reranker-v2-m3",
    "bge-reranker-base",
    "ms-marco-MiniLM-L-12-v2",
    "ms-marco-MiniLM-L-6-v2",
]


def _pick(models: list[str]) -> str | None:
    for pref in _PREF:
        for m in models:
            if pref in m:
                return m
    return models[0] if models else None


def _load() -> None:
    global _encoder, _backend
    if _backend is not None:
        return
    want = os.environ.get("OPS_RERANK_MODEL", "")
    try:
        from fastembed.rerank.cross_encoder import TextCrossEncoder
        models = [m["model"] for m in TextCrossEncoder.list_supported_models()]
        model = want if want in models else _pick(models)
        _encoder = TextCrossEncoder(model_name=model)
        _backend = "fastembed"
        return
    except Exception:
        pass
    try:
        from sentence_transformers import CrossEncoder
        _encoder = CrossEncoder(want or "BAAI/bge-reranker-v2-m3")
        _backend = "sentence-transformers"
        return
    except Exception:
        pass
    _backend = "none"


def available() -> bool:
    _load()
    return _backend in ("fastembed", "sentence-transformers")


def backend() -> str:
    _load()
    return _backend or "none"


def rerank(query: str, docs: list[str]) -> list[float]:
    """Return a relevance score per doc (higher = better), aligned to `docs`."""
    _load()
    if not docs:
        return []
    if _backend == "fastembed":
        return [float(s) for s in _encoder.rerank(query, docs)]
    if _backend == "sentence-transformers":
        return [float(s) for s in _encoder.predict([(query, d) for d in docs])]
    return [0.0] * len(docs)  # passthrough: preserve incoming order
