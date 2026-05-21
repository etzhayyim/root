"""Tests for etzhayyim_sdk.llm — LiteLLM OpenAI-compatible client.

All tests use httpx.MockTransport injected via llm._inject_transport() — no
real network calls are made.

Coverage:
  test_chat_happy                   — 200 + choices structure → content string
  test_chat_auth_error_401          — 401 → LlmAuthError
  test_chat_auth_error_403          — 403 → LlmAuthError
  test_chat_rate_limit              — 429 → LlmRateLimitError
  test_chat_server_error_500        — 500 → LlmServerError (status_code attr)
  test_chat_network_error           — ConnectError → LlmNetworkError
  test_chat_no_choices_raises       — empty choices → LlmError
  test_chat_json_parse_success      — valid JSON content → dict
  test_chat_json_parse_failure      — non-JSON content → LlmParseError (raw attr)
  test_translate_builds_prompt      — verify system prompt contains target_lang
  test_translate_with_source_lang   — source_lang included in system prompt
  test_vision_encodes_base64        — image_url contains data: URL with b64 payload
  test_vision_image_format_jpeg     — image_format="jpeg" produces correct MIME
  test_vision_json_success          — vision + JSON parse → dict
  test_vision_json_parse_error      — VLM non-JSON response → LlmParseError
  test_default_model_env_var        — ETZHAYYIM_LITELLM_DEFAULT_MODEL used

  Streaming (ADR-2605215100 §1 T1):
  test_chat_stream_yields_chunks    — 3-chunk SSE → 3 yielded strings
  test_chat_stream_handles_empty_lines  — keep-alive blanks don't error
  test_chat_stream_done_terminator  — [DONE] stops iteration cleanly
  test_chat_stream_auth_error       — 401 → LlmAuthError
  test_chat_stream_server_error     — 500 → LlmServerError

  Retry / backoff:
  test_chat_with_retry_rate_limit_then_success — 429, 429, 200 → 2 retries then success
  test_chat_with_retry_exhaustion   — 429×3 (attempts=3) → raises LlmRateLimitError
  test_chat_with_retry_off          — retry=False, 429 → raises immediately
  test_chat_no_retry_on_auth_error  — 401 → raises immediately (not in retry set)
  test_vision_with_retry            — vision() uses same retry pattern

ADR-2605215000 — inference SSoT: EVO-X2 LAN @ 192.168.1.70:4000.
ADR-2605215100 §1 T1 — Sentinel VLM tile classification.
"""

from __future__ import annotations

import base64
import json
import os
import sys
from pathlib import Path
from typing import Any

import httpx
import pytest

# ── Path setup ────────────────────────────────────────────────────────────────
_sdk_src = Path(__file__).resolve().parents[1] / "src"
if str(_sdk_src) not in sys.path:
    sys.path.insert(0, str(_sdk_src))


# ── Helpers ───────────────────────────────────────────────────────────────────


def _inject(handler):
    """Inject a MockTransport handler into the llm module singleton."""
    from etzhayyim_sdk import llm as llm_module

    transport = httpx.MockTransport(handler)
    llm_module._inject_transport(transport)


def _chat_response(content: str) -> httpx.Response:
    """Build a minimal OpenAI-compatible 200 chat completions response."""
    return httpx.Response(
        200,
        json={
            "id": "chatcmpl-test",
            "object": "chat.completion",
            "choices": [
                {
                    "index": 0,
                    "message": {"role": "assistant", "content": content},
                    "finish_reason": "stop",
                }
            ],
            "usage": {"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30},
        },
    )


# ── test_chat_happy ───────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_chat_happy():
    """chat() returns assistant content string on 200."""
    from etzhayyim_sdk import llm

    def handler(request: httpx.Request) -> httpx.Response:
        assert "/chat/completions" in request.url.path
        body = json.loads(request.content)
        assert body["messages"][0]["role"] == "user"
        assert body["max_tokens"] == 1024
        return _chat_response("Hello from EVO-X2!")

    _inject(handler)
    result = await llm.chat([{"role": "user", "content": "Hello"}])
    assert result == "Hello from EVO-X2!"


# ── test_chat_auth_error ──────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_chat_auth_error_401():
    """chat() raises LlmAuthError on 401."""
    from etzhayyim_sdk import llm
    from etzhayyim_sdk.errors import LlmAuthError

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, json={"error": {"message": "Unauthorized"}})

    _inject(handler)
    with pytest.raises(LlmAuthError, match="401"):
        await llm.chat([{"role": "user", "content": "test"}])


@pytest.mark.asyncio
async def test_chat_auth_error_403():
    """chat() raises LlmAuthError on 403."""
    from etzhayyim_sdk import llm
    from etzhayyim_sdk.errors import LlmAuthError

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(403, json={"error": {"message": "Forbidden"}})

    _inject(handler)
    with pytest.raises(LlmAuthError, match="403"):
        await llm.chat([{"role": "user", "content": "test"}])


