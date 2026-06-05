#!/usr/bin/env python3
"""kamado 竈 — legacy oil-refining → kotoba-EAVT migration bridge (R0).

ADR-2606051500. The legacy `oil-refining` actor stored refinery / unit / outage as
RisingWave/graph nodes driven by Cypher (`MATCH (r:Refinery) …`), prohibited by
ADR-2605262130 (the kotoba Datom log is first-class canonical state). This bridge reads a
legacy graph EXPORT (the Refinery / RefineryUnit / RefineryOutage node shape) and emits:

  1. kotoba-EDN datoms (`:refinery/* :unit/* :outage/*`) per the refining ontology, dedup-
     merged against the kamado seed (seed identity wins) → data/refinery-graph.migrated.kotoba.edn
  2. a kotoba `kg.ingest_batch` body (entities + claims + relations, mirroring
     publish-actor-records.mjs recordToKgEntity) ready to POST to the refining graph →
     out/oil-refining-kotoba-batch.json

CONSTITUTIONAL (kamado G1 / G4 / G7 / G8):
  - G4 — observation ≠ operation: a refinery's operator is an ORG id (`org.corp.*`), never a
    person. Any person-typed field in the export is REFUSED (a refinery is not a person).
  - G1 — observed assets are tagged `:observed-fossil` (observation of a fossil asset is
    permitted; OPERATING a fossil refinery is the unrepresentable thing — there is no
    :synthesis record here, so feedstock_guard is not bypassed).
  - G7 — every migrated node is tagged `:sourcing :representative` (migrated, not authoritative).
  - G8 — LIVE migration (reading a live RisingWave dump / live bulletin fetch) is OUTWARD-
    GATED: it requires KAMADO_OPERATOR_GATE=1 AND --live. Default is OFFLINE over a sample export.

stdlib only. Usage:
    python3 ingest.py --export data/ingest/legacy-oil-refining-export.sample.json [--out OUTDIR]
    KOTOBA_JWT=<bearer> python3 ingest.py --push   # POST batch → live kotobase.net (G8; JWT = attestation)
    python3 ingest.py --live          # refused unless KAMADO_OPERATOR_GATE=1 (G8)

The live target is the gftd kotobase endpoint (did:web:kotobase.net, etzhayyim/kotoba
upstream): POST https://kotobase.net/xrpc/ai.gftd.apps.kotobase.kg.ingest_batch, Bearer JWT.
kg.ingest is a TENANT write (sub == tenant_did); datomic.transact is operator-only.
"""
from __future__ import annotations

import json
import os
import pathlib
import sys
import urllib.error
import urllib.request

import analyze  # reuse the EDN reader + classify for dedup-vs-seed

# Live kotoba endpoint (gftd kotobase — etzhayyim/kotoba upstream; did:web:kotobase.net).
# Verified 2026-06-05: /health ok, kg.ingest_batch is a tenant write (Bearer gftd-AUTHN JWT).
KOTOBASE_ENDPOINT = "https://kotobase.net"
KG_INGEST_BATCH_NSID = "ai.gftd.apps.kotobase.kg.ingest_batch"

# G4: fields that would tie a refinery to a natural person — refused on sight.
PERSON_FIELDS = ("owner_person", "ceo", "person", "individual", "operator_person", "crew")
# legacy status string → kamado status keyword
STATUS_MAP = {"active": ":active", "idled": ":idled", "idle": ":idled",
              "decommissioning": ":decommissioning", "converted": ":converted",
              "down": ":down", "planned": ":planned", "resolved": ":resolved"}
UNIT_KINDS = ("cdu", "fcc", "hydrocracker", "coker", "reformer", "hydrotreater", "alkylation")


def _status(s, default=":active"):
    return STATUS_MAP.get((s or "").strip().lower(), default)


def _rid(code):
    cc, _, rest = (code or "").partition("-")
    return f"rf.{cc.lower()}.{rest.lower().replace('-', '_')}" if rest else f"rf.{code.lower()}"


def _uid(code, unit_type):
    return f"u.{_rid(code).removeprefix('rf.').replace('.', '_')}.{(unit_type or '').lower()}"


def _guard_no_person(node, ctx):
    for f in PERSON_FIELDS:
        if node.get(f):
            raise ValueError(
                f"G4 violation ({ctx}): export carries a person field {f!r}; a refinery is an "
                f"org asset, never a person (operator must be an org.corp.* id). Refusing."
            )


