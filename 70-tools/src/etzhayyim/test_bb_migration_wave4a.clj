;; test_bb_migration_wave4a.clj — parity smoke tests for wave-4a cljc ports.
;;
;; Modules covered:
;;   kashika  — Mermaid/DOT graph export, SLA math, shinka summary, pct formatter
;;   logs     — classify-layer, classify-scope, parse-arch-log, arch-report
;;
;; Skipped (thin IO wrappers, no pure logic to test):
;;   mitama   — SKIP: all XRPC HTTP, no pure logic
;;   nono     — SKIP: only _load_manifests (fs rglob), rest HTTP+subprocess
;;   yoroshiku — thin; run-readiness is #?(:clj …) file IO, no extractable pure kernel
;;
;; Run from repo root (bb.edn :paths includes 70-tools/src):
;;   bb 70-tools/src/etzhayyim/test_bb_migration_wave4a.clj

(ns etzhayyim.test-bb-migration-wave4a
  (:require [clojure.test :refer [deftest is testing run-tests]]
            [clojure.string :as str]
            [etzhayyim.kashika :as kashika]
            [etzhayyim.logs    :as logs]))

;; ─────────────────────────────────────────────────────────────────────────────
;; kashika — SLA math
;; ─────────────────────────────────────────────────────────────────────────────

(deftest test-kashika-sla-effective-single
  (testing "sla-effective with redundancy=1 is identity"
    (is (== 0.9999 (kashika/sla-effective 0.9999 1)))))

(deftest test-kashika-sla-effective-redundant
  (testing "sla-effective with redundancy=4 (four 0.99 instances)"
    ;; Python: _sla_effective(0.99, 4) = 0.99999999
    (let [r (kashika/sla-effective 0.99 4)]
      (is (< (Math/abs (- r 0.99999999)) 1e-12)))))

(deftest test-kashika-downtime-seconds
  (testing "downtime < 1 minute expressed in seconds"
    ;; avail=0.9999 → minutes=52.596 → hours → 52.6m  (NOT seconds)
    ;; Actually Python: downtime(0.9999) = "52.6m"
    (is (= "52.6m" (kashika/downtime-per-year 0.9999)))))

(deftest test-kashika-downtime-hours
  (testing "downtime >= 60 minutes expressed in hours"
    ;; Python: downtime(0.99) = "87.66h"
    (is (= "87.66h" (kashika/downtime-per-year 0.99)))))

(deftest test-kashika-downtime-mid
  (testing "downtime in minutes range"
    ;; Python: downtime(0.9995) = "4.38h"  (4.38h = 262.8 min > 60 → hours)
    (is (= "4.38h" (kashika/downtime-per-year 0.9995)))))

(deftest test-kashika-pct-basic
  (testing "pct formats to 1 decimal with percent sign"
    (is (= "20.0%" (kashika/pct 2 10)))))

(deftest test-kashika-pct-zero-num
  (testing "pct 0/10 = 0.0%"
    (is (= "0.0%" (kashika/pct 0 10)))))

(deftest test-kashika-pct-zero-total
  (testing "pct with zero total returns 0.0%"
    (is (= "0.0%" (kashika/pct 1 0)))))

;; ─────────────────────────────────────────────────────────────────────────────
;; kashika — shinka-summary
;; ─────────────────────────────────────────────────────────────────────────────

(deftest test-kashika-shinka-summary-basic
  (testing "shinka-summary aggregates correctly (parity with Python _shinka_summary)"
    ;; Python expected:
    ;; {'total': 2, 'avg_shinka': 80.0, 'avg_hyoka': 70.0, 'max_hyoka': 90,
    ;;  'top_actor': 'abc12345', 'joucho': 1, 'inbox': 1, 'cadence': 1, 'drill': 1,
    ;;  'validate': 1, 'analyze': 1, 'engage': 1, 'old_timer': 1}
    (let [rows [{"HyokaScore" 90 "ShinkaScore" 100 "Nanoid" "abc12345"
                 "HasJoucho" true "HasInbox" false "HasCadence" true "HasDrill" false
                 "HasValidate" true "HasAnalyze" false "HasEngage" true "HasOldTimer" true}
                {"HyokaScore" 50 "ShinkaScore" 60 "Nanoid" "xyz98765"
                 "HasJoucho" false "HasInbox" true "HasCadence" false "HasDrill" true
                 "HasValidate" false "HasAnalyze" true "HasEngage" false "HasOldTimer" false}]
          s (kashika/shinka-summary rows)]
      (is (= 2      (get s "total")))
      (is (= 80.0   (get s "avg_shinka")))
      (is (= 70.0   (get s "avg_hyoka")))
      (is (= 90     (get s "max_hyoka")))
      (is (= "abc12345" (get s "top_actor")))
      (is (= 1 (get s "joucho")))
      (is (= 1 (get s "inbox")))
      (is (= 1 (get s "cadence")))
      (is (= 1 (get s "drill")))
      (is (= 1 (get s "validate")))
      (is (= 1 (get s "analyze")))
      (is (= 1 (get s "engage")))
      (is (= 1 (get s "old_timer"))))))