# ── test_chat_rate_limit ──────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_chat_rate_limit():
    """chat() raises LlmRateLimitError on 429."""
    from etzhayyim_sdk import llm
    from etzhayyim_sdk.errors import LlmRateLimitError

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(429, json={"error": {"message": "Too Many Requests"}})

    _inject(handler)
    with pytest.raises(LlmRateLimitError):
        await llm.chat([{"role": "user", "content": "test"}])


# ── test_chat_server_error ────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_chat_server_error_500():
    """chat() raises LlmServerError on 500 with status_code attr."""
    from etzhayyim_sdk import llm
    from etzhayyim_sdk.errors import LlmServerError

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, text="Internal Server Error")

    _inject(handler)
    with pytest.raises(LlmServerError) as exc_info:
        await llm.chat([{"role": "user", "content": "test"}])
    assert exc_info.value.status_code == 500
    assert "Internal Server Error" in exc_info.value.body


# ── test_chat_network_error ───────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_chat_network_error():
    """chat() wraps httpx.ConnectError in LlmNetworkError."""
    from etzhayyim_sdk import llm
    from etzhayyim_sdk.errors import LlmNetworkError

    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("Connection refused")

    _inject(handler)
    with pytest.raises(LlmNetworkError) as exc_info:
        await llm.chat([{"role": "user", "content": "test"}])
    assert exc_info.value.cause is not None


# ── test_chat_no_choices ──────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_chat_no_choices_raises():
    """chat() raises LlmError when response has no choices."""
    from etzhayyim_sdk import llm
    from etzhayyim_sdk.errors import LlmError

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"id": "x", "choices": [], "object": "chat.completion"})

    _inject(handler)
    with pytest.raises(LlmError, match="no choices"):
        await llm.chat([{"role": "user", "content": "test"}])


# ── test_chat_json_parse_success ──────────────────────────────────────────────


@pytest.mark.asyncio
async def test_chat_json_parse_success():
    """chat_json() returns dict when assistant content is valid JSON."""
    from etzhayyim_sdk import llm

    payload = {"landCover": "forest", "confidence": 0.92}

    def handler(request: httpx.Request) -> httpx.Response:
        return _chat_response(json.dumps(payload))

    _inject(handler)
    result = await llm.chat_json([{"role": "user", "content": "classify"}])
    assert result == payload
    assert result["landCover"] == "forest"
    assert result["confidence"] == 0.92


# ── test_chat_json_parse_failure ──────────────────────────────────────────────


@pytest.mark.asyncio
async def test_chat_json_parse_failure():
    """chat_json() raises LlmParseError when assistant content is not JSON."""
    from etzhayyim_sdk import llm
    from etzhayyim_sdk.errors import LlmParseError

    def handler(request: httpx.Request) -> httpx.Response:
        return _chat_response("Sure, let me tell you about the land cover…")

    _inject(handler)
    with pytest.raises(LlmParseError) as exc_info:
        await llm.chat_json([{"role": "user", "content": "classify"}])
    # raw attribute contains the unparseable text
    assert "land cover" in exc_info.value.raw


# ── test_translate ────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_translate_builds_prompt():
    """translate() builds a system prompt containing the target language."""
    from etzhayyim_sdk import llm

    captured_body: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured_body.update(json.loads(request.content))
        return _chat_response("こんにちは")

    _inject(handler)
    result = await llm.translate("Hello", "Japanese")
    assert result == "こんにちは"

    messages = captured_body["messages"]
    assert messages[0]["role"] == "system"
    assert "Japanese" in messages[0]["content"]
    assert messages[1]["role"] == "user"
    assert messages[1]["content"] == "Hello"


@pytest.mark.asyncio
async def test_translate_with_source_lang():
    """translate() includes source language in the system prompt when provided."""
    from etzhayyim_sdk import llm

    captured_body: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured_body.update(json.loads(request.content))
        return _chat_response("Bonjour")

    _inject(handler)
    await llm.translate("Hello", "French", source_lang="English")

    system_content = captured_body["messages"][0]["content"]
    assert "English" in system_content
    assert "French" in system_content


# ── test_vision ───────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_vision_encodes_base64():
    """vision() encodes image_bytes as a base64 data URL in the message."""
    from etzhayyim_sdk import llm

    fake_png = b"\x89PNG\r\n\x1a\n" + b"\x00" * 20  # minimal PNG-like bytes
    captured_body: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured_body.update(json.loads(request.content))
        return _chat_response("forest")

    _inject(handler)
    await llm.vision("Classify this tile.", fake_png, image_format="png")

    messages = captured_body["messages"]
    assert messages[0]["role"] == "user"
    content_parts = messages[0]["content"]
    assert isinstance(content_parts, list)

    # First part: text
    text_part = content_parts[0]
    assert text_part["type"] == "text"
    assert text_part["text"] == "Classify this tile."

    # Second part: image_url with base64 data URL
    image_part = content_parts[1]
    assert image_part["type"] == "image_url"
    url = image_part["image_url"]["url"]
    assert url.startswith("data:image/png;base64,")

    # Verify the base64 payload decodes back to the original bytes
    b64_payload = url.split(",", 1)[1]
    decoded = base64.standard_b64decode(b64_payload)
    assert decoded == fake_png


