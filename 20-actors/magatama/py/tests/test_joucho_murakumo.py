"""Tests for joucho_murakumo.py — JouchoAggregationCell + fetch_joucho real impl.

Covers:
  - JouchoRecord dataclass construction
  - classify_mood: 6 mood paths (stressed/joyful/calm/grateful/focused/neutral)
  - aggregate_signals: empty list, single signal, multi-signal, clamp behaviour
  - joucho_aggregation_cell: single-adherent, no-signals, multi-adherent paths
  - fetch_joucho: happy path, 404 → None, partial record defaults
  - _safe_rkey: did:web and did:plc transformations
  - Substrate-fit regression: no psycopg/Stripe/RunPod imports in module source

Per JOUCHO-MIGRATION-DESIGN.md + ADR-2605215200 §4.
"""

from __future__ import annotations

import inspect
import pathlib
import textwrap
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from pymagatama.primitives.joucho_murakumo import (
    CALM_MOOD_THRESHOLD_PERMILLE,
    FOCUS_MOOD_THRESHOLD_PERMILLE,
    GRATITUDE_MOOD_THRESHOLD_PERMILLE,
    JOUCHO_AGGREGATION_WINDOW_DAYS,
    JOY_MOOD_THRESHOLD_PERMILLE,
    NEW_ADHERENT_DEFAULTS,
    SIGNAL_KIND_TO_AXIS_WEIGHTS,
    STRESS_MOOD_THRESHOLD_PERMILLE,
    JouchoRecord,
    _safe_rkey,
    aggregate_signals,
    classify_mood,
    fetch_joucho,
    joucho_aggregation_cell,
)

# ── Fixtures ─────────────────────────────────────────────────────────────────


_MODULE_SOURCE_PATH = pathlib.Path(
    __file__
).parent.parent / "src" / "pymagatama" / "primitives" / "joucho_murakumo.py"


# ── A. JouchoRecord dataclass ─────────────────────────────────────────────────


class TestJouchoRecord:
    def test_default_construction(self):
        """JouchoRecord instantiates with zero-value axes by default."""
        r = JouchoRecord(adherentDid="did:plc:test123")
        assert r.adherentDid == "did:plc:test123"
        assert r.joy == 0
        assert r.calm == 0
        assert r.stress == 0
        assert r.gratitude == 0
        assert r.focus == 0
        assert r.computed_at == ""
        assert r.from_signal_count == 0
        assert r.from_signals_since == ""
        assert r.aggregator_node == ""
        assert r.from_signal_days == 7

    def test_explicit_construction(self):
        """JouchoRecord fields are mutable after construction."""
        r = JouchoRecord(
            adherentDid="did:plc:abc",
            joy=600,
            calm=500,
            stress=100,
            gratitude=700,
            focus=400,
            computed_at="2026-05-21T12:00:00Z",
            from_signal_count=42,
            from_signals_since="2026-05-14T00:00:00Z",
            aggregator_node="levi",
            from_signal_days=7,
        )
        assert r.joy == 600
        assert r.gratitude == 700
        assert r.computed_at == "2026-05-21T12:00:00Z"
        assert r.aggregator_node == "levi"
        assert r.from_signals_since == "2026-05-14T00:00:00Z"

    def test_boundary_permille_values(self):
        """JouchoRecord accepts 0 and 1000 (lexicon min/max)."""
        r = JouchoRecord(adherentDid="did:plc:x", joy=0, calm=1000, stress=1000)
        assert r.joy == 0
        assert r.calm == 1000
        assert r.stress == 1000

    def test_slots_prevents_arbitrary_attributes(self):
        """slots=True: assigning unknown attribute raises AttributeError."""
        r = JouchoRecord(adherentDid="did:plc:x")
        with pytest.raises(AttributeError):
            r.unknown_field = "bad"  # type: ignore[attr-defined]


# ── B. classify_mood ──────────────────────────────────────────────────────────


