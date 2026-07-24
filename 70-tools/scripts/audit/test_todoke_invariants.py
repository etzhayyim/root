"""Lock-in tests for the todoke (届け) constitutional invariants.

Pins the structural properties designed in ADR-2606042300 (todoke — last-mile /
curb-to-door autonomous delivery, ≤25 kg, SAE-L4 sidewalk ODD) so a future
refactor cannot silently weaken a constitutional invariant. The signature todoke
invariant is the G7 safety envelope that REFUSES (raises, never clamps) any plan
that exceeds the per-zone sidewalk-speed cap, enters a non-ODD zone (a vehicular
road, N2), or exceeds the SAE-L4 ceiling (N2).

The envelope is declared in TWO runtimes that must agree, plus the lexicons:

  enforcement point 1 — the Clojure method (`methods/last_mile.cljc`):
      `check-envelope` / `plan-last-mile` raise ex-info with :envelope-violation.
  enforcement point 2 — the Rust route core (`route/src/lib.rs`):
      `Zone::speed_cap_mps` — the per-zone caps the cljc copy MUST match.
  enforcement point 3 — the published lexicons (`com.etzhayyim.todoke.*`):
      armed/gig/saeWithinCeiling/onDeviceOnly/serverSigned consts.

Invariants under test:

  1. N2/G7 (guard) — sae-level-ceiling == 4 and the envelope raises on an
     over-ceiling SAE level, an over-cap commanded speed, and a road (non-ODD)
     zone; a clean sidewalk plan succeeds.
  2. parity — cljc zone-speed-cap-mps == Rust Zone::speed_cap_mps (the file
     comment asserts they MUST match; this is the drift guard).
  3. N2 — lastMileRoute.saeWithinCeiling is const true.
  4. N2 — deliveryJob.armed is const false (no weaponised payload).
  5. G5 — deliveryJob.gig is const false (no-gig / cash≡0 labour).
  6. G8 — handoffProof.onDeviceOnly is const true (privacy-by-construction;
     no cloud image / face-match / biometric).
  7. G12 — handoffProof.serverSigned is const false (no-server-key).
  8. the safetyAlert refuse taxonomy pins the three envelope refusal reasons.

NOTE: enforcement points 1 and 2 now exercise the cljc port
(methods/last_mile.cljc via bb subprocess) since the Python methods/last_mile.py
was migrated to cljc.
"""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parents[3]
_LEX = _REPO / "00-contracts" / "lexicons" / "com" / "etzhayyim" / "todoke"
_RUST = _REPO / "20-actors" / "todoke" / "route" / "src" / "lib.rs"
_ACTORS = _REPO / "20-actors"

# Rust enum variant name -> the lower-case zone key used in cljc.
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


def _bb(expr: str) -> subprocess.CompletedProcess:
    """Run a Clojure expression via bb with the actors classpath."""
    return subprocess.run(
        ["bb", "--classpath", str(_ACTORS), "-e", expr],
        capture_output=True,
        text=True,
        check=False,
        cwd=str(_REPO),
    )


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
    """G7: plan-last-mile MUST raise on SAE-ceiling/speed/zone violations (via bb)."""
    result = _bb(
        "(require '[todoke.methods.last-mile :as lm])"
        "(def ceiling lm/sae-level-ceiling)"
        "(def sidewalk-cap (get lm/zone-speed-cap-mps \"sidewalk\"))"
        "(def sidewalk [{:id 0 :x 0.0 :y 0.0 :zone \"sidewalk\"}"
        "               {:id 1 :x 5.0 :y 0.0 :zone \"sidewalk\"}])"
        # SAE level above ceiling: refuse
        "(def r1 (try (lm/plan-last-mile sidewalk :sae-level 5 :commanded-mps 1.0)"
        "             :no-throw (catch Exception e :threw)))"
        # Speed over cap: refuse
        "(def r2 (try (lm/plan-last-mile sidewalk :sae-level 4 :commanded-mps (+ sidewalk-cap 0.5))"
        "             :no-throw (catch Exception e :threw)))"
        # Road zone (outside ODD): refuse
        "(def r3 (try (lm/plan-last-mile [{:id 0 :x 0.0 :y 0.0 :zone \"road\"}]"
        "                                :sae-level 4 :commanded-mps 0.5)"
        "             :no-throw (catch Exception e :threw)))"
        # Clean sidewalk plan at cap: pass
        "(def r4 (lm/plan-last-mile sidewalk :sae-level 4 :commanded-mps sidewalk-cap))"
        "(pr {:ceiling ceiling :r1 r1 :r2 r2 :r3 r3 :r4-ok (not (nil? r4))})"
    )
    assert result.returncode == 0, f"bb failed: {result.stderr}"
    out = result.stdout
    assert ":ceiling 4" in out, (
        f"N2: sae-level-ceiling MUST be 4 (Level 5 is a non-goal); stdout={out!r}"
    )
    assert ":r1 :threw" in out, (
        f"N2/G7: plan-last-mile MUST throw on SAE level > ceiling; stdout={out!r}"
    )
    assert ":r2 :threw" in out, (
        f"G7: plan-last-mile MUST throw on commanded speed > zone cap; stdout={out!r}"
    )
    assert ":r3 :threw" in out, (
        f"N2/G7: plan-last-mile MUST throw for a road (outside ODD); stdout={out!r}"
    )
    assert ":r4-ok true" in out, (
        f"G7: a clean sidewalk plan at/under cap should succeed; stdout={out!r}"
    )


# ─────────────────────────────────────────────────────────────────────────
# 2. parity — cljc caps == Rust caps (the file comment's "MUST match")
# ─────────────────────────────────────────────────────────────────────────


def test_clj_and_rust_zone_caps_agree():
    """Parity: cljc zone-speed-cap-mps MUST equal Rust Zone::speed_cap_mps."""
    # Read cljc caps via bb
    result = _bb(
        "(require '[todoke.methods.last-mile :as lm])"
        "(pr lm/zone-speed-cap-mps)"
    )
    assert result.returncode == 0, f"bb failed: {result.stderr}"
    # Parse the EDN map printed by pr (format: {sidewalk 1.8, crosswalk 1.4, ...})
    caps_str = result.stdout.strip()
    # Extract key-value pairs from the printed map
    clj: dict[str, float | None] = {}
    for m in re.finditer(r'"?(\w+)"?\s+([\d.]+|nil)', caps_str):
        key, val = m.group(1), m.group(2)
        clj[key] = None if val == "nil" else float(val)

    assert _RUST.exists(), f"Rust route core missing: {_RUST}"
    rust = _rust_speed_caps()
    assert clj == rust, (
        "todoke zone speed caps drifted between cljc (last_mile.cljc) and Rust "
        f"(route/src/lib.rs):\n  cljc: {clj}\n  rust: {rust}"
    )
    assert clj.get("road") is None, "N2: 'road' MUST stay outside the ODD (cap None)"


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