def migrate(export):
    """Legacy node export → (refineries, units, outages) kamado-EAVT dicts."""
    refineries, units, outages = {}, {}, {}

    for r in export.get("Refinery", []):
        _guard_no_person(r, f"Refinery {r.get('refinery_code')}")
        rid = _rid(r["refinery_code"])
        op = r.get("operator_org")
        if op and not str(op).startswith("org."):
            raise ValueError(f"G4 violation: operator {op!r} is not an org.corp.* id ({rid})")
        refineries[rid] = {
            ":refinery/id": rid,
            ":refinery/name": r.get("name") or r["refinery_code"],
            ":refinery/country": r.get("country_code"),
            ":refinery/operator": op,
            ":refinery/throughput-bpd": r.get("throughput_bpd", 0),
            ":refinery/status": _status(r.get("status")),
            # G1: observation of a fossil asset (NOT operation). No :synthesis record => the
            # feedstock guard is never bypassed; this only mirrors what exists in the world.
            ":refinery/feedstock-class": ":observed-fossil",
            ":refinery/transition-readiness": ":unknown",  # derived later by analyze/plan
            ":refinery/sourcing": ":representative",
        }

    for u in export.get("RefineryUnit", []):
        kind = (u.get("unit_type") or "").lower()
        uid = _uid(u["refinery_code"], kind)
        units[uid] = {
            ":unit/id": uid,
            ":unit/refinery": _rid(u["refinery_code"]),
            ":unit/kind": f":{kind}" if kind in UNIT_KINDS else ":unknown",
            ":unit/status": _status(u.get("status")),
            ":unit/sourcing": ":representative",
        }

    for o in export.get("RefineryOutage", []):
        kind = (o.get("unit_type") or "").lower()
        as_of = o.get("as_of", "")
        oid = f"o.{_rid(o['refinery_code']).removeprefix('rf.').replace('.', '_')}.{kind}.{as_of}"
        outages[oid] = {
            ":outage/id": oid,
            ":outage/unit": _uid(o["refinery_code"], kind),
            ":outage/status": _status(o.get("status"), ":planned"),
            ":outage/as-of": as_of,
            ":outage/sourcing": ":representative",
        }
    return refineries, units, outages


def dedup_vs_seed(migrated, seed_dict, idkey):
    """Seed identity wins (watari convention): keep seed rows, add only new migrated ids."""
    out = dict(seed_dict)
    added = 0
    for k, v in migrated.items():
        if k not in out:
            out[k] = v
            added += 1
    return out, added


# ── kotoba kg.ingest_batch (mirrors publish-actor-records.mjs recordToKgEntity) ──
def _entity(eid, etype, label, row, relations):
    # live kg.ingest contract (ai.gftd.apps.kotobase): {id, type?, label_*, claims?, relations?}
    claims = [{"pred": k.lstrip(":"), "value": str(v)}
              for k, v in row.items() if v not in (None, "", 0) or k.endswith("throughput-bpd")]
    return {"id": eid, "type": etype, "label_en": label, "claims": claims, "relations": relations}


def to_kg_batch(refineries, units, outages):
    entities = []
    for rid, r in refineries.items():
        entities.append(_entity(f"refinery.{rid}", "refinery-asset",
                                 r.get(":refinery/name", rid), r, []))
    for uid, u in units.items():
        entities.append(_entity(f"unit.{uid}", "refinery-unit", uid, u,
                                 [{"pred": "unit/refinery", "target": f"refinery.{u[':unit/refinery']}"}]))
    for oid, o in outages.items():
        entities.append(_entity(f"outage.{oid}", "refinery-outage", oid, o,
                                 [{"pred": "outage/unit", "target": f"unit.{o[':outage/unit']}"}]))
    return {"entities": entities}


