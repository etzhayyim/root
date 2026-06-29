#!/usr/bin/env bb
;; kanmon 関門 — heartbeat tests (append-on-change, idempotent, resume-safe).
(ns kanmon.methods.test-autorun
  (:require [kanmon.methods.autorun :as a]
            [kanmon.methods.kanmon-edn :as ke]
            [kanmon.methods.kotoba :as k]
            [clojure.java.io :as io]
            [clojure.test :refer [deftest is run-tests]]))

(def seed-path "20-actors/kanmon/kotoba/seed.edn")
(def ^:private tmp
  (str (System/getProperty "java.io.tmpdir") "/kanmon-test-autorun.kotoba.edn"))
(defn- fresh! [] (let [f (io/file tmp)] (when (.exists f) (.delete f))) tmp)
(defn- exams [] (ke/exams seed-path))

(deftest first-beat-appends
  (let [path (fresh!)
        r (a/beat {:exams (exams) :tx-id "b0" :as-of "t0" :log-path path})]
    (is (:appended r) "first beat appends")
    (is (pos? (:count r)) "route datoms emitted")
    (is (map? (:routes r)) "tally present")
    (is (= 1 (count (k/read-log path))))
    (is (:ok (k/verify-chain path)))))

(deftest second-identical-beat-is-noop
  (let [path (fresh!)]
    (a/beat {:exams (exams) :tx-id "b0" :as-of "t0" :log-path path})
    (let [r2 (a/beat {:exams (exams) :tx-id "b1" :as-of "t1" :log-path path})]
      (is (not (:appended r2)) "identical assessment → no-op")
      (is (= :no-change (:reason r2)) "idempotent-by-content")
      (is (= 1 (count (k/read-log path))) "chain did not grow"))))

(deftest changed-exam-appends-new-tx
  (let [path (fresh!)]
    (a/beat {:exams (exams) :tx-id "b0" :as-of "t0" :log-path path})
    ;; raise transparency on cn-zizhao so its route flips off :transparency-gap
    (let [mutated (mapv (fn [e] (if (= "cn-zizhao" (:id e)) (assoc e :transparency 0.8) e)) (exams))
          r (a/beat {:exams mutated :tx-id "b2" :as-of "t2" :log-path path})]
      (is (:appended r) "a changed assessment appends")
      (is (= 2 (count (k/read-log path))))
      (is (:ok (k/verify-chain path)) "chain stays intact across beats"))))

(deftest resume-safe-head-chaining
  (let [path (fresh!)
        r0 (a/beat {:exams (exams) :tx-id "b0" :as-of "t0" :log-path path})
        mutated (mapv (fn [e] (if (= "cn-zizhao" (:id e)) (assoc e :transparency 0.8) e)) (exams))
        r1 (a/beat {:exams mutated :tx-id "b1" :as-of "t1" :log-path path})]
    (is (= (:head r0) (get (first (k/read-log path)) ":tx/cid")))
    (is (= (:head r1) (k/head-cid path)) "beat head = ledger head after each append")))

(when (= *file* (System/getProperty "babashka.file"))
  (let [{:keys [fail error]} (run-tests 'kanmon.methods.test-autorun)]
    (when (pos? (+ fail error)) (System/exit 1))))
