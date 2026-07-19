(ns lg-organism.smoke-test
  "Smoke tests for the lg-organism clj port — clojure.test analogue of the
  Python `lg/tests/test_smoke.py`, plus node/dispatch behaviour tests the
  original could not run offline (the kotodama workers + LLM are injectable
  seams here, so topology + swap + Murakumo guard verify under bb)."
  (:require [clojure.test :refer [deftest is testing]]
            [langgraph.graph :as g]
            [lg-organism.server :as server]
            [lg-organism.tasks :as tasks]
            [lg-organism.llm :as llm]
            [lg-organism.audit :as audit]))

(def expected-graphs
  #{"health"
    ;; hakkou
    "createFermentRecord" "llmTransform" "finalizeFerment"
    ;; kabi
    "anastomosisProbe"
    ;; ki
    "absorb" "synthesize" "bloom" "ring"
    ;; kinoko
    "checkFlowThreshold"
    ;; kobo
    "budAgent" "sporulate" "germinate"
    ;; koke
    "scanRawSignals" "fixSignal" "classifyFixation"
    "handoffToHakkou" "handoffToSaikin"
    ;; saikin
    "probeEnvironment" "transferSignal" "formColony" "lyse" "handoffToKi"})

;; ── registry parity (mirrors test_smoke.py) ─────────────────────────────────

(deftest graphs-match-expected-set
  (is (= expected-graphs (set (keys server/GRAPHS))))
  (is (= 23 (count server/GRAPHS)) "1 health + 22 organism tasks"))

(deftest nsid-map-references-known-graphs
  (doseq [[nsid assistant] server/NSID-MAP]
    (is (contains? server/GRAPHS assistant)
        (str nsid " → " assistant " not in GRAPHS"))))

