"""Lock the datomic read path to the live-verified kotoba pull shape.

kotoba's datomic.pull returns ``datoms`` as dicts with ``a`` (attribute, leading
colon), ``v_edn`` (EDN-encoded value string), and ``added`` (bool) — exactly the
shape lg_yatabase/kotoba_datomic.py:_datoms_to_entity consumes. These tests feed
that real shape through our reader + the canonical event reconstruction, so the
KotobaCalendarStore read path is verified against the documented contract (not a
guessed shape), without needing a live pod.
"""

from __future__ import annotations

from lg_calendar import mapping
from lg_calendar.kotoba_datomic import datoms_to_attr_map


def _datom(a: str, v_edn: str, added: bool = True) -> dict:
    return {"e": "cal:event:slug01", "a": a, "v_edn": v_edn, "added": added}


def test_datoms_to_attr_map_uses_a_and_v_edn() -> None:
    datoms = [
        _datom(":cal/type", '"Event"'),
        _datom(":cal/id", '"cal:event:slug01"'),
        _datom(":cal/slug", '"slug01"'),
        _datom(":cal/summary", '"Standup"'),
        _datom(":cal/startsAt", '"2026-06-02T09:00:00Z"'),
        _datom(":cal/allDay", "false"),
        _datom(":cal/sequence", "3"),
        _datom(":cal/createdAtMs", "1764662400000"),
        # a retraction must be ignored
        _datom(":cal/summary", '"OldTitle"', added=False),
    ]
    attrs = datoms_to_attr_map(datoms)
    assert attrs is not None
    assert attrs["cal/summary"] == "Standup"          # bare key, leading colon stripped
    assert attrs["cal/startsAt"] == "2026-06-02T09:00:00Z"
    assert attrs["cal/allDay"] is False               # EDN false → bool
    assert attrs["cal/sequence"] == 3                 # EDN int → int
    assert attrs["cal/createdAtMs"] == 1764662400000


def test_datoms_roundtrip_to_canonical_event_with_json_attendees() -> None:
    # attendees are stored as a JSON string in :cal/attendeesJson; its EDN form
    # escapes the inner quotes — verify the full decode path reconstructs the list.
    attendees_json = '[{"email":"a@x.com","responseStatus":"accepted"}]'
    v_edn = '"' + attendees_json.replace("\\", "\\\\").replace('"', '\\"') + '"'
    datoms = [
        _datom(":cal/slug", '"slug01"'),
        _datom(":cal/id", '"cal:event:slug01"'),
        _datom(":cal/summary", '"Party"'),
        _datom(":cal/startsAt", '"2026-06-02T09:00:00Z"'),
        _datom(":cal/visibility", '"private"'),
        _datom(":cal/attendeesJson", v_edn),
    ]
    attrs = datoms_to_attr_map(datoms)
    event = mapping.attrs_to_event(attrs)
    assert event["did"] == "did:web:calendar.gftd.ai:event:slug01"
    assert event["summary"] == "Party"
    assert event["attendees"] == [{"email": "a@x.com", "responseStatus": "accepted"}]


def test_empty_datoms_is_none() -> None:
    assert datoms_to_attr_map([]) is None
