"""Port infrastructure and port-call tracking handlers for BPMN + Zeebe."""

from __future__ import annotations

import json
import time
from typing import Any
from uuid import uuid4

from pymagatama.db_sync import sync_cursor

OWNER_DID = "did:web:p0rt7890.gftd.ai"
PUBLIC_DID = "did:web:port.gftd.ai"
NANOID = "p0rt7890"

OTHER_COLLECTION = {
    "Berth": "ai.gftd.apps.port.berth",
    "Terminal": "ai.gftd.apps.port.terminal",
    "PortCallEvent": "ai.gftd.apps.port.portCallEvent",
}

OTHER_TABLE = {
    "Berth": "vertex_port_berth",
    "Terminal": "vertex_port_terminal",
    "PortCallEvent": "vertex_port_call_event",
}

PROMOTED_COLUMNS = {
    "Berth": {
        "berth_id": "berthId",
        "port_id": "portId",
        "name": "name",
        "berth_type": "berthType",
        "length_m": "lengthM",
        "depth_m": "depthM",
    },
    "Terminal": {
        "terminal_id": "terminalId",
        "port_id": "portId",
        "name": "name",
        "terminal_type": "terminalType",
        "operator": "operator",
        "capacity": "capacity",
    },
    "PortCallEvent": {
        "event_id": "eventId",
        "call_id": "callId",
        "port_id": "portId",
        "imo_number": "imoNumber",
        "event_type": "eventType",
        "event_timestamp": "timestamp",
        "berth_id": "berthId",
    },
}

SEED_PORTS = [
    {"name": "Shanghai", "unLocode": "CNSHA", "country": "CN", "latitude": 31.35, "longitude": 121.50, "portType": "seaport", "maxDraftM": 16.0, "annualThroughputTeu": 49000000},
    {"name": "Singapore", "unLocode": "SGSIN", "country": "SG", "latitude": 1.26, "longitude": 103.85, "portType": "seaport", "maxDraftM": 18.0, "annualThroughputTeu": 39000000},
    {"name": "Rotterdam", "unLocode": "NLRTM", "country": "NL", "latitude": 51.91, "longitude": 4.50, "portType": "seaport", "maxDraftM": 24.0, "annualThroughputTeu": 14500000},
    {"name": "Yokohama", "unLocode": "JPYOK", "country": "JP", "latitude": 35.45, "longitude": 139.65, "portType": "seaport", "maxDraftM": 16.0, "annualThroughputTeu": 3000000},
    {"name": "Ras Tanura", "unLocode": "SARTR", "country": "SA", "latitude": 26.64, "longitude": 50.17, "portType": "seaport", "maxDraftM": 27.0, "annualThroughputTeu": 0},
]


def now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _id(prefix: str) -> str:
    return f"{prefix}-{uuid4().hex[:12]}"


def _s(value: Any, default: str = "") -> str:
    return str(value if value is not None else default)


