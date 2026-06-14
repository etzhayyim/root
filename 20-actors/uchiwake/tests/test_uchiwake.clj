#!/usr/bin/env bb
;; Working Clojure port of tests/test_uchiwake.py (the stdlib invariant suite).
(ns uchiwake.tests.test-uchiwake
  "uchiwake 内訳 — invariant + correctness tests for the clj port (ADR-2606081800).

  Run:  bb --classpath 20-actors 20-actors/uchiwake/tests/test_uchiwake.clj"
  (:require [uchiwake.methods.uchiwake-edn :as e]
            [uchiwake.methods.analyze :as a]
            [clojure.java.io :as io]
            [clojure.edn :as edn]
            [clojure.string :as str]
            [clojure.test :refer [deftest is run-tests]]))

(def ^:private this-file *file*)
(defn- root [] (-> this-file io/file .getAbsoluteFile .getParentFile .getParentFile))
(defn- seed [] (io/file (root) "data" "seed-products.kotoba.edn"))
(defn- schema []
  (-> (root) .getParentFile .getParentFile
      (io/file "00-contracts" "schemas" "product-bom-ontology.kotoba.edn")))

;; ── seed loads ────────────────────────────────────────────────────────────────
(deftest seed-nonempty-and-counts
  (let [g (e/classify (e/load-edn (seed)))]
    (is (seq (:products g)))
    (is (seq (:materials g)))
    (is (seq (:bom g)))
    (is (= 11 (count (:products g))))
    (is (= 26 (count (:materials g))))
    (is (= 46 (count (:bom g))))
    (is (= 3 (count (:ownership g))))))

(deftest schema-loads
  (let [s (e/load-edn (schema))]
    (is (map? s))
    (is (= "2606081800" (:schema/adr s)))))

(deftest g5-every-node-has-sourcing
  (doseq [r (filter map? (e/load-edn (seed)))]
    (let [srcing (for [[k v] r :when (str/ends-with? (name k) "sourcing")] v)]
      (is (seq srcing) (str "missing sourcing on " (:product/id r (:material/id r r))))
      (doseq [v srcing]
        (is (#{:authoritative :representative :synthesized} v))))))

;; ── GTIN ──────────────────────────────────────────────────────────────────────
(deftest gtin-normalize-pads-to-14
  (is (= "05449000000996" (e/normalize-gtin "5449000000996")))
  (is (= 14 (count (e/normalize-gtin "5449000000996")))))

(deftest gtin-real-check-digits-valid
  (is (e/gtin-check-digit-ok? "5449000000996"))   ; Coca-Cola 330ml
  (is (e/gtin-check-digit-ok? "3017620422003")))  ; Nutella 750g

(deftest gtin-bad-check-digit-rejected
  (is (not (e/gtin-check-digit-ok? "5449000000997"))))

;; ── analyze ───────────────────────────────────────────────────────────────────
(deftest analyze-emits-derived-concentration
  (let [{:keys [derived report-md]} (a/analyze (seed))]
    (is (= 36 (count derived)) "derived concentration datom count")
    (is (every? #(true? (:concentration/derived %)) derived) "all flagged :concentration/derived true")
    (let [dims (set (map :concentration/dimension derived))]
      (is (contains? dims :material))
      (is (contains? dims :process-country))
      (is (contains? dims :ultimate-parent)))
    (is (str/includes? report-md "never a target-list"))))   ; G2 framing in the report

(deftest analyze-material-shares-bounded
  (let [{:keys [derived]} (a/analyze (seed))
        mats (filter #(= :material (:concentration/dimension %)) derived)]
    (is (seq mats))
    (is (every? #(<= 0.0 (:concentration/share %) 1.0) mats))
    ;; counts are integers ≥ 1 (a derived material is depended on by ≥1 product)
    (is (every? #(>= (:concentration/count %) 1) mats))))

(deftest analyze-is-deterministic
  ;; stable secondary sort → byte-identical report across runs (no map-iteration nondeterminism)
  (is (= (:report-md (a/analyze (seed))) (:report-md (a/analyze (seed))))))

(deftest derived-edn-round-trips
  (let [{:keys [derived]} (a/analyze (seed))
        parsed (edn/read-string (a/derived->edn derived))]
    (is (vector? parsed))
    (is (= (count derived) (count parsed)))
    (is (every? :concentration/id parsed))))

(when (= *file* (System/getProperty "babashka.file"))
  (let [{:keys [fail error]} (run-tests 'uchiwake.tests.test-uchiwake)]
    (System/exit (if (zero? (+ fail error)) 0 1))))
