"""llm — LiteLLM OpenAI-compatible client for EVO-X2 ROCm inference.

Provides async wrappers over the OpenAI-compatible /chat/completions endpoint
served by LiteLLM on either:
  - 127.0.0.1:4000   (local LiteLLM proxy, e.g. running on murakumo node)
  - 192.168.1.70:4000 (EVO-X2 LAN direct — ADR-2605215000 §1 inference SSoT)

Default model: ``qwen3-vl-8b-instruct-4bit`` (Qwen3-VL-8B-Instruct-4bit on
EVO-X2 ROCm gfx1151) per ADR-2605215100 §1 T1 (10-30s per tile target).

Configuration (env vars):
  ETZHAYYIM_LITELLM_URL           — LiteLLM base URL
                                    (default: http://192.168.1.70:4000/v1)
  ETZHAYYIM_LITELLM_KEY           — Bearer API key for the gateway
                                    (default: empty string)
  ETZHAYYIM_LITELLM_DEFAULT_MODEL — Default model alias
                                    (default: qwen3-vl-8b-instruct-4bit)

ADR references:
  ADR-2605215000 — inference SSoT: LiteLLM @ murakumo / EVO-X2 LAN only,
                   no RunPod / commercial GPU rental
  ADR-2605215100 §1 T1 — Sentinel-2/1 VLM tile classification via Qwen3-VL

Usage::

    from etzhayyim_sdk import llm

    # Simple chat
    reply = await llm.chat([{"role": "user", "content": "Hello"}])

    # Streaming chat (yields content deltas)
    async for chunk in llm.chat_stream([{"role": "user", "content": "Hello"}]):
        print(chunk, end="", flush=True)

    # Vision (for maps_sentinel T1)
    result = await llm.vision_json(
        "Classify this tile. Return JSON.",
        tile_bytes,
        image_format="png",
        max_tokens=256,
    )
"""

from __future__ import annotations

import asyncio
import base64
import json
import logging
import os
import random
from functools import wraps
from typing import Any, AsyncIterator, Callable, TypeVar

import httpx

from .errors import LlmAuthError, LlmError, LlmNetworkError, LlmParseError, LlmRateLimitError, LlmServerError

_log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Retry configuration constants
# ---------------------------------------------------------------------------

DEFAULT_RETRY_ATTEMPTS = 3
DEFAULT_RETRY_BASE_DELAY = 1.0  # seconds
DEFAULT_RETRY_JITTER = 0.5  # seconds (uniform random added to each delay)

T = TypeVar("T")

# ---------------------------------------------------------------------------
# Module-level singleton client (lazy init, match pds.py pattern)
# ---------------------------------------------------------------------------

_client: httpx.AsyncClient | None = None


def _get_client() -> httpx.AsyncClient:
    """Return the module-level singleton httpx.AsyncClient, creating it lazily.

    Timeout is set to 180 s — LLM inference can take 30+ s per tile.
    """
    global _client
    if _client is None or _client.is_closed:
        _client = httpx.AsyncClient(timeout=180.0)
    return _client


def _inject_transport(transport: httpx.AsyncBaseTransport) -> None:
    """Replace the module singleton with a client backed by *transport*.

    Called from tests to inject httpx.MockTransport without touching env vars.
    Resets the singleton client.
    """
    global _client
    _client = httpx.AsyncClient(transport=transport, timeout=180.0)


# ---------------------------------------------------------------------------
# Retry decorator
# ---------------------------------------------------------------------------


def _with_retry(
    fn: Callable[..., Any],
    *,
    attempts: int = DEFAULT_RETRY_ATTEMPTS,
    base_delay: float = DEFAULT_RETRY_BASE_DELAY,
    jitter: float = DEFAULT_RETRY_JITTER,
) -> Callable[..., Any]:
    """Wrap an async function with exponential-backoff retry on transient errors.

    Retries on :class:`~.errors.LlmRateLimitError` and
    :class:`~.errors.LlmNetworkError` only.  Other errors (auth, server,
    parse) raise immediately — they require operator action, not retrying.

    Backoff formula per attempt *n* (0-based)::

        delay = base_delay * 2^n + uniform(0, jitter)

    So with defaults: 1.0s, 2.0s–2.5s, 4.0s–4.5s ...

    Args:
        fn:         The async function to wrap.
        attempts:   Maximum total attempts (including the first try).
        base_delay: Base delay in seconds before the first retry.
        jitter:     Upper bound of the random jitter added to each delay.

    Returns:
        A wrapped async callable with the same signature as *fn*.
    """

    @wraps(fn)
    async def wrapper(*args: Any, **kwargs: Any) -> Any:
        last_exc: Exception | None = None
        for attempt in range(attempts):
            try:
                return await fn(*args, **kwargs)
            except (LlmRateLimitError, LlmNetworkError) as exc:
                last_exc = exc
                if attempt == attempts - 1:
                    raise
                delay = base_delay * (2**attempt) + random.uniform(0, jitter)
                _log.warning(
                    "llm transient error (attempt %d/%d), retrying in %.2fs: %s",
                    attempt + 1,
                    attempts,
                    delay,
                    exc,
                )
                await asyncio.sleep(delay)
        if last_exc:  # pragma: no cover — loop always raises before here
            raise last_exc

    return wrapper


