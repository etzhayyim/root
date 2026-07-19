(ns tests.test-smoke
  "Smoke tests for the lg-chat clj port — graph compiles, tools import + run
  (no network / LLM key required). clj port of tests/test_smoke.py."
  (:require [clojure.test :refer [deftest is]]
            [clojure.string :as str]
            [lg-chat.graphs.agent-chat :as ac]
            [lg-chat.tools :as tools]))

(deftest graph-compiles
  (let [graph ac/GRAPH
        node-names (-> graph :graph :nodes keys set)]
    (is (some? graph))
    (is (contains? node-names :prepare))
    (is (>= (count node-names) 3))))

(deftest tools-import
  (is (= 6 (count tools/TOOL-SCHEMAS)))
  (let [tool-names (set (map #(get-in % [:function :name]) tools/TOOL-SCHEMAS))]
    (is (= #{"code_exec" "image_gen" "file_save" "rag_search" "web_search" "schedule_report"}
           tool-names)))
  ;; dispatch-tool returns an error for unknown tools
  (is (false? (:ok (tools/dispatch-tool "__unknown__" {})))))

(deftest code-exec-tool
  (let [result (tools/tool-code-exec {"code" "print('hello from lg-chat')"})]
    (is (true? (:ok result)))
    (is (str/includes? (:stdout result) "hello from lg-chat"))))

(deftest code-exec-timeout
  (let [result (tools/tool-code-exec {"code" "import time; time.sleep(100)" "timeoutSec" 2})]
    (is (false? (:ok result)))
    (is (str/includes? (:error result) "timeout"))))

(deftest prepare-node
  ;; node-prepare builds the messages list with the system prompt + user turn
  (let [out (ac/node-prepare {:message "こんにちは" :history [{:role "user" :content "前"}]})]
    (is (= 0 (:iteration out)))
    (is (= "system" (:role (first (:messages out)))))
    (is (= "こんにちは" (:content (last (:messages out)))))))

(deftest explicit-host-config-controls-history
  (let [out (ac/node-prepare {:history [{:role "user" :content "drop"}
                                        {:role "assistant" :content "keep"}]
                              :host-config {:max-history 1}})]
    (is (= ["system" "assistant"] (mapv :role (:messages out))))))

(deftest tools-fail-closed-without-host-capabilities
  (is (false? (:ok (tools/tool-file-save {}))))
  (is (str/includes? (:error (tools/tool-schedule-report {})) "not configured")))

(deftest route-terminates-on-reply
  (is (= :langgraph/end (ac/route-after-llm {:reply "done" :messages []})))
  (is (= :langgraph/end (ac/route-after-llm {:iteration 99 :messages []})))
  (is (= :execute-tools
         (ac/route-after-llm {:messages [{:role "assistant" :tool_calls [{:id "x"}]}]}))))