def push_batch(batch, jwt, endpoint=KOTOBASE_ENDPOINT, nsid=KG_INGEST_BATCH_NSID):
    """POST the kg.ingest_batch to the LIVE kotoba endpoint (G8 — Bearer JWT = operator attestation).

    Uses stdlib urllib (no third-party deps). Returns (status, body). kg.ingest is a TENANT
    write (sub == tenant_did); datomic.transact is operator-only and not used here.
    """
    url = f"{endpoint.rstrip('/')}/xrpc/{nsid}"
    data = json.dumps(batch, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(url, data=data, method="POST", headers={
        "content-type": "application/json",
        "authorization": f"Bearer {jwt}",
    })
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace")


def render_edn(refineries, units, outages):
    def emit(d):
        return "\n".join(
            " {" + " ".join(f"{k} {json.dumps(v) if isinstance(v, str) and not v.startswith(':') else v}"
                            for k, v in row.items()) + "}"
            for row in d.values())
    L = [";; kamado 竈 — MIGRATED refinery graph (legacy oil-refining → kotoba EAVT, ADR-2606051500)",
         ";; :representative; seed identity wins on id collision. Generated by methods/ingest.py.",
         "["]
    L.append(emit(refineries))
    L.append(emit(units))
    L.append(emit(outages))
    L.append("]")
    return "\n".join(L)


def main(argv):
    here = pathlib.Path(__file__).resolve().parent
    if "--live" in argv:
        if os.environ.get("KAMADO_OPERATOR_GATE") != "1":
            sys.exit("kamado G8: live legacy-RisingWave / bulletin migration is Council+operator "
                     "gated. Set KAMADO_OPERATOR_GATE=1 with attestation. Default offline: "
                     "--export <legacy-export.json>.")
        sys.exit("kamado R0: live migration not implemented (design-only). Wire the RisingWave "
                 "dump reader / live bulletin fetch here once gated.")

    export_path = pathlib.Path(argv[argv.index("--export") + 1]) if "--export" in argv \
        else here.parent / "data" / "ingest" / "legacy-oil-refining-export.sample.json"
    out = pathlib.Path(argv[argv.index("--out") + 1]) if "--out" in argv else here / "out"
    out.mkdir(parents=True, exist_ok=True)

    export = json.loads(export_path.read_text(encoding="utf-8"))
    m_ref, m_unit, m_outage = migrate(export)

    # dedup vs the seed graph (seed wins)
    seed = analyze.classify(analyze.load_edn(here.parent / "data" / "seed-refinery-graph.kotoba.edn"))
    s_ref, s_unit, s_outage, _, _ = seed
    ref, a1 = dedup_vs_seed(m_ref, s_ref, ":refinery/id")
    unit, a2 = dedup_vs_seed(m_unit, s_unit, ":unit/id")
    outage, a3 = dedup_vs_seed(m_outage, s_outage, ":outage/id")

    (out / "refinery-graph.migrated.kotoba.edn").write_text(
        render_edn(ref, unit, outage), encoding="utf-8")
    batch = to_kg_batch(m_ref, m_unit, m_outage)   # batch = the MIGRATED rows (what to ingest)
    (out / "oil-refining-kotoba-batch.json").write_text(
        json.dumps(batch, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"kamado migrate (offline, :representative): legacy export {export_path.name} → "
          f"{len(m_ref)} refineries / {len(m_unit)} units / {len(m_outage)} outages")
    print(f"  merged vs seed: +{a1} refineries, +{a2} units, +{a3} outages new "
          f"(seed identity wins) → {out}/refinery-graph.migrated.kotoba.edn")
    print(f"  kg.ingest_batch: {len(batch['entities'])} entities → {out}/oil-refining-kotoba-batch.json")

    if "--push" in argv:
        # G8: the live push. A valid gftd-AUTHN JWT IS the operator attestation.
        jwt = os.environ.get("KOTOBA_JWT")
        if not jwt:
            sys.exit("kamado G8: --push needs a gftd-AUTHN JWT. Set KOTOBA_JWT=<bearer> "
                     "(tenant write; sub == tenant_did) then re-run. Target: "
                     f"{KOTOBASE_ENDPOINT}/xrpc/{KG_INGEST_BATCH_NSID}.")
        status, body = push_batch(batch, jwt)
        print(f"  → POST {KOTOBASE_ENDPOINT}/xrpc/{KG_INGEST_BATCH_NSID}  [{status}]")
        print(f"    {body[:400]}")
        return 0 if 200 <= status < 300 else 1

    print("  promote to live kotoba/KV (operator-gated, G8):")
    print(f"    KOTOBA_JWT=<bearer> python3 ingest.py --push   →  {KOTOBASE_ENDPOINT}/xrpc/{KG_INGEST_BATCH_NSID}  (refining graph)")
    print("    node ../../50-infra/etzhayyim-did-web/scripts/publish-actor-records.mjs "
          "--actor kamado --put-kv --ingest-kotoba   (actor-profile identity)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
