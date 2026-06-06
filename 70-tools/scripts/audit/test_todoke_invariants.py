"""Lock-in tests for the todoke (届け) constitutional invariants.

Pins the structural properties designed in ADR-2606042300 (todoke — last-mile /
curb-to-door autonomous delivery, ≤25 kg, SAE-L4 sidewalk ODD) so a future
refactor cannot silently weaken a constitutional invariant. The signature todoke
invariant is the G7 safety envelope that REFUSES (raises, never clamps) any plan
that exceeds the per-zone sidewalk-speed cap, enters a non-ODD zone (a vehicular
road, N2), or exceeds the SAE-L4 ceiling (N2).

The envelope is declared in TWO runtimes that must agree, plus the lexicons:

  enforcement point 1 — the Python method (`methods/last_mile.py`):
      `_check_envelope` / `plan_last_mile` raise EnvelopeViolation.
  enforcement point 2 — the Rust route core (`route/src/lib.rs`):
      `Zone::speed_cap_mps` — the per-zone caps the Python copy MUST match.
  enforcement point 3 — the published lexicons (`com.etzhayyim.todoke.*`):
      armed/gig/saeWithinCeiling/onDeviceOnly/serverSigned consts.

Invariants under test:

  1. N2/G7 (guard) — SAE_LEVEL_CEILING == 4 and the envelope raises on an
     over-ceiling SAE level, an over-cap commanded speed, and a road (non-ODD)
     zone; a clean sidewalk plan succeeds.
  2. parity — Python ZONE_SPEED_CAP_MPS == Rust Zone::speed_cap_mps (the file
     comment asserts they MUST match; this is the drift guard).
  3. N2 — lastMileRoute.saeWithinCeiling is const true.
  4. N2 — deliveryJob.armed is const false (no weaponised payload).
  5. G5 — deliveryJob.gig is const false (no-gig / cash≡0 labour).
  6. G8 — handoffProof.onDeviceOnly is const true (privacy-by-construction;
     no cloud image / face-match / biometric).
  7. G12 — handoffProof.serverSigned is const false (no-server-key).
  8. the safetyAlert refuse taxonomy pins the three envelope refusal reasons.
"""

from __future__ import annotations

import importlib.util
import json
import re
import sys
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parents[3]
_LEX = _REPO / "00-contracts" / "lexicons" / "com" / "etzhayyim" / "todoke"
_LAST_MILE = _REPO / "20-actors" / "todoke" / "methods" / "last_mile.py"
_RUST = _REPO / "20-actors" / "todoke" / "route" / "src" / "lib.rs"

# Rust enum variant name -> the lower-case zone key used in Python.
_ZONE_NAME_MAP = {
    "Sidewalk": "sidewalk",
    "Crosswalk": "crosswalk",
    "DoorPath": "doorpath",
    "BikeLane": "bikelane",
    "Road": "road",
}


def _load_json(p: Path) -> dict:
    return json.loads(p.read_text())


def _record_props(lex: dict) -> dict:
    return lex["defs"]["main"]["record"]["properties"]


def _import_last_mile():
    spec = importlib.util.spec_from_file_location("todoke_last_mile", _LAST_MILE)
    mod = importlib.util.module_from_spec(spec)
    # Register before exec: the @dataclass Stop resolves InitVar/annotations via
    # sys.modules[cls.__module__] at class-creation time (Python 3.12+).
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def _rust_speed_caps() -> dict[str, float | None]:
    text = _RUST.read_text()
    body = re.search(r"fn speed_cap_mps.*?\{(.*?)\n\s*\}", text, re.S)
    assert body, "could not locate Zone::speed_cap_mps in the Rust core"
    caps: dict[str, float | None] = {}
    for variant, val in re.findall(r"Zone::(\w+)\s*=>\s*(Some\([\d.]+\)|None)", body.group(1)):
        key = _ZONE_NAME_MAP.get(variant)
        if key is None:
            continue
        if val == "None":
            caps[key] = None
        else:
            caps[key] = float(re.search(r"[\d.]+", val).group())
    return caps


# ─────────────────────────────────────────────────────────────────────────
# 1. N2/G7 — the envelope REFUSES (raises), never clamps
# ─────────────────────────────────────────────────────────────────────────


