"""
kotoba-native Python functions — etzhayyim platform.

This is the kotoba-native, RW-free, Murakumo-only port of `udf_server.py`.
These functions are called in-process from kotoba cells (no Arrow-Flight server).
"""
from __future__ import annotations

import hashlib
import json
import os
import urllib.request

import numpy as np


def gmm_fit(features: list[float], k: int) -> str:
    """Fit a single data point against a GMM with k components.

    Batch-fit use case belongs application-side; this UDF is a deterministic
    single-row assignment (cluster 0 with probability 1.0) so the signature
    is usable in MVs. TODO: promote to gmm_batch_fit UDTF.
    """
    if not features or k < 1:
        return json.dumps({"cluster_id": -1, "probabilities": []})
    arr = np.asarray(features, dtype=np.float64)
    if arr.size < 1:
        return json.dumps({"cluster_id": 0, "probabilities": [1.0]})
    return json.dumps({
        "cluster_id": 0,
        "probabilities": [1.0] + [0.0] * (k - 1),
    })


def cosine_similarity(a: list[float], b: list[float]) -> float:
    """Cosine similarity between two feature vectors.

    For list<float> vector-vector similarity on RW-native columns, prefer
    built-in `list_cosine_similarity`; this UDF exists for JSONB-decoded or
    dynamically-shaped inputs.
    """
    if not a or not b or len(a) != len(b):
        return 0.0
    va = np.asarray(a, dtype=np.float64)
    vb = np.asarray(b, dtype=np.float64)
    na = np.linalg.norm(va)
    nb = np.linalg.norm(vb)
    if na == 0.0 or nb == 0.0:
        return 0.0
    return float(np.dot(va, vb) / (na * nb))


def posterior_update(prior: float, likelihood: float) -> float:
    """Bayesian single-step posterior update: P(H|E) = P(E|H)·P(H) / P(E)."""
    if prior is None:
        return 0.5 if likelihood is None else float(likelihood)
    if likelihood is None:
        return float(prior)
    p = max(0.0, min(1.0, float(prior)))
    l = max(0.0, min(1.0, float(likelihood)))
    evidence = l * p + (1.0 - l) * (1.0 - p)
    if evidence <= 0.0:
        return p
    return (l * p) / evidence


def news_source_credibility(source_type: str | None, primary: bool | None, official: bool | None) -> float:
    """Deterministic provenance score for news.etzhayyim.com intel briefs.

    This is intentionally model-free so scoring remains stable inside
    materialized views and Zeebe process gates.
    """
    st = (source_type or "unknown").lower()
    score = 0.45
    if primary:
        score += 0.25
    if official:
        score += 0.20
    if st in {"regulator", "official", "standards-body", "statistics", "clinical-registry"}:
        score += 0.10
    if st in {"rss", "platform"}:
        score -= 0.05
    return float(max(0.0, min(1.0, round(score, 3))))


def topology_dependency_hint(
    edge_table: str | None,
    src_vid: str | None,
    dst_vid: str | None,
    label: str | None,
) -> str:
    """Deterministic dependency hint for graph topology scans.

    Direction contract in the return JSON:
      - src_depends_on_dst: src_vid depends on dst_vid
      - dst_depends_on_src: dst_vid depends on src_vid
      - topology_only: relationship is useful topology but not a dependency
    """
    _ = src_vid, dst_vid
    text = f"{edge_table or ''} {label or ''}".lower()
    if "depends_on" in text or "dependency" in text:
        out = {"isDependency": True, "direction": "src_depends_on_dst", "confidence": 0.95, "reason": "explicit dependency relation"}
    elif "requires" in text or "_uses_" in text or text.endswith("_uses") or "uses_" in text:
        out = {"isDependency": True, "direction": "src_depends_on_dst", "confidence": 0.88, "reason": "requires/uses relation"}
    elif "consumes" in text or "input" in text:
        out = {"isDependency": True, "direction": "src_depends_on_dst", "confidence": 0.80, "reason": "consumer depends on consumed/input vertex"}
    elif "produces" in text or "emits" in text or "generates" in text or "enables" in text:
        out = {"isDependency": True, "direction": "dst_depends_on_src", "confidence": 0.72, "reason": "output/enabled vertex depends on producer/enabler"}
    elif "parent" in text or "contains" in text or "member" in text or "part_of" in text:
        out = {"isDependency": False, "direction": "topology_only", "confidence": 0.35, "reason": "containment/topology relation, not execution dependency"}
    else:
        out = {"isDependency": False, "direction": "unknown", "confidence": 0.25, "reason": "no dependency keyword"}
    return json.dumps(out, sort_keys=True, separators=(",", ":"))