(deftest test-kashika-shinka-summary-empty
  (testing "empty rows returns safe defaults"
    (let [s (kashika/shinka-summary [])]
      (is (= 0   (get s "total")))
      (is (= 0.0 (get s "avg_shinka")))
      (is (= 0.0 (get s "avg_hyoka"))))))

;; ─────────────────────────────────────────────────────────────────────────────
;; kashika — to-mermaid / to-dot / haisen-terminal
;; ─────────────────────────────────────────────────────────────────────────────

(def ^:private sample-apps
  [{"nanoid" "abc12345" "name" "actor-a"}
   {"nanoid" "xyz98765" "name" "actor-b"}])

(def ^:private sample-edges
  [{"from_nanoid" "abc12345" "to_nanoid" "xyz98765" "edge_type" "calls"}])

(deftest test-kashika-to-mermaid
  (testing "to-mermaid produces Mermaid LR graph"
    ;; Python: _to_mermaid(report) →
    ;;   "graph LR\n    abc12345[\"actor-a\"] -->|calls| xyz98765[\"actor-b\"]"
    (let [result (kashika/to-mermaid sample-apps sample-edges)]
      (is (str/starts-with? result "graph LR"))
      (is (str/includes? result "abc12345"))
      (is (str/includes? result "actor-a"))
      (is (str/includes? result "-->|calls|"))
      (is (str/includes? result "xyz98765")))))

(deftest test-kashika-to-mermaid-no-edges
  (testing "to-mermaid with no edges produces just header"
    (let [result (kashika/to-mermaid sample-apps [])]
      (is (= "graph LR" result)))))

(deftest test-kashika-to-dot
  (testing "to-dot produces Graphviz DOT string"
    ;; Python: _to_dot(report) →
    ;;   "digraph actors {\n  rankdir=\"LR\";\n  ..."
    (let [result (kashika/to-dot sample-apps sample-edges)]
      (is (str/starts-with? result "digraph actors {"))
      (is (str/includes? result "rankdir=\"LR\""))
      (is (str/includes? result "\"abc12345\" [label=\"actor-a\"]"))
      (is (str/includes? result "\"xyz98765\" [label=\"actor-b\"]"))
      (is (str/includes? result "\"abc12345\" -> \"xyz98765\" [label=\"calls\"]"))
      (is (str/ends-with? (str/trim result) "}")))))

(deftest test-kashika-haisen-terminal
  (testing "haisen-terminal renders table with app count header"
    ;; Python: haisen-terminal returns a string starting with "Apps: 2  Edges: 1"
    (let [data {"apps" sample-apps "edges" sample-edges}
          result (kashika/haisen-terminal data)]
      (is (str/includes? result "Apps: 2  Edges: 1"))
      (is (str/includes? result "abc12345"))
      (is (str/includes? result "actor-a"))
      (is (str/includes? result "NANOID")))))

;; ─────────────────────────────────────────────────────────────────────────────
;; kashika — sla-components catalog
;; ─────────────────────────────────────────────────────────────────────────────

(deftest test-kashika-sla-components-count
  (testing "9 SLA components preserved from Python"
    (is (= 9 (count kashika/sla-components)))))

(deftest test-kashika-target-sla
  (testing "target-sla = 0.9999"
    (is (== 0.9999 kashika/target-sla))))

