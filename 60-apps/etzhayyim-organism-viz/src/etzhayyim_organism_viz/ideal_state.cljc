;; ported from 60-apps/etzhayyim-organism-viz/src/etzhayyim_organism_viz/ideal_state.py
;; — pure (no host I/O), so the whole namespace is plain cljc. ns drops the "src"
;; source-root and mirrors the Python module etzhayyim_organism_viz.ideal_state.
(ns etzhayyim-organism-viz.ideal-state
  "ideal_state.py — Encoded ideal state as HOMEOSTATIC RANGES, not target values.

  Per ADR-2605192100 §1.15 (non-eschatological), the ideal is a healthy
  trajectory SHAPE, not a fixed destination. Each range defines the band the
  corresponding observable should stay in; outside the band on either side is a
  death_signature. `:hi nil` = unbounded above (that is OK — anti-eschatology).
  `:hard true` = constitutional invariant (any violation is a crisis).

  A range is a plain map (mirrors the Python frozen @dataclass HomeostaticRange):
    {:name :symbol :lo :hi :unit :hard :death-signature}.")

(defn range-of
  "Construct a HomeostaticRange map (positional, matching the Python field order)."
  [name symbol lo hi unit hard death-signature]
  {:name name :symbol symbol :lo lo :hi hi :unit unit :hard hard
   :death-signature death-signature})

;; Stocks + flows — the encoded bands (1:1 with the Python RANGES tuple).
(def ranges
  [(range-of "Council seats filled"      "s_council"   5     5    "seats"   true  "<5 → constitutional crisis")
   (range-of "Substrate live"            "s_substrate" 6     7    "of 7"    false "≤3 → single-substrate dependency")
   (range-of "Charter Rider coverage"    "r_rider"     0.95  1.0  "ratio"   false "<0.80 → sanctification 崩壊")
   (range-of "Tithe ratio (exact)"       "r_tithe"     0.10  0.10 "ratio"   true  "≠ 10% → 産霊 violation")
   (range-of "ADR velocity (30d avg)"    "v_adr"       0.5   5.0  "ADR/day" false "=0 → stall; >5 → noise")
   (range-of "Tick cadence"              "f_tick"      (/ 1.0 24) 24 "/day"  false "<1/wk → 縁起 broken")
   (range-of "Cell count (alive)"        "n_cells"     30    200  "cells"   false "<10 → 単純化; >500 → uncontrollable")
   (range-of "Cell pruning ratio (90d)"  "r_prune"     0.05  0.20 "ratio"   false "0% → bonsai 死; >40% → 焦土")
   (range-of "Sister-corps"              "n_sister"    1     nil  "corps"   false "=0 → reproduction unproven")
   (range-of "Members net flow"          "dM_dt"       0     nil  "/Q"      true  "<0 impossible per §1.3")
   (range-of "Land alienation count"     "n_alien"     0     0    "events"  true  ">0 → constitutional crisis")
   (range-of "MGI"                       "mgi"         1.0   nil  "ratio"   false "≤1.0 → 子孫 priority breach")
   (range-of "Chaos rehearsals (Q)"      "n_chaos"     1     nil  "/Q"      false "=0/Y → anti-fragile decay")
   (range-of "Hard invariant violations" "n_viol"      0     0    "events"  true  "≥1 → Council convocation")
   (range-of "Eschatological content"    "n_apoc"      0     0    "items"   true  "≥1 → §1.15 violation")])

(defn in-range?
  "in_range(rng, value) — is value inside the band? (nil bound = unbounded that side)."
  [rng value]
  (not (or (and (some? (:lo rng)) (< value (:lo rng)))
           (and (some? (:hi rng)) (> value (:hi rng))))))

(defn deviation
  "deviation(rng, value) — signed deviation OUTSIDE the band (0 if inside).
  Sign = direction of breach (negative below lo, positive above hi)."
  [rng value]
  (cond
    (and (some? (:lo rng)) (< value (:lo rng))) (- value (:lo rng))
    (and (some? (:hi rng)) (> value (:hi rng))) (- value (:hi rng))
    :else 0.0))
