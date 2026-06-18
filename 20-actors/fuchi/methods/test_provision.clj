;; test_provision.clj — 扶持 provision: rails → provisioning intents (real producing actors) +
;; abaki anti-monopoly route-around, parity with provision.py. Run via `bb test:fuchi`. ADR-2606142300.
(ns fuchi.methods.test-provision
  (:require [clojure.test :refer [deftest is testing run-tests]]
            [fuchi.methods.provision :as p]
            [fuchi.methods.route :as r]
            [fuchi.methods.live-gate :as lg]))

(def ^:private rails
  (r/route-envelope [{:envelope/line :housing   :envelope/imputed-usd-micros-yr 12000000000}
                     {:envelope/line :food      :envelope/imputed-usd-micros-yr 6000000000}
                     {:envelope/line :liquidity :envelope/imputed-usd-micros-yr 2000000000}]))

(deftest provisioning-intents
  (testing "rails → provisioning intents addressed to real producing actors (golden from provision.py)"
    (let [ints (p/provision rails "alloc-1" #{})]            ; no blocked entities
      (is (= 3 (count ints)))
      (is (= [["housing-commons" "commons-land" "commons"]
              ["food-mitsuho" "did:web:etzhayyim.com:actor:mitsuho" "actor"]
              ["liquidity-warifu" "did:web:etzhayyim.com:actor:warifu" "actor"]]
             (mapv (juxt :rail-kind :provider-did :provider-kind) ints)))
      (is (= [false false true] (mapv :member-principal ints)))   ; liquidity = member-principal
      (is (every? #(false? (:published %)) ints))            ; G10 structural
      (is (every? #(= 0 (:cash-usd-micros %)) ints))         ; G2
      (is (every? #(false? (:server-held-key %)) ints)))))   ; G9

(deftest intent-invariants
  (testing "G2 cash≡0 / G9 no-server-key / G10 unpublished / G3 known rail enforced"
    (is (thrown? Exception (p/make-provisioning-intent {:rail-kind "food-mitsuho" :cash-usd-micros 5})))
    (is (thrown? Exception (p/make-provisioning-intent {:rail-kind "food-mitsuho" :server-held-key true})))
    (is (thrown? Exception (p/make-provisioning-intent {:rail-kind "food-mitsuho" :published true})))
    (is (thrown? Exception (p/make-provisioning-intent {:rail-kind "unknown-rail"})))
    (is (map? (p/make-provisioning-intent {:rail-kind "care-iyashi" :imputed-usd-micros-yr 1})))))

(deftest abaki-route-around
  (testing "a provider blocked by the abaki Anti-Monopoly policy raises (route-around)"
    (is (thrown? Exception (p/provision rails "alloc-1" #{"mitsuho"})))   ; mitsuho provider blocked
    (is (= 3 (count (p/provision rails "alloc-1" #{}))))                  ; none blocked → all provisioned
    (is (set? (p/load-blocked-ids "20-actors/abaki/out/does-not-exist.json")))))  ; missing → #{}

(deftest dispatch-gated
  (testing "dispatch-live authorizes via the R2 autonomous gate; cash≡0 / no-server-key hold"
    (let [ints (p/provision rails "alloc-1" #{})
          recs (p/dispatch-live ints (lg/make-gate {:leg "provision"}))]
      (is (= 3 (count recs)))
      (is (every? :authorized-to-publish recs))
      (is (every? #(= 7 (:council-level %)) recs)))))

(when (= *file* (System/getProperty "babashka.file"))
  (let [{:keys [fail error]} (run-tests 'fuchi.methods.test-provision)]
    (System/exit (if (pos? (+ fail error)) 1 0))))
