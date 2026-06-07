"""Canonical calendar method handlers (ai.etzhayyim.apps.calendar.*).

Storage-agnostic: each handler takes a :class:`lg_calendar.store.CalendarStore`.
The Cloudflare ``calendar-compat`` worker reshapes these canonical results into
Google Calendar v3 / Microsoft Graph JSON; the handlers themselves are the SSoT
for behavior (concurrency, not-found, pagination).
"""

from __future__ import annotations

import time
from typing import Any

from . import ids, mapping
from .edn import tx_retract_entity
from .store import CalendarStore


def _now_ms() -> int:
    return int(time.time() * 1000)


async def _resolve(store: CalendarStore, event_id: str | None, ical_uid: str | None = None):
    """Resolve (slug, attrs) from a caller id (slug/eid/DID), iCalUid, or provider id."""
    slug = ids.resolve_slug(event_id or "")
    if slug:
        attrs = await store.get_event_attrs(slug)
        if attrs:
            return slug, attrs
    for attr, val in (
        ("cal/iCalUid", ical_uid),
        ("cal/iCalUid", event_id),
        ("cal/googleEventId", event_id),
        ("cal/msEventId", event_id),
    ):
        if not val:
            continue
        found = await store.lookup_slug(attr, val)
        if found:
            attrs = await store.get_event_attrs(found)
            if attrs:
                return found, attrs
    return None, None


# ── createEvent ───────────────────────────────────────────────────────────────


async def create_event(store: CalendarStore, inp: dict[str, Any]) -> dict[str, Any]:
    slug = ids.new_slug()
    now = _now_ms()
    ical = inp.get("iCalUid") or ids.ical_uid_for_slug(slug)
    event: dict[str, Any] = {
        "calendarId": inp.get("calendarId", "primary"),
        "iCalUid": ical,
        "summary": inp["summary"],
        "startsAt": inp["startsAt"],
        "allDay": bool(inp.get("allDay", False)),
        "visibility": inp.get("visibility", "private"),
        "status": "confirmed",
        "sequence": 0,
        "createdAtMs": now,
        "updatedAtMs": now,
        "attendees": inp.get("attendees", []),
        "reminders": inp.get("reminders", []),
    }
    for opt in ("description", "endsAt", "timezone", "location", "url", "rrule",
                "googleEventId", "msEventId", "organizerDid"):
        if inp.get(opt) is not None:
            event[opt] = inp[opt]

    await store.write_ops(mapping.create_ops(slug, event))
    event["did"] = ids.did_for_slug(slug)
    event["uri"] = ids.uri_for_slug(slug)
    return {"did": event["did"], "uri": event["uri"], "iCalUid": ical, "event": event}


# ── getEvent ──────────────────────────────────────────────────────────────────


async def get_event(store: CalendarStore, params: dict[str, Any]) -> dict[str, Any]:
    slug, attrs = await _resolve(store, params.get("eventId"), params.get("iCalUid"))
    if not attrs:
        return {"found": False}
    return {"found": True, "event": mapping.attrs_to_event(attrs)}


# ── listEvents ────────────────────────────────────────────────────────────────


async def list_events(store: CalendarStore, params: dict[str, Any]) -> dict[str, Any]:
    calendar_id = params.get("calendarId", "primary")
    starts_after = params.get("startsAfter")
    starts_before = params.get("startsBefore")
    visibility = params.get("visibility")
    attendee_did = params.get("attendeeDid")
    order_by = params.get("orderBy", "startsAt")
    offset = int(params.get("offset", 0))
    limit = int(params.get("limit", 50))

    events = [mapping.attrs_to_event(a) for a in await store.all_event_attrs()]

    def keep(ev: dict[str, Any]) -> bool:
        if calendar_id and ev.get("calendarId", "primary") != calendar_id:
            return False
        s = ev.get("startsAt", "")
        if starts_after and s < starts_after:
            return False
        if starts_before and s >= starts_before:
            return False
        if visibility and ev.get("visibility") != visibility:
            return False
        if attendee_did and not any(a.get("did") == attendee_did for a in ev.get("attendees", [])):
            return False
        return True

    filtered = [e for e in events if keep(e)]
    key = "updatedAtMs" if order_by == "updatedAtMs" else "startsAt"
    filtered.sort(key=lambda e: (e.get(key) is None, e.get(key)))
    page = filtered[offset:offset + limit]
    return {"events": page, "total": len(filtered), "offset": offset, "limit": limit}


