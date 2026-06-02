"""VIN / vehicle registration intelligence handlers for BPMN + Zeebe."""

from __future__ import annotations

import json
import re
import time
from typing import Any, Callable
from uuid import uuid4

from pymagatama.db_sync import sync_cursor

OWNER_DID = "did:web:vin.etzhayyim.com"
NANOID = "v1n0g10b"

TABLE_BY_COLLECTION = {
    "vehicle": "vertex_vin_vehicle",
    "licensePlate": "vertex_vin_license_plate",
    "cohortRegistration": "vertex_vin_cohort_registration",
    "jurisdictionRegistry": "vertex_vin_jurisdiction_registry",
    "manufacturer": "vertex_vin_manufacturer",
    "wmiCode": "vertex_vin_wmi_code",
    "vehicleType": "vertex_vin_vehicle_type",
    "productionPlant": "vertex_vin_production_plant",
    "productionLine": "vertex_vin_production_line",
    "shipmentVolume": "vertex_vin_shipment_volume",
    "shipmentCohort": "vertex_vin_cohort_registration",
}

JURISDICTIONS = [
    {"code": "jpn", "name": "国土交通省", "plate_format": "{地名}{分類番号}{かな}{番号}", "vin_required": "true"},
    {"code": "usa", "name": "NHTSA", "plate_format": "{state}-{plate}", "vin_required": "true"},
    {"code": "deu", "name": "KBA", "plate_format": "{city}-{alpha}{num}", "vin_required": "true"},
    {"code": "gbr", "name": "DVLA", "plate_format": "{area}{age}{random}", "vin_required": "true"},
    {"code": "fra", "name": "SIV", "plate_format": "{AA}-{123}-{AA}", "vin_required": "true"},
    {"code": "kor", "name": "MOLIT", "plate_format": "{num}{hangul}{num}", "vin_required": "true"},
    {"code": "chn", "name": "MPS", "plate_format": "{province}{alpha}{num}", "vin_required": "true"},
    {"code": "ind", "name": "MoRTH", "plate_format": "{state}{district}{num}", "vin_required": "true"},
    {"code": "bra", "name": "DENATRAN", "plate_format": "{AAA}-{1A23}", "vin_required": "true"},
    {"code": "can", "name": "TC", "plate_format": "{province}-{plate}", "vin_required": "true"},
]

VEHICLE_TYPES = [
    {"type_code": "sedan_c", "body_style": "sedan", "segment": "C"},
    {"type_code": "sedan_d", "body_style": "sedan", "segment": "D"},
    {"type_code": "suv_c", "body_style": "suv", "segment": "C"},
    {"type_code": "suv_d", "body_style": "suv", "segment": "D"},
    {"type_code": "pickup_f", "body_style": "pickup", "segment": "F"},
    {"type_code": "ev_bev", "body_style": "ev", "segment": "BEV"},
    {"type_code": "kei_a", "body_style": "kei", "segment": "A"},
    {"type_code": "hatchback_c", "body_style": "hatchback", "segment": "C"},
]

MANUFACTURERS = [
    {"name": "Toyota", "country": "jpn", "wmi_codes": ["JTD", "JTE", "JTN"]},
    {"name": "Honda", "country": "jpn", "wmi_codes": ["JHM", "JHL"]},
    {"name": "Nissan", "country": "jpn", "wmi_codes": ["JN1", "JN3"]},
    {"name": "BMW", "country": "deu", "wmi_codes": ["WBA", "WBS", "WBY"]},
    {"name": "Mercedes-Benz", "country": "deu", "wmi_codes": ["WDB", "WDC"]},
    {"name": "Volkswagen", "country": "deu", "wmi_codes": ["WVW", "WV2"]},
    {"name": "Ford", "country": "usa", "wmi_codes": ["1FA", "1FM", "1FT"]},
    {"name": "Tesla", "country": "usa", "wmi_codes": ["5YJ", "7SA"]},
    {"name": "Hyundai", "country": "kor", "wmi_codes": ["KMH", "KM8"]},
    {"name": "BYD", "country": "chn", "wmi_codes": ["LFP"]},
]

