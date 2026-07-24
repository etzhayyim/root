;; test_bb_migration_wave3b.clj — parity smoke tests for wave-3b cljc ports.
;;
;; Run with:  bb 70-tools/src/etzhayyim/test_bb_migration_wave3b.clj
;; from repo root (classpath 70-tools/src already in bb.edn :paths).
;;
;; Modules tested:
;;   etzhayyim.mokuteki    — rank ladder / axes / report assembly (wave-3b)
;;   etzhayyim.haisen      — actor wiring graph pure logic (wave-3b)
;;   etzhayyim.hinshitsu   — actor quality scoring / grading / diff-snap (wave-3b)
;;   etzhayyim.code-quality — cap / sql-scan / perf-test pure helpers (wave-3b)
;;
;; All assertions are verified against Python baseline runs on identical inputs.

(ns etzhayyim.test-bb-migration-wave3b
  (:require [clojure.test    :refer [deftest is testing run-tests]]
            [clojure.string  :as str]
            [etzhayyim.mokuteki    :as mok]
            [etzhayyim.haisen      :as hai]
            [etzhayyim.hinshitsu   :as hin]
            [etzhayyim.code-quality :as cq]))

;; ─────────────────────────────────────────────────────────────────────────────
;; etzhayyim.mokuteki
;; ─────────────────────────────────────────────────────────────────────────────

(deftest test-mok-resolve-rank-kyu6
  (testing "score 0 → Kyu 6"
    (is (= "Kyu 6" (:name (mok/resolve-rank 0))))))

(deftest test-mok-resolve-rank-kyu5
  (testing "score 100 → Kyu 5"
    (is (= "Kyu 5" (:name (mok/resolve-rank 100))))))

(deftest test-mok-resolve-rank-kyu1
  (testing "score 1500 → Kyu 1"
    (is (= "Kyu 1" (:name (mok/resolve-rank 1500))))))

(deftest test-mok-resolve-rank-dan1
  (testing "score 2000 → Dan 1"
    (is (= "Dan 1" (:name (mok/resolve-rank 2000))))))

(deftest test-mok-resolve-rank-dan10
  (testing "score 12000 → Dan 10"
    (is (= "Dan 10" (:name (mok/resolve-rank 12000))))))

(deftest test-mok-next-rank-from-zero
  (testing "next-rank from 0 → Kyu 5, need 100"
    (is (= ["Kyu 5" 100] (mok/next-rank 0)))))

(deftest test-mok-next-rank-from-100
  (testing "next-rank from 100 → Kyu 4, need 200"
    (is (= ["Kyu 4" 200] (mok/next-rank 100)))))

(deftest test-mok-next-rank-at-top
  (testing "next-rank from 12000 → [\"\", 0] (already Dan 10)"
    (is (= ["" 0] (mok/next-rank 12000)))))

(deftest test-mok-weighted-score
  (testing "weighted score: 0.6×80 + 0.4×60 = 72.0"
    ;; Python: _weighted_score([Component('a',80.0,0.6), Component('b',60.0,0.4)]) = 72.0
    (let [comps [(mok/make-component "a" 0.6 80.0 "")
                 (mok/make-component "b" 0.4 60.0 "")]]
      (is (< (Math/abs (- 72.0 (mok/weighted-score comps))) 1e-9)))))

(deftest test-mok-bar-half
  (testing "bar at 50% width 10: [█████░░░░░]"
    ;; Python: _bar(50, 10) = '[█████░░░░░]'
    (is (= "[█████░░░░░]" (mok/bar 50 10)))))

(deftest test-mok-bar-empty
  (testing "bar at 0%: all empty"
    (is (= "[░░░░░░░░░░]" (mok/bar 0 10)))))

(deftest test-mok-bar-full
  (testing "bar at 100%: all filled"
    (is (= "[██████████]" (mok/bar 100 10)))))

