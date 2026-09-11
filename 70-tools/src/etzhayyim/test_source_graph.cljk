;; etzhayyim.test-source-graph — source-graph pure invariants (cljc port).
;; Run via the aggregate: bb test:helpers
;; Covers the pure parse/graph helpers (file scanning is IO, deferred):
;; parse-ts-imports · parse-py-imports · orphan-paths · cycles · layer-violations.
(ns etzhayyim.test-source-graph
  (:require [clojure.test :refer [deftest is testing run-tests]]
            [etzhayyim.source-graph :as sg]))

(deftest ts-import-parsing
  (is (= ["./foo" "bar"]
         (sg/parse-ts-imports "import { a } from './foo';\nimport b from \"bar\";")))
  (testing "node:/bun:/@/http(s) specifiers are skipped"
    (is (= [] (sg/parse-ts-imports
               "import x from 'node:fs';\nimport y from '@scope/p';\nimport z from 'https://cdn/m';"))))
  (is (= [] (sg/parse-ts-imports ""))))

(deftest py-import-parsing
  (is (= ["os" "sys"] (sg/parse-py-imports "import os\nfrom sys import path")))
  (testing "private (underscore) modules are skipped"
    (is (= ["os"] (sg/parse-py-imports "import os\nimport _internal"))))
  (is (= [] (sg/parse-py-imports ""))))

(deftest orphan-paths-unreferenced
  (testing "a path that is neither source nor target of any edge is an orphan"
    (is (= ["c"]
           (sg/orphan-paths {:nodes [{:path "a"} {:path "b"} {:path "c"}]
                             :edges [{:source "a" :target "b"}]})))))

(deftest cycles-detection
  (testing "a → b → a is one cycle"
    (is (= 1 (count (sg/cycles {:edges [{:source "a" :target "b"}
                                        {:source "b" :target "a"}]})))))
  (testing "an acyclic graph has no cycles"
    (is (= [] (sg/cycles {:edges [{:source "a" :target "b"}]})))))

(deftest layer-violations-direction
  (testing "a higher-layer module importing a lower-layer one is a violation"
    (let [v (sg/layer-violations {:edges [{:source "70-tools/a.ts" :target "20-actors/b.ts"}]})]
      (is (= 1 (count v)))
      (is (= "70-tools" (:source-layer (first v))))
      (is (= "20-actors" (:target-layer (first v))))))
  (testing "a lower-layer module importing a higher-layer one is allowed"
    (is (= [] (sg/layer-violations {:edges [{:source "20-actors/a" :target "70-tools/b"}]}))))
  (testing "same-layer imports are not violations"
    (is (= [] (sg/layer-violations {:edges [{:source "70-tools/a" :target "70-tools/b"}]})))))

(defn -main [& _]
  (let [{:keys [fail error]} (run-tests 'etzhayyim.test-source-graph)]
    (System/exit (if (pos? (+ fail error)) 1 0))))
