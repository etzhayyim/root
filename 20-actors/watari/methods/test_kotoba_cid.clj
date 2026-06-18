#!/usr/bin/env bb
;; Cross-process CID-determinism guard for the watari kotoba commit-DAG.
(ns watari.methods.test-kotoba-cid
  "test_kotoba_cid.clj — watari content-addressing reproducibility (ADR-2605312345 / 2606041827).

  Deepens the determinism leg the autorun test left implicit: only a pinned literal tx-cid
  proves the sha256-over-canonical-(pr-str) form is REPRODUCIBLE ACROSS PROCESSES — recomputed
  in whatever bb/JVM runs the test, any CI machine. Seed-independent FIXED craft/movement datom
  vector (a sibling may edit the seed). G4 no-person-tracking: the fixed vector carries only
  craft + chokepoint movement, no person fields.

  Run:  bb --classpath 20-actors 20-actors/watari/methods/test_kotoba_cid.clj"
  (:require [watari.methods.kotoba :as k]
            [clojure.java.io :as io]
            [clojure.test :refer [deftest is run-tests]]))

(def ^:private fixed-datoms
  [[:db/add "craft.imo9876543" :craft/kind :vessel]
   [:db/add "craft.imo9876543" :craft/name "MV Example"]
   [:db/add "movement.malacca" :movement/chokepoint :malacca]
   [:db/add "movement.malacca" :movement/transit-load 3.0]])

;; ── pinned literals (captured 2026-06-16) ──
(def ^:private empty-cid "b752d9f3cc07ff707113bea25a08516b36f76bed8a6ff3bc0c91b45a4924e6b14")
(def ^:private fixed-cid "be263b462e643c025285873326b4551cff881273f7d849a678cf7c91b84f96baa")
(def ^:private with-prev-cid "b5e26252e7190df4feeb8d0bc602e3453bb7a04ddb40d0f8a1a03d8f7175c0c4d")

(deftest empty-tx-cid-is-pinned
  (is (= empty-cid (k/tx-cid [])))
  (is (= empty-cid (k/tx-cid [] ""))))

(deftest empty-cid-matches-the-shared-commit-dag-canonical-form
  ;; cross-actor invariant: kabuto / watatsuna / kanjo pin the SAME empty-tx literal.
  (is (= "b752d9f3cc07ff707113bea25a08516b36f76bed8a6ff3bc0c91b45a4924e6b14" (k/tx-cid []))))

(deftest fixed-datoms-cid-is-pinned
  (is (= fixed-cid (k/tx-cid fixed-datoms))))

(deftest tx-cid-is-a-pure-fn-of-datoms-and-prev
  (is (= (k/tx-cid fixed-datoms) (k/tx-cid fixed-datoms)))
  (is (= (k/tx-cid fixed-datoms "bX") (k/tx-cid fixed-datoms "bX"))))

(deftest prev-pointer-changes-cid-and-is-pinned
  (is (= with-prev-cid (k/tx-cid fixed-datoms "bDEADBEEF")))
  (is (not= fixed-cid with-prev-cid)))

(deftest make-tx-threads-the-pinned-cid
  (let [tx (k/make-tx fixed-datoms :tx-id 1 :as-of "2026-06-16" :prev-cid "")]
    (is (= fixed-cid (:tx/cid tx)))
    (is (= 4 (:tx/count tx)))
    (is (= "" (:tx/prev tx)))))

(deftest append-read-verify-roundtrip-on-temp-log
  (let [tmp (java.io.File/createTempFile "watari-cid-" ".kotoba.edn")
        path (.getAbsolutePath tmp)]
    (try
      (.delete tmp)
      (let [tx1 (k/make-tx fixed-datoms :tx-id 1 :as-of "2026-06-16" :prev-cid "")
            _ (k/append-tx tx1 path)
            head1 (k/head-cid path)
            tx2 (k/make-tx [[:db/add "craft.icao-abc123" :craft/kind :aircraft]]
                           :tx-id 2 :as-of "2026-06-16" :prev-cid head1)
            _ (k/append-tx tx2 path)]
        (is (= fixed-cid head1))
        (is (= 2 (count (k/read-log path))))
        (let [v (k/verify-chain path)]
          (is (true? (:ok v)))
          (is (= 2 (:length v)))
          (is (= -1 (:broken-at v))))
        (is (= (:tx/cid tx2) (k/head-cid path)))
        (let [bad (str (pr-str (assoc tx1 :tx/datoms [[:db/add "x" :y "z"]])) "\n"
                       (pr-str tx2) "\n")]
          (spit path (str ";; hdr\n" bad))
          (is (false? (:ok (k/verify-chain path))))))
      (finally (.delete (io/file path))))))

(when (= *file* (System/getProperty "babashka.file"))
  (let [{:keys [fail error]} (run-tests 'watari.methods.test-kotoba-cid)]
    (System/exit (if (zero? (+ fail error)) 0 1))))
