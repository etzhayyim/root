;; etzhayyim.test-agent-cmd — agent-cmd pure request/response shaper invariants.
;; Run: bb test:agent-cmd
;; Covers the pure helpers (XRPC/subprocess legs take an injectable :http-fn/:proc-fn):
;; build-auth-headers · build-list-agents-url/-request · build-get-agent-request ·
;; build-stop-body/-agent-request · build-organism-status-request ·
;; build-git-toplevel-command · parse-list-response · parse-get-response.
(ns etzhayyim.test-agent-cmd
  (:require [clojure.test :refer [deftest is testing run-tests]]
            [etzhayyim.agent-cmd :as ac]))

(deftest auth-headers
  (is (= {"Authorization" "Bearer tok" "Content-Type" "application/json"}
         (ac/build-auth-headers "tok"))))

(deftest url-and-request-builders
  (testing "listAgents URL strips a trailing slash"
    (is (= "https://pds.example/xrpc/com.etzhayyim.agent.listAgents"
           (ac/build-list-agents-url "https://pds.example/")))
    (is (= "https://pds.example/xrpc/com.etzhayyim.agent.listAgents"
           (ac/build-list-agents-url "https://pds.example"))))
  (testing "list request: 2-arity defaults filters to {}, 3-arity passes them"
    (let [h {"Authorization" "Bearer t"}]
      (is (= {} (:params (ac/build-list-agents-request "https://p" h))))
      (is (= {:status "running"}
             (:params (ac/build-list-agents-request "https://p" h {:status "running"}))))
      (is (= :get (:method (ac/build-list-agents-request "https://p" h))))))
  (testing "getAgent puts the id in params"
    (is (= {"id" "a1"} (:params (ac/build-get-agent-request "https://p" {} "a1")))))
  (testing "stopAgent body + request"
    (is (= {"id" "a1"} (ac/build-stop-body "a1")))
    (let [r (ac/build-stop-agent-request "https://p/" {} "a1")]
      (is (= :post (:method r)))
      (is (= "https://p/xrpc/com.etzhayyim.agent.stopAgent" (:url r)))
      (is (= "{\"id\":\"a1\"}" (:body r)))))
  (testing "organism status request"
    (let [r (ac/build-organism-status-request "https://org/")]
      (is (= "https://org/status" (:url r)))
      (is (number? (:timeout r)))))
  (testing "git toplevel argv"
    (is (= ["git" "rev-parse" "--show-toplevel"] (ac/build-git-toplevel-command)))))

(deftest response-parsers
  (testing "list response: :agents > :rows, [] on garbage / empty"
    (is (= [{:id "a"}] (ac/parse-list-response "{\"agents\":[{\"id\":\"a\"}]}")))
    (is (= [1 2] (ac/parse-list-response "{\"rows\":[1,2]}")))
    (is (= [] (ac/parse-list-response "{}")))
    (is (= [] (ac/parse-list-response "not json"))))
  (testing "get response: parsed map or nil on garbage"
    (is (= {:id "a" :status "running"}
           (ac/parse-get-response "{\"id\":\"a\",\"status\":\"running\"}")))
    (is (nil? (ac/parse-get-response "<<garbage>>")))))

(defn -main [& _]
  (let [{:keys [fail error]} (run-tests 'etzhayyim.test-agent-cmd)]
    (System/exit (if (pos? (+ fail error)) 1 0))))
