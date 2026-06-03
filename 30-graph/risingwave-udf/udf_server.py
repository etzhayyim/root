"""
RisingWave External Python UDF server — etzhayyim platform.

ADR-0044 compliant (arrow_udf 0.3.1 + @udf(io_threads=N)).
Protocol: Arrow Flight gRPC (port 8815).
Deploy: see K8s manifest `deploy/risingwave-udf.yaml`.

Functions:
  cosine_similarity — feature vector cosine (pure CPU, io_threads=1)
  posterior_update  — Bayesian posterior step (pure CPU, io_threads=1)
  segment_hash      — sha256 hash for k-anonymity grouping (pure CPU, io_threads=1)
  topology_dependency_hint — deterministic edge-table dependency classifier
  gmm_fit           — GMM single-row assignment (pure CPU, io_threads=1)
  classify_t3       — yabai T3 phishing classifier via Murakumo LLM (IO-bound, io_threads=50)
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
import urllib.request

import numpy as np
from arrow_udf import UdfServer, udf


# ─────────────────────────────────────────────────────────
# Pure-CPU UDFs — io_threads=1 (no benefit from threading;
# pure numpy releases GIL during hot math anyway)
# ─────────────────────────────────────────────────────────

@udf(input_types=["FLOAT64[]", "INT"], result_type="JSONB", io_threads=1)
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


@udf(input_types=["FLOAT64[]", "FLOAT64[]"], result_type="FLOAT64", io_threads=1)
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


@udf(input_types=["FLOAT64", "FLOAT64"], result_type="FLOAT64", io_threads=1)
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


@udf(input_types=["VARCHAR", "BOOLEAN", "BOOLEAN"], result_type="FLOAT64", io_threads=1)
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


@udf(input_types=["VARCHAR", "VARCHAR", "VARCHAR", "VARCHAR"], result_type="VARCHAR", io_threads=1)
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


@udf(
    input_types=["INT", "INT", "INT", "FLOAT64", "FLOAT64"],
    result_type="FLOAT64",
    io_threads=1,
)
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


@udf(input_types=["JSONB"], result_type="VARCHAR", io_threads=1)
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


# ─────────────────────────────────────────────────────────
# IO-bound UDFs — io_threads mandatory per ADR-0044 D3
# ─────────────────────────────────────────────────────────

_LLM_URL = os.environ.get("LLM_URL", "http://ollama.etzhayyim.com/v1/chat/completions")
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


@udf(
    input_types=["VARCHAR", "VARCHAR", "VARCHAR"],
    result_type="VARCHAR",
    io_threads=_T3_IO_THREADS,
)
def classify_t3(subject: str | None, from_addr: str | None, body_preview: str | None) -> str:
    """yabai T3 (LLM gray-zone) classifier — ADR-0032.

    Input: email row (subject, from_addr, body_preview).
    Output: JSON varchar {"label","confidence","reason"}.

    Throughput (empirical 2026-04-21, 50 rows × 500ms mock LLM):
      io_threads=1  → 16.5 rps (SDK gRPC pool bound)
      io_threads=20 → 32.9 rps
      io_threads=50 → 94.9 rps (95% efficient vs 50/0.5s theoretical 100)

    For gemma4:e4b (~2s real latency), io_threads=50 → ~25 rps.
    Cron (100 emails / 15 min) = 0.11 rps sustained → single instance OK.
    """
    return _call_llm(subject, from_addr, body_preview)


def main() -> None:
    port = int(os.environ.get("UDF_PORT", "8815"))
    server = UdfServer(location=f"0.0.0.0:{port}")
    server.add_function(gmm_fit)
    server.add_function(cosine_similarity)
    server.add_function(posterior_update)
    server.add_function(news_source_credibility)
    server.add_function(news_intel_priority)
    server.add_function(topology_dependency_hint)
    server.add_function(segment_hash)
    server.add_function(classify_t3)
    print(f"[risingwave-udf] listening on 0.0.0.0:{port}  llm={_LLM_URL}  t3_io_threads={_T3_IO_THREADS}", flush=True)
    server.serve()


if __name__ == "__main__":
    main()
