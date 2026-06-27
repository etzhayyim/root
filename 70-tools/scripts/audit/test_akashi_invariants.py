"""Lock-in tests for akashi (証) public ad-disclosure invariants.

Pins the R0 properties from ADR-2606022300 so future work cannot silently turn
akashi into an ad network, voter-profile system, commercial ad-intel product,
or unreviewed malak intake.
"""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parents[3]
_LEX = _REPO / "00-contracts" / "lexicons" / "com" / "etzhayyim" / "akashi"
# manifest invariants -> 20-actors/akashi/methods/test_manifest_invariants.cljc (jsonld retired)
_SOURCE_CATALOG = _REPO / "20-actors" / "akashi" / "registry" / "source-catalog.seed.json"
_SOURCE_POLICY_REVIEWS = (
    _REPO / "20-actors" / "akashi" / "registry" / "source-policy-reviews.seed.json"
)
_SOURCE_POLICY_APPROVAL_SCHEMA = (
    _REPO / "20-actors" / "akashi" / "registry" / "source-policy-approval.schema.json"
)
_SOURCE_POLICY_APPROVAL_EXAMPLE = (
    _REPO
    / "20-actors"
    / "akashi"
    / "registry"
    / "source-policy-approval.fixture-only.example.json"
)
_METHOD_SEED = _REPO / "20-actors" / "akashi" / "methods" / "v1-r0-seed.json"
_ADAPTER = (
    _REPO
    / "20-actors"
    / "akashi"
    / "adapters"
    / "regulator_bulk_fixture_parser.py"
)
_VALIDATOR = (
    _REPO / "20-actors" / "akashi" / "adapters" / "lexicon_shape_validator.py"
)
_DRY_RUN = _REPO / "20-actors" / "akashi" / "adapters" / "dry_run_fixtures.py"
_FIXTURE = (
    _REPO
    / "20-actors"
    / "akashi"
    / "fixtures"
    / "regulator_bulk"
    / "sample.json"
)
_MISSING_OPTIONAL_FIXTURE = (
    _REPO
    / "20-actors"
    / "akashi"
    / "fixtures"
    / "regulator_bulk"
    / "missing_optional_fields.json"
)
_NEGATIVE_MISSING_LANDING_URL = (
    _REPO
    / "20-actors"
    / "akashi"
    / "fixtures"
    / "regulator_bulk"
    / "negative_missing_landing_url.json"
)
_CLOSURE_FIXTURE = (
    _REPO / "20-actors" / "akashi" / "fixtures" / "closure" / "sample.json"
)
_NEGATIVE_MALAK_IMPORTED = (
    _REPO / "20-actors" / "akashi" / "fixtures" / "closure" / "negative_malak_imported.json"
)
_DRY_RUN_GOLDEN = (
    _REPO / "20-actors" / "akashi" / "fixtures" / "dry_run" / "summary.golden.json"
)
_CELLS = _REPO / "20-actors" / "kotodama" / "cells"

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

_CELL_NAMES = {
    "akashi_source_registry",
    "akashi_disclosure_fetch",
    "akashi_normalize_creative",
    "akashi_landing_evidence",
    "akashi_cross_platform_link",
    "akashi_transparency_report",
    "akashi_malak_evidence_bridge",
}


def _load(path: Path) -> dict:
    return json.loads(path.read_text())


def _props(lex: dict) -> dict:
    return lex["defs"]["main"]["record"]["properties"]


def _required(lex: dict) -> list[str]:
    return lex["defs"]["main"]["record"].get("required", [])


def test_lexicon_ids_match_namespace_and_are_records():
    files = sorted(_LEX.glob("*.json"))
    assert {p.stem for p in files} == _EXPECTED_LEXICONS
    for path in files:
        lex = _load(path)
        assert lex.get("lexicon") == 1
        assert lex["id"] == f"com.etzhayyim.akashi.{path.stem}"
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
        assert source["r0Coverage"] in {
            "registry-only",
            "preferred-future-source",
            "fixture-parser",
        }
        assert "fixture-parser" in source["requiredBeforeCollection"]


def test_source_policy_review_workflow_keeps_live_collection_disabled():
    catalog = _load(_SOURCE_CATALOG)
    reviews = _load(_SOURCE_POLICY_REVIEWS)
    source_ids = {source["id"] for source in catalog["sources"]}
    review_ids = {review["sourceId"] for review in reviews["reviews"]}

    assert reviews["status"] == "r0-review-workflow"
    assert reviews["defaultLiveCollectionStatus"] == "disabled"
    assert reviews["disableWithoutCodeChange"] is True
    assert review_ids == source_ids
    assert "fixture-parser" in reviews["requiredEvidenceBeforeAllowed"]
    assert "method-note" in reviews["requiredEvidenceBeforeAllowed"]

    for review in reviews["reviews"]:
        assert review["liveCollectionStatus"] == "disabled"
        assert review["reviewTx"] == "reserved"
        assert review["reviewStatus"] in {"manual-review", "fixture-only", "disabled"}
        assert review["adapterRuntime"] in {"disabled", "fixture-only"}
        if review["sourceId"] != "regulator-ad-repositories":
            assert review["approvedAccessModes"] == []
            assert review["adapterRuntime"] == "disabled"


