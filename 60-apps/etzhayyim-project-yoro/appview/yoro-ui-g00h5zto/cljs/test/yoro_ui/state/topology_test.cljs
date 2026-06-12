(ns yoro-ui.state.topology-test
  "Port of svelte/src/lib/session-topology.test.ts (P4).

   Invariants:
   - echoPersistence = 1 - distinct/total
   - Buffer is bounded to buffer-size (50).
   - Empty buffer → echoPersistence 0, distinctTopics 0.
   - Doom-scroll threshold tightens at night (20 min) vs day (45 min).
   - Raw topics are NOT exposed in the snapshot."
  (:require [cljs.test :refer [deftest is testing use-fixtures]]
            [yoro-ui.state.topology :as topo]))

(use-fixtures :each
  {:before (fn [] (topo/reset-session-topology))})

(deftest empty-session-returns-zeroes
  (let [s (topo/get-session-topology)]
    (is (zero? (:echoPersistence s)))
    (is (zero? (:distinctTopics s)))
    (is (zero? (:sampleSize s)))
    (is (>= (:dwellMs s) 0))))

(deftest echo-persistence-zero-for-all-distinct
  (topo/record-topic-visit "tag:a")
  (topo/record-topic-visit "tag:b")
  (topo/record-topic-visit "tag:c")
  (let [s (topo/get-session-topology)]
    (is (= 3 (:distinctTopics s)))
    (is (= 3 (:sampleSize s)))
    (is (< (js/Math.abs (:echoPersistence s)) 1e-5))))

(deftest echo-persistence-positive-when-topics-repeat
  (dotimes [_ 5] (topo/record-topic-visit "tag:cat"))
  (topo/record-topic-visit "tag:dog")
  (let [s (topo/get-session-topology)]
    (is (= 6 (:sampleSize s)))
    (is (= 2 (:distinctTopics s)))
    ;; echo = 1 - 2/6 = 0.6666...
    (is (< (js/Math.abs (- (:echoPersistence s) (/ 2 3))) 1e-5))))

(deftest ignores-nil-and-empty-inputs
  (topo/record-topic-visit nil)
  (topo/record-topic-visit js/undefined)
  (topo/record-topic-visit "")
  (let [s (topo/get-session-topology)]
    (is (zero? (:sampleSize s)))))

(deftest caps-internal-buffer-at-buffer-size
  (dotimes [i 200] (topo/record-topic-visit (str "tag:t" i)))
  (let [s (topo/get-session-topology)]
    (is (<= (:sampleSize s) 50))))

(deftest does-not-leak-raw-topics-through-snapshot
  (topo/record-topic-visit "tag:sensitive")
  (let [s (topo/get-session-topology)]
    (is (= #{:distinctTopics :dwellMs :echoPersistence :sampleSize}
           (set (keys s))))))

(deftest doom-scrolling-false-on-fresh-session
  (is (false? (topo/is-doom-scrolling?)))
  (is (false? (topo/is-doom-scrolling? :stress-idx 90))))

(deftest doom-scrolling-triggers-at-45min-day-when-stress-high
  (reset! topo/state {:sessionStart (- (.now js/Date) (* 46 60 1000))
                      :topics ["tag:a"]})
  (is (true? (topo/is-doom-scrolling? :stress-idx 80)))
  (is (false? (topo/is-doom-scrolling? :stress-idx 50))))

(deftest doom-scrolling-tightens-to-20min-at-night
  (reset! topo/state {:sessionStart (- (.now js/Date) (* 21 60 1000))
                      :topics ["tag:a"]})
  (is (true? (topo/is-doom-scrolling? :night-mode true :stress-idx 0)))
  (is (false? (topo/is-doom-scrolling? :night-mode false :stress-idx 0))))
