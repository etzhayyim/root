#!/usr/bin/env python3
"""mitooshi 見通し — backtest scorecard → promotion decision (R1, offline).

ADR-2606051800. The last leg of the loop: feed the rolling-origin backtest scorecard
(forecast.py) into the calibration_gate (cells/calibration_gate) and emit a PROMOTION
DECISION per method. A model version only goes live if it CLEARS the gate:
  G12 — beats its baseline (mean-skill > 0),
  G7  — is calibrated (PIT deviation ≤ ceiling),
  G9  — is member/operator-signed (server signature refused — no-server-key),
  G1  — no evaluated forecast asserts a point.

This is a REFUSAL gate: it never auto-promotes; it refuses anything that fails a gate, and
live promotion remains G10-gated (Council Lv6+ + operator). The decision is emitted as
:fc.promotion datoms — the exact record a live promotion would append.

Honest note: on the real two-regime :representative trail the scorecard is SKILLED (G12 ok)
but MISCALIBRATED (deviation ≫ ceiling), so the correct decision is G7 REFUSED — the gate
working as designed, not a bug. Non-trivial calibrated promotion needs real time-varying
ingest (G10-gated).

stdlib only. Usage:
    python3 promote.py --scorecard ../data/persisted/chokepoint-backtest-scorecard.kotoba.edn \
                       [--signed-by did:web:etzhayyim.com:member:...] [--deviation-max 0.4] [--out OUTDIR]
"""
from __future__ import annotations

import os
import pathlib
import sys

try:
    from analyze import load_edn
except ImportError:
    from mitooshi.methods.analyze import load_edn  # type: ignore

# the canonical gate logic from the calibration_gate cell (single source of truth).
# Loaded under a UNIQUE module name to avoid colliding with other cells' state_machine.py.
import importlib.util as _ilu

_CG = (pathlib.Path(__file__).resolve().parent.parent / "cells" / "calibration_gate"
       / "state_machine.py")
_spec = _ilu.spec_from_file_location("mitooshi_calibration_gate_sm", _CG)
_cg_mod = _ilu.module_from_spec(_spec)
sys.modules[_spec.name] = _cg_mod          # register so the cell's @dataclass resolves
_spec.loader.exec_module(_cg_mod)  # type: ignore
DEFAULT_DEVIATION_MAX = _cg_mod.DEFAULT_DEVIATION_MAX
review_promotion = _cg_mod.review_promotion


def decide_from_scorecard(rows: list[dict], signed_by: str = "",
                          deviation_max: float = DEFAULT_DEVIATION_MAX) -> list[dict]:
    """Run each scorecard method through the calibration_gate. Returns decision rows:
    {method, skill, deviation, phase, refusal, promoted}."""
    out: list[dict] = []
    for r in rows:
        if ":fc.score/method" not in r:
            continue
        method = str(r[":fc.score/method"]).lstrip(":")
        skill = float(r.get(":fc.score/mean-skill", 0.0) or 0.0)
        deviation = float(r.get(":fc.score/calibration-deviation", 0.0) or 0.0)
        result = review_promotion({
            "model_id": f"chokepoint-{method}",
            "skill": skill,
            "deviation": deviation,
            "deviation_max": deviation_max,
            "signed_by": signed_by,
        })
        cs = result["cell_state"]
        out.append({"method": method, "skill": skill, "deviation": deviation,
                    "phase": cs["phase"], "refusal": cs["refusal"],
                    "promoted": cs.get("payload", {}).get("promoted", False)})
    return out


def emit_decision_edn(decisions: list[dict], signed_by: str) -> str:
    L = [";; chokepoint-promotion-decision.kotoba.edn — calibration_gate decision per method.",
         ";; G12 skill>0 · G7 calibrated · G9 member-signed (no-server-key) · G1 no point.",
         ";; A REFUSAL gate: never auto-promotes. Live promotion G10-gated. ADR-2606051800.",
         f";; signed-by: {signed_by or '(unsigned)'}", "", "["]
    for d in decisions:
        refusal = d["refusal"].replace('"', "'")
        L.append(
            f' {{:fc.promotion/method :{d["method"]} :fc.promotion/skill {round(d["skill"], 4)} '
            f':fc.promotion/deviation {round(d["deviation"], 4)} '
            f':fc.promotion/phase :{d["phase"]} :fc.promotion/promoted {str(d["promoted"]).lower()} '
            f':fc.promotion/server-held-key false '
            f':fc.promotion/refusal "{refusal}"}}')
    L.append("]")
    return "\n".join(L) + "\n"


def main(argv: list[str]) -> int:
    if "--scorecard" not in argv:
        sys.exit(__doc__)
    scorecard = pathlib.Path(argv[argv.index("--scorecard") + 1])
    signed_by = argv[argv.index("--signed-by") + 1] if "--signed-by" in argv else \
        os.environ.get("MITOOSHI_PROMOTE_SIGNED_BY", "")
    deviation_max = float(argv[argv.index("--deviation-max") + 1]) if "--deviation-max" in argv \
        else DEFAULT_DEVIATION_MAX

    rows = load_edn(scorecard)
    decisions = decide_from_scorecard(rows, signed_by, deviation_max)
    if "--out" in argv:
        outdir = pathlib.Path(argv[argv.index("--out") + 1])
        outdir.mkdir(parents=True, exist_ok=True)
        (outdir / "chokepoint-promotion-decision.kotoba.edn").write_text(
            emit_decision_edn(decisions, signed_by))

    print(f"mitooshi promotion decision (signed-by: {signed_by or '(unsigned)'}, "
          f"deviation-max {deviation_max}):")
    for d in decisions:
        mark = "CLEARED" if d["phase"] == "cleared" else "REFUSED"
        why = "" if d["phase"] == "cleared" else f" — {d['refusal']}"
        print(f"  {d['method']:12s} skill={d['skill']:+} deviation={d['deviation']} → {mark}{why}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
