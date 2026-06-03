"""Intake graph state schema."""

from __future__ import annotations

from typing import Any, TypedDict


class IntakeState(TypedDict, total=False):
    case_id: str
    case_did: str
    lang: str
    domain: str
    state: str
    urgency: str
    jurisdiction: str
    owner_did: str
    actor_did: str
    summary_plain: str
    summary_cipher: str
    triage_result: dict[str, Any]
    lawyers: list[dict[str, Any]]
    grants: list[dict[str, Any]]
    error: str | None