def test_source_policy_approval_tx_format_is_fixture_only_at_r0():
    catalog = _load(_SOURCE_CATALOG)
    schema = _load(_SOURCE_POLICY_APPROVAL_SCHEMA)
    example = _load(_SOURCE_POLICY_APPROVAL_EXAMPLE)
    source_ids = {source["id"] for source in catalog["sources"]}

    assert schema["$id"] == "com.etzhayyim.akashi.sourcePolicyApprovalTx"
    assert schema["additionalProperties"] is False
    assert "allowed" in schema["properties"]["decision"]["enum"]
    assert schema["properties"]["rollback"]["properties"][
        "defaultRuntimeAfterRollback"
    ]["const"] == "disabled"

    required = set(schema["required"])
    assert set(example) == required
    assert example["sourceId"] in source_ids
    assert example["decision"] == "fixture-only"
    assert example["runtime"] == "fixture-only"
    assert "live-adapter" != example["runtime"]
    assert "public-bulk-export" in example["approvedAccessModes"]

    evidence_required = set(schema["properties"]["evidence"]["required"])
    assert evidence_required <= set(example["evidence"])
    assert example["rollback"]["disableTxRequired"] is True
    assert example["rollback"]["defaultRuntimeAfterRollback"] == "disabled"


def test_method_seed_outputs_existing_lexicons():
    seed = _load(_METHOD_SEED)
    assert seed["status"] == "reserved"
    outputs = {m["output"].split(".")[-1] for m in seed["methods"]}
    assert outputs <= _EXPECTED_LEXICONS
    assert {"sourcePolicySnapshot", "adDisclosureSnapshot", "adDisclosureLink", "malakEvidenceCandidate"} <= outputs


def test_seven_cells_raise_at_import_and_match_manifest():

    for name in sorted(_CELL_NAMES):
        path = _CELLS / name / "cell.py"
        readme = _CELLS / name / "README.md"
        assert path.exists(), f"missing cell.py for {name}"
        assert readme.exists(), f"missing README.md for {name}"
        assert "Output Lexicon:" in readme.read_text(), name

        spec = importlib.util.spec_from_file_location(f"_akashi_test_{name}", path)
        assert spec and spec.loader
        module = importlib.util.module_from_spec(spec)
        with pytest.raises(RuntimeError, match="akashi R0 scaffold"):
            spec.loader.exec_module(module)


def test_regulator_bulk_fixture_parser_is_fixture_only_and_shape_safe():
    source = _ADAPTER.read_text()
    for forbidden in ("requests", "httpx", "aiohttp", "urlopen"):
        assert forbidden not in source

    spec = importlib.util.spec_from_file_location("_akashi_regulator_parser", _ADAPTER)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    payload = _load(_FIXTURE)
    output = module.parse_regulator_bulk_fixture(
        payload,
        attesting_did="did:web:akashi.etzhayyim.com",
        source_policy_cid="cid:akashi:source-policy:test",
        method_note_cid="cid:akashi:method-note:test",
    )

    assert set(output) == {
        "methodNote",
        "sourcePolicySnapshot",
        "adDisclosureSnapshot",
        "advertiserIdentity",
        "landingEvidence",
        "creativeDisclosure",
        "deliveryDisclosure",
    }
    assert output["sourcePolicySnapshot"]["collectionStatus"] == "manual-review"
    assert output["sourcePolicySnapshot"]["accessMode"] == "public-bulk-export"
    assert output["adDisclosureSnapshot"][0]["sourceLimited"] is True
    assert output["advertiserIdentity"][0]["nonInferred"] is True
    assert output["landingEvidence"][0]["fetchMode"] == "manual-review-only"
    assert output["deliveryDisclosure"][0]["sourceLimited"] is True


def test_adapter_sources_do_not_import_network_clients():
    for path in (_ADAPTER, _VALIDATOR, _DRY_RUN):
        source = path.read_text()
        for forbidden in ("requests", "httpx", "aiohttp", "urlopen", "urllib.request"):
            assert forbidden not in source, f"{path.name}: forbidden network import"


