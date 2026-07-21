;; test_bb_migration_wave6c.clj — parity smoke tests for wave-6c cljc ports.
;;
;; Run with:  bb 70-tools/src/etzhayyim/test_bb_migration_wave6c.clj
;; from repo root (classpath 70-tools/src already in bb.edn :paths).
;;
;; Modules tested:
;;   etzhayyim.kosei    — remaining pure logic from kosei.py (wave-6c):
;;     make-violation / violation->dict / make-app-result / app-result-ok?
;;     make-report / compliance-pct / report->dict
;;     strip-jsonc-comments / norm-line
;;     detect-language / detect-npm-features / detect-cargo-features
;;     system-eta / tier-distribution
;;
;;   etzhayyim.shannon  — remaining pure logic from shannon.py (wave-6c):
;;     make-item / item->dict / make-check / check->dict
;;     make-report-meta / report-meta->dict
;;     norm-line / hash8 / dedup-items
;;     go-only-stub / make-check-result
;;     ordered-check-names / assemble-checks
;;
;; Parity values derived from running the Python originals on the same inputs.

(ns etzhayyim.test-bb-migration-wave6c
  (:require [clojure.test :refer [deftest is testing run-tests]]
            [etzhayyim.kosei   :as ko]
            [etzhayyim.shannon :as sh]
            [etzhayyim.shannon-scores :as ss]))

;; ─────────────────────────────────────────────────────────────────────────────
;; kosei: make-violation / violation->dict
;; ─────────────────────────────────────────────────────────────────────────────

(deftest test-ko-make-violation-basic
  (testing "make-violation constructs expected map"
    (let [v (ko/make-violation "missing_file" "error" "src/app.ts" "not found")]
      (is (= "missing_file" (:rule v)))
      (is (= "error" (:severity v)))
      (is (= "src/app.ts" (:path v)))
      (is (= "not found" (:detail v))))))

(deftest test-ko-make-violation-default-detail
  (testing "make-violation 3-arg default detail is empty string"
    (let [v (ko/make-violation "cors_missing" "warning" "src/app.ts")]
      (is (= "" (:detail v))))))

(deftest test-ko-violation-dict-parity
  (testing "violation->dict matches Python KoseiViolation.to_dict"
    (let [v (ko/make-violation "missing_file" "error" "src/app.ts" "not found")
          d (ko/violation->dict v)]
      (is (= {"rule" "missing_file"
               "severity" "error"
               "path" "src/app.ts"
               "detail" "not found"}
             d)))))

;; ─────────────────────────────────────────────────────────────────────────────
;; kosei: make-app-result / app-result-ok?
;; ─────────────────────────────────────────────────────────────────────────────

(deftest test-ko-app-result-ok-empty
  (testing "app-result-ok? true when no missing files and no violations"
    (is (true? (ko/app-result-ok? (ko/make-app-result "20-actors/foo" [] []))))))

(deftest test-ko-app-result-ok-missing-files
  (testing "app-result-ok? false when there are missing files"
    (let [r (ko/make-app-result "20-actors/foo" ["src/app.ts"] [])]
      (is (false? (ko/app-result-ok? r))))))

(deftest test-ko-app-result-ok-error-violation
  (testing "app-result-ok? false when there is an error violation"
    (let [v (ko/make-violation "cors" "error" "src/app.ts")
          r (ko/make-app-result "20-actors/foo" [] [v])]
      (is (false? (ko/app-result-ok? r))))))

(deftest test-ko-app-result-ok-warning-only
  (testing "app-result-ok? true when only warning violations exist"
    (let [v (ko/make-violation "cors" "warning" "src/app.ts")
          r (ko/make-app-result "20-actors/foo" [] [v])]
      (is (true? (ko/app-result-ok? r))))))

;; ─────────────────────────────────────────────────────────────────────────────
;; kosei: compliance-pct / make-report / report->dict
;; ─────────────────────────────────────────────────────────────────────────────

(deftest test-ko-compliance-pct-basic
  (testing "compliance-pct: 8/10 = 80.0"
    (is (= 80.0 (ko/compliance-pct 8 10)))))

(deftest test-ko-compliance-pct-zero-total
  (testing "compliance-pct: 0/0 safe (returns 0.0)"
    (is (= 0.0 (ko/compliance-pct 0 0)))))

