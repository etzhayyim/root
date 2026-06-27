(ns lg-pregel.smoke-test
  "Smoke tests for the lg-pregel clj port — clojure.test analogue of the Python
  `lg/tests/test_smoke.py`, plus dispatch/HITL behaviour tests the original could
  not run offline (the RisingWave/kotodama HITL store is injectable here, so the
  routing + interrupt-envelope shaping verify under bb with stubs)."
  (:require [clojure.test :refer [deftest is testing]]
            [langgraph.graph :as g]
            [lg-pregel.server :as server]
            [lg-pregel.store :as store]
            [lg-pregel.murakumo :as mk]
            [lg-pregel.graphs.outlook-triage :as ot]))

;; The clj twin mirrors the SERVER registry (server.py GRAPHS), which includes
;; projector_ops. The Python file's own `_EXPECTED_GRAPHS` (and langgraph.json)
;; omit projector_ops — a pre-existing Python drift documented in
;; graphs/projector_ops.cljc. We assert against the server registry (ground
;; truth), and separately pin the langgraph.json-declared subset.
(def expected-graphs
  #{"outlook_triage" "pregel_triage" "projector_lifecycle"
    "projector_driver" "projector_ops"})

(def langgraph-json-graphs
  #{"outlook_triage" "pregel_triage" "projector_lifecycle" "projector_driver"})

;; ── server registry parity ──────────────────────────────────────────────────

(deftest graphs-match-server-registry
  (is (= expected-graphs (set (keys server/GRAPHS)))))

(deftest langgraph-json-subset-present
  (testing "every graph declared in langgraph.json is registered in the server"
    (is (every? #(contains? server/GRAPHS %) langgraph-json-graphs))))

(deftest all-graphs-invocable
  (doseq [[nm graph] server/GRAPHS]
    (is (some? graph) (str "GRAPHS[" nm "] nil"))
    (is (map? (g/invoke graph {})) (str "GRAPHS[" nm "] not invocable"))))

(deftest graph-echoes-its-id
  (is (= "outlook_triage" (:graph (g/invoke ot/GRAPH {}))))
  (is (true? (:ok (g/invoke ot/GRAPH {})))))

;; ── /health /ok /graphs ─────────────────────────────────────────────────────

(deftest health-endpoint
  (let [r (server/health)]
    (is (= 200 (:status r)))
    (is (true? (get-in r [:body :ok])))
    (is (= "lg-pregel" (get-in r [:body :app])))
    (is (= expected-graphs (set (get-in r [:body :graphs]))))))

(deftest list-graphs-endpoint
  (is (= expected-graphs (set (get-in (server/list-graphs) [:body :graphs])))))

(deftest dispatcher-health-route
  (let [r (server/handle-request {:method :get :path "/ok" :headers {}})]
    (is (= 200 (:status r)))
    (is (true? (get-in r [:body :ok])))))

;; ── /runs ───────────────────────────────────────────────────────────────────

(deftest run-default-graph
  (let [r (server/run {} {})]
    (is (= 200 (:status r)))
    (is (= "outlook_triage" (get-in r [:body :graph])))
    (is (true? (get-in r [:body :ok])))))

(deftest run-by-assistant-id
  (let [r (server/run {:assistant_id "projector_driver" :input {:a 1}} {})]
    (is (= 200 (:status r)))
    (is (= "projector_driver" (get-in r [:body :graph])))))

(deftest run-unknown-graph-404
  (is (= 404 (:status (server/run {:assistant_id "nope"} {})))))

(deftest run-via-dispatcher
  (let [r (server/handle-request {:method :post :path "/runs" :headers {}
                                  :body {:graph "pregel_triage"}})]
    (is (= 200 (:status r)))
    (is (= "pregel_triage" (get-in r [:body :graph])))))

;; ── auth (LG_PREGEL_API_KEY) ────────────────────────────────────────────────

(deftest auth-open-when-unset
  (testing "no env key → open"
    (is (nil? (server/enforce-auth nil)))
    (is (nil? (server/enforce-auth "anything")))))

(deftest auth-cron-exempt
  (testing "x-cron=1 bypasses auth even when key would be required"
    (is (nil? (server/enforce-auth "wrong" true)))))

;; ── /stats ──────────────────────────────────────────────────────────────────

(deftest stats-clamps-days
  (binding [store/*store* (assoc store/default-store
                                 :get-all-stats (fn [days] {:days days}))]
    (is (= 365 (get-in (server/stats 9999 {}) [:body :days])) "clamped to 365")
    (is (= 1 (get-in (server/stats 0 {}) [:body :days])) "clamped to 1")
    (is (= 30 (get-in (server/stats nil {}) [:body :days])) "default 30")))

;; ── /threads/search ─────────────────────────────────────────────────────────

(deftest threads-search-non-interrupted-empty
  (is (= [] (:body (server/threads-search {:status "idle"} {})))))

(deftest threads-search-merges-and-sorts
  (binding [store/*store*
            (assoc store/default-store
                   :list-pending-gray   (fn [_] [{:id "g1" :updated_at "2026-01-01"}])
                   :list-pending-drafts (fn [_] [{:id "d1" :updated_at "2026-03-01"}]))]
    (let [items (:body (server/threads-search {} {}))]
      (is (= 2 (count items)))
      (is (= "d1" (:id (first items))) "newest updated_at first"))))

(deftest threads-search-clamps-limit
  (binding [store/*store*
            (assoc store/default-store
                   :list-pending-gray
                   (fn [limit] (is (= 1000 limit) "limit clamped to 1000") []))]
    (server/threads-search {:limit 99999} {})))

;; ── /threads/{id}/state ─────────────────────────────────────────────────────

(deftest thread-state-gray-envelope
  (binding [store/*store*
            (assoc store/default-store
                   :get-gray-item
                   (fn [_] {:from_address "a@b.com" :triage_score 7
                            :triage_reasons "spammy, link, foreign"}))]
    (let [r (server/thread-state "abc" {})
          iv (get-in r [:body :interrupts 0 :value])]
      (is (= 200 (:status r)))
      (is (= "interrupted" (get-in r [:body :status])))
      (is (= "request_human_decision" (:tool_name iv)))
      (is (= ["clean" "spam" "gray"] (:options iv)))
      (is (= 7 (get-in iv [:meta :triage_score])))
      (is (= ["spammy" "link" "foreign"] (get-in iv [:meta :triage_reasons]))
          "reasons split/trimmed"))))

(deftest thread-state-draft-envelope
  (binding [store/*store*
            (assoc store/default-store
                   :get-draft-item
                   (fn [_] {:from_address "x@y.com" :subject "Re: hi"
                            :draft_text "hello"}))]
    (let [r (server/thread-state "draft-99" {})
          iv (get-in r [:body :interrupts 0 :value])]
      (is (= 200 (:status r)))
      (is (= "request_draft_approval" (:tool_name iv)))
      (is (= ["approve" "discard"] (:options iv)))
      (is (= "hello" (get-in iv [:meta :draft_text]))))))

(deftest thread-state-not-found-404
  (is (= 404 (:status (server/thread-state "missing" {}))))
  (is (= 404 (:status (server/thread-state "draft-missing" {})))))

;; ── /threads/{id}/runs/stream ───────────────────────────────────────────────

(deftest thread-resume-gray-verdict
  (let [captured (atom nil)]
    (binding [store/*store*
              (assoc store/default-store
                     :apply-verdict (fn [tid v] (reset! captured [tid v]) {:ok true}))]
      (let [r (server/thread-resume "abc" {:command {:resume "spam"}} {})]
        (is (= 200 (:status r)))
        (is (= "text/event-stream" (get-in r [:headers "content-type"])))
        (is (= "spam" (:verdict r)))
        (is (= ["abc" "spam"] @captured))
        (is (re-find #"event.*updates" (:body r)))
        (is (re-find #"\"end\"" (:body r)))))))

(deftest thread-resume-invalid-verdict-defaults-gray
  (binding [store/*store* store/default-store]
    (is (= "gray" (:verdict (server/thread-resume "abc" {:command {:resume "weird"}} {}))))))

(deftest thread-resume-draft-verdict
  (let [captured (atom nil)]
    (binding [store/*store*
              (assoc store/default-store
                     :apply-draft-verdict
                     (fn [tid a t] (reset! captured [tid a t]) {:ok true}))]
      (let [r (server/thread-resume "draft-7"
                                    {:command {:resume "approve" :final_text "ok"}} {})]
        (is (= "approve" (:verdict r)))
        (is (= ["draft-7" "approve" "ok"] @captured))))))

;; ── dispatcher path parsing for thread routes ───────────────────────────────

(deftest dispatcher-thread-state-route
  (binding [store/*store*
            (assoc store/default-store :get-gray-item (fn [_] {:from_address "z@z"}))]
    (let [r (server/handle-request
             {:method :get :path "/threads/t1/state" :headers {}})]
      (is (= 200 (:status r)))
      (is (= "interrupted" (get-in r [:body :status]))))))

(deftest dispatcher-thread-resume-route
  (let [r (server/handle-request
           {:method :post :path "/threads/t1/runs/stream" :headers {}
            :body {:command {:resume "clean"}}})]
    (is (= 200 (:status r)))
    (is (= "clean" (:verdict r)))))

(deftest dispatcher-unknown-404
  (is (= 404 (:status (server/handle-request
                       {:method :get :path "/nope" :headers {}})))))

;; ── Murakumo loopback guard (ADR-2605215000) ────────────────────────────────

(deftest murakumo-guard
  (testing "off-fleet endpoint refused"
    (is (thrown? clojure.lang.ExceptionInfo
                 (mk/assert-murakumo "https://api.openai.com/v1"))))
  (testing "loopback gateway allowed"
    (is (nil? (mk/assert-murakumo "http://127.0.0.1:4000/v1")))))
