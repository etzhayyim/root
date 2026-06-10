"""Phase state machine for the tedai evidence_audit (手代) cell.

Graph: hash-evidence -> project-datoms -> assemble-batch. The G7/G9 leg: screen evidence enters
the audit trail ONLY as a sha256 hash (the raw frame stays on-device under the member's key), every
DesktopOp becomes a kotoba Datom entity, and the assembled batch is dry-run — live ingest is
operator-gated in methods/datom.py.

G7 (every op is a Datom, as-of, replayable) · G9 (hash-only evidence; flag keys never values) ·
G6 (live ingest operator-gated downstream).
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

from datom import evidence_hash, ingest_batch, op_entity  # noqa: E402
from desktop import DesktopOp  # noqa: E402


class AuditPhase(Enum):
    INIT = "init"
    EVIDENCE_HASHED = "evidence_hashed"
    PROJECTED = "projected"
    ASSEMBLED = "assembled"


@dataclass
class AuditState:
    phase: str = AuditPhase.INIT.value
    ops: list = field(default_factory=list)          # DesktopOp dicts
    planned_at: str = ""                              # caller-stamped; the cell reads no clock
    evidence_sha256: str = ""
    payload: dict = field(default_factory=dict)


def _state(d: dict[str, Any]) -> AuditState:
    return AuditState(**d.get("cell_state", {}))


def transition_hash_evidence(state: dict[str, Any]) -> dict[str, Any]:
    """G9: reduce any frame bytes to a sha256 immediately; the raw frame is never carried forward."""
    cs = _state(state)
    cs.ops = list(state.get("ops", cs.ops))
    cs.planned_at = state.get("planned_at", cs.planned_at)
    if not cs.ops:
        raise ValueError("evidence_audit: no ops supplied")
    if not cs.planned_at:
        raise ValueError("evidence_audit: planned_at must be caller-stamped (no clock reads here)")
    frame = state.get("frame_bytes")
    if frame is not None:
        cs.evidence_sha256 = evidence_hash(frame)    # the boundary: bytes in, hash out, nothing kept
    cs.phase = AuditPhase.EVIDENCE_HASHED.value
    return {"cell_state": cs.__dict__, "next_node": "project_datoms"}


def transition_project_datoms(state: dict[str, Any]) -> dict[str, Any]:
    """G7: project every op into a kotoba EAVT entity map (refusing gate-value drift)."""
    cs = _state(state)
    entities = [
        op_entity(DesktopOp(**op_dict), cs.planned_at,
                  evidence_sha256=cs.evidence_sha256 or None)
        for op_dict in cs.ops
    ]
    cs.payload["entities"] = entities
    cs.phase = AuditPhase.PROJECTED.value
    return {"cell_state": cs.__dict__, "next_node": "assemble_batch"}


def transition_assemble_batch(state: dict[str, Any]) -> dict[str, Any]:
    """Assemble the kg.ingest_batch body; live ingest stays operator-gated (G6, methods/datom.py)."""
    cs = _state(state)
    cs.payload["batch"] = ingest_batch(cs.payload["entities"])
    cs.payload["liveIngest"] = False                 # G6: dry-run; ingest_live() is the gated path
    cs.phase = AuditPhase.ASSEMBLED.value
    return {"cell_state": cs.__dict__, "next_node": "end"}
