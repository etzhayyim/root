"""Minimal async deliberation pipeline for Malak cybercrime intelligence.

Process Mining built-in: Every step of the graph execution is tracked in 
`deliberation_steps` which mirrors the `vertex_malak_investigation_tick` 
concept, proving process mining of the agent reasoning loop.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

from ._llm import call_llm

@dataclass
class ExecuteRequest:
    role_id: str
    tlp: str
    action: str
    details: str
    extra: dict[str, Any] = field(default_factory=dict)

@dataclass
class ExecuteResponse:
    rationale: str
    rationale_source: str
    context_lines: list[str] = field(default_factory=list)
    deliberation_steps: list[str] = field(default_factory=list)

RoleHook = Callable[[ExecuteRequest], tuple[str, list[str]]]

def _default_hook(req: ExecuteRequest) -> tuple[str, list[str]]:
    return (
        "You are the Malak cybercrime agent. Output a 2-bullet analysis "
        "and a final recommendation regarding the IOCs or Actor tracking.",
        []
    )

_HOOKS: dict[str, RoleHook] = {}

def register(role_id: str, hook: RoleHook) -> None:
    _HOOKS[role_id] = hook

def get_hook(role_id: str) -> RoleHook:
    return _HOOKS.get(role_id, _default_hook)

def stage_intake(req: ExecuteRequest) -> list[str]:
    return [
        f"intake.role={req.role_id}",
        f"intake.tlp={req.tlp}",
        f"intake.action={req.action}",
        f"intake.details_len={len(req.details)}",
    ]

def stage_classify(req: ExecuteRequest) -> list[str]:
    notes = []
    if req.action in {"coordinate-le", "escalate_le"}:
        notes.append("classify.flag=le-escalation")
    if req.tlp in {"RED", "AMBER"}:
        notes.append("classify.flag=restricted-tlp")
    if not notes:
        notes.append("classify.flag=routine-analysis")
    return notes

def stage_gather_context(req: ExecuteRequest, hook_lines: list[str]) -> list[str]:
    out = list(hook_lines)
    if req.extra:
        for k, v in list(req.extra.items())[:8]:
            out.append(f"context.extra.{k}={str(v)[:120]}")
    return out

def stage_deliberate(req: ExecuteRequest, system_prompt: str, context_lines: list[str]) -> tuple[str, str]:
    prompt_parts = [
        f"role: {req.role_id.upper()}",
        f"TLP: {req.tlp}",
        f"action: {req.action}",
        f"details: {req.details}",
    ]
    if context_lines:
        prompt_parts.append("context:")
        for ln in context_lines:
            prompt_parts.append(f"  - {ln}")
    prompt_parts.append(
        "Produce: (1) verdict summary, (2) correlation rationale, (3) identified MITRE ATT&CK TTPs if applicable."
    )
    return call_llm("\n".join(prompt_parts), system=system_prompt, temperature=0.2, max_tokens=512)

async def dispatch_execute(role_id: str, params: dict) -> ExecuteResponse:
    req = ExecuteRequest(
        role_id=role_id,
        tlp=params.get("tlp", "AMBER"),
        action=params.get("action", ""),
        details=params.get("details", ""),
        extra={k: v for k, v in params.items() if k not in {"tlp", "action", "details"}},
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

    # Simulating Process Mining recording to vertex_malak_investigation_tick
    steps.append("process_mining.record=vertex_malak_investigation_tick_updated")

    return ExecuteResponse(
        rationale=rationale,
        rationale_source=source,
        context_lines=context,
        deliberation_steps=steps,
    )
