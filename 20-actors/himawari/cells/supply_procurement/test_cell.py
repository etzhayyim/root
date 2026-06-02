#!/usr/bin/env python3
"""himawari supply_procurement 調達 — cell logic tests (ADR-2606021200).

Pure-logic tests over `SupplyProcurementCell.solve` and its helpers; no kotoba host
bindings required (the datalog import degrades to None in local dev). Verifies the
constitutional invariants of feedstock/consumable procurement:

  - G2: solar-grade-only (N1) + XUAR/forced-labor exclusion (N6) refuse the lot
  - commons-first / Ring-1 SBT↔SBT routing composed from okaimono (no re-impl)
  - G7: internal buys carry an exact 10% TitheRouter split, intent-only (G11)
  - §1.3/G11: external feedstock buys never settle internal value; operator-gated
  - G8: a CycloneDX 1.5 SBOM is emitted + projected to kotoba :cdx/* datoms
  - G2: per-lot provenance attestation (XUAR-exclusion + §2(g) audit CIDs) → kotoba
  - giemon AGV is referenced (composed) for intra-fab transport, never re-implemented
"""
import importlib.util
import pathlib

# Load the sibling cell.py under a UNIQUE module name so `pytest cells/` can collect
# all seven himawari cell test files without the bare module-name `cell` colliding.
_spec = importlib.util.spec_from_file_location(
    "himawari_supply_procurement_cell", pathlib.Path(__file__).parent / "cell.py"
)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
SupplyProcurementCell = _mod.SupplyProcurementCell

BUYER = "did:web:etzhayyim.com:himawari"
SUPPLIER = "did:web:supplier.example"


def _full_need(**over):
    need = {
        "needText": "solar-grade polysilicon",
        "lotId": "lot-2026-0042",
        "feedstockGrade": "solar-grade-6N",
        "process": "siemens",
        "originRegion": "JP",
        "supplierDid": SUPPLIER,
        "buyerDid": BUYER,
        "grossMinor": 4_200_000,
        "originRegionAttestationCid": "bafyOriginXUARfree",
        "sourcingAuditCid": "bafySourcingAudit2g",
        "attestingEngineerDid": "did:plc:eng-001",
        "attestingRobots": ["mimi", "otete"],
        "embodiedEnergyWhPerKg": 90_000,
        "operatorRef": "council-op-2026xxxx",
    }
    need.update(over)
    return need


# ----------------------------- G2 feedstock guards ----------------------------- #
def test_refuses_non_solar_grade():
    out = SupplyProcurementCell().solve({"need": _full_need(feedstockGrade="electronic-grade-9N")})
    assert out["refused"] is True
    assert "solar-grade" in out["reason"]


def test_refuses_xuar_origin():
    out = SupplyProcurementCell().solve({"need": _full_need(originRegion="XUAR")})
    assert out["refused"] is True
    assert "XUAR" in out["reason"]


def test_accepts_solar_grade_jp_origin():
    out = SupplyProcurementCell().solve({"need": _full_need(operatorRef="council-op-1")})
    assert out.get("refused") is not True
    assert out["procurementOrder"]["lotId"] == "lot-2026-0042"


# ----------------------------- commons-first / ring routing ----------------------------- #
def test_recycled_kerf_routes_commons():
    out = SupplyProcurementCell().solve(
        {"need": _full_need(feedstockGrade="recycled-kerf", makerActor=None)}
    )
    order = out["procurementOrder"]
    assert order["ring"] == "commons"
    assert order["settlement"] == "commons-none"
    assert order["titheMinor"] == 0


def test_internal_ring1_sbt_settles_with_exact_tithe():
    reg = {BUYER: True, "did:web:etzhayyim.com:hikari": True}
    out = SupplyProcurementCell().solve(
        {"need": _full_need(makerActor="hikari", ring="internal", grossMinor=18_000_000,
                            sbtRegistry=reg, operatorRef=None)}
    )
    order = out["procurementOrder"]
    assert order["state"] == "settle-intent"
    s = order["settlement"]
    assert s["titheMinor"] == 1_800_000
    assert s["makerPayoutMinor"] == 16_200_000
    # canonical invariant: gross == tithe + payout (no remainder loss)
    assert s["grossMinor"] == s["titheMinor"] + s["makerPayoutMinor"]
    assert s["state"] == "intent"  # NOT broadcast without operator (G11)


def test_internal_ring1_refuses_ineligible_sbt():
    reg = {BUYER: False}  # buyer not an active Adherent SBT holder
    out = SupplyProcurementCell().solve(
        {"need": _full_need(makerActor="hikari", ring="internal", sbtRegistry=reg)}
    )
    assert out["refused"] is True


