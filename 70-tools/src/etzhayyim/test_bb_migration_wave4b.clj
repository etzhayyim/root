;; test_bb_migration_wave4b.clj — parity smoke tests for wave-4b cljc ports.
;;
;; Run with:  bb 70-tools/src/etzhayyim/test_bb_migration_wave4b.clj
;; from repo root (classpath 70-tools/src already in bb.edn :paths).
;;
;; Modules ported: bunseki, process_mining, systemofsystem, complex_stubs
;; Module skipped: cohort (XRPC-only thin wrappers, no extractable pure logic)

(ns etzhayyim.test-bb-migration-wave4b
  (:require [clojure.test :refer [deftest is testing run-tests]]
            [etzhayyim.bunseki          :as b]
            [etzhayyim.process-mining   :as pm]
            [etzhayyim.systemofsystem   :as sos]
            [etzhayyim.complex-stubs    :as cs]))

;; ─────────────────────────────────────────────────────────────────────────────
;; bunseki
;; ─────────────────────────────────────────────────────────────────────────────

(deftest test-bunseki-arch-grade
  (testing "arch-grade boundaries"
    (is (= "A" (b/arch-grade 90)))
    (is (= "A" (b/arch-grade 95)))
    (is (= "B" (b/arch-grade 80)))
    (is (= "B" (b/arch-grade 89.9)))
    (is (= "C" (b/arch-grade 70)))
    (is (= "D" (b/arch-grade 60)))
    (is (= "F" (b/arch-grade 55)))
    (is (= "F" (b/arch-grade 0)))))

(deftest test-bunseki-build-traces
  (testing "build-traces groups by auth key"
    (let [events [{:auth "u1" :activity "login"}
                  {:auth "u1" :activity "query"}
                  {:auth "u2" :activity "login"}]
          traces (b/build-traces events)]
      (is (= 2 (count traces)))
      (is (= ["login" "query"] (get traces "u1")))
      (is (= ["login"] (get traces "u2")))))

  (testing "build-traces filters by object-type"
    (let [events [{:auth "u1" :activity "a" :type "T1"}
                  {:auth "u1" :activity "b" :type "T2"}]
          traces (b/build-traces events "T1")]
      (is (= 1 (count traces)))
      (is (= ["a"] (get traces "u1")))))

  (testing "build-traces falls back to method when no auth"
    (let [events [{:method "get-profile" :activity "view"}]
          traces (b/build-traces events)]
      (is (= ["view"] (get traces "get-profile")))))

  (testing "build-traces no activity falls back to method"
    (let [events [{:auth "u1" :method "get-profile"}]
          traces (b/build-traces events)]
      (is (= ["get-profile"] (get traces "u1"))))))

(deftest test-bunseki-build-dfg
  (testing "build-dfg counts transitions"
    ;; u1: login→query→logout (2 pairs), u2: login→query (1 pair)
    ;; unique pairs: login→query (count 2), query→logout (count 1) = 2 unique pairs
    (let [traces {"u1" ["login" "query" "logout"]
                  "u2" ["login" "query"]}
          dfg    (b/build-dfg traces)]
      (is (= 2 (count dfg)))
      (is (= "login" (:from (first dfg))))
      (is (= "query"  (:to   (first dfg))))
      (is (= 2         (:count (first dfg))))))

  (testing "build-dfg empty traces → empty list"
    (is (empty? (b/build-dfg {})))))

(deftest test-bunseki-analyze-variants
  (testing "analyze-variants groups signatures"
    (let [traces {"u1" ["a" "b"]
                  "u2" ["a" "b"]
                  "u3" ["a" "c"]}
          v      (b/analyze-variants traces)]
      (is (= 2 (count v)))
      (is (= 2 (:count (first v))))
      (is (= "a→b" (:variant (first v))))))

  (testing "analyze-variants single trace"
    (let [v (b/analyze-variants {"u1" ["x" "y"]})]
      (is (= 1 (count v)))
      (is (= 100.0 (:freq_pct (first v)))))))