# ---------------------------------------------------------------------------
# Configuration helpers
# ---------------------------------------------------------------------------


def _endpoint() -> str:
    """Return the LiteLLM /v1 base URL."""
    return os.environ.get("ETZHAYYIM_LITELLM_URL", "http://192.168.1.70:4000/v1")


def _api_key() -> str:
    """Return the Bearer API key for the LiteLLM gateway."""
    return os.environ.get("ETZHAYYIM_LITELLM_KEY", "")


def _default_model() -> str:
    """Return the default model alias (env-overridable)."""
    return os.environ.get(
        "ETZHAYYIM_LITELLM_DEFAULT_MODEL", "qwen3-vl-8b-instruct-4bit"
    )


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _auth_headers() -> dict[str, str]:
    key = _api_key()
    headers: dict[str, str] = {"Content-Type": "application/json"}
    if key:
        headers["Authorization"] = f"Bearer {key}"
    return headers


async def _post_chat_completions(
    payload: dict[str, Any],
    *,
    timeout: float | None = None,
) -> dict[str, Any]:
    """POST to /chat/completions; parse JSON; raise typed LlmError on failure.

    Returns the full response dict (OpenAI-compatible shape).
    """
    client = _get_client()
    url = _endpoint().rstrip("/") + "/chat/completions"
    request_kwargs: dict[str, Any] = {
        "json": payload,
        "headers": _auth_headers(),
    }
    if timeout is not None:
        request_kwargs["timeout"] = timeout

    try:
        resp = await client.post(url, **request_kwargs)
    except httpx.RequestError as exc:
        raise LlmNetworkError(exc) from exc

    if resp.status_code in (401, 403):
        raise LlmAuthError(
            f"LLM auth error {resp.status_code}: {resp.text!r}"
        )
    if resp.status_code == 429:
        raise LlmRateLimitError(
            f"LLM rate limited (429): {resp.text!r}"
        )
    if resp.status_code >= 500:
        raise LlmServerError(resp.status_code, resp.text)

    resp.raise_for_status()
    return resp.json()


def _extract_content(response_json: dict[str, Any]) -> str:
    """Extract assistant message content from a /chat/completions response."""
    choices = response_json.get("choices", [])
    if not choices:
        raise LlmError("LLM response has no choices")
    message = choices[0].get("message", {})
    content = message.get("content", "")
    return content


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


async def _chat_inner(
    messages: list[dict[str, Any]],
    *,
    model: str | None = None,
    max_tokens: int = 1024,
    temperature: float = 0.1,
    timeout: float | None = None,
) -> str:
    """Core chat implementation (no retry logic)."""
    payload: dict[str, Any] = {
        "model": model or _default_model(),
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
    }
    response_json = await _post_chat_completions(payload, timeout=timeout)
    return _extract_content(response_json)


_chat_inner_with_retry = _with_retry(_chat_inner)


async def chat(
    messages: list[dict[str, Any]],
    *,
    model: str | None = None,
    max_tokens: int = 1024,
    temperature: float = 0.1,
    timeout: float | None = None,
    retry: bool = True,
) -> str:
    """Send an OpenAI-compatible /chat/completions request; return assistant content.

    Args:
        messages:    List of ``{"role": "...", "content": "..."}`` dicts.
                     For vision, ``content`` may be a list of content parts
                     (text + image_url).
        model:       Override the model alias. Defaults to
                     ``ETZHAYYIM_LITELLM_DEFAULT_MODEL`` env var.
        max_tokens:  Maximum tokens to generate (default 1024).
        temperature: Sampling temperature (default 0.1 for determinism).
        timeout:     Per-request timeout in seconds. Falls back to client default
                     (180 s) when None.
        retry:       When ``True`` (default), retries up to
                     ``DEFAULT_RETRY_ATTEMPTS`` times on transient errors
                     (429 rate-limit, network failure) with exponential backoff.
                     Set to ``False`` to raise immediately on the first error.

    Returns:
        The assistant's message content string.

    Raises:
        LlmAuthError:       HTTP 401/403.
        LlmRateLimitError:  HTTP 429 (raised after exhausting retries when retry=True).
        LlmServerError:     HTTP 5xx with body (never retried).
        LlmNetworkError:    Connection failure (raised after exhausting retries when retry=True).
        LlmError:           Gateway returned no choices.
    """
    kwargs: dict[str, Any] = {
        "model": model,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "timeout": timeout,
    }
    if retry:
        return await _chat_inner_with_retry(messages, **kwargs)
    return await _chat_inner(messages, **kwargs)


