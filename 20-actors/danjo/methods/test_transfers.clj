;; test_transfers.clj — 国→地方 財政移転 (地方交付税 法定率繰入), per-yen traceable.
;; Run: bb test_transfers.clj   (or: clojure -M test_transfers.clj)   from methods/.
(ns root.danjo.methods.test-transfers
  (:require [clojure.string :as str]))

(load-file "transfers.clj")
(alias 'tr 'root.danjo.methods.transfers)
(alias 't  'root.danjo.methods.taxes)

(def checks (atom 0)) (def fails (atom 0))
(defn check [l p] (swap! checks inc) (if p (println "  ok  " l) (do (swap! fails inc) (println "  FAIL" l))))

(let [tax-reg (t/load-taxes "../data/jp-national-taxes.edn")
      reg     (tr/load-transfers "../data/jp-fiscal-transfers.edn")
      c       (tr/compute reg tax-reg)
      r       (tr/report c)]

  ;; ── registry + exact (1円) law-rate math ──
  (check "5 法定率 allocations" (= 5 (count (:allocations reg))))
  (check "所得税(源泉) 33.1% = 14.5兆 × 3310/10000 exact"
         (= 4799500000000 (->> (:allocations c) (filter #(= :income-withholding (:from-tax %))) first :amount-jpy)))
  (check "all allocation amounts are exact integers (no float)"
         (every? integer? (map :amount-jpy (:allocations c))))
  (check "total 法定率繰入 ≈ 16-17兆 (地方交付税原資)"
         (< 16000000000000 (:total-inflow-jpy r) 18000000000000))

  ;; ── reconciliation: inflow = distributed (closed 交付税特会 boundary, residual 0) ──
  (check "inflow = distributed (residual 0)" (zero? (:residual r)))
  (check "report flags per-yen-traceable" (true? (:per-yen-traceable? r)))

  ;; ── honesty: the PORTION is traceable, the tax overall stays fungible ──
  (check "honest note: tax-overall fungibility NOT flipped"
         (str/includes? (:note r) "覆らない"))
  ;; cross-check: the underlying 源泉所得税 trace is STILL non-traceable in revenue_ledger
  (let [seed (root.danjo.methods.revenue-ledger/load-seed "../data/gov-revenue-seed.jp.edn")
        w (root.danjo.methods.revenue-ledger/trace seed :withholding-income 2024)]
    (check "源泉所得税 overall STILL non-traceable (portion-honesty holds)" (false? (:traceable? w))))

  ;; ── EAVT datoms ──
  (let [ds (tr/transfer-datoms c)]
    (check "transfer datoms all :db/add" (every? #(= :db/add (first %)) ds))
    (check "交付税特会 declared earmarked"
           (some #(and (= :gov.account/earmark? (nth % 2)) (true? (nth % 3))) ds))
    (check "allocations carry :gov.transfer/rate-bp"
           (some #(= :gov.transfer/rate-bp (nth % 2)) ds))
    (check "allocations carry :gov.transfer/per-yen? true"
           (some #(and (= :gov.transfer/per-yen? (nth % 2)) (true? (nth % 3))) ds))
    (check "distributions carry :gov.alloc/ to 地方団体"
           (some #(= :gov.alloc/to (nth % 2)) ds))
    (check "datoms persist + bridge cleanly (run-cycle! :extra-datoms)"
           (let [log (str (System/getProperty "java.io.tmpdir") "/danjo-tr-" (rand-int 1000000) ".kotoba.edn")]
             (when (.exists (clojure.java.io/file log)) (.delete (clojure.java.io/file log)))
             (let [seed (root.danjo.methods.revenue-ledger/load-seed "../data/gov-revenue-seed.jp.edn")
                   res (root.danjo.methods.revenue-ledger/run-cycle!
                        {:seed seed :log-path log :as-of 1 :extra-datoms ds})
                   ok (:ok (root.danjo.methods.revenue-ledger/verify-chain log))]
               (.delete (clojure.java.io/file log))
               (and (pos? (:datom-count res)) ok))))))

(println (format "── transfers: %d checks, %d failures ──" @checks @fails))
(when (pos? @fails) (System/exit 1))
