#!/usr/bin/env bb
;; Cross-process CID-determinism guard for the kabuto kotoba commit-DAG.
(ns kabuto.methods.test-kotoba-cid
  "test_kotoba_cid.clj — kabuto content-addressing reproducibility (ADR-2605312345 / 2606022000).

  Deepens the determinism leg the autorun test left implicit: the in-process verify-chain
  proves a single run is self-consistent, but ONLY a pinned literal tx-cid proves the sha256
  over the canonical (pr-str) form is REPRODUCIBLE ACROSS PROCESSES — recomputed in whatever
  future bb/JVM runs this test, on any machine in CI. If hashing or canonicalization ever
  became process-dependent (e.g. set-iteration order leaking into the canonical form), these
  pinned assertions fail. Uses a FIXED datom vector (independent of the seed file, which a
  sibling agent may edit) so the pins are stable.

  Run:  bb --classpath 20-actors 20-actors/kabuto/methods/test_kotoba_cid.clj"
  (:require [kabuto.methods.kotoba :as k]
            [clojure.java.io :as io]
            [clojure.test :refer [deftest is run-tests]]))

;; A fixed, seed-independent datom set — ground + a derived :supply/* signal.
(def ^:private fixed-datoms
  [[:db/add "org.corp.jp.7203" :company/name "Toyota"]
   [:db/add "org.corp.jp.7203" :company/sector :automotive]
   [:db/add "supply-bloc-:apac" :supply/bloc-load 12.34]
   [:db/add "supply-bloc-:apac" :supply/derived true]])

;; ── pinned literals (captured 2026-06-16; the cross-process anchor) ──
(def ^:private empty-cid "b752d9f3cc07ff707113bea25a08516b36f76bed8a6ff3bc0c91b45a4924e6b14")
(def ^:private fixed-cid "b864486dd262495768ea108f9026d0e6021fe13ad19ca094bbeb2195e21a501da")
(def ^:private with-prev-cid "b083cfc26c5860f84269fbd193d1961d6b827f2e80df5dac8f3163279f8749ff4")

(deftest empty-tx-cid-is-pinned
  (is (= empty-cid (k/tx-cid [])))
  (is (= empty-cid (k/tx-cid [] ""))))

(deftest fixed-datoms-cid-is-pinned
  ;; the heart: a known datom vector hashes to a known CID, in any process.
  (is (= fixed-cid (k/tx-cid (k/canonical-order fixed-datoms)))))

(deftest prev-pointer-changes-cid-and-is-pinned
  ;; threading a parent CID is part of the canonical form → distinct, reproducible CID.
  (is (= with-prev-cid (k/tx-cid (k/canonical-order fixed-datoms) "bDEADBEEF")))
  (is (not= fixed-cid with-prev-cid)))

(deftest canonical-order-makes-iteration-order-irrelevant
  ;; the documented invariant: any permutation of the same datoms → identical CID.
  (let [perms [fixed-datoms
               (vec (reverse fixed-datoms))
               (vec (shuffle fixed-datoms))
               (vec (sort-by hash fixed-datoms))]]
    (is (apply = (map #(k/tx-cid (k/canonical-order %)) perms)))
    (is (= fixed-cid (k/tx-cid (k/canonical-order (vec (reverse fixed-datoms))))))))

(deftest canonical-order-is-idempotent
  (let [once (k/canonical-order fixed-datoms)]
    (is (= once (k/canonical-order once)))))

(deftest make-tx-threads-the-pinned-cid
  (let [tx (k/make-tx (k/canonical-order fixed-datoms) :tx-id 1 :as-of "2026-06-16" :prev-cid "")]
    (is (= fixed-cid (:tx/cid tx)))
    (is (= 4 (:tx/count tx)))
    (is (= "" (:tx/prev tx)))))

(deftest append-read-verify-roundtrip-on-temp-log
  ;; full commit-DAG: two txs, prev threaded, chain verifies, head = last cid. Temp file,
  ;; never touches tracked data.
  (let [tmp (java.io.File/createTempFile "kabuto-cid-" ".kotoba.edn")
        path (.getAbsolutePath tmp)]
    (try
      (.delete tmp)
      (let [d1 (k/canonical-order fixed-datoms)
            tx1 (k/make-tx d1 :tx-id 1 :as-of "2026-06-16" :prev-cid "")
            _ (k/append-tx tx1 path)
            head1 (k/head-cid path)
            d2 (k/canonical-order [[:db/add "org.corp.de.bmw" :company/name "BMW"]])
            tx2 (k/make-tx d2 :tx-id 2 :as-of "2026-06-16" :prev-cid head1)
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
  (let [{:keys [fail error]} (run-tests 'kabuto.methods.test-kotoba-cid)]
    (System/exit (if (zero? (+ fail error)) 0 1))))