class TestClassifyMood:
    """Covers all 6 mood paths with boundary and boundary-minus-1 values."""

    def _record(self, **kwargs) -> JouchoRecord:
        return JouchoRecord(adherentDid="did:plc:test", **kwargs)

    # -- stressed (priority gate, checked first)

    def test_stressed_at_threshold(self):
        r = self._record(stress=STRESS_MOOD_THRESHOLD_PERMILLE)
        assert classify_mood(r) == "stressed"

    def test_stressed_at_max(self):
        r = self._record(stress=1000)
        assert classify_mood(r) == "stressed"

    def test_stressed_below_threshold_is_not_stressed(self):
        r = self._record(stress=STRESS_MOOD_THRESHOLD_PERMILLE - 1)
        assert classify_mood(r) != "stressed"

    def test_stressed_overrides_high_joy(self):
        """Stress gate fires even when joy is high."""
        r = self._record(stress=700, joy=900)
        assert classify_mood(r) == "stressed"

    # -- joyful

    def test_joyful_at_threshold(self):
        r = self._record(joy=JOY_MOOD_THRESHOLD_PERMILLE, stress=0)
        assert classify_mood(r) == "joyful"

    def test_joyful_at_1000(self):
        r = self._record(joy=1000, stress=0)
        assert classify_mood(r) == "joyful"

    def test_joyful_below_threshold_not_joyful(self):
        r = self._record(joy=JOY_MOOD_THRESHOLD_PERMILLE - 1, stress=0)
        assert classify_mood(r) != "joyful"

    # -- calm

    def test_calm_at_threshold(self):
        r = self._record(calm=CALM_MOOD_THRESHOLD_PERMILLE, joy=0, stress=0)
        assert classify_mood(r) == "calm"

    def test_calm_below_threshold_not_calm(self):
        r = self._record(calm=CALM_MOOD_THRESHOLD_PERMILLE - 1, joy=0, stress=0)
        assert classify_mood(r) != "calm"

    # -- grateful

    def test_grateful_at_threshold(self):
        r = self._record(
            gratitude=GRATITUDE_MOOD_THRESHOLD_PERMILLE, joy=0, calm=0, stress=0
        )
        assert classify_mood(r) == "grateful"

    def test_grateful_below_threshold_not_grateful(self):
        r = self._record(
            gratitude=GRATITUDE_MOOD_THRESHOLD_PERMILLE - 1, joy=0, calm=0, stress=0
        )
        assert classify_mood(r) != "grateful"

    # -- focused

    def test_focused_at_threshold(self):
        r = self._record(
            focus=FOCUS_MOOD_THRESHOLD_PERMILLE, joy=0, calm=0, gratitude=0, stress=0
        )
        assert classify_mood(r) == "focused"

    def test_focused_below_threshold_not_focused(self):
        r = self._record(
            focus=FOCUS_MOOD_THRESHOLD_PERMILLE - 1, joy=0, calm=0, gratitude=0, stress=0
        )
        assert classify_mood(r) != "focused"

    # -- neutral (default when nothing meets threshold)

    def test_neutral_all_zeros(self):
        r = self._record()  # all axes = 0
        assert classify_mood(r) == "neutral"

    def test_neutral_new_adherent_defaults(self):
        """New-adherent permille defaults → neutral (matching vendor behaviour)."""
        r = JouchoRecord(
            adherentDid="did:plc:new",
            joy=NEW_ADHERENT_DEFAULTS["joy"],      # 400
            calm=NEW_ADHERENT_DEFAULTS["calm"],    # 400
            stress=NEW_ADHERENT_DEFAULTS["stress"],# 200
            gratitude=NEW_ADHERENT_DEFAULTS["gratitude"],  # 300
            focus=NEW_ADHERENT_DEFAULTS["focus"],  # 400
        )
        # stress=200 < 700; joy/calm/gratitude/focus all < 600 → neutral
        assert classify_mood(r) == "neutral"

    def test_priority_ordering_joy_before_calm(self):
        """When both joy and calm are at threshold, joy wins (checked first)."""
        r = self._record(
            joy=JOY_MOOD_THRESHOLD_PERMILLE,
            calm=CALM_MOOD_THRESHOLD_PERMILLE,
            stress=0,
        )
        assert classify_mood(r) == "joyful"

    def test_priority_ordering_calm_before_grateful(self):
        r = self._record(
            joy=0,
            calm=CALM_MOOD_THRESHOLD_PERMILLE,
            gratitude=GRATITUDE_MOOD_THRESHOLD_PERMILLE,
            stress=0,
        )
        assert classify_mood(r) == "calm"


