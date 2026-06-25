;; etzhayyim.test-mitama — mitama actor-lifecycle pure invariants (cljc port).
;; Run via the aggregate: bb test:helpers
;; Covers the pure SQL/payload/request shapers (HTTP dispatch deferred):
;; build-schema-status-stmt · clamp-timeout-ms · build-set-status-body ·
;; build-shinka-payload · build-{register,list-actors,inspect,set-status,shinka,schema-status}-request.
(ns etzhayyim.test-mitama
  (:require [clojure.test :refer [deftest is testing run-tests]]
            [etzhayyim.mitama :as m]))

(deftest schema-status-stmt
  (testing "no filters → bare statement"
    (is (= "SHOW ALTER TABLE COLUMN FROM graphar" (m/build-schema-status-stmt "" true ""))))
  (testing "table + state → WHERE with AND, state upper-cased"
    (is (= "SHOW ALTER TABLE COLUMN FROM graphar WHERE TableName = 'mytable' AND State = 'RUNNING'"
           (m/build-schema-status-stmt "mytable" false "running"))))
  (testing "all-tables? skips the table filter"
    (is (= "SHOW ALTER TABLE COLUMN FROM graphar WHERE State = 'RUNNING'"
           (m/build-schema-status-stmt "ignored" true "running"))))
  (testing "single quotes are doubled (injection-safe)"
    (is (= "SHOW ALTER TABLE COLUMN FROM graphar WHERE TableName = 't''x'"
           (m/build-schema-status-stmt "t'x" false "")))))

(deftest timeout-clamp
  (is (= 5000 (m/clamp-timeout-ms 5)))
  (is (= 1000 (m/clamp-timeout-ms 0)))        ;; floor
  (is (= 60000 (m/clamp-timeout-ms 100))))     ;; ceiling

(deftest payload-builders
  (is (= {:id "did:x" :status "dormant"} (m/build-set-status-body "did:x" "dormant")))
  (is (= {:model "gemma"} (m/build-shinka-payload "gemma")))
  (is (= {} (m/build-shinka-payload "")))
  (is (= {} (m/build-shinka-payload nil))))

(deftest request-shapers
  (testing "register POST carries the manifest body + bearer auth"
    (let [r (m/build-register-request "https://pds" "tok" {"name" "x"})]
      (is (= :post (:method r)))
      (is (= "https://pds/xrpc/com.etzhayyim.actor.register" (:url r)))
      (is (= "Bearer tok" (get-in r [:headers "Authorization"])))
      (is (= {"name" "x"} (:body r)))))
  (testing "nil token → no Authorization header"
    (is (nil? (get-in (m/build-register-request "https://pds" nil {}) [:headers "Authorization"]))))
  (testing "listActors limit defaults to 100, stringified"
    (is (= {"limit" "100"} (:params (m/build-list-actors-request "https://pds" "t" {}))))
    (is (= {"limit" "5"} (:params (m/build-list-actors-request "https://pds" "t" {:limit 5})))))
  (testing "getActor inspect puts id in params"
    (is (= {"id" "did:x"} (:params (m/build-inspect-request "https://pds" "t" "did:x")))))
  (testing "setStatus body via build-set-status-body"
    (is (= {:id "n1" :status "active"} (:body (m/build-set-status-request "https://pds" "t" "n1" "active")))))
  (testing "shinka body via build-shinka-payload"
    (is (= {:model "g"} (:body (m/build-shinka-request "https://pds" "t" "g"))))
    (is (= {} (:body (m/build-shinka-request "https://pds" "t" "")))))
  (testing "schema-status wraps stmt + clamped timeout"
    (let [r (m/build-schema-status-request "https://pds" "t" "tbl" false "running" 5)]
      (is (= "https://pds/xrpc/com.etzhayyim.kagami.sql" (:url r)))
      (is (= 5000 (get-in r [:body :timeoutMs])))
      (is (re-find #"TableName = 'tbl'" (get-in r [:body :statement]))))))

(defn -main [& _]
  (let [{:keys [fail error]} (run-tests 'etzhayyim.test-mitama)]
    (System/exit (if (pos? (+ fail error)) 1 0))))
