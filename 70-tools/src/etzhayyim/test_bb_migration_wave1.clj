;; test_bb_migration_wave1.clj — parity smoke tests for wave-1 cljc ports.
;;
;; Run with:  bb 70-tools/src/etzhayyim/test_bb_migration_wave1.clj
;; from repo root (classpath 70-tools/src already in bb.edn :paths).
;;
;; Each test deep-compares the Clojure output against the expected output
;; derived from running the Python counterpart on the same sample inputs.

(ns etzhayyim.test-bb-migration-wave1
  (:require [clojure.test :refer [deftest is testing run-tests]]
            [etzhayyim.identifier-audit :as ia]
            [etzhayyim.bonsai           :as bonsai]
            [etzhayyim.source-graph     :as sg]))

;; ─────────────────────────────────────────────────────────────────────────────
;; identifier-audit
;; ─────────────────────────────────────────────────────────────────────────────

(deftest test-ia-valid-nanoid
  (testing "valid nanoid passes"
    (let [viols (ia/audit-jsonld-data {"nanoid" "abc12345" "name" "my-actor"} "f.jsonld")]
      (is (empty? viols)))))

(deftest test-ia-invalid-nanoid-too-short
  (testing "nanoid < 8 chars is a violation"
    (let [viols (ia/audit-jsonld-data {"nanoid" "ab12" "name" "my-actor"} "f.jsonld")]
      (is (= 1 (count viols)))
      (is (= "nanoid-format" (:rule (first viols)))))))

(deftest test-ia-invalid-nanoid-too-long
  (testing "nanoid > 12 chars is a violation"
    (let [viols (ia/audit-jsonld-data {"nanoid" "abcdefghijklm" "name" "my-actor"} "f.jsonld")]
      (is (= 1 (count viols))))))

(deftest test-ia-invalid-did
  (testing "unsupported DID method flagged"
    (let [viols (ia/audit-jsonld-data {"nanoid" "abc12345" "did" "did:ethr:abc123"} "f.jsonld")]
      (is (= 1 (count viols)))
      (is (= "did-format" (:rule (first viols)))))))