PLANTS = [
    {"plant_code": "TMC_MOTOMACHI", "name": "元町工場", "country": "jpn", "manufacturer_name": "Toyota", "capacity_annual": 200000},
    {"plant_code": "TMC_TSUTSUMI", "name": "堤工場", "country": "jpn", "manufacturer_name": "Toyota", "capacity_annual": 400000},
    {"plant_code": "BMW_DING", "name": "Dingolfing", "country": "deu", "manufacturer_name": "BMW", "capacity_annual": 350000},
    {"plant_code": "TESLA_FREMONT", "name": "Fremont CA", "country": "usa", "manufacturer_name": "Tesla", "capacity_annual": 650000},
    {"plant_code": "TESLA_SHANGHAI", "name": "Shanghai", "country": "chn", "manufacturer_name": "Tesla", "capacity_annual": 950000},
    {"plant_code": "HMC_ULSAN", "name": "Ulsan", "country": "kor", "manufacturer_name": "Hyundai", "capacity_annual": 1600000},
]

LINES = [
    {"line_id": "L1", "plant_code": "TMC_MOTOMACHI", "vehicle_types": ["sedan_d"], "throughput_per_hour": 60},
    {"line_id": "L1", "plant_code": "BMW_DING", "vehicle_types": ["sedan_d"], "throughput_per_hour": 55},
    {"line_id": "L1", "plant_code": "TESLA_FREMONT", "vehicle_types": ["sedan_d", "ev_bev"], "throughput_per_hour": 65},
    {"line_id": "L1", "plant_code": "HMC_ULSAN", "vehicle_types": ["sedan_c", "ev_bev"], "throughput_per_hour": 100},
]

YEAR_MAP = {
    "A": "2010", "B": "2011", "C": "2012", "D": "2013", "E": "2014", "F": "2015",
    "G": "2016", "H": "2017", "J": "2018", "K": "2019", "L": "2020", "M": "2021",
    "N": "2022", "P": "2023", "R": "2024", "S": "2025", "T": "2026",
}


def now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _id(prefix: str) -> str:
    return f"{prefix}-{uuid4().hex[:12]}"


def _s(value: Any, default: str = "") -> str:
    return str(value if value is not None else default)


def _n(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9_]", "", re.sub(r"[\s/]+", "_", value.lower()))


def vin_to_did(vin: str) -> str:
    return f"{OWNER_DID}:vehicle:vin{vin.upper()}"


def plate_to_did(jurisdiction: str, plate: str) -> str:
    compact = re.sub(r"[\s-]", "", plate.lower())
    return f"{OWNER_DID}:plate:{jurisdiction}:{compact}"


def mfr_to_did(name: str) -> str:
    return f"{OWNER_DID}:manufacturer:{_slug(name)}"


def wmi_to_did(code: str) -> str:
    return f"{OWNER_DID}:wmi:{code.lower()}"


def plant_to_did(mfr: str, code: str) -> str:
    return f"{OWNER_DID}:plant:{_slug(mfr)}:{code.lower()}"


def line_to_did(plant_code: str, line_id: str) -> str:
    return f"{OWNER_DID}:line:{plant_code.lower()}:{line_id.lower()}"


def vtype_to_did(segment: str, body: str) -> str:
    return f"{OWNER_DID}:type:{segment.lower()}:{body.lower()}"


def _common(collection: str, did: str, rec_id: str | None = None) -> dict[str, Any]:
    return {
        "vertex_id": did,
        "_seq": None,
        "created_date": time.strftime("%Y-%m-%d", time.gmtime()),
        "sensitivity_ord": 100,
        "owner_did": OWNER_DID,
        "rkey": _id(collection),
        "repo": OWNER_DID,
        "did": did,
        "collection": f"com.etzhayyim.apps.vin.{collection}",
        "status": "active",
        "id": rec_id or _id(collection),
        "org_id": "anon",
        "user_id": "anon",
        "actor_id": NANOID,
        "created_at": now_iso(),
    }


def _execute(sql: str, params: tuple[Any, ...] = ()) -> int:
    with sync_cursor() as cur:
        cur.execute(sql, params)
        return int(cur.rowcount or 0)


def _select(table: str, where: str = "TRUE", params: tuple[Any, ...] = (), limit: int = 50, offset: int = 0) -> list[dict[str, Any]]:
    with sync_cursor() as cur:
        cur.execute(f"SELECT * FROM {table} WHERE {where} LIMIT %s OFFSET %s", (*params, limit, offset))
        cols = [d[0] for d in cur.description or []]
        return [dict(zip(cols, row)) for row in cur.fetchall()]


def _insert(table: str, values: dict[str, Any]) -> None:
    values = {k: v for k, v in values.items() if v is not None}
    cols = list(values)
    placeholders = ", ".join(["%s"] * len(cols))
    col_sql = ", ".join(cols)
    updates = ", ".join([f"{c}=EXCLUDED.{c}" for c in cols if c != "vertex_id"])
    _execute(
        f"INSERT INTO {table} ({col_sql}) VALUES ({placeholders}) "
        f"ON CONFLICT (vertex_id) DO UPDATE SET {updates}",
        tuple(values[c] for c in cols),
    )


