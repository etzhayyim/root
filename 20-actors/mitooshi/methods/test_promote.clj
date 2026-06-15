#!/usr/bin/env bb
;; Tests for mitooshi backtest→promotion decision (methods/promote.clj).
;; 1:1 port of test_promote.py — all 7 test cases, every assertion preserved.
;;
;; Run:
;;   bb --classpath 20-actors 20-actors/mitooshi/methods/test_promote.clj
;;
;; The .cljc sibling (test_promote.cljc) defines the same ns but its -main is never
;; invoked by bb (hollow false-green). This .clj file runs exactly the 7 tests and
;; confirms "Ran 7 tests" — proof the correct file loaded.
(ns mitooshi.methods.test-promote
  "Tests for mitooshi backtest→promotion decision (methods/promote.clj).
  1:1 port of methods/test_promote.py.

  The calibration_gate is a REFUSAL gate. These tests prove each gate fires on the
  scorecard: G12 (skill≤0 refused), G7 (miscalibrated refused — the real two-regime
  trail's outcome), G9 (unsigned / server-signed refused), and that a
  skilled+calibrated+member-signed model clears. The gate logic itself is the cell's
  review-promotion (single source of truth)."
  (:require [clojure.test :refer [deftest is run-tests]]
            [clojure.string :as str]
            [clojure.java.io :as io]
            [mitooshi.methods.promote :as p]))

;; PROOF this .clj loaded (not the .cljc): resolve a var present only in promote.clj.
;; If bb loaded the .cljc, this would throw and tests would not run.
(when-not (resolve 'mitooshi.methods.promote/promote-clj-loaded)
  (throw (ex-info "bb loaded promote.cljc instead of promote.clj — wrong file!" {})))

(def ^:private member "did:web:etzhayyim.com:member:alice")

;; The scorecard the Python test reads: methods/../data/persisted/...
;; *file* is the path of this test file: .../methods/test_promote.clj
(def ^:private scorecard-file
  (-> (io/file *file*)        ;; .../methods/test_promote.clj
      (.getParentFile)        ;; .../methods
      (.getParentFile)        ;; .../mitooshi
      (io/file "data" "persisted" "chokepoint-backtest-scorecard.kotoba.edn")))

(defn- rows
  "Build a minimal scorecard row vector — mirrors _rows() in test_promote.py."
  ([skill deviation] (rows skill deviation "persistence"))
  ([skill deviation method]
   [{":fc.score/method" (str ":" method)
     ":fc.score/mean-skill" skill
     ":fc.score/calibration-deviation" deviation}]))

;; ── test cases (1:1 with test_promote.py) ────────────────────────────────────

(deftest test-skilled-calibrated-signed-clears
  ;; skilled (G12 ok), calibrated (G7 ok), member-signed (G9 ok) → CLEARED
  (let [d (first (p/decide-from-scorecard (rows 0.5 0.2) {:signed-by member}))]
    (is (= "cleared" (:phase d)))
    (is (true? (:promoted d)))))

(deftest test-unskilled-refused-g12
  ;; skill ≤ 0 → G12 refusal
  (let [d (first (p/decide-from-scorecard (rows -0.1 0.2) {:signed-by member}))]
    (is (= "refused" (:phase d)))
    (is (str/includes? (:refusal d) "G12"))))

(deftest test-miscalibrated-refused-g7
  ;; skill is fine but deviation exceeds the ceiling → G7 refusal
  (let [d (first (p/decide-from-scorecard (rows 0.7 1.3) {:signed-by member}))]
    (is (= "refused" (:phase d)))
    (is (str/includes? (:refusal d) "G7"))))

(deftest test-unsigned-refused-g9-no-server-key
  ;; no signed-by → G9 refusal
  (let [d (first (p/decide-from-scorecard (rows 0.5 0.2) {:signed-by ""}))]
    (is (= "refused" (:phase d)))
    (is (str/includes? (:refusal d) "G9"))))

(deftest test-server-signature-refused-g9
  ;; signed-by starting with "server" → G9 refusal (no-server-key)
  (let [d (first (p/decide-from-scorecard (rows 0.5 0.2) {:signed-by "server:etzhayyim"}))]
    (is (= "refused" (:phase d)))
    (is (str/includes? (:refusal d) "G9"))))

(deftest test-decision-edn-records-server-held-key-false
  ;; emit-decision-edn always records serverHeldKey false (no-server-key) + promoted true
  (let [edn (p/emit-decision-edn
             (p/decide-from-scorecard (rows 0.5 0.2) {:signed-by member})
             member)]
    (is (str/includes? edn ":fc.promotion/server-held-key false"))
    (is (str/includes? edn ":fc.promotion/promoted true"))))

(deftest test-real-scorecard-is-refused-on-calibration
  ;; honest end-to-end: the real two-regime trail is SKILLED but MISCALIBRATED, so even
  ;; a member signature does NOT clear it — the gate working as designed, not a bug.
  (when (.exists scorecard-file)
    (let [rows      (p/load-edn scorecard-file)
          decisions (p/decide-from-scorecard rows {:signed-by member})]
      (is (seq decisions) "expected scorecard methods")
      (doseq [d decisions]
        (is (> (:skill d) 0))                          ;; G12 satisfied (skilled)
        (is (= "refused" (:phase d)))
        (is (str/includes? (:refusal d) "G7"))))))     ;; but miscalibrated → G7 refused

;; ── entry point ──────────────────────────────────────────────────────────────

(when (= *file* (System/getProperty "babashka.file"))
  (let [{:keys [fail error]} (clojure.test/run-tests 'mitooshi.methods.test-promote)]
    (System/exit (if (zero? (+ fail error)) 0 1))))