# ── updateEvent ───────────────────────────────────────────────────────────────


async def update_event(store: CalendarStore, inp: dict[str, Any]) -> dict[str, Any]:
    slug, attrs = await _resolve(store, inp.get("eventId"))
    if not attrs:
        return {"ok": False, "notFound": True}
    if "ifSequence" in inp and inp["ifSequence"] is not None:
        if attrs.get("cal/sequence") != inp["ifSequence"]:
            return {"ok": False, "conflict": True}

    patch: dict[str, Any] = {}
    for f in ("summary", "description", "startsAt", "endsAt", "allDay", "timezone",
              "location", "url", "rrule", "visibility", "status", "attendees", "reminders"):
        if f in inp and inp[f] is not None:
            patch[f] = inp[f]
    patch["sequence"] = int(attrs.get("cal/sequence", 0)) + 1
    patch["updatedAtMs"] = _now_ms()

    await store.write_ops(mapping.update_ops(slug, attrs, patch))
    new_attrs = await store.get_event_attrs(slug) or attrs
    return {"ok": True, "event": mapping.attrs_to_event(new_attrs)}


# ── deleteEvent ───────────────────────────────────────────────────────────────


async def delete_event(store: CalendarStore, inp: dict[str, Any]) -> dict[str, Any]:
    slug, attrs = await _resolve(store, inp.get("eventId"))
    if not attrs:
        return {"ok": False, "notFound": True}
    if "ifSequence" in inp and inp["ifSequence"] is not None:
        if attrs.get("cal/sequence") != inp["ifSequence"]:
            return {"ok": False, "conflict": True}
    await store.write_ops([tx_retract_entity(ids.eid_for_slug(slug))])
    return {"ok": True}


# ── rsvp ──────────────────────────────────────────────────────────────────────


async def rsvp(store: CalendarStore, inp: dict[str, Any]) -> dict[str, Any]:
    slug, attrs = await _resolve(store, inp.get("eventId"))
    if not attrs:
        return {"ok": False, "notFound": True}
    event = mapping.attrs_to_event(attrs)
    attendees: list[dict[str, Any]] = event.get("attendees", [])
    respondent_did = inp.get("respondentDid")
    respondent_email = inp.get("respondentEmail")
    response = inp["response"]

    matched = False
    for a in attendees:
        if (respondent_did and a.get("did") == respondent_did) or (
            respondent_email and a.get("email") == respondent_email
        ):
            a["responseStatus"] = response
            matched = True
            break
    if not matched:
        attendees.append({
            "did": respondent_did,
            "email": respondent_email,
            "responseStatus": response,
        })

    patch = {"attendees": attendees, "sequence": int(attrs.get("cal/sequence", 0)) + 1, "updatedAtMs": _now_ms()}
    await store.write_ops(mapping.update_ops(slug, attrs, patch))
    return {"ok": True, "eventId": slug, "response": response}


# ── listCalendars ─────────────────────────────────────────────────────────────


async def list_calendars(store: CalendarStore, params: dict[str, Any]) -> dict[str, Any]:
    # Reference impl exposes a single synthetic 'primary' calendar per owner.
    # A future increment models calendars as their own :cal/type "Calendar" entities.
    offset = int(params.get("offset", 0))
    limit = int(params.get("limit", 50))
    calendars = [{
        "calendarId": "primary",
        "summary": "Primary",
        "primary": True,
        "accessRole": "owner",
    }]
    page = calendars[offset:offset + limit]
    return {"calendars": page, "total": len(calendars), "offset": offset, "limit": limit}
