;; test_book.clj — 扶持 book: toritate ledger projection + kanae flow graph, parity with book.py.
;; Run via `bb test:fuchi`. ADR-2606142300.
(ns fuchi.methods.test-book
  (:require [clojure.test :refer [deftest is testing run-tests]]
            [fuchi.methods.book :as b]
            [fuchi.methods.route :as r]
            [fuchi.methods.live-gate :as lg]))

(def ^:private rails
  (r/route-envelope [{:envelope/line :housing   :envelope/imputed-usd-micros-yr 12000000000}
                     {:envelope/line :food      :envelope/imputed-usd-micros-yr 6000000000}
                     {:envelope/line :liquidity :envelope/imputed-usd-micros-yr 2000000000}]))

(deftest toritate-booking
  (testing "in-kind rails → toritate ledgerEntries; member-principal liquidity NOT booked (golden)"
    (let [es (b/book-toritate rails "alloc-1" "did:maint")]
      (is (= 2 (count es)))                                  ; liquidity skipped
      (is (= ["subsistence-flow" "subsistence-flow"] (mapv :category es)))
      (is (= [12000000000 6000000000] (mapv :imputed-usd-micros-yr es)))
      (is (every? #(= 0 (:cash-usd-micros %)) es))           ; cash≡0
      (is (every? #(= "did:maint" (:counterparty-did %)) es)))))

(deftest no-payroll-category
  (testing "toritate category enum — payroll/salary/wage unrepresentable (cash≡0 too)"
    (is (thrown? Exception (b/make-ledger-entry {:category "payroll" :imputed-usd-micros-yr 1})))
    (is (thrown? Exception (b/make-ledger-entry {:category "salary" :imputed-usd-micros-yr 1})))
    (is (thrown? Exception (b/make-ledger-entry {:category "nonsense" :imputed-usd-micros-yr 1})))
    (is (thrown? Exception (b/make-ledger-entry {:category "subsistence-flow" :cash-usd-micros 5})))
    (is (map? (b/make-ledger-entry {:category "grant" :imputed-usd-micros-yr 1})))))

(deftest kanae-flow-graph
  (testing "Sankey edges: Public Fund → 扶持 → provider → maintainer (golden from book.py)"
    (let [edges (b/flow-graph rails "alloc-1" "did:maint")]
      (is (= 7 (count edges)))                               ; 1 funding leg + 6 provider/maintainer legs
      (let [fund (first edges)]
        (is (= b/public-fund (:frm fund)))
        (is (= b/fuchi (:to fund)))
        (is (= "publicfund-to-fuchi" (:flow-class fund)))
        (is (= 18000000000 (:imputed-usd-micros-yr fund)))   ; in-kind total only (liquidity excluded)
        (is (true? (:in-kind fund))))
      ;; liquidity legs are flagged in-kind false (member-principal)
      (let [warifu-legs (filter #(or (= "warifu" (:frm %)) (= "warifu" (:to %))) edges)]
        (is (= 2 (count warifu-legs)))
        (is (every? #(false? (:in-kind %)) warifu-legs)))
      ;; every commons-land / mitsuho leg is in-kind
      (is (every? :in-kind (filter #(#{"commons-land" "mitsuho"} (:to %)) edges))))))

(deftest live-write-gated
  (testing "write-live commits via the R2 autonomous gate; cash≡0 holds in live mode"
    (let [es (b/book-toritate rails "alloc-1" "did:maint")
          receipt (b/write-live es (lg/make-gate {:leg "book"}))]
      (is (true? (:committed receipt)))
      (is (= 2 (count (:entries receipt))))
      (is (= 7 (:council-level receipt)))                    ; autonomous gate
      (is (thrown? Exception (b/write-live [{:cash-usd-micros 9}] (lg/make-gate {:leg "book"})))))))

(when (= *file* (System/getProperty "babashka.file"))
  (let [{:keys [fail error]} (run-tests 'fuchi.methods.test-book)]
    (System/exit (if (pos? (+ fail error)) 1 0))))
