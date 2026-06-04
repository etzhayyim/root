"""Canonical event <-> :cal/* datom mapping (ADR-2606010500 D3).

A canonical event is the ``ai.gftd.apps.calendar.defs#event`` shape. In datomic
it is one entity ``cal:event:{slug}`` with ``:cal/*`` attributes; attendees and
reminders are stored as canonical JSON strings (``:cal/attendeesJson`` /
``:cal/remindersJson``) for a single-pull round-trip.
"""

from __future__ import annotations

import json
from typing import Any

from . import ids
from .edn import tx_add, tx_retract

# Scalar canonical field -> bare datomic attribute. Order is stable for tests.
SCALAR_FIELDS: dict[str, str] = {
    "iCalUid": "cal/iCalUid",
    "googleEventId": "cal/googleEventId",
    "msEventId": "cal/msEventId",
    "calendarId": "cal/calendarId",
    "summary": "cal/summary",
    "description": "cal/description",
    "startsAt": "cal/startsAt",
    "endsAt": "cal/endsAt",
    "allDay": "cal/allDay",
    "timezone": "cal/timezone",
    "location": "cal/location",
    "url": "cal/url",
    "rrule": "cal/rrule",
    "visibility": "cal/visibility",
    "status": "cal/status",
    "sequence": "cal/sequence",
    "createdAtMs": "cal/createdAtMs",
    "updatedAtMs": "cal/updatedAtMs",
    "organizerDid": "cal/organizerDid",
}
JSON_FIELDS = {"attendees": "cal/attendeesJson", "reminders": "cal/remindersJson"}

DEFAULTS = {"allDay": False, "visibility": "private", "status": "confirmed", "sequence": 0, "calendarId": "primary"}


def create_ops(slug: str, event: dict[str, Any]) -> list[list[Any]]:
    """Full asserting tx-ops for a brand-new event entity."""
    eid = ids.eid_for_slug(slug)
    ops: list[list[Any]] = [
        tx_add(eid, "cal/type", "Event"),
        tx_add(eid, "cal/id", eid),
        tx_add(eid, "cal/slug", slug),
    ]
    for field, attr in SCALAR_FIELDS.items():
        v = event.get(field, DEFAULTS.get(field))
        if v is not None:
            ops.append(tx_add(eid, attr, v))
    for field, attr in JSON_FIELDS.items():
        arr = event.get(field) or []
        if arr:
            ops.append(tx_add(eid, attr, json.dumps(arr, ensure_ascii=False, separators=(",", ":"))))
    return ops


def update_ops(slug: str, current_attrs: dict[str, Any], patch: dict[str, Any]) -> list[list[Any]]:
    """Delete-then-insert tx-ops for the changed fields only (cardinality-safe).

    Retracts the current value of each touched attribute (when present) and
    asserts the new one — avoids relying on a cardinality-one schema default.
    """
    eid = ids.eid_for_slug(slug)
    ops: list[list[Any]] = []
    for field, attr in SCALAR_FIELDS.items():
        if field not in patch:
            continue
        new_v = patch[field]
        old_v = current_attrs.get(attr)
        if old_v == new_v:
            continue
        if old_v is not None:
            ops.append(tx_retract(eid, attr, old_v))
        if new_v is not None:
            ops.append(tx_add(eid, attr, new_v))
    for field, attr in JSON_FIELDS.items():
        if field not in patch:
            continue
        new_json = json.dumps(patch[field] or [], ensure_ascii=False, separators=(",", ":"))
        old_json = current_attrs.get(attr)
        if old_json == new_json:
            continue
        if old_json is not None:
            ops.append(tx_retract(eid, attr, old_json))
        ops.append(tx_add(eid, attr, new_json))
    return ops


def attrs_to_event(attrs: dict[str, Any]) -> dict[str, Any]:
    """Reconstruct the canonical event dict from a bare ``cal/*`` attr map."""
    slug = attrs.get("cal/slug") or ids.slug_from_eid(attrs.get("cal/id", "cal:event:unknown"))
    event: dict[str, Any] = {
        "did": ids.did_for_slug(slug),
        "uri": ids.uri_for_slug(slug),
    }
    for field, attr in SCALAR_FIELDS.items():
        if attr in attrs and attrs[attr] is not None:
            event[field] = attrs[attr]
    for field, attr in JSON_FIELDS.items():
        raw = attrs.get(attr)
        if raw:
            try:
                event[field] = json.loads(raw) if isinstance(raw, str) else raw
            except (ValueError, TypeError):
                event[field] = []
    # ensure defaults surface for required-ish fields
    event.setdefault("calendarId", DEFAULTS["calendarId"])
    event.setdefault("visibility", DEFAULTS["visibility"])
    event.setdefault("status", DEFAULTS["status"])
    event.setdefault("allDay", DEFAULTS["allDay"])
    event.setdefault("sequence", DEFAULTS["sequence"])
    return event
