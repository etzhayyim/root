"""Lock-in tests for the iyashi (癒 / clinical care provider) constitutional invariants.

iyashi is the clinical-encounter provider procedural + attestation substrate (NOT
a state-licensed medical entity; ADR-2605263000). Five structural discipline
boundaries (CLAUDE.md "Constitutional Discipline"): encrypted PHI envelope (G2),
no commercial EHR (G11), no insurance billing (G13), no provider payroll —
vocation-flow stewards (G14), Murakumo-only inference (G12). This suite pins the
schema-enforceable ones. Mirrors tadori/tsukuroi/karute/kokoro lock-in suites.

  1. Structural PHI encryption — clinical-content lexicons require
     encryptedPayloadCid + a pseudonym subject + a consent CID (ADR-2605181100).
  2. No commercial EHR (G11) — clinicFacilityAttestation.commercialEhrNoneInstalled
     const true; silenIyashiReview.commercialEhrPenetrationBps const 0.
  3. Vocation-flow, not payroll (G14) — providerAttestation pins
     employmentRelation const "vocation-flow" + lLevel const "L5".
  4. No floats; id↔namespace; manifest namespaces match disk (incl. the
     phlebotomyAttestation that this commit re-declared); DID/name.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parents[3]
_LEX = _REPO / "00-contracts" / "lexicons" / "com" / "etzhayyim" / "iyashi"
# manifest invariants → 20-actors/iyashi/methods/test_manifest_invariants.cljc (jsonld retired)

# Lexicons whose payload is clinical content and MUST stay in the encrypted envelope.
_PHI_CONTENT = ["clinicalEncounterAttestation", "chronicCareContinuityRecord"]


def _load(p: Path) -> dict:
    return json.loads(p.read_text())


def _walk(node):
    if isinstance(node, dict):
        yield node
        for v in node.values():
            yield from _walk(v)
    elif isinstance(node, list):
        for v in node:
            yield from _walk(v)


def _rec(stem: str) -> dict:
    return _load(_LEX / f"{stem}.json")["defs"]["main"]["record"]


# ─── 1. structural PHI encryption (G2) ──────────────────────────────────


class TestPhiEncryption:
    @pytest.mark.parametrize("stem", _PHI_CONTENT)
    def test_requires_encrypted_payload_and_consent_and_pseudonym(self, stem):
        req = set(_rec(stem)["required"])
        assert "encryptedPayloadCid" in req, f"{stem}: G2 encrypted envelope mandatory"
        assert "consentRecordCid" in req, f"{stem}: consent CID required"
        assert "patientPseudonymDid" in req, f"{stem}: subject is a pseudonym DID (min disclosure)"

    @pytest.mark.parametrize("stem", ["vaccinationAttestation", "phlebotomyAttestation"])
    def test_clinical_events_are_pseudonymized_and_consented(self, stem):
        req = set(_rec(stem)["required"])
        assert "patientPseudonymDid" in req, f"{stem}: subject is a pseudonym DID"
        assert "consentRecordCid" in req or "orderRefCid" in req, (
            f"{stem}: must carry a consent / order reference"
        )


# ─── 2. no commercial EHR (G11) ─────────────────────────────────────────


class TestNoCommercialEhr:
    def test_facility_attests_no_commercial_ehr(self):
        p = _rec("clinicFacilityAttestation")["properties"]["commercialEhrNoneInstalled"]
        assert p.get("const") is True, (
            "G11: Epic/Cerner/Athena/Allscripts/etc. PROHIBITED (Charter Rider §2(e))"
        )

    def test_review_pins_zero_commercial_ehr_penetration(self):
        p = _rec("silenIyashiReview")["properties"]["commercialEhrPenetrationBps"]
        assert p.get("const") == 0, "G11: commercial-EHR penetration must be const 0 bps"


# ─── 3. vocation-flow, not payroll (G14) ────────────────────────────────


class TestVocationFlowNotPayroll:
    def test_provider_employment_relation_is_vocation_flow(self):
        p = _rec("providerAttestation")["properties"]["employmentRelation"]
        assert p.get("const") == "vocation-flow", (
            "G14: providers are vocation-flow stewards, NOT employees (no payroll/wage)"
        )

    def test_provider_l_level_is_l5(self):
        p = _rec("providerAttestation")["properties"]["lLevel"]
        assert p.get("const") == "L5", "providers are Liberation-Ladder L5 stewards"


# ─── 4. hygiene + manifest consistency ──────────────────────────────────


class TestHygieneAndManifest:
    @pytest.mark.parametrize("path", sorted(_LEX.glob("*.json")))
    def test_no_number_type(self, path):
        bad = [n for n in _walk(_load(path)) if n.get("type") == "number"]
        assert not bad, f"{path.name}: no `type: number` (ADR-2605190900); found {len(bad)}"

    def test_each_id_matches_namespace(self):
        for p in _LEX.glob("*.json"):
            assert _load(p)["id"] == f"com.etzhayyim.iyashi.{p.stem}"

