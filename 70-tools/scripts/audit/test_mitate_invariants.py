"""Lock-in tests for the mitate (見立て / diagnostic + treatment routing) invariants.

mitate is the diagnostic-routing advisory actor (ADR-2605260100): symptom intake
→ Bayesian 鑑別 advisory → test-ordering routing → treatment-plan advisory →
longitudinal followup. It is NOT a prescriber/surgeon. Health data is PHI and MUST
stay in the com.etzhayyim.encrypted.* envelope (ADR-2605181100); plaintext
symptom/診断/検査結果 on MST is prohibited (CLAUDE.md Boundaries). This suite pins
the schema-enforceable invariants. Mirrors the karute/kokoro/iyashi lock-in suites.

  1. Structural PHI encryption — the symptom / result / followup lexicons require
     their encrypted-envelope field (no plaintext clinical content on MST).
  2. No floats (Lexicon v1, ADR-2605190900); id↔namespace.
  3. Manifest ↔ disk consistency — every mitate lexicon on disk is declared in the
     manifest. (This suite re-declared diagnosticConsentReceipt, which the manifest
     and the CLAUDE.md "8 lexicons" count had drifted past — disk has 9.)
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parents[3]
_LEX = _REPO / "00-contracts" / "lexicons" / "com" / "etzhayyim" / "mitate"
# manifest invariants → 20-actors/mitate/methods/test_manifest_invariants.cljc (jsonld retired)

# Lexicon stem → its required encrypted-envelope field (PHI content carriers).
_ENC_FIELD = {
    "rhinitisIntake": "encryptedSymptomEnvelope",
    "diagnosticResult": "encryptedResultEnvelope",
    "outcomeFollowup": "encryptedFollowupEnvelope",
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


def _rec(stem: str) -> dict:
    return _load(_LEX / f"{stem}.json")["defs"]["main"]["record"]


# ─── 1. structural PHI encryption ───────────────────────────────────────


class TestPhiEncryption:
    @pytest.mark.parametrize("stem,field", sorted(_ENC_FIELD.items()))
    def test_clinical_content_requires_encrypted_envelope(self, stem, field):
        req = set(_rec(stem)["required"])
        assert field in req, (
            f"{stem}: {field} must be required — clinical content stays in the "
            "com.etzhayyim.encrypted.* envelope, never plaintext on MST (ADR-2605181100)"
        )


# ─── 2. Lexicon hygiene ─────────────────────────────────────────────────


class TestLexiconHygiene:
    @pytest.mark.parametrize("path", sorted(_LEX.glob("*.json")))
    def test_no_number_type(self, path):
        bad = [n for n in _walk(_load(path)) if n.get("type") == "number"]
        assert not bad, f"{path.name}: no `type: number` (ADR-2605190900); found {len(bad)}"

    def test_each_id_matches_namespace(self):
        for p in _LEX.glob("*.json"):
            assert _load(p)["id"] == f"com.etzhayyim.mitate.{p.stem}"


# ─── 3. manifest ↔ disk consistency (the orphan this suite closed) ──────

