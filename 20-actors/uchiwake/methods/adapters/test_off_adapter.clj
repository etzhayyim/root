#!/usr/bin/env bb
;; uchiwake 内訳 — Open Food Facts bulk-ingest adapter tests (babashka port). ADR-2606081800.
(ns uchiwake.methods.adapters.test-off-adapter
  (:require [uchiwake.methods.adapters.openfoodfacts :as off]
            [uchiwake.methods.uchiwake-edn :as ue]
            [cheshire.core :as json]
            [clojure.edn :as edn]
            [clojure.java.io :as io]
            [clojure.string :as str]
            [clojure.test :refer [deftest is are testing run-tests]]))

;; ── fixture ───────────────────────────────────────────────────────────────────
;; Resolve the sample JSON fixture the same way the Python test does:
;; tests/test_off_adapter.py sets ROOT = parent of tests/ (= actor root), then
;; SAMPLE = ROOT / "data" / "ingest" / "openfoodfacts.sample.json".
;; This file lives in methods/adapters/, so actor-root = ../../../../ from here.
(def ^:private this-file *file*)

(defn- actor-root []
  (-> this-file io/file .getAbsoluteFile
      .getParentFile   ;; adapters/
      .getParentFile   ;; methods/
      .getParentFile)) ;; uchiwake/

(def ^:private sample-path
  (delay (io/file (actor-root) "data" "ingest" "openfoodfacts.sample.json")))

(def ^:private fixture
  "Load + normalise the sample file once."
  (delay
   (let [records (json/parse-string (slurp @sample-path))]
     (off/normalize-dataset records))))

(defn- datoms [] (first @fixture))
(defn- stats  [] (second @fixture))

;; ── tests ─────────────────────────────────────────────────────────────────────

(deftest test-bad-gtin-record-skipped
  ;; 4 records in the fixture; 1 has a wrong check digit → 3 admitted, 1 skipped
  (is (= 3 (get (stats) "products_ok")))
  (is (= 1 (get (stats) "skipped_bad_gtin"))))

(deftest test-products-keyed-on-normalized-gtin14
  (let [prods (filter #(contains? % ":product/id") (datoms))]
    (is (= 3 (count prods)))
    (doseq [p prods]
      (is (= 14 (count (get p ":product/gtin"))))
      (is (ue/gtin-check-digit-ok? (get p ":product/gtin")))
      (is (= ":representative" (get p ":product/sourcing"))))))

(deftest test-ingredients-become-bom-edges-with-mass
  (let [edges  (filter #(contains? % ":bom.edge/id") (datoms))
        ;; Nutella GTIN 3017620422003 → gtin.03017620422003; sugar edge
        sugar  (filter (fn [e]
                         (and (= "gtin.03017620422003" (get e ":bom.edge/parent"))
                              (= "mat.sugar"           (get e ":bom.edge/child"))))
                       edges)]
    (is (pos? (count edges)))
    (is (= 1 (count sugar)))
    (is (< (Math/abs (- 56.0 (get (first sugar) ":bom.edge/qty" 0.0))) 0.001))
    (is (= "%mass" (get (first sugar) ":bom.edge/qty-unit")))))

(deftest test-known-ingredients-map-to-canonical-materials
  (let [mat-ids (set (map #(get % ":material/id")
                          (filter #(contains? % ":material/id") (datoms))))]
    (doseq [canon ["mat.sugar" "mat.cocoa" "mat.palm-oil"
                   "mat.water" "mat.co2" "mat.milk-powder"]]
      (is (contains? mat-ids canon) (str "expected " canon " in mat-ids")))))

(deftest test-materials-deduped-across-products
  ;; sugar appears in all 3 products but should be emitted only once
  (let [mats (filter #(contains? % ":material/id") (datoms))
        ids  (map #(get % ":material/id") mats)]
    (is (= (count ids) (count (set ids))))))

(deftest test-output-is-valid-edn-loadable
  ;; to-edn emits real EDN (keywords as bare :kw, strings quoted).
  ;; clojure.edn/read-string parses it back with keyword keys.
  (let [edn-str (off/to-edn (datoms))
        ;; Strip leading comment lines before read-string (edn reader doesn't handle ; comments)
        stripped (str/join "\n" (remove #(str/starts-with? (str/trim %) ";") (str/split-lines edn-str)))
        parsed   (edn/read-string stripped)]
    (is (vector? parsed))
    (is (= 3 (count (filter #(and (map? %) (contains? % :product/id)) parsed))))))

;; ── runner ────────────────────────────────────────────────────────────────────
(when (= *file* (System/getProperty "babashka.file"))
  (let [{:keys [fail error]} (clojure.test/run-tests 'uchiwake.methods.adapters.test-off-adapter)]
    (System/exit (if (zero? (+ fail error)) 0 1))))
