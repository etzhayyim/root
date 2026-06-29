#!/usr/bin/env bb
;; kanmon 関門 — barrier-load → OPENING route engine tests (+ charter negative space).
(ns kanmon.methods.test-analyze
  (:require [kanmon.methods.analyze :as az]
            [kanmon.methods.kanmon-edn :as ke]
            [clojure.string :as str]
            [clojure.test :refer [deftest is run-tests]]))

(def seed-path "20-actors/kanmon/kotoba/seed.edn")
(defn- exams [] (ke/exams seed-path))
(defn- by-id [rows id] (first (filter #(= id (:id (:exam %))) rows)))

(def allowed-routes #{:transparency-gap :destake :equity-watch :open-pathway :monitor})

(deftest barrier-load-is-on-read-and-bounded
  (doseq [e (exams)]
    (let [bl (az/barrier-load e)]
      (is (<= 0.0 bl 1.0) (str (:id e) " barrier-load in 0..1")))))

(deftest every-route-is-an-opening
  (let [rows (get (az/assess (exams)) "exams")]
    (is (every? #(allowed-routes (:route %)) rows)
        "every route is an OPENING — no capture/entrench/optimize route exists (G4)")))

(deftest all-five-openings-exercised
  (let [tally (get (az/assess (exams)) "tally")]
    (doseq [r allowed-routes]
      (is (contains? tally r) (str "route " r " exercised by the seed")))))

(deftest known-routes-match
  (let [rows (get (az/assess (exams)) "exams")]
    (is (= :destake          (:route (by-id rows "cn-gaokao")))   "高考 = one-shot life-gate → :destake")
    (is (= :destake          (:route (by-id rows "kr-suneung")))  "수능 → :destake")
    (is (= :transparency-gap (:route (by-id rows "cn-zizhao")))   "综合评价 opaque → :transparency-gap")
    (is (= :transparency-gap (:route (by-id rows "kr-naesin")))   "내신 opaque → :transparency-gap")
    (is (= :open-pathway     (:route (by-id rows "cn-kaoyan")))   "考研 few alternatives → :open-pathway")
    (is (= :equity-watch     (:route (by-id rows "jp-chugaku")))  "中学受験 access disparity → :equity-watch")
    (is (= :monitor          (:route (by-id rows "jp-kyotsu")))   "共通テスト comparatively open → :monitor")))

(deftest transparency-gate-has-precedence
  ;; an exam below the transparency floor routes to :transparency-gap regardless of stakes
  (let [opaque {:id "x" :country :jp :kind :university-entrance
                :selectivity 0.9 :single-shot 0.95 :stakes 0.95
                :alt-pathways 0.1 :transparency 0.2 :equity 0.1}]
    (is (= :transparency-gap (:route (az/route opaque))))))

(deftest top-is-most-exclusive-gate
  (let [a (az/assess (exams))
        top (get a "top")
        maxbl (apply max (map :barrier-load (get a "exams")))]
    (is (= maxbl (:barrier-load top)) "top = highest barrier-load gate")))

(deftest datoms-carry-derived-and-sourcing
  (let [ds (az/datoms (az/assess (exams)))]
    (is (some (fn [[_ _ a _]] (= a ":kanmon.rem/route")) ds) "route emitted")
    (is (some (fn [[_ _ a v]] (and (= a ":kanmon/derived") (true? v))) ds) "derived flagged")
    (is (some (fn [[_ _ a _]] (= a ":kanmon/sourcing")) ds) "sourcing flagged")
    (is (some (fn [[_ _ a _]] (= a ":kanmon.rem/barrier-load")) ds) "barrier-load emitted")))

(deftest negative-space-no-person-no-prediction-no-gaming
  ;; the charter heart: map-not-target, no person, no pass-prediction, no gaming guide
  (let [ds (az/datoms (az/assess (exams)))
        attrs (map (fn [[_ _ a _]] a) ds)]
    (doseq [forbidden [":kanmon.student/" ":kanmon.person/" ":kanmon/rank-student"
                       ":kanmon/pass-prediction" ":kanmon/gaming-guide"
                       ":kanmon/target-list" ":kanmon.exam/official-pastquestion"]]
      (is (not-any? #(str/includes? % forbidden) attrs)
          (str forbidden " is structurally absent")))))

(when (= *file* (System/getProperty "babashka.file"))
  (let [{:keys [fail error]} (run-tests 'kanmon.methods.test-analyze)]
    (when (pos? (+ fail error)) (System/exit 1))))
