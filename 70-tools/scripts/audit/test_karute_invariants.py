"""Lock-in tests for the karute (電子カルテ / EMR) constitutional invariants.

karute is the FHIR-mapped clinical-record lexicon layer (ADR-2605231100); every
record is PHI and MUST flow through the com.etzhayyim.encrypted.record envelope
(ADR-2605181100). Two invariant families are pinned here:

  1. FHIR binding — each karute lexicon pins `fhirResourceType` const to its
     exact FHIR resource type (an interop invariant: a drifted resourceType
     silently breaks every downstream FHIR Bundle). homeVisit also pins
     encounterClass=home; soapNote pins compositionType=SOAP.

  2. PHI-plaintext-guard COVERAGE — the karute-phi-plaintext-guard lefthook
     blocks plaintext writes to com.etzhayyim.karute.* outside the encrypted
     envelope. Its detection regex + inner-types list MUST cover EXACTLY the set
     of karute lexicons on disk. This is the constitutional safety property:
     a clinical lexicon the guard does not list is a silent PHI-plaintext leak
     (the gap this suite was written to close — carePlan / homecareEpisode /
     homeVisit were unguarded until this commit).

No floats (Lexicon v1, ADR-2605190900); each id matches its namespace.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parents[3]
_LEX = _REPO / "00-contracts" / "lexicons" / "com" / "etzhayyim" / "karute"
_GUARD = _REPO / "70-tools" / "scripts" / "lint" / "karute-phi-plaintext-guard.mjs"

# Designed FHIR resource-type binding per karute lexicon (filename stem → const).
_FHIR_MAP = {
    "patient": "Patient",
    "encounter": "Encounter",
    "soapNote": "Composition",
    "observation": "Observation",
    "condition": "Condition",
    "medicationRequest": "MedicationRequest",
    "serviceRequest": "ServiceRequest",
    "dispenseRecord": "MedicationDispense",
    "carePlan": "CarePlan",
    "homecareEpisode": "EpisodeOfCare",
    "homeVisit": "Encounter",
}


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


def _lexicon_stems() -> set[str]:
    return {p.stem for p in _LEX.glob("*.json")}


# ─── 1. FHIR resourceType binding ───────────────────────────────────────


class TestFhirBinding:
    def test_lexicon_set_matches_expected_map(self):
        # If a lexicon is added/removed, _FHIR_MAP must be updated deliberately.
        assert _lexicon_stems() == set(_FHIR_MAP), (
            f"karute lexicon set drifted from _FHIR_MAP: {_lexicon_stems() ^ set(_FHIR_MAP)}"
        )

    @pytest.mark.parametrize("stem,fhir", sorted(_FHIR_MAP.items()))
    def test_each_lexicon_pins_its_fhir_resource_type(self, stem, fhir):
        rec = _load(_LEX / f"{stem}.json")["defs"]["main"]["record"]
        got = rec["properties"]["fhirResourceType"].get("const")
        assert got == fhir, f"{stem}: fhirResourceType const must be {fhir!r}, got {got!r}"

    def test_home_visit_and_soap_secondary_consts(self):
        hv = _load(_LEX / "homeVisit.json")["defs"]["main"]["record"]
        assert hv["properties"]["encounterClass"].get("const") == "home"
        sn = _load(_LEX / "soapNote.json")["defs"]["main"]["record"]
        assert sn["properties"]["compositionType"].get("const") == "SOAP"

    def test_each_id_matches_namespace(self):
        for p in _LEX.glob("*.json"):
            assert _load(p)["id"] == f"com.etzhayyim.karute.{p.stem}"


# ─── 2. no floats (Lexicon v1) ──────────────────────────────────────────


class TestNoFloatTypes:
    @pytest.mark.parametrize("path", sorted(_LEX.glob("*.json")))
    def test_no_number_type(self, path):
        bad = [n for n in _walk(_load(path)) if n.get("type") == "number"]
        assert not bad, f"{path.name}: no `type: number` (ADR-2605190900); found {len(bad)}"


# ─── 3. PHI-plaintext-guard coverage (the constitutional safety property) ─


def _guard_regex_types() -> set[str]:
    src = _GUARD.read_text()
    m = re.search(r"karute\\\.\(([^)]+)\)\\b", src)
    assert m, "could not locate KARUTE_TYPE_PATTERN alternation in the guard"
    return set(m.group(1).split("|"))


def _guard_list_types() -> set[str]:
    src = _GUARD.read_text()
    block = re.search(r"KARUTE_INNER_TYPES\s*=\s*\[(.*?)\]", src, re.S)
    assert block, "could not locate KARUTE_INNER_TYPES array in the guard"
    return set(re.findall(r"com\.etzhayyim\.karute\.(\w+)", block.group(1)))


class TestPhiGuardCoverage:
    def test_guard_exists(self):
        assert _GUARD.exists(), "karute-phi-plaintext-guard.mjs must exist"

    def test_detection_regex_covers_every_lexicon(self):
        # The constitutional invariant: every karute clinical lexicon is matched
        # by the guard's detection regex. A lexicon NOT here is a silent PHI leak.
        assert _guard_regex_types() == _lexicon_stems(), (
            "PHI-guard detection regex vs karute lexicons drifted "
            f"(unguarded = potential plaintext PHI leak): {_guard_regex_types() ^ _lexicon_stems()}"
        )

    def test_inner_types_list_covers_every_lexicon(self):
        assert _guard_list_types() == _lexicon_stems(), (
            f"KARUTE_INNER_TYPES list vs karute lexicons drifted: {_guard_list_types() ^ _lexicon_stems()}"
        )

    def test_regex_and_list_agree(self):
        # The messaging list and the detection regex must not diverge.
        assert _guard_regex_types() == _guard_list_types(), (
            f"guard regex vs inner-types list drifted: {_guard_regex_types() ^ _guard_list_types()}"
        )
