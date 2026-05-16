"""Mold-Allergy handlers for BPMN + Zeebe."""

from __future__ import annotations

import json
import time
from decimal import Decimal
from typing import Any
from uuid import uuid4

from pymagatama.db_sync import sync_cursor

OWNER_DID = "did:web:mold-allergy.gftd.ai"

IUIS_FUNGAL_ALLERGENS: list[dict[str, Any]] = [
    {"species": "Alternaria alternata", "allergen": "Alt a 1", "uniprot": "P79085", "mw_kda": 16.4, "function": "major allergen, unique fold"},
    {"species": "Alternaria alternata", "allergen": "Alt a 6", "uniprot": "Q9HDT3", "mw_kda": 11.0, "function": "enolase"},
    {"species": "Cladosporium herbarum", "allergen": "Cla h 8", "uniprot": "P40918", "mw_kda": 28.0, "function": "mannitol dehydrogenase"},
    {"species": "Cladosporium herbarum", "allergen": "Cla h 9", "uniprot": "P42039", "mw_kda": 39.0, "function": "vacuolar serine protease"},
    {"species": "Aspergillus fumigatus", "allergen": "Asp f 1", "uniprot": "P04389", "mw_kda": 18.0, "function": "mitogillin, ribotoxin"},
    {"species": "Aspergillus fumigatus", "allergen": "Asp f 2", "uniprot": "P79017", "mw_kda": 37.0, "function": "fibrinogen binding"},
    {"species": "Aspergillus fumigatus", "allergen": "Asp f 3", "uniprot": "O43099", "mw_kda": 19.0, "function": "peroxisomal protein"},
    {"species": "Penicillium chrysogenum", "allergen": "Pen ch 13", "uniprot": "Q9UVF8", "mw_kda": 34.0, "function": "alkaline serine protease"},
    {"species": "Penicillium chrysogenum", "allergen": "Pen ch 18", "uniprot": "Q9P8U2", "mw_kda": 32.0, "function": "vacuolar serine protease"},
    {"species": "Malassezia sympodialis", "allergen": "Mala s 1", "uniprot": "Q9UW20", "mw_kda": 35.3, "function": "beta-glucosidase homolog"},
    {"species": "Malassezia sympodialis", "allergen": "Mala s 11", "uniprot": "Q8NIY1", "mw_kda": 22.7, "function": "Mn superoxide dismutase"},
    {"species": "Trichophyton rubrum", "allergen": "Tri r 2", "uniprot": "", "mw_kda": 30.0, "function": "subtilisin-like serine protease"},
]


def now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _id(prefix: str) -> str:
    return f"{prefix}-{uuid4().hex[:12]}"


