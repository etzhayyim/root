"""Phase state machine for the 朱 (ake) revision_log cell — the append-only history projection.

The 'view history' tab, as a cell. A cleared promotion APPENDS one revision; the cell guarantees
the history only ever GROWS (G5 — never overwrite, never delete; 非終末論). Reuses
methods/revision.py so the append/read semantics are a single source of truth.
"""
from __future__ import annotations

import pathlib
import sys
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

_METHODS = pathlib.Path(__file__).resolve().parents[2] / "methods"
if str(_METHODS) not in sys.path:
    sys.path.insert(0, str(_METHODS))
from revision import append_revision, current, history_of  # noqa: E402


class RevisionPhase(Enum):
    INIT = "init"
    APPENDED = "appended"
    REFUSED = "refused"


@dataclass
class RevisionState:
    phase: str = RevisionPhase.INIT.value
    history: list = field(default_factory=list)
    edit: dict = field(default_factory=dict)
    as_of: int = 0
    refusal: str = ""
    payload: dict = field(default_factory=dict)


def _state(d: dict[str, Any]) -> RevisionState:
    return RevisionState(**d.get("cell_state", {}))


def append(state: dict[str, Any]) -> dict[str, Any]:
    cs = _state(state)
    cs.history = list(state.get("history", cs.history))
    cs.edit = dict(state.get("edit", cs.edit))
    cs.as_of = int(state.get("as_of", cs.as_of))

    before = len(cs.history)
    cs.history = append_revision(cs.history, cs.edit, cs.as_of)
    if len(cs.history) != before + 1:   # defensive: append must only ever grow by one
        cs.refusal = "G5: revision log must grow by exactly one (append-only)"
        cs.phase = RevisionPhase.REFUSED.value
        return {"cell_state": cs.__dict__}

    entity = cs.edit.get(":edit/target-entity", "?")
    attr = str(cs.edit.get(":edit/target-attr", "")).lstrip(":").split("/")[-1]
    cur = current(cs.history, entity, attr)
    cs.payload = {
        "entity": entity, "attr": attr,
        "current": (cur or {}).get(":revision/value", ""),
        "sourcing": (cur or {}).get(":revision/sourcing", ":representative"),
        "revisions": len(history_of(cs.history, entity, attr)),
        "asOf": cs.as_of,
    }
    cs.refusal = ""
    cs.phase = RevisionPhase.APPENDED.value
    return {"cell_state": cs.__dict__}
