"""Yotei scheduling XRPC primitives for BPMN/LangServer."""

from __future__ import annotations

import datetime
from datetime import timezone
import decimal as _decimal
import json
import time
import uuid
from typing import Any

from pymagatama.kotoba_datomic import get_kotoba_client


YOTEI_DID = "did:web:yotei.etzhayyim.com"

COLLECTION_TABLE = {
    "calendar": "vertex_yotei_calendar",
    "availability": "vertex_yotei_availability",
    "event": "vertex_yotei_event",
    "booking": "vertex_yotei_booking",
}


def _now() -> str:
    return _dt.datetime.now(tz=_dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _today() -> str:
    return _now()[:10]


def _id(prefix: str) -> str:
    return f"{prefix}-{int(time.time() * 1000):x}-{uuid.uuid4().hex[:8]}"


def _int(v: Any, default: int, *, min_value: int = 0, max_value: int = 100_000) -> int:
    try:
        n = int(v)
    except (TypeError, ValueError):
        n = default
    return max(min_value, min(max_value, n))


def _jsonable(v: Any) -> Any:
    if isinstance(v, (_dt.datetime, _dt.date)):
        return v.isoformat()
    if isinstance(v, _decimal.Decimal):
        f = float(v)
        return int(f) if f.is_integer() else f
    return v


def _camel(key: str) -> str:
    bits = key.split("_")
    return bits[0] + "".join(b[:1].upper() + b[1:] for b in bits[1:])


def _inflate(row: dict[str, Any]) -> dict[str, Any]:
    out = dict(row)
    for k, v in row.items():
        if "_" in k and _camel(k) not in out:
            out[_camel(k)] = v
    return out


def _rows(cur: Any) -> list[dict[str, Any]]:
    cols = [d[0] for d in (cur.description or [])]
    return [_inflate({cols[i]: _jsonable(row[i]) for i in range(len(cols))}) for row in cur.fetchall()]


def _row_text(row: dict[str, Any], key: str) -> str:
    return str(row.get(key) or "")


def _base(kind: str, id_value: str, status: str = "active") -> dict[str, Any]:
    collection = f"com.etzhayyim.apps.yotei.{kind}"
    return {
        "vertex_id": f"at://{YOTEI_DID}/{collection}/{id_value}",
        "created_date": _today(),
        "sensitivity_ord": 1,
        "owner_did": YOTEI_DID,
        "rkey": id_value,
        "repo": YOTEI_DID,
        "did": YOTEI_DID,
        "collection": collection,
        "status": status,
        "id": id_value,
    }


def _insert(table: str, values: dict[str, Any]) -> None:
    get_kotoba_client().insert_row(table, values)


def _query(kind: str, where_sql: str = "", params: tuple[Any, ...] = (), order: str = "", limit: int = 100) -> list[dict[str, Any]]:
    table = COLLECTION_TABLE[kind]
    status_filter = "status NOT IN ('deleted','removed','cancelled_tombstone')"
    where = f"WHERE {status_filter}"
    if where_sql:
        where += f" AND {where_sql}"
    sql = f"SELECT * FROM {table} {where}"
    if order:
        sql += f" ORDER BY {order}"
    sql += f" LIMIT {max(1, min(limit, 500))}"
    with sync_cursor() as cur:
        cur.execute(sql, params)
        return _rows(cur)


def _update(table: str, id_value: str, values: dict[str, Any]) -> None:
    sets = ", ".join(f"{k} = %s" for k in values)
    with sync_cursor() as cur:
        cur.execute(f"UPDATE {table} SET {sets} WHERE id = %s", (*values.values(), id_value))


def task_yotei_create_calendar(name: str = "", timezone: str = "Asia/Tokyo", defaultDurationMin: Any = 30, **_: Any) -> dict[str, Any]:
    cal_id = _id("cal")
    now = _now()
    _insert("vertex_yotei_calendar", {
        **_base("calendar", cal_id, "active"),
        "owner_did_ref": YOTEI_DID,
        "name": name,
        "timezone": timezone or "Asia/Tokyo",
        "default_duration_min": _int(defaultDurationMin, 30, min_value=5, max_value=1440),
        "booking_page_enabled": True,
        "org_id": "anon",
        "user_id": "anon",
        "actor_id": YOTEI_DID,
        "created_at": now,
    })
    return {"id": cal_id, "name": name, "status": "created"}


def task_yotei_get_calendar(id: str = "", **_: Any) -> dict[str, Any]:
    rows = _query("calendar", "id = %s", (id,), limit=1)
    return rows[0] if rows else {"error": "not_found"}


def task_yotei_list_calendars(**_: Any) -> dict[str, Any]:
    rows = _query("calendar", order="created_at DESC", limit=50)
    return {"calendars": rows, "total": len(rows)}


def task_yotei_delete_calendar(id: str = "", **_: Any) -> dict[str, Any]:
    _update("vertex_yotei_calendar", id, {"status": "deleted"})
    return {"id": id, "status": "deleted"}


def task_yotei_set_availability(
    calendarId: str = "", dayOfWeek: Any = 0, startTime: str = "", endTime: str = "", specificDate: str = "", **_: Any
) -> dict[str, Any]:
    avl_id = _id("avl")
    recurring = not bool(specificDate)
    day = _int(dayOfWeek, 0, min_value=-1, max_value=6)
    _insert("vertex_yotei_availability", {
        **_base("availability", avl_id, "active"),
        "calendar_id": calendarId,
        "day_of_week": day,
        "start_time": startTime,
        "end_time": endTime,
        "specific_date": specificDate or "",
        "recurring": recurring,
        "org_id": "anon",
        "user_id": "anon",
        "actor_id": YOTEI_DID,
        "created_at": _now(),
    })
    return {"id": avl_id, "day": specificDate or str(day), "startTime": startTime, "endTime": endTime, "status": "set"}


def task_yotei_get_availability(calendarId: str = "", **_: Any) -> dict[str, Any]:
    rows = _query("availability", "calendar_id = %s", (calendarId,), order="day_of_week ASC", limit=100)
    return {"availability": rows, "total": len(rows)}


def task_yotei_remove_availability(id: str = "", **_: Any) -> dict[str, Any]:
    _update("vertex_yotei_availability", id, {"status": "removed"})
    return {"id": id, "status": "removed"}


def task_yotei_get_open_slots(calendarId: str = "", dateFrom: str = "", dateTo: str = "", durationMin: Any = 30, **_: Any) -> dict[str, Any]:
    avails = _query("availability", "calendar_id = %s", (calendarId,), limit=200)
    events = _query(
        "event",
        "calendar_id = %s AND start_at >= %s AND start_at <= %s AND status != %s",
        (calendarId, dateFrom, dateTo, "cancelled"),
        limit=500,
    )
    return {
        "calendarId": calendarId,
        "dateRange": {"from": dateFrom, "to": dateTo},
        "durationMin": _int(durationMin, 30, min_value=5, max_value=1440),
        "availabilityRules": len(avails),
        "existingEvents": len(events),
        "note": "Slot computation: client-side from availability rules minus existing events",
    }


def task_yotei_create_event(calendarId: str = "", title: str = "", startAt: str = "", endAt: str = "", location: str = "", description: str = "", **_: Any) -> dict[str, Any]:
    event_id = _id("evt")
    _insert("vertex_yotei_event", {
        **_base("event", event_id, "confirmed"),
        "calendar_id": calendarId,
        "title": title,
        "start_at": startAt,
        "end_at": endAt,
        "location": location or "",
        "description": description or "",
        "org_id": "anon",
        "user_id": "anon",
        "actor_id": YOTEI_DID,
        "created_at": _now(),
    })
    return {"id": event_id, "title": title, "status": "confirmed"}


def task_yotei_update_event(id: str = "", title: str = "", startAt: str = "", endAt: str = "", location: Any = None, description: Any = None, status: str = "", **_: Any) -> dict[str, Any]:
    rows = _query("event", "id = %s", (id,), limit=1)
    if not rows:
        return {"error": "not_found"}
    updates: dict[str, Any] = {}
    if title:
        updates["title"] = title
    if startAt:
        updates["start_at"] = startAt
    if endAt:
        updates["end_at"] = endAt
    if location is not None:
        updates["location"] = str(location)
    if description is not None:
        updates["description"] = str(description)
    if status:
        updates["status"] = status
    if updates:
        _update("vertex_yotei_event", id, updates)
    return {"id": id, "status": "updated"}


def task_yotei_cancel_event(id: str = "", **_: Any) -> dict[str, Any]:
    _update("vertex_yotei_event", id, {"status": "cancelled"})
    return {"id": id, "status": "cancelled"}


def task_yotei_list_events(calendarId: str = "", dateFrom: str = "", dateTo: str = "", **_: Any) -> dict[str, Any]:
    clauses = ["calendar_id = %s", "status != %s"]
    params: list[Any] = [calendarId, "cancelled"]
    if dateFrom:
        clauses.append("start_at >= %s")
        params.append(dateFrom)
    if dateTo:
        clauses.append("start_at <= %s")
        params.append(dateTo)
    rows = _query("event", " AND ".join(clauses), tuple(params), order="start_at ASC", limit=100)
    return {"events": rows, "total": len(rows)}


def task_yotei_get_event(id: str = "", **_: Any) -> dict[str, Any]:
    rows = _query("event", "id = %s", (id,), limit=1)
    return rows[0] if rows else {"error": "not_found"}


def task_yotei_propose_booking(calendarId: str = "", requesterDid: str = "", durationMin: Any = 30, message: str = "", preferredDates: Any = None, **_: Any) -> dict[str, Any]:
    booking_id = _id("bk")
    duration = _int(durationMin, 30, min_value=5, max_value=1440)
    slots = preferredDates if isinstance(preferredDates, list) else []
    _insert("vertex_yotei_booking", {
        **_base("booking", booking_id, "proposed"),
        "calendar_id": calendarId,
        "event_id": "",
        "requester_did": requesterDid,
        "responder_did": YOTEI_DID,
        "duration_min": duration,
        "proposed_slots": json.dumps(slots, ensure_ascii=False),
        "confirmed_slot": "",
        "message": message or "",
        "org_id": "anon",
        "user_id": "anon",
        "actor_id": YOTEI_DID,
        "created_at": _now(),
    })
    return {"id": booking_id, "status": "proposed", "durationMin": duration}


def task_yotei_confirm_booking(id: str = "", slot: Any = None, **_: Any) -> dict[str, Any]:
    rows = _query("booking", "id = %s", (id,), limit=1)
    if not rows:
        return {"error": "not_found"}
    bk = rows[0]
    slot_obj = slot if isinstance(slot, dict) else {}
    event_id = _id("evt")
    _insert("vertex_yotei_event", {
        **_base("event", event_id, "confirmed"),
        "calendar_id": _row_text(bk, "calendarId"),
        "title": f"Meeting with {_row_text(bk, 'requesterDid')}",
        "start_at": str(slot_obj.get("start") or ""),
        "end_at": str(slot_obj.get("end") or ""),
        "location": "",
        "description": f"Booking {id}",
        "org_id": "anon",
        "user_id": "anon",
        "actor_id": YOTEI_DID,
        "created_at": _now(),
    })
    _update("vertex_yotei_booking", id, {"status": "confirmed", "event_id": event_id, "confirmed_slot": json.dumps(slot_obj)})
    return {"id": id, "eventId": event_id, "status": "confirmed", "slot": slot_obj}


def task_yotei_cancel_booking(id: str = "", **_: Any) -> dict[str, Any]:
    _update("vertex_yotei_booking", id, {"status": "cancelled"})
    return {"id": id, "status": "cancelled"}


def task_yotei_list_bookings(calendarId: str = "", status: str = "", **_: Any) -> dict[str, Any]:
    clauses = ["calendar_id = %s"]
    params: list[Any] = [calendarId]
    if status:
        clauses.append("status = %s")
        params.append(status)
    rows = _query("booking", " AND ".join(clauses), tuple(params), order="created_at DESC", limit=50)
    return {"bookings": rows, "total": len(rows)}


def task_yotei_get_booking(id: str = "", **_: Any) -> dict[str, Any]:
    rows = _query("booking", "id = %s", (id,), limit=1)
    return rows[0] if rows else {"error": "not_found"}


def task_yotei_suggest_slots(calendarId: str = "", requesterDid: str = "", durationMin: Any = 30, purpose: str = "", preferredTimeOfDay: str = "", **_: Any) -> dict[str, Any]:
    avails = _query("availability", "calendar_id = %s", (calendarId,), order="day_of_week ASC", limit=3)
    duration = _int(durationMin, 30, min_value=5, max_value=1440)
    slots = []
    base_date = _dt.datetime.now(tz=_dt.UTC).date()
    for i, av in enumerate(avails or [{"startTime": "09:00", "endTime": "09:30"}]):
        day = base_date + _dt.timedelta(days=i + 1)
        start = f"{day.isoformat()}T{_row_text(av, 'startTime') or '09:00'}:00Z"
        slots.append({"start": start, "end": f"{day.isoformat()}T{_row_text(av, 'endTime') or '09:30'}:00Z", "reason": preferredTimeOfDay or purpose or "available"})
    return {"slots": slots[:3], "note": f"Suggested for {requesterDid}; duration {duration} minutes."}


def task_yotei_auto_reschedule(eventId: str = "", reason: str = "", **_: Any) -> dict[str, Any]:
    rows = _query("event", "id = %s", (eventId,), limit=1)
    if not rows:
        return {"error": "event_not_found"}
    evt = rows[0]
    start = _dt.datetime.now(tz=_dt.UTC) + _dt.timedelta(days=1)
    alternatives = [
        {"start": (start + _dt.timedelta(days=i)).isoformat().replace("+00:00", "Z"), "end": (start + _dt.timedelta(days=i, minutes=30)).isoformat().replace("+00:00", "Z"), "reason": reason or "next available window"}
        for i in range(3)
    ]
    return {"alternatives": alternatives, "originalEvent": {"id": eventId, "title": evt.get("title")}, "advice": "Review availability before confirming."}


def task_yotei_analyze_schedule(calendarId: str = "", **_: Any) -> dict[str, Any]:
    avails = _query("availability", "calendar_id = %s", (calendarId,), limit=100)
    events = _query("event", "calendar_id = %s AND status != %s", (calendarId, "cancelled"), limit=100)
    bookings = _query("booking", "calendar_id = %s AND status IN (%s,%s)", (calendarId, "proposed", "confirmed"), limit=100)
    density = "high" if len(events) > 20 else "medium" if len(events) > 8 else "low"
    risk = "high" if len(bookings) > 10 else "medium" if len(bookings) > 4 else "low"
    return {
        "utilization": f"{min(100, int((len(events) / max(1, len(avails) * 3)) * 100))}%",
        "meetingDensity": density,
        "focusBlocks": max(0, len(avails) - len(events)),
        "overcommitRisk": risk,
        "suggestions": ["Protect focus blocks", "Batch short meetings"] if events else ["Add availability windows"],
        "summary": f"{len(events)} events and {len(bookings)} active bookings.",
    }


def task_yotei_health(**_: Any) -> dict[str, Any]:
    return {"status": "ok", "app": "yotei", "nanoid": "unyrsfan", "timestamp": _now()}


def task_yotei_describe(**_: Any) -> dict[str, Any]:
    return {
        "name": "Yotei Scheduler",
        "description": "Calendar scheduling and availability coordination.",
        "capabilities": ["calendar-scheduling", "availability-management", "meeting-booking", "event-management"],
        "did": YOTEI_DID,
    }


def register(worker: Any, *, timeout_ms: int = 60_000) -> None:
    tasks = {
        "xrpc.com.etzhayyim.apps.yotei.analyzeSchedule": task_yotei_analyze_schedule,
        "xrpc.com.etzhayyim.apps.yotei.autoReschedule": task_yotei_auto_reschedule,
        "xrpc.com.etzhayyim.apps.yotei.cancelBooking": task_yotei_cancel_booking,
        "xrpc.com.etzhayyim.apps.yotei.cancelEvent": task_yotei_cancel_event,
        "xrpc.com.etzhayyim.apps.yotei.confirmBooking": task_yotei_confirm_booking,
        "xrpc.com.etzhayyim.apps.yotei.createCalendar": task_yotei_create_calendar,
        "xrpc.com.etzhayyim.apps.yotei.createEvent": task_yotei_create_event,
        "xrpc.com.etzhayyim.apps.yotei.deleteCalendar": task_yotei_delete_calendar,
        "xrpc.com.etzhayyim.apps.yotei.describe": task_yotei_describe,
        "xrpc.com.etzhayyim.apps.yotei.getAvailability": task_yotei_get_availability,
        "xrpc.com.etzhayyim.apps.yotei.getBooking": task_yotei_get_booking,
        "xrpc.com.etzhayyim.apps.yotei.getCalendar": task_yotei_get_calendar,
        "xrpc.com.etzhayyim.apps.yotei.getEvent": task_yotei_get_event,
        "xrpc.com.etzhayyim.apps.yotei.getOpenSlots": task_yotei_get_open_slots,
        "xrpc.com.etzhayyim.apps.yotei.health": task_yotei_health,
        "xrpc.com.etzhayyim.apps.yotei.listBookings": task_yotei_list_bookings,
        "xrpc.com.etzhayyim.apps.yotei.listCalendars": task_yotei_list_calendars,
        "xrpc.com.etzhayyim.apps.yotei.listEvents": task_yotei_list_events,
        "xrpc.com.etzhayyim.apps.yotei.proposeBooking": task_yotei_propose_booking,
        "xrpc.com.etzhayyim.apps.yotei.removeAvailability": task_yotei_remove_availability,
        "xrpc.com.etzhayyim.apps.yotei.setAvailability": task_yotei_set_availability,
        "xrpc.com.etzhayyim.apps.yotei.suggestSlots": task_yotei_suggest_slots,
        "xrpc.com.etzhayyim.apps.yotei.updateEvent": task_yotei_update_event,
    }
    for task_type, handler in tasks.items():
        worker.task(task_type=task_type, single_value=False, timeout_ms=timeout_ms)(handler)