async def chat_json(
    messages: list[dict[str, Any]],
    *,
    model: str | None = None,
    max_tokens: int = 1024,
    temperature: float = 0.1,
    timeout: float | None = None,
) -> dict[str, Any]:
    """Same as :func:`chat` but parses the assistant content as JSON.

    Useful for structured extraction where the model is prompted to return
    a JSON object.

    Args:
        messages:    See :func:`chat`.
        model:       See :func:`chat`.
        max_tokens:  See :func:`chat`.
        temperature: See :func:`chat`.
        timeout:     See :func:`chat`.

    Returns:
        Parsed JSON dict from the assistant's response.

    Raises:
        LlmParseError:  Assistant content is not valid JSON.
        (all errors from :func:`chat`)
    """
    content = await chat(
        messages,
        model=model,
        max_tokens=max_tokens,
        temperature=temperature,
        timeout=timeout,
    )
    try:
        return json.loads(content)
    except (json.JSONDecodeError, ValueError) as exc:
        raise LlmParseError(
            f"LLM response is not valid JSON: {exc}",
            raw=content,
        ) from exc


async def translate(
    source_text: str,
    target_lang: str,
    *,
    source_lang: str | None = None,
    model: str | None = None,
) -> str:
    """Translate *source_text* to *target_lang* using the LLM.

    Args:
        source_text: Text to translate.
        target_lang: Target language name or code (e.g. ``"Japanese"`` / ``"ja"``).
        source_lang: Source language hint (optional). When None, the model
                     auto-detects the source language.
        model:       Override the model alias. Defaults to
                     ``ETZHAYYIM_LITELLM_DEFAULT_MODEL`` env var.

    Returns:
        Translated text string.

    Raises:
        (all errors from :func:`chat`)
    """
    if source_lang:
        system_prompt = (
            f"You are a professional translator. "
            f"Translate the following {source_lang} text to {target_lang}. "
            f"Return only the translation with no explanations."
        )
    else:
        system_prompt = (
            f"You are a professional translator. "
            f"Translate the following text to {target_lang}. "
            f"Return only the translation with no explanations."
        )

    messages: list[dict[str, Any]] = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": source_text},
    ]
    return await chat(messages, model=model)


async def _vision_inner(
    prompt: str,
    image_bytes: bytes,
    *,
    image_format: str = "png",
    model: str | None = None,
    max_tokens: int = 256,
) -> str:
    """Core vision implementation (no retry logic)."""
    img_b64 = base64.standard_b64encode(image_bytes).decode("utf-8")
    data_url = f"data:image/{image_format};base64,{img_b64}"

    messages: list[dict[str, Any]] = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": data_url}},
            ],
        }
    ]
    # Call _chat_inner directly so vision retry controls its own stack
    return await _chat_inner(messages, model=model, max_tokens=max_tokens)


_vision_inner_with_retry = _with_retry(_vision_inner)


async def vision(
    prompt: str,
    image_bytes: bytes,
    *,
    image_format: str = "png",
    model: str | None = None,
    max_tokens: int = 256,
    retry: bool = True,
) -> str:
    """Send an image + text prompt to the vision-language model.

    Encodes *image_bytes* as a base64 data URL and sends it via the
    OpenAI-compatible multipart content format.

    Args:
        prompt:       Text prompt / question about the image.
        image_bytes:  Raw PNG or JPEG bytes.
        image_format: ``"png"`` (default) or ``"jpeg"``.
        model:        Override the model alias.
        max_tokens:   Maximum tokens to generate (default 256 for tile
                      classification — short JSON responses expected).
        retry:        When ``True`` (default), retries on transient errors.
                      Set to ``False`` to raise immediately on the first error.

    Returns:
        The assistant's message content string.

    Raises:
        (all errors from :func:`chat`)
    """
    if retry:
        return await _vision_inner_with_retry(
            prompt, image_bytes, image_format=image_format, model=model, max_tokens=max_tokens
        )
    return await _vision_inner(
        prompt, image_bytes, image_format=image_format, model=model, max_tokens=max_tokens
    )


