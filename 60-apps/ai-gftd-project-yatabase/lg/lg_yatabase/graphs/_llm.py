"""Guarded LLM caller for yatabase marketing + sales graphs.

When GFTD_LLM_API_KEY is set, POST to GFTD_LLM_URL with a tight JSON
schema instruction and parse the structured response. When the key is
absent or the call fails for any reason, return the caller's
deterministic fallback. The graph is always functional — LLM is an
augmentation layer, never a hard dependency.

Both marketing scoring and sales decision selection use this; the
shape is intentionally narrow (no streaming, no tools, no retries) so
LLM downtime never blocks the cron.
"""

from __future__ import annotations

import json
import logging
import os
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any

_log = logging.getLogger(__name__)

_LLM_URL = os.environ.get(
    "GFTD_LLM_URL",
    "https://gemma-e2b.etzhayyim.com/v1/chat/completions",
)
_LLM_KEY = os.environ.get("GFTD_LLM_API_KEY", "")
_LLM_MODEL = os.environ.get(
    "YATABASE_LLM_MODEL",
    os.environ.get("GFTD_LLM_MODEL", "gemma-4-E2B-it"),
)
_LLM_TIMEOUT = float(os.environ.get("YATABASE_LLM_TIMEOUT_SEC", "15"))


@dataclass
class LLMScore:
    score: int
    reasoning: str
    source: str  # "llm" / "fallback-no-key" / "fallback-error:<cls>"


def _http_post(url: str, headers: dict[str, str], body: dict[str, Any], timeout: float) -> dict[str, Any]:
    req = urllib.request.Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def call_llm_json(prompt: str, *, system: str = "", max_tokens: int = 256,
                  temperature: float = 0.1) -> tuple[dict[str, Any] | None, str]:
    """Return (parsed_json_dict_or_None, source).

    `source` is one of "llm" / "fallback-no-key" / "fallback-error:<cls>"
    / "fallback-non-json". Caller uses `source` to decide whether to log
    a degraded-LLM warning."""
    if not _LLM_KEY:
        return None, "fallback-no-key"
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    try:
        resp = _http_post(
            _LLM_URL,
            headers={
                "Authorization": f"Bearer {_LLM_KEY}",
                "Content-Type": "application/json",
            },
            body={
                "model": _LLM_MODEL,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "response_format": {"type": "json_object"},
            },
            timeout=_LLM_TIMEOUT,
        )
        choices = resp.get("choices") or []
        if not choices:
            return None, "fallback-empty-choices"
        content = choices[0].get("message", {}).get("content") or ""
        try:
            parsed = json.loads(content)
            if not isinstance(parsed, dict):
                return None, "fallback-non-json"
            return parsed, "llm"
        except json.JSONDecodeError:
            return None, "fallback-non-json"
    except urllib.error.URLError as e:
        return None, f"fallback-error:{type(e).__name__}"
    except (TimeoutError, KeyError) as e:
        return None, f"fallback-error:{type(e).__name__}"


# ---------------------------------------------------------------------------
# Marketing scoring.
# ---------------------------------------------------------------------------

