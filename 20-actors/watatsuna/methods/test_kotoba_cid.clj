#!/usr/bin/env bb
;; Cross-process CID-determinism guard for the watatsuna kotoba commit-DAG.
(ns watatsuna.methods.test-kotoba-cid
  "test_kotoba_cid.clj — watatsuna content-addressing reproducibility (ADR-2605312345 / 2606012600).

  Deepens the determinism leg the autorun test left implicit: the in-process verify-chain
  proves a single run self-consistent, but ONLY a pinned literal tx-cid proves the sha256 over
  the canonical (pr-str) form is REPRODUCIBLE ACROSS PROCESSES — recomputed in whatever bb/JVM
  runs the test, on any CI machine. watatsuna's `canonical` carries no internal sort (the caller
  / autorun's graph-datoms supplies a stable vector order), so the guard is: a FIXED datom
  vector hashes to a FIXED CID, in any process. Seed-independent (a sibling may edit the seed).

  Run:  bb --classpath 20-actors 20-actors/watatsuna/methods/test_kotoba_cid.clj"
  (:require [watatsuna.methods.kotoba :as k]
            [clojure.java.io :as io]
            [clojure.test :refer [deftest is run-tests]]))

;; A fixed, seed-independent cable-graph datom vector — ground + a derived :resilience/* signal.
(def ^:private fixed-datoms
  [[:db/add "cable.sea-me-we-6" :cable/name "SeaMeWe-6"]
   [:db/add "cable.sea-me-we-6" :cable/status :active]
   [:db/add "resil.malacca" :resilience/chokepoint :malacca]
   [:db/add "resil.malacca" :resilience/cable-load 940.16]])

;; ── pinned literals (captured 2026-06-16; the cross-process anchor) ──
(def ^:private empty-cid "b752d9f3cc07ff707113bea25a08516b36f76bed8a6ff3bc0c91b45a4924e6b14")
(def ^:private fixed-cid "b113696e54f585aed5c626ce5f265961ecaf544a5e795062b048e905779201425")
(def ^:private with-prev-cid "bafe8fd5366c3459c6e3f18079a163868df2cebeef9a33ea6799608cded92db77")

(deftest empty-tx-cid-is-pinned
  (is (= empty-cid (k/tx-cid [])))
  (is (= empty-cid (k/tx-cid [] ""))))

(deftest empty-cid-matches-the-shared-commit-dag-canonical-form
  ;; cross-actor invariant: every emitter shares the same {:datoms :prev} canonical form +
  ;; sha256, so an empty tx hashes identically across actors (kabuto pins the same literal).
  (is (= "b752d9f3cc07ff707113bea25a08516b36f76bed8a6ff3bc0c91b45a4924e6b14" (k/tx-cid []))))

(deftest fixed-datoms-cid-is-pinned
  (is (= fixed-cid (k/tx-cid fixed-datoms))))

(deftest tx-cid-is-a-pure-fn-of-datoms-and-prev
  ;; same input → same output, recomputed (no hidden state / no per-call entropy).
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
  (let [tmp (java.io.File/createTempFile "watatsuna-cid-" ".kotoba.edn")
        path (.getAbsolutePath tmp)]
    (try
      (.delete tmp)
      (let [tx1 (k/make-tx fixed-datoms :tx-id 1 :as-of "2026-06-16" :prev-cid "")
            _ (k/append-tx tx1 path)
            head1 (k/head-cid path)
            tx2 (k/make-tx [[:db/add "cable.tam-1" :cable/name "TAM-1"]]
                           :tx-id 2 :as-of "2026-06-16" :prev-cid head1)
            _ (k/append-tx tx2 path)]
        (is (= fixed-cid head1))
        (is (= 2 (count (k/read-log path))))
        (let [v (k/verify-chain path)]
          (is (true? (:ok v)))
          (is (= 2 (:length v)))
          (is (= -1 (:broken-at v))))
        (is (= (:tx/cid tx2) (k/head-cid path)))
        ;; tamper-evident: corrupting a datom breaks the recomputed CID
        (let [bad (str (pr-str (assoc tx1 :tx/datoms [[:db/add "x" :y "z"]])) "\n"
                       (pr-str tx2) "\n")]
          (spit path (str ";; hdr\n" bad))
          (is (false? (:ok (k/verify-chain path))))))
      (finally (.delete (io/file path))))))

(when (= *file* (System/getProperty "babashka.file"))
  (let [{:keys [fail error]} (run-tests 'watatsuna.methods.test-kotoba-cid)]
    (System/exit (if (zero? (+ fail error)) 0 1))))