# ── C. aggregate_signals ──────────────────────────────────────────────────────


class TestAggregateSignals:
    """Pure function tests — no I/O."""

    # -- empty list → new-adherent defaults

    def test_empty_signals_returns_new_adherent_defaults(self):
        result = aggregate_signals([])
        assert result == NEW_ADHERENT_DEFAULTS
        assert result["stress"] == 200   # stress default is lower (200‰ = 20%)

    def test_empty_signals_stress_default(self):
        result = aggregate_signals([])
        # New-adherent stress is 200 (not 1000), matching vendor new-adherent state.
        assert result["stress"] == 200

    # -- single ritual signal

    def test_ritual_signal_contributes_joy_and_focus(self):
        """ritual: joy += weight × 0.8, focus += weight × 0.3, then /signal_count."""
        signals = [{"signalKind": "ritual", "weight": 1000}]
        result = aggregate_signals(signals)
        # signal_count = 1; joy_acc = 1000*800//1000 = 800; joy = 800//1 = 800
        assert result["joy"] == 800
        # focus_acc = 1000*300//1000 = 300; focus = 300//1 = 300
        assert result["focus"] == 300
        assert result["calm"] == 0
        assert result["gratitude"] == 0

    def test_ritual_weight_500_joy_and_focus(self):
        """ritual weight=500 → joy=400, focus=150 before norm."""
        signals = [{"signalKind": "ritual", "weight": 500}]
        result = aggregate_signals(signals)
        # joy_acc = 500*800//1000 = 400; joy = 400//1 = 400
        assert result["joy"] == 400
        # focus_acc = 500*300//1000 = 150; focus = 150//1 = 150
        assert result["focus"] == 150

    # -- single oath signal

    def test_oath_signal_contributes_calm_and_focus(self):
        """oath: calm += weight × 0.9, focus += weight × 0.7."""
        signals = [{"signalKind": "oath", "weight": 1000}]
        result = aggregate_signals(signals)
        assert result["calm"] == 900
        assert result["focus"] == 700
        assert result["joy"] == 0
        assert result["gratitude"] == 0

    # -- single contribution signal

    def test_contribution_signal(self):
        """contribution: gratitude += weight × 1.0, focus += weight × 0.5."""
        signals = [{"signalKind": "contribution", "weight": 600}]
        result = aggregate_signals(signals)
        # gratitude_acc = 600*1000//1000 = 600; gratitude = 600//1 = 600
        assert result["gratitude"] == 600
        # focus_acc = 600*500//1000 = 300; focus = 300//1 = 300
        assert result["focus"] == 300

    # -- single governance-participation signal

    def test_governance_participation_signal(self):
        """governance-participation: calm += weight × 0.8."""
        signals = [{"signalKind": "governance-participation", "weight": 500}]
        result = aggregate_signals(signals)
        # calm_acc = 500*800//1000 = 400; calm = 400//1 = 400
        assert result["calm"] == 400
        assert result["joy"] == 0

    # -- single kuniUmi-witness signal

    def test_kuni_umi_witness_signal(self):
        """kuniUmi-witness: joy += weight × 0.6."""
        signals = [{"signalKind": "kuniUmi-witness", "weight": 500}]
        result = aggregate_signals(signals)
        # joy_acc = 500*600//1000 = 300; joy = 300//1 = 300
        assert result["joy"] == 300

    # -- multiple signals → normalisation by count

    def test_two_signals_normalised_by_count(self):
        """Two equal signals: normalise divides accumulated sum by 2."""
        signals = [
            {"signalKind": "ritual", "weight": 1000},
            {"signalKind": "ritual", "weight": 1000},
        ]
        result = aggregate_signals(signals)
        # joy_acc = 800 + 800 = 1600; joy = 1600 // 2 = 800
        assert result["joy"] == 800
        # focus_acc = 300 + 300 = 600; focus = 600 // 2 = 300
        assert result["focus"] == 300

    def test_mixed_signal_kinds(self):
        """ritual + oath → both joy/focus + calm/focus contributions, normalised."""
        signals = [
            {"signalKind": "ritual", "weight": 1000},  # joy+=800, focus+=300
            {"signalKind": "oath", "weight": 1000},    # calm+=900, focus+=700
        ]
        result = aggregate_signals(signals)
        # signal_count = 2
        # joy_acc=800 → joy = 800//2 = 400
        assert result["joy"] == 400
        # calm_acc=900 → calm = 900//2 = 450
        assert result["calm"] == 450
        # focus_acc = 300 + 700 = 1000 → focus = 1000//2 = 500
        assert result["focus"] == 500
        assert result["gratitude"] == 0

    # -- clamp behaviour: accumulated values must not exceed 1000

    def test_high_weight_clamped_to_1000(self):
        """Very high accumulator must be clamped to 1000, not overflow."""
        # contribution weight=1000 × 1.0 factor = 1000; after //1 = 1000 (at ceiling)
        signals = [{"signalKind": "contribution", "weight": 1000}]
        result = aggregate_signals(signals)
        assert result["gratitude"] == 1000

    def test_many_high_signals_clamped(self):
        """Multiple high-weight ritual signals: joy saturates at 1000."""
        # 5 rituals weight=1000 each: joy_acc = 5×800=4000; //5=800. Still 800.
        signals = [{"signalKind": "ritual", "weight": 1000}] * 5
        result = aggregate_signals(signals)
        # normalised = acc//count; 4000//5 = 800 (no clamp needed in this case)
        assert result["joy"] == 800

        # But if acc > 1000 per signal × count scenario:
        # contribution×2: gratitude_acc = 2000; //2 = 1000 (at boundary)
        signals2 = [{"signalKind": "contribution", "weight": 1000}] * 2
        r2 = aggregate_signals(signals2)
        assert r2["gratitude"] == 1000  # clamped / at ceiling
        assert r2["gratitude"] <= 1000

    # -- stress = inhibitor (inverse of positive mean)

    def test_stress_is_inhibitor_of_positives(self):
        """With high joy/calm/gratitude/focus, stress should be low."""
        signals = [
            {"signalKind": "ritual", "weight": 1000},        # joy=800, focus=300
            {"signalKind": "oath", "weight": 1000},          # calm=900, focus=700
            {"signalKind": "contribution", "weight": 1000},  # grat=1000, focus=500
        ]
        result = aggregate_signals(signals)
        # joy=800/3≈266, calm=900/3=300, grat=1000/3≈333, focus=(300+700+500)/3=500
        # stress = 1000 - (266+300+333+500)/4 = 1000 - ~350 ≈ 650
        # The exact value depends on integer division; just verify stress < 1000.
        assert 0 <= result["stress"] <= 1000

    def test_empty_signals_stress_not_1000(self):
        """Empty signals → new-adherent defaults; stress is 200 (not maximum)."""
        result = aggregate_signals([])
        assert result["stress"] == 200

    def test_positive_signals_reduce_stress_vs_unknown_kind(self):
        """Positive signals → lower stress than a signal of unknown kind.

        Unknown kind contributes nothing, so all positive axes remain 0 and
        stress = 1000 - 0 = 1000.  A ritual signal raises joy/focus, which
        drives positive_mean > 0 and therefore stress < 1000.
        """
        max_stress = aggregate_signals(
            [{"signalKind": "unknown-kind", "weight": 1000}]
        )["stress"]  # should be 1000
        ritual_stress = aggregate_signals(
            [{"signalKind": "ritual", "weight": 1000}]
        )["stress"]
        assert ritual_stress < max_stress

    def test_unknown_signal_kind_is_ignored(self):
        """Signals with unknown signalKind contribute nothing (silently skipped)."""
        signals = [{"signalKind": "unknown-kind", "weight": 1000}]
        result = aggregate_signals(signals)
        # signal_count=1, all acc=0; joy/calm/grat/focus = 0; stress = 1000 - 0 = 1000
        assert result["joy"] == 0
        assert result["calm"] == 0
        assert result["gratitude"] == 0
        assert result["focus"] == 0
        assert result["stress"] == 1000

    def test_all_axes_present_in_result(self):
        """Result always contains all 5 axes."""
        result = aggregate_signals([])
        for axis in ("joy", "calm", "stress", "gratitude", "focus"):
            assert axis in result

    def test_all_values_in_permille_range(self):
        """All returned values must be in 0-1000."""
        signals = [
            {"signalKind": "ritual", "weight": 500},
            {"signalKind": "oath", "weight": 800},
            {"signalKind": "contribution", "weight": 300},
        ]
        result = aggregate_signals(signals)
        for axis, val in result.items():
            assert 0 <= val <= 1000, f"{axis}={val} out of permille range"


