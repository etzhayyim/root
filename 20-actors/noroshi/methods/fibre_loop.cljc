(ns noroshi.methods.fibre-loop
  "fibre_loop — noroshi (烽) fibre-optic infrastructure operational loop (R0 :representative).
  1:1 Clojure port of methods/fibre_loop.py.

  lay → align → splice composed under noroshi's gates. LAY = a CableLayPlant cross-track
  tracking loop (PID + simulate from _substrate); ALIGN = the REUSED noroshi aligner
  (active-alignment/align + IEC 60825 laser gate); SPLICE = a fusion-splice loss model.
  Pure + deterministic; dry-run, no-server-key. The __main__ demo is omitted."
  (:require [clojure.string :as str]
            [noroshi.methods._substrate :as sub]
            [noroshi.methods.active-alignment :as aa]))

(def PERMITTED-USES ["lay" "align" "splice" "inspect" "repair" "bury"])
(def SPLICE-LOSS-MAX-DB 0.10)
(def ^:private SPLICE-K-OFFSET 0.0016)
(def ^:private SPLICE-K-ANGLE 0.012)

(defn- py-round [x n]
  #?(:clj (-> (java.math.BigDecimal. (double x))
              (.setScale (int n) java.math.RoundingMode/HALF_EVEN) (.doubleValue))
     :default (let [f (Math/pow 10 n)] (/ (Math/round (* x f)) f))))

;; ── LAY: cross-track-error tracking plant ───────────────────────────────────────
;; Plant state is an atom {:k :drift :e}; measure reads :e; step integrates.
(defn cable-lay-plant
  [& {:keys [k drift e] :or {k 1.0 drift 0.05 e 0.0}}]
  (atom {"k" k "drift" drift "e" e}))

(defn plant-measure [p] (get p "e"))

(defn plant-step! [plant command dt]
  (swap! plant (fn [p] (update p "e" + (* (+ (* (get p "k") command) (get p "drift")) dt)))))

(defn lay-segment
  "Track the planned route from an initial cross-track error to ~0. Raises (assert-civilian) first."
  [route-xte0 & {:keys [use k drift kp ki cmd_limit steps dt tol]
                 :or {use "lay" k 1.0 drift 0.05 kp 3.0 ki 1.5 cmd_limit 5.0 steps 4000 dt 0.01 tol 1e-3}}]
  (sub/assert-civilian use PERMITTED-USES)
  (let [plant (cable-lay-plant :k k :drift drift :e route-xte0)
        pid (sub/make-pid :kp kp :ki ki :out_min (- cmd_limit) :out_max cmd_limit)
        res (sub/simulate plant plant-measure plant-step! pid 0.0 steps dt :tol tol)
        settling-step (get res "settling_step")
        settling-seconds (if (>= settling-step 0) (* settling-step dt) -1.0)]
    {"use" use
     "initial_xte_m" (py-round route-xte0 6)
     "final_xte_m" (get res "final_value")
     "track_converged" (get res "converged")
     "settling_seconds" (py-round settling-seconds 3)
     "max_abs_xte_m" (get res "max_abs_error")}))

;; ── SPLICE: fusion-splice loss model ────────────────────────────────────────────
(defn splice-loss-db
  "Fusion-splice insertion loss (dB) — grows with lateral core offset² and cleave-angle mismatch²."
  [lateral-offset-um cleave-angle-deg]
  (let [off (Math/abs (double lateral-offset-um))
        ang (Math/abs (double cleave-angle-deg))]
    (py-round (+ (* SPLICE-K-OFFSET off off) (* SPLICE-K-ANGLE ang ang)) 6)))

(defn splice
  "Evaluate a single fusion splice against the acceptance threshold (default fusion ≤0.10 dB)."
  [lateral-offset-um cleave-angle-deg & {:keys [threshold_db] :or {threshold_db SPLICE-LOSS-MAX-DB}}]
  (let [loss (splice-loss-db lateral-offset-um cleave-angle-deg)]
    {"lateral_offset_um" (py-round (Math/abs (double lateral-offset-um)) 6)
     "cleave_angle_deg" (py-round (Math/abs (double cleave-angle-deg)) 6)
     "loss_db" loss
     "threshold_db" threshold_db
     "passed" (<= loss threshold_db)}))

