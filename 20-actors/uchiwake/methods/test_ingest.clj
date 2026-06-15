#!/usr/bin/env bb
;; Working Clojure test for methods/ingest.clj (no Python test existed; new coverage).
(ns uchiwake.methods.test-ingest
  "Tests for the uchiwake 内訳 product / GTIN / BOM ingest bridge (methods/ingest.clj).

  Guards the bridge mapping (OFF-shaped JSON → :bom.edge/* :representative), the seed-wins
  dedup merge (seed product/material ids block bridged datoms), the G7 outward gate (live
  full-universe GS1/GLEIF fetch refused without the operator gate), and the GTIN check-digit
  skip invariant (a record with a bad GS1 mod-10 check digit is dropped before ingest).

  Pins:
    - seed: 11 products, 18 parts, 26 materials, 46 BOM edges, 3 ownership edges
    - bridge (offline, openfoodfacts.sample.json): 12 new BOM-edge datoms
    - specific record: Nutella GTIN-13 3017620422003 → sugar bom.edge %mass 56.0
    - GTIN skip: 5449000000997 (bad check digit) → never appears in bridged datoms
    - G7 refusal: --live without UCHIWAKE_OPERATOR_GATE=1 → refused with G7 message

  Run:  bb --classpath 20-actors 20-actors/uchiwake/methods/test_ingest.clj"
  (:require [uchiwake.methods.ingest :as ing]
            [uchiwake.methods.uchiwake-edn :as ue]
            [clojure.string :as str]
            [clojure.test :refer [deftest is run-tests]]))

;; ── seed classification ───────────────────────────────────────────────────────

(deftest seed-classification-matches-python-baseline
  (let [[seed-rows _] (ing/bridge-offline)
        g (ue/classify seed-rows)]
    (is (= (count (:products g))  11) "11 seed products")
    (is (= (count (:parts g))     18) "18 seed parts")
    (is (= (count (:materials g)) 26) "26 seed materials")
    (is (= (count (:bom g))       46) "46 seed BOM edges")
    (is (= (count (:ownership g))  3) "3 ownership edges")))

;; ── bridge count ─────────────────────────────────────────────────────────────

(deftest bridge-offline-emits-12-new-datoms
  (let [[_ bridged] (ing/bridge-offline)]
    ;; All 3 GTIN-valid OFF products are already in the seed (product + material datoms excluded).
    ;; Only the BOM edges that are NOT already in the seed are bridged: 12.
    (is (= (count bridged) 12) "exactly 12 new BOM-edge datoms bridged offline")))

(deftest bridged-datoms-are-all-bom-edges
  (let [[_ bridged] (ing/bridge-offline)]
    ;; All 12 bridged datoms should be :bom.edge/* records
    (is (every? :bom.edge/id bridged) "every bridged datom is a :bom.edge/* record")
    (is (every? :bom.edge/parent bridged) "every bridged datom has a :bom.edge/parent")))

;; ── seed-wins dedup (G5) ─────────────────────────────────────────────────────

(deftest seed-wins-on-id-no-seed-ids-in-bridged
  (let [[seed-rows bridged] (ing/bridge-offline)
        seed-ids            (ing/seed-id-set seed-rows)
        bridged-ids         (set (keep :bom.edge/id bridged))]
    ;; None of the bridged bom.edge ids should already be in the seed
    (is (empty? (clojure.set/intersection seed-ids bridged-ids))
        "seed-wins: no bridged id duplicates a seed id")))

(deftest seed-product-ids-not-re-bridged
  (let [[seed-rows bridged] (ing/bridge-offline)
        bridged-product-ids (set (keep :product/id bridged))]
    ;; The 3 OFF products (Nutella, CocaCola, KitKat) are already in the seed
    (is (not (contains? bridged-product-ids "gtin.03017620422003")) "Nutella already in seed — not bridged")
    (is (not (contains? bridged-product-ids "gtin.05449000000996")) "Coca-Cola already in seed — not bridged")
    (is (not (contains? bridged-product-ids "gtin.07613035044289")) "KitKat already in seed — not bridged")))

;; ── specific record pinning ───────────────────────────────────────────────────

(deftest nutella-sugar-bom-edge-pinned
  ;; Nutella GTIN-13 3017620422003 → sugar ingredient %mass 56.0 is in the OFF sample
  ;; The BOM edge should be bridged since the seed's Nutella BOM may not include it.
  (let [[_ bridged] (ing/bridge-offline)
        nutella-sugar (first (filter #(= (:bom.edge/id %) "bom.03017620422003.sugar") bridged))]
    (is (some? nutella-sugar) "Nutella sugar BOM edge bridged")
    (is (= (:bom.edge/parent nutella-sugar) "gtin.03017620422003") "parent is Nutella GTIN product")
    (is (= (:bom.edge/child nutella-sugar)  "mat.sugar") "child is mat.sugar")
    (is (= (:bom.edge/qty nutella-sugar)    56.0) "sugar %mass is 56.0 (pinned vs Python)")
    (is (= (:bom.edge/qty-unit nutella-sugar) "%mass") "qty-unit is %mass")
    (is (= (:bom.edge/sourcing nutella-sugar) :representative) "sourcing :representative (G5)")))

(deftest all-bridged-bom-edges-are-representative
  ;; G5: every bridged datom carries :representative sourcing
  (let [[_ bridged] (ing/bridge-offline)]
    (is (every? #(= (:bom.edge/sourcing %) :representative) bridged)
        "all bridged BOM edges carry :representative sourcing (G5)")))

;; ── GTIN skip (bad check digit) ──────────────────────────────────────────────

(deftest bad-gtin-record-not-in-bridged
  ;; The OFF sample contains 5449000000997 (bad check digit; real Coca-Cola is 5449000000996).
  ;; It must be skipped — neither as a product nor as a set of BOM edges.
  (let [[_ bridged] (ing/bridge-offline)
        bad-gtin    "5449000000997"
        bad-gtin14  "05449000000997"]
    (is (not-any? #(= (:product/gtin %) bad-gtin14) bridged)
        "bad-GTIN product (5449000000997) is not in bridged datoms")
    (is (not-any? #(str/includes? (str (:bom.edge/id %)) bad-gtin) bridged)
        "no BOM edge for the bad-GTIN product exists in bridged datoms")))

(deftest valid-gtin-coca-cola-bom-edges-bridged
  ;; The GOOD Coca-Cola (5449000000996) should contribute BOM edges (water, sugar, co2)
  (let [[_ bridged] (ing/bridge-offline)
        coke-edges  (filter #(= (:bom.edge/parent %) "gtin.05449000000996") bridged)]
    (is (= (count coke-edges) 3) "Coca-Cola contributes 3 BOM edges (water, sugar, co2)")
    (is (some #(= (:bom.edge/child %) "mat.water") coke-edges)  "water edge present")
    (is (some #(= (:bom.edge/child %) "mat.sugar") coke-edges)  "sugar edge present")
    (is (some #(= (:bom.edge/child %) "mat.co2") coke-edges)    "co2 edge present")))

;; ── G7 outward gate ───────────────────────────────────────────────────────────

(deftest g7-live-refused-without-operator-gate
  (let [msg (ing/live-refusal ["--live"] nil)]
    (is (some? msg) "--live refused when UCHIWAKE_OPERATOR_GATE is not set")
    (is (str/includes? msg "G7")      "refusal message mentions G7")
    (is (str/includes? msg "REFUSED") "refusal message says REFUSED")
    (is (str/includes? msg "UCHIWAKE_OPERATOR_GATE") "refusal message names the env-var")))

(deftest g7-live-allowed-with-operator-gate
  (let [msg (ing/live-refusal ["--live"] "1")]
    (is (some? msg) "gate message returned when gate is set")
    (is (not (str/includes? msg "REFUSED")) "gate open — not a refusal")
    (is (str/includes? msg "G7") "gate message mentions G7")))

(deftest g7-offline-not-refused
  (is (nil? (ing/live-refusal ["--offline"] nil))
      "offline args do not trigger G7 gate")
  (is (nil? (ing/live-refusal [] nil))
      "no --live arg → no gate message"))

;; ── seed-id-set helper ────────────────────────────────────────────────────────

(deftest seed-id-set-covers-seed-products
  (let [[seed-rows _] (ing/bridge-offline)
        ids           (ing/seed-id-set seed-rows)]
    (is (>= (count ids) 100) "seed-id-set captures all 126 seed datoms")
    (is (contains? ids "gtin.03017620422003") "Nutella GTIN in seed-id-set")
    (is (contains? ids "gtin.05449000000996") "Coca-Cola GTIN in seed-id-set")
    (is (contains? ids "mat.sugar")           "mat.sugar in seed-id-set")
    (is (contains? ids "mat.cocoa")           "mat.cocoa in seed-id-set")))

(when (= *file* (System/getProperty "babashka.file"))
  (require 'clojure.set)
  (let [{:keys [fail error]} (run-tests 'uchiwake.methods.test-ingest)]
    (System/exit (if (zero? (+ fail error)) 0 1))))
