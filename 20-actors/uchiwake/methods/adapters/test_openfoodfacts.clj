;; test_openfoodfacts.clj — uchiwake OFF→datom normalizer, byte-parity with openfoodfacts.py.
;; Auto-discovered by `bb test:actors` (path-matching ns). ADR-2606142300.
(ns uchiwake.methods.adapters.test-openfoodfacts
  (:require [clojure.test :refer [deftest is testing run-tests]]
            [uchiwake.methods.adapters.openfoodfacts :as off]))

(def ^:private recs
  [{"code" "3017620422003" "product_name" "Nutella" "brands" "Ferrero"
    "ingredients" [{"id" "en:sugar" "text" "Sugar" "percent_estimate" 56.3}
                   {"id" "en:palm-oil" "text" "Palm Oil" "percent_estimate" 30.0}
                   {"id" "en:hazelnut" "text" "Hazelnuts" "percent_estimate" 13.0}]}
   {"code" "3017620422004" "product_name" "BadGTIN" "brands" "X" "ingredients" []}   ; wrong check digit
   {"code" "5449000000996" "product_name" "Coca-Cola" "brands" "Coca-Cola"
    "ingredients" [{"id" "en:water" "text" "Water"} {"id" "en:sugar" "text" "Sugar" "percent_estimate" 10.6}]}])

(def ^:private result (off/normalize-dataset recs))
(def ^:private datoms (first result))
(def ^:private stats (second result))

(deftest dataset-stats
  (testing "normalize-dataset: ok/skip/material counts + GTIN validation gate (golden)"
    (is (= {:products-ok 2 :skipped-bad-gtin 1 :materials 4} stats))   ; bad-GTIN row skipped (G5)
    (is (= 11 (count datoms)))))

(deftest product-datom
  (testing "OFF product → :product datom with validated GTIN-14 + gs1-prefix (golden)"
    (let [p (first (filter #(= "gtin.03017620422003" (get % ":product/id")) datoms))]
      (is (= "03017620422003" (get p ":product/gtin")))
      (is (= ":gtin-13" (get p ":product/gtin-format")))
      (is (= "Nutella" (get p ":product/name")))
      (is (= "Ferrero" (get p ":product/brand")))
      (is (= "301" (get p ":product/gs1-prefix")))
      (is (= ":food-beverage" (get p ":product/sector")))
      (is (= ":representative" (get p ":product/sourcing"))))))   ; G5 — never :authoritative

(deftest bom-edge-and-qty
  (testing "ingredient → :bom.edge with bounded %mass qty (never a confidential recipe)"
    (let [e (first (filter #(= "bom.03017620422003.sugar" (get % ":bom.edge/id")) datoms))]
      (is (= "gtin.03017620422003" (get e ":bom.edge/parent")))
      (is (= "mat.sugar" (get e ":bom.edge/child")))
      (is (= 1 (get e ":bom.edge/tier")))
      (is (== 0.3 (get e ":bom.edge/criticality")))
      (is (== 56.3 (get e ":bom.edge/qty")))
      (is (= "%mass" (get e ":bom.edge/qty-unit")))
      (is (= ":representative" (get e ":bom.edge/sourcing"))))))

(deftest material-aliasing
  (testing "ingredient id → canonical material id (alias) or honest slug fallback"
    (is (= "mat.sugar" (first (off/material-for {"id" "en:sugar" "text" "Sugar"}))))
    (is (= "Sugar (sucrose)" (get (second (off/material-for {"id" "en:sugar"})) ":material/name")))
    (is (= "mat.cocoa" (first (off/material-for {"id" "en:fat-reduced-cocoa"}))))   ; alias collapse
    (is (= "mat.weird-thing" (first (off/material-for {"id" "en:weird-thing" "text" "Weird"}))))
    (is (= "mat.unknown" (first (off/material-for {}))))                            ; empty → unknown
    (is (= ":representative" (get (second (off/material-for {"id" "en:water"})) ":material/sourcing")))))

(deftest gtin-gate
  (testing "a bad/missing GTIN check digit yields NO datoms (skipped, not admitted)"
    (is (= [] (off/normalize-record {"code" "3017620422004"})))   ; wrong check digit
    (is (= [] (off/normalize-record {"code" ""})))
    (is (= [] (off/normalize-record {})))
    (is (seq (off/normalize-record {"code" "3017620422003"})))))   ; valid → admitted

(when (= *file* (System/getProperty "babashka.file"))
  (let [{:keys [fail error]} (run-tests 'uchiwake.methods.adapters.test-openfoodfacts)]
    (System/exit (if (pos? (+ fail error)) 1 0))))
