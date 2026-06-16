(ns noroshi.methods.test-fibre-loop
  "Tests for the noroshi fibre-optic loop core — lay → align → splice (ADR-2606051600).
  1:1 Clojure port of methods/test_fibre_loop.py (pytest → clojure.test).

  Reuses the existing noroshi aligner + the shared infra-robotics substrate; nothing
  re-implements Hooke-Jeeves or the laser-safety gate. SafetyError/LaserSafetyError are
  both Exceptions here, so `thrown? Exception` covers either."
  (:require [clojure.test :refer [deftest is run-tests]]
            [noroshi.methods.fibre-loop :as F]
            [noroshi.methods.active-alignment :as aa]
            [noroshi.methods._substrate :as sub]))

;; ── LAY ─────────────────────────────────────────────────────────────────────────
(deftest test-lay-converges-to-route
  (let [res (F/lay-segment 2.0)]
    (is (get res "track_converged"))
    (is (< (Math/abs (double (get res "final_xte_m"))) 1e-2))
    (is (> (get res "settling_seconds") 0))))

(deftest test-lay-rejects-drift-to-zero-steady-state
  (let [res (F/lay-segment -3.0 :drift 0.2)]
    (is (get res "track_converged"))
    (is (< (Math/abs (double (get res "final_xte_m"))) 1e-2))))

(deftest test-lay-plant-is-a-plant
  (let [p (F/cable-lay-plant :e 1.0)]
    (is (= (F/plant-measure @p) 1.0))
    (F/plant-step! p -1.0 0.1)
    (is (< (F/plant-measure @p) 1.0))))

(deftest test-lay-non-civilian-use-raises
  (is (thrown? #?(:clj Exception :cljs js/Error) (F/lay-segment 1.0 :use "weapon"))))

;; ── SPLICE ────────────────────────────────────────────────────────────────────
(deftest test-splice-loss-grows-with-offset
  (is (< (F/splice-loss-db 0.0 0.0) (F/splice-loss-db 2.0 0.0) (F/splice-loss-db 5.0 0.0))))

(deftest test-splice-loss-grows-with-cleave-angle
  (is (< (F/splice-loss-db 0.0 0.0) (F/splice-loss-db 0.0 1.0) (F/splice-loss-db 0.0 3.0))))

(deftest test-splice-loss-is-quadratic-in-offset
  (let [l1 (F/splice-loss-db 1.0 0.0) l2 (F/splice-loss-db 2.0 0.0)]
    (is (<= (Math/abs (- l2 (* 4.0 l1))) (* 1e-6 (max (Math/abs l2) (Math/abs (* 4.0 l1)) 1e-30))))))

(deftest test-splice-loss-uses-magnitude
  (is (= (F/splice-loss-db -2.0 -1.0) (F/splice-loss-db 2.0 1.0))))

(deftest test-splice-passes-when-well-aligned
  (let [res (F/splice 0.4 0.3)]
    (is (<= (get res "loss_db") F/SPLICE-LOSS-MAX-DB))
    (is (get res "passed"))))

(deftest test-splice-fails-when-offset-large
  (let [res (F/splice 12.0 0.0)]
    (is (> (get res "loss_db") F/SPLICE-LOSS-MAX-DB))
    (is (not (get res "passed")))))

;; ── laser-safety inherited from the REUSED aligner ──────────────────────────────
(deftest test-weapon-laser-use-cannot-be-energised-in-the-loop
  (is (thrown? #?(:clj Exception :cljs js/Error)
               (F/lay-align-splice 2.0 "m:ed25519:demo" ["did:web:robot-a" "did:web:robot-b"]
                                   :laser (aa/laser-spec :use "weapon")))))

(deftest test-hazardous-laser-without-interlock-refused-in-the-loop
  (is (thrown? #?(:clj Exception :cljs js/Error)
               (F/lay-align-splice 2.0 "m:ed25519:demo" ["did:web:robot-a" "did:web:robot-b"]
                                   :laser (aa/laser-spec :laser_class "4" :use "alignment" :enclosure_interlock false)))))

;; ── G7 no-server-key gate ───────────────────────────────────────────────────────
(deftest test-server-signature-refused
  (is (thrown? #?(:clj Exception :cljs js/Error)
               (F/lay-align-splice 2.0 "m:ed25519:demo" ["did:web:robot-a" "did:web:robot-b"]
                                   :server_sig "s:platform:sig"))))

(deftest test-missing-member-signature-refused
  (is (thrown? #?(:clj Exception :cljs js/Error)
               (F/lay-align-splice 2.0 "" ["did:web:robot-a" "did:web:robot-b"]))))

;; ── N1 civilian-use gate on the composed loop ───────────────────────────────────
(deftest test-non-civilian-use-raises-on-full-loop
  (is (thrown? #?(:clj Exception :cljs js/Error)
               (F/lay-align-splice 2.0 "m:ed25519:demo" ["did:web:robot-a" "did:web:robot-b"]
                                   :use "fire-control"))))

;; ── full happy path ─────────────────────────────────────────────────────────────
(deftest test-full-lay-align-splice-happy-path
  (let [seg (F/lay-align-splice 2.0 "m:ed25519:demo" ["did:web:robot-a" "did:web:robot-b"])]
    (is (get seg "track_converged"))
    (is (get seg "align_converged"))
    (is (get seg "splice_passed"))
    (is (get seg "witness_ok"))
    (is (= (get seg "overall_ok") true))
    (is (= (get seg "server_held_key") false))
    (is (= (get seg "dry_run") true))
    (is (= (get seg "representative") true))
    (is (> (get seg "coupling_loss_db") 0.0))))

(deftest test-overall-not-ok-when-witness-quorum-fails
  (let [seg (F/lay-align-splice 2.0 "m:ed25519:demo" ["did:web:robot-a"])]
    (is (= (get seg "witness_ok") false))
    (is (= (get seg "overall_ok") false))))

(deftest test-overall-not-ok-when-splice-fails
  (let [seg (F/lay-align-splice 2.0 "m:ed25519:demo" ["did:web:robot-a" "did:web:robot-b"]
                                :splice_offset_um 15.0)]
    (is (= (get seg "splice_passed") false))
    (is (= (get seg "overall_ok") false))))

;; ── datom projection ─────────────────────────────────────────────────────────────
(deftest test-to-datoms-carries-charter-invariants
  (let [seg (F/lay-align-splice 2.0 "m:ed25519:demo" ["did:web:robot-a" "did:web:robot-b"])
        d (F/to-datoms seg "fibre-seg-001")]
    (is (= (get d ":fibre.segment/id") "fibre-seg-001"))
    (is (= (get d ":fibre.segment/server-held-key") false))
    (is (= (get d ":fibre.segment/dry-run") true))
    (is (= (get d ":fibre.segment/representative") true))
    (is (= (get d ":fibre.segment/overall-ok") true))))

#?(:clj (defn -main [& _] (run-tests 'noroshi.methods.test-fibre-loop)))
