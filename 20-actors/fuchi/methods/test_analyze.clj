;; test_analyze.clj — 扶持 analyze: end-to-end allocation pipeline over the :representative seed,
;; parity with analyze.py run(). Run via `bb test:fuchi`. ADR-2606142300.
(ns fuchi.methods.test-analyze
  (:require [clojure.test :refer [deftest is testing run-tests]]
            [clojure.string :as str]
            [fuchi.methods.analyze :as a]))

(def ^:private res (a/run))

(defn- row [did] (first (filter #(str/ends-with? (str (:did %)) did) (:rows res))))

(deftest pipeline-routing-outcomes
  (testing "each seed maintainer routes + resolves exactly as analyze.py run() (golden)"
    (is (= 5 (count (:rows res))))
    (is (= ":auto"        (:route (row "abel"))))   (is (= "accepted" (:outcome (row "abel"))))
    (is (= "accepted"     (:outcome (row "seth"))))                          ; via sbt-vote
    (is (str/starts-with? (:route (row "seth")) ":sbt-vote 5-1/48h✓"))       ; real 1 SBT=1 vote tally
    (is (= ":council-lv7" (:route (row "eve"))))    (is (= "pending"  (:outcome (row "eve"))))
    (is (= "accepted"     (:outcome (row "noah"))))                          ; outreach, auto
    (is (= ":refused"     (:route (row "cain"))))   (is (= "refused"  (:outcome (row "cain"))))))

(deftest pipeline-projection-counts
  (testing "provisioning / ledger / flow / derived counts match analyze.py run()"
    (is (= 14 (count (:intents res))))
    (is (= 13 (count (:ledger res))))
    (is (= 32 (count (:flows res))))
    (is (= 4  (count (:derived res))))))           ; abel+seth+eve+noah booked; cain refused

(deftest cash-zero-everywhere
  (testing "cash≡0 holds across every projection (the defining invariant)"
    (is (every? #(= 0 (:cash-usd-micros %)) (:intents res)))
    (is (every? #(= 0 (:cash-usd-micros %)) (:ledger res)))
    (is (every? #(false? (:server-held-key %)) (:intents res)))
    (is (every? #(false? (:published %)) (:intents res)))         ; G10 dry-run
    (is (every? #(= 0 (:alloc/cash-usd-micros %)) (:derived res)))))

(deftest displacement-coupling-G2
  (testing "Displacement-Dividend coupling: funded cohort admissible, unfunded refused (golden)"
    (let [by (into {} (map (juxt #(str (get-in % [:earmark :cohort-id])) identity) (:coupling res)))]
      (is (= 2 (count (:coupling res))))
      (is (true?  (get-in (by "cohort-sanae-2026") [:gate :admissible])))   ; funded
      (is (false? (get-in (by "cohort-hataori-2026") [:gate :admissible])))  ; unfunded → G2 refuse
      (is (= 6000000000 (get-in (by "cohort-sanae-2026") [:earmark :tithe-usd-micros]))))))  ; 10% of 60e9

(deftest live-legs-and-scorecard
  (testing "all four R2 live legs admissible; scorecard renders"
    (is (= #{"provision" "vote" "book" "couple"} (set (map :leg (:live-status res)))))
    (is (every? :admissible (:live-status res)))
    (let [sc (a/scorecard res)]
      (is (str/includes? sc "扶持"))
      (is (str/includes? sc "accepted: 3"))                       ; abel + seth + noah
      (is (str/includes? sc "refused: 1")))))                     ; cain

(when (= *file* (System/getProperty "babashka.file"))
  (let [{:keys [fail error]} (run-tests 'fuchi.methods.test-analyze)]
    (System/exit (if (pos? (+ fail error)) 1 0))))
