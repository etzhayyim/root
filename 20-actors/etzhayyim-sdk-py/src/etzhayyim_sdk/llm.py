"""etzhayyim-sdk-py LLM module — EVO-X2 LiteLLM integration.

Provides `translate()` and `chat()` with retry logic for religious-corp
actors running on the Murakumo fleet (ADR-2605215000).

Forbidden per ADR-2605215000 §1: OpenRouter / Vultr Serverless / RunPod.
All LLM calls are routed via EVO-X2 LiteLLM (llm.etzhayyim.com).

Configuration:
  ETZHAYYIM_LLM_URL    — base URL of the LiteLLM proxy (default: http://levi.local:4000)
  ETZHAYYIM_LLM_KEY    — API key for the LiteLLM proxy
  ETZHAYYIM_LLM_MODEL  — default model (default: gemma-4-e4b-it)

Usage::

    from etzhayyim_sdk import llm

    translated = await llm.translate(
        source_text="Hello world",
        target_lang="ja",
        source_lang="en",
    )

    reply = await llm.chat(
        prompt="Summarise this post.",
        context="<post text>",
    )
"""

from __future__ import annotations

import asyncio
import logging
import os
from typing import Any

import httpx

from .errors import EtzhayyimSdkError

_log = logging.getLogger(__name__)

# ── Error hierarchy ────────────────────────────────────────────────────────────


class LlmError(EtzhayyimSdkError):
    """Base error for LLM module failures."""


class LlmNetworkError(LlmError):
    """Raised when the HTTP request to the LLM proxy fails at the transport layer."""


class LlmAuthError(LlmError):
    """Raised when the LLM proxy returns HTTP 401 (authentication failure)."""


class LlmRateLimitError(LlmError):
    """Raised when the LLM proxy returns HTTP 429 (rate limit exceeded)."""


class LlmServerError(LlmError):
    """Raised when the LLM proxy returns HTTP 5xx."""


# ── Configuration ────────────────────────────────────────────────────────────


def _llm_url() -> str:
    return os.environ.get("ETZHAYYIM_LLM_URL", "http://levi.local:4000").rstrip("/")


def _llm_key() -> str:
    return os.environ.get("ETZHAYYIM_LLM_KEY", "")


def _llm_model() -> str:
    return os.environ.get("ETZHAYYIM_LLM_MODEL", "gemma-4-e4b-it")


# ── Singleton client ────────────────────────────────────────────────────────────

_client: httpx.AsyncClient | None = None


def _get_client() -> httpx.AsyncClient:
    global _client
    if _client is None:
        headers: dict[str, str] = {}
        key = _llm_key()
        if key:
            headers["Authorization"] = f"Bearer {key}"
        _client = httpx.AsyncClient(headers=headers, timeout=60.0)
    return _client


def _inject_client(client: httpx.AsyncClient) -> None:
    """Replace the singleton client. Used exclusively in tests."""
    global _client
    _client = client


# ── Internal retry helper ─────────────────────────────────────────────────────


_MAX_RETRIES = 3
_RETRY_DELAY_S = 2.0


async def _chat_completions(
    messages: list[dict[str, str]],
    model: str | None = None,
    max_tokens: int = 512,
    temperature: float = 0.3,
) -> str:
    """POST /v1/chat/completions with exponential backoff retry.

    Returns the assistant message text on success.

    Raises:
        LlmAuthError:       HTTP 401
        LlmRateLimitError:  HTTP 429
        LlmServerError:     HTTP 5xx (after retries)
        LlmNetworkError:    transport-level failure (after retries)
        LlmError:           HTTP 4xx other than 401/429
    """
    url = f"{_llm_url()}/v1/chat/completions"
    resolved_model = model or _llm_model()
    payload: dict[str, Any] = {
        "model": resolved_model,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
    }
    client = _get_client()
    last_exc: Exception | None = None

    for attempt in range(_MAX_RETRIES):
        try:
            resp = await client.post(url, json=payload)
        except httpx.HTTPError as exc:
            last_exc = LlmNetworkError(f"network error calling LLM: {exc}")
            if attempt < _MAX_RETRIES - 1:
                await asyncio.sleep(_RETRY_DELAY_S * (attempt + 1))
            continue

        if resp.status_code == 401:
            raise LlmAuthError(f"LLM auth failed (HTTP 401): {resp.text[:200]}")
        if resp.status_code == 429:
            raise LlmRateLimitError(f"LLM rate limited (HTTP 429): {resp.text[:200]}")
        if resp.status_code >= 500:
            last_exc = LlmServerError(f"LLM error HTTP {resp.status_code}: {resp.text[:200]}")
            if attempt < _MAX_RETRIES - 1:
                await asyncio.sleep(_RETRY_DELAY_S * (attempt + 1))
            continue
        if resp.status_code >= 400:
            raise LlmError(f"LLM error HTTP {resp.status_code}: {resp.text[:200]}")

        try:
            data = resp.json()
        except Exception as exc:
            raise LlmError(f"LLM response not valid JSON: {exc}") from exc

        choices = data.get("choices") or []
        if not choices:
            raise LlmError(f"LLM returned no choices: {data}")

        message = choices[0].get("message") or {}
        content = message.get("content") or ""
        return str(content).strip()

    if last_exc is not None:
        raise last_exc
    raise LlmError("LLM call failed after retries (unknown reason)")


