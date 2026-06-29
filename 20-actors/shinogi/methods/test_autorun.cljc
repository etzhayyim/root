#!/usr/bin/env bb
;; shinogi 鎬 — heartbeat tests (append once, idempotent-by-content no-op).
(ns shinogi.methods.test-autorun
  (:require [shinogi.methods.shinogi-edn :as se]
            [shinogi.methods.autorun :as ar]
            [shinogi.methods.kotoba :as k]
            [clojure.test :refer [deftest is run-tests]]
            [clojure.java.io :as io]))

(def seed-path "20-actors/shinogi/kotoba/seed.exam-involution.edn")
(defn- tmp-log []
  (str (io/file (System/getProperty "java.io.tmpdir")
                (str "shinogi-test-autorun-" (hash (str (gensym))) ".edn"))))

(deftest beat-appends-then-noops
  (let [log (tmp-log)
        drivers (se/drivers seed-path)]
    (try
      (let [r1 (ar/beat {:drivers drivers :tx-id "b1" :as-of "a1" :log-path log})]
        (is (:appended r1) "first beat appends")
        (is (pos? (:count r1)) "datoms emitted")
        (is (= 9 (count (:regimes r1))) "all nine stock regimes reported")
        (is (number? (:failure-gap r1)) "failure-cycle relief-gap reported")
        ;; idempotent-by-content: an identical second beat is a no-op
        (let [r2 (ar/beat {:drivers drivers :tx-id "b2" :as-of "a2" :log-path log})]
          (is (not (:appended r2)) "identical second beat is a no-op")
          (is (= :no-change (:reason r2)))
          (is (= 1 (count (k/read-log log))) "ledger still has exactly one tx"))
        ;; a CHANGED seed (drop a driver) DOES append
        (let [r3 (ar/beat {:drivers (vec (rest drivers)) :tx-id "b3" :as-of "a3" :log-path log})]
          (is (:appended r3) "a changed driver set appends a new tx")
          (is (= 2 (count (k/read-log log))))
          (is (:ok (k/verify-chain log)) "chain still verifies")))
      (finally (io/delete-file log true)))))

#?(:clj
   (defn -main [& _]
     (let [r (run-tests 'shinogi.methods.test-autorun)]
       (System/exit (if (zero? (+ (:fail r) (:error r))) 0 1)))))
