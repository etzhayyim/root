#!/usr/bin/env bb
;; shinan 指南 — coverage engine tests (+ charter negative space: the 学習解放 heart).
(ns shinan.methods.test-analyze
  (:require [shinan.methods.analyze :as az]
            [shinan.methods.shinan-edn :as se]
            [clojure.string :as str]
            [clojure.test :refer [deftest is run-tests]]))

(def seed-path "20-actors/shinan/kotoba/seed.edn")
(defn- topics [] (se/topics seed-path))
(defn- resources [] (se/resources seed-path))
(defn- t-by-id [rows id] (first (filter #(= id (:id (:topic %))) rows)))

(def topic-routes #{:covered :needs-localization :coverage-gap})
(def resource-routes #{:offer :monitor})

(deftest routes-are-in-the-allowed-sets
  (let [a (az/assess (topics) (resources))]
    (is (every? #(topic-routes (:route %)) (get a "topics")))
    (is (every? #(resource-routes (:route %)) (get a "resources")))))

(deftest all-topic-and-resource-routes-exercised
  (let [a (az/assess (topics) (resources))]
    (doseq [r topic-routes] (is (contains? (get a "topic-tally") r) (str "topic route " r)))
    (doseq [r resource-routes] (is (contains? (get a "resource-tally") r) (str "resource route " r)))))

(deftest known-coverage-routes
  (let [rows (get (az/assess (topics) (resources)) "topics")]
    (is (= :covered            (:route (t-by-id rows "t-cn-math-gaokao"))) "高考数学 has a zh resource → covered")
    (is (= :covered            (:route (t-by-id rows "t-jp-japanese")))    "共通テスト国語 has a ja resource → covered")
    (is (= :needs-localization (:route (t-by-id rows "t-kr-english")))     "수능영어 only-English open resource → needs-localization")
    (is (= :coverage-gap       (:route (t-by-id rows "t-cn-science")))     "高考理科综合 no open resource → coverage-gap")))

(deftest worklist-is-the-gaps-and-localization
  (let [a (az/assess (topics) (resources))
        wl (set (map (comp :id :topic) (get a "worklist")))]
    (is (contains? wl "t-cn-science") "gap is on the 学習解放 worklist")
    (is (contains? wl "t-kr-english") "localization need is on the worklist")
    (is (not (contains? wl "t-jp-japanese")) "covered topic is not on the worklist")))

(deftest low-openness-resource-is-monitor
  (let [rows (get (az/assess (topics) (resources)) "resources")
        archived (first (filter #(= "r-archived-notes" (:id (:resource %))) rows))]
    (is (= :monitor (:route archived)) "low-availability resource → :monitor")))

(deftest datoms-carry-derived-and-sourcing
  (let [ds (az/datoms (az/assess (topics) (resources)))]
    (is (some (fn [[_ _ a _]] (= a ":shinan.rem/route")) ds) "route emitted")
    (is (some (fn [[_ _ a v]] (and (= a ":shinan/derived") (true? v))) ds) "derived flagged")
    (is (some (fn [[_ _ a _]] (= a ":shinan.resource/license")) ds) "license emitted")))

(deftest negative-space-no-score-no-rank-no-gate-no-prediction
  ;; THE CHARTER HEART (学習解放, no carve-out): none of these can be emitted.
  (let [ds (az/datoms (az/assess (topics) (resources)))
        attrs (map (fn [[_ _ a _]] a) ds)]
    (doseq [forbidden [":shinan/score" ":shinan/grade" ":shinan/rank"
                       ":shinan/pass-prediction" ":shinan.learner/" ":shinan.person/"
                       ":shinan/gate" ":shinan/credential" ":shinan/transcript"
                       ":shinan/timed-test" ":shinan/leaderboard" ":shinan/streak"
                       ":shinan/official-pastquestion"]]
      (is (not-any? #(str/includes? % forbidden) attrs)
          (str forbidden " is structurally absent")))))

(when (= *file* (System/getProperty "babashka.file"))
  (let [{:keys [fail error]} (run-tests 'shinan.methods.test-analyze)]
    (when (pos? (+ fail error)) (System/exit 1))))