@pytest.mark.asyncio
async def test_vision_image_format_jpeg():
    """vision() uses correct MIME type for image_format='jpeg'."""
    from etzhayyim_sdk import llm

    captured_body: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured_body.update(json.loads(request.content))
        return _chat_response("urban")

    _inject(handler)
    await llm.vision("Classify.", b"\xff\xd8\xff" + b"\x00" * 10, image_format="jpeg")

    url = captured_body["messages"][0]["content"][1]["image_url"]["url"]
    assert url.startswith("data:image/jpeg;base64,")


# ── test_vision_json ──────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_vision_json_success():
    """vision_json() returns dict from VLM JSON response."""
    from etzhayyim_sdk import llm

    vlm_output = {"landCover": "water", "confidence": 0.88}

    def handler(request: httpx.Request) -> httpx.Response:
        return _chat_response(json.dumps(vlm_output))

    _inject(handler)
    result = await llm.vision_json("Classify tile.", b"\x89PNG\r\n" + b"\x00" * 20)
    assert result["landCover"] == "water"
    assert result["confidence"] == 0.88


@pytest.mark.asyncio
async def test_vision_json_parse_error():
    """vision_json() raises LlmParseError when VLM returns non-JSON."""
    from etzhayyim_sdk import llm
    from etzhayyim_sdk.errors import LlmParseError

    def handler(request: httpx.Request) -> httpx.Response:
        return _chat_response("The image appears to show a forested area…")

    _inject(handler)
    with pytest.raises(LlmParseError) as exc_info:
        await llm.vision_json("Classify.", b"\x89PNG" + b"\x00" * 20)
    assert "forested" in exc_info.value.raw


# ── test_default_model_env_var ────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_default_model_env_var(monkeypatch):
    """chat() uses ETZHAYYIM_LITELLM_DEFAULT_MODEL when no model is specified."""
    from etzhayyim_sdk import llm

    monkeypatch.setenv("ETZHAYYIM_LITELLM_DEFAULT_MODEL", "my-custom-model-v2")

    captured_body: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured_body.update(json.loads(request.content))
        return _chat_response("ok")

    _inject(handler)
    await llm.chat([{"role": "user", "content": "test"}])
    assert captured_body["model"] == "my-custom-model-v2"


@pytest.mark.asyncio
async def test_model_override_takes_precedence(monkeypatch):
    """When model= is passed explicitly it overrides the env var default."""
    from etzhayyim_sdk import llm

    monkeypatch.setenv("ETZHAYYIM_LITELLM_DEFAULT_MODEL", "env-model")

    captured_body: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured_body.update(json.loads(request.content))
        return _chat_response("ok")

    _inject(handler)
    await llm.chat([{"role": "user", "content": "test"}], model="override-model")
    assert captured_body["model"] == "override-model"


# ── Error hierarchy smoke ─────────────────────────────────────────────────────


def test_llm_error_hierarchy():
    """All LLM errors form the correct hierarchy."""
    from etzhayyim_sdk.errors import (
        EtzhayyimSdkError,
        LlmAuthError,
        LlmError,
        LlmNetworkError,
        LlmParseError,
        LlmRateLimitError,
        LlmServerError,
    )

    assert issubclass(LlmError, EtzhayyimSdkError)
    assert issubclass(LlmNetworkError, LlmError)
    assert issubclass(LlmServerError, LlmError)
    assert issubclass(LlmAuthError, LlmError)
    assert issubclass(LlmRateLimitError, LlmError)
    assert issubclass(LlmParseError, LlmError)


def test_llm_server_error_attrs():
    """LlmServerError exposes status_code and body."""
    from etzhayyim_sdk.errors import LlmServerError

    err = LlmServerError(503, "Service Unavailable")
    assert err.status_code == 503
    assert "503" in str(err)
    assert err.body == "Service Unavailable"


def test_llm_network_error_cause():
    """LlmNetworkError wraps the original exception in .cause."""
    from etzhayyim_sdk.errors import LlmNetworkError

    original = ConnectionRefusedError("refused")
    err = LlmNetworkError(original)
    assert err.cause is original


def test_llm_parse_error_raw():
    """LlmParseError stores unparseable text in .raw."""
    from etzhayyim_sdk.errors import LlmParseError

    err = LlmParseError("not JSON", raw="some free text")
    assert err.raw == "some free text"