def news_intel_priority(
    evidence_count: int | None,
    official_count: int | None,
    corroborated_count: int | None,
    recency_hours: float | None,
    impact: float | None,
) -> float:
    """Priority score for turning source evidence into an intel dispatch."""
    evidence = max(0, int(evidence_count or 0))
    official = max(0, int(official_count or 0))
    corroborated = max(0, int(corroborated_count or 0))
    hours = max(0.0, float(recency_hours or 0.0))
    imp = max(0.0, min(1.0, float(impact or 0.0)))
    freshness = max(0.0, 1.0 - hours / 168.0)
    score = (
        0.22 * min(1.0, evidence / 5.0)
        + 0.24 * min(1.0, official / 2.0)
        + 0.18 * min(1.0, corroborated / 3.0)
        + 0.16 * freshness
        + 0.20 * imp
    )
    return float(max(0.0, min(1.0, round(score, 3))))


def segment_hash(features_json) -> str:
    """Deterministic sha256 prefix for k-anonymity grouping.

    Identical feature dicts produce identical hashes (JSON keys sorted).
    Returns empty string on invalid input so callers can filter.

    Note: arrow_udf decodes JSONB to native Python dict/list before eval,
    but some clients pass varchar JSON strings. Accept both.
    """
    if features_json is None or features_json == "":
        return ""
    try:
        obj = (
            json.loads(features_json)
            if isinstance(features_json, (str, bytes, bytearray))
            else features_json
        )
        canonical = json.dumps(obj, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:32]
    except (json.JSONDecodeError, TypeError):
        return ""


# ADR-2605215000: Murakumo loopback only
_LLM_URL = os.environ.get("LLM_URL", "http://127.0.0.1:4000/v1/chat/completions")
_LLM_MODEL = os.environ.get("LLM_MODEL", "gemma4:e4b")
_LLM_TIMEOUT_SEC = float(os.environ.get("LLM_TIMEOUT_SEC", "8"))
_T3_IO_THREADS = int(os.environ.get("T3_IO_THREADS", "50"))

_T3_SYSTEM_PROMPT = (
    "You are a BEC/phishing classifier for gray-zone email. "
    "Reply ONLY valid JSON with keys: "
    "label (FraudSignal|IntelExtraction|null), confidence (0..1), reason (short string)."
)


def _call_llm(subject: str | None, from_addr: str | None, body_preview: str | None) -> str:
    content = (
        f"Subject: {subject or ''}\n"
        f"From: {from_addr or ''}\n"
        f"Body: {body_preview or ''}"
    )
    payload = {
        "model": _LLM_MODEL,
        "messages": [
            {"role": "system", "content": _T3_SYSTEM_PROMPT},
            {"role": "user", "content": content},
        ],
        "stream": False,
        "options": {"num_predict": 64, "temperature": 0.1},
    }
    req = urllib.request.Request(
        _LLM_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=_LLM_TIMEOUT_SEC) as res:
            raw = res.read().decode("utf-8", errors="ignore")
        obj = json.loads(raw)
        text = obj["choices"][0]["message"]["content"]
        try:
            parsed = json.loads(text)
        except Exception:
            parsed = {"label": None, "confidence": 0.0, "reason": "llm-non-json"}
        return json.dumps(parsed)
    except Exception as e:
        return json.dumps({
            "label": None,
            "confidence": 0.0,
            "reason": f"error:{type(e).__name__}",
        })


def classify_t3(subject: str | None, from_addr: str | None, body_preview: str | None) -> str:
    """yabai T3 (LLM gray-zone) classifier — ADR-0032.

    Input: email row (subject, from_addr, body_preview).
    Output: JSON varchar {"label","confidence","reason"}.
    """
    return _call_llm(subject, from_addr, body_preview)


if __name__ == "__main__":
    # PURE functions self-test (no network, no arrow_udf, no RW)
    assert abs(cosine_similarity([1.0, 0.0], [1.0, 0.0]) - 1.0) < 1e-6
    assert abs(cosine_similarity([1.0, 0.0], [0.0, 1.0]) - 0.0) < 1e-6

    assert 0.0 <= posterior_update(0.5, 0.8) <= 1.0

    h1 = segment_hash({"a": 1, "b": 2})
    h2 = segment_hash({"b": 2, "a": 1})
    assert h1 == h2 and len(h1) == 32

    assert 0.0 <= news_source_credibility("regulator", True, True) <= 1.0
    assert 0.0 <= news_intel_priority(5, 2, 3, 0.0, 1.0) <= 1.0

    hint = json.loads(topology_dependency_hint("edge", "v1", "v2", "depends_on"))
    assert hint["isDependency"] is True

    gmm = json.loads(gmm_fit([1.0, 2.0], 3))
    assert gmm["cluster_id"] == 0 and len(gmm["probabilities"]) == 3

    print("OK")