(deftest test-ko-compliance-pct-all-pass
  (testing "compliance-pct: 10/10 = 100.0"
    (is (= 100.0 (ko/compliance-pct 10 10)))))

(deftest test-ko-report-dict-keys
  (testing "report->dict has expected keys matching Python KoseiReport.to_dict"
    (let [rpt (ko/make-report "2026-06-21T00:00:00Z" 10 8 [])
          d   (ko/report->dict rpt)]
      (is (contains? d "evaluated_at"))
      (is (contains? d "total_apps"))
      (is (contains? d "ok_apps"))
      (is (contains? d "compliance_pct"))
      (is (contains? d "results"))
      (is (contains? d "global_violations")))))

(deftest test-ko-report-compliance-pct-rounded
  (testing "report->dict compliance_pct is rounded"
    (let [rpt (ko/make-report "2026-06-21T00:00:00Z" 10 8 [])
          d   (ko/report->dict rpt)]
      (is (= 80.0 (get d "compliance_pct"))))))

;; ─────────────────────────────────────────────────────────────────────────────
;; kosei: strip-jsonc-comments
;; ─────────────────────────────────────────────────────────────────────────────

(deftest test-ko-strip-jsonc-line-comment
  (testing "strip-jsonc-comments removes // line comments and preserves newline"
    (let [j1 "{\"a\": 1, // comment\n\"b\": 2}"
          r  (ko/strip-jsonc-comments j1)]
      (is (= "{\"a\": 1, \n\"b\": 2}" r)))))

(deftest test-ko-strip-jsonc-block-comment
  (testing "strip-jsonc-comments removes /* block */ comments"
    (let [j2 "{/* block */ \"x\": 42}"
          r  (ko/strip-jsonc-comments j2)]
      (is (= "{ \"x\": 42}" r)))))

(deftest test-ko-strip-jsonc-slash-in-string
  (testing "strip-jsonc-comments leaves slashes inside strings alone"
    (let [j3 "{\"url\": \"http://foo.com\", \"b\": 2}"
          r  (ko/strip-jsonc-comments j3)]
      (is (= j3 r)))))

(deftest test-ko-strip-jsonc-no-comment
  (testing "strip-jsonc-comments is a no-op on plain JSON"
    (let [j4 "{\"key\": 42}"
          r  (ko/strip-jsonc-comments j4)]
      (is (= j4 r)))))

(deftest test-ko-strip-jsonc-unterminated-block
  (testing "strip-jsonc-comments handles unterminated block comment"
    (let [j5 "{\"a\": /* unterminated"
          r  (ko/strip-jsonc-comments j5)]
      (is (= "{\"a\": " r)))))

;; ─────────────────────────────────────────────────────────────────────────────
;; kosei: norm-line
;; ─────────────────────────────────────────────────────────────────────────────

(deftest test-ko-norm-line-bold-markers
  (testing "norm-line strips ** markers and lowercases"
    (is (= "hello world" (ko/norm-line "  **Hello**  World  ")))))

(deftest test-ko-norm-line-backtick
  (testing "norm-line strips backtick markers"
    (is (= "code here" (ko/norm-line "  `code` here  ")))))

(deftest test-ko-norm-line-italic
  (testing "norm-line strips * markers"
    (is (= "bold text" (ko/norm-line "*bold* text")))))

(deftest test-ko-norm-line-empty
  (testing "norm-line handles empty/whitespace string"
    (is (= "" (ko/norm-line "  ")))))

;; ─────────────────────────────────────────────────────────────────────────────
;; kosei: detect-language
;; ─────────────────────────────────────────────────────────────────────────────

(deftest test-ko-detect-language-rust
  (testing "detect-language returns rust when has-cargo"
    (is (= "rust" (ko/detect-language {:has-cargo true})))))

(deftest test-ko-detect-language-go
  (testing "detect-language returns go when has-go-mod"
    (is (= "go" (ko/detect-language {:has-go-mod true})))))

(deftest test-ko-detect-language-python
  (testing "detect-language returns python when has-python"
    (is (= "python" (ko/detect-language {:has-python true})))))

(deftest test-ko-detect-language-default
  (testing "detect-language defaults to typescript"
    (is (= "typescript" (ko/detect-language {})))))

(deftest test-ko-detect-language-rust-priority
  (testing "detect-language cargo > go > python priority"
    (is (= "rust" (ko/detect-language {:has-cargo true :has-go-mod true :has-python true})))))

