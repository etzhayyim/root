"""kiyo RisingWave Python External UDF functions.

ADR-0044 compliant: Arrow Flight gRPC, port 8815.
Deploy: add to risingwave-udf K8s deployment.

Functions:
  kiyo_embed_query(query TEXT) → DOUBLE PRECISION[]
    — embed a search query string for cosine similarity search.
    — io_threads=100: each call fires one HTTP request to Murakumo.

  kiyo_classify_subject(title TEXT, abstract TEXT) → VARCHAR[]
    — classify paper into arXiv-compatible subject codes.
    — io_threads=50: LLM call per row.

Usage in RisingWave SQL:
  SELECT p.paper_id, p.title,
         list_cosine_similarity(p.embedding, kiyo_embed_query('autopoiesis')) AS score
  FROM vertex_kiyo_paper p
  WHERE p.status = 'active' AND p.embedding IS NOT NULL
  ORDER BY score DESC
  LIMIT 20;
"""

from __future__ import annotations

import json
import os
import urllib.request

from arrow_udf import UdfServer, udf

MURAKUMO_URL = os.environ.get("MURAKUMO_URL", "https://murakumo-serve.etzhayyim.com")
MURAKUMO_KEY = os.environ.get("MURAKUMO_API_KEY", "")
EMBED_MODEL  = os.environ.get("KIYO_EMBED_MODEL", "nomic-embed-text")
LLM_MODEL    = os.environ.get("KIYO_LLM_MODEL", "gemma3:4b")

KNOWN_SUBJECTS = [
    "cs.AI", "cs.DC", "cs.MA", "cs.LG", "cs.CR", "cs.SE",
    "math.ST", "math.OC", "q-bio.BM", "q-bio.NC",
    "econ.GN", "econ.EM",
    "etzhayyim.arch", "etzhayyim.agent", "etzhayyim.bio", "etzhayyim.law",
]


def _post_json(url: str, body: dict) -> dict:
    data = json.dumps(body).encode()
    req  = urllib.request.Request(
        url, data=data,
        headers={
            "Content-Type":  "application/json",
            "Authorization": f"Bearer {MURAKUMO_KEY}",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read())


@udf(input_types=["VARCHAR"], result_type="DOUBLE PRECISION[]", io_threads=100)
def kiyo_embed_query(query: str | None) -> list[float]:
    """Embed a search query string.

    io_threads=100 allows 100 concurrent embedding requests from
    streaming SQL — matches CF Worker Promise.all(100) pattern.
    """
    if not query:
        return []
    try:
        resp   = _post_json(
            f"{MURAKUMO_URL}/v1/embeddings",
            {"model": EMBED_MODEL, "input": query},
        )
        return resp["data"][0]["embedding"]
    except Exception:
        return []


@udf(input_types=["VARCHAR", "VARCHAR"], result_type="VARCHAR[]", io_threads=50)
def kiyo_classify_subject(title: str | None, abstract: str | None) -> list[str]:
    """Classify a paper into arXiv-compatible subject codes via LLM.

    Returns at most 3 subject codes from KNOWN_SUBJECTS.
    io_threads=50 for concurrent LLM calls in batch ingestion scenarios.
    """
    if not title and not abstract:
        return []
    prompt = (
        f"Classify this academic paper into arXiv subject codes.\n"
        f"Available codes: {', '.join(KNOWN_SUBJECTS)}\n"
        f"Return a JSON array of 1-3 matching codes.\n"
        f"Title: {title or ''}\nAbstract: {(abstract or '')[:500]}"
    )
    try:
        resp = _post_json(
            f"{MURAKUMO_URL}/v1/chat/completions",
            {
                "model": LLM_MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.0,
            },
        )
        content = resp["choices"][0]["message"]["content"]
        import re
        m = re.search(r"\[.*?\]", content, re.DOTALL)
        codes: list[str] = json.loads(m.group(0)) if m else []
        return [c for c in codes if c in KNOWN_SUBJECTS][:3]
    except Exception:
        return []


if __name__ == "__main__":
    server = UdfServer(location="0.0.0.0:8815")
    server.add_function(kiyo_embed_query)
    server.add_function(kiyo_classify_subject)
    server.serve()
