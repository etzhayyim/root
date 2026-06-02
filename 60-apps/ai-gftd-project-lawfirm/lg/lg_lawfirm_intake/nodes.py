"""Intake triage + bengoshi matching nodes.

Flow: triage_node → summarize_node → search_node → match_node

triage_node   — LLM classify domain / urgency / specialization from summary
summarize_node — encrypt summary with signal:v1: prefix (ADR-0018 Stage 1)
search_node   — GET bengoshi.etzhayyim.com searchLawyers by jurisdiction + specialization
match_node    — POST inviteExternalCounsel for top-3 matched lawyers
"""

from __future__ import annotations

import base64
import json
import logging
import os
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

from lg_lawfirm_intake.state import IntakeState  # type: ignore[import-untyped]

_log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

_LLM_URL = os.environ.get("etzhayyim_LLM_URL", "https://gemma-e4b.etzhayyim.com/v1/chat/completions")
_LLM_KEY = os.environ.get("etzhayyim_LLM_API_KEY", "")
_LLM_MODEL = os.environ.get("LAWFIRM_LLM_MODEL", os.environ.get("etzhayyim_LLM_MODEL", "gemma-4-E4B-it"))
_LLM_TIMEOUT = float(os.environ.get("LAWFIRM_LLM_TIMEOUT_SEC", "20"))

_BENGOSHI_URL = os.environ.get("BENGOSHI_URL", "https://bengoshi.etzhayyim.com")
_DISPATCHER_URL = os.environ.get("DISPATCHER_URL", "https://dispatcher.etzhayyim.com")
_INTERNAL_SECRET = os.environ.get("DISPATCHER_INTERNAL_SECRET", "")

_INVITE_LIMIT = int(os.environ.get("LAWFIRM_INVITE_LIMIT", "3"))
_INVITE_EXPIRES_DAYS = int(os.environ.get("LAWFIRM_INVITE_EXPIRES_DAYS", "90"))

# ---------------------------------------------------------------------------
# HTTP helpers
# ---------------------------------------------------------------------------

def _http_get(url: str, params: dict[str, str] | None = None) -> dict[str, Any]:
    if params:
        url = url + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=10) as r:
        return json.loads(r.read().decode("utf-8"))


def _http_post(
    url: str,
    body: dict[str, Any],
    *,
    headers: dict[str, str] | None = None,
    timeout: float = 15,
) -> dict[str, Any]:
    h = {"Content-Type": "application/json"}
    if headers:
        h.update(headers)
    req = urllib.request.Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        headers=h,
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def _internal_headers() -> dict[str, str]:
    h: dict[str, str] = {}
    if _INTERNAL_SECRET:
        h["x-internal-trust"] = _INTERNAL_SECRET
    return h


# ---------------------------------------------------------------------------
# LLM helper (guarded — fallback when key absent or call fails)
# ---------------------------------------------------------------------------

_TRIAGE_SYSTEM = (
    "You are a legal intake triage assistant for lawfirm.etzhayyim.com.\n"
    "Given a client complaint in any language, classify it and return JSON:\n"
    '{"domain": "<one of: ni138|land|family|consumer|labour|corporate|tax|criminal|rera|fema|pil-rti|visa|other>",\n'
    ' "urgency": "<routine|urgent|ex-parte>",\n'
    ' "specializations": ["<csv tokens from: labor,contract,family,ip,criminal,tax,land,corporate,consumer,immigration,other>"],\n'
    ' "jurisdiction": "<ISO 3166-1 alpha-3 or ISO 3166-2, infer from state/lang/context>",\n'
    ' "summary_en": "<1-2 sentence English summary, no PII>"}\n'
    "Reply ONLY with the JSON object. Default urgency=routine when unclear."
)