;; ─────────────────────────────────────────────────────────────────────────────
;; kosei: detect-npm-features
;; ─────────────────────────────────────────────────────────────────────────────

(deftest test-ko-detect-npm-features-onnx
  (testing "detect-npm-features detects onnx"
    (is (true? (:has-onnx (ko/detect-npm-features "onnxruntime-web"))))))

(deftest test-ko-detect-npm-features-webgpu
  (testing "detect-npm-features detects webgpu"
    (is (true? (:has-webgpu (ko/detect-npm-features "@webgpu/types"))))))

(deftest test-ko-detect-npm-features-mcp
  (testing "detect-npm-features detects @modelcontextprotocol"
    (is (true? (:has-mcp (ko/detect-npm-features "@modelcontextprotocol/server"))))))

(deftest test-ko-detect-npm-features-empty
  (testing "detect-npm-features all false for empty string"
    (let [f (ko/detect-npm-features "")]
      (is (false? (:has-onnx f)))
      (is (false? (:has-webgpu f)))
      (is (false? (:has-fido2 f)))
      (is (false? (:has-mcp f)))
      (is (false? (:has-wasm f))))))

;; ─────────────────────────────────────────────────────────────────────────────
;; kosei: system-eta / tier-distribution
;; ─────────────────────────────────────────────────────────────────────────────

(deftest test-ko-system-eta-mixed
  (testing "system-eta matches Python: (2*0.667 + 3*0.5 + 1*0.91) / 6 = 0.624"
    (is (< (Math/abs (- (ko/system-eta {:T1 2 :T2 3 :T3 1}) 0.624)) 1e-9))))

(deftest test-ko-system-eta-all-t3
  (testing "system-eta all T3 = 0.91"
    (is (< (Math/abs (- (ko/system-eta {:T1 0 :T2 0 :T3 5}) 0.910)) 1e-9))))

(deftest test-ko-system-eta-no-assigned
  (testing "system-eta returns 0.0 when no apps assigned"
    (is (= 0.0 (ko/system-eta {:T1 0 :T2 0 :T3 0})))))

(deftest test-ko-tier-distribution-counts
  (testing "tier-distribution counts match"
    (let [tiers ["T1" "T1" "T2" "T2" "T2" "T3" nil ""]
          dist  (ko/tier-distribution tiers)]
      (is (= 2 (:T1 dist)))
      (is (= 3 (:T2 dist)))
      (is (= 1 (:T3 dist)))
      (is (= 2 (:unassigned dist)))
      (is (= 8 (:total dist))))))

(deftest test-ko-tier-distribution-eta
  (testing "tier-distribution system-eta matches formula"
    (let [tiers ["T1" "T1" "T2" "T2" "T2" "T3"]
          dist  (ko/tier-distribution tiers)]
      (is (< (Math/abs (- (:system-eta dist) 0.624)) 1e-9)))))

;; ─────────────────────────────────────────────────────────────────────────────
;; shannon: make-item / item->dict
;; ─────────────────────────────────────────────────────────────────────────────

(deftest test-sh-make-item-basic
  (testing "make-item constructs expected map"
    (let [item (sh/make-item "foo.ts" "claude_md_duplication" 0.8 "bar.ts" "detail")]
      (is (= "foo.ts" (:path item)))
      (is (= "claude_md_duplication" (:kind item)))
      (is (= 0.8 (:redundancy item)))
      (is (= "bar.ts" (:duplicate-of item)))
      (is (= "detail" (:detail item))))))

(deftest test-sh-item-dict-parity
  (testing "item->dict matches Python ShannonItem.to_dict"
    (let [item (sh/make-item "foo.ts" "claude_md_duplication" 0.8 "bar.ts" "duplicated content")
          d    (sh/item->dict item)]
      (is (= "foo.ts" (get d "path")))
      (is (= 0.8 (get d "redundancy")))
      (is (= "bar.ts" (get d "duplicate_of")))
      (is (= "duplicated content" (get d "detail"))))))

(deftest test-sh-item-dict-omits-empty-optional
  (testing "item->dict omits optional keys when empty"
    (let [item (sh/make-item "foo.ts" "x" 0.5)
          d    (sh/item->dict item)]
      (is (not (contains? d "duplicate_of")))
      (is (not (contains? d "detail"))))))

