"""Lock-in tests for the kokoro (心 / mental-health support) constitutional invariants.

kokoro is the mental-health support actor (NOT clinical psychiatry). Its lexicons
encode some of the repo's sharpest ethical red lines — bans on conversion therapy,
AI-only therapy, video recording, surveillance mood-monitoring, mandatory
screening, and commercial mental-health software — plus structural PHI encryption
for session content (ADR-2605181100). This suite pins them so a refactor cannot
silently weaken a constitutional invariant. Mirrors the tadori/tsukuroi/karute
lock-in suites.

  1. Structural PHI encryption — the session-content lexicons require their
     encrypted-CID field (no plaintext therapy content on MST).
  2. Mental-health ethics red lines — silenKokoroReview pins 8 zero-counters
     const 0 + the counselor-vocation ratio const 10000 (100.00%).
  3. Free-conscience / no-surveillance — peerSupportCircleAttestation pins
     optInOnly const true (G9) + surveillanceBasedMonitoring const false (G10).
  4. No floats (Lexicon v1); id↔namespace; manifest namespaces match disk.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parents[3]
_LEX = _REPO / "00-contracts" / "lexicons" / "com" / "etzhayyim" / "kokoro"
# manifest invariants → 20-actors/kokoro/methods/test_manifest_invariants.cljc (jsonld retired)

# silenKokoroReview counters that MUST be structurally zero (the ethics red lines).
_ZERO_COUNTERS = [
    "clinicalPsychiatricEntityPenetrationPct",
    "videoRecordingEventsCount",
    "conversionTherapyEventsCount",
    "aiOnlyTherapyEventsCount",
    "commercialMentalHealthSoftwarePenetrationPct",
    "commercialAiTherapyChatbotPenetrationPct",
    "mandatoryScreeningEventsCount",
    "surveillanceBasedMoodMonitoringEventsCount",
]


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


# ─── 1. structural PHI encryption ───────────────────────────────────────


class TestPhiEncryption:
    @pytest.mark.parametrize("stem,field", [
        ("griefSupportAttestation", "encryptedPayloadCid"),
        ("peerSupportCircleAttestation", "encryptedPayloadCid"),
        ("acuteCrisisEscalationLog", "encryptedContextCid"),
    ])
    def test_session_content_requires_encrypted_cid(self, stem, field):
        req = set(_rec(stem)["required"])
        assert field in req, (
            f"{stem}: {field} must be required — session content stays in the "
            "com.etzhayyim.encrypted.* envelope, never plaintext on MST (ADR-2605181100)"
        )

    def test_subjects_are_pseudonymized(self):
        # Minimum-disclosure: subjects are pseudonym DIDs, not real identities.
        grief = set(_rec("griefSupportAttestation")["required"])
        assert "bereavedPseudonymDid" in grief
        acute = set(_rec("acuteCrisisEscalationLog")["required"])
        assert "affectedPseudonymDid" in acute


# ─── 2. mental-health ethics red lines (silenKokoroReview) ──────────────


class TestEthicsRedLines:
    def test_eight_zero_counters_const_zero(self):
        props = _rec("silenKokoroReview")["properties"]
        for c in _ZERO_COUNTERS:
            assert props.get(c, {}).get("const") == 0, (
                f"silenKokoroReview.{c} must be const 0 — a constitutional ban "
                "(conversion therapy / AI-only therapy / video / surveillance / "
                "mandatory screening / commercial software)"
            )

    def test_counselor_vocation_ratio_full_compliance(self):
        props = _rec("silenKokoroReview")["properties"]
        ratio = props["counselorVocationFlowCompliantRatioPctIntegerHundredths"]
        assert ratio.get("const") == 10000, "100.00% (integer-hundredths) vocation-flow compliance required"

    def test_zero_counter_set_has_not_shrunk(self):
        # Guard against a counter being silently dropped from the review.
        props = _rec("silenKokoroReview")["properties"]
        const_zero = {k for k, v in props.items() if isinstance(v, dict) and v.get("const") == 0}
        missing = set(_ZERO_COUNTERS) - const_zero
        assert not missing, f"silenKokoroReview dropped ethics counters: {missing}"


# ─── 3. free conscience / no surveillance ───────────────────────────────


class TestFreeConscienceNoSurveillance:
    def test_peer_circle_opt_in_only_const_true(self):
        p = _rec("peerSupportCircleAttestation")["properties"]["optInOnly"]
        assert p.get("const") is True, "G9: participation is opt-in only (free conscience)"

    def test_peer_circle_no_surveillance_monitoring(self):
        p = _rec("peerSupportCircleAttestation")["properties"]["surveillanceBasedMonitoring"]
        assert p.get("const") is False, (
            "G10: no smart-wearable mood tracking / facial-emotion / voice-affect analysis"
        )


# ─── 4. Lexicon hygiene + manifest consistency ──────────────────────────


class TestLexiconHygiene:
    @pytest.mark.parametrize("path", sorted(_LEX.glob("*.json")))
    def test_no_number_type(self, path):
        bad = [n for n in _walk(_load(path)) if n.get("type") == "number"]
        assert not bad, f"{path.name}: no `type: number` (ADR-2605190900); found {len(bad)}"

    def test_each_id_matches_namespace(self):
        for p in _LEX.glob("*.json"):
            assert _load(p)["id"] == f"com.etzhayyim.kokoro.{p.stem}"

