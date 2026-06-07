"""Lock-in tests for the Basic High Income + Mission-Funding constitutional invariants.

Pins the structural properties designed in ADR-2605301020 (Basic High Income —
imputed-income FLOW + commons-asset STOCK doctrine) and ADR-2605301036
(Mission-Funding Earned-Revenue Arm) so a future refactor cannot silently weaken
a constitutional invariant.

The invariants under test are NOT amendable without Council process; this suite
fails fast if any artifact drifts:

  1. metricReport.basicHighIncome.cashStipendUsdMicros is pinned `const: 0`
     (on-chain proof of ADR-2605261000 §5 N1 — no fiat-replacement UBI), and the
     block is REQUIRED on every report.
  2. give.vendorMissionDonationAttestation accepts ONLY {donation, grant} purposes
     (no external-commercial purpose ever touches the religious-corp substrate —
     ADR-2605192115 §4).
  3. toritate valuation v1-retail-equiv: every `stock` (commons-asset) entry is
     `alienable: false` (access-not-title; ADR-2605301020 §2 generalizing the
     ADR-2605192245 land waqf), and the table-level cashStipend invariant is 0.
  4. The 3 R0 Pregel cell stubs raise at import time until R1 (no accidental
     activation of cash/income machinery before Council ratification).
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parents[3]
_LEX = _REPO / "00-contracts" / "lexicons" / "com" / "etzhayyim"
_METRIC = _LEX / "liberation" / "metricReport.json"
_VENDOR = _LEX / "give" / "vendorMissionDonationAttestation.json"
_VENDOR_POLICY = _LEX / "give" / "vendorSurplusPolicy.json"
_VALUATION = _REPO / "20-actors" / "toritate" / "valuation" / "v1-retail-equiv.json"
_CELLS = _REPO / "20-actors" / "kotodama" / "cells"
_TORITATE_MANIFEST = _REPO / "20-actors" / "toritate" / "manifest.jsonld"


def _load(p: Path) -> dict:
    return json.loads(p.read_text())


def _walk(node):
    """Yield every dict node in a nested JSON structure."""
    if isinstance(node, dict):
        yield node
        for v in node.values():
            yield from _walk(v)
    elif isinstance(node, list):
        for v in node:
            yield from _walk(v)


# ─── 1. metricReport basicHighIncome ────────────────────────────────────


class TestMetricReportBasicHighIncome:
    def test_block_is_required(self):
        rec = _load(_METRIC)["defs"]["main"]["record"]
        assert "basicHighIncome" in rec["required"], (
            "basicHighIncome must be required so every report carries the N1 proof"
        )

    def test_cash_stipend_pinned_zero(self):
        rec = _load(_METRIC)["defs"]["main"]["record"]
        cash = rec["properties"]["basicHighIncome"]["properties"]["cashStipendUsdMicros"]
        assert cash.get("type") == "integer"
        assert cash.get("const") == 0, "cashStipendUsdMicros must be const 0 (ADR-2605261000 §5 N1)"

    def test_no_float_types(self):
        # ADR-2605190900: integer-with-implied-units only; the lefthook enforces
        # this, but pin it here too so a record-shape edit can't reintroduce floats.
        bad = [n for n in _walk(_load(_METRIC)) if n.get("type") == "number"]
        assert not bad, f"no `type: number` allowed in lexicons; found {len(bad)}"


# ─── 2. vendorMissionDonationAttestation purpose enum ───────────────────


class TestVendorDonationPurpose:
    def test_purpose_enum_is_donation_or_grant_only(self):
        rec = _load(_VENDOR)["defs"]["main"]["record"]
        purpose = rec["properties"]["purpose"]
        assert set(purpose["enum"]) == {"donation", "grant"}, (
            "vendor donation must be titheable donation/grant only — no commercial "
            "purpose may reach the religious-corp substrate (ADR-2605192115 §4)"
        )

    def test_no_customer_pii_amount_is_micros(self):
        rec = _load(_VENDOR)["defs"]["main"]["record"]
        assert rec["properties"]["donatedAmountMicros"]["type"] == "integer"
        # vendorDid + period + donatedAmountMicros + purpose + txHash are required;
        # nothing customer-identifying is required.
        assert "donatedAmountMicros" in rec["required"]


# ─── 2b. vendorSurplusPolicy — Council-attested mission-commitment ──────


class TestVendorSurplusPolicy:
    def test_council_attestation_min_three(self):
        rec = _load(_VENDOR_POLICY)["defs"]["main"]["record"]
        att = rec["properties"]["councilAttestation"]
        assert att.get("minItems", 0) >= 3, "policy needs Council Lv6+ ≥3 (ADR-2605301036 §6)"
        assert "councilAttestation" in rec["required"]

    def test_payout_ratio_is_bounded_integer(self):
        rec = _load(_VENDOR_POLICY)["defs"]["main"]["record"]
        ratio = rec["properties"]["payoutRatioBps"]
        assert ratio["type"] == "integer"
        assert ratio.get("maximum") == 10000, "payout ratio is basis points, capped at 100%"

    def test_no_float_types(self):
        bad = [n for n in _walk(_load(_VENDOR_POLICY)) if n.get("type") == "number"]
        assert not bad, f"no `type: number` allowed; found {len(bad)}"


# ─── 3. toritate valuation — commons-asset non-alienability ─────────────


class TestValuationInvariants:
    def test_every_stock_entry_is_non_alienable(self):
        table = _load(_VALUATION)
        stock = table["stock"]
        entries = {k: v for k, v in stock.items() if not k.startswith("_") and isinstance(v, dict)}
        assert entries, "expected at least one commons-asset stock entry"
        for key, entry in entries.items():
            assert entry.get("alienable") is False, (
                f"stock entry {key!r} must be alienable:false (access-not-title, "
                "ADR-2605301020 §2)"
            )

    def test_table_cash_invariant_zero(self):
        table = _load(_VALUATION)
        assert table["invariants"]["cashStipendUsd"] == 0

    def test_every_entry_has_citable_source(self):
        # ADR-2605301020 §4 + valuation/README: every category must carry a
        # sourceRef to an open, citable price source before attestation — no
        # bare "TBD" placeholders may survive into a populated table.
        table = _load(_VALUATION)
        missing = []
        for section in ("flow", "stock"):
            for key, entry in table[section].items():
                if key.startswith("_") or not isinstance(entry, dict):
                    continue
                src = entry.get("sourceRef", "")
                if not src or "TBD" in src:
                    missing.append(f"{section}.{key}")
        bsrc = table.get("benchmark", {}).get("sourceRef", "")
        if not bsrc or "TBD" in bsrc:
            missing.append("benchmark")
        assert not missing, f"entries missing a citable sourceRef: {missing}"


# ─── 4. R0 cell stubs raise at import ───────────────────────────────────


@pytest.mark.parametrize("cell", [
    "toritate_imputed_income_compute",
    "toritate_commons_asset_value",
    "basic_high_income_aggregate",
])
def test_cell_stub_raises_r0(cell):
    spec = importlib.util.spec_from_file_location(f"_{cell}", _CELLS / cell / "cell.py")
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    with pytest.raises(RuntimeError) as exc:
        spec.loader.exec_module(mod)
    assert "R0 scaffold" in str(exc.value)


# ─── 5. example records conform to their lexicon schemas ────────────────
#
# Nothing else in the repo validates instance records against lexicon schemas
# (validate-lexicons.py checks the schema files themselves). This minimal
# validator catches drift between an example fixture and its lexicon: required
# fields, additionalProperties:false, primitive types, const, enum, minItems,
# and string length bounds — enough to fail fast if a field is renamed or a
# const/enum is weakened.

_EXAMPLES = _REPO / "00-contracts" / "examples" / "com" / "etzhayyim"


def _validate_record(schema_obj: dict, value, path: str = "$") -> list[str]:
    errs: list[str] = []
    t = schema_obj.get("const")
    if "const" in schema_obj and value != t:
        errs.append(f"{path}: const {t!r} != {value!r}")
    if "enum" in schema_obj and value not in schema_obj["enum"]:
        errs.append(f"{path}: {value!r} not in enum {schema_obj['enum']}")

    typ = schema_obj.get("type")
    if typ == "object":
        if not isinstance(value, dict):
            return errs + [f"{path}: expected object"]
        props = schema_obj.get("properties", {})
        for req in schema_obj.get("required", []):
            if req not in value:
                errs.append(f"{path}: missing required {req!r}")
        if schema_obj.get("additionalProperties") is False:
            extra = set(value) - set(props)
            if extra:
                errs.append(f"{path}: unexpected keys {sorted(extra)} (additionalProperties:false)")
        for k, v in value.items():
            if k in props:
                errs += _validate_record(props[k], v, f"{path}.{k}")
    elif typ == "integer":
        if isinstance(value, bool) or not isinstance(value, int):
            errs.append(f"{path}: expected integer, got {type(value).__name__}")
        else:
            if "minimum" in schema_obj and value < schema_obj["minimum"]:
                errs.append(f"{path}: {value} < minimum {schema_obj['minimum']}")
            if "maximum" in schema_obj and value > schema_obj["maximum"]:
                errs.append(f"{path}: {value} > maximum {schema_obj['maximum']}")
    elif typ == "string":
        if not isinstance(value, str):
            errs.append(f"{path}: expected string")
        else:
            if "minLength" in schema_obj and len(value) < schema_obj["minLength"]:
                errs.append(f"{path}: len {len(value)} < minLength {schema_obj['minLength']}")
            if "maxLength" in schema_obj and len(value) > schema_obj["maxLength"]:
                errs.append(f"{path}: len {len(value)} > maxLength {schema_obj['maxLength']}")
    elif typ == "array":
        if not isinstance(value, list):
            errs.append(f"{path}: expected array")
        else:
            if "minItems" in schema_obj and len(value) < schema_obj["minItems"]:
                errs.append(f"{path}: {len(value)} items < minItems {schema_obj['minItems']}")
            item_schema = schema_obj.get("items")
            if isinstance(item_schema, dict):
                for i, item in enumerate(value):
                    errs += _validate_record(item_schema, item, f"{path}[{i}]")
    return errs


@pytest.mark.parametrize("example_rel, lexicon_path", [
    ("liberation/metricReport.example.v1.json", _METRIC),
    ("give/vendorMissionDonationAttestation.example.v1.json", _VENDOR),
    ("give/vendorSurplusPolicy.example.v1.json", _VENDOR_POLICY),
])
def test_example_conforms_to_lexicon(example_rel, lexicon_path):
    record_schema = _load(lexicon_path)["defs"]["main"]["record"]
    instance = _load(_EXAMPLES / example_rel)
    errs = _validate_record(record_schema, instance)
    assert not errs, "example does not conform to lexicon:\n  " + "\n  ".join(errs)


def test_metric_example_cash_stipend_is_zero():
    inst = _load(_EXAMPLES / "liberation/metricReport.example.v1.json")
    assert inst["basicHighIncome"]["cashStipendUsdMicros"] == 0


def test_vendor_donation_example_purpose_is_titheable():
    inst = _load(_EXAMPLES / "give/vendorMissionDonationAttestation.example.v1.json")
    assert inst["purpose"] in {"donation", "grant"}


# ─── 6. cross-artifact arithmetic consistency ───────────────────────────
#
# Pin the planning figures so a future edit can't leave the valuation table
# internally inconsistent or let the example fixture drift from it.

_RATIO_TOL = 0.011  # stageBaskets ratios are rounded to 2 decimals


def test_stage_basket_ratios_match_benchmark():
    table = _load(_VALUATION)
    bench = table["benchmark"]["perAdherentUsdYr"]
    assert bench > 0
    drift = []
    for stage, row in table["stageBaskets"].items():
        if stage.startswith("_") or not isinstance(row, dict):
            continue
        computed = (row["flowUsdYr"] + row["stockUsdYr"]) / bench
        if abs(computed - row["benchmarkRatio"]) > _RATIO_TOL:
            drift.append(f"{stage}: stated {row['benchmarkRatio']} vs computed {computed:.4f}")
    assert not drift, "stageBaskets benchmarkRatio drift:\n  " + "\n  ".join(drift)


def test_l6_target_approaches_high_income_benchmark():
    # ADR-2605301020 §3: L6 target standard of living ≥ OECD upper-decile basket
    # (ratio →1.0). Pin that the planning table actually reaches near-parity.
    row = _load(_VALUATION)["stageBaskets"]["L6"]
    assert row["benchmarkRatio"] >= 0.95, "L6 should approach the high-income benchmark"


def test_metric_example_matches_valuation_l3_row():
    table = _load(_VALUATION)
    l3 = table["stageBaskets"]["L3"]
    ex = _load(_EXAMPLES / "liberation/metricReport.example.v1.json")["basicHighIncome"]
    assert ex["imputedIncomeMedianUsdMicrosYr"] == l3["flowUsdYr"] * 1_000_000
    assert ex["commonsAssetAccessMedianUsdMicros"] == l3["stockUsdYr"] * 1_000_000
    assert ex["highIncomeBenchmarkRatioPermille"] == round(l3["benchmarkRatio"] * 1000)


# ─── 7. give namespace README index completeness ────────────────────────


def test_give_readme_indexes_every_lexicon():
    give = _LEX / "give"
    readme = (give / "README.md").read_text()
    missing = []
    for lex in sorted(give.rglob("*.json")):
        nsid = _load(lex)["id"]
        short = nsid.removeprefix("com.etzhayyim.give.")  # e.g. usdc.donation / vendorSurplusPolicy
        if short not in readme:
            missing.append(short)
    assert not missing, f"give/README.md must index every lexicon; missing: {missing}"


# ─── 8. toritate manifest declares the Basic High Income compute cells ──
#
# Lock the manifest ↔ disk consistency for the two BHI compute cells (only —
# the original 6 toritate cells are path-reserved and intentionally have no dir
# yet, so we do NOT assert those).


def _manifest_cell_modules() -> set[str]:
    return {c["module"] for c in _load(_TORITATE_MANIFEST)["cells"]}


def test_manifest_declares_bhi_compute_cells():
    modules = _manifest_cell_modules()
    for mod in (
        "kotodama.cells.toritate_imputed_income_compute",
        "kotodama.cells.toritate_commons_asset_value",
    ):
        assert mod in modules, f"toritate manifest must declare {mod}"


def test_manifest_bhi_cells_exist_on_disk():
    for cell in ("toritate_imputed_income_compute", "toritate_commons_asset_value"):
        assert (_CELLS / cell / "cell.py").exists(), f"{cell}/cell.py missing on disk"
