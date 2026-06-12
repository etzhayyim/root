;; ported from 20-actors/mitooshi/methods/promote.py (unit_refactor stage 0)
;; mitooshi 見通し — backtest scorecard → promotion decision (R1, offline).
(ns mitooshi.methods.promote
  (:require [clojure.string] [clojure.set] [clojure.edn]))

(declare cg decide-from-scorecard emit-decision-edn main)

;; TODO: port-failed unit _CG (/var/folders/px/b63lssbx5056kq_1t6pvc1f80000gn/T/tmpvosl4ktd/scratch.clj:2:13: e)
;; _CG = (pathlib.Path(__file__).resolve().parent.parent / "cells" / "calibration_gate"
;;        / "state_machine.py")
;; _spec = _ilu.spec_from_file_location("mitooshi_calibration_gate_sm", _CG)
;; _cg_mod = _ilu.module_from_spec(_spec)
;; sys.modules[_spec.name] = _cg_mod          # register so the cell's @dataclass resolves
;; DEFAULT_DEVIATION_MAX = _cg_mod.DEFAULT_DEVIATION_MAX
;; review_promotion = _cg_mod.review_promotion
(def cg nil) ;; TODO: port-failed const

;; TODO: port-failed unit decide_from_scorecard (assembled-lint error)
;; def decide_from_scorecard(rows: list[dict], signed_by: str = "",
;;                           deviation_max: float = DEFAULT_DEVIATION_MAX) -> list[dict]:
;;     """Run each scorecard method through the calibration_gate. Returns decision rows:
;;     {method, skill, deviation, phase, refusal, promoted}."""
;;     out: list[dict] = []
;;     for r in rows:
;;         if ":fc.score/method" not in r:
;;             continue
;;         method = str(r[":fc.score/method"]).lstrip(":")
;;         skill = float(r.get(":fc.score/mean-skill", 0.0) or 0.0)
;;         deviation = float(r.get(":fc.score/calibration-deviation", 0.0) or 0.0)
;;         result = review_promotion({
;;             "model_id": f"chokepoint-{method}",
;;             "skill": skill,
;;             "deviation": deviation,
;;             "deviation_max": deviation_max,
;;             "signed_by": signed_by,
;;         })
;;         cs = result["cell_state"]
;;         out.append({"method": method, "skill": skill, "deviation": deviation,
;;                     "phase": cs["phase"], "refusal": cs["refusal"],
;;                     "promoted": cs.get("payload", {}).get("promoted", False)})
;;     return out
(defn decide-from-scorecard [& _]
  (throw (ex-info "TODO: port-failed" {:from "decide_from_scorecard"})))

;; TODO: port-failed unit emit_decision_edn (/var/folders/px/b63lssbx5056kq_1t6pvc1f80000gn/T/tmp8kmv5b4i/scratch.clj:2:1: er)
;; def emit_decision_edn(decisions: list[dict], signed_by: str) -> str:
;;     L = [";; chokepoint-promotion-decision.kotoba.edn — calibration_gate decision per method.",
;;          ";; G12 skill>0 · G7 calibrated · G9 member-signed (no-server-key) · G1 no point.",
;;          ";; A REFUSAL gate: never auto-promotes. Live promotion G10-gated. ADR-2606051800.",
;;          f";; signed-by: {signed_by or '(unsigned)'}", "", "["]
;;     for d in decisions:
;;         refusal = d["refusal"].replace('"', "'")
;;         L.append(
;;             f' {{:fc.promotion/method :{d["method"]} :fc.promotion/skill {round(d["skill"], 4)} '
;;             f':fc.promotion/deviation {round(d["deviation"], 4)} '
;;             f':fc.promotion/phase :{d["phase"]} :fc.promotion/promoted {str(d["promoted"]).lower()} '
;;             f':fc.promotion/server-held-key false '
;;             f':fc.promotion/refusal "{refusal}"}}')
;;     L.append("]")
;;     return "\n".join(L) + "\n"
(defn emit-decision-edn [& _]
  (throw (ex-info "TODO: port-failed" {:from "emit_decision_edn"})))

;; TODO: port-failed unit main (/var/folders/px/b63lssbx5056kq_1t6pvc1f80000gn/T/tmpji1s6gyy/scratch.clj:9:25: e)
;; def main(argv: list[str]) -> int:
;;     if "--scorecard" not in argv:
;;         sys.exit(__doc__)
;;     scorecard = pathlib.Path(argv[argv.index("--scorecard") + 1])
;;     signed_by = argv[argv.index("--signed-by") + 1] if "--signed-by" in argv else \
;;         os.environ.get("MITOOSHI_PROMOTE_SIGNED_BY", "")
;;     deviation_max = float(argv[argv.index("--deviation-max") + 1]) if "--deviation-max" in argv \
;;         else DEFAULT_DEVIATION_MAX
;; 
;;     rows = load_edn(scorecard)
;;     decisions = decide_from_scorecard(rows, signed_by, deviation_max)
;;     if "--out" in argv:
;;         outdir = pathlib.Path(argv[argv.index("--out") + 1])
;;         outdir.mkdir(parents=True, exist_ok=True)
;;         (outdir / "chokepoint-promotion-decision.kotoba.edn").write_text(
;;             emit_decision_edn(decisions, signed_by))
;; 
;;     print(f"mitooshi promotion decision (signed-by: {signed_by or '(unsigned)'}, "
;;           f"deviation-max {deviation_max}):")
;;     for d in decisions:
;;         mark = "CLEARED" if d["phase"] == "cleared" else "REFUSED"
;;         why = "" if d["phase"] == "cleared" else f" — {d['refusal']}"
;;         print(f"  {d['method']:12s} skill={d['skill']:+} deviation={d['deviation']} → {mark}{why}")
;;     return 0
(defn main [& _]
  (throw (ex-info "TODO: port-failed" {:from "main"})))