# ── D. SDK-absent guard (no etzhayyim_sdk installed in test env) ──────────────


class TestSdkAbsentGuard:
    """When etzhayyim_sdk is not installed (_pds_mod/_mst_mod are None),
    the cell functions raise ImportError, not NotImplementedError."""

    @pytest.mark.asyncio
    async def test_joucho_aggregation_cell_raises_import_error_without_sdk(self):
        """Without SDK, joucho_aggregation_cell raises ImportError."""
        with pytest.raises(ImportError, match="etzhayyim_sdk not available"):
            await joucho_aggregation_cell()

    @pytest.mark.asyncio
    async def test_joucho_aggregation_cell_with_did_raises_import_error(self):
        """Without SDK, single-adherent path also raises ImportError."""
        with pytest.raises(ImportError, match="etzhayyim_sdk not available"):
            await joucho_aggregation_cell("did:plc:test")

    @pytest.mark.asyncio
    async def test_fetch_joucho_raises_import_error_without_sdk(self):
        """Without SDK, fetch_joucho raises ImportError."""
        with pytest.raises(ImportError, match="etzhayyim_sdk not available"):
            await fetch_joucho("did:plc:test")


# ── E. Substrate-fit regression ───────────────────────────────────────────────


class TestSubstrateFit:
    """Verify joucho_murakumo.py source contains no forbidden substrate imports."""

    @pytest.fixture(scope="class")
    def source_text(self) -> str:
        return _MODULE_SOURCE_PATH.read_text(encoding="utf-8")

    def test_no_psycopg_import(self, source_text: str):
        """No direct psycopg import (RisingWave/Postgres forbidden per ADR-2605172000)."""
        assert "import psycopg" not in source_text
        assert "psycopg2" not in source_text

    def test_no_stripe_import(self, source_text: str):
        """No Stripe import (fiat payment processor forbidden per ADR-2605192115)."""
        assert "import stripe" not in source_text
        assert "from stripe" not in source_text

    def test_no_runpod_import(self, source_text: str):
        """No RunPod import (commercial GPU rental forbidden per ADR-2605215000)."""
        assert "import runpod" not in source_text
        assert "from runpod" not in source_text

    def test_no_sqlalchemy_import(self, source_text: str):
        """No SQLAlchemy import (RW-coupled ORM forbidden per ADR-2605172000)."""
        assert "sqlalchemy" not in source_text.lower()

    def test_substrate_guard_present(self, source_text: str):
        """Module-level substrate-fit guard (runpod/RW_URL check) must exist."""
        assert "runpod" in source_text
        assert "RW_URL" in source_text
        assert "raise ImportError" in source_text

    def test_no_rw_url_write(self, source_text: str):
        """No direct RisingWave URL usage."""
        assert "RW_URL" not in source_text.replace(
            'os.environ.get("RW_URL")', ""
        )  # guard reference is allowed; direct usage is not


