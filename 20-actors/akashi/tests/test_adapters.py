#!/usr/bin/env python3
"""akashi — adapter tests (lexicon validator + regulator fixture parser +
dry-run pipeline). Pure stdlib; the actor had real parsing/validation code
with zero tests (coverage/maturity loop iteration 2).

Run: PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/ -q
"""
import copy
import pathlib
import sys

import pytest

ACTOR_DIR = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ACTOR_DIR / "adapters"))

from lexicon_shape_validator import validate_record, validate_records  # noqa: E402
from edn_export import (  # noqa: E402
    records_to_datomic_bundle,
    records_to_edn,
    records_to_tx_data,
)
from platform_ad_library_fixture_parser import (  # noqa: E402
    PARSER_VERSION as PLATFORM_PARSER_VERSION,
    parse_platform_ad_library_fixture,
)
from persist_fixture_edn import materialize  # noqa: E402
from regulator_bulk_fixture_parser import (  # noqa: E402
    PARSER_VERSION,
    parse_regulator_bulk_fixture,
)

# ── lexicon_shape_validator ──────────────────────────────────────────────────

LEX = {
    "id": "com.etzhayyim.akashi.test",
    "defs": {
        "main": {
            "record": {
                "required": ["name", "kind"],
                "properties": {
                    "name": {"type": "string", "minLength": 2, "maxLength": 8},
                    "kind": {"type": "string", "knownValues": ["a", "b"]},
                    "count": {"type": "integer", "minimum": 0, "maximum": 10},
                    "flag": {"type": "boolean"},
                    "tags": {
                        "type": "array",
                        "minLength": 1,
                        "items": {"type": "string"},
                    },
                    "ref": {"type": "ref", "ref": "#sub"},
                },
            }
        },
        "sub": {
            "required": ["x"],
            "properties": {"x": {"type": "integer"}},
        },
    },
}

GOOD = {"name": "ok", "kind": "a", "count": 3, "flag": True,
        "tags": ["t"], "ref": {"x": 1}}


def test_validator_accepts_a_fully_populated_record():
    validate_record(GOOD, LEX)  # must not raise
    validate_records([GOOD, GOOD], LEX)


@pytest.mark.parametrize("mutate, match", [
    (lambda r: r.pop("name"), "missing required field name"),
    (lambda r: r.__setitem__("bogus", 1), "unknown field bogus"),
    (lambda r: r.__setitem__("kind", "z"), "unknown value 'z'"),
    (lambda r: r.__setitem__("name", "x"), "shorter than minLength"),
    (lambda r: r.__setitem__("name", "toolongname"), "longer than maxLength"),
    (lambda r: r.__setitem__("count", -1), "below minimum"),
    (lambda r: r.__setitem__("count", 11), "above maximum"),
    (lambda r: r.__setitem__("count", True), "expected integer"),
    (lambda r: r.__setitem__("flag", "yes"), "expected boolean"),
    (lambda r: r.__setitem__("tags", []), "shorter than minLength"),
    (lambda r: r.__setitem__("tags", [1]), "expected string"),
    (lambda r: r.__setitem__("ref", {"x": 1, "y": 2}), "unknown object field y"),
    (lambda r: r.__setitem__("ref", {}), "missing required object field x"),
    (lambda r: r.__setitem__("ref", "not-an-object"), "expected object"),
])
def test_validator_rejects_each_violation(mutate, match):
    record = copy.deepcopy(GOOD)
    mutate(record)
    with pytest.raises(ValueError, match=match):
        validate_record(record, LEX)


def test_validator_const_and_unsupported_type():
    lex = {"id": "t", "defs": {"main": {"record": {
        "required": [], "properties": {"v": {"type": "string", "const": "fixed"}}}}}}
    validate_record({"v": "fixed"}, lex)
    with pytest.raises(ValueError, match="expected const"):
        validate_record({"v": "other"}, lex)
    bad = {"id": "t", "defs": {"main": {"record": {
        "required": [], "properties": {"v": {"type": "cid-link"}}}}}}
    with pytest.raises(ValueError, match="unsupported schema type"):
        validate_record({"v": 1}, bad)


# ── regulator_bulk_fixture_parser ────────────────────────────────────────────

