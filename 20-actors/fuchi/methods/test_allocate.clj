;; test_allocate.clj — 扶持 allocate: tenure-weighted in-kind sustenance + charter invariants,
;; parity with allocate.py. Run via `bb test:fuchi`. ADR-2606142300.
(ns fuchi.methods.test-allocate
  (:require [clojure.test :refer [deftest is testing run-tests]]
            [fuchi.methods.allocate :as al]))

(def ^:private cohort
  [{:did "did:a" :tenure-months 480 :hazard-permille 2000 :covenant "vowed" :prior-imputed-usd-micros-yr 10000000}
   {:did "did:b" :tenure-months 60  :hazard-permille 1000 :covenant "vowed" :prior-imputed-usd-micros-yr 5000000}
   {:did "did:c" :tenure-months 120 :hazard-permille 1500 :covenant "outreach" :prior-imputed-usd-micros-yr 8000000}])

(deftest tenure-weight-curve
  (testing "w = ln(1+min(tenure,40))×hazard — byte-equivalent with allocate.py"
    (is (== 7.427144133408616 (al/tenure-weight (first cohort))))
    (is (== 1.791759469228055 (al/tenure-weight (second cohort))))
    (is (== 1.0 (al/floor-decay 0)))
    (is (== 0.5 (al/floor-decay 30)))
    (is (== 0.0 (al/floor-decay 120)))))                  ; clamped at horizon

(deftest allocation-shares-ranks-floors
  (testing "vowed cohort tenure-weighted share (Σ=1), priority rank, decaying floor (golden)"
    (let [as (al/allocate cohort 6000000 0 "sustenance")
          by (into {} (map (juxt :maintainer-did identity) as))]
      (is (= ["did:a" "did:b" "did:c"] (mapv :maintainer-did as)))   ; vowed-first priority order
      (is (== 7.427144 (:weight (by "did:a"))))
      (is (== 0.805643 (:share (by "did:a"))))
      (is (= 1 (:priority-rank (by "did:a"))))
      (is (= 6000000 (:floor-usd-micros-yr (by "did:a"))))            ; min(10M,6M)×decay1.0
      (is (== 0.194357 (:share (by "did:b"))))
      (is (= 2 (:priority-rank (by "did:b"))))
      (is (= 5000000 (:floor-usd-micros-yr (by "did:b"))))
      (is (== 0.805643 (+ (:share (by "did:a")) -0.194357 (:share (by "did:b")))))  ; Σ shares ≈ 1 (a+b)
      ;; outreach — share 0, minimal floor (×0.25), ranked after vowed
      (is (== 0.0 (:share (by "did:c"))))
      (is (= 3 (:priority-rank (by "did:c"))))
      (is (= 1500000 (:floor-usd-micros-yr (by "did:c")))))))         ; min(8M,6M)×1.0×0.25

(deftest cash-zero-invariant
  (testing "cash≡0 structurally for every allocation (N1)"
    (let [as (al/allocate cohort 6000000)]
      (is (every? #(= 0 (:cash-usd-micros %)) as))
      (is (every? #(false? (:server-held-key %)) as)))))

(deftest instrument-allowlist-G1
  (testing "G1 — only sustenance instruments; investment/return vehicles UNREPRESENTABLE"
    (is (= "sustenance" (al/assert-instrument "sustenance")))
    (is (= "in-kind-grant" (al/assert-instrument ":in-kind-grant")))   ; colon stripped
    (doseq [bad ["equity" "debt" "convertible" "revenue-share" "carry" "dividend" "loan" "interest" "warrant" "option" "exit"]]
      (is (thrown? Exception (al/assert-instrument bad))))
    (is (thrown? Exception (al/assert-instrument "random")))           ; not in allowlist
    (is (thrown? Exception (al/allocate cohort 6000000 0 "equity")))))  ; allocate rejects too

(deftest structural-guards
  (testing "make-allocation + allocate enforce cash≡0 / no-server-key / G5 owns-payoff"
    (is (thrown? Exception (al/make-allocation {:instrument "sustenance" :cash-usd-micros 5})))
    (is (thrown? Exception (al/make-allocation {:instrument "sustenance" :server-held-key true})))
    (is (thrown? Exception (al/allocate [{:did "x" :tenure-months 12 :hazard-permille 1000
                                          :covenant "vowed" :owns-payoff true}] 100)))))  ; G5

(deftest cohort-from-seed-kw
  (testing "build a cohort from edn :maintainer/* records (keyword normalization)"
    (let [c (al/cohort-from-seed [{:maintainer/did "did:z" :maintainer/tenure-months 24
                                   :maintainer/hazard-permille 1200 :maintainer/covenant ":vowed"}])]
      (is (= "did:z" (:did (first c))))
      (is (= "vowed" (:covenant (first c))))                ; ":vowed" → "vowed"
      (is (= 24 (:tenure-months (first c))))
      (is (false? (:owns-payoff (first c)))))))

(when (= *file* (System/getProperty "babashka.file"))
  (let [{:keys [fail error]} (run-tests 'fuchi.methods.test-allocate)]
    (System/exit (if (pos? (+ fail error)) 1 0))))