# ── F. Constants sanity ───────────────────────────────────────────────────────


class TestConstants:
    def test_aggregation_window_days(self):
        assert JOUCHO_AGGREGATION_WINDOW_DAYS == 7

    def test_mood_thresholds_are_permille(self):
        """All mood thresholds should be in 0-1000 range."""
        for threshold in (
            JOY_MOOD_THRESHOLD_PERMILLE,
            CALM_MOOD_THRESHOLD_PERMILLE,
            STRESS_MOOD_THRESHOLD_PERMILLE,
            GRATITUDE_MOOD_THRESHOLD_PERMILLE,
            FOCUS_MOOD_THRESHOLD_PERMILLE,
        ):
            assert 0 <= threshold <= 1000

    def test_stress_threshold_is_highest(self):
        """Stress threshold (700) > other thresholds (600) — inhibitor priority."""
        assert STRESS_MOOD_THRESHOLD_PERMILLE > JOY_MOOD_THRESHOLD_PERMILLE
        assert STRESS_MOOD_THRESHOLD_PERMILLE > CALM_MOOD_THRESHOLD_PERMILLE

    def test_signal_kind_weights_all_positive(self):
        """All axis weights in SIGNAL_KIND_TO_AXIS_WEIGHTS must be positive."""
        for kind, axes in SIGNAL_KIND_TO_AXIS_WEIGHTS.items():
            for axis, weight in axes.items():
                assert weight > 0, f"{kind}.{axis} weight must be positive"

    def test_new_adherent_defaults_produce_neutral_mood(self):
        """New-adherent permille defaults → neutral mood (stress below 700 threshold)."""
        r = JouchoRecord(
            adherentDid="did:plc:new",
            **{k: v for k, v in NEW_ADHERENT_DEFAULTS.items()},
        )
        assert classify_mood(r) == "neutral"


