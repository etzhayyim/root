;; test_tax_assess.clj — matsurigoto tax-assess conformance + byte-equivalent parity with
;; tax_assess.py against the published JP 速算表. Run via `bb test:matsurigoto`. ADR-2606142300.
(ns matsurigoto.methods.modules.test-tax-assess
  (:require [clojure.test :refer [deftest is testing run-tests]]
            [matsurigoto.methods.modules.tax-assess :as ta]))

(def ^:private jp (get-in ta/embedded-rate-tables ["JPN.income" :brackets]))

(deftest jp-quick-calc-table-parity
  (testing "JP 速算表 reference liabilities reproduced exactly (golden from tax_assess.py)"
    (is (== 0.0       (:liability (ta/assess-income-tax 0 jp))))
    (is (== 97500.0   (:liability (ta/assess-income-tax 1950000 jp))))
    (is (== 572500.0  (:liability (ta/assess-income-tax 5000000 jp))))
    (is (== 1434000.0 (:liability (ta/assess-income-tax 9000000 jp))))
    (is (== 5204000.0 (:liability (ta/assess-income-tax 20000000 jp))))
    (is (== 17704000.0 (:liability (ta/assess-income-tax 50000000 jp))))))

(deftest effective-rate-half-even
  (testing "effective rate (round 6, half-to-even) matches Python golden"
    (is (== 0.0      (:effective-rate (ta/assess-income-tax 0 jp))))
    (is (== 0.05     (:effective-rate (ta/assess-income-tax 1950000 jp))))
    (is (== 0.1145   (:effective-rate (ta/assess-income-tax 5000000 jp))))
    (is (== 0.159333 (:effective-rate (ta/assess-income-tax 9000000 jp))))
    (is (== 0.2602   (:effective-rate (ta/assess-income-tax 20000000 jp))))
    (is (== 0.35408  (:effective-rate (ta/assess-income-tax 50000000 jp))))))

(deftest bracket-breakdown
  (testing "per-bracket breakdown for taxable 5,000,000 (golden)"
    (let [bs (:brackets (ta/assess-income-tax 5000000 jp))]
      (is (= 3 (count bs)))
      (is (= [97500.0 135000.0 340000.0] (mapv #(double (:tax-in-bracket %)) bs)))
      (is (= [0 1950000 3300000] (mapv :lower bs)))
      (is (= [0.05 0.10 0.20] (mapv :rate bs))))))

(deftest assess-from-return-and-receipt
  (testing "gross−deductions → taxable, with G1 unsigned receipt"
    (let [r (ta/assess-from-return 6000000 1000000 "JPN.income")]
      (is (== 572500.0 (:liability r)))
      (is (= "JPY" (:currency r)))
      (is (= "JPN.income" (:rate-table r)))
      (let [rc (:receipt r)]
        (is (nil? (:proof rc)))                          ; G1 — signs nothing
        (is (false? (:server-held-authority rc)))         ; G1
        (is (= "assessed-unsigned" (:status rc)))
        (is (== 572500.0 (:assessed-amount rc)))))))

(deftest vat-net-and-refund
  (testing "net VAT = output − input; negative → refund (G1 unsigned receipt)"
    (let [due (ta/assess-vat 500.50 300.25 "JPY")
          ref (ta/assess-vat 300.0 500.0 "JPY")]
      (is (== 200.25 (:net-vat-due due)))
      (is (== 0.0 (:refund-due due)))
      (is (== 0.0 (:net-vat-due ref)))
      (is (== 200.0 (:refund-due ref)))
      (is (false? (:server-held-authority (:receipt due)))))))

(deftest localization-rate-tables
  (testing "load-rate-tables! merges data/rates/*.edn (universal algorithm, localized param)"
    (ta/load-rate-tables!)
    (is (contains? @ta/rate-tables "USA.income"))
    (is (= "USD" (get-in @ta/rate-tables ["USA.income" :currency])))
    (is (>= (count @ta/rate-tables) 7))                  ; JPN+FLAT20 embedded + ≥5 jurisdictions
    (testing "USA federal single-filer brackets assess (localization generality)"
      (is (== 0.0 (:liability (ta/assess-income-tax 0 (get-in @ta/rate-tables ["USA.income" :brackets]))))))))

(deftest discipline-and-guards
  (testing "input guards + G1 live-filing gate"
    (is (thrown? Exception (ta/assess-income-tax -1 jp)))     ; negative income
    (is (thrown? Exception (ta/assess-income-tax 1000 [])))   ; empty brackets
    (is (thrown? Exception (ta/assess-from-return 1 0 "NOPE.income")))  ; unknown table
    (is (thrown? Exception (ta/solve)))                       ; live filing Council+operator gated
    (is (false? ta/server-held-authority))))                  ; G1

(when (= *file* (System/getProperty "babashka.file"))
  (let [{:keys [fail error]} (run-tests 'matsurigoto.methods.modules.test-tax-assess)]
    (System/exit (if (pos? (+ fail error)) 1 0))))
