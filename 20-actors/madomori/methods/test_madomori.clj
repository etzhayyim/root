;; madomori 窓守 — test suite (clojure.test, babashka-runnable).
;; Run: bb --classpath 20-actors 20-actors/madomori/methods/test_madomori.clj
;; Per ADR-2606142020 (madomori R0).
(ns madomori.methods.test-madomori
  (:require [clojure.test :refer [deftest is testing run-tests]]
            [clojure.edn :as edn]
            [madomori.methods.facade-path :as fp]
            [madomori.methods.wind-envelope :as we]
            [madomori.methods.adhesion :as ad]
            [madomori.methods.analyze :as az]
            [madomori.methods.datom-emit :as de]))

;; ── facade_path ──────────────────────────────────────────────────────────────
(deftest boustrophedon-visits-every-pane-once
  (testing "S-shape coverage visits every pane exactly once"
    (let [path (fp/boustrophedon 3 4)
          cov (fp/coverage path 3 4)]
      (is (= 12 (count path)))
      (is (:complete? cov))
      (is (not (:duplicate? cov)))
      (is (empty? (:missing cov))))))

(deftest boustrophedon-alternates-direction
  (testing "row 0 left→right, row 1 right→left (minimal-turn sweep)"
    (let [path (fp/boustrophedon 2 3)]
      (is (= [[0 0] [0 1] [0 2] [1 2] [1 1] [1 0]] path)))))

(deftest boustrophedon-rejects-negative
  (is (thrown? clojure.lang.ExceptionInfo (fp/boustrophedon -1 4))))

(deftest path-length-and-budget-scale
  (testing "longer grids cost more path; budget scales per-pane (G2)"
    (let [p1 (fp/boustrophedon 2 2)
          p2 (fp/boustrophedon 4 4)]
      (is (< (fp/path-length-m p1 4.0 3.0) (fp/path-length-m p2 4.0 3.0)))
      (let [b (fp/consumable-budget 16 0.25 4.0)]
        (is (= 16 (:panes b)))
        (is (= 4.0 (:water-l b)))
        (is (= 64.0 (:agent-ml b)))))))

(deftest coverage-detects-missing-and-duplicate
  (testing "an incomplete or double-pass path is not complete"
    (is (not (:complete? (fp/coverage [[0 0] [0 1]] 2 2))))         ; missing
    (is (not (:complete? (fp/coverage [[0 0] [0 0] [0 1] [1 0] [1 1]] 2 2)))))) ; dup

;; ── wind_envelope (★ G5) ─────────────────────────────────────────────────────
(deftest sway-grows-with-wind-and-rope
  (testing "sway amplitude grows with wind speed and rope length"
    (is (< (we/sway-amplitude-m 50.0 14.0 4.0)
           (we/sway-amplitude-m 50.0 14.0 8.0)))      ; more wind
    (is (< (we/sway-amplitude-m 25.0 14.0 6.0)
           (we/sway-amplitude-m 80.0 14.0 6.0)))      ; more rope
    (is (thrown? clojure.lang.ExceptionInfo (we/sway-amplitude-m 50.0 0.0 4.0)))))  ; bad mass

(deftest wind-work-stop-raises-above-threshold
  (testing "★ G5 — work-permitted? RAISES at/above the wind work-stop threshold"
    (let [two [{:independent true} {:independent true}]]
      (is (true? (we/work-permitted? {:speed-mps 6.0 :gust-mps 8.0 :stop-threshold-mps 10.0} two)))
      (is (thrown? clojure.lang.ExceptionInfo
                   (we/work-permitted? {:speed-mps 11.0 :stop-threshold-mps 10.0} two)))
      ;; a gust alone above threshold also stops work
      (is (thrown? clojure.lang.ExceptionInfo
                   (we/work-permitted? {:speed-mps 6.0 :gust-mps 12.0 :stop-threshold-mps 10.0} two))))))

(deftest single-anchor-plan-raises
  (testing "★ G5 — a descent needs ≥2 independent anchors; single-anchor RAISES"
    (is (not (we/fall-arrest-redundant? [{:independent true}])))
    (is (we/fall-arrest-redundant? [{:independent true} {:independent true}]))
    ;; a non-independent second anchor does not count
    (is (not (we/fall-arrest-redundant? [{:independent true} {:independent false}])))
    (is (thrown? clojure.lang.ExceptionInfo
                 (we/work-permitted? {:speed-mps 3.0 :stop-threshold-mps 10.0}
                                     [{:independent true}])))))