;; ─────────────────────────────────────────────────────────────────────────────
;; shannon: make-check / check->dict
;; ─────────────────────────────────────────────────────────────────────────────

(deftest test-sh-make-check-defaults
  (testing "make-check 1-arg defaults"
    (let [chk (sh/make-check "test_check")]
      (is (= 100.0 (:score chk)))
      (is (= 0.0 (:weight chk)))
      (is (= 0 (:violations chk)))
      (is (= "" (:details chk)))
      (is (= [] (:items chk))))))

(deftest test-sh-check-dict-parity
  (testing "check->dict matches Python ShannonCheck.to_dict"
    (let [item (sh/make-item "foo.ts" "x" 0.5)
          chk  (sh/make-check "claude_md_duplication" 20.0 0.3 5 "5 dupes" [item])
          d    (sh/check->dict chk)]
      (is (= "claude_md_duplication" (get d "name")))
      (is (= 20.0 (get d "score")))
      (is (= 0.3 (get d "weight")))
      (is (= 5 (get d "violations")))
      (is (= "5 dupes" (get d "details")))
      (is (= 1 (count (get d "items")))))))

;; ─────────────────────────────────────────────────────────────────────────────
;; shannon: make-report-meta / report-meta->dict
;; ─────────────────────────────────────────────────────────────────────────────

(deftest test-sh-report-meta-dict-keys
  (testing "report-meta->dict has expected keys"
    (let [r (sh/make-report-meta "2026-06-21T00:00:00Z" 85.0 0.15 [] [] "w * (1 - r)")
          d (sh/report-meta->dict r)]
      (is (contains? d "evaluated_at"))
      (is (contains? d "overall_score"))
      (is (contains? d "redundancy_rate"))
      (is (contains? d "checks"))
      (is (contains? d "hotspots"))
      (is (contains? d "scoring_model"))
      (is (= 85.0 (get d "overall_score")))
      (is (= 0.15 (get d "redundancy_rate"))))))

;; ─────────────────────────────────────────────────────────────────────────────
;; shannon: norm-line
;; ─────────────────────────────────────────────────────────────────────────────

(deftest test-sh-norm-line-bold-parity
  (testing "sh/norm-line matches Python _norm_line: bold markers"
    (is (= "hello world" (sh/norm-line "  **Hello**  World  ")))))

(deftest test-sh-norm-line-backtick-parity
  (testing "sh/norm-line matches Python _norm_line: backtick markers"
    (is (= "code here" (sh/norm-line "  `code` here  ")))))

(deftest test-sh-norm-line-empty-parity
  (testing "sh/norm-line handles empty string"
    (is (= "" (sh/norm-line "  ")))))

;; ─────────────────────────────────────────────────────────────────────────────
;; shannon: hash8 — PARITY CRITICAL
;; ─────────────────────────────────────────────────────────────────────────────

(deftest test-sh-hash8-hello-parity
  (testing "hash8(\"hello\") matches Python sha256.hexdigest()[:16] = 2cf24dba5fb0a30e"
    (is (= "2cf24dba5fb0a30e" (sh/hash8 "hello")))))

(deftest test-sh-hash8-empty-parity
  (testing "hash8(\"\") matches Python = e3b0c44298fc1c14"
    (is (= "e3b0c44298fc1c14" (sh/hash8 "")))))

(deftest test-sh-hash8-abc-def-parity
  (testing "hash8(\"abc def\") matches Python = 010971ea0013a09d"
    (is (= "010971ea0013a09d" (sh/hash8 "abc def")))))

;; ─────────────────────────────────────────────────────────────────────────────
;; shannon: dedup-items
;; ─────────────────────────────────────────────────────────────────────────────

(deftest test-sh-dedup-preserves-first
  (testing "dedup-items keeps first occurrence, drops second identical path+kind"
    (let [items [(sh/make-item "a.ts" "x" 0.5)
                 (sh/make-item "a.ts" "x" 0.5)
                 (sh/make-item "b.ts" "y" 0.3)]
          result (sh/dedup-items items)]
      (is (= 2 (count result))))))

(deftest test-sh-dedup-different-kind
  (testing "dedup-items keeps different kind on same path"
    (let [items [(sh/make-item "a.ts" "x" 0.5)
                 (sh/make-item "a.ts" "z" 0.1)]
          result (sh/dedup-items items)]
      (is (= 2 (count result))))))