def test_external_feedstock_is_operator_gated_no_internal_value():
    out = SupplyProcurementCell().solve(
        {"need": _full_need(ring="external", operatorRef=None)}
    )
    order = out["procurementOrder"]
    assert order["ring"] == "external"
    assert order["state"] == "external-pending-operator"  # §1.3/G11
    assert order["titheMinor"] == 0                        # no internal value inflow


def test_external_feedstock_handoff_with_operator():
    out = SupplyProcurementCell().solve(
        {"need": _full_need(ring="external", operatorRef="council-op-1")}
    )
    assert out["procurementOrder"]["state"] == "external-handoff"


# ----------------------------- G8 SBOM → kotoba ----------------------------- #
def test_sbom_attestation_is_cyclonedx_with_feedstock_component():
    out = SupplyProcurementCell().solve({"need": _full_need()})
    sbom = out["sbomAttestation"]
    assert sbom["bomFormat"] == "CycloneDX"
    assert sbom["specVersion"] == "1.5"
    assert sbom["componentCount"] >= 1
    # the feedstock itself is the primary purl-keyed component
    purls = [c.get("purl") for c in sbom["cyclonedx"]["components"]]
    assert any(p and p.startswith("pkg:himawari-feedstock/") for p in purls)


def test_sbom_projects_consumables_to_kotoba_datoms():
    consumable = {
        "bom-ref": "consumable/ag-paste-001", "type": "device", "name": "silver paste",
        "purl": "pkg:himawari-consumable/ag-paste@2026", "supplier": {"name": "did:web:paste.example"},
    }
    out = SupplyProcurementCell().solve({"need": _full_need(components=[consumable])})
    sbom = out["sbomAttestation"]
    assert sbom["componentCount"] == 2  # feedstock + the consumable
    # G8: one kotoba :cdx/* entity per component, purl carried as the CVE join key
    ents = sbom["kotobaEntities"]
    assert len(ents) == 2
    cdx_purls = [
        cl["value"] for e in ents for cl in e["claims"] if cl["pred"] == "cdx/purl"
    ]
    assert "pkg:himawari-consumable/ag-paste@2026" in cdx_purls


def test_kotoba_writes_carry_sbom_and_provenance():
    out = SupplyProcurementCell().solve({"need": _full_need()})
    writes = out["kotobaWrites"]
    types = {e["type"] for e in writes}
    assert "SbomComponent" in types                       # G8
    assert "PolysiliconProvenanceAttestation" in types    # G2


# ----------------------------- G2 per-lot provenance ----------------------------- #
def test_provenance_attestation_attested_when_complete():
    out = SupplyProcurementCell().solve({"need": _full_need()})
    prov = out["provenanceAttestation"]
    rec = prov["record"]
    assert rec["$type"] == "com.etzhayyim.himawari.polysiliconProvenanceAttestation"
    assert rec["attested"] is True
    assert rec["originRegionAttestationCid"] == "bafyOriginXUARfree"
    assert rec["sourcingAuditCid"] == "bafySourcingAudit2g"


def test_provenance_unattested_when_missing_audit_cid():
    out = SupplyProcurementCell().solve({"need": _full_need(sourcingAuditCid=None)})
    rec = out["provenanceAttestation"]["record"]
    assert rec["attested"] is False              # never silently vouched
    assert "sourcingAuditCid" in rec["unattestedReason"]


def test_provenance_unattested_with_single_robot():
    out = SupplyProcurementCell().solve({"need": _full_need(attestingRobots=["mimi"])})
    rec = out["provenanceAttestation"]["record"]
    assert rec["attested"] is False              # lexicon requires ≥2 attesting robots
    assert "attestingRobots(min2)" in rec["unattestedReason"]


def test_provenance_entity_has_xuar_exclusion_claim():
    out = SupplyProcurementCell().solve({"need": _full_need()})
    ent = out["provenanceAttestation"]["kotobaEntity"]
    preds = {c["pred"]: c["value"] for c in ent["claims"]}
    assert preds["provenance/originAttestationCid"] == "bafyOriginXUARfree"
    assert preds["provenance/attested"] == "true"


# ----------------------------- giemon AGV composition ----------------------------- #
def test_intra_fab_transport_is_giemon_agv():
    out = SupplyProcurementCell().solve({"need": _full_need()})
    assert out["intraFabTransport"] == "giemon-agv"               # composed, not re-implemented
    assert out["procurementOrder"]["intraFabTransport"] == "giemon-agv"


if __name__ == "__main__":
    import sys

    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    failed = 0
    for fn in fns:
        try:
            fn()
            print(f"  ok   {fn.__name__}")
        except AssertionError as e:
            failed += 1
            print(f"  FAIL {fn.__name__}: {e}")
    print(f"\n{len(fns) - failed}/{len(fns)} passed")
    sys.exit(1 if failed else 0)
