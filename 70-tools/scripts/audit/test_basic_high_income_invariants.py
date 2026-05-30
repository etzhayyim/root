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
_LEX = _REPO / "00-contracts" / "lexicons" / "app" / "etzhayyim"
_METRIC = _LEX / "liberation" / "metricReport.json"
_VENDOR = _LEX / "give" / "vendorMissionDonationAttestation.json"
_VENDOR_POLICY = _LEX / "give" / "vendorSurplusPolicy.json"
_VALUATION = _REPO / "20-actors" / "toritate" / "valuation" / "v1-retail-equiv.json"
_CELLS = _REPO / "20-actors" / "magatama" / "cells"


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
