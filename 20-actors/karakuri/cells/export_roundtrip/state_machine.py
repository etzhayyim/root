"""Phase state machine for the karakuri export_roundtrip (絡繰) cell.

Graph: owner-check -> format-select -> export-plan. Wires the T3 export builder (methods/export.py)
into the manifest graph. G9 own-data-only + encrypted (enforced by construction), G6 dry-run (live
pull/push gated), G7 audit-ready output.
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

_METHODS = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "methods"))
if _METHODS not in sys.path:
    sys.path.insert(0, _METHODS)

from export import (  # noqa: E402
    EXPORT_FORMATS,
    MEMBER,
    OwnerViolation,
    build_export_plan,
    verify_roundtrip,
)


class ExportPhase(Enum):
    INIT = "init"
    OWNER_OK = "owner_ok"
    FORMAT_OK = "format_ok"
    PLANNED = "planned"
    REFUSED = "refused"


@dataclass
class ExportState:
    phase: str = ExportPhase.INIT.value
    service: str = ""
    fmt: str = "kotoba-edn"
    owner: str = MEMBER
    payload: dict = field(default_factory=dict)


def _state(d: dict[str, Any]) -> ExportState:
    return ExportState(**d.get("cell_state", {}))


def transition_owner_check(state: dict[str, Any]) -> dict[str, Any]:
    """G9: refuse anything but the member's OWN data (no third-party PII)."""
    cs = _state(state)
    cs.service = state.get("service", cs.service)
    cs.owner = state.get("owner", cs.owner)
    cs.fmt = state.get("fmt", cs.fmt)
    if cs.owner != MEMBER:
        cs.phase = ExportPhase.REFUSED.value
        cs.payload["outcome"] = "g9-non-member-owner-refused"
        return {"cell_state": cs.__dict__, "next_node": "end"}
    cs.phase = ExportPhase.OWNER_OK.value
    return {"cell_state": cs.__dict__, "next_node": "format_select"}


def transition_format_select(state: dict[str, Any]) -> dict[str, Any]:
    """Select a portable export format; an unknown format is refused honestly."""
    cs = _state(state)
    if cs.fmt not in EXPORT_FORMATS:
        cs.phase = ExportPhase.REFUSED.value
        cs.payload["outcome"] = f"unknown-format:{cs.fmt}"
        return {"cell_state": cs.__dict__, "next_node": "end"}
    cs.phase = ExportPhase.FORMAT_OK.value
    return {"cell_state": cs.__dict__, "next_node": "export_plan"}


def transition_export_plan(state: dict[str, Any]) -> dict[str, Any]:
    """G6/G9: build + roundtrip-verify the encrypted, member-owned export plan (no bytes moved at R0)."""
    cs = _state(state)
    try:
        artifact = verify_roundtrip(build_export_plan(cs.service, cs.fmt, owner=cs.owner))
    except OwnerViolation:
        cs.phase = ExportPhase.REFUSED.value
        cs.payload["outcome"] = "g9-non-member-owner-refused"
        return {"cell_state": cs.__dict__, "next_node": "end"}
    cs.payload["export"] = {
        "service": artifact.service,
        "format": artifact.fmt,
        "owner": artifact.owner,             # G9 — member
        "encrypted": artifact.encrypted,      # G9 — true
        "secretRef": artifact.secret_ref,     # encrypted-envelope ref only
        "dryRun": artifact.dry_run,           # G6
        "roundtripOk": artifact.roundtrip_ok,
    }
    cs.phase = ExportPhase.PLANNED.value
    return {"cell_state": cs.__dict__, "next_node": "end"}