def score_lead(lead: dict, *, segment: str) -> LLMScore:
    """Return a 0-100 fit score with one-line reasoning."""
    system = (
        "You are yatabase.etzhayyim.com's nishino lead-scorer. Score 0-100 how good "
        "a fit a lead is for yatabase (graph DB + storage + auth + MCP SaaS). "
        "ICP segments: dev-tooling-saas (Supabase/Hasura/Neo4j users), "
        "data-team-mid-market (50-500 emp data teams), bsky-builders "
        "(AT-Protocol devs), jp-saas-founders (JP SaaS startups). "
        "Output JSON: {\"score\": int 0-100, \"reasoning\": \"<= 1 sentence\"}. "
        "Be conservative: default 30 if signal is thin."
    )
    prompt = (
        f"Lead JSON:\n```\n{json.dumps({k: lead.get(k) for k in ('company','domain','tech_stack','signal','employees')}, ensure_ascii=False)}\n```\n"
        f"Classified ICP segment: {segment}\n\n"
        "Return ONLY the JSON object."
    )
    parsed, source = call_llm_json(prompt, system=system, max_tokens=128)
    if parsed is None:
        return LLMScore(score=_heuristic_score(lead, segment),
                        reasoning=f"heuristic ({source})", source=source)
    try:
        s = int(parsed.get("score", 0))
        s = max(0, min(100, s))
        r = str(parsed.get("reasoning", ""))[:240]
        return LLMScore(score=s, reasoning=r, source=source)
    except (TypeError, ValueError):
        return LLMScore(score=_heuristic_score(lead, segment),
                        reasoning="heuristic (fallback-bad-score-type)",
                        source="fallback-bad-score-type")


def _heuristic_score(lead: dict, segment: str) -> int:
    """Deterministic fallback when LLM is unreachable.

    Coarse but defensible: bsky-builders + dev-tooling-saas score highest
    because that's our wedge today; jp-saas-founders next; data-team-mid-
    market third; unknown gets a floor.
    """
    base = {
        "bsky-builders": 70,
        "dev-tooling-saas": 65,
        "jp-saas-founders": 55,
        "data-team-mid-market": 50,
        "unknown": 30,
    }.get(segment, 30)

    # Signal text bumps
    signal = (lead.get("signal") or "").lower()
    if any(k in signal for k in ("starred", "issue opened", "imported", "evaluating")):
        base += 10
    # Contact email present → reduce friction
    if (lead.get("contact_email") or "").strip():
        base += 5
    # Tech stack richness
    stack = (lead.get("tech_stack") or "")
    if len(stack.split(",")) >= 3:
        base += 5
    return max(0, min(100, base))


# ---------------------------------------------------------------------------
# Sales decision (LLM-augmented).
# ---------------------------------------------------------------------------

DecisionLiteral = str  # mirrors graphs.sales.DecisionLiteral but avoid circular import


def decide_sales_action(org_state: dict, *, default: DecisionLiteral) -> tuple[DecisionLiteral, str, str]:
    """Return (decision, reasoning, source).

    Source is "llm" or one of the fallback markers. Default is the
    deterministic policy's choice — used when LLM is unreachable OR
    when LLM picks something outside the allowed enum.
    """
    allowed = {"do_nothing", "send_onboarding", "send_usage_recap",
               "send_upgrade", "book_call", "escalate_human"}
    system = (
        "You are nishino, the yatabase sales agent. Pick one decision from the "
        "allowed enum based on the org's compact state JSON. Output JSON: "
        "{\"decision\": str, \"reasoning\": \"<= 1 sentence\"}. Allowed enum: "
        + ", ".join(sorted(allowed))
        + ". Policy: incident_count_24h>0 → do_nothing. last_touch <7d → "
        "do_nothing. usage=0 + no prior touch → send_onboarding. "
        "plan='free' AND usage>800/d → send_upgrade. paid + churn risk → "
        "escalate_human. Default → do_nothing."
    )
    prompt = (
        f"Org state JSON:\n```\n{json.dumps({k: org_state.get(k) for k in ('plan','signup_at','usage_24h','usage_30d','last_touch_at','last_touch_kind','incident_count_24h')}, ensure_ascii=False)}\n```\n"
        "Return ONLY the JSON object."
    )
    parsed, source = call_llm_json(prompt, system=system, max_tokens=96)
    if parsed is None:
        return default, f"deterministic policy ({source})", source
    decision = str(parsed.get("decision", "")).strip()
    if decision not in allowed:
        return default, f"deterministic policy (llm picked invalid {decision!r})", "fallback-invalid-enum"
    reasoning = str(parsed.get("reasoning", ""))[:240] or "(no reasoning)"
    return decision, reasoning, source