def test_fixture_parser_output_validates_against_akashi_lexicons():
    parser_spec = importlib.util.spec_from_file_location(
        "_akashi_regulator_parser",
        _ADAPTER,
    )
    validator_spec = importlib.util.spec_from_file_location(
        "_akashi_lexicon_validator",
        _VALIDATOR,
    )
    assert parser_spec and parser_spec.loader
    assert validator_spec and validator_spec.loader

    parser = importlib.util.module_from_spec(parser_spec)
    validator = importlib.util.module_from_spec(validator_spec)
    parser_spec.loader.exec_module(parser)
    validator_spec.loader.exec_module(validator)

    output = parser.parse_regulator_bulk_fixture(
        _load(_FIXTURE),
        attesting_did="did:web:akashi.etzhayyim.com",
        source_policy_cid="cid:akashi:source-policy:test",
        method_note_cid="cid:akashi:method-note:test",
    )

    singleton_outputs = ("methodNote", "sourcePolicySnapshot")
    for name in singleton_outputs:
        validator.validate_record(output[name], _load(_LEX / f"{name}.json"))

    list_outputs = (
        "adDisclosureSnapshot",
        "advertiserIdentity",
        "landingEvidence",
        "creativeDisclosure",
        "deliveryDisclosure",
    )
    for name in list_outputs:
        validator.validate_records(output[name], _load(_LEX / f"{name}.json"))


def test_missing_optional_fixture_preserves_source_limited_gaps():
    parser_spec = importlib.util.spec_from_file_location(
        "_akashi_regulator_parser",
        _ADAPTER,
    )
    validator_spec = importlib.util.spec_from_file_location(
        "_akashi_lexicon_validator",
        _VALIDATOR,
    )
    assert parser_spec and parser_spec.loader
    assert validator_spec and validator_spec.loader

    parser = importlib.util.module_from_spec(parser_spec)
    validator = importlib.util.module_from_spec(validator_spec)
    parser_spec.loader.exec_module(parser)
    validator_spec.loader.exec_module(validator)

    output = parser.parse_regulator_bulk_fixture(
        _load(_MISSING_OPTIONAL_FIXTURE),
        attesting_did="did:web:akashi.etzhayyim.com",
        source_policy_cid="cid:akashi:source-policy:test",
        method_note_cid="cid:akashi:method-note:test",
    )

    advertiser = output["advertiserIdentity"][0]
    creative = output["creativeDisclosure"][0]
    delivery = output["deliveryDisclosure"][0]

    assert advertiser["verifiedStatus"] == "not-disclosed"
    assert "websiteDomain" not in advertiser
    assert creative["sourceIssuePoliticalFlag"] == "not-applicable"
    assert delivery["status"] == "unknown"
    assert "spendRange" not in delivery
    assert "impressionRange" not in delivery

    for name, records in output.items():
        lex = _load(_LEX / f"{name}.json")
        if isinstance(records, list):
            validator.validate_records(records, lex)
        else:
            validator.validate_record(records, lex)


def test_closure_fixture_validates_and_malak_candidate_stays_candidate_only():
    validator_spec = importlib.util.spec_from_file_location(
        "_akashi_lexicon_validator",
        _VALIDATOR,
    )
    assert validator_spec and validator_spec.loader
    validator = importlib.util.module_from_spec(validator_spec)
    validator_spec.loader.exec_module(validator)

    closure = _load(_CLOSURE_FIXTURE)["records"]
    for name in ("adDisclosureLink", "adTransparencyReport", "malakEvidenceCandidate"):
        validator.validate_records(closure[name], _load(_LEX / f"{name}.json"))

    candidate = closure["malakEvidenceCandidate"][0]
    assert candidate["reviewStatus"] == "candidate-only"
    assert candidate["nonAdjudicatingNotice"] is True
    assert "malakImportCid" not in candidate


def test_negative_fixtures_are_rejected():
    parser_spec = importlib.util.spec_from_file_location(
        "_akashi_regulator_parser",
        _ADAPTER,
    )
    assert parser_spec and parser_spec.loader
    parser = importlib.util.module_from_spec(parser_spec)
    parser_spec.loader.exec_module(parser)

    with pytest.raises(KeyError, match="landingUrl"):
        parser.parse_regulator_bulk_fixture(
            _load(_NEGATIVE_MISSING_LANDING_URL),
            attesting_did="did:web:akashi.etzhayyim.com",
            source_policy_cid="cid:akashi:source-policy:test",
            method_note_cid="cid:akashi:method-note:test",
        )

    candidate = _load(_NEGATIVE_MALAK_IMPORTED)["records"]["malakEvidenceCandidate"][0]
    assert candidate["reviewStatus"] == "malak-imported"
    assert "malakImportCid" in candidate
    assert candidate["reviewStatus"] != "candidate-only"


def test_dry_run_cli_emits_validated_local_fixture_summary_only():
    result = subprocess.run(
        [sys.executable, str(_DRY_RUN)],
        check=True,
        capture_output=True,
        text=True,
    )
    summary = json.loads(result.stdout)

    assert summary["actor"] == "akashi"
    assert summary["mode"] == "fixture-dry-run"
    assert summary["networkAccess"] is False
    assert summary["writes"] is False
    assert summary["recordCounts"]["methodNote"] == 1
    assert summary["recordCounts"]["sourcePolicySnapshot"] == 1
    assert summary["recordCounts"]["adDisclosureSnapshot"] == 2
    assert summary["recordCounts"]["malakEvidenceCandidate"] == 1
    assert summary["totalRecords"] == sum(summary["recordCounts"].values())
    assert summary == _load(_DRY_RUN_GOLDEN)


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))