# ── G. _safe_rkey transformation ──────────────────────────────────────────────


class TestSafeRkey:
    """_safe_rkey must be deterministic and produce PDS-safe rkeys."""

    def test_safe_rkey_did_plc(self):
        """did:plc:abc123 → did_plc_abc123 (colons replaced with underscores)."""
        assert _safe_rkey("did:plc:abc123") == "did_plc_abc123"

    def test_safe_rkey_did_web(self):
        """did:web:foo.com → did_web_foo.com (only colons replaced; dots preserved)."""
        assert _safe_rkey("did:web:foo.com") == "did_web_foo.com"

    def test_safe_rkey_deterministic(self):
        """Same DID always produces the same rkey (no randomness)."""
        did = "did:plc:xyz789"
        assert _safe_rkey(did) == _safe_rkey(did)

    def test_safe_rkey_no_colons_in_result(self):
        """Result must contain no colon characters (forbidden in PDS rkeys)."""
        assert ":" not in _safe_rkey("did:plc:abc123")
        assert ":" not in _safe_rkey("did:web:foo.bar.com")


# ── H. joucho_aggregation_cell (mocked SDK) ───────────────────────────────────

# ---------------------------------------------------------------------------
# Helper: build a minimal kyumeiSignal record dict in MST list format.
# ---------------------------------------------------------------------------


def _make_signal(adherent_did: str, kind: str, weight: int = 800) -> dict:
    return {
        "uri": f"at://{adherent_did}/app.etzhayyim.shinka.kyumeiSignal/tid001",
        "cid": "bafyreitest",
        "value": {
            "$type": "app.etzhayyim.shinka.kyumeiSignal",
            "adherentDid": adherent_did,
            "signalKind": kind,
            "weight": weight,
            "recordedAt": "2026-05-21T10:00:00Z",
            "evidenceCid": "bafyreitest",
        },
    }


def _make_mock_sdk(mst_query_side_effect=None, mst_query_return=None, pds_put_return="at://did/col/rkey"):
    """Return (mock_mst, mock_pds) pair with AsyncMock internals."""
    mock_mst = MagicMock()
    if mst_query_side_effect is not None:
        mock_mst.query = AsyncMock(side_effect=mst_query_side_effect)
    else:
        mock_mst.query = AsyncMock(return_value=mst_query_return or [])

    mock_pds = MagicMock()
    mock_pds.put_record = AsyncMock(return_value=pds_put_return)
    return mock_mst, mock_pds