;; ── COMPOSE: lay → align → splice ───────────────────────────────────────────────
(defn lay-align-splice
  "Run the full fibre-segment loop end to end under noroshi's gates (dry-run, R0)."
  [route-xte0 member-sig witness-sigs
   & {:keys [use server_sig coupler laser splice_offset_um splice_cleave_angle_deg splice_threshold_db lay_kwargs]
      :or {use "lay" server_sig "" coupler nil laser nil
           splice_offset_um 0.4 splice_cleave_angle_deg 0.3 splice_threshold_db SPLICE-LOSS-MAX-DB lay_kwargs {}}}]
  (sub/assert-civilian use PERMITTED-USES)
  (sub/require-member-signature member-sig server_sig)
  (let [coupler (or coupler (aa/coupler-model))
        laser (or laser (aa/laser-spec :use "alignment"))
        lay (apply lay-segment route-xte0 :use use (mapcat identity lay_kwargs))
        alignment (aa/align coupler laser)
        sp (splice splice_offset_um splice_cleave_angle_deg :threshold_db splice_threshold_db)
        wq (sub/witness-quorum-ok witness-sigs)
        overall-ok (and (get lay "track_converged")
                        (get alignment "converged")
                        (get sp "passed")
                        (get wq "ok"))]
    {"use" use
     "track_converged" (get lay "track_converged")
     "final_xte_m" (get lay "final_xte_m")
     "lay_settling_seconds" (get lay "settling_seconds")
     "coupling_loss_db" (get alignment "loss_db")
     "align_converged" (get alignment "converged")
     "splice_loss_db" (get sp "loss_db")
     "splice_passed" (get sp "passed")
     "witness_ok" (get wq "ok")
     "overall_ok" overall-ok
     "server_held_key" false
     "dry_run" true
     "representative" true}))

(defn to-datoms
  "Project a fibre-segment result into kotoba EAVT-shaped datoms (G9)."
  [result segment-id]
  {":fibre.segment/id" segment-id
   ":fibre.segment/use" (get result "use")
   ":fibre.segment/track-converged" (get result "track_converged")
   ":fibre.segment/final-xte-m" (get result "final_xte_m")
   ":fibre.segment/lay-settling-seconds" (get result "lay_settling_seconds")
   ":fibre.segment/coupling-loss-db" (get result "coupling_loss_db")
   ":fibre.segment/align-converged" (get result "align_converged")
   ":fibre.segment/splice-loss-db" (get result "splice_loss_db")
   ":fibre.segment/splice-passed" (get result "splice_passed")
   ":fibre.segment/witness-ok" (get result "witness_ok")
   ":fibre.segment/overall-ok" (get result "overall_ok")
   ":fibre.segment/server-held-key" (get result "server_held_key")
   ":fibre.segment/dry-run" (get result "dry_run")
   ":fibre.segment/representative" (get result "representative")})

(defn report
  "Render the fibre-loop face out/ artifact (honest R0 framing for the governance test)."
  []
  (let [lay (lay-segment 2.0)
        sp (splice 0.4 0.3)
        seg (lay-align-splice 2.0 "m:ed25519:demo" ["did:web:robot-a" "did:web:robot-b"])]
    (str/join "\n"
              ["# noroshi 烽 — fibre-optic infrastructure loop (lay → align → splice)"
               ""
               "## lay (cross-track route tracking)"
               (str "- initial cross-track error : " (get lay "initial_xte_m") " m")
               (str "- final cross-track error   : " (get lay "final_xte_m") " m  "
                    "(" (if (get lay "track_converged") "converged" "not-converged") " "
                    "in " (get lay "settling_seconds") "s)")
               ""
               "## align (reused Hooke-Jeeves aligner + IEC 60825 laser gate)"
               (str "- coupling insertion loss   : " (get seg "coupling_loss_db") " dB  "
                    "(" (if (get seg "align_converged") "converged" "not-converged") ")")
               ""
               "## splice (fusion-splice acceptance)"
               (str "- splice loss               : " (get sp "loss_db") " dB  "
                    "(threshold " SPLICE-LOSS-MAX-DB " dB → " (if (get sp "passed") "PASS" "FAIL") ")")
               ""
               (str "## segment overall : " (if (get seg "overall_ok") "OK" "NOT-OK") "  "
                    "(serverHeldKey=" (get seg "server_held_key") ", dryRun=" (get seg "dry_run") ")")
               ""
               (str "> R0 simulation only — no robot, no live laser, no live cable plow, no live actuation (G7/G8). "
                    "A live cable-laying fleet displaces fibre crews ⇒ G2-coupled to the Displacement Dividend "
                    "(ADR-2606032130). :representative — arithmetic + the reused aligner, no measured device (G10).")])))
