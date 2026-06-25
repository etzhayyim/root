"""Lock-in tests for the toritsugi (取次) constitutional invariants.

Pins the structural properties designed in ADR-2605312030 (取次 toritsugi —
citizen-facing government-procedure concierge; the service-delivery counterpart
to passive danjo, ADR-2605301600, and to himotoki, ADR-2605302130) so a future
refactor cannot silently weaken a constitutional invariant. None are amendable
without Council process; this suite fails fast if any artifact drifts. Mirrors
test_tsukuroi_invariants.py / test_tadori_invariants.py.

Invariants under test (the citizen-side / 行政書士法-UPL-bounded /
self-submit-default ceiling, ADR-2605312030 §4):

  1. The 7 R0 cell stubs raise at import time until R1.
  2. The manifest pins 15 gates G1..G15 + 6 lexiconNamespaces matching disk,
     and 7 cells whose module paths match the on-disk kotodama.cells dirs.
  3. No `type: number` (float) anywhere in the lexicons (Lexicon v1,
     ADR-2605190900).
  4. G8 non-fabrication + G14: `procedure` requires legalBasis + provenance +
     verificationStatus; verificationStatus knownValues are exactly the three
     verification tiers.
  5. G5 行政書士法/UPL: `applicationDraft.assistMode` admits ONLY "input-assist"
     (作成代理 is unrepresentable at the schema layer).
  6. G15 self-submit-default: `submissionRecord.mode` is required and admits
     exactly {member-self-submit, agent-on-behalf}; a councilGateRef field
     exists (the 代行 R3 gate).
  7. G14 + G8 seed honesty: every seed procedure ships verificationStatus =
     unverified-seed AND cites legalBasis + provenance.
  8. G15 structural double-gate: the submit cell pins DAIKOU_R3_GATE_TX = None.
  9. G6 PII confidentiality: the member-PII-bearing records expose ONLY an
     encrypted-envelope pointer field, never an inline plaintext content field.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parents[3]
_LEX = _REPO / "00-contracts" / "lexicons" / "com" / "etzhayyim" / "toritsugi"
_PROCEDURE = _LEX / "procedure.json"
_BENEFIT = _LEX / "benefitMatch.json"
_GUIDE = _LEX / "procedureGuide.json"
_DRAFT = _LEX / "applicationDraft.json"
_SUBMISSION = _LEX / "submissionRecord.json"
_STATUS = _LEX / "statusTrack.json"
# manifest invariants -> 20-actors/toritsugi/methods/test_manifest_invariants.cljc (jsonld retired)
_SEED = _REPO / "20-actors" / "toritsugi" / "registry" / "procedures.seed.json"
_CELLS = _REPO / "20-actors" / "kotodama" / "cells"

_CELL_NAMES = [
    "toritsugi_procedure_registry",
    "toritsugi_eligibility_match",
    "toritsugi_intake",
    "toritsugi_guide",
    "toritsugi_draft",
    "toritsugi_submit",
    "toritsugi_status_track",
]


def _load(path: Path) -> dict:
    return json.loads(path.read_text())


def _props(lex: dict) -> dict:
    return lex["defs"]["main"]["record"]["properties"]


def _required(lex: dict) -> list:
    return lex["defs"]["main"]["record"].get("required", [])


# ─────────────────────────────────────────────────────────────────────────
# 1. cell stubs raise at import
# ─────────────────────────────────────────────────────────────────────────


def test_seven_cells_raise_at_import():
    assert len(_CELL_NAMES) == 7
    for name in _CELL_NAMES:
        cell_path = _CELLS / name / "cell.py"
        assert cell_path.exists(), f"missing cell scaffold: {name}"
        spec = importlib.util.spec_from_file_location(f"_t_{name}", cell_path)
        mod = importlib.util.module_from_spec(spec)
        with pytest.raises(RuntimeError, match="R0 scaffold"):
            spec.loader.exec_module(mod)


# ─────────────────────────────────────────────────────────────────────────
# 2. manifest pins 15 gates + 6 namespaces + 7 cells matching disk
# ─────────────────────────────────────────────────────────────────────────


# ─────────────────────────────────────────────────────────────────────────
# 3. No type: number anywhere
# ─────────────────────────────────────────────────────────────────────────


def test_no_float_types():
    for path in _LEX.glob("*.json"):
        blob = path.read_text()
        assert '"type": "number"' not in blob, f"{path.name}: no float (Lexicon v1)"


# ─────────────────────────────────────────────────────────────────────────
# 3b. Each lexicon id matches its filename namespace + is a v1 record
#     (pins the green state of nsid-lexicon-exists / lexicon-primary-types so
#      a renamed id or a dropped `record` def fails here, not silently)
# ─────────────────────────────────────────────────────────────────────────


def test_lexicon_id_matches_namespace_and_is_v1_record():
    files = sorted(_LEX.glob("*.json"))
    assert len(files) == 6, "exactly 6 toritsugi lexicons on disk"
    for path in files:
        lex = _load(path)
        assert lex.get("lexicon") == 1, f"{path.name}: must be Lexicon v1"
        assert lex["id"] == f"com.etzhayyim.toritsugi.{path.stem}", (
            f"{path.name}: id must equal com.etzhayyim.toritsugi.{path.stem}"
        )
        assert lex["defs"]["main"]["type"] == "record", f"{path.name}: main is a record"
        assert isinstance(_props(lex), dict) and _props(lex), (
            f"{path.name}: record.properties must be a non-empty object"
        )


# ─────────────────────────────────────────────────────────────────────────
# 4. G8 + G14: procedure requires legalBasis + provenance + verificationStatus
# ─────────────────────────────────────────────────────────────────────────


def test_procedure_nonfabrication_and_verification_gate():
    lex = _load(_PROCEDURE)
    req = _required(lex)
    for field in ("legalBasis", "provenance", "verificationStatus"):
        assert field in req, f"G8/G14: procedure MUST require {field}"
    vs = _props(lex)["verificationStatus"]["knownValues"]
    assert set(vs) == {"unverified-seed", "maintainer-verified", "council-verified"}, vs


# ─────────────────────────────────────────────────────────────────────────
# 5. G5: applicationDraft.assistMode admits ONLY input-assist
# ─────────────────────────────────────────────────────────────────────────


def test_application_draft_input_assist_only():
    props = _props(_load(_DRAFT))
    assist = props["assistMode"]["knownValues"]
    assert assist == ["input-assist"], "G5: 作成代理 must be unrepresentable"
    assert "memberConfirmed" in _required(_load(_DRAFT)), "G8: member must confirm"


# ─────────────────────────────────────────────────────────────────────────
# 6. G15: submissionRecord.mode required + self-submit default + 代行 gate
# ─────────────────────────────────────────────────────────────────────────


def test_submission_mode_and_council_gate():
    lex = _load(_SUBMISSION)
    props = _props(lex)
    assert "mode" in _required(lex), "G15: mode MUST be required"
    modes = props["mode"]["knownValues"]
    assert set(modes) == {"member-self-submit", "agent-on-behalf"}, modes
    assert modes[0] == "member-self-submit", "G15: self-submit is the default-first mode"
    assert "councilGateRef" in props, "G15: 代行 (agent-on-behalf) needs a council gate ref"


# ─────────────────────────────────────────────────────────────────────────
# 7. G14 + G8: seed honesty — all unverified-seed + cite legalBasis/provenance
# ─────────────────────────────────────────────────────────────────────────


def test_seed_all_unverified_and_cited():
    seed = _load(_SEED)
    procs = seed["procedures"]
    assert len(procs) >= 6, "seed ships >= 6 procedures"
    # UNIVERSAL invariants (every entry, every jurisdiction): G14 unverified-seed
    # + G8 non-empty https provenance. The DEEP worldwide-data invariants
    # (distinct-jurisdiction span, per-currency fee shape, etc.) are owned by the
    # sibling suite test_toritsugi_registry_seed.py per the 2026-06-02 division of
    # responsibility (this JP-origin suite pins the lexicon/manifest/cell shape +
    # the JP backbone; the sibling pins the worldwide registry data).
    for p in procs:
        assert p["verificationStatus"] == "unverified-seed", (
            f"G14: seed {p.get('procedureId')} MUST ship unverified-seed"
        )
        prov = p.get("provenance") or ""
        assert prov, f"G8: {p.get('procedureId')} MUST cite provenance"
        assert prov.startswith("https://"), (
            f"G8: {p.get('procedureId')} provenance MUST be https"
        )
    # STRICT JP-backbone invariants: the original .go.jp-only fail-closed rule
    # (VERIFICATION.md) + legalBasis citation are enforced on the JP rows, where a
    # single authoritative official-domain pattern (.go.jp) and a known statute
    # citation are reliable. They are NOT imposed on worldwide rows, where (a) no
    # single official-domain pattern holds without false-negatives on legitimate
    # official sites (canada.ca / government.nl / borger.dk / poliziadistato.it),
    # and (b) fabricating a per-country statute number would itself violate G8 —
    # those rows leave legalBasis null rather than invent one (resolve at guide
    # time). Comment at the original site said "widen as other jurisdictions
    # land"; the honest widening is to scope, not to loosen, the strict checks.
    jp = [p for p in procs if p.get("jurisdiction") == "jpn"]
    assert jp, "JP backbone MUST remain present in the seed"
    for p in jp:
        assert p.get("legalBasis"), (
            f"G8: JP-backbone {p.get('procedureId')} MUST cite legalBasis"
        )
        prov = p.get("provenance") or ""
        assert ".go.jp" in prov, (
            f"G8: JP-backbone {p.get('procedureId')} provenance MUST be an official "
            f".go.jp source (VERIFICATION.md fail-closed rule); got {prov}"
        )


# ─────────────────────────────────────────────────────────────────────────
# 8. G15 structural double-gate: submit cell pins DAIKOU_R3_GATE_TX = None
# ─────────────────────────────────────────────────────────────────────────


def test_submit_cell_daikou_gate_present_and_none():
    src = (_CELLS / "toritsugi_submit" / "cell.py").read_text()
    assert "DAIKOU_R3_GATE_TX" in src, "G15: 代行 R3 gate constant MUST exist"
    assert "DAIKOU_R3_GATE_TX: str | None = None" in src, "G15: 代行 gate MUST default None"


# ─────────────────────────────────────────────────────────────────────────
# 9. G6: PII-bearing records expose ONLY an encrypted-envelope pointer
# ─────────────────────────────────────────────────────────────────────────


def test_pii_only_via_encrypted_pointer():
    # Each PII-bearing record references an com.etzhayyim.encrypted.* envelope
    # via a *Ref pointer field, and carries no inline plaintext content field.
    expectations = {
        _DRAFT: "encryptedDraftRef",
        _BENEFIT: "encryptedDetailRef",
        _STATUS: "resultRef",
        _SUBMISSION: "receiptRef",
    }
    for path, ptr in expectations.items():
        props = _props(_load(path))
        assert ptr in props, f"G6: {path.name} MUST expose encrypted pointer {ptr}"
        forbidden = {"content", "plaintext", "rawForm", "piiInline"}
        assert not (forbidden & set(props)), f"G6: {path.name} must not inline PII"


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))