def _n(value: Any, default: float = 0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _execute(sql: str, params: tuple[Any, ...] = ()) -> int:
    with sync_cursor() as cur:
        cur.execute(sql, params)
        return int(cur.rowcount or 0)


def _inflate(row: dict[str, Any]) -> dict[str, Any]:
    props = row.get("props")
    if isinstance(props, str) and props:
        try:
            parsed = json.loads(props)
            if isinstance(parsed, dict):
                return {**row, **parsed}
        except json.JSONDecodeError:
            pass
    return row


def _select_other(label: str, limit: int = 10000, offset: int = 0) -> list[dict[str, Any]]:
    table = OTHER_TABLE[label]
    with sync_cursor() as cur:
        cur.execute(f"SELECT * FROM {table} ORDER BY created_date DESC LIMIT %s OFFSET %s", (limit, offset))
        cols = [d[0] for d in cur.description or []]
        return [_inflate(dict(zip(cols, row))) for row in cur.fetchall()]


def _select_ports(limit: int = 10000, offset: int = 0) -> list[dict[str, Any]]:
    with sync_cursor() as cur:
        cur.execute("SELECT * FROM vertex_transport WHERE label = 'Port' ORDER BY created_date DESC LIMIT %s OFFSET %s", (limit, offset))
        cols = [d[0] for d in cur.description or []]
        return [_inflate(dict(zip(cols, row))) for row in cur.fetchall()]


def _insert_port(props: dict[str, Any], port_id: str | None = None) -> dict[str, Any]:
    pid = _s(port_id or props.get("portId") or props.get("unLocode") or _id("port"))
    props = {**props, "portId": pid, "nodeLabel": "Port", "createdAt": props.get("createdAt") or now_iso()}
    did = props.get("did") or f"{PUBLIC_DID}:{pid.lower()}"
    _execute(
        """INSERT INTO vertex_transport
        (vertex_id, _seq, created_date, sensitivity_ord, owner_did, rkey, repo, label, did, name, display_name,
         description, category, code, lat, lng, status, props, actor_did, org_did)
        VALUES (%s, _next_seq('vertex_transport'), %s, %s, %s, %s, %s, 'Port', %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (vertex_id) DO UPDATE SET props = EXCLUDED.props, status = EXCLUDED.status""",
        (
            f"at://{OWNER_DID}/ai.gftd.apps.port.port/{pid}",
            time.strftime("%Y-%m-%d", time.gmtime()),
            100,
            OWNER_DID,
            pid,
            OWNER_DID,
            did,
            props.get("name"),
            props.get("name"),
            props.get("description"),
            props.get("portType") or "port",
            props.get("unLocode") or pid,
            _n(props.get("latitude")),
            _n(props.get("longitude")),
            props.get("status") or "operational",
            json.dumps(props, ensure_ascii=False, sort_keys=True),
            OWNER_DID,
            "anon",
        ),
    )
    return {"ok": True, "portId": pid}


def _insert_other(label: str, props: dict[str, Any], id_field: str) -> dict[str, Any]:
    table = OTHER_TABLE[label]
    rec_id = _s(props.get(id_field) or _id(label.lower()))
    props = {**props, id_field: rec_id, "nodeLabel": label, "createdAt": props.get("createdAt") or now_iso(), "orgId": "anon", "userId": "anon", "actorId": OWNER_DID}
    vertex_id = f"at://{OWNER_DID}/ai.gftd.apps.port.{label}/{rec_id}"
    columns = [
        "vertex_id", "_seq", "created_date", "sensitivity_ord", "owner_did", "rkey", "repo",
        "label", "did", "collection", "status", "props", "actor_did", "org_did",
    ]
    values: list[Any] = [
        vertex_id,
        time.strftime("%Y-%m-%d", time.gmtime()),
        100,
        OWNER_DID,
        rec_id,
        OWNER_DID,
        label,
        props.get("did") or vertex_id,
        OTHER_COLLECTION[label],
        "active",
        json.dumps(props, ensure_ascii=False, sort_keys=True),
        OWNER_DID,
        "anon",
    ]
    promoted = PROMOTED_COLUMNS[label]
    for column, prop_name in promoted.items():
        columns.append(column)
        value = props.get(prop_name)
        if column in {"length_m", "depth_m", "capacity"}:
            value = _n(value)
        values.append(value)
    placeholders = ", ".join(["%s"] * (len(values) - 1))
    update_columns = ["props", "status", *promoted.keys()]
    assignments = ", ".join(f"{column} = EXCLUDED.{column}" for column in update_columns)
    _execute(
        f"""INSERT INTO {table}
        ({", ".join(columns)})
        VALUES (%s, _next_seq('{table}'), {placeholders})
        ON CONFLICT (vertex_id) DO UPDATE SET {assignments}""",
        tuple(values),
    )
    if label in {"Berth", "Terminal"} and props.get("portId"):
        _insert_edge("edge_port_infrastructure", rec_id, f"at://{OWNER_DID}/ai.gftd.apps.port.port/{props.get('portId')}", vertex_id, f"HAS_{label.upper()}", props)
    elif label == "PortCallEvent":
        _insert_edge("edge_port_call_event", rec_id, _s(props.get("callId") or props.get("portId")), vertex_id, "HAS_PORT_CALL_EVENT", props)
    return {"ok": True, id_field: rec_id}


def _insert_edge(table: str, key: str, src_vid: str, dst_vid: str, relation: str, props: dict[str, Any]) -> None:
    edge_id = f"at://{OWNER_DID}/{table}/{key}"
    _execute(
        f"""INSERT INTO {table}
        (edge_id, _seq, created_date, sensitivity_ord, owner_did, src_vid, dst_vid, relation, status, props, actor_did, org_did)
        VALUES (%s, _next_seq('{table}'), %s, %s, %s, %s, %s, %s, 'active', %s, %s, %s)
        ON CONFLICT (edge_id) DO UPDATE SET src_vid = EXCLUDED.src_vid, dst_vid = EXCLUDED.dst_vid, props = EXCLUDED.props""",
        (
            edge_id,
            time.strftime("%Y-%m-%d", time.gmtime()),
            100,
            OWNER_DID,
            src_vid,
            dst_vid,
            relation,
            json.dumps(props, ensure_ascii=False, sort_keys=True),
            OWNER_DID,
            "anon",
        ),
    )


def register_port(**kwargs: Any) -> dict[str, Any]:
    return _insert_port(dict(kwargs))


def update_port(**kwargs: Any) -> dict[str, Any]:
    return _insert_port(dict(kwargs))


def register_berth(**kwargs: Any) -> dict[str, Any]:
    return _insert_other("Berth", dict(kwargs), "berthId")


def register_terminal(**kwargs: Any) -> dict[str, Any]:
    return _insert_other("Terminal", dict(kwargs), "terminalId")


def get_port(portId: Any = None, id: Any = None, locode: Any = None, portLocode: Any = None, **_: Any) -> dict[str, Any]:
    key = _s(portId or id or locode or portLocode)
    row = next((p for p in _select_ports() if _s(p.get("portId")) == key or _s(p.get("unLocode")) == key or _s(p.get("code")) == key), None)
    return row or {"error": "not found"}


def list_ports(limit: Any = 50, offset: Any = 0, country: Any = None, portType: Any = None, **_: Any) -> dict[str, Any]:
    rows = _select_ports(10000, int(_n(offset)))
    if _s(country):
        rows = [r for r in rows if _s(r.get("country")) == _s(country)]
    if _s(portType):
        rows = [r for r in rows if _s(r.get("portType")) == _s(portType)]
    rows = rows[: int(_n(limit, 50))]
    return {"items": rows, "total": len(rows)}


def search_ports(query: Any = None, q: Any = None, limit: Any = 50, **_: Any) -> dict[str, Any]:
    needle = _s(query or q).lower()
    rows = [r for r in _select_ports() if needle in _s(r.get("name")).lower() or needle in _s(r.get("unLocode")).lower() or needle in _s(r.get("country")).lower()]
    rows = rows[: int(_n(limit, 50))]
    return {"items": rows, "count": len(rows)}


def get_port_berths(portId: Any = None, locode: Any = None, limit: Any = 50, **_: Any) -> dict[str, Any]:
    key = _s(portId or locode)
    rows = [r for r in _select_other("Berth") if not key or _s(r.get("portId")) == key][: int(_n(limit, 50))]
    return {"items": rows, "total": len(rows)}


def get_port_terminals(portId: Any = None, locode: Any = None, limit: Any = 50, **_: Any) -> dict[str, Any]:
    key = _s(portId or locode)
    rows = [r for r in _select_other("Terminal") if not key or _s(r.get("portId")) == key][: int(_n(limit, 50))]
    return {"items": rows, "total": len(rows)}


def receive_port_call_event(**kwargs: Any) -> dict[str, Any]:
    rec = {
        "eventId": _s(kwargs.get("eventId") or _id("pce")),
        "callId": kwargs.get("callId") or "",
        "portId": kwargs.get("portId") or kwargs.get("portLocode") or "",
        "imoNumber": kwargs.get("imoNumber") or "",
        "eventType": kwargs.get("eventType") or "eta-update",
        "timestamp": kwargs.get("timestamp") or now_iso(),
        "berthId": kwargs.get("berthId"),
        "pilotOnBoard": kwargs.get("pilotOnBoard"),
        "tugsRequired": kwargs.get("tugsRequired"),
    }
    return _insert_other("PortCallEvent", rec, "eventId")


def list_port_call_events(limit: Any = 50, offset: Any = 0, **_: Any) -> dict[str, Any]:
    rows = _select_other("PortCallEvent", int(_n(limit, 50)), int(_n(offset)))
    return {"items": rows, "total": len(rows)}


def get_vessels_at_port(locode: Any = None, portLocode: Any = None, portId: Any = None, limit: Any = 50, **_: Any) -> dict[str, Any]:
    key = _s(locode or portLocode or portId)
    rows = [r for r in _select_other("PortCallEvent") if _s(r.get("portId")) == key][: int(_n(limit, 50))]
    return {"items": [{"pc": r} for r in rows], "count": len(rows)}


def get_port_occupancy(locode: Any = None, portLocode: Any = None, **_: Any) -> dict[str, Any]:
    key = _s(locode or portLocode)
    events = [r for r in _select_other("PortCallEvent") if _s(r.get("portId")) == key]
    berths = [r for r in _select_other("Berth") if _s(r.get("portId")) == key]
    berthed = len([r for r in events if _s(r.get("eventType")) in ("arrival", "berthed")])
    approaching = len([r for r in events if _s(r.get("eventType")) in ("eta-update", "approaching")])
    total = len(berths)
    return {"locode": key, "berthed": berthed, "approaching": approaching, "totalBerths": total, "utilization": berthed / total if total else 0}


def seed_ports(force: Any = False, **_: Any) -> dict[str, Any]:
    existing = len(_select_ports(1, 0))
    if existing and not force:
        return {"ok": True, "skipped": True, "existingPorts": existing}
    ports = berths = terminals = 0
    for p in SEED_PORTS:
        _insert_port({**p, "portId": p["unLocode"], "status": "operational", "did": f"{PUBLIC_DID}:{p['unLocode'].lower()}"})
        ports += 1
        _insert_other("Berth", {"portId": p["unLocode"], "name": f"{p['name']} main berth", "lengthM": 400, "depthM": p["maxDraftM"], "berthType": "container" if p["annualThroughputTeu"] else "tanker"}, "berthId")
        berths += 1
        _insert_other("Terminal", {"portId": p["unLocode"], "name": f"{p['name']} terminal", "terminalType": "container" if p["annualThroughputTeu"] else "liquid", "operator": p["name"], "capacity": p["annualThroughputTeu"]}, "terminalId")
        terminals += 1
    return {"ok": True, "ports": ports, "berths": berths, "terminals": terminals, "countries": len({p["country"] for p in SEED_PORTS})}


def get_dashboard(**_: Any) -> dict[str, Any]:
    return {"dashboard": {"Port": len(_select_ports()), "Berth": len(_select_other("Berth")), "Terminal": len(_select_other("Terminal")), "PortCallEvent": len(_select_other("PortCallEvent"))}}
