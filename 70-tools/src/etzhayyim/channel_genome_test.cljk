(ns etzhayyim.channel-genome-test
  "Tests for the kotoba-genome W1×W2 bridge (ADR-2606302205): an actor learns WHICH
  channel to grow on by folding per-channel real growth readings, and recommends by
  realised growth-rate (not prediction accuracy). Run: bb --classpath 70-tools/src
  -e \"(require 'etzhayyim.channel-genome-test)
       (clojure.test/run-tests 'etzhayyim.channel-genome-test)\""
  (:require [clojure.test :refer [deftest is testing]]
            [etzhayyim.channel-genome :as cg]))

(defn- fold [rounds] (reduce cg/beat-channels cg/empty-state rounds))

(deftest learns-the-growing-channel
  (testing "the actor prefers the channel where growth actually RISES, not the flat/falling ones"
    (let [rounds [{:x 1.0 :at-proto 4.0 :email 2.0 :telegram 2.0 :line 2.0}
                  {:x 2.0 :at-proto 3.0 :email 2.0 :telegram 2.0 :line 2.0}
                  {:x 3.0 :at-proto 2.0 :email 2.0 :telegram 2.0 :line 2.0}
                  {:x 4.0 :at-proto 1.0 :email 2.0 :telegram 2.0 :line 2.0}]
          st  (fold rounds)
          rec (cg/preferred-channel st)
          g   (into {} (map (juxt :channel identity)) (:ranked rec))]
      (is (= 4 (:round st)))
      (is (= :x (:channel rec)))
      (is (= :dry-run (:status rec)))
      (is (= 5 (count (:ranked rec))))
      ;; :x rose every scored beat → high up-rate; the falling channel → low
      (is (> (:up-rate (g :x)) (:up-rate (g :at-proto))))
      ;; the falling channel is no better than a flat one (both never rise)
      (is (>= (:up-rate (g :email)) (:up-rate (g :at-proto)))))))

(deftest untried-channel-is-neutral
  (testing "a channel with no readings is neutral (0.5 up-rate, weight 1.0)"
    (let [gr (cg/channel-growth cg/empty-state :line)]
      (is (= 0.5 (:up-rate gr)))
      (is (zero? (:n gr)))
      (is (= 1.0 (:weight gr))))))

(deftest deterministic-replay
  (testing "folding the same rounds twice yields the identical recommendation (crash-resume)"
    (let [rounds [{:x 1.0 :line 1.0} {:x 2.0 :line 1.0} {:x 3.0 :line 1.0}]]
      (is (= (cg/preferred-channel (fold rounds))
             (cg/preferred-channel (fold rounds))))
      (is (= :x (:channel (cg/preferred-channel (fold rounds))))))))

(deftest partial-round-leaves-others-untouched
  (testing "a round that omits a channel does not touch that channel's genome"
    (let [st (cg/beat-channels (fold [{:x 1.0 :line 1.0}]) {:x 2.0})]
      ;; round1 pre-registers both (no score yet); round2 folds only :x → :x gets its
      ;; first scored beat, :line stays unscored (its genome untouched).
      (is (= 0 (:n (cg/channel-growth st :line))))
      (is (= 1 (:n (cg/channel-growth st :x))))
      (is (= 2 (:round st))))))
