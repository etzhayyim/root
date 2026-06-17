#!/usr/bin/env bb
;; Cross-actor commit-DAG canonical-form invariant for the food/logistics kotoba emitters.
(ns canonical-form-invariant
  "canonical_form_invariant.clj — the substrate-level content-addressing topology of the
  food/logistics kotoba commit-DAG emitters (ADR-2605312345 / 2606152000).

  Discovered while completing the determinism sweep: the six commit-DAG emitters do NOT all
  share one content-addressing scheme — they fall into TWO canonical-form families:

    Family A — Clojure  {:datoms <pr-str> :prev <pr-str>}   → empty-tx cid b752d9f3…
               kabuto · watatsuna · watari · kanjo
    Family B — JSON     {\"datoms\":[…],\"prev\":…}            → empty-tx cid b2fc787b…
               kakaku · meyasu   (the same JSON form uchiwake's kotoba.cljc uses)

  Within a family every emitter hashes byte-identically (one scheme, no per-actor drift);
  the families are DISTINCT (a tx hashes differently across families). This test PINS that
  topology so a refactor that accidentally diverges an emitter from its family — or migrates an
  actor to the wrong family, or a future canonical-form UNIFICATION — is caught structurally
  rather than silently changing CIDs. (Unifying the two families onto one scheme is a separate,
  CID-breaking change for a future ADR; this test documents + guards the current reality.)

  Run:  bb --classpath 20-actors 70-tools/scripts/clj-test-sweep/canonical_form_invariant.clj"
  (:require [kabuto.methods.kotoba :as kab]
            [watatsuna.methods.kotoba :as wat]
            [watari.methods.kotoba :as wri]
            [kanjo.methods.kotoba :as knj]
            [kakaku.py.kotoba :as kak]
            [meyasu.py.kotoba :as mey]
            [clojure.test :refer [deftest is run-tests]]))

;; ── pinned anchors (captured 2026-06-17) ──
(def ^:private family-a-empty "b752d9f3cc07ff707113bea25a08516b36f76bed8a6ff3bc0c91b45a4924e6b14")
(def ^:private family-b-empty "b2fc787b426127d7002522f570fd7ecc7576f34c65385163053d35e20c9b3ff76")
(def ^:private family-b-fixed "b48c66036a4c5bab8cd3c04c58bd2f166252fa245fc56a208ed2981e0467cf167")

(def ^:private family-a [kab/tx-cid wat/tx-cid wri/tx-cid knj/tx-cid])
(def ^:private family-b [kak/tx-cid mey/tx-cid])

(deftest family-a-shares-one-canonical-form
  ;; kabuto/watatsuna/watari/kanjo: the Clojure {:datoms :prev} pr-str form.
  (doseq [tx-cid family-a]
    (is (= family-a-empty (tx-cid [])) "Family-A empty-tx cid")))

(deftest family-b-shares-one-canonical-form
  ;; kakaku/meyasu: the JSON {\"datoms\":…,\"prev\":…} form.
  (doseq [tx-cid family-b]
    (is (= family-b-empty (tx-cid [])) "Family-B empty-tx cid"))
  ;; same scheme on a NON-empty datom set (not just a coincidental empty hash)
  (let [ds [[":db/add" "e1" ":x/v" 1] [":db/add" "e1" ":x/w" "two"]]]
    (doseq [tx-cid family-b]
      (is (= family-b-fixed (tx-cid ds "bPREV")) "Family-B fixed-datom cid"))))

(deftest the-two-families-are-distinct
  ;; the substrate currently has TWO commit-DAG content-addressing schemes; a tx hashes
  ;; differently across families. (Pins the split so a silent unification/divergence is caught.)
  (is (not= family-a-empty family-b-empty))
  (is (not= ((first family-a) []) ((first family-b) []))))

(deftest every-emitter-is-cross-process-pure
  ;; recomputed here = recomputed in any process: tx-cid is a pure fn of its args.
  (doseq [tx-cid (concat family-a family-b)]
    (is (= (tx-cid []) (tx-cid [])))
    (is (re-matches #"b[0-9a-f]{64}" (tx-cid [])))))

(when (= *file* (System/getProperty "babashka.file"))
  (let [{:keys [fail error]} (run-tests 'canonical-form-invariant)]
    (System/exit (if (zero? (+ fail error)) 0 1))))