async def vision_json(
    prompt: str,
    image_bytes: bytes,
    *,
    image_format: str = "png",
    model: str | None = None,
    max_tokens: int = 256,
) -> dict[str, Any]:
    """Vision call with JSON parsing. Primary entrypoint for maps_sentinel T1.

    Combines :func:`vision` and :func:`chat_json`: encodes the image, calls
    the VLM, and parses the response as JSON.  Retries on transient errors
    via the ``vision()`` retry wrapper.

    Args:
        prompt:       Text prompt instructing the VLM to return JSON.
        image_bytes:  Raw PNG or JPEG bytes.
        image_format: ``"png"`` (default) or ``"jpeg"``.
        model:        Override the model alias.
        max_tokens:   Maximum tokens to generate (default 256).

    Returns:
        Parsed JSON dict from the VLM response.

    Raises:
        LlmParseError:  VLM response is not valid JSON.
        (all errors from :func:`vision`)

    ADR-2605215100 §1 T1 — used by maps_sentinel_murakumo.t1_vision_language_detect().
    """
    content = await vision(
        prompt, image_bytes, image_format=image_format, model=model, max_tokens=max_tokens
    )
    try:
        return json.loads(content)
    except (json.JSONDecodeError, ValueError) as exc:
        raise LlmParseError(
            f"VLM response is not valid JSON: {exc}",
            raw=content,
        ) from exc


async def chat_stream(
    messages: list[dict[str, Any]],
    *,
    model: str | None = None,
    max_tokens: int = 1024,
    temperature: float = 0.1,
) -> AsyncIterator[str]:
    """Stream an OpenAI-compatible /chat/completions response via SSE.

    Yields content delta strings (each SSE chunk's
    ``choices[0].delta.content``).  The caller can join them for the full
    response or process each delta incrementally for low-latency display.

    Sends ``stream=True`` in the request body.  Parses the SSE response
    line-by-line, stripping ``data: `` prefixes, skipping keep-alive blank
    lines, and stopping cleanly on ``data: [DONE]``.

    .. note::
        Streaming retries are **not** supported here.  A retry would need to
        restart from the beginning, discarding partially-received output.
        Callers that need retry semantics should call :func:`chat` with
        ``retry=True`` (the default) instead.

    Args:
        messages:    List of ``{"role": "...", "content": "..."}`` dicts.
        model:       Override the model alias. Defaults to
                     ``ETZHAYYIM_LITELLM_DEFAULT_MODEL`` env var.
        max_tokens:  Maximum tokens to generate (default 1024).
        temperature: Sampling temperature (default 0.1 for determinism).

    Yields:
        Content delta strings as they arrive from the server.

    Raises:
        LlmAuthError:       HTTP 401/403.
        LlmRateLimitError:  HTTP 429.
        LlmServerError:     HTTP 5xx with body.
        LlmNetworkError:    Connection / transport failure.

    ADR-2605215100 §1 T1 — 10-30 s TTFT target for Sentinel tile processing.
    """
    client = _get_client()
    url = _endpoint().rstrip("/") + "/chat/completions"
    payload: dict[str, Any] = {
        "model": model or _default_model(),
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "stream": True,
    }

    try:
        async with client.stream("POST", url, json=payload, headers=_auth_headers()) as resp:
            if resp.status_code in (401, 403):
                body_text = await resp.aread()
                raise LlmAuthError(
                    f"LLM auth error {resp.status_code}: {body_text.decode(errors='replace')!r}"
                )
            if resp.status_code == 429:
                body_text = await resp.aread()
                raise LlmRateLimitError(
                    f"LLM rate limited (429): {body_text.decode(errors='replace')!r}"
                )
            if resp.status_code >= 500:
                body_text = await resp.aread()
                raise LlmServerError(
                    resp.status_code,
                    body_text.decode(errors="replace"),
                )

            async for line in resp.aiter_lines():
                line = line.strip()
                if not line or not line.startswith("data: "):
                    continue
                data = line[6:]  # strip leading "data: "
                if data == "[DONE]":
                    return
                try:
                    chunk = json.loads(data)
                except json.JSONDecodeError:
                    continue
                choices = chunk.get("choices", [])
                if not choices:
                    continue
                delta = choices[0].get("delta", {})
                content = delta.get("content")
                if content:
                    yield content
    except (LlmAuthError, LlmRateLimitError, LlmServerError):
        raise
    except httpx.HTTPError as exc:
        raise LlmNetworkError(exc) from exc
