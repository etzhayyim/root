"""Project-kind processors for the manimani LangGraph (ADR-2605080800
Phase 2 — real LLM implementations + skeleton fallbacks).

Each processor is a stateless function:
``(parsed_text, project_meta, *, actor_did) -> Artifact-like dict``.

Phase 2 wiring:
  - ``extract_facts``           — Anthropic structured output → ``facts_jsonl``
  - ``expand_todo``             — Anthropic structured output → ``todos_jsonl``
  - ``summarize``               — Anthropic chat → ``summary_text`` ≤280 char
  - ``defer_for_user_review``   — no LLM call, raw passthrough preserved

Tier defaults (override via ``MANIMANI_PROCESSOR_TIER_*`` env):
  - facts / todo  → tier=balanced (Anthropic Sonnet equivalent)
  - summary       → tier=fast      (Anthropic Haiku equivalent)
  - defer         → no LLM

Failure mode: every LLM-backed processor falls back to ``raw_passthrough``
when the upstream call fails (transport / parse error). The artifact row
always lands; the user can re-process with ``ai.gftd.apps.manimani.process``
once the upstream LLM recovers.
"""

from __future__ import annotations

import json
import os
from typing import Any


# ── env-driven tier resolution ───────────────────────────────────────


def _tier_for(processor: str) -> str:
    overrides = {
        "extract_facts": os.environ.get("MANIMANI_PROCESSOR_TIER_FACTS"),
        "expand_todo": os.environ.get("MANIMANI_PROCESSOR_TIER_TODO"),
        "summarize": os.environ.get("MANIMANI_PROCESSOR_TIER_SUMMARY"),
    }
    val = (overrides.get(processor) or "").strip()
    if val:
        return val
    if processor == "summarize":
        return "fast"
    return "structured"  # facts / todo


# ── extract_facts (knowledge) ────────────────────────────────────────


_FACTS_SYSTEM = """You extract atomic, verifiable facts from a user note.

Output a single JSON object (no preamble, no code fence) of this shape:

{
  "facts": [
    {
      "claim": "≤280 char declarative statement",
      "subject": "what or who the claim is about",
      "evidence": "≤140 char quote / paraphrase from the source text",
      "confidence": 0.0-1.0
    }
  ]
}

Rules:
  - Each fact must be self-contained (resolvable without external context).
  - Drop opinions, plans, and TODOs (those go to a different processor).
  - At most 12 facts. Prefer fewer, higher-quality facts over many weak ones.
  - confidence < 0.5 means "I couldn't verify this against the source"
    — drop those facts before emitting.
  - If the input has no extractable facts, return {"facts": []}."""


def extract_facts(*, parsed_text: str, project_meta: dict, actor_did: str) -> dict[str, Any]:
    text = (parsed_text or "").strip()
    if not text:
        return _passthrough(text)

    res = _llm_json(
        tier=_tier_for("extract_facts"),
        system=_FACTS_SYSTEM,
        user=text[:8000],
        max_tokens=1200,
    )
    if not res or not res.get("ok"):
        return _passthrough(text, error=res.get("error") if res else "no llm response")

    data = res.get("data") or {}
    facts = data.get("facts") if isinstance(data, dict) else None
    if not isinstance(facts, list):
        return _passthrough(text, error="LLM output missing 'facts' array")

    # Emit one JSON object per line. Filter low-confidence in the prompt
    # already; defensively re-filter here.
    lines: list[str] = []
    for f in facts:
        if not isinstance(f, dict):
            continue
        try:
            conf = float(f.get("confidence") or 0.0)
        except (TypeError, ValueError):
            conf = 0.0
        if conf < 0.5:
            continue
        line = json.dumps(
            {
                "claim": str(f.get("claim") or "").strip()[:280],
                "subject": str(f.get("subject") or "").strip()[:140],
                "evidence": str(f.get("evidence") or "").strip()[:140],
                "confidence": conf,
            },
            ensure_ascii=False,
        )
        if line.strip():
            lines.append(line)

    if not lines:
        return _passthrough(text)

    return {
        "artifact_kind": "facts_jsonl",
        "content": "\n".join(lines),
        "model_id": res.get("model"),
        "tokens_in": _usage(res, "prompt_tokens"),
        "tokens_out": _usage(res, "completion_tokens"),
        "error_text": None,
    }


# ── expand_todo (task) ───────────────────────────────────────────────


_TODO_SYSTEM = """You extract action items from a user note.

Output a single JSON object (no preamble, no code fence):

{
  "todos": [
    {
      "title": "≤120 char imperative phrasing (e.g. 'Review Q3 OKR draft')",
      "due_hint": "ISO 8601 date or null",
      "owner_hint": "name or null",
      "priority": "low" | "normal" | "high",
      "rationale": "≤80 char why this is a TODO"
    }
  ]
}

Rules:
  - Imperative voice. Drop the subject ("I will…" → "Review…").
  - Group related steps into one todo when reasonable; don't split a
    paragraph into 12 micro-tasks.
  - At most 10 todos.
  - due_hint / owner_hint may be null; do NOT invent them.
  - If there are no actionable items, return {"todos": []}."""