def _summary(row: dict[str, Any] | None, keys: list[str]) -> dict[str, Any]:
    if not row:
        return {}
    return {k: row.get(k) for k in keys}


def decode_vin_structure(vin: str) -> dict[str, Any]:
    v = re.sub(r"[^A-HJ-NPR-Z0-9]", "", vin.upper())
    if len(v) != 17:
        return {"error": "VIN must be 17 characters"}
    wmi, vds, vis = v[:3], v[3:9], v[9:17]
    manufacturer = next((m for m in MANUFACTURERS if wmi in m["wmi_codes"]), None)
    return {
        "wmi": wmi,
        "vds": vds,
        "vis": vis,
        "year": YEAR_MAP.get(v[9], "unknown"),
        "make": manufacturer["name"] if manufacturer else "Unknown",
        "model": vds,
        "plant": v[10],
        "vin": v,
    }


def example_method(**_: Any) -> dict[str, Any]:
    return {"ok": True, "nanoid": NANOID, "did": OWNER_DID}


def debug_pds(**_: Any) -> dict[str, Any]:
    return {"hasPds": False, "execution": "bpmn+zeebe-python", "appId": NANOID}


def decode_vin(vin: Any = None, **_: Any) -> dict[str, Any]:
    if not _s(vin):
        return {"error": "vin is required"}
    decoded = decode_vin_structure(_s(vin))
    if decoded.get("error"):
        return decoded
    did = vin_to_did(decoded["vin"])
    _insert(
        "vertex_vin_vehicle",
        {
            **_common("vehicle", did, _id("veh")),
            "vin": decoded["vin"],
            "make": decoded["make"],
            "model": decoded["model"],
            "year": _n(decoded["year"]) if decoded["year"] != "unknown" else None,
            "plant": decoded["plant"],
            "wmi": decoded["wmi"],
            "vds": decoded["vds"],
            "vis": decoded["vis"],
        },
    )
    return {"did": did, **decoded}


def get_vehicle(vin: Any = None, **_: Any) -> dict[str, Any]:
    rows = _select("vertex_vin_vehicle", "vin = %s", (_s(vin).upper(),), 1, 0) if _s(vin) else []
    return _summary(rows[0], ["vin", "make", "model", "year", "wmi"]) if rows else {"error": "vehicle not found"}


def list_vehicles(limit: Any = 50, offset: Any = 0, **_: Any) -> dict[str, Any]:
    rows = _select("vertex_vin_vehicle", limit=_n(limit, 50), offset=_n(offset))
    return {"items": [_summary(r, ["vin", "make", "model", "year", "wmi"]) for r in rows], "total": len(rows), "limit": _n(limit, 50), "offset": _n(offset)}


def search_vehicles(make: Any = None, limit: Any = 50, **_: Any) -> dict[str, Any]:
    rows = _select("vertex_vin_vehicle", "make = %s" if _s(make) else "TRUE", (_s(make),) if _s(make) else (), _n(limit, 50), 0)
    return {"items": [_summary(r, ["vin", "make", "model", "year", "wmi"]) for r in rows]}


def get_vehicle_history(vin: Any = None, **_: Any) -> dict[str, Any]:
    v = _s(vin)
    if not v:
        return {"error": "vin is required"}
    plates = _select("vertex_vin_license_plate", "vin = %s", (v,), 50, 0)
    cohorts = _select("vertex_vin_cohort_registration", "vin = %s", (v,), 50, 0)
    return {
        "vin": v,
        "plates": [_summary(r, ["plate", "jurisdiction"]) for r in plates],
        "cohorts": [{"cohortDid": r.get("cohort_did"), "label": r.get("label_name") or r.get("cohort_did")} for r in cohorts],
    }


def get_manufacturer(name: Any = None, **_: Any) -> dict[str, Any]:
    rows = _select("vertex_vin_manufacturer", "name = %s", (_s(name),), 1, 0) if _s(name) else []
    return _summary(rows[0], ["name", "country"]) if rows else {"error": "manufacturer not found"}


def list_manufacturers(limit: Any = 50, offset: Any = 0, **_: Any) -> dict[str, Any]:
    rows = _select("vertex_vin_manufacturer", limit=_n(limit, 50), offset=_n(offset))
    return {"items": [_summary(r, ["name", "country"]) for r in rows], "total": len(rows), "limit": _n(limit, 50), "offset": _n(offset)}