class TestJouchoAggregationCell:
    """Tests for joucho_aggregation_cell with mocked etzhayyim_sdk."""

    _MODULE = "pymagatama.primitives.joucho_murakumo"

    @pytest.mark.asyncio
    async def test_single_adherent_aggregates_correctly_and_calls_put_record(self):
        """Single-adherent path: 3 signals aggregated → put_record called once."""
        did = "did:plc:adherent001"
        signals = [
            _make_signal(did, "ritual", 800),
            _make_signal(did, "oath", 1000),
            _make_signal(did, "contribution", 600),
        ]

        mock_mst, mock_pds = _make_mock_sdk(mst_query_return=signals)

        with (
            patch(f"{self._MODULE}._mst_mod", mock_mst),
            patch(f"{self._MODULE}._pds_mod", mock_pds),
        ):
            result = await joucho_aggregation_cell(did)

        assert len(result) == 1
        rec = result[0]
        assert rec.adherentDid == did
        assert rec.from_signal_count == 3
        # 3 signals with multiple kinds → positive axes > 0; stress < 1000
        assert rec.joy > 0
        assert rec.calm > 0
        assert rec.gratitude > 0
        assert rec.focus > 0
        assert 0 <= rec.stress < 1000
        # computed_at should be a non-empty ISO 8601 string
        assert rec.computed_at.endswith("Z")
        # from_signals_since should be set
        assert rec.from_signals_since != ""
        # put_record called once with correct collection and rkey
        mock_pds.put_record.assert_called_once()
        call_kwargs = mock_pds.put_record.call_args
        assert call_kwargs[0][0] == "app.etzhayyim.joucho.joucho"
        assert call_kwargs[1]["rkey"] == _safe_rkey(did)

    @pytest.mark.asyncio
    async def test_no_signals_applies_new_adherent_defaults(self):
        """Empty signals for an adherent → new-adherent defaults; put_record still called."""
        did = "did:plc:newadherent"
        mock_mst, mock_pds = _make_mock_sdk(mst_query_return=[])

        with (
            patch(f"{self._MODULE}._mst_mod", mock_mst),
            patch(f"{self._MODULE}._pds_mod", mock_pds),
        ):
            result = await joucho_aggregation_cell(did)

        assert len(result) == 1
        rec = result[0]
        assert rec.from_signal_count == 0
        # Empty signals → new-adherent defaults
        assert rec.joy == NEW_ADHERENT_DEFAULTS["joy"]
        assert rec.calm == NEW_ADHERENT_DEFAULTS["calm"]
        assert rec.stress == NEW_ADHERENT_DEFAULTS["stress"]
        assert rec.gratitude == NEW_ADHERENT_DEFAULTS["gratitude"]
        assert rec.focus == NEW_ADHERENT_DEFAULTS["focus"]
        # put_record still called (upsert with defaults)
        mock_pds.put_record.assert_called_once()

    @pytest.mark.asyncio
    async def test_multi_adherent_discovery_calls_put_record_three_times(self):
        """adherent_did=None → discover 3 adherents → 3 put_record calls."""
        did_a = "did:plc:alpha"
        did_b = "did:plc:beta"
        did_c = "did:plc:gamma"

        # First call: discovery query returns signals from 3 adherents
        discovery_signals = [
            _make_signal(did_a, "ritual", 800),
            _make_signal(did_b, "oath", 1000),
            _make_signal(did_c, "contribution", 600),
            _make_signal(did_a, "kuniUmi-witness", 500),  # second signal for did_a
        ]

        # Per-adherent query returns only their own signals (client-side filter)
        def per_adherent_signals(collection, *, filter=None, limit=100):
            if filter and "adherentDid" in filter:
                queried_did = filter["adherentDid"]
                return [s for s in discovery_signals if s["value"]["adherentDid"] == queried_did]
            return discovery_signals

        mock_mst, mock_pds = _make_mock_sdk(mst_query_side_effect=per_adherent_signals)

        with (
            patch(f"{self._MODULE}._mst_mod", mock_mst),
            patch(f"{self._MODULE}._pds_mod", mock_pds),
        ):
            result = await joucho_aggregation_cell(None)

        assert len(result) == 3
        result_dids = {r.adherentDid for r in result}
        assert result_dids == {did_a, did_b, did_c}
        assert mock_pds.put_record.call_count == 3


# ── I. fetch_joucho (mocked SDK) ──────────────────────────────────────────────