def test_n2_g7_envelope_refuses_violations():
    lm = _import_last_mile()
    assert lm.SAE_LEVEL_CEILING == 4, (
        f"N2: SAE ceiling MUST be 4 (Level 5 is a non-goal); got {lm.SAE_LEVEL_CEILING}"
    )
    sidewalk = [lm.Stop(0, 0.0, 0.0, "sidewalk"), lm.Stop(1, 5.0, 0.0, "sidewalk")]
    sidewalk_cap = lm.ZONE_SPEED_CAP_MPS["sidewalk"]

    # over SAE ceiling → refuse
    with pytest.raises(lm.EnvelopeViolation):
        lm.plan_last_mile(sidewalk, sae_level=5, commanded_mps=1.0)
    # commanded speed over the sidewalk cap → refuse
    with pytest.raises(lm.EnvelopeViolation):
        lm.plan_last_mile(sidewalk, sae_level=4, commanded_mps=sidewalk_cap + 0.5)
    # a vehicular road is outside the ODD (cap None) → refuse
    with pytest.raises(lm.EnvelopeViolation):
        lm.plan_last_mile([lm.Stop(0, 0.0, 0.0, "road")], sae_level=4, commanded_mps=0.5)

    # a clean sidewalk plan at/under cap succeeds.
    order = lm.plan_last_mile(sidewalk, sae_level=4, commanded_mps=sidewalk_cap)
    assert order is not None


# ─────────────────────────────────────────────────────────────────────────
# 2. parity — Python caps == Rust caps (the file comment's "MUST match")
# ─────────────────────────────────────────────────────────────────────────


def test_python_and_rust_zone_caps_agree():
    lm = _import_last_mile()
    py = dict(lm.ZONE_SPEED_CAP_MPS)
    rust = _rust_speed_caps()
    assert py == rust, (
        "todoke zone speed caps drifted between Python (last_mile.py) and Rust "
        f"(route/src/lib.rs):\n  py:   {py}\n  rust: {rust}"
    )
    assert py.get("road") is None, "N2: 'road' MUST stay outside the ODD (cap None)"


# ─────────────────────────────────────────────────────────────────────────
# 3. N2 — lastMileRoute stays within the SAE ceiling
# ─────────────────────────────────────────────────────────────────────────


def test_n2_last_mile_route_sae_within_ceiling_const_true():
    props = _record_props(_load_json(_LEX / "lastMileRoute.json"))
    assert props["saeWithinCeiling"].get("const") is True, (
        "N2: lastMileRoute.saeWithinCeiling MUST be const true (SAE-L4 ceiling)"
    )


# ─────────────────────────────────────────────────────────────────────────
# 4 + 5. N2 / G5 — deliveryJob is unarmed + non-gig
# ─────────────────────────────────────────────────────────────────────────


def test_n2_g5_delivery_job_unarmed_and_non_gig():
    props = _record_props(_load_json(_LEX / "deliveryJob.json"))
    assert props["armed"].get("const") is False, (
        "N2: deliveryJob.armed MUST be const false (no weaponised payload)"
    )
    assert props["gig"].get("const") is False, (
        "G5: deliveryJob.gig MUST be const false (no-gig labour, cash≡0)"
    )


# ─────────────────────────────────────────────────────────────────────────
# 6 + 7. G8 / G12 — handoff proof is on-device + not server-signed
# ─────────────────────────────────────────────────────────────────────────


def test_g8_g12_handoff_proof_on_device_and_no_server_key():
    props = _record_props(_load_json(_LEX / "handoffProof.json"))
    assert props["onDeviceOnly"].get("const") is True, (
        "G8: handoffProof.onDeviceOnly MUST be const true (privacy-by-construction; "
        "no cloud image / face-match / biometric)"
    )
    assert props["serverSigned"].get("const") is False, (
        "G12: handoffProof.serverSigned MUST be const false (no-server-key)"
    )


# ─────────────────────────────────────────────────────────────────────────
# 8. the safetyAlert refuse taxonomy pins the envelope refusal reasons
# ─────────────────────────────────────────────────────────────────────────


def test_safety_alert_refuse_taxonomy_is_pinned():
    kinds = set(_record_props(_load_json(_LEX / "safetyAlert.json"))["kind"]["enum"])
    required = {"sae-level-too-high", "zone-outside-odd", "speed-exceeds-zone-cap"}
    missing = required - kinds
    assert not missing, (
        f"safetyAlert.kind MUST carry the envelope refusal reasons; missing {sorted(missing)}"
    )


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