(deftest test-sh-dedup-parity
  (testing "dedup-items matches Python _dedup: 4 items → 3 after dedup"
    (let [items [(sh/make-item "a.ts" "x" 0.5)
                 (sh/make-item "a.ts" "x" 0.5)  ; duplicate
                 (sh/make-item "b.ts" "y" 0.3)
                 (sh/make-item "a.ts" "z" 0.1)]
          result (sh/dedup-items items)]
      (is (= 3 (count result)))
      (is (= ["a.ts" "b.ts" "a.ts"] (mapv :path result)))
      (is (= ["x" "y" "z"] (mapv :kind result))))))

;; ─────────────────────────────────────────────────────────────────────────────
;; shannon: go-only-stub / make-check-result
;; ─────────────────────────────────────────────────────────────────────────────

(deftest test-sh-go-only-stub-score
  (testing "go-only-stub returns score 100.0 and 0 violations"
    (let [stub (sh/go-only-stub "code_clone_cross")]
      (is (= "code_clone_cross" (:name stub)))
      (is (= 100.0 (:score stub)))
      (is (= 0 (:violations stub)))
      (is (seq (:details stub))))))

(deftest test-sh-go-only-stub-details-parity
  (testing "go-only-stub details message matches Python _go_only_stub"
    (let [stub (sh/go-only-stub "code_clone_cross")]
      (is (= "not available in Python port — use Go binary: etzhayyim shannon scan"
             (:details stub))))))

(deftest test-sh-make-check-result-score
  (testing "make-check-result: 5 violations out of 20 → score = 75.0"
    (let [chk (sh/make-check-result "test" 5 20 [])]
      (is (= 75.0 (:score chk)))
      (is (= 5 (:violations chk))))))

(deftest test-sh-make-check-result-no-violations
  (testing "make-check-result: 0 violations out of 0 total → score = 100.0"
    (let [chk (sh/make-check-result "test" 0 0 [])]
      (is (= 100.0 (:score chk))))))

;; ─────────────────────────────────────────────────────────────────────────────
;; shannon: ordered-check-names / assemble-checks
;; ─────────────────────────────────────────────────────────────────────────────

(deftest test-sh-ordered-check-names-count
  (testing "ordered-check-names returns 9 checks"
    (is (= 9 (count (sh/ordered-check-names))))))

(deftest test-sh-ordered-check-names-first
  (testing "ordered-check-names starts with claude_md_duplication"
    (is (= "claude_md_duplication" (first (sh/ordered-check-names))))))

(deftest test-sh-assemble-checks-fills-stubs
  (testing "assemble-checks fills Go-only stubs when checks-map is empty"
    (let [checks (sh/assemble-checks {})]
      (is (= 9 (count checks)))
      ;; Go stubs should have score 100.0
      (let [stub (first (filter #(= "code_clone_cross" (:name %)) checks))]
        (is (= 100.0 (:score stub)))))))

(deftest test-sh-assemble-checks-uses-provided
  (testing "assemble-checks uses provided check over stub"
    (let [custom-chk (sh/make-check "claude_md_duplication" 50.0 0.3 3 "3 dupes" [])
          checks (sh/assemble-checks {"claude_md_duplication" custom-chk})]
      (let [found (first (filter #(= "claude_md_duplication" (:name %)) checks))]
        (is (= 50.0 (:score found)))
        (is (= 3 (:violations found)))))))

;; ─────────────────────────────────────────────────────────────────────────────
;; reuse: verify wave-2 exports still accessible via shannon-scores
;; ─────────────────────────────────────────────────────────────────────────────

(deftest test-sh-ss-cap-reuse
  (testing "ss/cap accessible from shannon-scores (reused, not re-ported)"
    (is (= 100.0 (ss/cap 150.0)))
    (is (= 0.0   (ss/cap -5.0)))))

(deftest test-sh-ss-entropy-reuse
  (testing "ss/sh-entropy accessible from shannon-scores (reused, not re-ported)"
    ;; sh-entropy takes a count map (not a vector)
    (is (= 0.0 (ss/sh-entropy {"a" 1})))
    (is (< (Math/abs (- (ss/sh-entropy {"a" 1 "b" 1}) 1.0)) 1e-9))))

;; ─────────────────────────────────────────────────────────────────────────────
;; test runner
;; ─────────────────────────────────────────────────────────────────────────────

(run-tests 'etzhayyim.test-bb-migration-wave6c)
