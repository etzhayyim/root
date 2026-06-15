#!/usr/bin/env bb
;; Working Clojure port of py/test_agent.py.
(ns meyasu.py.test-agent
  "meyasu 目安 — unified arbitrage orchestrator tests (methods clj port).

  Verifies the fusion + publication invariants: fuses kakaku spread/SD + mitooshi forecast into
  one card (no math re-implemented); G2 a point-asserted/speculative forecast is REFUSED;
  trajectory = forecast mean vs present index; attention = notable spread AND tightening → routed
  to the resilience planner (G4); publish is aggregate-first (G3), no nudge/affiliate (G1),
  operator-gated (no-server-key); persist writes a forecast BAND, never a point (G1/G2).

  Run:  bb --classpath 20-actors 20-actors/meyasu/py/test_agent.clj"
  (:require [meyasu.py.agent :as agent]
            [clojure.test :refer [deftest is run-tests]]))

(defn- item [& {:keys [notable mean now point use*] :or {notable true mean 0.5 now 0.1 point false use* :resilience}}]
  {:productId "jan_x"
   :kakaku {:spread 700 :spreadFraction 0.22 :notable notable :cheapestMerchant "a_com"
            :supplyDemandIndex now :reading "balanced"}
   :mitooshi {:mean mean :sd 0.3 :target 7 :use use* :pointAsserted point}})

(deftest fuse-combines-spread-and-forecast
  (let [out (agent/handle-fuse {:items [(item)]})
        c (first (:cards out))]
    (is (= (count (:cards out)) 1))
    (is (= (:priceSpread c) 700))
    (is (= (:forecastBand c) [0.2 0.8]))          ; mean 0.5 ± sd 0.3
    (is (= (:intent c) "buyer-transparency+supply-resilience"))))

(deftest trajectory-tightening-easing-stable
  (is (= (agent/trajectory 0.1 0.5) "tightening"))
  (is (= (agent/trajectory 0.5 0.1) "easing"))
  (is (= (agent/trajectory 0.3 0.32) "stable")))

(deftest attention-routes-to-resilience-planner
  (let [c (first (:cards (agent/handle-fuse {:items [(item :notable true :mean 0.6 :now 0.1)]})))]
    (is (true? (:attention c)))
    (is (= (:routeTo c) agent/resilience-planner))))

(deftest non-attention-routes-to-buyer-planner
  (let [c (first (:cards (agent/handle-fuse {:items [(item :notable true :mean 0.1 :now 0.1)]})))]
    (is (false? (:attention c)))
    (is (= (:routeTo c) agent/buyer-planner))))

(deftest fuse-refuses-point-asserted-forecast-g2
  (let [out (agent/handle-fuse {:items [(item :point true)]})]
    (is (empty? (:cards out)))
    (is (clojure.string/includes? (:reason (first (:refused out))) "G2"))))

(deftest fuse-refuses-speculative-use-g2
  (let [out (agent/handle-fuse {:items [(item :use* :trade)]})]
    (is (empty? (:cards out)))
    (is (clojure.string/includes? (:reason (first (:refused out))) "G2"))))

(deftest fuse-without-forecast-is-ok
  (let [it {:productId "p" :kakaku {:spread 100 :spreadFraction 0.1 :notable false
                                    :supplyDemandIndex 0.0 :reading "balanced"}}
        c (first (:cards (agent/handle-fuse {:items [it]})))]
    (is (nil? (:forecastBand c)))
    (is (= (:trajectory c) "unknown"))))

(deftest publish-default-draft-aggregate-no-nudge
  (let [cards (:cards (agent/handle-fuse {:items [(item)]}))
        out (agent/handle-publish {:cards cards})
        p (first (:posts out))]
    (is (= (:state p) "draft"))                   ; operator-gated
    (is (= (:shape p) "aggregate"))               ; G3
    (is (and (false? (:nudge p)) (false? (:affiliate p))))  ; G1
    (is (= (:aggregateSharePct out) 100))))

(deftest publish-attention-card-creates-handoff
  (let [cards (:cards (agent/handle-fuse {:items [(item :notable true :mean 0.6 :now 0.1)]}))
        out (agent/handle-publish {:cards cards})]
    (is (= (count (:handoffs out)) 1))
    (is (= (:routeTo (first (:handoffs out))) agent/resilience-planner))))

(deftest publish-posts-with-operator
  (let [cards (:cards (agent/handle-fuse {:items [(item)]}))
        out (agent/handle-publish {:cards cards :operatorRef "op:1"})]
    (is (= (:state (first (:posts out))) "posted"))
    (is (true? (:broadcast out)))))

(deftest persist-emits-card-datoms
  (let [cards (:cards (agent/handle-fuse {:items [(item)]}))
        out (agent/handle-persist {:cards cards :observedAt "2026-06-07T00:00:00Z"})
        kinds (set (map second (:datoms out)))]
    (is (> (:datomCount out) 0))
    (is (contains? kinds :meyasu.card/product))
    (is (contains? kinds :meyasu.card/intent))))

(deftest persist-writes-forecast-as-band-not-point-g1
  (let [cards (:cards (agent/handle-fuse {:items [(item :mean 0.5 :now 0.1)]}))
        attrs (set (map second (:datoms (agent/handle-persist {:cards cards :observedAt "t"}))))]
    (is (contains? attrs :meyasu.card/forecast-band-lo))
    (is (contains? attrs :meyasu.card/forecast-band-hi))
    ;; no point-value attribute — a band, never a point (G1/G2)
    (is (not-any? #(or (clojure.string/includes? (str %) "forecast-point")
                       (= % :meyasu.card/forecast-mean)) attrs))))

(deftest persist-no-server-key-tx-only-without-operator
  (let [cards (:cards (agent/handle-fuse {:items [(item)]}))]
    (is (= (:writeState (agent/handle-persist {:cards cards})) "tx-only"))))

(deftest persist-commits-with-operator
  (let [cards (:cards (agent/handle-fuse {:items [(item)]}))]
    (is (= (:writeState (agent/handle-persist {:cards cards :operatorRef "op:1"})) "committed"))))

(deftest card-to-datoms-uses-observed-at-in-id
  (let [card (first (:cards (agent/handle-fuse {:items [(item)]})))
        datoms (agent/card-to-datoms card "2026-06-07T12:00:00Z")
        eid (first (first datoms))]
    (is (clojure.string/includes? eid "2026-06-07T12:00:00Z"))
    (is (clojure.string/starts-with? eid "meyasu.card."))))

(when (= *file* (System/getProperty "babashka.file"))
  (require 'clojure.string)
  (let [{:keys [fail error]} (run-tests 'meyasu.py.test-agent)]
    (System/exit (if (zero? (+ fail error)) 0 1))))
