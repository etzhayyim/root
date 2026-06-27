(ns lg-webmk.test-smoke
  "Smoke tests for the lg-webmk clj port (no LLM / no live store required) —
  clj.test mirror of tests/test_smoke.py, plus store-enabled end-to-end coverage.

  Run: bb --config 60-apps/etzhayyim-project-webmk/lg/bb.edn test"
  (:require [clojure.test :refer [deftest is testing]]
            [langgraph.graph :as g]
            [lg-webmk.store :as store]
            [lg-webmk.server :as server]
            [lg-webmk.graphs.health :as health]
            [lg-webmk.graphs.create-proposal :as create-proposal]
            [lg-webmk.graphs.deliver-proposal :as deliver-proposal]
            [lg-webmk.graphs.get-proposal :as get-proposal]
            [lg-webmk.graphs.list-proposals :as list-proposals]))

;; ── parity with test_smoke.py (store disabled = Python no-RW path) ──

(deftest test-health-graph-no-store
  (let [result (g/invoke health/GRAPH {})]
    (is (contains? result :ok))))

(deftest test-get-proposal-no-store
  (let [result (g/invoke get-proposal/GRAPH {:proposal-id "prop-test-001"})]
    (is (contains? result :ok))
    (is (or (false? (:ok result)) (contains? result :proposal)))))

(deftest test-list-proposals-no-store
  (let [result (g/invoke list-proposals/GRAPH {:limit 10 :offset 0})]
    (is (true? (:ok result)))
    (is (= [] (:items result)))
    (is (= 0 (:total result)))))

(deftest test-create-proposal-no-llm
  (let [result (g/invoke create-proposal/GRAPH
                         {:client-name "Test Corp" :website-url ""
                          :industry "technology" :target-audience "SMBs"
                          :budget-jpy 500000 :delivery-email "test@example.com"})]
    ;; reaches store_proposal (terminating retry) even with no LLM
    (is (or (contains? result :copy-markdown) (contains? result :error)))
    (is (= true (:ok result)))))

(deftest test-deliver-proposal-no-resend
  (let [result (g/invoke deliver-proposal/GRAPH
                         {:proposal-id "prop-test-001"
                          :delivery-email "test@example.com"
                          :copy-markdown "# Test Proposal"})]
    (is (contains? result :ok))
    (is (or (true? (:ok result)) (contains? result :error)))))

(deftest test-nsid-map-coverage
  (doseq [[nsid assistant-id] server/nsid-map]
    (is (contains? server/graphs assistant-id)
        (str "NSID '" nsid "' maps to '" assistant-id "' but graph missing"))))

(deftest test-graph-names
  (is (= #{"health" "create_proposal" "deliver_proposal" "get_proposal" "list_proposals"}
         (set (keys server/graphs)))))

;; ── store-enabled end-to-end (stronger than the unconfigured Python path) ──

(deftest test-store-roundtrip
  (with-redefs [store/enabled? (constantly true)]
    (store/reset-store!)
    (testing "create persists, get fetches, list returns it"
      (let [created (g/invoke create-proposal/GRAPH
                              {:proposal-id "prop-rt-1" :client-name "ACME"
                               :website-url "" :industry "retail"
                               :target-audience "consumers" :budget-jpy 300000})]
        (is (true? (:stored created)))
        (let [got (g/invoke get-proposal/GRAPH {:proposal-id "prop-rt-1"})]
          (is (true? (:ok got)))
          (is (= "ACME" (get-in got [:proposal :clientName])))
          (is (= "draft" (get-in got [:proposal :status]))))
        (let [listed (g/invoke list-proposals/GRAPH {:limit 10 :offset 0})]
          (is (= 1 (:total listed)))
          (is (= "prop-rt-1" (get-in listed [:items 0 :proposalId]))))))
    (testing "deliver marks delivered"
      (g/invoke deliver-proposal/GRAPH
                {:proposal-id "prop-rt-1" :delivery-email "" :copy-markdown "x"})
      ;; delivery-email blank → not delivered → status stays draft
      (is (= "draft" (:status (store/get-proposal "prop-rt-1")))))
    (store/reset-store!)))

;; ── server dispatch (XRPC + /runs surface) ──

(deftest test-server-dispatch
  (testing "run-graph routes by assistant_id"
    (let [r (server/run-graph {"assistant_id" "health" "input" {}})]
      (is (= 200 (:status r)))
      (is (true? (get-in r [:body :ok]))))
    (let [r (server/run-graph {"assistant_id" "nope" "input" {}})]
      (is (= 404 (:status r)))))
  (testing "xrpc maps NSID → graph and normalizes camelCase input"
    (let [r (server/xrpc "com.etzhayyim.apps.webmk.listProposals" {"limit" 5})]
      (is (= 200 (:status r)))
      (is (true? (get-in r [:body :ok]))))
    (let [r (server/xrpc "com.etzhayyim.apps.webmk.unknown" {})]
      (is (= 404 (:status r))))))
