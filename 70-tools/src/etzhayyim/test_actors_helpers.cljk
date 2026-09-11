;; etzhayyim.test-actors-helpers — actors pure-helper invariants (cljc port).
;; Run: bb test:actors
;; Covers the pure helpers (XRPC/Ollama/Murakumo legs take an injectable :http-fn):
;; sanitize-path · stable-rkey · build-prompt · parse-result · score-jokyo.
(ns etzhayyim.test-actors-helpers
  (:require [clojure.test :refer [deftest is testing run-tests]]
            [etzhayyim.actors :as actors]))

(deftest sanitize-path-slug
  (is (= "hello-world" (actors/sanitize-path "Hello World")))
  (is (= "ab-c" (actors/sanitize-path "a/b c")))         ;; '/' dropped, space → '-'
  (is (= "foobar" (actors/sanitize-path "Foo_Bar")))     ;; '_' dropped, lower-cased
  (is (= "x123" (actors/sanitize-path "x123"))))

(deftest stable-rkey-sha256
  (testing "16 lowercase hex chars, deterministic, key-sensitive"
    (let [k (actors/stable-rkey "at://did/coll/self")]
      (is (re-matches #"[0-9a-f]{16}" k))
      (is (= k (actors/stable-rkey "at://did/coll/self")))
      (is (not= k (actors/stable-rkey "at://did/coll/other"))))))

(deftest build-prompt-includes-identity
  (let [p (actors/build-prompt {:nanoid "n1" :handle "a.example"
                                :display-name "Alpha" :description "does things"})]
    (is (string? p))
    (is (re-find #"n1" p))
    (is (re-find #"Alpha" p))
    (is (re-find #"EXPERTISE_IN" p))))

(deftest score-jokyo-bands
  (is (= {:total-score 100 :grade "S"}
         (actors/score-jokyo {:health-ok true :heartbeat-ok true :health-ms 100 :heartbeat-ms 100})))
  (is (= {:total-score 80 :grade "A"}
         (actors/score-jokyo {:health-ok true :heartbeat-ok true :health-ms 300 :heartbeat-ms 600})))
  (is (= {:total-score 40 :grade "C"}
         (actors/score-jokyo {:health-ok true :heartbeat-ok false :health-ms 300 :heartbeat-ms 600})))
  (is (= {:total-score 0 :grade "D"}
         (actors/score-jokyo {:health-ok false :heartbeat-ok false :health-ms 999 :heartbeat-ms 999}))))

(deftest parse-result-extracts-json
  (testing "valid JSON block → structured result (sub-did path sanitized, edge from defaults to nanoid)"
    (let [r (actors/parse-result
             {:did "did:x" :nanoid "n1"}
             (str "noise {\"domain_summary\":\"sum\","
                  "\"sub_dids\":[{\"path\":\"My Path\",\"display_name\":\"d\",\"description\":\"desc\"}],"
                  "\"knowledge_edges\":[{\"relation\":\"SERVES\",\"to\":\"users\"}]} trailing"))]
      (is (= "" (:error r)))
      (is (= "sum" (:domain-summary r)))
      (is (= [{:path "my-path" :display-name "d" :description "desc"}] (:sub-dids r)))
      (is (= [{:from "n1" :relation "SERVES" :to "users"}] (:knowledge-edges r)))))
  (testing "no JSON in the response → error + empty fields"
    (let [r (actors/parse-result {:did "d" :nanoid "n"} "no json here")]
      (is (= "no JSON in LLM response" (:error r)))
      (is (= [] (:sub-dids r))))))

(defn -main [& _]
  (let [{:keys [fail error]} (run-tests 'etzhayyim.test-actors-helpers)]
    (System/exit (if (pos? (+ fail error)) 1 0))))
