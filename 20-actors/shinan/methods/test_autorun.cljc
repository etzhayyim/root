#!/usr/bin/env bb
;; shinan 指南 — heartbeat tests (append-on-change, idempotent, resume-safe).
(ns shinan.methods.test-autorun
  (:require [shinan.methods.autorun :as a]
            [shinan.methods.shinan-edn :as se]
            [shinan.methods.kotoba :as k]
            [clojure.java.io :as io]
            [clojure.test :refer [deftest is run-tests]]))

(def seed-path "20-actors/shinan/kotoba/seed.edn")
(def ^:private tmp
  (str (System/getProperty "java.io.tmpdir") "/shinan-test-autorun.kotoba.edn"))
(defn- fresh! [] (let [f (io/file tmp)] (when (.exists f) (.delete f))) tmp)
(defn- topics [] (se/topics seed-path))
(defn- resources [] (se/resources seed-path))

(deftest first-beat-appends
  (let [path (fresh!)
        r (a/beat {:topics (topics) :resources (resources) :tx-id "b0" :as-of "t0" :log-path path})]
    (is (:appended r) "first beat appends")
    (is (pos? (:count r)) "coverage datoms emitted")
    (is (map? (:topic-routes r)))
    (is (map? (:resource-routes r)))
    (is (= 1 (count (k/read-log path))))
    (is (:ok (k/verify-chain path)))))

(deftest second-identical-beat-is-noop
  (let [path (fresh!)]
    (a/beat {:topics (topics) :resources (resources) :tx-id "b0" :as-of "t0" :log-path path})
    (let [r2 (a/beat {:topics (topics) :resources (resources) :tx-id "b1" :as-of "t1" :log-path path})]
      (is (not (:appended r2)) "identical assessment → no-op")
      (is (= :no-change (:reason r2)) "idempotent-by-content")
      (is (= 1 (count (k/read-log path))) "chain did not grow"))))

(deftest improved-coverage-appends-new-tx
  (let [path (fresh!)]
    (a/beat {:topics (topics) :resources (resources) :tx-id "b0" :as-of "t0" :log-path path})
    ;; localize the English OER into zh → t-cn-english flips needs-localization → covered
    (let [mutated (mapv (fn [r] (if (= "r-oer-english" (:id r))
                                  (assoc r :languages [:en :zh]) r))
                        (resources))
          r (a/beat {:topics (topics) :resources mutated :tx-id "b2" :as-of "t2" :log-path path})]
      (is (:appended r) "improved coverage appends")
      (is (= 2 (count (k/read-log path))))
      (is (:ok (k/verify-chain path)) "chain stays intact across beats"))))

(deftest heartbeat-refuses-non-open-resource
  ;; 学習解放 — the guard holds even at the heartbeat.
  (let [path (fresh!)
        bad (conj (resources) {:id "r-paid" :license :proprietary :openness 0.9 :covers [] :languages [:en]})]
    (is (thrown? clojure.lang.ExceptionInfo
                 (a/beat {:topics (topics) :resources bad :tx-id "bx" :as-of "tx" :log-path path})))))

(deftest resume-safe-head-chaining
  (let [path (fresh!)
        r0 (a/beat {:topics (topics) :resources (resources) :tx-id "b0" :as-of "t0" :log-path path})
        mutated (mapv (fn [r] (if (= "r-oer-english" (:id r)) (assoc r :languages [:en :zh]) r))
                      (resources))
        r1 (a/beat {:topics (topics) :resources mutated :tx-id "b1" :as-of "t1" :log-path path})]
    (is (= (:head r0) (get (first (k/read-log path)) ":tx/cid")))
    (is (= (:head r1) (k/head-cid path)) "beat head = ledger head after each append")))

(when (= *file* (System/getProperty "babashka.file"))
  (let [{:keys [fail error]} (run-tests 'shinan.methods.test-autorun)]
    (when (pos? (+ fail error)) (System/exit 1))))
