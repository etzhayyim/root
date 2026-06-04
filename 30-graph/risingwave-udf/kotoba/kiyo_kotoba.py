"""kiyo kotoba-native Python functions.

This is the kotoba-native, RW-free, Murakumo-only port of `kiyo_udf.py`.
These functions are called in-process from kotoba cells (no Arrow-Flight server).
"""

from __future__ import annotations

import json
import os
import urllib.request

# ADR-2605215000: Murakumo loopback only
MURAKUMO_URL = os.environ.get("MURAKUMO_URL", "http://127.0.0.1:4000")
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


def kiyo_embed_query(query: str | None) -> list[float]:
    """Embed a search query string."""
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


def kiyo_classify_subject(title: str | None, abstract: str | None) -> list[str]:
    """Classify a paper into arXiv-compatible subject codes via LLM.

    Returns at most 3 subject codes from KNOWN_SUBJECTS.
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