PAYLOAD = {
    "source": {
        "platform": "test-regulator",
        "sourceUrl": "https://regulator.example/bulk",
        "jurisdiction": "JP",
    },
    "capturedAt": "2026-06-11T00:00:00Z",
    "records": [
        {
            "sourceRecordId": "rec-1",
            "sourceUrl": "https://regulator.example/rec-1",
            "advertiser": {
                "displayName": "Example Corp",
                "platformAdvertiserId": "adv-9",
                "websiteDomain": "example.com",
                "verifiedStatus": "verified",
            },
            "landingUrl": "https://Landing.Example.com/page?q=1",
            "creativeText": "creative body",
            "language": "ja",
            "status": "active",
            "spendRange": {"lower": 100, "upper": 200, "currency": "JPY"},
        },
        {
            "sourceRecordId": "rec-2",
            "sourceUrl": "https://regulator.example/rec-2",
            "advertiser": {"displayName": "Minimal Inc"},
            "landingUrl": "https://min.example/",
            "creativeText": "minimal",
        },
    ],
}

KW = dict(
    attesting_did="did:web:akashi.etzhayyim.com",
    source_policy_cid="cid:akashi:source-policy:test",
    method_note_cid="cid:akashi:method-note:test",
)


def test_parser_maps_every_record_family():
    out = parse_regulator_bulk_fixture(copy.deepcopy(PAYLOAD), **KW)
    assert out["methodNote"]["version"] == PARSER_VERSION
    for family in ("adDisclosureSnapshot", "advertiserIdentity",
                   "landingEvidence", "creativeDisclosure", "deliveryDisclosure"):
        assert len(out[family]) == 2, family
    # provenance honesty markers survive the mapping
    assert all(s["sourceLimited"] for s in out["adDisclosureSnapshot"])
    assert all(a["nonInferred"] for a in out["advertiserIdentity"])


def test_parser_is_deterministic_and_content_addressed():
    a = parse_regulator_bulk_fixture(copy.deepcopy(PAYLOAD), **KW)
    b = parse_regulator_bulk_fixture(copy.deepcopy(PAYLOAD), **KW)
    assert a == b
    s = a["adDisclosureSnapshot"][0]
    assert s["payloadCid"].startswith("cid:akashi:payload:")
    assert len(s["payloadSha256"]) == 64
    # changing the source record must change its content address
    mutated = copy.deepcopy(PAYLOAD)
    mutated["records"][0]["creativeText"] = "different"
    c = parse_regulator_bulk_fixture(mutated, **KW)
    assert c["adDisclosureSnapshot"][0]["payloadCid"] != s["payloadCid"]


def test_parser_source_limited_gaps_are_preserved_not_invented():
    out = parse_regulator_bulk_fixture(copy.deepcopy(PAYLOAD), **KW)
    minimal = out["advertiserIdentity"][1]
    # undisclosed fields are ABSENT (None-stripped), never fabricated
    assert "platformAdvertiserId" not in minimal
    assert "websiteDomain" not in minimal
    assert minimal["verifiedStatus"] == "not-disclosed"
    delivery_min = out["deliveryDisclosure"][1]
    assert delivery_min["status"] == "unknown"
    assert "spendRange" not in delivery_min


def test_parser_normalizes_domain_and_range_aliases():
    out = parse_regulator_bulk_fixture(copy.deepcopy(PAYLOAD), **KW)
    assert out["landingEvidence"][0]["domain"] == "landing.example.com"
    spend = out["deliveryDisclosure"][0]["spendRange"]
    # lower/upper aliases map onto min/max
    assert spend["min"] == 100 and spend["max"] == 200
    assert spend["currency"] == "JPY"


# ── platform_ad_library_fixture_parser ───────────────────────────────────────

PLATFORM_PAYLOAD = {
    "source": {
        "platform": "meta",
        "sourceFamily": "social-ad-library",
        "sourceUrl": "https://www.facebook.com/ads/library/",
        "jurisdiction": "US",
        "accessMode": "manual-review-only",
    },
    "capturedAt": "2026-07-10T00:00:00Z",
    "records": [
        {
            "sourceRecordId": "meta-1",
            "sourceUrl": "https://www.facebook.com/ads/library/?id=meta-1",
            "advertiser": {
                "displayName": "Meta Fixture Advertiser",
                "platformAdvertiserId": "page-1",
                "pageUrl": "https://www.facebook.com/page-1",
                "websiteDomain": "example.org",
                "verifiedStatus": "source-verified",
            },
            "creativeText": "public source creative",
            "media": {
                "cid": "cid:akashi:media:meta-1",
                "sha256": "a" * 64,
            },
            "language": "en",
            "disclosedCategory": "public-interest",
            "sourceIssuePoliticalFlag": "source-not-disclosed",
            "landingUrl": "https://Example.Org/landing",
            "startedAt": "2026-07-01T00:00:00Z",
            "status": "inactive",
            "spendRange": {"lower": 10, "upper": 20, "currency": "USD"},
            "targetingSummary": {"sourceLimited": True, "regions": ["US"]},
        }
    ],
}