(deftest test-bunseki-compute-score
  (testing "compute-score returns expected keys"
    (let [events [{:auth "u1" :activity "login" :duration_ms 100}
                  {:auth "u1" :activity "query" :duration_ms 200}
                  {:auth "u2" :activity "login" :duration_ms 150}
                  {:auth "u2" :activity "update" :duration_ms 600}]
          traces (b/build-traces events)
          score  (b/compute-score events traces)]
      (is (= 2 (:total_traces score)))
      (is (= 4 (:total_events score)))
      (is (number? (:score score)))))

  (testing "compute-score empty → safe defaults"
    (let [s (b/compute-score [] {})]
      (is (= 0 (:total_traces s)))
      (is (= 0 (:total_events s))))))

(deftest test-bunseki-arch-dfg
  (testing "arch-dfg counts edge pairs"
    (let [edges [{:from_nanoid "a" :to_nanoid "b" :edge_type "invoke"}
                 {:from_nanoid "a" :to_nanoid "b" :edge_type "invoke"}
                 {:from_nanoid "b" :to_nanoid "c" :edge_type "subscribe"}]
          dfg   (b/arch-dfg edges 10)]
      (is (= 2 (count dfg)))
      (is (= 2 (:count (first dfg))))
      (is (= "a" (:from (first dfg))))))

  (testing "arch-dfg respects top limit"
    (let [edges (mapv (fn [i] {:from_nanoid (str "n" i) :to_nanoid "z" :edge_type "invoke"})
                      (range 20))
          dfg   (b/arch-dfg edges 5)]
      (is (= 5 (count dfg))))))

(deftest test-bunseki-arch-conformance
  (testing "arch-conformance naming-convention rule"
    (let [apps  [{:nanoid "abc1234"} {:nanoid "BadNanoid"}]
          conf  (b/arch-conformance apps [])]
      (is (= 3 (count conf)))
      (let [naming (first conf)]
        (is (= "naming-convention" (:rule naming)))
        (is (= 1 (:conformant naming))))))

  (testing "arch-conformance has-edges rule"
    (let [apps  [{:nanoid "abc1234"} {:nanoid "xyz9876"}]
          edges [{:from_nanoid "abc1234" :to_nanoid "xyz9876" :edge_type "invoke"}]
          conf  (b/arch-conformance apps edges)]
      (let [has-edges (second conf)]
        (is (= "has-edges" (:rule has-edges)))
        (is (= 2 (:conformant has-edges)))))))

(deftest test-bunseki-arch-cycles
  (testing "arch-cycles detects simple cycle"
    (let [adj {"a" ["b"] "b" ["a"]}
          res (b/arch-cycles adj 10)]
      (is (pos? (:total_cycles res)))))

  (testing "arch-cycles no cycle in DAG"
    (let [adj {"a" ["b"] "b" ["c"]}
          res (b/arch-cycles adj 10)]
      (is (zero? (:total_cycles res))))))

;; ─────────────────────────────────────────────────────────────────────────────
;; process_mining
;; ─────────────────────────────────────────────────────────────────────────────

(deftest test-pm-compute-summary-empty
  (testing "empty handlers → perfect score"
    (let [s (pm/compute-pm-summary [])]
      (is (= 0  (:total_handlers s)))
      (is (= 0  (:total_bottlenecks s)))
      (is (= 100.0 (:score s)))
      (is (= "S" (:grade s))))))

(deftest test-pm-compute-summary-scoring
  (testing "1 critical reduces score by 25"
    (let [s (pm/compute-pm-summary [{:bottleneck_count 1
                                     :bottlenecks [{:severity "critical"}]}])]
      (is (= 75.0 (:score s)))
      (is (= "A"  (:grade s)))))

  (testing "1 critical + 1 high → 65"
    (let [s (pm/compute-pm-summary [{:bottleneck_count 2
                                     :bottlenecks [{:severity "critical"}
                                                   {:severity "high"}]}])]
      (is (= 65.0 (:score s)))
      (is (= "B"  (:grade s)))))

  (testing "score floors at 0"
    (let [bs (vec (repeat 10 {:severity "critical"}))
          s  (pm/compute-pm-summary [{:bottleneck_count 10 :bottlenecks bs}])]
      (is (= 0.0 (:score s)))
      (is (= "D"  (:grade s))))))