def lookup_plate(plate: Any = None, jurisdiction: Any = None, **_: Any) -> dict[str, Any]:
    if not _s(plate) or not _s(jurisdiction):
        return {"error": "plate and jurisdiction are required"}
    plates = _select("vertex_vin_license_plate", "plate = %s AND jurisdiction = %s", (_s(plate), _s(jurisdiction)), 1, 0)
    if not plates:
        return {"error": "plate not found"}
    return get_vehicle(plates[0].get("vin"))


def register_plate(plate: Any = None, jurisdiction: Any = None, vin: Any = None, **_: Any) -> dict[str, Any]:
    if not _s(plate) or not _s(jurisdiction) or not _s(vin):
        return {"error": "plate, jurisdiction, vin required"}
    did = plate_to_did(_s(jurisdiction), _s(plate))
    _insert("vertex_vin_license_plate", {**_common("licensePlate", did, _id("plt")), "plate": _s(plate), "jurisdiction": _s(jurisdiction), "vin": _s(vin)})
    return {"did": did, "plate": _s(plate), "jurisdiction": _s(jurisdiction), "vin": _s(vin)}


def _seed_many(collection: str, table: str, items: list[dict[str, Any]], mapper: Callable[[dict[str, Any]], dict[str, Any]]) -> dict[str, Any]:
    for item in items:
        _insert(table, mapper(item))
    return {"seeded": len(items)}


def seed_jurisdictions(**_: Any) -> dict[str, Any]:
    return _seed_many("jurisdictionRegistry", "vertex_vin_jurisdiction_registry", JURISDICTIONS, lambda j: {
        **_common("jurisdictionRegistry", f"{OWNER_DID}:jurisdiction:{j['code']}", _id("jur")),
        "country_code": j["code"], "authority_name": j["name"], "plate_format": j["plate_format"], "vin_required": j["vin_required"],
    })


def seed_manufacturers(**_: Any) -> dict[str, Any]:
    return _seed_many("manufacturer", "vertex_vin_manufacturer", MANUFACTURERS, lambda m: {
        **_common("manufacturer", mfr_to_did(m["name"]), _id("mfr")),
        "name": m["name"], "manufacturer_name": m["name"], "country": m["country"], "wmi_codes": json.dumps(m["wmi_codes"]),
    })


def seed_wmi_codes(**_: Any) -> dict[str, Any]:
    items = [{"code": code, "manufacturer_name": m["name"], "region": m["country"]} for m in MANUFACTURERS for code in m["wmi_codes"]]
    return _seed_many("wmiCode", "vertex_vin_wmi_code", items, lambda w: {
        **_common("wmiCode", wmi_to_did(w["code"]), _id("wmi")),
        "code": w["code"], "manufacturer_name": w["manufacturer_name"], "region": w["region"],
    })


def seed_vehicle_types(**_: Any) -> dict[str, Any]:
    return _seed_many("vehicleType", "vertex_vin_vehicle_type", VEHICLE_TYPES, lambda vt: {
        **_common("vehicleType", vtype_to_did(vt["segment"], vt["body_style"]), _id("vtp")),
        "type_code": vt["type_code"], "body_style": vt["body_style"], "segment": vt["segment"],
    })


def seed_production_plants(**_: Any) -> dict[str, Any]:
    return _seed_many("productionPlant", "vertex_vin_production_plant", PLANTS, lambda p: {
        **_common("productionPlant", plant_to_did(p["manufacturer_name"], p["plant_code"]), _id("plt")),
        **p,
    })


def seed_production_lines(**_: Any) -> dict[str, Any]:
    return _seed_many("productionLine", "vertex_vin_production_line", LINES, lambda line: {
        **_common("productionLine", line_to_did(line["plant_code"], line["line_id"]), _id("pln")),
        "line_id": line["line_id"], "plant_code": line["plant_code"], "vehicle_types": json.dumps(line["vehicle_types"]),
        "throughput_per_hour": line["throughput_per_hour"],
    })


def get_plant(plant_code: Any = None, **_: Any) -> dict[str, Any]:
    rows = _select("vertex_vin_production_plant", "plant_code = %s", (_s(plant_code),), 1, 0) if _s(plant_code) else []
    return _summary(rows[0], ["plant_code", "name", "country", "manufacturer_name", "capacity_annual"]) if rows else {"error": "plant not found"}


def list_plants(limit: Any = 50, **_: Any) -> dict[str, Any]:
    rows = _select("vertex_vin_production_plant", limit=_n(limit, 50))
    return {"items": [_summary(r, ["plant_code", "name", "country", "manufacturer_name", "capacity_annual"]) for r in rows], "total": len(rows)}


