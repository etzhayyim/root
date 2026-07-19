(ns lg-karma.smoke-test
  "Smoke tests for the lg-karma clj port — clojure.test mirror of
  `lg/tests/test_smoke.py`, plus graph-behaviour tests the python could not run
  offline (the native primitives are injectable here, so the single-node graph
  contract + the swap seam verify under bb with stubs).

  Run: bb --config 60-apps/etzhayyim-project-karma/lg-clj/bb.edn test"
  (:require [clojure.test :refer [deftest is testing]]
            [langgraph.graph :as g]
            [lg-karma.handlers :as h]
            [lg-karma.graphs :as graphs]
            [lg-karma.server :as server]))

(def health-nsid "com.etzhayyim.apps.karma.health")

;; ── registry parity (mirrors test_smoke.py) ─────────────────────────────────

(deftest server-namespace-loads
  (is (map? server/GRAPHS))
  (is (map? server/NSID-MAP)))

(deftest health-graph-present
  (is (contains? server/GRAPHS "health") "GRAPHS must contain 'health'"))

(deftest health-nsid-in-nsid-map
  (is (contains? server/NSID-MAP health-nsid))
  (is (= "health" (get server/NSID-MAP health-nsid))))

(deftest nsid-map-references-known-graphs
  (doseq [[nsid gname] server/NSID-MAP]
    (is (contains? server/GRAPHS gname)
        (str "NSID-MAP[" nsid "] → " gname " not in GRAPHS"))))

(deftest graph-count-matches-langgraph-json
  ;; langgraph.json declares health + 45 tasks = 46 keys.
  (is (= 46 (count server/GRAPHS)))
  (is (= 45 (count h/task-names)))
  (is (= 46 (count server/NSID-MAP))))

(deftest no-duplicate-task-names
  (is (= (count h/task-names) (count (set h/task-names)))))

(deftest all-graphs-invocable
  (doseq [[nm graph] server/GRAPHS]
    (is (some? graph) (str "GRAPHS[" nm "] nil"))
    (is (map? (g/invoke graph {:input {}})) (str "GRAPHS[" nm "] not invocable"))))

;; ── endpoint surface (≡ test_smoke.py endpoint tests) ───────────────────────

(deftest health-endpoint
  (let [r (server/health)]
    (is (= 200 (:status r)))
    ;; python /health returns the graph result {status, service}; the python
    ;; test's `r.json()["ok"]` assertion is inconsistent with its own server —
    ;; we assert the server's actual (faithful) behaviour instead.
    (is (= "ok" (get-in r [:body :status])))
    (is (= "lg-karma" (get-in r [:body :service])))))

(deftest ok-endpoint
  (let [r (server/handler {:uri "/ok" :request-method :get})]
    (is (= 200 (:status r)))))

(deftest unknown-assistant-404
  (is (= 404 (:status (server/run {"assistant_id" "nope" "input" {}})))))

(deftest unknown-nsid-xrpc-404
  ;; python server raises 501; the python test (and wave-1 twins) expect 404.
  (is (= 404 (:status (server/xrpc "com.etzhayyim.apps.karma.unknownMethod" {})))))

(deftest runs-defaults-to-health
  (let [r (server/run {})]
    (is (= 200 (:status r)))
    (is (= "ok" (get-in r [:body :output :status])))
    (is (number? (get-in r [:body :elapsed_s])))))

;; ── single-node graph contract (START → execute → END) ──────────────────────

(deftest health-graph-invokes
  (let [out (g/invoke graphs/HEALTH {:input {}})]
    (is (= {:status "ok" :service "lg-karma"} (:result out)))))

(deftest task-graph-default-unwired
  ;; every task defaults to the `unwired` swap-seam stub → flows through :result
  (let [out (g/invoke (server/GRAPHS "ipfsPinBatch") {:input {:cids ["a" "b"]}})]
    (is (h/unwired? (:result out)))
    (is (= "ipfsPinBatch" (get-in out [:result :unwired])))
    (is (= {:cids ["a" "b"]} (get-in out [:result :echo])))
    (is (nil? (:error out)))))

(deftest task-graph-handler-injection
  ;; the actor swap: rebind *handlers* with a real impl → surfaces as :result
  (binding [h/*handlers* (assoc h/*handlers*
                                "wbtBalanceGet"
                                (fn [in] {:balance 42 :for (:did in)}))]
    (let [out (g/invoke (server/GRAPHS "wbtBalanceGet")
                        {:input {:did "did:plc:x"}})]
      (is (= {:balance 42 :for "did:plc:x"} (:result out)))
      (is (nil? (:error out))))))

(deftest task-graph-handler-exception->error
  ;; handler throws → {:error str[:300]} (≡ python except → {"error": ...})
  (binding [h/*handlers* (assoc h/*handlers*
                                "daoFinalize"
                                (fn [_] (throw (ex-info "boom-finalize" {}))))]
    (let [out (g/invoke (server/GRAPHS "daoFinalize") {:input {}})]
      (is (re-find #"boom-finalize" (:error out)))
      (is (nil? (:result out))))))

(deftest error-clipped-to-300
  (binding [h/*handlers* (assoc h/*handlers*
                                "daoCastVote"
                                (fn [_] (throw (ex-info (apply str (repeat 500 "x")) {}))))]
    (let [out (g/invoke (server/GRAPHS "daoCastVote") {:input {}})]
      (is (<= (count (:error out)) 300)))))

;; ── /runs + /xrpc dispatch through an injected handler ──────────────────────

(deftest runs-dispatch-injected
  (binding [h/*handlers* (assoc h/*handlers*
                                "coverageSnapshot"
                                (fn [_] {:covered 7 :total 9}))]
    (let [r (server/run {"assistant_id" "coverageSnapshot" "input" {}})]
      (is (= 200 (:status r)))
      (is (= {:covered 7 :total 9} (get-in r [:body :output]))))))

(deftest xrpc-dispatch-injected
  (binding [h/*handlers* (assoc h/*handlers*
                                "filecoinStatusGet"
                                (fn [in] {:deal (:deal-id in) :state "active"}))]
    (let [r (server/xrpc "com.etzhayyim.apps.karma.filecoinStatusGet" {:deal-id "d1"})]
      (is (= 200 (:status r)))
      (is (= "active" (get-in r [:body :output :state]))))))

(deftest xrpc-handler-error->500
  (binding [h/*handlers* (assoc h/*handlers*
                                "rebirthEmerge"
                                (fn [_] (throw (ex-info "no-rebirth" {}))))]
    (let [r (server/xrpc "com.etzhayyim.apps.karma.rebirthEmerge" {})]
      (is (= 500 (:status r)))
      (is (re-find #"no-rebirth" (get-in r [:body :error]))))))

;; ── http handler routing ────────────────────────────────────────────────────

(deftest http-handler-routes
  (testing "/ok"
    (is (= 200 (:status (server/handler {:uri "/ok" :request-method :get})))))
  (testing "unknown route → 404"
    (is (= 404 (:status (server/handler {:uri "/nope" :request-method :get})))))
  (testing "/xrpc unmapped → 404"
    (is (= 404 (:status (server/handler {:uri "/xrpc/com.etzhayyim.apps.karma.nope"
                                         :request-method :post :body nil}))))))

(deftest server-start-requires-explicit-capability
  (is (thrown-with-msg? clojure.lang.ExceptionInfo
                        #"explicit HTTP server capability required"
                        (server/start! nil {:port 0}))))
