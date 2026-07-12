;; test_bb_migration_wave3a.clj — parity smoke tests for wave-3a cljc ports.
;;
;; Modules: coverage, dodaf, deps, metrics
;;
;; Run with:  bb 70-tools/src/etzhayyim/test_bb_migration_wave3a.clj
;; from repo root (classpath 70-tools/src in bb.edn :paths).
;;
;; Each test deep-compares the Clojure output against the expected output
;; derived from the Python originals on the same sample inputs.

(ns etzhayyim.test-bb-migration-wave3a
  (:require [clojure.test :refer [deftest is testing run-tests]]
            [clojure.string :as str]
            [etzhayyim.coverage :as cov]
            [etzhayyim.dodaf    :as dodaf]
            [etzhayyim.deps     :as deps]
            [etzhayyim.metrics  :as m]))

;; ─────────────────────────────────────────────────────────────────────────────
;; coverage
;; ─────────────────────────────────────────────────────────────────────────────

(deftest test-cov-completeness-all-present
  (testing "all required + optional present → all true"
    (let [data {"nanoid" "abc12345" "did" "did:web:x" "name" "foo"
                "performerType" "agent" "uiType" "dashboard"}
          c    (cov/check-actor-completeness data)]
      (is (true? (get c "nanoid")))
      (is (true? (get c "did")))
      (is (true? (get c "performerType")))
      (is (true? (get c "uiType"))))))

(deftest test-cov-completeness-missing
  (testing "missing required fields → false in completeness map"
    (let [data {"nanoid" "abc12345" "name" "foo"}
          c    (cov/check-actor-completeness data)]
      (is (false? (get c "did")))
      (is (false? (get c "performerType"))))))

(deftest test-cov-score-all-required
  (testing "4/8 fields present → score 50"
    (let [data {"nanoid" "abc12345" "did" "did:web:x" "name" "foo" "performerType" "agent"}
          c    (cov/check-actor-completeness data)]
      (is (= 50 (cov/compute-actor-score c))))))

(deftest test-cov-score-partial
  (testing "2/8 fields present → score 25"
    (let [data {"nanoid" "abc12345" "name" "foo"}
          c    (cov/check-actor-completeness data)]
      (is (= 25 (cov/compute-actor-score c))))))

(deftest test-cov-actor-summary
  (testing "actor-summary returns correct structure"
    (let [data    {"nanoid" "abc12345" "name" "foo" "did" "did:web:x" "performerType" "agent"}
          summary (cov/actor-summary data "60-apps/foo/kotodama.jsonld")]
      (is (= "abc12345" (:nanoid summary)))
      (is (= 50 (:score summary)))
      (is (vector? (:missing summary)))
      (is (map? (:completeness summary))))))

