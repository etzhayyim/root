"""revision.py — 朱 (ake) append-only revision history. ADR-2606052100.

The "view history" tab, as data. Every accepted edit APPENDS one revision datom; nothing is
ever overwritten or deleted (G5, 非終末論). The latest `as-of` for an (entity, attr) is the
current value; the full ordered stream is the history. A `:promote-sourcing` op appends a new
authoritative revision and LEAVES the prior representative one in place (both remain, at their
own `as-of`).

Every mutating helper RETURNS A NEW LIST — it never mutates its input — so a caller can never
shrink the log. `current(...)` / `as_of(...)` / `history_of(...)` are the read side.

Stdlib only.
"""

from __future__ import annotations

from typing import Any

from triage import _kw, _verifiable_provenance


def _rev(entity: str, attr: str, value: str, sourcing: str, as_of: int, by: str,
         op: str, edit_id: str) -> dict:
    return {
        ":revision/entity": entity,
        ":revision/attr": attr,
        ":revision/value": value,
        ":revision/sourcing": ":" + _kw(sourcing) if sourcing else ":representative",
        ":revision/as-of": int(as_of),
        ":revision/by": by,
        ":revision/op": ":" + _kw(op),
        ":revision/edit": edit_id,
    }


def append_revision(history: list[dict], edit: dict, as_of: int) -> list[dict]:
    """Append a revision for an accepted edit. Returns a NEW list (G5 — never mutates/shrinks)."""
    rev = _rev(
        entity=edit.get(":edit/target-entity", "?"),
        attr=_kw(edit.get(":edit/target-attr", "")),
        value=str(edit.get(":edit/proposed-value", "")),
        sourcing=edit.get(":edit/sourcing", ":representative"),
        as_of=as_of,
        by=edit.get(":edit/author", "?"),
        op=edit.get(":edit/op", ":assert"),
        edit_id=edit.get(":edit/id", "?"),
    )
    return list(history) + [rev]


def promote_sourcing(history: list[dict], entity: str, attr: str, provenance: str,
                     as_of: int, by: str, edit_id: str) -> list[dict]:
    """Promote the current value of (entity, attr) :representative → :authoritative (G4).

    Appends a NEW authoritative revision carrying the current value; the prior representative
    revision is left untouched (non-destructive). Raises if provenance is not verifiable, or if
    there is no current value to promote.
    """
    if not _verifiable_provenance(provenance):
        raise ValueError("G4: promotion to :authoritative requires verifiable provenance (URL/CID)")
    cur = current(history, entity, _kw(attr))
    if cur is None:
        raise ValueError(f"nothing to promote: no current revision for {entity}:{_kw(attr)}")
    rev = _rev(entity, _kw(attr), cur.get(":revision/value", ""), ":authoritative",
               as_of, by, ":promote-sourcing", edit_id)
    return list(history) + [rev]


def history_of(history: list[dict], entity: str, attr: str) -> list[dict]:
    """Full ordered revision history for (entity, attr) — the 'view history' tab."""
    attr = _kw(attr)
    rows = [r for r in history
            if r.get(":revision/entity") == entity and _kw(r.get(":revision/attr", "")) == attr]
    return sorted(rows, key=lambda r: int(r.get(":revision/as-of", 0)))


def as_of(history: list[dict], entity: str, attr: str, ts: int) -> dict | None:
    """The value of (entity, attr) as it stood at instant `ts` (time-travel read)."""
    rows = [r for r in history_of(history, entity, attr) if int(r.get(":revision/as-of", 0)) <= ts]
    return rows[-1] if rows else None


def current(history: list[dict], entity: str, attr: str) -> dict | None:
    """The latest revision for (entity, attr)."""
    rows = history_of(history, entity, attr)
    return rows[-1] if rows else None