def _call_triage_llm(summary: str, lang: str, domain_hint: str) -> dict[str, Any] | None:
    if not _LLM_KEY:
        return None
    prompt = (
        f"Client language: {lang}\n"
        f"Domain hint: {domain_hint or 'unknown'}\n"
        f"Complaint: {summary[:800]}\n\nReturn ONLY the JSON object."
    )
    try:
        resp = _http_post(
            _LLM_URL,
            body={
                "model": _LLM_MODEL,
                "messages": [
                    {"role": "system", "content": _TRIAGE_SYSTEM},
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.1,
                "max_tokens": 256,
                "response_format": {"type": "json_object"},
            },
            headers={"Authorization": f"Bearer {_LLM_KEY}", "Content-Type": "application/json"},
            timeout=_LLM_TIMEOUT,
        )
        content = (resp.get("choices") or [{}])[0].get("message", {}).get("content", "")
        parsed = json.loads(content)
        if not isinstance(parsed, dict):
            return None
        return parsed
    except (urllib.error.URLError, TimeoutError, KeyError, json.JSONDecodeError) as exc:
        _log.warning("[triage_node] llm call failed: %s", exc)
        return None


def _fallback_triage(domain_hint: str) -> dict[str, Any]:
    domain = domain_hint if domain_hint in {
        "ni138", "land", "family", "consumer", "labour", "corporate",
        "tax", "criminal", "rera", "fema", "pil-rti", "visa",
    } else "other"
    return {
        "domain": domain,
        "urgency": "routine",
        "specializations": ["contract"],
        "jurisdiction": "IND",
        "summary_en": "(triage unavailable — LLM key not configured)",
    }


# ---------------------------------------------------------------------------
# signal:v1: encryption (ADR-0018 Stage 1 — base64 envelope)
# ---------------------------------------------------------------------------

def _signal_v1_encrypt(plaintext: str) -> str:
    encoded = base64.b64encode(plaintext.encode("utf-8")).decode("ascii")
    return f"signal:v1:{encoded}"


# ---------------------------------------------------------------------------
# Nodes
# ---------------------------------------------------------------------------

async def triage_node(state: IntakeState) -> dict:
    """Classify intake by domain, urgency, and specialization using LLM."""
    summary = state.get("summary_plain") or ""
    lang = state.get("lang") or "en"
    domain_hint = state.get("domain") or ""

    result = _call_triage_llm(summary, lang, domain_hint) or _fallback_triage(domain_hint)

    update: dict[str, Any] = {"triage_result": result}
    if not state.get("domain") and result.get("domain"):
        update["domain"] = result["domain"]
    if not state.get("urgency") and result.get("urgency"):
        update["urgency"] = result["urgency"]
    if not state.get("jurisdiction") and result.get("jurisdiction"):
        update["jurisdiction"] = result["jurisdiction"]
    return update


async def summarize_node(state: IntakeState) -> dict:
    """Encrypt plaintext summary with signal:v1: prefix (ADR-0018 Stage 1)."""
    plain = state.get("summary_plain") or ""
    if not plain:
        return {}
    triage = state.get("triage_result") or {}
    summary_en = triage.get("summary_en") or plain[:200]
    cipher = _signal_v1_encrypt(summary_en)
    return {"summary_cipher": cipher}


async def search_node(state: IntakeState) -> dict:
    """Search bengoshi.etzhayyim.com for verified lawyers matching jurisdiction + specialization."""
    jurisdiction = state.get("jurisdiction") or "IND"
    triage = state.get("triage_result") or {}
    specializations: list[str] = triage.get("specializations") or []
    specialization = specializations[0] if specializations else ""

    params: dict[str, str] = {
        "jurisdiction": jurisdiction,
        "limit": "10",
        "offset": "0",
    }
    if specialization:
        params["specialization"] = specialization

    try:
        resp = _http_get(
            f"{_BENGOSHI_URL}/xrpc/com.etzhayyim.apps.bengoshi.searchLawyers",
            params=params,
        )
        lawyers: list[dict] = resp.get("lawyers") or []
        return {"lawyers": lawyers[:_INVITE_LIMIT]}
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        _log.warning("[search_node] bengoshi search failed: %s", exc)
        return {"lawyers": []}


async def match_node(state: IntakeState) -> dict:
    """Send inviteExternalCounsel for the top matched lawyers."""
    lawyers: list[dict] = state.get("lawyers") or []
    case_did = state.get("case_did") or ""
    if not lawyers or not case_did:
        _log.info("[match_node] skip — no lawyers (%d) or no case_did", len(lawyers))
        return {"grants": []}

    import datetime

    expires_at = (
        datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=_INVITE_EXPIRES_DAYS)
    ).strftime("%Y-%m-%dT%H:%M:%SZ")

    grants: list[dict] = []
    for lawyer in lawyers[:_INVITE_LIMIT]:
        grantee_did = lawyer.get("did") or ""
        if not grantee_did:
            continue
        try:
            resp = _http_post(
                f"{_DISPATCHER_URL}/xrpc/com.etzhayyim.apps.lawfirm.inviteExternalCounsel",
                body={
                    "matterDid": case_did,
                    "granteeDid": grantee_did,
                    "granteeHandle": lawyer.get("fullName") or "",
                    "role": "advisory",
                    "capabilities": ["read", "comment", "propose"],
                    "expiresAt": expires_at,
                    "message": "Intake case requires legal consultation. Please review.",
                },
                headers=_internal_headers(),
            )
            grants.append({
                "granteeDid": grantee_did,
                "grantDid": resp.get("grantDid"),
                "grantUri": resp.get("grantUri"),
                "conflictCheckPassed": resp.get("conflictCheckPassed", True),
            })
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            _log.warning("[match_node] invite failed for %s: %s", grantee_did, exc)

    return {"grants": grants}