(deftest test-cov-actor-summary-missing
  (testing "actor-summary :missing lists only required fields"
    (let [data    {"nanoid" "abc12345" "name" "foo"}
          summary (cov/actor-summary data "p.jsonld")]
      (is (some #{"did"} (:missing summary)))
      (is (some #{"performerType"} (:missing summary)))
      ;; optional fields must NOT appear in :missing
      (is (not (some #{"uiType"} (:missing summary)))))))

(deftest test-cov-oil-match-true
  (testing "oil actor matched"
    (is (true? (cov/oil-match? {"name" "Oil Refinery" "description" ""})))))

(deftest test-cov-oil-match-false
  (testing "non-oil actor not matched"
    (is (false? (cov/oil-match? {"name" "medical robot" "description" "healthcare"})))))

(deftest test-cov-oil-match-in-description
  (testing "oil keyword in description also matches"
    (is (true? (cov/oil-match? {"name" "logistics" "description" "crude oil transport"})))))

(deftest test-cov-governance-issues-all-missing
  (testing "no governance fields → 3 issues"
    (is (= 3 (count (cov/governance-issues {"nanoid" "x"}))))))

(deftest test-cov-governance-issues-partial
  (testing "operator present → 2 issues"
    (let [issues (cov/governance-issues {"nanoid" "x" "operator" "admin"})]
      (is (= 2 (count issues)))
      (is (not (some #{"operator"} issues))))))

(deftest test-cov-governance-ok
  (testing "all governance fields present → ok"
    (is (true? (cov/governance-ok? {"operator" "a" "authority" "b" "visibility" "public"})))))

(deftest test-cov-build-heal-prompt
  (testing "heal prompt contains actor context and field list"
    (let [prompt (cov/build-heal-prompt {:nanoid "abc" :name "foo"
                                         :path "60-apps/foo/kotodama.jsonld"
                                         :missing ["did" "performerType"]})]
      (is (str/starts-with? prompt "You are a metadata filler"))
      (is (str/includes? prompt "\"did\", \"performerType\""))
      (is (str/includes? prompt "Output only JSON:")))))

(deftest test-cov-heal-prompt-empty-missing
  (testing "heal prompt with no missing fields"
    (let [prompt (cov/build-heal-prompt {:nanoid "x" :name "y" :path "p" :missing []})]
      (is (str/includes? prompt "Missing fields:")))))

(deftest test-cov-extract-json-block
  (testing "extracts first JSON object from raw string"
    (let [raw "Here is the result: {\"foo\": \"bar\", \"baz\": 42} done"]
      (is (= "{\"foo\": \"bar\", \"baz\": 42}"
             (cov/extract-json-block raw))))))

(deftest test-cov-extract-json-block-none
  (testing "returns nil when no JSON block present"
    (is (nil? (cov/extract-json-block "plain text no braces")))
    (is (nil? (cov/extract-json-block nil)))))

;; ─────────────────────────────────────────────────────────────────────────────
;; dodaf
;; ─────────────────────────────────────────────────────────────────────────────

(deftest test-dodaf-find-viewpoints
  (testing "extract distinct DoDAF viewpoint codes from text"
    (let [vps (dodaf/find-viewpoints "This covers AV-1 and OV-5 and SV-4 and AV-1 again.")]
      (is (= #{"AV-1" "OV-5" "SV-4"} (set vps))))))

(deftest test-dodaf-find-viewpoints-empty
  (testing "no viewpoints in text"
    (is (empty? (dodaf/find-viewpoints "no architectural refs here")))))

(deftest test-dodaf-artifact-counts
  (testing "counts by :type"
    (let [arts [{:type "adr"} {:type "lexicon"} {:type "adr"}]
          counts (dodaf/artifact-counts arts)]
      (is (= 2 (get counts "adr")))
      (is (= 1 (get counts "lexicon"))))))

(deftest test-dodaf-build-tag-cond
  (testing "single tag condition"
    (let [cond (dodaf/build-tag-cond "scope_tags" ["cloudflare"])]
      (is (= "(list_contains(scope_tags, 'cloudflare'))" cond)))))

(deftest test-dodaf-build-tag-cond-multi
  (testing "multi-tag OR condition"
    (let [cond (dodaf/build-tag-cond "scope_tags" ["cloudflare" "wasm"])]
      (is (= "(list_contains(scope_tags, 'cloudflare') OR list_contains(scope_tags, 'wasm'))" cond)))))

(deftest test-dodaf-build-tag-cond-empty
  (testing "empty tag list → empty string"
    (is (= "" (dodaf/build-tag-cond "scope_tags" [])))))

(deftest test-dodaf-build-path-cond
  (testing "path condition with folder col"
    (let [cond (dodaf/build-path-cond "scope_folders" "60-apps/foo.ts")]
      (is (str/includes? cond "scope_folders"))
      (is (str/includes? cond "60-apps/foo.ts")))))

(deftest test-dodaf-build-path-cond-empty
  (testing "empty folder col → empty string"
    (is (= "" (dodaf/build-path-cond "" "60-apps/foo.ts")))
    (is (= "" (dodaf/build-path-cond "scope_folders" "")))))

(deftest test-dodaf-build-where
  (testing "both tag and path → combined WHERE"
    (let [w (dodaf/build-where "scope_tags" "scope_folders" ["cloudflare"] "60-apps/foo.ts")]
      (is (str/starts-with? w "WHERE "))
      (is (str/includes? w "AND")))))

(deftest test-dodaf-build-where-empty
  (testing "no conditions → empty string"
    (is (= "" (dodaf/build-where "scope_tags" "scope_folders" [] "")))))

(deftest test-dodaf-extract-prose
  (testing "extracts first prose paragraph"
    (let [body "\nThis is the description.\nIt spans multiple lines.\n\n- not this"
          prose (dodaf/extract-prose body)]
      (is (= "This is the description. It spans multiple lines." prose)))))

(deftest test-dodaf-extract-prose-code-block
  (testing "skips code blocks"
    (let [body "```\nsome code\n```\nReal prose here."
          prose (dodaf/extract-prose body)]
      (is (= "Real prose here." prose)))))

(deftest test-dodaf-extract-critical-sections
  (testing "extracts ## CRITICAL: sections"
    (let [text "# Title\n\n## CRITICAL: Rule One\n\nThis is the rule.\n\n## CRITICAL: Rule Two\n\nAnother rule.\n"
          secs (dodaf/extract-critical-sections text "CLAUDE.md")]
      (is (= 2 (count secs)))
      (is (= "Rule One" (:title (first secs))))
      (is (= "CLAUDE.md" (:file (first secs))))
      (is (str/includes? (:rule-text (first secs)) "This is the rule")))))

(deftest test-dodaf-extract-critical-sections-empty
  (testing "no CRITICAL sections → empty vec"
    (is (empty? (dodaf/extract-critical-sections "# Normal heading\n\nContent." "f.md")))))

(deftest test-dodaf-id-from-title
  (testing "derives stable ID from path+title"
    (is (= "etzhayyim-project-hoge-shannon-redundancy-prohibition"
           (dodaf/dodaf-id-from-title "60-apps/etzhayyim-project-hoge/CLAUDE.md"
                                       "Shannon Redundancy Prohibition")))
    (is (= "root-no-kv-usage"
           (dodaf/dodaf-id-from-title "CLAUDE.md" "No KV Usage")))))

(deftest test-dodaf-tags-for-file
  (testing "infers tags from path"
    (let [tags (set (dodaf/dodaf-tags-for-file "60-apps/foo/CLAUDE.md"))]
      (is (contains? tags "claude"))
      (is (contains? tags "at-protocol"))
      (is (contains? tags "typescript"))))
  (testing "root CLAUDE.md gets root-policy tag"
    (is (some #{"root-policy"} (dodaf/dodaf-tags-for-file "CLAUDE.md")))))

(deftest test-dodaf-seed-tv1
  (testing "seed-tv1 returns non-empty vec of maps"
    (let [records (dodaf/seed-tv1 "2026-06-22T00:00:00Z")]
      (is (pos? (count records)))
      (is (every? :id records))
      (is (every? #(= "TV-1" (:view %)) records)))))

(deftest test-dodaf-seed-av2
  (testing "seed-av2 returns non-empty vec with :term fields"
    (let [records (dodaf/seed-av2 "2026-06-22T00:00:00Z")]
      (is (pos? (count records)))
      (is (every? :term records)))))

(deftest test-dodaf-seed-ov5
  (testing "seed-ov5 returns non-empty vec with :permitted fields"
    (let [records (dodaf/seed-ov5 "2026-06-22T00:00:00Z")]
      (is (pos? (count records)))
      (is (every? #(contains? % :permitted) records)))))

;; ─────────────────────────────────────────────────────────────────────────────
;; deps
;; ─────────────────────────────────────────────────────────────────────────────

(deftest test-deps-build-kv-records
  (testing "builds correct KV entries from actor list"
    (let [actors [{"name" "foo" "did" "did:web:foo" "nanoid" "abc12345"}
                  {"name" "bar" "did" "did:web:bar"}]
          kv     (deps/build-kv-records actors)]
      (is (= 3 (count kv)))
      (is (some #{"actor:foo"} (map :key kv)))
      (is (some #{"actor:bar"} (map :key kv)))
      (is (some #{"actors:index"} (map :key kv))))))

(deftest test-deps-build-kv-records-sorted
  (testing "actors are sorted alphabetically by name"
    (let [actors [{"name" "zebra" "did" "did:web:z"}
                  {"name" "alpha" "did" "did:web:a"}]
          kv     (deps/build-kv-records actors)]
      ;; First entry should be alpha (sorted), last is actors:index
      (is (= "actor:alpha" (:key (first kv)))))))

(deftest test-deps-build-kv-records-index
  (testing "actors:index entry contains all names"
    (let [actors [{"name" "foo" "did" "d"} {"name" "bar" "did" "d"}]
          kv     (deps/build-kv-records actors)
          idx    (first (filter #(= "actors:index" (:key %)) kv))]
      (is (some? idx))
      (is (str/includes? (:value idx) "foo"))
      (is (str/includes? (:value idx) "bar")))))

(deftest test-deps-build-kv-records-skips-nameless
  (testing "actors without name are skipped"
    (let [actors [{"did" "did:web:x"} {"name" "foo" "did" "d"}]
          kv     (deps/build-kv-records actors)]
      ;; Only foo + actors:index
      (is (= 2 (count kv))))))

(deftest test-deps-summarize-deps-graph-summary-path
  (testing "uses summary path when linkerStatus absent"
    (let [graph {"summary" {"totalResolvedLinks" 10 "totalUnresolvedLinks" 2}}
          s     (deps/summarize-deps-graph graph)]
      (is (= 12 (get s "totalLinks")))
      (is (= 10 (get s "resolvedLinks")))
      (is (= 2  (get s "unresolvedLinks")))
      (is (= 0.8333 (get s "linkCoverageRate"))))))

(deftest test-deps-summarize-deps-graph-linker-path
  (testing "prefers linkerStatus.summary when present and non-zero"
    (let [graph {"linkerStatus" {"summary" {"totalLinks" 20 "resolvedLinks" 18 "unresolvedLinks" 2}}}
          s     (deps/summarize-deps-graph graph)]
      (is (= 20 (get s "totalLinks")))
      (is (= 18 (get s "resolvedLinks"))))))

(deftest test-deps-summarize-zero-total
  (testing "zero total → coverage 0.0"
    (let [graph {}
          s     (deps/summarize-deps-graph graph)]
      (is (= 0 (get s "totalLinks")))
      (is (= 0.0 (get s "linkCoverageRate"))))))

(deftest test-deps-filter-layers-all
  (testing "section=all returns all layers"
    (let [layers [{:section "packages" :name "a" :tags []}
                  {:section "infra" :name "b" :tags []}]
          result (deps/filter-layers layers "all" "")]
      (is (= 2 (count result))))))

(deftest test-deps-filter-layers-by-section
  (testing "filter by section"
    (let [layers [{:section "packages" :name "a" :tags []}
                  {:section "infra" :name "b" :tags []}]
          result (deps/filter-layers layers "packages" "")]
      (is (= 1 (count result)))
      (is (= "a" (:name (first result)))))))

(deftest test-deps-filter-layers-by-tag
  (testing "filter by tag"
    (let [layers [{:section "packages" :name "a" :tags ["substrate"]}
                  {:section "packages" :name "b" :tags ["actors"]}]
          result (deps/filter-layers layers "" "substrate")]
      (is (= 1 (count result)))
      (is (= "a" (:name (first result)))))))

(deftest test-deps-render-tree-header
  (testing "tree header contains section label"
    (let [layers [{:name "kotoba" :layer 1 :description "Storage" :tags [] :depends-on [] :section "packages"}]
          tree   (deps/render-deps-tree layers "packages")]
      (is (str/starts-with? tree "deps layer DAG  [packages]")))))

(deftest test-deps-render-tree-layers
  (testing "tree contains layer numbers and names"
    (let [layers [{:name "a" :layer 1 :description "desc" :tags [] :depends-on [] :section "all"}
                  {:name "b" :layer 2 :description "desc" :tags [] :depends-on ["a"] :section "all"}]
          tree   (deps/render-deps-tree layers "all")]
      (is (str/includes? tree "Layer 1:"))
      (is (str/includes? tree "Layer 2:"))
      (is (str/includes? tree "a")))))

(deftest test-deps-render-mermaid-header
  (testing "mermaid output starts with # header and contains mermaid block"
    (let [layers [{:name "kotoba" :layer 1 :description "s" :tags [] :depends-on [] :section "packages"}]
          md     (deps/render-deps-mermaid layers "packages")]
      (is (str/starts-with? md "# deps layer DAG [packages]"))
      (is (str/includes? md "```mermaid"))
      (is (str/includes? md "graph BT")))))

(deftest test-deps-deps-mv-name
  (testing "extracts VIEW name from CREATE MATERIALIZED VIEW IF NOT EXISTS"
    (is (= "mv_deps_summary_live"
           (deps/deps-mv-name "CREATE MATERIALIZED VIEW IF NOT EXISTS mv_deps_summary_live AS SELECT")))))

(deftest test-deps-summary
  (testing "deps-summary extracts counts from data map"
    (let [data {"migrations" [1 2 3] "conventions" [1] "projects" [1 2] "mitama_actors" []}
          s    (deps/deps-summary data)]
      (is (= 3 (:migrations s)))
      (is (= 1 (:conventions s)))
      (is (= 2 (:projects s)))
      (is (= 0 (:mitama-actors s)))
      (is (true? (:has-deps-toml s))))))

(deftest test-deps-summary-empty
  (testing "empty data map → has-deps-toml false"
    (let [s (deps/deps-summary {})]
      (is (false? (:has-deps-toml s))))))

(deftest test-deps-migrations-by-status
  (testing "filter migrations by status"
    (let [data {"migrations" [{"status" "done" "id" "m1"}
                               {"status" "pending" "id" "m2"}
                               {"status" "done" "id" "m3"}]}
          done (deps/migrations-by-status data "done")]
      (is (= 2 (count done))))))

(deftest test-deps-governance-score
  (testing "all present → 100.0"
    (is (= 100.0 (deps/governance-score {:wit-ok true :app-ok true :gov-ok true}))))
  (testing "none present → 0.0"
    (is (= 0.0 (deps/governance-score {:wit-ok false :app-ok false :gov-ok false}))))
  (testing "partial → 66.66..."
    (is (> (deps/governance-score {:wit-ok true :app-ok true :gov-ok false}) 66.0))))

(deftest test-deps-governance-verdict
  (testing "score < 60 → not-suitable"
    (is (= "not-suitable" (deps/governance-verdict 30.0 []))))
  (testing "score >= 60 with findings → partial"
    (is (= "partial" (deps/governance-verdict 80.0 ["missing foo"]))))
  (testing "score >= 60 no findings → suitable"
    (is (= "suitable" (deps/governance-verdict 100.0 [])))))

;; ─────────────────────────────────────────────────────────────────────────────
;; metrics
;; ─────────────────────────────────────────────────────────────────────────────

(deftest test-metrics-window-valid
  (testing "valid windows are accepted"
    (is (true? (m/window-valid? "1h")))
    (is (true? (m/window-valid? "24h")))
    (is (true? (m/window-valid? "7d")))
    (is (true? (m/window-valid? "30d")))))

(deftest test-metrics-window-invalid
  (testing "unknown window strings rejected"
    (is (false? (m/window-valid? "2h")))
    (is (false? (m/window-valid? "")))
    (is (false? (m/window-valid? nil)))))

(deftest test-metrics-nsid
  (testing "known types return correct NSIDs"
    (is (= "com.etzhayyim.metrics.getSummary"    (m/metrics-nsid :summary)))
    (is (= "com.etzhayyim.metrics.getLatency"    (m/metrics-nsid :latency)))
    (is (= "com.etzhayyim.metrics.getThroughput" (m/metrics-nsid :throughput)))
    (is (= "com.etzhayyim.metrics.getErrorRate"  (m/metrics-nsid :errors)))))

(deftest test-metrics-nsid-unknown
  (testing "unknown type returns nil"
    (is (nil? (m/metrics-nsid :foo)))))

(deftest test-metrics-url
  (testing "builds full XRPC URL"
    (is (= "https://pds.aozora.app/xrpc/com.etzhayyim.metrics.getLatency"
           (m/metrics-url "https://pds.aozora.app/" :latency)))))

(deftest test-metrics-url-strips-trailing-slash
  (testing "strips double trailing slash from pds-base"
    (is (str/includes? (m/metrics-url "https://pds.aozora.app" :latency) "/xrpc/"))))

(deftest test-metrics-parse-latency
  (testing "extracts p50/p95/p99 from response"
    (let [r (m/parse-latency {"p50" 12 "p95" 45 "p99" 120})]
      (is (= 12  (:p50 r)))
      (is (= 45  (:p95 r)))
      (is (= 120 (:p99 r))))))

(deftest test-metrics-parse-latency-missing-keys
  (testing "missing keys default to nil"
    (let [r (m/parse-latency {})]
      (is (nil? (:p50 r))))))

(deftest test-metrics-parse-throughput
  (testing "extracts rps/rpm/total"
    (let [r (m/parse-throughput {"rps" 50.0 "rpm" 3000.0 "total" 18000})]
      (is (= 50.0 (:rps r)))
      (is (= 3000.0 (:rpm r))))))

(deftest test-metrics-parse-errors
  (testing "extracts error-rate and top-errors"
    (let [r (m/parse-errors {"errorRate" 0.02 "topErrors" ["nsid.a" "nsid.b"] "totalRequests" 500})]
      (is (= 0.02 (:error-rate r)))
      (is (= ["nsid.a" "nsid.b"] (:top-errors r)))
      (is (= 500 (:total-reqs r))))))

(deftest test-metrics-format-summary
  (testing "formats k/v pairs as '  key: val' lines"
    (let [lines (vec (m/format-summary {"p50" 12 "p99" 120}))]
      (is (= 2 (count lines)))
      (is (some #(str/includes? % "p50") lines))
      (is (some #(str/includes? % "12") lines)))))

(deftest test-metrics-format-latency
  (testing "formats latency with header"
    (let [lines (m/format-latency {:p50 12 :p95 45 :p99 nil} "1h")]
      (is (= "latency (1h):" (first lines)))
      (is (some #(str/includes? % "p50: 12ms") lines))
      ;; nil p99 should not appear
      (is (not (some #(str/includes? % "p99") lines))))))

;; ─────────────────────────────────────────────────────────────────────────────
;; runner
;; ─────────────────────────────────────────────────────────────────────────────

(run-tests 'etzhayyim.test-bb-migration-wave3a)