(deftest nsid-map-completeness
  (is (= (inc (count tasks/*task-handlers*)) (count server/NSID-MAP))
      "every task NSID + the health NSID is mapped")
  (is (= "health" (get server/NSID-MAP "com.etzhayyim.apps.organism.health"))))

(deftest all-graphs-invocable
  (doseq [[nm graph] server/GRAPHS]
    (is (some? graph) (str "GRAPHS[" nm "] nil"))
    (is (map? (g/invoke graph {:input {}})) (str nm " not invocable"))))

(deftest nsid-last-segment
  (is (= "anastomosisProbe"
         (tasks/nsid->assistant "com.etzhayyim.apps.kabi.anastomosisProbe")))
  (is (= "absorb" (tasks/nsid->assistant "com.etzhayyim.ki.absorb"))))

;; ── endpoints (/ok, /health, /runs, /xrpc) ──────────────────────────────────

(deftest ok-endpoint-lists-graphs
  (let [r (server/ok)]
    (is (= 200 (:status r)))
    (is (true? (get-in r [:body :ok])))
    (is (= expected-graphs (set (get-in r [:body :graphs]))))))

(deftest health-endpoint
  (let [r (server/health)]
    (is (= 200 (:status r)))
    (is (= "ok" (get-in r [:body :status])))
    (is (= "lg-organism" (get-in r [:body :service])))))

(deftest unknown-assistant-404
  (is (= 404 (:status (server/dispatch-run {:assistant_id "nope" :input {}})))))

(deftest unmapped-xrpc-501
  ;; DEVIATION-NOTE: faithful to server.py, an UNMAPPED NSID returns 501
  ;; (the Python test_smoke.py asserts 404, which the deployed server does NOT
  ;; actually return — we mirror the runtime, not the aspirational test).
  (is (= 501 (:status (server/dispatch-xrpc "com.etzhayyim.ki.unknownMethod" {})))))

;; ── single-node graph topology + worker echo ────────────────────────────────

(deftest task-graph-topology-and-echo
  (let [out (g/invoke (server/GRAPHS "absorb") {:input {:seed 1}})]
    (is (= "stub-ok" (get-in out [:result :status])))
    (is (= "ki" (get-in out [:result :worker])))
    (is (= "absorb" (get-in out [:result :task])))
    (is (= {:seed 1} (get-in out [:result :input])))))

(deftest dispatch-run-task-happy-path
  (let [r (server/dispatch-run {:assistant_id "formColony" :input {:n 3}})]
    (is (= 200 (:status r)))
    (is (= "saikin" (get-in r [:body :output :worker])))
    (is (= "formColony" (get-in r [:body :output :task])))
    (is (number? (get-in r [:body :elapsed_s])))))

(deftest dispatch-run-defaults-to-health
  (let [r (server/dispatch-run {})]
    (is (= 200 (:status r)))
    (is (= "ok" (get-in r [:body :output :status])))))

(deftest dispatch-xrpc-maps-nsid
  (let [r (server/dispatch-xrpc "com.etzhayyim.koke.fixSignal" {:x 1})]
    (is (= 200 (:status r)))
    (is (= "koke" (get-in r [:body :output :worker])))
    (is (= "fixSignal" (get-in r [:body :output :task])))))

;; ── error path: handler throws → node merges :error → 500 ───────────────────

(deftest handler-exception-becomes-500
  (binding [tasks/*task-handlers*
            (assoc tasks/*task-handlers*
                   "com.etzhayyim.ki.bloom"
                   (fn [_in] (throw (ex-info "boom" {}))))]
    (let [r (server/dispatch-run {:assistant_id "bloom" :input {}})]
      (is (= 500 (:status r)))
      (is (re-find #"boom" (str (get-in r [:body :error])))))))

;; ── injectable task swap (actor seam) ───────────────────────────────────────

(deftest task-handler-swap
  (binding [tasks/*task-handlers*
            (assoc tasks/*task-handlers*
                   "com.etzhayyim.ki.ring"
                   (fn [in] {:status "swapped" :echo in}))]
    (let [r (server/dispatch-run {:assistant_id "ring" :input {:k :v}})]
      (is (= 200 (:status r)))
      (is (= "swapped" (get-in r [:body :output :status])))
      (is (= {:k :v} (get-in r [:body :output :echo]))))))

;; ── hakkou.llmTransform routes through the Murakumo LLM seam ─────────────────

(deftest llm-transform-uses-injectable-edge
  (binding [llm/*llm-chat* (fn [_sys user] (str "REPLY:" user))]
    (let [r (server/dispatch-run {:assistant_id "llmTransform"
                                  :input {:prompt "ferment this"}})]
      (is (= 200 (:status r)))
      (is (= "ok" (get-in r [:body :output :status])))
      (is (re-find #"REPLY:ferment this" (get-in r [:body :output :output]))))))

(deftest murakumo-fleet-guard
  (testing "off-fleet endpoint refused"
    (is (thrown? #?(:clj clojure.lang.ExceptionInfo :cljs :default)
                 (llm/assert-murakumo "https://api.openai.com/v1"))))
  (testing "malformed endpoint refused"
    (is (thrown? #?(:clj clojure.lang.ExceptionInfo :cljs :default)
                 (llm/assert-murakumo "not-a-url"))))
  (testing "loopback gateway allowed"
    (is (nil? (llm/assert-murakumo "http://127.0.0.1:4000/v1")))))

(deftest live-authority-requires-explicit-capabilities
  (is (thrown-with-msg? #?(:clj clojure.lang.ExceptionInfo :cljs :default)
                        #"explicit chat capability"
                        (llm/llm-chat "system" "user")))
  #?(:clj
     (is (thrown-with-msg? clojure.lang.ExceptionInfo
                           #"explicit run-server capability"
                           (server/start! nil 0)))))

(deftest injected-http-wire-contract
  #?(:clj
     (let [seen (atom nil)
           reply (llm/murakumo-llm-chat-with
                  (fn [url opts]
                    (reset! seen [url opts])
                    {:status 200
                     :body "{\"choices\":[{\"message\":{\"content\":\" safe \"}}]}"})
                  llm/default-config "system" "user")]
       (is (= "safe" reply))
       (is (= "http://127.0.0.1:4000/v1/chat/completions" (first @seen)))
       (is (= "application/json" (get-in @seen [1 :headers "Content-Type"])))
       (is (re-find #"\"model\"" (get-in @seen [1 :body]))))))

;; ── audit ledger seam ───────────────────────────────────────────────────────

(deftest audit-records-when-enabled
  (audit/reset-ledger!)
  (binding [tasks/*task-handlers* tasks/*task-handlers*]
    (binding [audit/*disabled?* false]
      (server/dispatch-run {:assistant_id "absorb" :input {}})
      (is (= 1 (count (audit/entries))))
      (is (= "absorb" (:assistant (first (audit/entries)))))
      (is (= "ok" (:status (first (audit/entries))))))))

(deftest audit-noop-when-disabled
  (audit/reset-ledger!)
  (binding [audit/*disabled?* true]
    (server/dispatch-run {:assistant_id "absorb" :input {}})
    (is (= 0 (count (audit/entries))))))