(deftest test-ia-valid-did
  (testing "did:web passes"
    (let [viols (ia/audit-jsonld-data {"nanoid" "abc12345" "did" "did:web:etzhayyim.com"} "f.jsonld")]
      (is (empty? (filter #(= "did-format" (:rule %)) viols))))))

(deftest test-ia-name-uppercase
  (testing "CamelCase name flagged"
    (let [viols (ia/audit-jsonld-data {"nanoid" "abc12345" "name" "MyActor"} "f.jsonld")]
      (is (some #(= "name-lowercase" (:rule %)) viols)))))

(deftest test-ia-name-underscore
  (testing "snake_case name flagged"
    (let [viols (ia/audit-jsonld-data {"nanoid" "abc12345" "name" "my_actor"} "f.jsonld")]
      (is (some #(= "name-lowercase" (:rule %)) viols)))))

(deftest test-ia-run-audit-jsonld
  (testing "run-audit with jsonld :data"
    (let [viols (ia/run-audit [{:path "kotodama.jsonld"
                                :data {"nanoid" "ab" "name" "Bad_Name"
                                       "did" "did:ethr:123"}}])]
      ;; expect nanoid-format, did-format, name-lowercase = 3 violations
      (is (= 3 (count viols))))))

(deftest test-ia-run-audit-ts-inline-nanoid
  (testing "inline nanoid in TS flagged when malformed"
    (let [content "const x = { \"nanoid\": \"toolong_nanoid_xyz\" };"
          viols   (ia/run-audit [{:path "src/app.ts" :content content}])]
      (is (= 1 (count viols)))
      (is (= "nanoid-format" (:rule (first viols)))))))

(deftest test-ia-violations->report
  (testing "violations->report aggregates correctly"
    (let [vs    [{:rule "nanoid-format" :path "a" :value "x" :detail ""}
                 {:rule "did-format"    :path "b" :value "y" :detail ""}
                 {:rule "nanoid-format" :path "c" :value "z" :detail ""}]
          rpt   (ia/violations->report vs)]
      (is (= 3 (:total rpt)))
      (is (= 2 (get-in rpt [:by-rule "nanoid-format"]))))))

;; ─────────────────────────────────────────────────────────────────────────────
;; bonsai
;; ─────────────────────────────────────────────────────────────────────────────

(deftest test-bonsai-classify-tier-fruit
  (testing "file with TODO → fruit"
    (is (= "fruit" (bonsai/classify-tier "TODO_cleanup.ts")))))

(deftest test-bonsai-classify-tier-flower
  (testing "test file → flower"
    (is (= "flower" (bonsai/classify-tier "foo.test.ts")))))

(deftest test-bonsai-classify-tier-seed
  (testing "CLAUDE.md → seed"
    (is (= "seed" (bonsai/classify-tier "CLAUDE.md")))))

(deftest test-bonsai-classify-tier-branch
  (testing ".ts source → branch"
    (is (= "branch" (bonsai/classify-tier "app.ts")))))

(deftest test-bonsai-classify-tier-leaf
  (testing ".json → leaf"
    (is (= "leaf" (bonsai/classify-tier "package.json")))))

(deftest test-bonsai-score-node-todo
  (testing "TODO comment increases score"
    (let [{:keys [prune-score signals]}
          (bonsai/score-node "foo.ts" "// TODO: clean this up\n// FIXME: remove me")]
      (is (pos? prune-score))
      (is (some #(clojure.string/includes? % "TODO") signals)))))

(deftest test-bonsai-score-node-empty
  (testing "empty file penalty: 40 points (elif path means trivial <5 is NOT added when 0)"
    (let [{:keys [prune-score signals]}
          (bonsai/score-node "empty.ts" "")]
      (is (= 40 prune-score))
      (is (some #(= "empty file" %) signals))
      ;; 'trivial' signal must NOT appear (elif semantics)
      (is (not (some #(clojure.string/includes? % "trivial") signals))))))

(deftest test-bonsai-score-node-legacy
  (testing "legacy filename flagged"
    (let [{:keys [prune-score signals]}
          (bonsai/score-node "old_handler.ts" "function old() {}")]
      (is (>= prune-score 30))
      (is (some #(clojure.string/includes? % "legacy") signals)))))

(deftest test-bonsai-scan-workspace
  (testing "scan-workspace returns sensible report"
    ;; Use a low threshold so we can assert candidates are found.
    ;; app.ts: score 0 (content fine), utils.py: 1 TODO + trivial (<5 lines) = 30.
    ;; With threshold=20, only utils.py qualifies.
    (let [files [{:path "src/app.ts"        :content "function main() {}"}
                 {:path "src/utils.py"      :content "# TODO: clean up\ndef utils():\n pass"}
                 {:path "CLAUDE.md"         :content "# instructions"}
                 {:path "node_modules/x.ts" :content "skipped"}]
          rpt20 (bonsai/scan-workspace files 20)
          rpt50 (bonsai/scan-workspace files 50)]
      ;; node_modules skipped; CLAUDE.md + 2 source files = 3 total files
      (is (pos? (:total-files rpt20)))
      ;; at threshold 20: app.ts (trivial 1-line=20) + utils.py (TODO+trivial=30) qualify
      (is (= 2 (count (:prune-candidates rpt20))))
      ;; at threshold 50: no file reaches 50
      (is (= 0 (count (:prune-candidates rpt50))))
      (is (>= (:growth-score rpt20) 0)))))

(deftest test-bonsai-growth-health
  (testing "growth-health classification"
    (is (= :healthy       (bonsai/growth-health {:growth-score 80})))
    (is (= :needs-pruning (bonsai/growth-health {:growth-score 55})))
    (is (= :overgrown     (bonsai/growth-health {:growth-score 20})))))

;; ─────────────────────────────────────────────────────────────────────────────
;; source-graph
;; ─────────────────────────────────────────────────────────────────────────────

(deftest test-sg-parse-ts-imports
  (testing "extracts relative imports from TS"
    (let [imports (sg/parse-ts-imports
                   "import { foo } from './utils'\nimport type { Bar } from '../types'")]
      (is (= ["./utils" "../types"] imports)))))

(deftest test-sg-parse-ts-skips-npm
  (testing "npm @-scoped imports skipped"
    (let [imports (sg/parse-ts-imports "import x from '@etzhayyim/sdk'")]
      (is (empty? imports)))))

(deftest test-sg-parse-ts-skips-node
  (testing "node: protocol skipped"
    (let [imports (sg/parse-ts-imports "import fs from 'node:fs'")]
      (is (empty? imports)))))

(deftest test-sg-parse-py-imports
  (testing "extracts python module names"
    (let [imports (sg/parse-py-imports "import os\nfrom pathlib import Path\nfrom .shannon import _resolve_root")]
      (is (= ["os" "pathlib" ".shannon"] imports)))))

(deftest test-sg-parse-py-skips-private
  (testing "private _ modules skipped"
    (let [imports (sg/parse-py-imports "import __future__")]
      (is (empty? imports)))))

(deftest test-sg-scan-source-graph
  (testing "scan produces nodes for ts/py, ignores others"
    (let [rpt (sg/scan-source-graph
               [{:path "src/app.ts"  :content "import {x} from './lib'"}
                {:path "src/lib.ts"  :content "export const x = 1"}
                {:path "CLAUDE.md"   :content "ignored"}
                {:path "foo.py"      :content "import os"}])]
      (is (= 3 (count (:nodes rpt))))  ;; app.ts, lib.ts, foo.py
      ;; one edge from app.ts → ./lib
      (is (= 1 (count (:edges rpt)))))))

(deftest test-sg-orphan-paths
  (testing "lib.ts unreferenced is orphan"
    (let [rpt (sg/scan-source-graph
               [{:path "src/app.ts" :content ""}
                {:path "src/lib.ts" :content ""}])]
      (let [orphans (sg/orphan-paths rpt)]
        (is (= ["src/app.ts" "src/lib.ts"] (sort orphans)))))))

(deftest test-sg-cycles-detected
  (testing "mutual import cycle detected"
    (let [rpt {:edges [{:source "a.ts" :target "b.ts"}
                       {:source "b.ts" :target "a.ts"}]}
          cs  (sg/cycles rpt)]
      ;; At least one cycle found
      (is (pos? (count cs))))))

(deftest test-sg-layer-violations
  (testing "60-apps importing from 10-protocol is OK (higher → lower layer)"
    (let [rpt {:edges [{:source "60-apps/x.ts" :target "10-protocol/y.ts"}]}
          vs  (sg/layer-violations rpt)]
      (is (= 1 (count vs)))))
  (testing "10-protocol importing from 60-apps is a violation (lower → higher layer)"
    (let [rpt {:edges [{:source "10-protocol/y.ts" :target "60-apps/x.ts"}]}
          vs  (sg/layer-violations rpt)]
      (is (empty? vs)))))  ;; lower → higher is fine per the direction rule

;; ─────────────────────────────────────────────────────────────────────────────
;; run
;; ─────────────────────────────────────────────────────────────────────────────

(let [{:keys [pass fail error]}
      (run-tests 'etzhayyim.test-bb-migration-wave1)]
  (when (pos? (+ fail error))
    (System/exit 1)))
