"""Project classifier — LLM-driven (Phase 2) with deterministic fallback.

Phase 2 (this file): the public entrypoint :func:`classify_project` calls
:func:`classify_project_llm` (Anthropic structured output via
``pymagatama.llm.call_tier_json``) when ``MANIMANI_CLASSIFIER=llm``
(default). Falls back to :func:`classify_project_stub` when:

  - ``MANIMANI_CLASSIFIER=stub`` is set explicitly (dev / smoke tests),
  - the LLM call fails (`ok=False` from ``call_tier_json``),
  - the LLM returns JSON that doesn't validate against
    :class:`ProjectClassification`.

LLM tier defaults to ``classifier`` (cheap, structured-output-friendly).
Override with ``MANIMANI_CLASSIFIER_TIER`` env var.

Confidence floor (< 0.5) is enforced by the StateGraph node
(``graph.py:classify_project``), not here — the floor is a graph-level
policy, the classifier just reports its honest confidence.
"""

from __future__ import annotations

import json
import os
import re
from typing import Iterable

from pymagatama.manimani.state import (
    NewProjectProposal,
    ProjectClassification,
    ProjectKind,
)


# ── public entrypoint ────────────────────────────────────────────────


def classify_project(
    *,
    parsed_text: str,
    actor_did: str,
    existing_projects: Iterable[dict],
    project_hint: str | None = None,
) -> ProjectClassification:
    """Classify an intake. LLM by default; falls back to stub on failure.

    Behavior is selected at call time by ``MANIMANI_CLASSIFIER`` env:
      - "llm" (default): call Anthropic structured output, fall back to
        stub on transport / parse error.
      - "stub": deterministic Phase 1 stub (used by smoke tests).
    """

    # projectHint match short-circuits before any LLM cost.
    slug_hint = (project_hint or "").strip().lower()
    if slug_hint:
        for proj in existing_projects:
            if str(proj.get("slug") or "") == slug_hint:
                return ProjectClassification(
                    decision="existing",
                    existing_project_id=str(proj.get("vertex_id") or ""),
                    confidence=1.0,
                    rationale=f"projectHint matched existing slug={slug_hint}",
                )

    mode = (os.environ.get("MANIMANI_CLASSIFIER") or "llm").strip().lower()
    candidates = list(existing_projects)
    if mode == "stub":
        return classify_project_stub(
            parsed_text=parsed_text,
            actor_did=actor_did,
            existing_projects=candidates,
            project_hint=project_hint,
        )

    llm_result = classify_project_llm(
        parsed_text=parsed_text,
        actor_did=actor_did,
        existing_projects=candidates,
    )
    if llm_result is not None:
        return llm_result

    # LLM failed → fall back to stub. The stub returns a fresh-project
    # decision with confidence=0.0, which the graph normalizes to
    # kind=unsorted. This preserves "always make progress" behavior.
    return classify_project_stub(
        parsed_text=parsed_text,
        actor_did=actor_did,
        existing_projects=candidates,
        project_hint=project_hint,
    )


# ── Phase 2: LLM implementation ──────────────────────────────────────


_CLASSIFIER_SYSTEM = """You are the manimani project classifier.

Your task: decide whether an incoming intake belongs to an EXISTING project
in the user's workspace, or whether a NEW project should emerge.

Inputs you receive:
  - intake.parsed_text: the user's note / link / fragment
  - existing_projects: up to 20 active projects (slug, title, kind, last_intake_at)

Output a single JSON object that matches this exact shape (no extra keys,
no preamble, no code fence):

{
  "decision": "existing" | "new",
  "existing_project_id": "<vertex_id>" | null,
  "confidence": 0.0-1.0,
  "new_project_proposal": {
    "slug": "kebab-case-slug",
    "title": "Human Readable Title",
    "kind": "knowledge" | "task" | "memo" | "unsorted",
    "initial_tags": ["tag1", "tag2"]
  } | null,
  "rationale": "≤200 char explanation"
}

Rules:
  - decision="existing" REQUIRES existing_project_id (vertex_id from input).
  - decision="new" REQUIRES new_project_proposal.
  - If the intake is too short / ambiguous to classify, prefer
    decision="new" with kind="unsorted" + low confidence (<0.5). The user
    can reclassify later.
  - kind heuristic:
      "knowledge" — durable factual content, references, claims, citations
      "task"      — action items, TODOs, due dates, names of assignees
      "memo"      — short notes, inline thoughts, captures without action
      "unsorted"  — anything that doesn't clearly fit the above three
  - slug is kebab-case, ≤48 chars, ASCII letters/digits/hyphens only.
  - rationale ≤200 chars, English or the intake language."""


