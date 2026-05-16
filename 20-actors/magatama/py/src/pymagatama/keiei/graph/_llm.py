"""LLM caller for keiei graphs — env override → murakumo → deterministic fallback.

Resilient by design: if no LLM endpoint is reachable, return a structured
deterministic rationale so the daemon stays useful and the ledger keeps
filling. Phase 1 = "graphs run end-to-end"; production-quality LLM-backed
reasoning lands when GFTD_LLM_API_KEY / litellm proxy is wired into the
launchd EnvironmentVariables.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any

# Default endpoint is the Vultr CPU inference pool (gemma-4-E2B-it Q4_K_M
# served by llama.cpp's OpenAI-compatible server, exposed via Cloudflare
# Tunnel `gemma-e2b.gftd.ai`). Override via env when staging a different
# backend. ADR 2605101200; runbook at 50-infra/vultr/keiei-llm-pool/RUNBOOK.md.
LLM_URL = os.environ.get(
    "GFTD_LLM_URL",
    "https://gemma-e2b.gftd.ai/v1/chat/completions",
)
LLM_KEY = os.environ.get("GFTD_LLM_API_KEY", "")
LLM_MODEL = os.environ.get(
    "KEIEI_LLM_MODEL",
    os.environ.get("GFTD_LLM_MODEL", "gemma-4-E2B-it"),
)
LLM_TIMEOUT = float(os.environ.get("KEIEI_LLM_TIMEOUT_SEC", "20"))


def _http_post(url: str, headers: dict, body: dict, timeout: float) -> dict:
    req = urllib.request.Request(
        url,
        data=json.dumps(body).encode(),
        headers=headers,
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode())


def call_llm(prompt: str, *, system: str = "", temperature: float = 0.2,
             max_tokens: int = 512) -> tuple[str, str]:
    """Returns (text, source).

    `source` is one of "llm" / "fallback-no-key" / "fallback-error:{cls}".
    Caller should record `source` in the ledger so audit can distinguish
    real LLM rationales from deterministic stubs.
    """
    if not LLM_KEY:
        return _deterministic_stub(prompt, system), "fallback-no-key"

    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    try:
        resp = _http_post(
            LLM_URL,
            headers={
                "Authorization": f"Bearer {LLM_KEY}",
                "Content-Type": "application/json",
            },
            body={
                "model": LLM_MODEL,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
            },
            timeout=LLM_TIMEOUT,
        )
        choices = resp.get("choices") or []
        if not choices:
            return _deterministic_stub(prompt, system), "fallback-empty-choices"
        return choices[0]["message"]["content"].strip(), "llm"
    except urllib.error.URLError as e:
        return _deterministic_stub(prompt, system), f"fallback-error:{type(e).__name__}"
    except (json.JSONDecodeError, KeyError, TimeoutError) as e:
        return _deterministic_stub(prompt, system), f"fallback-error:{type(e).__name__}"


def _deterministic_stub(prompt: str, system: str) -> str:
    """Cheap structured fallback: extract the 'summary' line and echo a
    shape-preserving rationale. Better than failing the request; worse than
    a real LLM. Caller should treat it as a placeholder."""
    head = prompt.strip().splitlines()[0] if prompt.strip() else "(no prompt)"
    return (
        "[deterministic-fallback] LLM endpoint unreachable; returning "
        "shape-preserving rationale.\n"
        f"observed: {head[:240]}\n"
        "decision-shape: proceed within role authority; defer to human "
        "principal on Class A; record artefact in ledger."
    )
