"""SupplyProcurementCell — himawari 調達 cell per ADR-2606021200.

調達 — SBOM<->kotoba procurement + okaimono commons-first.
G8 (full SBOM on-chain CycloneDX -> kotoba EAVT, ADR-2605312330) +
    G2 (§2(g) per-lot sourcing audit + XUAR-exclusion chain-of-custody) enforcement.

This cell does NOT re-implement the provisioning commons or the SBOM bridge. I
COMPOSES:
  - okaimono (ADR-2606012100) commons-first three-ring routing + SBT↔SBT eligibility
    + USDC/TitheRouter settlement intent — the verified `20-actors/okaimono/py/agent.py`
    handlers, reached as plain functions (no host binding required).
  - the giemon CycloneDX -> kotoba EAVT bridge (ADR-2605312330,
    `70-tools/scripts/sbom/cyclonedx_to_kotoba.py`) for the on-chain SBOM (G8).
  - giemon AGV (ADR-2606010030) for intra-fab transport of received lots — referenced
    by class, never re-implemented.

For a feedstock/consumable need it (1) routes commons-first through okaimono, (2) builds
a `procurementOrder`, (3) emits a CycloneDX-shaped `sbomAttestation` and projects it to
kotoba `:cdx/*` datoms (G8), and (4) writes a per-lo
`com.etzhayyim.himawari.polysiliconProvenanceAttestation`-shaped provenance datom se
with the XUAR-exclusion + §2(g) sourcing-audit CIDs (G2). Settlement is intent-only and
on-chain broadcast / live external purchase stays operator-gated (G11/§1.3).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

# --------------------------------------------------------------------------- #
# Compose okaimono (commons-first rings + SBT↔SBT + settlement) and the giemon
# CycloneDX→kotoba SBOM bridge as libraries — NOT re-implemented here.
# Both live elsewhere in the monorepo; resolve them relative to this file so the
# cell works under the import-only smoke test and a real run alike.
# --------------------------------------------------------------------------- #
_ROOT = Path(__file__).resolve().parents[4]  # …/etzhayyim-roo
_OKAIMONO_PY = _ROOT / "20-actors" / "okaimono" / "py"
_SBOM_TOOLS = _ROOT / "70-tools" / "scripts" / "sbom"
for _p in (_OKAIMONO_PY, _SBOM_TOOLS):
    if _p.is_dir() and str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

try:  # okaimono provisioning-commons handlers (ADR-2606012100)
    import agent as _okaimono  # type: ignore
except ImportError:  # pragma: no cover - graceful local-dev fallback
    _okaimono = None  # type: ignore

try:  # giemon CycloneDX → kotoba EAVT bridge (ADR-2605312330)
    from cyclonedx_to_kotoba import cyclonedx_to_ingest as _cdx_to_ingest  # type: ignore
except ImportError:  # pragma: no cover
    _cdx_to_ingest = None  # type: ignore

# kotoba-provided host bindings (WASM Component Model imports), as in okaimono/py/agent.py.
try:
    from kotoba import datalog  # type: ignore
except ImportError:  # local dev fallback
    datalog = None  # type: ignore


# --------------------------------------------------------------------------- #
# Constitutional constants for procurement (himawari ADR-2606021200).
# --------------------------------------------------------------------------- #
# G2: solar-grade feedstock grades ONLY — never logic-grade 9N+ EG-Si (N1).
_SOLAR_GRADES = frozenset({"solar-grade-6N", "solar-grade-6N+", "recycled-kerf"})
# G2: forced-labor / XUAR-exclusion is non-negotiable.
_XUAR_REGIONS = frozenset({"XUAR", "xinjiang", "新疆", "uyghur"})
# G8: intra-fab transport of received lots routes to the giemon AGV (composed, ADR-2606010030).
_INTRA_FAB_TRANSPORT = "giemon-agv"
# Commons-first ring ordering is constitutional (mirrors okaimono RING_ORDER).
_RING_ORDER = getattr(_okaimono, "RING_ORDER", ["commons", "internal", "external"])
_TITHE_BPS = getattr(_okaimono, "TITHE_BPS", 1000)


class SupplyProcurementCell:
    """調達 — SBOM<->kotoba procurement + okaimono commons-first."""

    def __init__(self) -> None:
        pass

    # ----------------------------------------------------------------------- #
    # Pregel solve entry — feedstock/consumable need → procurement order + SBOM
    # attestation + per-lot provenance, written to the kotoba Datom log.
    # ----------------------------------------------------------------------- #
    def solve(self, state: dict[str, Any]) -> dict[str, Any]:
        """Resolve one procurement need and emit the order + attestations.

        Input `state` carries a `need` describing the feedstock/consumable lot:
          {
            "needText": "solar-grade polysilicon",   # free-text need (commons-first match)
            "lotId": "lot-2026-0042",                 # required for a feedstock lo
            "feedstockGrade": "solar-grade-6N",       # G2: solar-grade only
            "process": "siemens",                     # siemens|fbr|umg-upgraded|recycled
            "originRegion": "JP",                      # G2: XUAR-excluded
            "supplierDid": "did:web:supplier.example",
            "buyerDid": "did:web:etzhayyim.com:himawari",
            "makerActor": "kanayama",                 # internal Ring-1 producer (optional)
            "grossMinor": 4_200_000,                   # quote for the lot (USDC minor units)
            "originRegionAttestationCid": "bafy…",     # G2 XUAR-exclusion chain-of-custody
            "sourcingAuditCid": "bafy…",               # G2 §2(g) Charter-Rider audi
            "attestingEngineerDid": "did:plc:eng-001",
            "attestingRobots": ["mimi", "otete"],      # ≥2 attesting robots
            "embodiedEnergyWhPerKg": 90_000,           # G4 lifecycle energy accounting
            "components": [ … CycloneDX-shaped consumables … ],  # G8 SBOM inpu
            "sbtRegistry": {did: active?},             # SBT↔SBT eligibility map (Ring 1)
            "operatorRef": "council-op-…",             # G11: gate live broadcast / external buy
          }

        Returns `state` extended with `procurementOrder`, `sbomAttestation`,
        `provenanceAttestation`, and `kotobaWrites` (the datoms persisted, G6/G8).
        Refusals (non-solar grade, XUAR origin, ineligible SBT trade) never reach
        a settlement intent and are surfaced with an explicit reason.
        """
        need = dict(state.get("need", {}))
        # G2 hard gates first — a refused lot must never be ordered or persisted.
        gate = self._guard_feedstock(need)
        if gate is not None:
            return {**state, "procurementOrder": gate, "refused": True, "reason": gate["reason"]}

        ring = self._resolve_ring(need)
        order = self._build_procurement_order(need, ring)
        if order.get("refused") or order.get("state") == "refused":
            return {**state, "procurementOrder": order, "refused": True, "reason": order.get("reason")}

        sbom = self._build_sbom_attestation(need, order)
        provenance = self._build_provenance_attestation(need) if need.get("lotId") else None

        writes: list[dict] = []
        writes.extend(sbom.get("kotobaEntities", []))      # G8: CycloneDX → :cdx/* datoms
        if provenance is not None:
            writes.append(provenance["kotobaEntity"])      # G2: per-lot provenance datom se
        self._persist(writes)

        return {
            **state,
            "procurementOrder": order,
            "sbomAttestation": sbom,
            "provenanceAttestation": provenance,
            "intraFabTransport": _INTRA_FAB_TRANSPORT,      # giemon AGV (composed)
            "kotobaWrites": writes,
        }

    # ----------------------------------------------------------------------- #
    # G2 — feedstock guards: solar-grade only + XUAR/forced-labor exclusion.
    # ----------------------------------------------------------------------- #
    def _guard_feedstock(self, need: dict) -> dict | None:
        """Return a refusal order dict if the lot violates a G2 constitutional gate,
        else None. Solar-grade-only (N1) + XUAR-exclusion (N6) are NOT amendable."""

        # Check abaki route-around policy (React mechanism)
        abaki_policy_path = _ROOT / "20-actors" / "abaki" / "out" / "routing-policy.json"
        if abaki_policy_path.exists():
            try:
                with open(abaki_policy_path, "r", encoding="utf-8") as f:
                    policy = json.load(f)
                blocked_ids = {e["id"] for e in policy.get("blocked_entities", [])}
                supplier_did = need.get("supplierDid", "")
                supplier_name = need.get("supplierName", "")

                for blocked_id in blocked_ids:
                    if blocked_id in supplier_did or blocked_id in supplier_name:
                        return {
                            "state": "refused",
                            "reason": f"Supplier blocked by abaki Anti-Monopoly policy (CI threshold exceeded). React mechanism activated: Route Around {blocked_id}."
                        }
            except Exception:
                pass

        grade = need.get("feedstockGrade")
        if grade is not None and grade not in _SOLAR_GRADES:
            return {
                "state": "refused",
                "reason": f"feedstockGrade {grade!r} is not solar-grade (N1: solar-grade only, "
                f"never logic-grade EG-Si); allowed={sorted(_SOLAR_GRADES)}",
            }
        origin = str(need.get("originRegion", "")).strip().lower()
        if origin and any(x.lower() in origin for x in _XUAR_REGIONS):
            return {
                "state": "refused",
                "reason": "origin region is XUAR/forced-labor excluded (G2/N6 constitutional — "
                "NO XUAR polysilicon ever); closes hikari §G2 structurally",
            }
        return None

    # ----------------------------------------------------------------------- #
    # Commons-first ring resolution (composes okaimono).
    # ----------------------------------------------------------------------- #
    def _resolve_ring(self, need: dict) -> str:
        """Route the need commons-first (G4/G12 mirror): an explicit `ring` wins;
        otherwise prefer an internal Ring-1 producing actor (e.g. kanayama recycled-Si),
        falling back to external feedstock supply only when no internal source exists."""
        if need.get("ring") in _RING_ORDER:
            return str(need["ring"])
        maker = need.get("makerActor")
        maker_set = getattr(_okaimono, "MAKER_ACTORS", set())
        if maker and maker in maker_set:
            return "internal"
        # recycled-kerf feedstock is, by definition, a commons (closed-loop) source.
        if need.get("feedstockGrade") == "recycled-kerf":
            return "commons"
        return "external"

    # ----------------------------------------------------------------------- #
    # procurementOrder — commons-first, SBT↔SBT-gated, tithe-on-internal.
    # ----------------------------------------------------------------------- #
    def _build_procurement_order(self, need: dict, ring: str) -> dict:
        """Build the procurement order. Internal Ring-1 buys go through okaimono's
        verified SBT↔SBT eligibility + USDC/TitheRouter settlement intent (G7);
        external feedstock buys are a member/operator-gated handoff (§1.3/G11):
        external purchase value never flows INTO etzhayyim."""
        buyer = need.get("buyerDid", "did:web:etzhayyim.com:himawari")
        gross = int(need.get("grossMinor", 0))
        base = {
            "lotId": need.get("lotId"),
            "needText": need.get("needText", ""),
            "ring": ring,
            "buyerDid": buyer,
            "intraFabTransport": _INTRA_FAB_TRANSPORT,  # received lots → giemon AGV
        }

        if ring == "commons":
            # best procurement = closed-loop recovery; no settlement, no tithe (mirror okaimono).
            return {**base, "state": "commons-recovery", "settlement": "commons-none", "titheMinor": 0}

        if ring == "internal":
            maker = need.get("makerActor", "")
            registry = need.get("sbtRegistry", {})
            if _okaimono is not None:
                elig = _okaimono.check_sbt_eligibility(buyer, maker, registry)
                if not elig["eligible"]:
                    return {**base, "state": "refused", "reason": elig["reason"]}
                settlement = _okaimono.build_settlement_intent(
                    gross, maker, operator_ref=need.get("operatorRef")
                )
            else:  # pragma: no cover - okaimono should always be importable in-repo
                tithe = (gross * _TITHE_BPS) // 10_000
                settlement = {
                    "rail": "usdc-base-l2", "grossMinor": gross, "titheMinor": tithe,
                    "makerPayoutMinor": gross - tithe, "makerActor": maker,
                    "state": "executed" if need.get("operatorRef") else "intent",
                }
            return {**base, "state": "settle-intent", "makerActor": maker, "settlement": settlement}

        # external: feedstock supplier. §1.3 — no external value INTO etzhayyim; this is a
        # member/operator-gated purchase handoff, not an internal sale. No tithe on external.
        return {
            **base,
            "state": "external-handoff" if need.get("operatorRef") else "external-pending-operator",
            "supplierDid": need.get("supplierDid"),
            "settlement": "operator-gated-purchase",
            "grossMinor": gross,
            "titheMinor": 0,
            "operatorRef": need.get("operatorRef"),
        }

    # ----------------------------------------------------------------------- #
    # G8 — SBOM attestation: CycloneDX 1.5 doc + kotoba EAVT projection.
    # ----------------------------------------------------------------------- #
    def _build_sbom_attestation(self, need: dict, order: dict) -> dict:
        """Emit a CycloneDX 1.5 SBOM for the lot's feedstock + consumables and projec
        it to kotoba `:cdx/*` datoms via the giemon bridge (ADR-2605312330, G8).
        purl is the CVE/recall join key; supplier+mpn enables recall (mirrors giemon)."""
        lot_id = need.get("lotId") or order.get("needText") or "unknown-lot"
        components = list(need.get("components", []))
        # Always include the feedstock itself as the primary component (purl-keyed).
        if need.get("feedstockGrade"):
            components = [self._feedstock_component(need)] + components
        cdx = self._cyclonedx_doc(lot_id, need, components)

        if _cdx_to_ingest is not None:
            entities = _cdx_to_ingest(cdx).get("entities", [])
        else:  # pragma: no cover - bridge should always be importable in-repo
            entities = [
                {
                    "id": c.get("bom-ref") or c.get("purl") or c.get("name", "unknown"),
                    "type": "SbomComponent",
                    "labelEn": c.get("name", ""),
                    "claims": [
                        {"pred": "cdx/purl", "value": c.get("purl", "")},
                        {"pred": "cdx/sbom", "value": lot_id},
                    ],
                }
                for c in components
            ]
        return {
            "lotId": lot_id,
            "bomFormat": "CycloneDX",
            "specVersion": cdx["specVersion"],
            "componentCount": len(components),
            "cyclonedx": cdx,
            "kotobaEntities": entities,  # G8: one :cdx/* entity per componen
        }

    def _feedstock_component(self, need: dict) -> dict:
        """The feedstock lot as a CycloneDX `device` component, purl-keyed on grade+process
        (mirrors the giemon part purl convention so the CVE/recall join works uniformly)."""
        grade = need.get("feedstockGrade", "unknown")
        process = need.get("process", "unknown")
        lot = need.get("lotId", "unknown")
        purl = f"pkg:himawari-feedstock/{grade}/{process}@{lot}"
        comp: dict[str, Any] = {
            "bom-ref": f"feedstock/{lot}",
            "type": "device",
            "name": f"polysilicon {grade}",
            "version": str(lot),
            "purl": purl,
            "properties": [
                {"name": "giemon:procurement", "value": "feedstock"},
                {"name": "giemon:grade", "value": grade},
                {"name": "giemon:process", "value": process},
            ],
        }
        supplier = need.get("supplierDid")
        if supplier:
            comp["supplier"] = {"name": supplier}
            comp["properties"].append({"name": "giemon:supplierDid", "value": supplier})
        return comp

    def _cyclonedx_doc(self, lot_id: str, need: dict, components: list) -> dict:
        """Assemble a minimal, valid CycloneDX 1.5 document for the lot (G8). The
        top-level metadata.component names the lot so `cdx/sbom` carries the lot id."""
        return {
            "bomFormat": "CycloneDX",
            "specVersion": "1.5",
            "version": 1,
            "metadata": {
                "tools": [{"vendor": "etzhayyim", "name": "himawari-supply_procurement", "version": "0.1.0"}],
                "component": {"type": "application", "name": str(lot_id)},
            },
            "components": components,
        }

    # ----------------------------------------------------------------------- #
    # G2 — per-lot provenance attestation (XUAR-exclusion + §2(g) audit) → kotoba.
    # Shape mirrors com.etzhayyim.himawari.polysiliconProvenanceAttestation.
    # ----------------------------------------------------------------------- #
    def _build_provenance_attestation(self, need: dict) -> dict:
        """Build a per-lot provenance attestation matching the himawari lexicon
        `polysiliconProvenanceAttestation` and project it to kotoba `:provenance/*`
        datoms (G2/G6). Required fields are enforced; a lot missing the XUAR-exclusion
        or §2(g) audit CID is flagged `unattested` (never silently vouched)."""
        required = [
            "lotId", "feedstockGrade", "originRegionAttestationCid", "supplierDid",
            "sourcingAuditCid", "attestingEngineerDid", "attestingRobots",
        ]
        record: dict[str, Any] = {
            "$type": "com.etzhayyim.himawari.polysiliconProvenanceAttestation",
            "lotId": need.get("lotId"),
            "feedstockGrade": need.get("feedstockGrade"),
            "process": need.get("process"),
            "originRegionAttestationCid": need.get("originRegionAttestationCid"),
            "supplierDid": need.get("supplierDid"),
            "sourcingAuditCid": need.get("sourcingAuditCid"),
            "attestingEngineerDid": need.get("attestingEngineerDid"),
            "attestingRobots": list(need.get("attestingRobots", [])),
            "embodiedEnergyWhPerKg": need.get("embodiedEnergyWhPerKg"),
        }
        missing = [k for k in required if not record.get(k)]
        # ≥2 attesting robots is a lexicon minItems constraint.
        if len(record["attestingRobots"]) < 2 and "attestingRobots" not in missing:
            missing.append("attestingRobots(min2)")
        record["attested"] = not missing
        if missing:
            record["unattestedReason"] = f"missing G2 provenance fields: {missing}"

        # Project to kotoba EAVT (G6) — one entity, kebab→snake handled at the runtime
        # boundary; here we record explicit :provenance/* claims for queryability.
        claims = [
            {"pred": "provenance/lot", "value": record["lotId"]},
            {"pred": "provenance/grade", "value": record["feedstockGrade"]},
            {"pred": "provenance/originAttestationCid", "value": record["originRegionAttestationCid"]},
            {"pred": "provenance/sourcingAuditCid", "value": record["sourcingAuditCid"]},
            {"pred": "provenance/supplierDid", "value": record["supplierDid"]},
            {"pred": "provenance/attestingEngineerDid", "value": record["attestingEngineerDid"]},
            {"pred": "provenance/attested", "value": str(record["attested"]).lower()},
        ]
        if record.get("embodiedEnergyWhPerKg") is not None:
            claims.append({"pred": "provenance/embodiedEnergyWhPerKg",
                           "value": str(record["embodiedEnergyWhPerKg"])})
        entity = {
            "id": f"provenance/{record['lotId']}",
            "type": "PolysiliconProvenanceAttestation",
            "labelEn": f"lot {record['lotId']} {record.get('feedstockGrade')}",
            "claims": claims,
        }
        return {"record": record, "kotobaEntity": entity}

    # ----------------------------------------------------------------------- #
    # G6 — persist to the kotoba Datom log (canonical state; never RW/SQL).
    # ----------------------------------------------------------------------- #
    def _persist(self, entities: list[dict]) -> None:
        """Write the SBOM + provenance entities to the kotoba Datom log (G6/G8).
        When the host binding is absent (local dev / import-only smoke test) this is a
        no-op — the computed datoms are still returned in `state["kotobaWrites"]`, so
        nothing is silently dropped. NEVER routes to RisingWave/SQL/Lance (ADR-2605262130)."""
        if datalog is None or not entities:
            return
        try:  # kotoba host binding: kg.ingest_batch shape {"entities": [...]}
            datalog.ingest_batch(json.dumps({"entities": entities}))  # type: ignore[union-attr]
        except Exception:  # pragma: no cover - host-side ingest failure is non-fatal here
            pass
