"""Lock-in tests for akashi (証) public ad-disclosure invariants.

Pins the R0 properties from ADR-2606022300 so future work cannot silently turn
akashi into an ad network, voter-profile system, commercial ad-intel product,
or unreviewed malak intake.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parents[3]
_LEX = _REPO / "00-contracts" / "lexicons" / "app" / "etzhayyim" / "akashi"
_MANIFEST = _REPO / "20-actors" / "akashi" / "manifest.jsonld"
_SOURCE_CATALOG = _REPO / "20-actors" / "akashi" / "registry" / "source-catalog.seed.json"
_METHOD_SEED = _REPO / "20-actors" / "akashi" / "methods" / "v1-r0-seed.json"

_EXPECTED_LEXICONS = {
    "sourcePolicySnapshot",
    "adDisclosureSnapshot",
    "advertiserIdentity",
    "creativeDisclosure",
    "deliveryDisclosure",
    "landingEvidence",
    "adDisclosureLink",
    "methodNote",
    "adTransparencyReport",
    "malakEvidenceCandidate",
}

_FORBIDDEN_PROFILE_WORDS = {
    "voter",
    "persuasion",
    "supporter",
    "opponent",
    "psychographic",
    "profileScore",
    "politicalInterest",
    "personCohort",
}


def _load(path: Path) -> dict:
    return json.loads(path.read_text())


def _props(lex: dict) -> dict:
    return lex["defs"]["main"]["record"]["properties"]


def _required(lex: dict) -> list[str]:
    return lex["defs"]["main"]["record"].get("required", [])


def test_manifest_gates_and_namespaces_match_disk():
    manifest = _load(_MANIFEST)
    gates = manifest["constitutionalDiscipline"]
    assert len(gates) == 13
    for key in (
        "passiveOnly",
        "sourceProvenanceMandatory",
        "nonAdjudicating",
        "noPoliticalProfiling",
        "noTargetLists",
        "openMethod",
        "sourcePolicyRequired",
        "noAdSdk",
        "noCommercialAdIntel",
        "publicRecordMinimization",
        "murakumoOnlyInference",
        "transparentForce",
        "malakBridgeReview",
    ):
        assert key in gates

    namespaces = manifest["lexiconNamespaces"]
    assert len(namespaces) == len(_EXPECTED_LEXICONS)
    assert {n.split(".")[-1] for n in namespaces} == _EXPECTED_LEXICONS
    for leaf in _EXPECTED_LEXICONS:
        assert (_LEX / f"{leaf}.json").exists(), f"missing lexicon {leaf}"


def test_lexicon_ids_match_namespace_and_are_records():
    files = sorted(_LEX.glob("*.json"))
    assert {p.stem for p in files} == _EXPECTED_LEXICONS
    for path in files:
        lex = _load(path)
        assert lex.get("lexicon") == 1
        assert lex["id"] == f"app.etzhayyim.akashi.{path.stem}"
        assert lex["defs"]["main"]["type"] == "record"
        assert isinstance(_props(lex), dict) and _props(lex)


def test_no_float_types_and_no_profile_fields():
    for path in _LEX.glob("*.json"):
        text = path.read_text()
        assert '"type": "number"' not in text, f"{path.name}: no float types"
        for word in _FORBIDDEN_PROFILE_WORDS:
            assert word not in text, f"{path.name}: forbidden profiling token {word}"


def test_source_policy_required_before_snapshot():
    source_policy = _load(_LEX / "sourcePolicySnapshot.json")
    snapshot = _load(_LEX / "adDisclosureSnapshot.json")

    for field in ("accessMode", "collectionStatus", "methodNoteCid", "attestingDid"):
        assert field in _required(source_policy)

    assert "sourcePolicyCid" in _required(snapshot)
    assert "payloadCid" in _required(snapshot)
    assert "payloadSha256" in _required(snapshot)

    access_modes = _props(source_policy)["accessMode"]["knownValues"]
    assert "disabled" in access_modes
    assert "manual-review-only" in access_modes


def test_non_adjudicating_records_are_structurally_const_true():
    for name in ("adDisclosureLink", "adTransparencyReport", "malakEvidenceCandidate"):
        lex = _load(_LEX / f"{name}.json")
        assert "nonAdjudicatingNotice" in _required(lex), name
        field = _props(lex)["nonAdjudicatingNotice"]
        assert field["type"] == "boolean"
        assert field["const"] is True


def test_malak_candidate_review_gate_and_source_cids():
    lex = _load(_LEX / "malakEvidenceCandidate.json")
    req = set(_required(lex))
    assert {"sourceCids", "reviewStatus", "nonAdjudicatingNotice", "methodNoteCid"} <= req
    assert _props(lex)["sourceCids"]["minLength"] == 2
    assert _props(lex)["reviewStatus"]["knownValues"] == [
        "candidate-only",
        "human-reviewed",
        "malak-imported",
        "rejected",
    ]


def test_source_catalog_is_planning_only_and_manual_review():
    catalog = _load(_SOURCE_CATALOG)
    assert catalog["status"] == "planning-seed"
    sources = catalog["sources"]
    assert {s["id"] for s in sources} >= {
        "meta-ad-library",
        "x-ads-transparency",
        "line-ad-disclosure",
        "google-ad-transparency",
        "tiktok-commercial-content-library",
        "regulator-ad-repositories",
    }
    for source in sources:
        assert source["collectionStatus"] == "manual-review"
        assert source["r0Coverage"] in {"registry-only", "preferred-future-source"}
        assert "fixture-parser" in source["requiredBeforeCollection"]


def test_method_seed_outputs_existing_lexicons():
    seed = _load(_METHOD_SEED)
    assert seed["status"] == "reserved"
    outputs = {m["output"].split(".")[-1] for m in seed["methods"]}
    assert outputs <= _EXPECTED_LEXICONS
    assert {"sourcePolicySnapshot", "adDisclosureSnapshot", "adDisclosureLink", "malakEvidenceCandidate"} <= outputs


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