def classify_project_llm(
    *,
    parsed_text: str,
    actor_did: str,
    existing_projects: Iterable[dict],
) -> ProjectClassification | None:
    """Call the LLM with structured-output prompt. Returns None on failure
    (caller falls back to the stub)."""

    try:  # pragma: no cover — module is present in the runtime image
        from pymagatama.llm import call_tier_json
    except ImportError:
        return None

    tier = (os.environ.get("MANIMANI_CLASSIFIER_TIER") or "classifier").strip()
    truncated_text = (parsed_text or "")[:4000]

    candidates_compact: list[dict] = []
    for proj in list(existing_projects)[:20]:
        candidates_compact.append(
            {
                "vertex_id": str(proj.get("vertex_id") or ""),
                "slug": str(proj.get("slug") or ""),
                "title": (proj.get("title") or "")[:80],
                "kind": str(proj.get("kind") or "unsorted"),
                "last_intake_at": proj.get("last_intake_at"),
            }
        )

    user_payload = {
        "intake": {
            "actor_did": actor_did,
            "parsed_text": truncated_text,
        },
        "existing_projects": candidates_compact,
    }

    res = call_tier_json(
        tier,
        _CLASSIFIER_SYSTEM,
        json.dumps(user_payload, ensure_ascii=False),
        max_tokens=600,
        temperature=0.0,
    )
    if not res.get("ok"):
        return None
    data = res.get("data") or {}
    try:
        # Coerce LLM output (snake_case) into Pydantic model. All fields
        # except `decision`, `confidence`, `rationale` are optional.
        return ProjectClassification.model_validate(_coerce_llm_payload(data))
    except Exception:
        return None


def _coerce_llm_payload(data: dict) -> dict:
    """Be lenient about minor LLM output drift (camelCase keys, snake_case
    new_project_proposal nested keys)."""

    out = dict(data)
    # camelCase → snake_case for the top-level fields the model promised.
    if "existingProjectId" in out and "existing_project_id" not in out:
        out["existing_project_id"] = out.pop("existingProjectId")
    if "newProjectProposal" in out and "new_project_proposal" not in out:
        out["new_project_proposal"] = out.pop("newProjectProposal")
    if "initialTags" in out and "initial_tags" not in out:
        out["initial_tags"] = out.pop("initialTags")

    proposal = out.get("new_project_proposal")
    if isinstance(proposal, dict):
        if "initialTags" in proposal and "initial_tags" not in proposal:
            proposal["initial_tags"] = proposal.pop("initialTags")
    return out


# ── Phase 1 stub (kept as deterministic fallback) ────────────────────


def classify_project_stub(
    *,
    parsed_text: str,
    actor_did: str,
    existing_projects: Iterable[dict],
    project_hint: str | None = None,
) -> ProjectClassification:
    """Deterministic Phase 1 stub. Used when MANIMANI_CLASSIFIER=stub or
    the LLM path failed. Returns ``decision="new"`` + ``confidence=0.0``
    so the graph routes to ``kind=unsorted``."""

    slug_hint = (project_hint or "").strip().lower()
    if slug_hint:
        for proj in existing_projects:
            if str(proj.get("slug") or "") == slug_hint:
                return ProjectClassification(
                    decision="existing",
                    existing_project_id=str(proj.get("vertex_id") or ""),
                    confidence=1.0,
                    rationale=f"projectHint matched existing slug={slug_hint}",
                )

    slug = _slug_from_text(parsed_text) or "unsorted"
    title = _title_from_text(parsed_text) or "Unsorted"
    return ProjectClassification(
        decision="new",
        confidence=0.0,
        new_project_proposal=NewProjectProposal(
            slug=slug,
            title=title,
            kind=ProjectKind.UNSORTED,
            initial_tags=[],
        ),
        rationale="Stub fallback — LLM unavailable or MANIMANI_CLASSIFIER=stub.",
    )


# ── helpers ──────────────────────────────────────────────────────────


_STOPWORDS = frozenset(
    {
        "the", "a", "an", "and", "or", "but", "if", "of", "to", "for", "in",
        "on", "at", "by", "with", "is", "are", "was", "were", "be", "been",
        "from", "as", "that", "this", "these", "those", "it", "its", "i",
        "you", "we", "they", "he", "she",
        "を", "が", "は", "の", "に", "と", "も", "で", "へ", "や", "から",
        "まで", "より",
    }
)


def _slug_from_text(text: str) -> str | None:
    if not text:
        return None
    tokens = re.findall(r"[A-Za-z0-9]+", text.lower())
    tokens = [t for t in tokens if t and t not in _STOPWORDS]
    if not tokens:
        return None
    head = tokens[:3]
    slug = "-".join(head)[:48].strip("-")
    return slug or None


def _title_from_text(text: str) -> str | None:
    if not text:
        return None
    head = text.strip().splitlines()[0].strip()
    if len(head) > 120:
        head = head[:117] + "..."
    return head or None