;; ── adhesion (★ G7) ──────────────────────────────────────────────────────────
(deftest adhesion-fos-by-surface
  (testing "glass seals better than stone → higher factor-of-safety"
    (is (> (ad/factor-of-safety 900.0 :glass 14.0)
           (ad/factor-of-safety 900.0 :stone 14.0)))
    (is (thrown? clojure.lang.ExceptionInfo (ad/effective-adhesion-n 900.0 :unknown)))))

(deftest adhesion-safe-raises-below-margin
  (testing "★ G7 — adhesion-safe? RAISES when FoS is below the required factor"
    (is (true? (ad/adhesion-safe? {:suction-force-n 900.0 :surface :glass
                                   :mass-kg 14.0 :required-fos 2.5})))
    ;; porous stone (efficiency 0.45) can't make the margin at this load → RAISE
    (is (thrown? clojure.lang.ExceptionInfo
                 (ad/adhesion-safe? {:suction-force-n 900.0 :surface :stone
                                     :mass-kg 20.0 :required-fos 2.5})))
    ;; too heavy on glass → RAISE
    (is (thrown? clojure.lang.ExceptionInfo
                 (ad/adhesion-safe? {:suction-force-n 900.0 :surface :glass
                                     :mass-kg 60.0 :required-fos 2.5})))))

;; ── G3 privacy-by-construction (structural) ──────────────────────────────────
(def seed (az/load-seed "20-actors/madomori/data/facade.edn"))

(deftest imagery-is-on-device-only-and-no-recognition
  (testing "★ G3 — imagery never leaves the device; no person/interior recognition"
    (let [img (get-in seed [:robot :imagery])]
      (is (true? (:on-device-only img)))
      (is (= :pane-edge-only (:recognition img)))
      ;; the data model cannot express off-device imagery or biometric/interior recognition
      (is (not (contains? img :off-device)))
      (is (not (contains? img :cloud)))
      (is (not= :person (:recognition img)))
      (is (not= :interior (:recognition img)))
      (is (not= :biometric (:recognition img))))
    (testing "the emitted Datom log carries only the on-device imagery flag"
      (let [out (de/emit seed (az/run seed) 1)]
        (is (re-find #":mado\.robot/imagery-on-device true" out))
        (is (nil? (re-find #"(?i)off-device|cloud|biometric|interior" out)))))))

;; ── analyze + datom_emit (end-to-end over the seed) ──────────────────────────
(deftest analyze-end-to-end
  (let [res (az/run seed)]
    (testing "coverage is complete over the full pane grid"
      (is (:complete? (get-in res [:coverage :coverage])))
      (is (= (* (get-in res [:face :rows]) (get-in res [:face :cols]))
             (get-in res [:coverage :coverage :total])))
      (is (pos? (get-in res [:coverage :length-m]))))
    (testing "safety envelope + adhesion present; reference seed is a GO"
      (is (contains? (:envelope res) :permitted?))
      (is (:fall-arrest-redundant? (:envelope res)))          ; 2 independent anchors
      (is (:permitted? (:envelope res)))                       ; wind 6 m/s < 10
      (is (:safe? (:adhesion res)))                            ; glass FoS ≥ 2.5
      (is (true? (:go? res))))))

(deftest analyze-stops-on-high-wind
  (testing "★ G5 — a high-wind seed is NOT a GO (envelope refuses)"
    (let [windy (assoc-in seed [:wind :speed-mps] 14.0)
          res (az/run windy)]
      (is (not (:permitted? (:envelope res))))
      (is (false? (:go? res))))))

(deftest datom-emit-shape
  (let [res (az/run seed)
        out (de/emit seed res 1)]
    (testing "emits ground :add datoms + transient :derived readouts"
      (is (re-find #":mado\.face/surface" out))
      (is (re-find #":mado\.robot/required-fos" out))
      (is (re-find #":en/kind :anchored-by" out))
      (is (re-find #":mado\.anchor/independent" out))
      (is (re-find #":bond/adhesion-fos" out))
      (is (re-find #":bond/go" out))
      (is (re-find #":derived\]" out))
      ;; well-formed EDN vector of datoms
      (is (vector? (clojure.edn/read-string out))))))

(let [{:keys [fail error]} (run-tests 'madomori.methods.test-madomori)]
  (System/exit (if (pos? (+ fail error)) 1 0)))