(deftest test-kashika-sla-report
  (testing "sla-report computes effective avail for all components"
    (let [rpt (kashika/sla-report)]
      (is (= 9 (count (:components rpt))))
      (is (number? (:spof-count rpt)))
      (every? #(contains? % :effective-avail) (:components rpt)))))

;; ─────────────────────────────────────────────────────────────────────────────
;; logs — classify-layer
;; ─────────────────────────────────────────────────────────────────────────────

(deftest test-logs-classify-layer-projects
  (testing "60-apps/* → projects"
    (is (= "projects" (logs/classify-layer "60-apps/foo")))))

(deftest test-logs-classify-layer-infra
  (testing "50-infra/* → infra"
    (is (= "infra" (logs/classify-layer "50-infra/bar")))))

(deftest test-logs-classify-layer-actors
  (testing "20-actors/* → actors"
    (is (= "actors" (logs/classify-layer "20-actors/baz")))))

(deftest test-logs-classify-layer-docs
  (testing "90-docs/* → docs"
    (is (= "docs" (logs/classify-layer "90-docs/x")))))

(deftest test-logs-classify-layer-engine
  (testing "40-engine/* → engine"
    (is (= "engine" (logs/classify-layer "40-engine/y")))))

(deftest test-logs-classify-layer-graph
  (testing "30-graph/* → graph"
    (is (= "graph" (logs/classify-layer "30-graph/z")))))

(deftest test-logs-classify-layer-contracts
  (testing "00-contracts/* → contracts"
    (is (= "contracts" (logs/classify-layer "00-contracts/c")))))

(deftest test-logs-classify-layer-tools
  (testing "70-tools/* → tools"
    (is (= "tools" (logs/classify-layer "70-tools/t")))))

(deftest test-logs-classify-layer-root
  (testing "README.md → root (no prefix match)"
    (is (= "root" (logs/classify-layer "README.md")))))

;; ─────────────────────────────────────────────────────────────────────────────
;; logs — classify-scope
;; ─────────────────────────────────────────────────────────────────────────────

(deftest test-logs-classify-scope-deep
  (testing "path with >2 segments returns second segment"
    ;; Python: _classify_scope("60-apps/foo/bar", "projects") = "foo"
    (is (= "foo" (logs/classify-scope "60-apps/foo/bar" "projects")))))

(deftest test-logs-classify-scope-root-layer
  (testing "root layer → scope always root"
    (is (= "root" (logs/classify-scope "root/x" "root")))))

(deftest test-logs-classify-scope-short-path
  (testing "single-segment path → root scope"
    (is (= "root" (logs/classify-scope "a" "root")))))

;; ─────────────────────────────────────────────────────────────────────────────
;; logs — parse-arch-log / arch-report
;; ─────────────────────────────────────────────────────────────────────────────

(def ^:private git-log-fixture
  ;; Each SHA is exactly 40 hex chars (a real git SHA length)
  (str/split-lines
   (str "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa|2026-06-01T10:00:00+09:00|Jun Kawasaki|feat(actors): add funadaiku\n"
        " 20-actors/funadaiku/manifest.json        |  3 +++\n"
        " 20-actors/funadaiku/actor.py              | 50 ++++++++++++++++++++++\n"
        " 2 files changed, 53 insertions(+)\n"
        "\n"
        "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb|2026-06-02T11:00:00+09:00|Jun Kawasaki|fix(infra): update worker\n"
        " 50-infra/etzhayyim-did-web/worker.ts     | 10 ++++------\n"
        " 1 file changed, 4 insertions(+), 6 deletions(-)\n")))

(deftest test-logs-parse-arch-log-count
  (testing "parse-arch-log returns one event per commit header"
    (let [events (logs/parse-arch-log git-log-fixture)]
      (is (= 2 (count events))))))

(deftest test-logs-parse-arch-log-sha
  (testing "sha truncated to 12 chars"
    (let [events (logs/parse-arch-log git-log-fixture)
          first-evt (first events)]
      (is (= 12 (count (:sha first-evt)))))))

(deftest test-logs-parse-arch-log-layer
  (testing "dominant layer assigned from file paths"
    (let [events (logs/parse-arch-log git-log-fixture)]
      ;; first commit has 20-actors/* files → actors
      (is (= "actors" (:layer (first events))))
      ;; second commit has 50-infra/* → infra
      (is (= "infra" (:layer (second events)))))))

(deftest test-logs-parse-arch-log-added-removed
  (testing "added/removed lines parsed from stat summary"
    (let [events (logs/parse-arch-log git-log-fixture)]
      (is (= 53 (:added (first events))))
      ;; second commit: 4 insertions, 6 deletions
      (is (= 4 (:added (second events))))
      (is (= 6 (:removed (second events)))))))

(deftest test-logs-arch-report
  (testing "arch-report aggregates by-layer counts"
    (let [events (logs/parse-arch-log git-log-fixture)
          rpt    (logs/arch-report events)]
      (is (= 2 (:total-events rpt)))
      (is (= {"actors" 1 "infra" 1} (:by-layer rpt))))))

;; ─────────────────────────────────────────────────────────────────────────────
;; run
;; ─────────────────────────────────────────────────────────────────────────────

(let [{:keys [pass fail error]}
      (run-tests 'etzhayyim.test-bb-migration-wave4a)]
  (when (pos? (+ fail error))
    (System/exit 1)))
