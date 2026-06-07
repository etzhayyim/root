"""Murakumo-only LLM factory + charter guard (ADR-2605215000).

The agentic e2e layer (browser-use + langgraph) drives a browser with an LLM.
That LLM MUST be the Murakumo fleet (LiteLLM gateway on loopback 127.0.0.1:4000,
or a LAN fleet node), NEVER a commercial endpoint (OpenAI / Anthropic-direct /
Vertex / Bedrock / RunPod). This module is the single place an LLM client is
constructed, and `assert_murakumo_only()` refuses any non-fleet base URL by
construction — the same posture as the repo's other no-commercial-inference
guards.

Pure + import-light: the guard + key resolution are testable without langchain
or browser-use installed (make_llm imports them lazily).
"""

from __future__ import annotations

import os
import subprocess
from urllib.parse import urlparse

# The charter inference SSoT: LiteLLM gateway on loopback (TCC-exempt per
# ADR-2605302355) → EVO-X2 LAN + per-node Ollama. OpenAI-compatible surface.
DEFAULT_BASE_URL = "http://127.0.0.1:4000/v1"
DEFAULT_MODEL = "gemma4"

# Hosts that ARE the Murakumo fleet (loopback + the private LAN per
# ADR-2605215000 / 2605514...). Anything else is rejected.
_ALLOWED_HOSTS = {"127.0.0.1", "localhost", "::1", "0.0.0.0"}
_ALLOWED_HOST_SUFFIXES = (".murakumo.etzhayyim.com",)
_ALLOWED_PRIVATE_PREFIXES = ("192.168.", "10.", "172.16.", "172.17.", "172.18.", "172.19.")

# Commercial inference hosts that are constitutionally prohibited in any
# etzhayyim inference path (ADR-2605215000). Listed for an explicit, legible
# refusal message; the allowlist above is the actual gate.
_PROHIBITED_SUBSTRINGS = (
    "api.openai.com",
    "api.anthropic.com",
    "openai.azure.com",
    "generativelanguage.googleapis.com",
    "aiplatform.googleapis.com",
    "bedrock",
    "api.runpod",
    "api.together",
    "api.groq.com",
    "api.mistral.ai",
)


class CharterInferenceViolation(RuntimeError):
    """Raised when an LLM endpoint is not the Murakumo fleet."""


def assert_murakumo_only(base_url: str) -> None:
    """Refuse any base_url that is not the loopback gateway / LAN fleet.

    This is the ADR-2605215000 enforcement point for the e2e harness.
    """
    low = (base_url or "").lower()
    for bad in _PROHIBITED_SUBSTRINGS:
        if bad in low:
            raise CharterInferenceViolation(
                f"commercial inference endpoint '{bad}' is prohibited "
                f"(ADR-2605215000 — Murakumo fleet only): {base_url}"
            )
    host = (urlparse(base_url).hostname or "").lower()
    if host in _ALLOWED_HOSTS:
        return
    if any(host.endswith(s) for s in _ALLOWED_HOST_SUFFIXES):
        return
    if any(host.startswith(p) for p in _ALLOWED_PRIVATE_PREFIXES):
        return
    raise CharterInferenceViolation(
        f"LLM base_url host '{host}' is not a Murakumo fleet node "
        f"(loopback / *.murakumo.etzhayyim.com / private LAN only): {base_url}"
    )


def resolve_api_key() -> str:
    """KOTOBA_INFERENCE_API_KEY from env, else the macOS Keychain mirror.

    The key authorizes the loopback LiteLLM gateway (bearer). Never a commercial
    vendor key (those would be refused by assert_murakumo_only anyway).
    """
    env = os.environ.get("KOTOBA_INFERENCE_API_KEY") or os.environ.get("MURAKUMO_API_KEY")
    if env:
        return env
    try:
        out = subprocess.run(
            ["security", "find-generic-password", "-s", "etzhayyim",
             "-a", "KOTOBA_INFERENCE_API_KEY", "-w"],
            capture_output=True, text=True, timeout=10,
        )
        if out.returncode == 0 and out.stdout.strip():
            return out.stdout.strip()
    except Exception:
        pass
    # LiteLLM often accepts any bearer for loopback; fall back to a placeholder so
    # a misconfigured key surfaces as an auth error, not a silent commercial call.
    return "sk-murakumo-loopback"


def base_url() -> str:
    return os.environ.get("MURAKUMO_BASE_URL", DEFAULT_BASE_URL)


def model_name() -> str:
    return os.environ.get("MURAKUMO_MODEL", DEFAULT_MODEL)


def make_llm(*, model: str | None = None, temperature: float = 0.0):
    """Construct the browser-use / langchain chat model bound to Murakumo.

    Tries browser-use's own ChatOpenAI wrapper first (newer browser-use ships
    its own), then langchain_openai.ChatOpenAI — BOTH are OpenAI-compatible
    clients that we point at the Murakumo gateway (NOT at OpenAI). The guard runs
    before any client is built, so a misconfigured base_url can never reach a
    commercial host.
    """
    url = base_url()
    assert_murakumo_only(url)  # charter gate — runs before any network client exists
    key = resolve_api_key()
    mdl = model or model_name()

    # Prefer browser-use's native LLM (keeps version compatibility with Agent).
    try:
        from browser_use.llm import ChatOpenAI as BuChatOpenAI  # type: ignore

        return BuChatOpenAI(model=mdl, base_url=url, api_key=key, temperature=temperature)
    except Exception:
        pass
    from langchain_openai import ChatOpenAI  # type: ignore

    return ChatOpenAI(model=mdl, base_url=url, api_key=key, temperature=temperature)