(deftest test-pm-analyze-handler-content
  (testing "detects nested-await"
    (let [r (pm/analyze-handler-content "test.handler" "const a = await x; const b = await y;")]
      (is (some #(= "nested-await" (:pattern %)) (:bottlenecks r)))))

  (testing "detects outbound-fetch"
    (let [r (pm/analyze-handler-content "test.handler" "const r = fetch(url);")]
      (is (some #(= "outbound-fetch" (:pattern %)) (:bottlenecks r)))))

  (testing "detects infinite-loop"
    (let [r (pm/analyze-handler-content "test.handler" "while (true) { doSomething(); }")]
      (is (some #(= "infinite-loop" (:pattern %)) (:bottlenecks r)))))

  (testing "detects repeated-json-parse when >2"
    (let [content "JSON.parse(a); JSON.parse(b); JSON.parse(c);"
          r       (pm/analyze-handler-content "test.handler" content)]
      (is (some #(= "repeated-json-parse" (:pattern %)) (:bottlenecks r)))))

  (testing "no false positives on clean code"
    (let [r (pm/analyze-handler-content "test.handler" "const x = 1 + 2;")]
      (is (zero? (:bottleneck_count r))))))

;; ─────────────────────────────────────────────────────────────────────────────
;; systemofsystem
;; ─────────────────────────────────────────────────────────────────────────────

(deftest test-sos-cluster-layer
  (testing "keyword classification"
    (is (= "identity"  (sos/cluster-layer "auth-service")))
    (is (= "interface" (sos/cluster-layer "yoro-ui")))
    (is (= "infra"     (sos/cluster-layer "pds-worker")))
    (is (= "inference" (sos/cluster-layer "murakumo-llm")))
    (is (= "data"      (sos/cluster-layer "graph-db")))
    (is (= "app"       (sos/cluster-layer "myfeature")))
    (is (= "app"       (sos/cluster-layer "unknown-thing")))))

(deftest test-sos-cohesion
  (testing "cohesion = internal/(internal+external)"
    (is (= 0.75 (sos/cohesion {:internal_edges 3 :external_edges 1})))
    (is (= 1.0  (sos/cohesion {:internal_edges 5 :external_edges 0})))
    (is (= 0.0  (sos/cohesion {:internal_edges 0 :external_edges 4})))
    (is (= 0.0  (sos/cohesion {:internal_edges 0 :external_edges 0})))))

(deftest test-sos-health-verdict
  (testing "health thresholds"
    (is (= "HEALTHY"         (sos/sos-health-verdict 10 70)))
    (is (= "ACCEPTABLE"      (sos/sos-health-verdict 30 50)))
    (is (= "NEEDS ATTENTION" (sos/sos-health-verdict 50 30)))
    (is (= "NEEDS ATTENTION" (sos/sos-health-verdict 20 30)))))

(deftest test-sos-build-nanoid-map
  (testing "nanoid-map inversion"
    (let [clusters [{:name "proj-a" :nanoids ["n1" "n2"]}
                    {:name "proj-b" :nanoids ["n3"]}]
          m        (sos/build-nanoid-map clusters)]
      (is (= 3 (count m)))
      (is (= "proj-a" (m "n1")))
      (is (= "proj-b" (m "n3"))))))

(deftest test-sos-coupling-cohesion
  (testing "coupling and cohesion scores sum to 100 for fully partitioned graph"
    (let [clusters [{:name "a" :nanoids ["n1" "n2"]}
                    {:name "b" :nanoids ["n3" "n4"]}]
          ;; half intra, half cross
          edges    [{:from_nanoid "n1" :to_nanoid "n2"}
                    {:from_nanoid "n3" :to_nanoid "n4"}
                    {:from_nanoid "n1" :to_nanoid "n3"}
                    {:from_nanoid "n2" :to_nanoid "n4"}]
          nm       (sos/build-nanoid-map clusters)
          cp       (sos/coupling-score edges nm)
          co       (sos/cohesion-score edges nm)]
      (is (= 50.0 cp))
      (is (= 50.0 co)))))

(deftest test-sos-layer-groups
  (testing "layer-groups returns grouped map"
    (let [clusters [{:name "auth-svc"} {:name "pds-worker"} {:name "myapp"}]
          groups   (sos/layer-groups clusters)]
      (is (contains? groups "identity"))
      (is (contains? groups "infra"))
      (is (contains? groups "app")))))

(deftest test-sos-cross-cluster-pairs
  (testing "cross-cluster-pairs counts inter-cluster edges"
    (let [clusters [{:name "a" :nanoids ["n1"]}
                    {:name "b" :nanoids ["n2"]}]
          edges    [{:from_nanoid "n1" :to_nanoid "n2"}
                    {:from_nanoid "n1" :to_nanoid "n2"}]
          pairs    (sos/cross-cluster-pairs clusters edges)]
      (is (= 1 (count pairs)))
      (is (= 2 (:edge_count (first pairs)))))))

;; ─────────────────────────────────────────────────────────────────────────────
;; complex_stubs
;; ─────────────────────────────────────────────────────────────────────────────

(deftest test-cs-parse-duration
  (testing "parses duration strings"
    (is (= 30   (cs/parse-duration "30s")))
    (is (= 120  (cs/parse-duration "2m")))
    (is (= 300  (cs/parse-duration "1h")))    ; 3600 capped to 300
    (is (= 300  (cs/parse-duration "999s")))  ; >300 capped
    (is (= 60   (cs/parse-duration "60")))    ; bare number = seconds
    ))

(deftest test-cs-date-check
  (testing "YYYY-MM-DD valid"
    (is (cs/date? "2026-06-21"))
    (is (cs/date? "2000-01-01")))
  (testing "invalid dates"
    (is (not (cs/date? "2026-6-21")))   ; month not 2-digit
    (is (not (cs/date? "notadate")))
    (is (not (cs/date? "2026/06/21")))
    (is (not (cs/date? "")))))

(deftest test-cs-strip-jsonc-comments
  (testing "removes // line comments"
    (let [out (cs/strip-jsonc-comments "{\"a\": 1 // comment\n}")]
      (is (not (clojure.string/includes? out "//")))
      (is (clojure.string/includes? out "\"a\""))))
  (testing "preserves // inside strings"
    (let [out (cs/strip-jsonc-comments "{\"url\": \"http://example.com\"}")]
      (is (clojure.string/includes? out "http://example.com")))))

(deftest test-cs-parse-toml-array
  (testing "parses quoted comma-separated array"
    (is (= ["a" "b" "c"] (cs/parse-toml-array "[\"a\", \"b\", \"c\"]"))))
  (testing "handles single-quoted values"
    (is (= ["x"] (cs/parse-toml-array "['x']"))))
  (testing "returns empty vec for empty array"
    (is (= [] (cs/parse-toml-array "[]")))
    (is (= [] (cs/parse-toml-array ""))))
  (testing "strips trailing commas"
    (is (= ["a" "b"] (cs/parse-toml-array "[\"a\", \"b\",]")))))

(deftest test-cs-parse-front-matter
  (testing "parses scalar fields"
    (let [{:keys [result error]}
          (cs/parse-front-matter "---\nid: my-doc\ntitle: Hello World\nstatus: active\n---\n# Body")]
      (is (nil? error))
      (is (= "my-doc"      (get result "id")))
      (is (= "Hello World" (get result "title")))
      (is (= "active"      (get result "status")))))

  (testing "parses boolean fields"
    (let [{:keys [result]}
          (cs/parse-front-matter "---\nauthor: bob\nauthoritative: true\n---")]
      (is (= true (get result "authoritative")))))

  (testing "error on missing opening delimiter"
    (let [{:keys [error]}
          (cs/parse-front-matter "# No front matter")]
      (is (string? error))
      (is (clojure.string/includes? error "opening"))))

  (testing "error on missing closing delimiter"
    (let [{:keys [error]}
          (cs/parse-front-matter "---\nid: test\n")]
      (is (string? error))
      (is (clojure.string/includes? error "closing"))))

  (testing "parses quoted string values"
    (let [{:keys [result]}
          (cs/parse-front-matter "---\ntitle: \"My Title\"\n---")]
      (is (= "My Title" (get result "title"))))))

;; ─────────────────────────────────────────────────────────────────────────────
;; Run all tests
;; ─────────────────────────────────────────────────────────────────────────────

(run-tests 'etzhayyim.test-bb-migration-wave4b)