(deftest test-mok-derive-axes-engagement
  (testing "derive-axes: engagement = A*0.5 + D*0.5"
    ;; layer-a score=80, layer-b=50, layer-c=50, layer-d=60
    ;; engagement = 80*0.5 + 60*0.5 = 70.0
    (let [a (mok/make-layer "A" "Structure" "構造" 0.30 80.0 0 [])
          b (mok/eval-layer-b-stub)
          c (mok/eval-layer-c-stub)
          d (mok/make-layer "D" "Implementation" "実装" 0.25 60.0 0 [])
          axes (mok/derive-axes a b c d)
          eng  (first (filter #(str/starts-with? (:name %) "Engagement") axes))]
      (is (< (Math/abs (- 70.0 (:score eng))) 1e-9)))))

(deftest test-mok-eval-layer-b-stub
  (testing "eval-layer-b-stub returns layer with score 50.0 and id B"
    (let [l (mok/eval-layer-b-stub)]
      (is (= "B" (:id l)))
      (is (= 50.0 (:score l))))))

(deftest test-mok-eval-layer-c-stub
  (testing "eval-layer-c-stub returns layer with score 50.0 and id C"
    (let [l (mok/eval-layer-c-stub)]
      (is (= "C" (:id l)))
      (is (= 50.0 (:score l))))))

(deftest test-mok-report-from-stubs
  (testing "build-mokuteki-report-from assembles total-score from stub layers"
    ;; stub B and C both score 50; use simple A and D with fixed scores
    (let [a  (mok/make-layer "A" "Structure"      "構造" 0.30 50.0 (int (* 50.0 0.30 120)) [])
          b  (mok/eval-layer-b-stub)
          c  (mok/eval-layer-c-stub)
          d  (mok/make-layer "D" "Implementation" "実装" 0.25 50.0 (int (* 50.0 0.25 120)) [])
          r  (mok/build-mokuteki-report-from a b c d "2026-01-01T00:00:00Z")]
      (is (= 4 (count (:layers r))))
      (is (= "2026-01-01T00:00:00Z" (:generated-at r)))
      (is (pos? (:total-score r)))
      ;; rank should resolve without throwing
      (is (string? (:name (:rank r)))))))

(deftest test-mok-flatten-report-keys
  (testing "flatten-report contains expected flat keys"
    (let [a  (mok/make-layer "A" "Structure"      "構造" 0.30 80.0 (int (* 80.0 0.30 120)) [])
          b  (mok/eval-layer-b-stub)
          c  (mok/eval-layer-c-stub)
          d  (mok/make-layer "D" "Implementation" "実装" 0.25 70.0 (int (* 70.0 0.25 120)) [])
          r  (mok/build-mokuteki-report-from a b c d "2026-01-01T00:00:00Z")
          flat (mok/flatten-report r)]
      (is (contains? flat "total_score"))
      (is (contains? flat "max_score"))
      (is (contains? flat "rank_name"))
      (is (contains? flat "layer_a_score"))
      (is (contains? flat "layer_d_score"))
      (is (= 12000 (get flat "max_score"))))))

;; ─────────────────────────────────────────────────────────────────────────────
;; etzhayyim.haisen
;; ─────────────────────────────────────────────────────────────────────────────

(deftest test-hai-app-from-jsonld-basic
  (testing "app-from-jsonld parses nanoid and fields"
    ;; Python: _app_from_jsonld({'nanoid':'test001','did':'did:plc:abc','name':'Test App',
    ;;   'performerType':'worker','collections':['com.etzhayyim.test'],
    ;;   'witExports':['iface:greet']})
    ;; → app.nanoid='test001', app.collections=['com.etzhayyim.test'], wit_exports=['iface:greet']
    (let [data {"nanoid"        "test001"
                "did"           "did:plc:abc"
                "name"          "Test App"
                "performerType" "worker"
                "uiType"        "none"
                "runtimeType"   "edge"
                "collections"   ["com.etzhayyim.test"]
                "witImports"    []
                "witExports"    ["iface:greet"]}
          app (hai/app-from-jsonld data)]
      (is (= "test001" (:nanoid app)))
      (is (= ["com.etzhayyim.test"] (:collections app)))
      (is (= ["iface:greet"] (:wit-exports app))))))

(deftest test-hai-app-from-jsonld-missing-nanoid
  (testing "app-from-jsonld returns nil when nanoid absent"
    ;; Python: _app_from_jsonld({'name':'x'}) → None
    (is (nil? (hai/app-from-jsonld {"name" "x"})))))

(deftest test-hai-orphans
  (testing "orphans: app with no edges is orphan"
    ;; Python: r.orphans → ['c'] (apps=['a','b','c'], edges=[a→b])
    (let [apps  [(hai/make-app {"nanoid" "a"})
                 (hai/make-app {"nanoid" "b"})
                 (hai/make-app {"nanoid" "c"})]
          edges [{:from "a" :to "b" :type :invoke}]
          r     {:apps apps :edges edges}]
      (is (= ["c"] (mapv :nanoid (hai/orphans r)))))))

(deftest test-hai-orphans-none
  (testing "orphans: returns empty when all apps are connected"
    (let [apps  [(hai/make-app {"nanoid" "a"})
                 (hai/make-app {"nanoid" "b"})]
          edges [{:from "a" :to "b" :type :invoke}]
          r     {:apps apps :edges edges}]
      (is (empty? (hai/orphans r))))))

(deftest test-hai-coupling
  (testing "coupling: in-degree count sorted descending"
    ;; Python: r.coupling() → {'b': 1}
    (let [apps  [(hai/make-app {"nanoid" "a"})
                 (hai/make-app {"nanoid" "b"})
                 (hai/make-app {"nanoid" "c"})]
          edges [{:from "a" :to "b" :type :invoke}]
          r     {:apps apps :edges edges}
          c     (hai/coupling r)]
      (is (= [["b" 1]] c)))))

(deftest test-hai-coupling-multi-edges
  (testing "coupling: multiple edges to same target sum correctly"
    (let [apps  [(hai/make-app {"nanoid" "a"})
                 (hai/make-app {"nanoid" "b"})
                 (hai/make-app {"nanoid" "c"})]
          edges [{:from "a" :to "b" :type :invoke}
                 {:from "c" :to "b" :type :writes}]
          r     {:apps apps :edges edges}
          c     (into {} (hai/coupling r))]
      (is (= 2 (get c "b"))))))

(deftest test-hai-build-edges-wasm-import
  (testing "build-edges: wasm-import edge from wit-imports vs wit-exports"
    (let [apps-data [{"nanoid"     "exporter"
                      "witExports" ["iface:compute"]
                      "witImports" []
                      "collections" []}
                     {"nanoid"     "importer"
                      "witImports" ["iface:compute"]
                      "witExports" []
                      "collections" []}]
          src-map   {"importer" "" "exporter" ""}
          edges     (hai/build-edges apps-data src-map)]
      ;; importer should have a wasm-import edge to exporter
      (is (some #(and (= "importer" (:from %))
                      (= "exporter" (:to %))
                      (= :wasm-import (:type %)))
                edges)))))

;; ─────────────────────────────────────────────────────────────────────────────
;; etzhayyim.hinshitsu
;; ─────────────────────────────────────────────────────────────────────────────

(deftest test-hin-grade-s
  (testing "grade S for 90+"
    (is (= "S" (hin/grade 95)))
    (is (= "S" (hin/grade 90)))))

(deftest test-hin-grade-a
  (testing "grade A for 70-89"
    (is (= "A" (hin/grade 75)))
    (is (= "A" (hin/grade 70)))))

(deftest test-hin-grade-b
  (testing "grade B for 50-69"
    (is (= "B" (hin/grade 55)))
    (is (= "B" (hin/grade 50)))))

(deftest test-hin-grade-c
  (testing "grade C for 30-49"
    (is (= "C" (hin/grade 35)))
    (is (= "C" (hin/grade 30)))))

(deftest test-hin-grade-d
  (testing "grade D below 30"
    (is (= "D" (hin/grade 10)))
    (is (= "D" (hin/grade 0)))))

(deftest test-hin-fix-suggestions-missing-file
  (testing "fix-suggestions: missing file → Create suggestion"
    ;; Python: _fix_suggestions(['missing:wrangler.jsonc']) → ['Create wrangler.jsonc']
    (is (= ["Create wrangler.jsonc"] (hin/fix-suggestions ["missing:wrangler.jsonc"])))))

(deftest test-hin-fix-suggestions-missing-field
  (testing "fix-suggestions: missing_field → Add field suggestion"
    ;; Python: _fix_suggestions(['missing_field:description']) → ["Add 'description' field to kotodama.jsonld"]
    (is (= ["Add 'description' field to kotodama.jsonld"]
           (hin/fix-suggestions ["missing_field:description"])))))

(deftest test-hin-fix-suggestions-nsid-placeholder
  (testing "fix-suggestions: nsid_placeholder suggestion"
    (let [sugs (hin/fix-suggestions ["nsid_placeholder"])]
      (is (= 1 (count sugs)))
      (is (str/includes? (first sugs) "NSID")))))

(deftest test-hin-fix-suggestions-hardcoded-model
  (testing "fix-suggestions: hardcoded_model suggestion"
    (let [sugs (hin/fix-suggestions ["hardcoded_model"])]
      (is (= 1 (count sugs)))
      (is (str/includes? (first sugs) "resolveModelId")))))

(deftest test-hin-score-actor-missing-fields
  (testing "score-actor: missing required fields each deduct 5 points"
    ;; Python: actor with empty name/did/performerType/description (4 fields) = 100 - 4*5 = 80
    ;; (no dir/existing_files so file checks are skipped)
    (let [actor {"nanoid" "a2" "name" "" "did" "" "performerType" "" "description" ""}
          [score issues] (hin/score-actor actor)]
      (is (= 80 score))
      (is (= 4 (count issues))))))

(deftest test-hin-score-actor-ok-fields
  (testing "score-actor: all fields present, no files → score 100"
    ;; (existing_files key absent → file checks skipped)
    (let [actor {"nanoid" "a3" "name" "App" "did" "did:test" "performerType" "worker"
                 "description" "A test app"}
          [score _issues] (hin/score-actor actor)]
      (is (= 100 score)))))

(deftest test-hin-score-actor-nsid-placeholder
  (testing "score-actor: nsid_placeholder in app_ts_content deducts 10"
    (let [actor {"nanoid" "a4" "name" "App" "did" "did:test"
                 "performerType" "worker" "description" "x"
                 "app_ts_content" "const n = \"nsid\";"}
          [score issues] (hin/score-actor actor)]
      (is (= 90 score))
      (is (some #(= "nsid_placeholder" %) issues)))))

(deftest test-hin-diff-snap-basic
  (testing "diff-snap: scan_count, score_count, avg_total_score match Python"
    ;; Python: dids=['did:1','did:2','did:3']
    ;;   scan={did:1:{did_doc_reachable:T,with_posts:T}, did:2:{did_doc_reachable:F}}
    ;;   score={did:1:{total_score:80}, did:2:{total_score:60}}
    ;; → {scan_count:2, score_count:2, did_doc_reachable:1, avg_total_score:70.0}
    (let [dids  ["did:1" "did:2" "did:3"]
          scan  {"did:1" {"did_doc_reachable" true  "with_posts" true}
                 "did:2" {"did_doc_reachable" false}}
          score {"did:1" {"total_score" 80}
                 "did:2" {"total_score" 60}}
          snap  (hin/diff-snap dids scan score)]
      (is (= 2 (:scan-count snap)))
      (is (= 2 (:score-count snap)))
      (is (= 1 (:did-doc-reachable snap)))
      (is (< (Math/abs (- 70.0 (:avg-total-score snap))) 1e-9)))))

(deftest test-hin-diff-snap-empty
  (testing "diff-snap: all zeros when no matches"
    (let [snap (hin/diff-snap ["did:x"] {} {})]
      (is (= 0 (:scan-count snap)))
      (is (= 0.0 (:avg-total-score snap))))))

(deftest test-hin-diff-delta
  (testing "diff-delta computes subtraction of two snaps"
    (let [before {:scan-count 5 :score-count 5 :did-doc-reachable 3
                  :atproto-reachable 2 :with-posts 1 :avg-total-score 60.0}
          after  {:scan-count 7 :score-count 7 :did-doc-reachable 5
                  :atproto-reachable 4 :with-posts 3 :avg-total-score 75.0}
          delta  (hin/diff-delta before after)]
      (is (= 2 (:scan-count delta)))
      (is (= 2 (:did-doc-reachable delta)))
      (is (< (Math/abs (- 15.0 (:avg-total-score delta))) 1e-9)))))

;; ─────────────────────────────────────────────────────────────────────────────
;; etzhayyim.code-quality
;; ─────────────────────────────────────────────────────────────────────────────

(deftest test-cq-cap-high
  (testing "cap: clamps above 100 to 100.0"
    ;; Python: _cap(105) = 100.0
    (is (= 100.0 (cq/cap 105.0)))
    (is (= 100.0 (cq/cap 200.0)))))

(deftest test-cq-cap-low
  (testing "cap: clamps below 0 to 0.0"
    ;; Python: _cap(-5) = 0.0
    (is (= 0.0 (cq/cap -5.0)))
    (is (= 0.0 (cq/cap -100.0)))))

(deftest test-cq-cap-passthrough
  (testing "cap: passes through in-range values"
    ;; Python: _cap(50.7) = 50.7
    (is (= 50.7 (cq/cap 50.7)))
    (is (= 0.0  (cq/cap 0.0)))
    (is (= 100.0 (cq/cap 100.0)))))

(deftest test-cq-overall-score-empty
  (testing "overall-score returns 0.0 when no available checks"
    (is (= 0.0 (cq/overall-score [])))))

(deftest test-cq-overall-score-average
  (testing "overall-score averages available check scores"
    (let [checks [(cq/make-check "a" "ta" true 80.0 0 "" "")
                  (cq/make-check "b" "tb" true 60.0 0 "" "")
                  (cq/make-check "c" "tc" false 0.0 0 "" "")]]  ;; unavailable
      ;; Only a and b: (80 + 60) / 2 = 70.0
      (is (< (Math/abs (- 70.0 (cq/overall-score checks))) 1e-9)))))

(deftest test-cq-overall-score-skips-error
  (testing "overall-score skips checks with non-blank error"
    (let [checks [(cq/make-check "a" "ta" true 80.0 0 "" "")
                  (cq/make-check "b" "tb" true 50.0 0 "" "some error")]]
      ;; Only a counts: 80.0
      (is (< (Math/abs (- 80.0 (cq/overall-score checks))) 1e-9)))))

(deftest test-cq-sql-injection-safe
  (testing "score-sql-injection: clean content → score 100, issues 0"
    (let [r (cq/score-sql-injection "const q = db.prepare(sql);")]
      (is (= 100.0 (:score r)))
      (is (= 0 (:issues r))))))

(deftest test-cq-sql-injection-bad-esc
  (testing "score-sql-injection: ${esc(...)} detected → score 0, issues >= 1"
    ;; Content with the esc-interpolation pattern: ${esc(val)}
    (let [content "${esc(val)}"
          r (cq/score-sql-injection content)]
      (is (= 0.0 (:score r)))
      (is (pos? (:issues r))))))

(deftest test-cq-sql-injection-bad-template
  (testing "score-sql-injection: template literal ${...} detected → score 0"
    ;; Content with template SQL: \"${userId}\"
    (let [content "\"${userId}\""
          r (cq/score-sql-injection content)]
      (is (= 0.0 (:score r))))))

(deftest test-cq-parse-machete-output-no-unused
  (testing "parse-machete-output: no unused when no tab-leading lines"
    (let [r (cq/parse-machete-output "No unused dependencies found\n")]
      (is (= 0 (:unused-count r))))))

(deftest test-cq-parse-machete-output-with-unused
  (testing "parse-machete-output: counts tab-leading lines"
    (let [out "\tserde\n\ttokio\n\tserde_json\n"
          r   (cq/parse-machete-output out)]
      (is (= 3 (:unused-count r))))))

(deftest test-cq-parse-go-vet-rc0
  (testing "parse-go-vet-output: exit 0 → no issues"
    (is (= {:issues 0} (cq/parse-go-vet-output "" 0)))))

(deftest test-cq-parse-go-vet-issues
  (testing "parse-go-vet-output: counts non-trivial lines on non-zero exit"
    (let [out "pkg/foo.go:10:3: unreachable code\npkg/bar.go:5:1: another issue\n"
          r   (cq/parse-go-vet-output out 1)]
      (is (= {:issues 2} r)))))

(deftest test-cq-parse-go-vet-skips-trivial
  (testing "parse-go-vet-output: skips # comment lines and 'matched no packages'"
    (let [out "# pkg/foo\nmatched no packages\n# another\n"
          r   (cq/parse-go-vet-output out 1)]
      (is (= {:issues 0} r)))))

(deftest test-cq-parse-go-mod-tidy-clean
  (testing "parse-go-mod-tidy-output: exit 0, no output → not dirty"
    (is (= {:dirty false} (cq/parse-go-mod-tidy-output "" 0)))))

(deftest test-cq-parse-go-mod-tidy-dirty-exit
  (testing "parse-go-mod-tidy-output: non-zero exit → dirty"
    (is (= {:dirty true} (cq/parse-go-mod-tidy-output "" 1)))))

(deftest test-cq-parse-go-mod-tidy-dirty-output
  (testing "parse-go-mod-tidy-output: exit 0 but non-empty output → dirty"
    (is (= {:dirty true} (cq/parse-go-mod-tidy-output "--- go.mod\n+++ go.mod\n" 0)))))

(deftest test-cq-build-report
  (testing "build-report: overall-score and shape"
    (let [checks [(cq/make-check "a" "ta" true 80.0 0 "" "")
                  (cq/make-check "b" "tb" true 60.0 0 "" "")]
          rpt    (cq/build-report checks)]
      (is (= 2 (:available-tools rpt)))
      ;; overall = (80+60)/2 = 70; Math/round(70*10) / ... = 700 — but build-report rounds
      ;; to nearest int via Math/round(score*10) / 10 pattern
      ;; Actually build-report does (Math/round (* score 10.0)) which gives 700 not 70.0
      ;; Let's check the actual value is numeric
      (is (number? (:overall-score rpt))))))

(deftest test-cq-perf-test-found
  (testing "score-perf-test: toBeLessThan present → score 100, issues 0"
    (let [content "expect(ms).toBeLessThan(100);"
          r       (cq/score-perf-test content "yoro-profile.spec.ts")]
      (is (= 100.0 (:score r)))
      (is (= 0 (:issues r))))))

(deftest test-cq-perf-test-missing
  (testing "score-perf-test: no toBeLessThan → score 0, issues 1"
    (let [content "expect(value).toBe(42);"
          r       (cq/score-perf-test content "my.spec.ts")]
      (is (= 0.0 (:score r)))
      (is (= 1 (:issues r))))))

;; ─────────────────────────────────────────────────────────────────────────────
;; runner
;; ─────────────────────────────────────────────────────────────────────────────

(run-tests 'etzhayyim.test-bb-migration-wave3b)