# ── Public API ─────────────────────────────────────────────────────────────────


async def translate(
    source_text: str,
    target_lang: str,
    source_lang: str = "",
    *,
    model: str | None = None,
    max_tokens: int = 1024,
) -> str:
    """Translate *source_text* to *target_lang* via EVO-X2 LiteLLM.

    Per ADR-2605215000 §1: routes to Murakumo fleet LiteLLM proxy (EVO-X2),
    NOT OpenRouter / Vultr Serverless / RunPod.

    Args:
        source_text: Text to translate (≤ ~2000 characters recommended).
        target_lang: BCP-47 language code of the target language (e.g. "ja", "en", "zh-Hans").
        source_lang: BCP-47 language code of the source language. Auto-detected if empty.
        model:       LLM model override. Defaults to ETZHAYYIM_LLM_MODEL env var
                     (or "gemma-4-e4b-it" if not set).
        max_tokens:  Maximum tokens for the translation output (default 1024).

    Returns:
        Translated text as a string.

    Raises:
        LlmError:           base class for all LLM failures.
        LlmAuthError:       authentication failure.
        LlmRateLimitError:  rate limit exceeded.
        LlmServerError:     LLM proxy 5xx after retries.
        LlmNetworkError:    transport-level failure after retries.
    """
    if not source_text:
        return ""

    if source_lang:
        lang_hint = f"from {source_lang} "
    else:
        lang_hint = ""

    system_prompt = (
        "You are a precise translation assistant for the etzhayyim religious-corp "
        "social platform. Translate the given text accurately. "
        "Output ONLY the translated text — no explanations, no markdown, no prefixes."
    )
    user_prompt = (
        f"Translate the following text {lang_hint}to {target_lang}:\n\n{source_text}"
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    result = await _chat_completions(messages, model=model, max_tokens=max_tokens, temperature=0.1)
    _log.debug("translate: %s→%s len_in=%d len_out=%d", source_lang or "?", target_lang, len(source_text), len(result))
    return result


async def chat(
    prompt: str,
    context: str = "",
    *,
    model: str | None = None,
    max_tokens: int = 512,
    temperature: float = 0.7,
) -> str:
    """Send a single-turn chat prompt via EVO-X2 LiteLLM.

    Per ADR-2605215000 §1: routes to Murakumo fleet LiteLLM proxy (EVO-X2),
    NOT OpenRouter / Vultr Serverless / RunPod.

    Args:
        prompt:      User prompt string.
        context:     Optional context prepended to the user message.
        model:       LLM model override. Defaults to ETZHAYYIM_LLM_MODEL env var.
        max_tokens:  Maximum tokens for the response (default 512).
        temperature: Sampling temperature (default 0.7).

    Returns:
        Assistant reply as a string.

    Raises:
        LlmError, LlmAuthError, LlmRateLimitError, LlmServerError, LlmNetworkError.
    """
    user_content = f"{context}\n\n{prompt}".strip() if context else prompt

    messages = [
        {"role": "user", "content": user_content},
    ]

    result = await _chat_completions(messages, model=model, max_tokens=max_tokens, temperature=temperature)
    _log.debug("chat: len_prompt=%d len_reply=%d", len(prompt), len(result))
    return result
