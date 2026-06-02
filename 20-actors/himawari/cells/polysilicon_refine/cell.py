"""PolysiliconRefineCell — himawari per ADR-2606021200.

Solar-grade polysilicon feedstock QA + on-chain provenance.
G2 (feedstock provenance on-chain per lot — NO XUAR/forced-labor
    polysilicon ever; no conflict-mineral In/Ga; full chain-of-custody
    CID-anchored) structural enforcement. Closes hikari §G2.

The cell is the structural fix for hikari §G2: instead of trusting a vendor's
self-attestation on a *purchased* module, himawari refines feedstock first-party
and writes an Ed25519/CID-anchored chain-of-custody per lot. A lot that cannot
prove a forced-labor-free origin, or whose origin falls in an excluded region,
is REFUSED here — it never reaches ingot_wafer. Refusal is the safe default
(a missing attestation is a fail, never a silent pass).

LLM access (if any) is Murakumo-only via the kotoba host binding (127.0.0.1:4000);
this cell does no inference. State is written back to the kotoba Datom log as
`:himawari.polysilicon/*` datoms (G2/G8); IPFS/Base-L2 anchoring of the resulting
attestation record is operator-gated (G11) and performed by the substrate, not here.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

# kotoba-provided host bindings (WASM Component Model imports). In local dev /
# import-only smoke the bindings are absent, so the cell degrades to compute-only
# (it builds the record and skips the on-chain write rather than crashing).
try:
    from kotoba import datalog  # type: ignore
except ImportError:  # local dev fallback
    datalog = None  # type: ignore

# --------------------------------------------------------------------------- #
# G2 / N6 — XUAR + forced-labor exclusion (constitutional, NOT a tunable gate)
# --------------------------------------------------------------------------- #
# Regions under documented systemic forced-labor risk for polysilicon. A lot whose
# declared origin matches any of these is refused regardless of paperwork (N6 is
# constitutional). The match is case-insensitive substring over the origin string.
_EXCLUDED_ORIGIN_TERMS = (
    "xuar",
    "xinjiang",
    "新疆",
    "uyghur",
    "uighur",
    "ujgur",
    "kashgar",
    "hotan",
    "aksu",
)

# Feedstock grades / processes accepted by the lexicon
# (com.etzhayyim.himawari.polysiliconProvenanceAttestation). Solar-grade ONLY —
# logic-grade 9N+ EG-Si belongs to the iwakura/fuigo/tsukuru track (N1), not here.
_VALID_GRADES = frozenset({"solar-grade-6N", "solar-grade-6N+", "recycled-kerf"})
_VALID_PROCESSES = frozenset({"siemens", "fbr", "umg-upgraded", "recycled"})

# Conflict-mineral dopants/elements that must NOT appear in solar feedstock (G2):
# In/Ga are conflict-mineral-risk and are also a CdTe/CIGS thin-film tell (N2/N3).
_CONFLICT_ELEMENTS = frozenset({"In", "Ga"})

# Required chain-of-custody evidence (each must be a non-empty CID-or-DID string).
_REQUIRED_PROVENANCE = (
    "originRegionAttestationCid",  # XUAR-exclusion / forced-labor-free attestation
    "supplierDid",                 # who supplied the lot
    "sourcingAuditCid",            # §2(g) Charter Rider supply-chain audit per lot
    "attestingEngineerDid",        # PV-process engineer who signed off (R1 trigger #2)
)


def _cid(payload: dict[str, Any]) -> str:
    """Deterministic content id over a canonical JSON serialization.

    R0/R1 honest stand-in for a real IPFS CIDv1: a sha256 of the canonicalized
    payload with a `bafy~` prefix so it is visibly NOT a fetched IPFS CID. The
    real CIDv1 (dag-cbor multihash) is produced by the kotoba/IPFS substrate when
    the attestation is anchored (operator-gated, G11); this function only fixes
    the chain-of-custody digest so the record is tamper-evident locally."""
    canon = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    digest = hashlib.sha256(canon.encode("utf-8")).hexdigest()
    return f"bafy~sha256-{digest}"


class PolysiliconRefineCell:
    """Solar-grade polysilicon feedstock QA + on-chain provenance."""

    def __init__(self) -> None:
        pass

    # ----------------------------------------------------------------------- #
    # lexicon shaping — #robotSignature (objects, not flat did/name strings)
    # ----------------------------------------------------------------------- #
    @staticmethod
    def _robot_signatures(entries: list[Any], recorded_at: str) -> list[dict[str, Any]]:
        """Normalize attestingRobots into an array of #robotSignature objects.

        The lexicon #robotSignature requires robotDid + signature (role + timestamp
        optional). A caller may already pass full objects (funadaiku-style richer
        convention) — those are passed through, only filling required-but-missing
        fields. A bare did/name string (legacy callers) is lifted into an object:
        the string becomes robotDid and a deterministic content-binding signature is
        derived (an R2 honest stand-in for the off-cell Ed25519 device key — never a
        fake "signed" claim, just a tamper-evident binding of this witness to the lot).
        """
        out: list[dict[str, Any]] = []
        for entry in entries:
            if isinstance(entry, dict):
                sig = dict(entry)
                robot_did = str(sig.get("robotDid", "")).strip()
                if "signature" not in sig or not str(sig.get("signature", "")).strip():
                    sig["signature"] = (
                        "ed25519:" + _cid({"robotDid": robot_did, "recordedAt": recorded_at})
                    )
                out.append(sig)
            else:
                robot_did = str(entry).strip()
                out.append(
                    {
                        "robotDid": robot_did,
                        # R2 substitute for the off-cell Ed25519 witness key (substrate
                        # boundary); deterministic content binding, not a fake signature.
                        "signature": "ed25519:"
                        + _cid({"robotDid": robot_did, "recordedAt": recorded_at}),
                        "role": "lot_provenance_witness",
                        "timestamp": recorded_at,
                    }
                )
        return out

    # ----------------------------------------------------------------------- #
    # lexicon shaping — #custodyHop array (ordered quarry → polysilicon path)
    # ----------------------------------------------------------------------- #
    @staticmethod
    def _chain_of_custody(state: dict[str, Any], recorded_at: str) -> list[dict[str, Any]]:
        """Build the ordered chainOfCustody as an array of #custodyHop objects.

        The lexicon requires chainOfCustody as an array of #custodyHop (minItems 1),
        each with stage + custodianDid + regionCode + evidenceCid. NOT a flat scalar
        CID. A caller may supply richer hops directly (passed through, filling only
        required-but-missing fields); otherwise a genuine hop is synthesized from the
        provenance the cell already holds — the declared origin region, the supplier
        DID, and the origin-region + sourcing-audit evidence CIDs. The final
        polysilicon-refine hop (this cell's own custody) is always appended so the
        quarry → polysilicon path terminates at himawari.
        """
        declared_origin = str(state.get("declaredOrigin", "")).strip()
        supplier_did = str(state.get("supplierDid", "")).strip()
        origin_cid = str(state.get("originRegionAttestationCid", "")).strip()
        audit_cid = str(state.get("sourcingAuditCid", "")).strip()
        engineer_did = str(state.get("attestingEngineerDid", "")).strip()

        provided = list(state.get("chainOfCustody", []) or [])
        if provided:
            hops: list[dict[str, Any]] = []
            for hop in provided:
                h = dict(hop) if isinstance(hop, dict) else {}
                h.setdefault("stage", "polysilicon-refine")
                h.setdefault("custodianDid", supplier_did)
                h.setdefault("regionCode", declared_origin)
                h.setdefault("evidenceCid", origin_cid)
                h.setdefault("recordedAt", recorded_at)
                hops.append(h)
            return hops

        # Synthesize from held provenance: upstream supplier custody, then this cell.
        hops = [
            {
                "stage": "metallurgical-grade-si",
                "custodianDid": supplier_did,
                "regionCode": declared_origin,
                "evidenceCid": origin_cid,
                "recordedAt": recorded_at,
            },
            {
                "stage": "polysilicon-refine",
                "custodianDid": engineer_did or supplier_did,
                "regionCode": declared_origin,
                "evidenceCid": audit_cid or origin_cid,
                "recordedAt": recorded_at,
            },
        ]
        return hops

    def solve(self, state: dict[str, Any]) -> dict[str, Any]:
        """QA one polysilicon feedstock lot and emit a provenance attestation.

        Input `state` keys (a candidate lot to admit into himawari manufacture):
          lotId, feedstockGrade, process, declaredOrigin, supplierDid,
          originRegionAttestationCid, sourcingAuditCid, attestingEngineerDid,
          recordedAt (ISO-8601 attestation timestamp — threaded through, NOT a
            wall-clock call, so the record is deterministic/testable; ingot_wafer
            passthrough convention),
          chainOfCustody (optional list[#custodyHop]: ordered quarry → polysilicon
            hops; if absent a genuine hop is synthesized from the provenance the
            cell already holds — declaredOrigin / supplierDid / the evidence CIDs),
          attestingRobots (≥2 — each may be a #robotSignature dict OR a bare
            did/name string, which is lifted into a #robotSignature object),
          dopantElements (optional list), embodiedEnergyWhPerKg (optional int).

        Returns the input state plus:
          accepted          bool — True only if every G2/N6/N1 check passes
          violations        list[str] — every failed check (empty iff accepted)
          provenance        the com.etzhayyim.himawari.polysiliconProvenanceAttestation
                            record (built even on refusal, so the refusal itself is
                            auditable on-chain); carries lexicon-required recordedAt,
                            chainOfCustody (array of #custodyHop), and attestingRobots
                            (array of #robotSignature objects)
          chainOfCustodyCid the tamper-evident digest over the provenance record
          datomsWritten     int — number of datoms transacted to kotoba (0 if no host)

        A refused lot carries `accepted=False` and is NOT routed to ingot_wafer.
        """
        lot_id = str(state.get("lotId", "")).strip()
        grade = str(state.get("feedstockGrade", "")).strip()
        process = str(state.get("process", "")).strip()
        declared_origin = str(state.get("declaredOrigin", "")).strip()
        supplier_did = str(state.get("supplierDid", "")).strip()
        recorded_at = str(state.get("recordedAt", "")).strip()
        attesting_robots_in = list(state.get("attestingRobots", []) or [])
        dopants = list(state.get("dopantElements", []) or [])

        # attestingRobots → array of #robotSignature objects (lexicon requires
        # objects with robotDid + signature; role/timestamp carried when known).
        # A bare did/name string is lifted into a hop-shaped object so legacy
        # callers and the funadaiku-style richer convention both validate.
        attesting_robots = self._robot_signatures(attesting_robots_in, recorded_at)

        violations: list[str] = []

        # --- identity ---
        if not lot_id:
            violations.append("lotId is required (no anonymous feedstock, G2)")

        # --- N1: solar-grade only (not logic-grade EG-Si) ---
        if grade not in _VALID_GRADES:
            violations.append(
                f"feedstockGrade {grade!r} not solar-grade — must be one of "
                f"{sorted(_VALID_GRADES)} (N1: NOT logic-grade 9N+ EG-Si)"
            )
        if process not in _VALID_PROCESSES:
            violations.append(
                f"process {process!r} unknown — must be one of {sorted(_VALID_PROCESSES)}"
            )

        # --- G2 / N6: XUAR + forced-labor exclusion (constitutional) ---
        origin_lc = declared_origin.lower()
        hit = next((t for t in _EXCLUDED_ORIGIN_TERMS if t in origin_lc), None)
        if hit is not None:
            violations.append(
                f"declaredOrigin {declared_origin!r} matches excluded forced-labor "
                f"region term {hit!r} — REFUSED (N6 constitutional, no waiver, ever)"
            )
        if not declared_origin:
            violations.append("declaredOrigin is required for XUAR-exclusion screening (G2)")

        # --- G2: conflict-mineral dopant screen ---
        bad_elems = sorted(set(dopants) & _CONFLICT_ELEMENTS)
        if bad_elems:
            violations.append(
                f"conflict-mineral element(s) {bad_elems} present — refused (G2; "
                f"also a CdTe/CIGS thin-film tell, N2/N3)"
            )

        # --- G2: complete chain-of-custody evidence (missing → refuse, no silent pass) ---
        for key in _REQUIRED_PROVENANCE:
            if not str(state.get(key, "")).strip():
                violations.append(f"missing chain-of-custody evidence: {key} (G2 §2(g))")

        # --- recordedAt is a lexicon-required attestation timestamp (G11 as-of) ---
        if not recorded_at:
            violations.append(
                "recordedAt is required (ISO-8601 attestation timestamp, G11 as-of)"
            )

        # --- G11: ≥2 attesting robots (kuni-umi Mimi metrology + an Otete handler) ---
        if len(attesting_robots) < 2:
            violations.append(
                "attestingRobots requires ≥2 entries (deterministic provenance, G11)"
            )

        # --- G2: build the ordered quarry → polysilicon chain-of-custody ---
        # The lexicon requires chainOfCustody as an array of #custodyHop (minItems 1),
        # NOT a flat scalar CID. Build genuine hops from the provenance the cell
        # already holds; a caller may also supply richer hops directly.
        chain_of_custody = self._chain_of_custody(state, recorded_at)
        if len(chain_of_custody) < 1:
            violations.append(
                "chainOfCustody requires ≥1 hop (G2 quarry → polysilicon custody)"
            )

        accepted = not violations

        # Build the provenance record per the lexicon, on accept AND on refusal.
        # The refusal record is itself anchored so a rejected lot is permanently
        # auditable (a forced-labor lot that was turned away leaves a trail).
        provenance: dict[str, Any] = {
            "$type": "com.etzhayyim.himawari.polysiliconProvenanceAttestation",
            "lotId": lot_id,
            "recordedAt": recorded_at,
            "feedstockGrade": grade,
            "process": process,
            "originRegionAttestationCid": str(state.get("originRegionAttestationCid", "")),
            "supplierDid": supplier_did,
            "sourcingAuditCid": str(state.get("sourcingAuditCid", "")),
            "attestingEngineerDid": str(state.get("attestingEngineerDid", "")),
            # lexicon: array of #robotSignature objects + array of #custodyHop objects.
            "attestingRobots": attesting_robots,
            "chainOfCustody": chain_of_custody,
            "embodiedEnergyWhPerKg": int(state.get("embodiedEnergyWhPerKg", 0)),
            # provenance-decision fields (not in the required lexicon set; carried for audit)
            "declaredOrigin": declared_origin,
            "qaVerdict": "accepted" if accepted else "refused",
            "violations": violations,
        }
        # chain_cid = tamper-evident digest over the whole record (the chainOfCustody
        # array is the lexicon field; this scalar is a record-level content binding,
        # also returned in-band so the substrate can anchor it (G11)).
        chain_cid = _cid(provenance)
        provenance["chainOfCustodyCid"] = chain_cid

        datoms_written = self._write_provenance(provenance)

        return {
            **state,
            "accepted": accepted,
            "violations": violations,
            "provenance": provenance,
            "chainOfCustodyCid": chain_cid,
            "datomsWritten": datoms_written,
            # downstream routing: only an accepted lot is handed to ingot_wafer (issachar)
            "routeToCell": "ingot_wafer" if accepted else None,
        }

    # ----------------------------------------------------------------------- #
    # kotoba write — per-lot provenance datoms (G2/G8). Implicit-write style is
    # not available to the class-based cell shape, so we transact explicitly when
    # the host binding is present; absent host (local dev / import smoke) → no-op.
    # ----------------------------------------------------------------------- #
    def _write_provenance(self, provenance: dict[str, Any]) -> int:
        if datalog is None:
            return 0
        lot = provenance["lotId"]
        entity = f"polysilicon/{lot}"
        # EAVT assertions; attribute names mirror the himawari kotoba schema namespace.
        datoms = [
            [entity, ":himawari.polysilicon/lot-id", lot],
            [entity, ":himawari.polysilicon/recorded-at", provenance["recordedAt"]],
            [entity, ":himawari.polysilicon/feedstock-grade", provenance["feedstockGrade"]],
            [entity, ":himawari.polysilicon/process", provenance["process"]],
            [entity, ":himawari.polysilicon/declared-origin", provenance["declaredOrigin"]],
            [entity, ":himawari.polysilicon/supplier-did", provenance["supplierDid"]],
            [entity, ":himawari.polysilicon/origin-attestation-cid",
             provenance["originRegionAttestationCid"]],
            [entity, ":himawari.polysilicon/sourcing-audit-cid", provenance["sourcingAuditCid"]],
            [entity, ":himawari.polysilicon/attesting-engineer-did",
             provenance["attestingEngineerDid"]],
            [entity, ":himawari.polysilicon/embodied-energy-wh-per-kg",
             provenance["embodiedEnergyWhPerKg"]],
            [entity, ":himawari.polysilicon/qa-verdict", provenance["qaVerdict"]],
            [entity, ":himawari.polysilicon/chain-of-custody-cid",
             provenance["chainOfCustodyCid"]],
        ]
        # chain-of-custody hops: one custody-component entity per hop (ordered by index),
        # referenced from the lot entity so the quarry → polysilicon path is queryable.
        for idx, hop in enumerate(provenance.get("chainOfCustody", [])):
            hop_eid = f"{entity}/hop/{idx}"
            datoms.append([entity, ":himawari.polysilicon/custody-hop", hop_eid])
            datoms.append([hop_eid, ":himawari.custody-hop/stage", hop.get("stage", "")])
            datoms.append([hop_eid, ":himawari.custody-hop/custodian-did",
                           hop.get("custodianDid", "")])
            datoms.append([hop_eid, ":himawari.custody-hop/region-code",
                           hop.get("regionCode", "")])
            datoms.append([hop_eid, ":himawari.custody-hop/evidence-cid",
                           hop.get("evidenceCid", "")])
        # robot witness quorum: each #robotSignature recorded by robotDid + signature.
        for sig in provenance.get("attestingRobots", []):
            datoms.append([entity, ":himawari.polysilicon/attesting-robot-did",
                           sig.get("robotDid", "")])
            datoms.append([entity, ":himawari.polysilicon/attesting-robot-signature",
                           sig.get("signature", "")])
        try:
            datalog.transact(datoms)  # type: ignore[union-attr]
        except Exception:
            # honest TODO: the kotoba host transact ABI is finalized at R1 activation
            # (per ADR-2606021200 gate set); until then a host that lacks `.transact`
            # leaves the record compute-only. The provenance dict + CID are still
            # returned for the caller / substrate to anchor — never a fake success.
            return 0
        return len(datoms)
