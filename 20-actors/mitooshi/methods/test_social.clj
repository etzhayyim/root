#!/usr/bin/env bb
;; Tests for the mitooshi aggregate-first resilience advisory / social layer (methods/social.clj).
;;
;; Run:
;;   bb --classpath 20-actors 20-actors/mitooshi/methods/test_social.clj
;;
;; Verifies the non-adjudicating delivery invariants: distribution-only (G1), non-speculative
;; use (G2), planner-routed (G3), aggregate-first (G4), broadcast operator-gated (no-server-key).
(ns mitooshi.methods.test-social
  (:require [clojure.test :refer [deftest is are testing run-tests]]
            [mitooshi.methods.social :as social :refer [compose-resilience-advisory
                                                        handle-social-post
                                                        ALLOWED-USE
                                                        PLANNERS]]))

(deftest advisory-states-a-band-not-a-point
  (let [adv (compose-resilience-advisory "s-x" 0.2 0.3 7)]
    (is (= false (get adv "pointAsserted")) "G1: pointAsserted must be false")
    (is (= [-0.1 0.5] (get adv "band68")) "band68 must be [mean-sd, mean+sd] rounded to 4dp")
    (is (clojure.string/includes? (get adv "text") "[-0.1, 0.5]") "text must state the band, not a single value")))

(deftest advisory-refuses-point-assertion-g1
  (is (thrown-with-msg? Exception #"G1"
        (compose-resilience-advisory "s-x" 0.2 0.3 7 ":resilience" true))
      "a point-asserted forecast must be refused (G1)"))

(deftest advisory-refuses-speculative-use-g2
  (doseq [bad [":trade" ":speculation" ":wager" ":position"]]
    (is (thrown-with-msg? Exception #"G2"
          (compose-resilience-advisory "s-x" 0.2 0.3 7 bad))
        (str "use " bad " must be refused (G2)"))))

(deftest advisory-requires-planner-route-g3
  ;; bad planner must be refused
  (is (thrown-with-msg? Exception #"G3"
        (compose-resilience-advisory "s-x" 0.2 0.3 7 ":resilience" false "some-trader"))
      "an advisory must route to a planner (G3)")
  ;; a valid planner is accepted
  (let [adv (compose-resilience-advisory "s-x" 0.2 0.3 7 ":resilience" false "kanae")]
    (is (= "kanae" (get adv "routeTo")))
    (is (clojure.string/includes? (get adv "text") "kanae"))))

(deftest allowed-use-excludes-trade
  (is (contains? ALLOWED-USE ":resilience"))
  (is (contains? PLANNERS "danjo"))
  (doseq [forbidden [":trade" ":speculation" ":wager" ":position"]]
    (is (not (contains? ALLOWED-USE forbidden))
        (str forbidden " must not be in ALLOWED-USE"))))

(deftest social-post-default-is-draft-aggregate
  (let [out (handle-social-post {"forecasts" [{"series" "s-x" "mean" 0.2 "sd" 0.3
                                               "target" 7 "routeTo" "danjo"}]})]
    (is (= 1 (count (get out "posts"))))
    (let [p (first (get out "posts"))]
      (is (= "draft" (get p "state")) "operator-gated (no-server-key)")
      (is (= "aggregate" (get p "shape")) "G4: shape must be aggregate"))
    (is (= 100 (get out "aggregateSharePct")))))

(deftest social-post-posts-with-operator
  (let [out (handle-social-post {"forecasts" [{"series" "s-x" "mean" 0.2 "sd" 0.3
                                               "target" 7 "routeTo" "danjo"}]
                                 "operatorRef" "op:1"})]
    (is (= "posted" (get (first (get out "posts")) "state")))))

(deftest social-post-refuses-bad-items-per-item
  (let [out (handle-social-post {"forecasts" [{"series" "ok"  "mean" 0.2 "sd" 0.3 "target" 7 "routeTo" "danjo"}
                                              {"series" "pt"  "mean" 0.2 "sd" 0.3 "target" 7 "pointAsserted" true}
                                              {"series" "tr"  "mean" 0.2 "sd" 0.3 "target" 7 "use" ":trade"}]})]
    (is (= 1 (count (get out "posts"))) "only the clean item should post")
    (let [reasons (into {} (map (fn [r] [(get r "series") (get r "reason")]) (get out "refused")))]
      (is (clojure.string/includes? (get reasons "pt") "G1"))
      (is (clojure.string/includes? (get reasons "tr") "G2")))))

;; Entry point — mirrors social.py's __main__ guard pattern.
(when (= *file* (System/getProperty "babashka.file"))
  (let [{:keys [fail error]} (clojure.test/run-tests 'mitooshi.methods.test-social)]
    (System/exit (if (zero? (+ fail error)) 0 1))))
