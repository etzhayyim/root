#!/usr/bin/env bb
;; kanmon 関門 — dry-run social-post invariants (seed-and-grow rails enforced).
(ns kanmon.methods.test-social
  (:require [kanmon.methods.social :as social]
            [kanmon.cells.social-post.state-machine :as sm]
            [kanmon.methods.dynamics :as dyn]
            [kanmon.methods.analyze :as az]
            [kanmon.methods.kanmon-edn :as ke]
            [clojure.string :as str]
            [clojure.test :refer [deftest is run-tests]]))

(def seed-path "20-actors/kanmon/kotoba/seed.edn")
(defn- rows [] (get (az/assess (ke/exams seed-path)) "exams"))
(def SRCS ["https://www.mext.go.jp/" "https://www.dnc.ac.jp/"])

(deftest opening-post-pins-the-rails
  (let [p (social/draft-opening-post (first (rows)) SRCS)]
    (is (= ":dry-run" (get p ":post/status")) "R0-gate: dry-run only")
    (is (true? (get p ":post/is-mirror")) "G-mirror")
    (is (true? (get p ":post/non-adjudicating-notice")))
    (is (false? (get p ":post/server-held-key")) "no-server-key")
    (is (>= (count (get p ":post/sources")) 2) "≥2 sources")
    (is (str/includes? (get p ":post/body") "OPENING map"))))

(deftest leverage-post-narrates-dynamics-not-people
  (let [a (dyn/analyze (rows))
        p (social/draft-leverage-post a SRCS)]
    (is (= ":dry-run" (get p ":post/status")))
    (is (str/includes? (get p ":post/body") "Meadows"))
    (is (str/includes? (get p ":post/body") "仮説")) "leverage is a hypothesis, not a directive"))

(deftest under-sourced-post-refused
  (is (thrown-with-msg? clojure.lang.ExceptionInfo #"sources"
                        (social/draft-opening-post (first (rows)) ["only-one"]))))

(deftest content-scan-refuses-ranking-and-prediction
  ;; a post that ranks students or predicts pass/fail is non-emittable (kanmon negative space)
  (is (thrown-with-msg? clojure.lang.ExceptionInfo #"content-scan"
                        (social/scan-clean! "受験生を偏差値で序列化する")))
  (is (thrown-with-msg? clojure.lang.ExceptionInfo #"content-scan"
                        (social/scan-clean! "合否予測: この受験生は落ちる確率70%")))
  (is (= "ゲートの構造の観測" (social/scan-clean! "ゲートの構造の観測")) "clean text passes"))

(deftest live-posting-refused-at-r0
  (is (thrown-with-msg? clojure.lang.ExceptionInfo #"seed-and-grow"
                        (social/build-live))))

;; ── membrane state machine ───────────────────────────────────────────────────
(deftest membrane-drafts-valid-record
  (let [out (sm/transition-to-drafted
             {"subject" "関門 開放地図: 共通テスト" "sources" SRCS
              "requested_status" "dry-run" "server_held_key" false})
        cs (get out "cell_state")]
    (is (= sm/phase-drafted (get cs "phase")))
    (is (= ":dry-run" (get-in cs ["payload" ":post/status"])))
    (is (false? (get-in cs ["payload" ":post/server-held-key"])))))

(deftest membrane-refuses-server-key-and-live-and-undersourced-and-ranking
  (is (= sm/phase-refused (get-in (sm/transition-to-drafted
                                   {"subject" "x" "sources" SRCS "server_held_key" true})
                                  ["cell_state" "phase"])) "server-key refused")
  (is (= sm/phase-refused (get-in (sm/transition-to-drafted
                                   {"subject" "x" "sources" SRCS "requested_status" "published"})
                                  ["cell_state" "phase"])) "live refused at R0")
  (is (= sm/phase-refused (get-in (sm/transition-to-drafted
                                   {"subject" "x" "sources" ["one"]})
                                  ["cell_state" "phase"])) "under-sourced refused")
  (is (= sm/phase-refused (get-in (sm/transition-to-drafted
                                   {"subject" "偏差値ランキング" "sources" SRCS})
                                  ["cell_state" "phase"])) "ranking content refused"))

(when (= *file* (System/getProperty "babashka.file"))
  (let [{:keys [fail error]} (run-tests 'kanmon.methods.test-social)]
    (when (pos? (+ fail error)) (System/exit 1))))
