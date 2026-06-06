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
    # CANONICAL write — etzhayyim's OWN kotoba, DID-bound auth (no vendor auth root):
    KOTOBA_ENDPOINT=<etzhayyim-node> KOTOBA_AUTH=<did-bound-bearer> python3 ingest.py --push
    # OPTIONAL gftd pinning mirror (content-addressed COPY only, NOT canonical):
    KOTOBA_JWT=<gftd-jwt> python3 ingest.py --mirror-gftd
    python3 ingest.py --live          # refused unless KAMADO_OPERATOR_GATE=1 (G8)

SUBSTRATE BOUNDARY: the canonical write goes to etzhayyim's own kotoba (the engine is
etzhayyim's open-source, github.com/etzhayyim/kotoba), authenticated by an etzhayyim
DID-bound token — religious-corp canonical state is NOT gated by a vendor auth service
(Ownership invariant + Murakumo-only consent boundary). gftd kotobase
(did:web:kotobase.net) is an OPTIONAL availability mirror only. kg.ingest is a TENANT
write (sub == tenant_did); datomic.transact is operator-only.
"""
from __future__ import annotations

import json
import os
import pathlib
import sys
import urllib.error
import urllib.request

import analyze  # reuse the EDN reader + classify for dedup-vs-seed

# ── Substrate-boundary (CRITICAL) ────────────────────────────────────────────
# CANONICAL write path = etzhayyim's OWN kotoba endpoint, authenticated by an
# etzhayyim DID-bound token (member/operator signature — no-server-key). The
# kotoba ENGINE is etzhayyim's own open-source (github.com/etzhayyim/kotoba,
# 40-engine/kotoba). Per the Ownership invariant (意思決定権・payoff = etzhayyim only)
# + the Murakumo-only consent-capability boundary (ADR-2605215000), religious-corp
# CANONICAL STATE must NOT be gated by a vendor's auth service. So the default
# push target is operator-supplied (KOTOBA_ENDPOINT) — there is deliberately NO
# hardcoded vendor default.
CANONICAL_NSID = "com.etzhayyim.apps.kotobase.kg.ingest_batch"

# OPTIONAL pinning MIRROR = gftd kotobase (did:web:kotobase.net, runs etzhayyim/kotoba
# unmodified; verified live 2026-06-05). Because state is content-addressed (CID
# commit-DAG) + Base L2 anchored, a mirror can only host a COPY — it cannot alter or
# own the data (datomic.transact is operator-only there; CIDs are immutable). gftd is
# therefore a commodity availability vendor (Pinata-class), NEVER the canonical auth
# root. It is opt-in ONLY via --mirror-gftd with a gftd-AUTHN JWT.
GFTD_MIRROR_ENDPOINT = "https://kotobase.net"
GFTD_MIRROR_NSID = "ai.gftd.apps.kotobase.kg.ingest_batch"

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


def push_batch(batch, auth, endpoint, nsid):
    """POST kg.ingest_batch to a kotoba endpoint (G8 — Bearer token = operator attestation).

    Endpoint/nsid/auth are all explicit: the CANONICAL path supplies etzhayyim's own
    endpoint + DID-bound token; the gftd MIRROR path supplies kotobase.net + a gftd JWT.
    Uses stdlib urllib (no third-party deps). Returns (status, body). kg.ingest is a TENANT
    write (sub == tenant_did); datomic.transact is operator-only and not used here.
    """
    url = f"{endpoint.rstrip('/')}/xrpc/{nsid}"
    data = json.dumps(batch, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(url, data=data, method="POST", headers={
        "content-type": "application/json",
        "authorization": f"Bearer {auth}",
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
        # CANONICAL path: etzhayyim's OWN kotoba endpoint + DID-bound token (no vendor auth root).
        endpoint = os.environ.get("KOTOBA_ENDPOINT")
        auth = os.environ.get("KOTOBA_AUTH")
        nsid = os.environ.get("KOTOBA_NSID", CANONICAL_NSID)
        if not endpoint or not auth:
            sys.exit(
                "kamado G8 (canonical write): --push targets etzhayyim's OWN kotoba — NOT a "
                "vendor. Set KOTOBA_ENDPOINT=<etzhayyim kotoba node> and KOTOBA_AUTH=<etzhayyim "
                "DID-bound bearer / member-sig> then re-run. (Ownership invariant: religious-corp "
                "canonical state is not gated by a vendor auth service. For an OPTIONAL gftd "
                "pinning mirror — copy only, never canonical — use --mirror-gftd with KOTOBA_JWT.)")
        status, body = push_batch(batch, auth, endpoint, nsid)
        print(f"  → POST {endpoint.rstrip('/')}/xrpc/{nsid}  [{status}]  (CANONICAL — etzhayyim)")
        print(f"    {body[:400]}")
        return 0 if 200 <= status < 300 else 1

    if "--mirror-gftd" in argv:
        # OPTIONAL mirror: a content-addressed COPY on gftd kotobase. NOT the canonical home.
        jwt = os.environ.get("KOTOBA_JWT")
        if not jwt:
            sys.exit(f"kamado: --mirror-gftd pins a COPY to the gftd kotobase mirror "
                     f"({GFTD_MIRROR_ENDPOINT}) — a commodity availability vendor, NEVER the "
                     f"canonical auth root. Needs a gftd-AUTHN JWT: set KOTOBA_JWT=<bearer>. "
                     f"The CANONICAL write is --push to etzhayyim's own kotoba.")
        print("  NOTE: gftd kotobase is a pinning MIRROR (content-addressed copy), not canonical.")
        status, body = push_batch(batch, jwt, GFTD_MIRROR_ENDPOINT, GFTD_MIRROR_NSID)
        print(f"  → POST {GFTD_MIRROR_ENDPOINT}/xrpc/{GFTD_MIRROR_NSID}  [{status}]  (MIRROR — gftd)")
        print(f"    {body[:400]}")
        return 0 if 200 <= status < 300 else 1

    print("  promote to live kotoba/KV (operator-gated, G8):")
    print("    CANONICAL (etzhayyim's own kotoba — no vendor auth):")
    print(f"      KOTOBA_ENDPOINT=<etzhayyim-node> KOTOBA_AUTH=<did-bound-bearer> python3 ingest.py --push")
    print("    actor-profile identity (etzhayyim CF KV — own infra):")
    print("      node ../../50-infra/etzhayyim-did-web/scripts/publish-actor-records.mjs "
          "--actor kamado --put-kv --ingest-kotoba")
    print("    OPTIONAL gftd pinning mirror (copy only, NOT canonical):")
    print(f"      KOTOBA_JWT=<gftd-jwt> python3 ingest.py --mirror-gftd")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