def test_platform_parser_maps_meta_x_style_ad_library_records():
    out = parse_platform_ad_library_fixture(copy.deepcopy(PLATFORM_PAYLOAD), **KW)
    assert out["methodNote"]["version"] == PLATFORM_PARSER_VERSION
    assert out["sourcePolicySnapshot"]["sourceFamily"] == "social-ad-library"
    assert out["sourcePolicySnapshot"]["accessMode"] == "manual-review-only"
    assert len(out["adDisclosureSnapshot"]) == 1
    assert out["advertiserIdentity"][0]["pageUrl"] == "https://www.facebook.com/page-1"
    assert out["advertiserIdentity"][0]["nonInferred"] is True
    assert out["landingEvidence"][0]["domain"] == "example.org"
    assert out["creativeDisclosure"][0]["mediaCid"] == "cid:akashi:media:meta-1"
    assert "targetingSummaryCid" in out["deliveryDisclosure"][0]
    assert out["deliveryDisclosure"][0]["spendRange"]["currency"] == "USD"


# ── dry-run pipeline (fixtures → parse → lexicon-validate, end-to-end) ──────

def test_dry_run_fixtures_validate_against_real_lexicons():
    sys.path.insert(0, str(ACTOR_DIR / "adapters"))
    from dry_run_fixtures import load_dry_run_records  # noqa: E402
    output = load_dry_run_records()
    assert output, "dry-run pipeline returned no record families"
    total = sum(len(v) if isinstance(v, list) else 1 for v in output.values())
    assert total >= 25, f"expected a non-trivial fixture set, got {total} records"
    platforms = {r["platform"] for r in output["adDisclosureSnapshot"]}
    assert {"meta", "x"}.issubset(platforms)


def test_edn_export_emits_datomic_datascript_tx_data():
    from dry_run_fixtures import load_dry_run_records  # noqa: E402

    records = load_dry_run_records()
    tx = records_to_tx_data(records)
    assert len(tx) == sum(len(v) if isinstance(v, list) else 1 for v in records.values())
    first = tx[0]
    assert "db/id" in first
    assert "akashi.record/family" in first
    assert "akashi.record/cid" in first
    edn = records_to_edn({"adDisclosureSnapshot": records["adDisclosureSnapshot"][:1]})
    assert edn.startswith("[{")
    assert ":akashi.record/family" in edn
    assert ":akashi.adDisclosureSnapshot/platform" in edn


def test_datomic_bundle_emits_schema_and_scalar_tx_ops():
    from dry_run_fixtures import load_dry_run_records  # noqa: E402

    bundle = records_to_datomic_bundle(load_dry_run_records())
    schema = bundle["akashi.datomic/schema"]
    tx = bundle["akashi.datomic/tx-data"]
    assert schema
    assert tx
    assert all(op[0] == "db/add" for op in tx)
    assert all(not isinstance(op[3], (dict, list)) for op in tx)
    idents = {s["db/ident"]: s for s in schema}
    assert idents["akashi.record/cid"]["db/unique"] == "db.unique/identity"
    assert idents["akashi.deliveryDisclosure/region-summary"][
        "db/cardinality"
    ] == "db.cardinality/many"
    assert "akashi.deliveryDisclosure/spend-range-min" in idents
    assert "akashi.deliveryDisclosure/impression-range-max" in idents


def test_persist_fixture_edn_materializes_storage_manifest(tmp_path):
    out = tmp_path / "akashi.fixture.tx.kotoba.edn"
    datomic = tmp_path / "akashi.fixture.datomic.edn"
    manifest = tmp_path / "manifest.edn"
    payload = materialize(out, manifest, datomic)
    assert out.exists()
    assert datomic.exists()
    assert manifest.exists()
    assert payload["akashi.storage/records"] == 25
    assert payload["akashi.storage/format"] == "datomic-datascript-tx-edn"
    assert payload["akashi.storage/artifact"].endswith(".tx.kotoba.edn")
    assert payload["akashi.storage/cidv1"].startswith("bafkrei")
    assert payload["akashi.storage/kotoba-rad"][
        "akashi.storage/identity-journal"
    ] == "80-data/kotoba-rad/akashi.identity.journal.edn"
    assert payload["akashi.storage/kotoba-rad"]["cidv1"] == payload["akashi.storage/cidv1"]
    assert payload["akashi.storage/datomic"]["path"].endswith(".datomic.edn")
    assert payload["akashi.storage/datomic"]["cidv1"].startswith("bafkrei")