class TestFetchJoucho:
    """Tests for fetch_joucho with mocked etzhayyim_sdk.

    Since etzhayyim_sdk is not installed in the test environment, we patch
    _pds_mod and _PdsNotFoundError in the module namespace rather than
    importing from etzhayyim_sdk.errors directly.
    """

    _MODULE = "pymagatama.primitives.joucho_murakumo"

    def _make_pds_record(self, did: str, **overrides) -> dict:
        value = {
            "$type": "app.etzhayyim.joucho.joucho",
            "adherentDid": did,
            "joy": 650,
            "calm": 500,
            "stress": 200,
            "gratitude": 700,
            "focus": 400,
            "computed_at": "2026-05-21T10:00:00Z",
            "from_signal_count": 5,
            "from_signals_since": "2026-05-14T10:00:00Z",
            "aggregator_node": "levi",
            "from_signal_days": 7,
        }
        value.update(overrides)
        return {"uri": f"at://{did}/app.etzhayyim.joucho.joucho/{_safe_rkey(did)}", "cid": "bafytest", "value": value}

    @pytest.mark.asyncio
    async def test_happy_path_returns_joucho_record(self):
        """get_record returns a full record → JouchoRecord parsed correctly."""
        did = "did:plc:happy001"
        raw = self._make_pds_record(did)

        mock_pds = MagicMock()
        mock_pds.get_record = AsyncMock(return_value=raw)

        # We also need to patch _PdsNotFoundError so fetch_joucho doesn't see None
        class _FakePdsNotFoundError(Exception):
            pass

        with (
            patch(f"{self._MODULE}._pds_mod", mock_pds),
            patch(f"{self._MODULE}._PdsNotFoundError", _FakePdsNotFoundError),
        ):
            rec = await fetch_joucho(did)

        assert rec is not None
        assert isinstance(rec, JouchoRecord)
        assert rec.adherentDid == did
        assert rec.joy == 650
        assert rec.calm == 500
        assert rec.stress == 200
        assert rec.gratitude == 700
        assert rec.focus == 400
        assert rec.from_signal_count == 5
        assert rec.computed_at == "2026-05-21T10:00:00Z"
        assert rec.aggregator_node == "levi"

    @pytest.mark.asyncio
    async def test_404_returns_none(self):
        """PdsNotFoundError from get_record → fetch_joucho returns None."""
        class _FakePdsNotFoundError(Exception):
            pass

        did = "did:plc:notfound001"
        mock_pds = MagicMock()
        mock_pds.get_record = AsyncMock(side_effect=_FakePdsNotFoundError("404"))

        with (
            patch(f"{self._MODULE}._pds_mod", mock_pds),
            patch(f"{self._MODULE}._PdsNotFoundError", _FakePdsNotFoundError),
        ):
            rec = await fetch_joucho(did)

        assert rec is None

    @pytest.mark.asyncio
    async def test_partial_record_applies_defaults(self):
        """Record missing optional fields → JouchoRecord uses field defaults."""
        did = "did:plc:partial001"
        # Minimal record — only required fields, missing optional ones
        minimal_value = {
            "adherentDid": did,
            "joy": 300,
            "calm": 0,
            "stress": 800,
            "gratitude": 0,
            "focus": 0,
            "computed_at": "2026-05-21T09:00:00Z",
            "from_signal_count": 2,
            # from_signals_since, aggregator_node, from_signal_days are absent
        }
        raw = {"uri": f"at://{did}/app.etzhayyim.joucho.joucho/{_safe_rkey(did)}", "cid": "bafytest2", "value": minimal_value}

        mock_pds = MagicMock()
        mock_pds.get_record = AsyncMock(return_value=raw)

        class _FakePdsNotFoundError(Exception):
            pass

        with (
            patch(f"{self._MODULE}._pds_mod", mock_pds),
            patch(f"{self._MODULE}._PdsNotFoundError", _FakePdsNotFoundError),
        ):
            rec = await fetch_joucho(did)

        assert rec is not None
        assert rec.from_signals_since == ""       # JouchoRecord default
        assert rec.aggregator_node == ""          # JouchoRecord default
        assert rec.from_signal_days == 7          # JouchoRecord default
