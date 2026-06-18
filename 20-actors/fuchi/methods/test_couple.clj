;; test_couple.clj — 扶持 couple: Displacement-Dividend coupling (TitheRouter split + G2 gate),
;; parity with couple.py. Run via `bb test:fuchi`. ADR-2606142300.
(ns fuchi.methods.test-couple
  (:require [clojure.test :refer [deftest is testing run-tests]]
            [fuchi.methods.couple :as c]
            [fuchi.methods.live-gate :as lg]))

(def ^:private funded-event
  (c/make-displacement-event {:displacing-actor "sanae" :cohort-id "c1" :displaced-count 10
                              :surplus-usd-micros-yr 100000000 :funded true}))
(def ^:private earmark (c/earmark-from-surplus funded-event))

(deftest tithe-split-exact
  (testing "10% TitheRouter split is an exact integer split (gross = tithe + earmark) — golden"
    (is (= 100000000 (:gross-usd-micros-yr earmark)))
    (is (= 10000000 (:tithe-usd-micros earmark)))
    (is (= 90000000 (:earmark-usd-micros-yr earmark)))
    ;; odd surplus — no rounding leak
    (let [e (c/earmark-from-surplus (c/make-displacement-event {:displacing-actor "a" :cohort-id "c"
                                                                :surplus-usd-micros-yr 12345 :funded true}))]
      (is (= 1234 (:tithe-usd-micros e)))
      (is (= 11111 (:earmark-usd-micros-yr e)))
      (is (= 12345 (+ (:tithe-usd-micros e) (:earmark-usd-micros-yr e)))))
    (is (thrown? Exception (c/make-cohort-earmark {:gross-usd-micros-yr 100 :tithe-usd-micros 10
                                                   :earmark-usd-micros-yr 80})))))  ; 10+80≠100

(deftest g2-coupling-gate
  (testing "G2 — admissible iff funded AND committed ≤ earmark (golden from couple.py)"
    (let [ok (c/coupling-gate funded-event earmark 50000000)]
      (is (true? (:admissible ok)))
      (is (= 40000000 (:headroom ok))))                      ; 90M − 50M
    (is (false? (:admissible (c/coupling-gate funded-event earmark 95000000))))   ; over earmark
    (let [unfunded (c/earmark-from-surplus (c/make-displacement-event
                                            {:displacing-actor "x" :cohort-id "c" :surplus-usd-micros-yr 100000000 :funded false}))]
      (is (false? (:admissible (c/coupling-gate funded-event unfunded 1))))        ; not funded
      (is (= 0 (:headroom (c/coupling-gate funded-event unfunded 1)))))))

(deftest event-guards
  (testing "displacement event input guards"
    (is (thrown? Exception (c/make-displacement-event {:surplus-usd-micros-yr -1})))
    (is (thrown? Exception (c/make-displacement-event {:displaced-count -1})))))

(deftest commit-live-stacks-two-refusals
  (testing "commit-live: R2 gate + G2 coupling both apply (no live displacement without funded cohort)"
    (let [g  (lg/make-gate {:leg "couple"})
          cm (c/commit-live funded-event earmark 50000000 g)]
      (is (true? (:admissible cm)))
      (is (= 7 (:council-level cm)))                          ; couple leg = Lv7
      (is (= 50000000 (:committed-usd-micros-yr cm)))
      ;; G2 refusal: unfunded cohort cannot commit even through the gate
      (let [unfunded (c/earmark-from-surplus (c/make-displacement-event
                                              {:displacing-actor "x" :cohort-id "c" :surplus-usd-micros-yr 100000000 :funded false}))]
        (is (thrown? Exception (c/commit-live funded-event unfunded 1 g))))
      ;; G2 refusal: over-committed beyond the funded earmark
      (is (thrown? Exception (c/commit-live funded-event earmark 95000000 g))))))

(when (= *file* (System/getProperty "babashka.file"))
  (let [{:keys [fail error]} (run-tests 'fuchi.methods.test-couple)]
    (System/exit (if (pos? (+ fail error)) 1 0))))
