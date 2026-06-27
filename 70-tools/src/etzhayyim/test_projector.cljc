;; etzhayyim.test-projector — projector MCP request/arg pure invariants (cljc port).
;; Run via the aggregate: bb test:helpers
;; Covers the pure MCP shapers (HTTP POST deferred): build-mcp-headers ·
;; build-mcp-request · unwrap-mcp-response · check-mcp-error · build-*-args.
(ns etzhayyim.test-projector
  (:require [clojure.test :refer [deftest is testing run-tests]]
            [etzhayyim.projector :as p]))

(deftest mcp-headers
  (is (= {"Content-Type" "application/json" "Authorization" "Bearer tok"}
         (p/build-mcp-headers "tok")))
  (is (= {"Content-Type" "application/json"} (p/build-mcp-headers nil)))
  (is (= {"Content-Type" "application/json"} (p/build-mcp-headers ""))))

(deftest mcp-request-shape
  (let [r (p/build-mcp-request "projector.create_project" {"name" "x"})]
    (is (= {:name "projector.create_project" :arguments {"name" "x"}} (:params r)))
    (is (some? (:jsonrpc r)))
    (is (some? (:method r)))))

(deftest unwrap-response
  (testing "content[0].text parsed as JSON"
    (is (= {"ok" true}
           (p/unwrap-mcp-response {"result" {"content" [{"text" "{\"ok\":true}"}]}}))))
  (testing "non-JSON text → {text}"
    (is (= {"text" "plain"}
           (p/unwrap-mcp-response {"result" {"content" [{"text" "plain"}]}}))))
  (testing "no content → result map itself"
    (is (= {"x" 1} (p/unwrap-mcp-response {"result" {"x" 1}})))))

(deftest check-error
  (testing "JSON-RPC error throws"
    (is (thrown? clojure.lang.ExceptionInfo
                 (p/check-mcp-error {"error" {"code" -1 "message" "boom"}}))))
  (testing "no error → returns data unchanged"
    (is (= {"result" {}} (p/check-mcp-error {"result" {}})))))

(deftest arg-builders
  (testing "create: required name, optionals only when present"
    (is (= {"name" "P"} (p/build-create-args {:name "P"})))
    (is (= {"name" "P" "orgId" "o" "description" "d"}
           (p/build-create-args {:name "P" :org-id "o" :description "d"}))))
  (testing "status: summarize coerced to boolean"
    (is (= {"projectId" "p1" "summarize" true} (p/build-status-args "p1" true)))
    (is (= {"projectId" "p1" "summarize" false} (p/build-status-args "p1" nil))))
  (testing "update: progress 0 is included (some?, not truthy)"
    (is (= {"projectId" "p" "progressPermille" 0} (p/build-update-args {:project-id "p" :progress 0}))))
  (testing "list: limit defaults to 20"
    (is (= {"limit" 20} (p/build-list-args {})))
    (is (= {"limit" 5 "orgId" "o" "lifecycleState" "active"}
           (p/build-list-args {:org-id "o" :state "active" :limit 5}))))
  (testing "blocker add: type/severity default"
    (is (= {"projectId" "p" "title" "t" "blockerType" "technical" "severity" "medium"}
           (p/build-blocker-add-args {:project-id "p" :title "t"})))
    (is (= "security" (get (p/build-blocker-add-args
                            {:project-id "p" :title "t" :blocker-type "security"}) "blockerType"))))
  (testing "blocker resolve: optional resolution"
    (is (= {"blockerId" "b"} (p/build-blocker-resolve-args {:blocker-id "b"})))
    (is (= {"blockerId" "b" "resolution" "fixed"}
           (p/build-blocker-resolve-args {:blocker-id "b" :resolution "fixed"})))))

(defn -main [& _]
  (let [{:keys [fail error]} (run-tests 'etzhayyim.test-projector)]
    (System/exit (if (pos? (+ fail error)) 1 0))))