def _num(value: Any, default: float = 0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _clamp(value: Any, fallback: int = 50) -> int:
    try:
        parsed = int(value if value is not None else fallback)
    except (TypeError, ValueError):
        parsed = fallback
    return max(1, min(parsed, 100))


def _offset(value: Any) -> int:
    try:
        return max(0, int(value or 0))
    except (TypeError, ValueError):
        return 0


def _jsonable(value: Any) -> Any:
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, dict):
        return {k: _jsonable(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_jsonable(v) for v in value]
    return value


def _fetch_all(sql: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
    with sync_cursor() as cur:
        cur.execute(sql, params)
        cols = [d[0] for d in cur.description]
        return [_jsonable(dict(zip(cols, row))) for row in (cur.fetchall() or [])]


def _execute(sql: str, params: tuple[Any, ...] = ()) -> int:
    with sync_cursor() as cur:
        cur.execute(sql, params)
        return int(cur.rowcount or 0)


def seed_allergen_catalog(**_: Any) -> dict[str, Any]:
    written = 0
    created = now_iso()
    for item in IUIS_FUNGAL_ALLERGENS:
        vertex_id = f"mold-allergy:allergen:{item['allergen'].lower().replace(' ', '-')}"
        _execute(
            """INSERT INTO vertex_mold_allergen
            (vertex_id, _seq, owner_did, species, allergen, uniprot, mw_kda, biochemical_function, source, created_at, actor_id)
            VALUES (%s, _next_seq('vertex_mold_allergen'), %s, %s, %s, %s, %s, %s, 'WHO-IUIS allergen nomenclature', %s, 'm0ldalg1')
            ON CONFLICT (vertex_id) DO UPDATE SET
              species=EXCLUDED.species,
              uniprot=EXCLUDED.uniprot,
              mw_kda=EXCLUDED.mw_kda,
              biochemical_function=EXCLUDED.biochemical_function""",
            (vertex_id, OWNER_DID, item["species"], item["allergen"], item["uniprot"], item["mw_kda"], item["function"], created),
        )
        written += 1
    return {"written": written, "total": len(IUIS_FUNGAL_ALLERGENS)}


def record_air_sampling(**kwargs: Any) -> dict[str, Any]:
    site = str(kwargs.get("site") or "")
    if not site:
        return {"error": "site required"}
    session_id = _id("air")
    _execute(
        """INSERT INTO vertex_mold_air_sampling
        (vertex_id, _seq, owner_did, session_id, site, sampled_at, method,
         alternaria_count_per_m3, cladosporium_count_per_m3, aspergillus_count_per_m3,
         penicillium_count_per_m3, temperature_c, relative_humidity, created_at, actor_id)
        VALUES (%s, _next_seq('vertex_mold_air_sampling'), %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'm0ldalg1')""",
        (
            f"mold-allergy:air:{session_id}",
            OWNER_DID,
            session_id,
            site,
            str(kwargs.get("sampledAt") or now_iso()),
            str(kwargs.get("method") or "Burkard"),
            _num(kwargs.get("alternariaCountPerM3")),
            _num(kwargs.get("cladosporiumCountPerM3")),
            _num(kwargs.get("aspergillusCountPerM3")),
            _num(kwargs.get("penicilliumCountPerM3")),
            _num(kwargs.get("temperatureC")),
            _num(kwargs.get("relativeHumidity")),
            now_iso(),
        ),
    )
    return {"sessionId": session_id}


def propose_slit_candidate(**kwargs: Any) -> dict[str, Any]:
    species = str(kwargs.get("species") or "")
    if not species:
        return {"error": "species required"}
    candidate_id = _id("slit")
    excipients = kwargs.get("excipients")
    if not isinstance(excipients, list):
        excipients = ["mannitol", "gelatin", "sodium hydroxide"]
    _execute(
        """INSERT INTO vertex_mold_slit_candidate
        (vertex_id, _seq, owner_did, candidate_id, species, allergen_source, major_allergen,
         dosage_form, buildup_weeks, maintenance_dose_jau, excipients_json,
         target_indication, design_lineage, phase, created_at, actor_id)
        VALUES (%s, _next_seq('vertex_mold_slit_candidate'), %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'Shidakure/Acitea', %s, %s, 'm0ldalg1')""",
        (
            f"mold-allergy:slit:{candidate_id}",
            OWNER_DID,
            candidate_id,
            species,
            str(kwargs.get("allergenSource") or "recombinant"),
            str(kwargs.get("majorAllergen") or ""),
            str(kwargs.get("dosageForm") or "freeze-dried orodispersible tablet"),
            int(_num(kwargs.get("buildupWeeks"), 1)),
            _num(kwargs.get("maintenanceDoseJau"), 2000),
            json.dumps(excipients, ensure_ascii=False),
            str(kwargs.get("targetIndication") or "allergic rhinitis"),
            str(kwargs.get("phase") or "preclinical"),
            now_iso(),
        ),
    )
    return {"candidateId": candidate_id}


def list_allergens(species: Any = None, limit: Any = 50, offset: Any = 0, **_: Any) -> dict[str, Any]:
    lim = _clamp(limit, 50)
    off = _offset(offset)
    if species:
        rows = _fetch_all(
            "SELECT * FROM vertex_mold_allergen WHERE species=%s ORDER BY species, allergen LIMIT %s OFFSET %s",
            (str(species), lim, off),
        )
    else:
        rows = _fetch_all("SELECT * FROM vertex_mold_allergen ORDER BY species, allergen LIMIT %s OFFSET %s", (lim, off))
    return {"allergens": rows, "total": len(rows), "offset": off, "limit": lim}


def list_slit_candidates(species: Any = None, phase: Any = None, limit: Any = 50, offset: Any = 0, **_: Any) -> dict[str, Any]:
    lim = _clamp(limit, 50)
    off = _offset(offset)
    where: list[str] = []
    params: list[Any] = []
    if species:
        where.append("species=%s")
        params.append(str(species))
    if phase:
        where.append("phase=%s")
        params.append(str(phase))
    clause = f"WHERE {' AND '.join(where)}" if where else ""
    rows = _fetch_all(
        f"SELECT * FROM vertex_mold_slit_candidate {clause} ORDER BY created_at DESC LIMIT %s OFFSET %s",
        (*params, lim, off),
    )
    return {"candidates": rows, "total": len(rows), "offset": off, "limit": lim}