def expand_todo(*, parsed_text: str, project_meta: dict, actor_did: str) -> dict[str, Any]:
    text = (parsed_text or "").strip()
    if not text:
        return _passthrough(text)

    res = _llm_json(
        tier=_tier_for("expand_todo"),
        system=_TODO_SYSTEM,
        user=text[:8000],
        max_tokens=1000,
    )
    if not res or not res.get("ok"):
        return _passthrough(text, error=res.get("error") if res else "no llm response")

    data = res.get("data") or {}
    todos = data.get("todos") if isinstance(data, dict) else None
    if not isinstance(todos, list):
        return _passthrough(text, error="LLM output missing 'todos' array")

    lines: list[str] = []
    for t in todos:
        if not isinstance(t, dict):
            continue
        title = str(t.get("title") or "").strip()
        if not title:
            continue
        priority = str(t.get("priority") or "normal").strip().lower()
        if priority not in ("low", "normal", "high"):
            priority = "normal"
        line = json.dumps(
            {
                "title": title[:120],
                "due_hint": (str(t.get("due_hint")).strip()[:32] if t.get("due_hint") else None),
                "owner_hint": (str(t.get("owner_hint")).strip()[:64] if t.get("owner_hint") else None),
                "priority": priority,
                "rationale": str(t.get("rationale") or "").strip()[:80] or None,
            },
            ensure_ascii=False,
        )
        lines.append(line)

    if not lines:
        return _passthrough(text)

    return {
        "artifact_kind": "todos_jsonl",
        "content": "\n".join(lines),
        "model_id": res.get("model"),
        "tokens_in": _usage(res, "prompt_tokens"),
        "tokens_out": _usage(res, "completion_tokens"),
        "error_text": None,
    }


# ── summarize (memo) ─────────────────────────────────────────────────


_SUMMARY_SYSTEM = """You summarize a user memo into a single 280-char line.

Output the summary as plain text — no JSON, no quotes, no preamble.
Rules:
  - ≤280 chars (Twitter-length).
  - Keep the original language (Japanese stays Japanese).
  - Drop personal opinions and rhetorical flourishes; keep the gist.
  - Append up to 3 hashtags at the end (lowercase, kebab-case),
    space-separated, prefixed with '#'."""


def summarize(*, parsed_text: str, project_meta: dict, actor_did: str) -> dict[str, Any]:
    text = (parsed_text or "").strip()
    if not text:
        return _passthrough(text)

    try:  # pragma: no cover
        from pymagatama.llm import call_tier
    except ImportError:
        return _passthrough(text, error="pymagatama.llm unavailable")

    try:
        resp = call_tier(
            _tier_for("summarize"),
            _SUMMARY_SYSTEM,
            text[:8000],
            max_tokens=300,
            temperature=0.3,
        )
    except Exception as exc:  # LlmError or transport
        return _passthrough(text, error=f"summarize failed: {exc}")

    content = (resp.get("content") or "").strip()
    if not content:
        return _passthrough(text, error="empty summary")

    if len(content) > 320:
        content = content[:317].rstrip() + "..."

    return {
        "artifact_kind": "summary_text",
        "content": content,
        "model_id": resp.get("model"),
        "tokens_in": _usage(resp, "prompt_tokens"),
        "tokens_out": _usage(resp, "completion_tokens"),
        "error_text": None,
    }


# ── defer (unsorted) ─────────────────────────────────────────────────


def defer_for_user_review(*, parsed_text: str, project_meta: dict, actor_did: str) -> dict[str, Any]:
    """``kind=unsorted`` — no LLM call, raw passthrough preserved."""

    return _passthrough(parsed_text)


# ── helpers ──────────────────────────────────────────────────────────


def _llm_json(*, tier: str, system: str, user: str, max_tokens: int) -> dict | None:
    try:  # pragma: no cover
        from pymagatama.llm import call_tier_json
    except ImportError:
        return None
    return call_tier_json(
        tier,
        system,
        user,
        max_tokens=max_tokens,
        temperature=0.0,
    )


def _passthrough(text: str, *, error: str | None = None) -> dict[str, Any]:
    return {
        "artifact_kind": "raw_passthrough" if error is None else "raw_passthrough",
        "content": text,
        "model_id": None,
        "tokens_in": None,
        "tokens_out": None,
        "error_text": error,
    }


def _usage(res: dict, key: str) -> int | None:
    usage = res.get("usage") if isinstance(res, dict) else None
    if not isinstance(usage, dict):
        return None
    val = usage.get(key)
    try:
        return int(val) if val is not None else None
    except (TypeError, ValueError):
        return None


# ── routing tables (consumed by graph.py) ────────────────────────────


PROCESSOR_BY_KIND: dict[str, str] = {
    "knowledge": "extract_facts",
    "task": "expand_todo",
    "memo": "summarize",
    "unsorted": "defer_for_user_review",
}


PROCESSOR_DEFAULT_TIER: dict[str, str] = {
    "extract_facts": "structured",
    "expand_todo": "structured",
    "summarize": "fast",
    "defer_for_user_review": "fast",
}
