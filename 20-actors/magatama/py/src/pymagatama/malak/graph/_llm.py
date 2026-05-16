"""LLM caller for malak graphs. Mirrors keiei but points to malak LLM if we had a dedicated one.
We will reuse the same environment variables for now, connecting to local Ollama.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request

LLM_URL = os.environ.get("GFTD_LLM_URL", "http://127.0.0.1:11434/v1/chat/completions")
LLM_KEY = os.environ.get("GFTD_LLM_API_KEY", "ollama")
LLM_MODEL = os.environ.get("MALAK_LLM_MODEL", os.environ.get("KEIEI_LLM_MODEL", "gemma4:e4b"))
LLM_TIMEOUT = float(os.environ.get("MALAK_LLM_TIMEOUT_SEC", "120"))

def _http_post(url: str, headers: dict, body: dict, timeout: float) -> dict:
    req = urllib.request.Request(
        url,
        data=json.dumps(body).encode(),
        headers=headers,
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode())

def call_llm(prompt: str, *, system: str = "", temperature: float = 0.2, max_tokens: int = 512) -> tuple[str, str]:
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
                "User-Agent": "malak-lsp/1.0"
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
    head = prompt.strip().splitlines()[0] if prompt.strip() else "(no prompt)"
    return (
        "[deterministic-fallback] LLM endpoint unreachable.\n"
        f"observed: {head[:240]}\n"
        "decision-shape: proceed with standard TLP enforcement."
    )