def list_vehicle_types(limit: Any = 50, **_: Any) -> dict[str, Any]:
    rows = _select("vertex_vin_vehicle_type", limit=_n(limit, 50))
    return {"items": [_summary(r, ["type_code", "body_style", "segment"]) for r in rows], "total": len(rows)}


def list_jurisdictions(limit: Any = 50, offset: Any = 0, **_: Any) -> dict[str, Any]:
    rows = _select("vertex_vin_jurisdiction_registry", limit=_n(limit, 50), offset=_n(offset))
    return {"items": [_summary(r, ["country_code", "authority_name"]) for r in rows], "total": len(rows), "limit": _n(limit, 50), "offset": _n(offset)}


def ingest_shipment(plant_code: Any = None, jurisdiction: Any = None, year: Any = None, month: Any = None, vehicle_type: Any = None, volume: Any = None, **_: Any) -> dict[str, Any]:
    if not all([_s(plant_code), _s(jurisdiction), _n(year), _n(month), _s(vehicle_type), _n(volume)]):
        return {"error": "plant_code, jurisdiction, year, month, vehicle_type, volume required"}
    did = f"{OWNER_DID}:shipment:{_s(plant_code).lower()}:{_s(jurisdiction)}:{_n(year)}:{_n(month)}:{_s(vehicle_type)}"
    _insert("vertex_vin_shipment_volume", {**_common("shipmentVolume", did, _id("shp")), "plant_code": _s(plant_code), "jurisdiction": _s(jurisdiction), "year": _n(year), "month": _n(month), "vehicle_type": _s(vehicle_type), "volume": _n(volume)})
    return {"plantCode": _s(plant_code), "jurisdiction": _s(jurisdiction), "year": _n(year), "month": _n(month), "vehicleType": _s(vehicle_type), "volume": _n(volume)}


def get_shipment_flow(year: Any = 2025, **_: Any) -> dict[str, Any]:
    rows = _select("vertex_vin_shipment_volume", "year = %s", (_n(year, 2025),), 10000, 0)
    plants = {r.get("plant_code"): r for r in _select("vertex_vin_production_plant", limit=10000)}
    grouped: dict[tuple[str, str, str], int] = {}
    for r in rows:
        key = (_s(r.get("plant_code")), _s(r.get("jurisdiction")), _s(r.get("vehicle_type")))
        grouped[key] = grouped.get(key, 0) + _n(r.get("volume"))
    flows = []
    for (plant, dest, vt), vol in grouped.items():
        p = plants.get(plant, {})
        cap = _n(p.get("capacity_annual"))
        flows.append({"plant": plant, "plant_name": p.get("name", ""), "manufacturer": p.get("manufacturer_name", ""), "destination": dest, "vehicle_type": vt, "actual_flow": vol, "capacity": cap, "utilization": vol / cap if cap else 0})
    return {"year": _n(year, 2025), "flows": flows}


def list_shipment_cohorts(limit: Any = 50, offset: Any = 0, **_: Any) -> dict[str, Any]:
    rows = _select("vertex_vin_cohort_registration", limit=_n(limit, 50), offset=_n(offset))
    return {"items": [{"cohortDid": r.get("cohort_did"), "label": r.get("label_name"), "volume": r.get("volume")} for r in rows], "total": len(rows), "limit": _n(limit, 50), "offset": _n(offset)}


def register_cohort(vin: Any = None, cohortDid: Any = None, label: Any = None, **_: Any) -> dict[str, Any]:
    if not _s(vin) or not _s(cohortDid):
        return {"error": "vin and cohortDid required"}
    did = f"{OWNER_DID}:cohort-registration:{_s(vin).lower()}:{uuid4().hex[:8]}"
    _insert("vertex_vin_cohort_registration", {**_common("cohortRegistration", did, _id("coh")), "vin": _s(vin), "cohort_did": _s(cohortDid), "label_name": _s(label, _s(cohortDid))})
    return {"vin": _s(vin), "cohortDid": _s(cohortDid), "label": _s(label, _s(cohortDid))}


def list_cohort(cohortDid: Any = None, **_: Any) -> dict[str, Any]:
    if not _s(cohortDid):
        return {"error": "cohortDid required"}
    rows = _select("vertex_vin_cohort_registration", "cohort_did = %s", (_s(cohortDid),), 50, 0)
    return {"cohortDid": _s(cohortDid), "members": [{"vin": r.get("vin")} for r in rows]}


def collect_recall(**_: Any) -> dict[str, Any]:
    return {"status": "triggered", "ts": now_iso()}
