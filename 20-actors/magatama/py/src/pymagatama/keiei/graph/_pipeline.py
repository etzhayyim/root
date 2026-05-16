"""Minimal async deliberation pipeline shared by all role graphs.

5-stage: intake → classify → gather_context → deliberate → emit.

This is *not* langgraph — keeping zero hard deps so the resident daemon
runs on a stock python3. The five stages are explicit because audit
needs to be able to point at "where did the rationale come from" later.
A future Phase will replace this with `langgraph.graph.StateGraph` once
the daemon's launchd env carries `langgraph` + checkpointer.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

from ._llm import call_llm


@dataclass
class DecideRequest:
    role_id: str
    decision_class: str
    action_kind: str
    summary: str
    artefact: str
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class DecideResponse:
    rationale: str
    rationale_source: str            # "llm" / "fallback-*"
    context_lines: list[str] = field(default_factory=list)
    deliberation_steps: list[str] = field(default_factory=list)


# Per-role hooks: signature `(req: DecideRequest) -> tuple[system_prompt, context_lines]`
# Default hook returns a generic operating-entity prompt.
RoleHook = Callable[[DecideRequest], tuple[str, list[str]]]


def _default_hook(req: DecideRequest) -> tuple[str, list[str]]:
    return (
        "You are an AI executive officer at the amanomibashira platform "
        "(operated through Gftd Japan vendor capacity). Operating entity = "
        "amanomibashira, sole principal. Be concise (<=8 lines). Surface "
        "trade-offs, name the failure mode, recommend an action, and flag "
        "any escalation requirement.",
        [],
    )


_HOOKS: dict[str, RoleHook] = {}


def register(role_id: str, hook: RoleHook) -> None:
    _HOOKS[role_id] = hook


def get_hook(role_id: str) -> RoleHook:
    return _HOOKS.get(role_id, _default_hook)


# ---------------------------------------------------------------------------
# Stages
# ---------------------------------------------------------------------------

def stage_intake(req: DecideRequest) -> list[str]:
    return [
        f"intake.role={req.role_id}",
        f"intake.class={req.decision_class}",
        f"intake.action_kind={req.action_kind or '-'}",
        f"intake.summary_len={len(req.summary)}",
    ]


def stage_classify(req: DecideRequest) -> list[str]:
    notes = []
    if req.decision_class == "A":
        notes.append("classify.flag=class-A-blocking-escalate")
    if req.action_kind in {"spend", "wire", "payroll", "sign-legal"}:
        notes.append("classify.flag=financial-action")
    if req.action_kind in {"hire", "fire", "comp-change"}:
        notes.append("classify.flag=hr-action")
    if not notes:
        notes.append("classify.flag=routine")
    return notes


def stage_gather_context(req: DecideRequest, hook_lines: list[str]) -> list[str]:
    out = list(hook_lines)
    if req.artefact and req.artefact != "—":
        out.append(f"context.artefact={req.artefact}")
    if req.extra:
        for k, v in list(req.extra.items())[:8]:
            out.append(f"context.extra.{k}={str(v)[:120]}")
    return out


def stage_deliberate(req: DecideRequest, system_prompt: str,
                     context_lines: list[str]) -> tuple[str, str]:
    prompt_parts = [
        f"role: {req.role_id.upper()}",
        f"decision_class: {req.decision_class}",
        f"action_kind: {req.action_kind or '-'}",
        f"summary: {req.summary}",
    ]
    if context_lines:
        prompt_parts.append("context:")
        for ln in context_lines:
            prompt_parts.append(f"  - {ln}")
    prompt_parts.append(
        "Produce: (1) verdict in one sentence, (2) two-bullet rationale, "
        "(3) one-line failure-mode warning, (4) explicit escalation note "
        "if Class B in primary mode."
    )
    return call_llm("\n".join(prompt_parts), system=system_prompt,
                    temperature=0.2, max_tokens=512)


# ---------------------------------------------------------------------------
# Public dispatch
# ---------------------------------------------------------------------------

async def deliberate(role_id: str, params: dict) -> DecideResponse:
    req = DecideRequest(
        role_id=role_id,
        decision_class=params.get("class", "C"),
        action_kind=params.get("actionKind", ""),
        summary=params.get("summary", ""),
        artefact=params.get("artefact", "—"),
        extra={k: v for k, v in params.items()
               if k not in {"class", "actionKind", "summary", "artefact"}},
    )

    steps = []
    steps.extend(stage_intake(req))
    steps.extend(stage_classify(req))

    hook = get_hook(role_id)
    system_prompt, hook_ctx = hook(req)
    context = stage_gather_context(req, hook_ctx)
    steps.append(f"context.lines={len(context)}")

    rationale, source = stage_deliberate(req, system_prompt, context)
    steps.append(f"deliberate.source={source}")
    steps.append(f"deliberate.rationale_len={len(rationale)}")

    return DecideResponse(
        rationale=rationale,
        rationale_source=source,
        context_lines=context,
        deliberation_steps=steps,
    )
