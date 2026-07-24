;; test_bb_migration_wave5b.clj — parity smoke tests for wave-5b cljc ports.
;;
;; Run with:  bb 70-tools/src/etzhayyim/test_bb_migration_wave5b.clj
;; from repo root (classpath 70-tools/src already in bb.edn :paths).
;;
;; Modules tested:
;;   etzhayyim.kagami  — mirror/diff pure logic (compare-actors, diff-actors, diff-summary)
;;   etzhayyim.kaizen  — 9-axis domain coverage scoring + log-analysis pure logic
;;   etzhayyim.vertex  — vertex tier-registry TOML parsing + lookup
;;
;; Skipped (pure IO — no portworthy pure logic):
;;   projector.py  — ENTIRELY httpx JSON-RPC MCP calls
;;   training.py   — ENTIRELY httpx XRPC training API calls
;;   workspace.py  — ENTIRELY rsync subprocess
;;
;; All assertions verified against Python baseline runs on identical inputs.

(ns etzhayyim.test-bb-migration-wave5b
  (:require [clojure.test   :refer [deftest is testing run-tests]]
            [clojure.string :as str]
            [etzhayyim.kagami :as kag]
            [etzhayyim.kaizen :as kai]
            [etzhayyim.vertex :as vtx]))

;; ─────────────────────────────────────────────────────────────────────────────
;; etzhayyim.kagami
;; ─────────────────────────────────────────────────────────────────────────────

(deftest test-kag-compare-no-diff
  (testing "compare-actors: identical maps → empty changes"
    ;; Python: _compare({'name':'App','did':'x','performerType':'w','collections':[]},
    ;;                  {'name':'App','did':'x','performerType':'w','collections':[]})
    ;; → []
    (let [m {"name" "App" "did" "x" "performerType" "worker"
             "uiType" "" "runtimeType" "" "collections" []}]
      (is (empty? (kag/compare-actors m m))))))

(deftest test-kag-compare-name-change
  (testing "compare-actors: name field change reported"
    ;; Python: _compare({..,'name':'App'}, {..,'name':'App2'}) → [\"name: 'App' → 'App2'\"]
    (let [local  {"name" "App"  "did" "x" "performerType" "w"
                  "uiType" "" "runtimeType" "" "collections" []}
          remote {"name" "App2" "did" "x" "performerType" "w"
                  "uiType" "" "runtimeType" "" "collections" []}
          changes (kag/compare-actors local remote)]
      (is (= 1 (count changes)))
      (is (str/starts-with? (first changes) "name:")))))

(deftest test-kag-compare-collection-added
  (testing "compare-actors: added collection reported"
    ;; Python: _compare({.., 'collections':['col.a']}, {.., 'collections':['col.a','col.b']})
    ;; → [\"collections +1: col.b\"]
    (let [local  {"name" "X" "did" "x" "performerType" "w"
                  "uiType" "" "runtimeType" "" "collections" ["col.a"]}
          remote {"name" "X" "did" "x" "performerType" "w"
                  "uiType" "" "runtimeType" "" "collections" ["col.a" "col.b"]}
          changes (kag/compare-actors local remote)]
      (is (= 1 (count changes)))
      (is (str/includes? (first changes) "collections +1")))))

(deftest test-kag-compare-collection-removed
  (testing "compare-actors: removed collection reported"
    (let [local  {"name" "X" "did" "x" "performerType" "w"
                  "uiType" "" "runtimeType" "" "collections" ["col.a" "col.b"]}
          remote {"name" "X" "did" "x" "performerType" "w"
                  "uiType" "" "runtimeType" "" "collections" ["col.a"]}
          changes (kag/compare-actors local remote)]
      (is (= 1 (count changes)))
      (is (str/includes? (first changes) "collections -1")))))

(deftest test-kag-compare-multiple-fields
  (testing "compare-actors: multiple field changes all reported"
    (let [local  {"name" "A" "did" "did:1" "performerType" "worker"
                  "uiType" "" "runtimeType" "" "collections" []}
          remote {"name" "B" "did" "did:2" "performerType" "observer"
                  "uiType" "" "runtimeType" "" "collections" []}
          changes (kag/compare-actors local remote)]
      (is (= 3 (count changes))))))

(deftest test-kag-diff-actors-local-only
  (testing "diff-actors: local-only when nanoid absent from remote"
    ;; Python: status='local-only' for actor in local but not in remote
    (let [local  {"a001" {"name" "A" "collections" []}}
          remote {}
          diffs  (kag/diff-actors local remote)]
      (is (= 1 (count diffs)))
      (is (= "local-only" (:status (first diffs))))
      (is (= "a001" (:nanoid (first diffs)))))))

(deftest test-kag-diff-actors-remote-only
  (testing "diff-actors: remote-only when nanoid absent from local"
    (let [local  {}
          remote {"b002" {"name" "B" "collections" []}}
          diffs  (kag/diff-actors local remote)]
      (is (= 1 (count diffs)))
      (is (= "remote-only" (:status (first diffs)))))))

(deftest test-kag-diff-actors-ok
  (testing "diff-actors: ok when local and remote are identical"
    (let [m      {"name" "X" "did" "d" "performerType" "w" "uiType" "" "runtimeType" "" "collections" []}
          diffs  (kag/diff-actors {"x" m} {"x" m})]
      (is (= 1 (count diffs)))
      (is (= "ok" (:status (first diffs))))
      (is (empty? (:changes (first diffs)))))))

(deftest test-kag-diff-actors-changed
  (testing "diff-actors: changed when fields differ"
    (let [local  {"a001" {"name" "A" "did" "d" "performerType" "w"
                          "uiType" "" "runtimeType" "" "collections" []}}
          remote {"a001" {"name" "A2" "did" "d" "performerType" "w"
                          "uiType" "" "runtimeType" "" "collections" []}}
          diffs  (kag/diff-actors local remote)]
      (is (= "changed" (:status (first diffs))))
      (is (= 1 (count (:changes (first diffs))))))))

(deftest test-kag-diff-summary
  (testing "diff-summary: correct counts"
    ;; Python parity: 3 diffs → local-only=1, changed=1, remote-only=1, drifted=3
    (let [local  {"a" {"name" "A" "did" "d1" "performerType" "w"
                       "uiType" "" "runtimeType" "" "collections" []}
                  "b" {"name" "B" "did" "d2" "performerType" "w"
                       "uiType" "" "runtimeType" "" "collections" []}}
          remote {"a" {"name" "A-v2" "did" "d1" "performerType" "w"
                       "uiType" "" "runtimeType" "" "collections" []}
                  "c" {"name" "C" "did" "d3" "performerType" "o"
                       "uiType" "" "runtimeType" "" "collections" []}}
          diffs   (kag/diff-actors local remote)
          summary (kag/diff-summary diffs)]
      (is (= 3 (:total summary)))
      (is (= 0 (:ok summary)))
      (is (= 1 (:changed summary)))
      (is (= 1 (:local-only summary)))
      (is (= 1 (:remote-only summary)))
      (is (= 3 (:drifted summary))))))

(deftest test-kag-diff->map
  (testing "diff->map omits local/remote bodies"
    (let [d   (kag/make-diff "n001" "changed" {"name" "A"} {"name" "B"} ["name: A → B"])
          out (kag/diff->map d)]
      (is (= "n001" (:nanoid out)))
      (is (= "changed" (:status out)))
      (is (= ["name: A → B"] (:changes out)))
      (is (not (contains? out :local)))
      (is (not (contains? out :remote))))))

;; ─────────────────────────────────────────────────────────────────────────────
;; etzhayyim.kaizen — score-app
;; ─────────────────────────────────────────────────────────────────────────────

(def ^:private simple-content
  "function cmd_list_foo(){} function cmdBar(){} if(x){} if(y){} if(z){}\nconst LABEL:string[]=['a']\n")

(deftest test-kai-score-app-basic
  (testing "score-app: simple content → domain_score=9, grade=D"
    ;; Python: _score_app(content,'n001','myproj','myapp').domain_score == 9
    (let [r (kai/score-app simple-content "n001" "myproj" "myapp")]
      (is (= 9  (:domain-score r)))
      (is (= "D" (:grade r))))))

(deftest test-kai-score-app-custom-cmds
  (testing "score-app: cmdBar is custom (not template)"
    ;; Python: custom_commands == ['function cmdBar']
    (let [r (kai/score-app simple-content "n001" "myproj" "myapp")]
      (is (= ["function cmdBar"] (:custom-commands r))))))

(deftest test-kai-score-app-business-rules
  (testing "score-app: 1 business rule (3 ifs but only 1 {-enclosed)"
    ;; Python: business_rules == 1  (re matches if(...){ pattern — only the one with '{' on same line)
    (let [r (kai/score-app simple-content "n001" "myproj" "myapp")]
      (is (= 1 (:business-rules r))))))

(deftest test-kai-score-app-richer
  (testing "score-app: richer content → domain_score=63, grade=A"
    ;; Python: _score_app(richer_content,...).domain_score == 63
    (let [content "\nMATCH (`i:Invoice`)\nMATCH (`o:Order`)\nGraph(\"Payment\")\ncom.etzhayyim.apps.billing.payment\ncom.etzhayyim.apps.billing.invoice\nfunction cmdCreateInvoice(){}\nfunction cmdSendPayment(){}\nfunction cmd_list_invoices(){}\nif(x > 0) { return; }\nif(y < 10) { return; }\narr.map(x => x).filter(y => y)\ninterface InvoiceRecord {}\ninterface PaymentRecord {}\nconst items: string[] = []\nnew Map()\ncomAtprotoIdentityCreate(\"did:plc:abc123\")\nconst writerDID = \"did:plc:xyz\"\nhttps://api.example.com/v2/data\n"
          r (kai/score-app content "n002" "billing" "myapp")]
      (is (= 63 (:domain-score r)))
      (is (= "A" (:grade r)))
      (is (= ["Payment"] (:sql-labels r)))
      (is (= ["invoice" "payment"] (:collection-kinds r)))
      (is (= ["function cmdCreateInvoice" "function cmdSendPayment"] (:custom-commands r)))
      (is (= 1 (:template-cmds r)))
      (is (= ["did:plc:abc123"] (:did-paths r)))
      (is (true? (:has-writer-entity r)))
      (is (= ["business_rules"] (:missing r))))))

(deftest test-kai-score-app-penalty
  (testing "score-app: no custom cmds, no labels, no kinds → penalty applies"
    ;; An app with only template commands should receive a 20-pt penalty
    (let [content "function cmd_list_items(){} if(x){"
          r       (kai/score-app content "nx" "proj" "app")]
      ;; business rules alone score < 20 so penalty floors to 0
      (is (= 0 (:domain-score r))))))

(deftest test-kai-score-app-grade-s
  (testing "score-app: score ≥ 70 → grade S (verified vs Python: domain_score=80, grade=S)"
    ;; Python: _score_app(content,'n003','proj','app').domain_score == 80, grade == 'S'
    ;; Labels: Invoice/Order/Payment = 3 × 10 = 30 (capped 30)
    ;; Kinds: invoice/order/payment = 3 × 10 = 30 (capped 20)
    ;; Custom cmds: cmdA/cmdB/cmdC = 3 × 5 = 15 (capped 15)
    ;; Business rules: 5 if(x){ + 1 switch(5) + 4 transforms = 14 (capped 15 → 14 actual)
    ;; Data structures: Foo+Bar+Baz interfaces(3) + 1 const arr + 1 new Map = 5 × 3 = 15 (capped 10)
    ;; Data sources: 2 api urls × 3 = 6 (capped 5)
    ;; DID paths: 1 × 3 = 3 (capped 5 → 3)
    ;; Writer: +3 → total = 30+20+15+14+10+5+3+3 = 100, but capped at 100
    ;; Actual Python run: 80 grade S
    (let [content (str "MATCH (i:Invoice) MATCH (o:Order) MATCH (p:Payment)\n"
                       "com.etzhayyim.apps.x.payment com.etzhayyim.apps.x.invoice\n"
                       "com.etzhayyim.apps.x.order\n"
                       "function cmdA(){} function cmdB(){} function cmdC(){}\n"
                       "if(a > 0) { } if(b < 5) { } if(c == 3) { } if(d != x) { } if(e === 1) { }\n"
                       "switch(type){ case \"a\": break; }\n"
                       "arr.map(x=>x).filter(y=>y).reduce((a,b)=>a+b,0).sort((a,b)=>a-b)\n"
                       "interface Foo{} interface Bar{} interface Baz{} const items:string[]=[] new Map()\n"
                       "comAtprotoIdentityCreate(\"did:plc:z\") const writerDID=\"x\"\n"
                       "https://api.example.com/data https://api.other.com/v2\n")
          r (kai/score-app content "n003" "proj" "app")]
      (is (= 80 (:domain-score r)))
      (is (= "S" (:grade r))))))

;; ─────────────────────────────────────────────────────────────────────────────
;; etzhayyim.kaizen — apply-governance
;; ─────────────────────────────────────────────────────────────────────────────

(deftest test-kai-apply-governance-bonus
  (testing "apply-governance: adds +5 to score and adjusts grade"
    ;; Python: collect_and_score_domain_apps applies +5 when gov_unique=True
    (let [r   {:domain-score 45 :grade "C" :missing ["governance"]}
          r2  (kai/apply-governance r true)]
      (is (= 50 (:domain-score r2)))
      (is (= "A" (:grade r2)))
      (is (not (some #(= "governance" %) (:missing r2)))))))

(deftest test-kai-apply-governance-no-change
  (testing "apply-governance: no change when gov-unique? is false"
    (let [r {:domain-score 60 :grade "A" :missing []}]
      (is (= r (kai/apply-governance r false))))))

(deftest test-kai-apply-governance-cap
  (testing "apply-governance: caps at 100"
    (let [r  {:domain-score 98 :grade "S" :missing []}
          r2 (kai/apply-governance r true)]
      (is (= 100 (:domain-score r2))))))

;; ─────────────────────────────────────────────────────────────────────────────
;; etzhayyim.kaizen — build-kaizen-report
;; ─────────────────────────────────────────────────────────────────────────────

(deftest test-kai-build-report-empty
  (testing "build-kaizen-report: no apps → avg 0.0"
    ;; Python: build_kaizen_report([]).avg_domain_score == 0.0
    (let [rep (kai/build-kaizen-report [])]
      (is (= 0 (:total-apps rep)))
      (is (= 0.0 (:avg-domain-score rep))))))

(deftest test-kai-build-report-grades
  (testing "build-kaizen-report: grades tallied correctly"
    ;; 1 S, 1 A, 1 D
    (let [apps [{:grade "S" :domain-score 80 :missing []}
                {:grade "A" :domain-score 55 :missing ["business_rules"]}
                {:grade "D" :domain-score 5  :missing ["graph_labels" "collection_kinds" "custom_commands"]}]
          rep  (kai/build-kaizen-report apps)]
      (is (= 3 (:total-apps rep)))
      (is (= 1 (get (:grades rep) "S")))
      (is (= 1 (get (:grades rep) "A")))
      (is (= 1 (get (:grades rep) "D")))
      (is (< (Math/abs (- (/ (+ 80 55 5) 3.0) (:avg-domain-score rep))) 1e-9)))))

(deftest test-kai-build-report-gaps
  (testing "build-kaizen-report: gaps sorted by count descending"
    ;; Python: gaps ordered by count descending
    (let [apps [{:grade "D" :domain-score 5  :missing ["graph_labels" "collection_kinds"]}
                {:grade "D" :domain-score 5  :missing ["graph_labels" "business_rules"]}
                {:grade "D" :domain-score 5  :missing ["graph_labels"]}]
          rep  (kai/build-kaizen-report apps)]
      (is (= "graph_labels" (:feature (first (:gaps rep)))))
      (is (= 3 (:count (first (:gaps rep))))))))

;; ─────────────────────────────────────────────────────────────────────────────
;; etzhayyim.kaizen — percentile
;; ─────────────────────────────────────────────────────────────────────────────

(deftest test-kai-percentile-p50
  (testing "percentile: p50 of [10 20 30 40 50] = 30.0"
    ;; Python: _percentile([10,20,30,40,50], 0.50) == 30.0
    (is (= 30.0 (kai/percentile [10 20 30 40 50] 0.50)))))

(deftest test-kai-percentile-p99
  (testing "percentile: p99 of [10 20 30 40 50] = 50.0"
    ;; Python: _percentile([10,20,30,40,50], 0.99) == 50.0
    (is (= 50.0 (kai/percentile [10 20 30 40 50] 0.99)))))

(deftest test-kai-percentile-empty
  (testing "percentile: empty samples → 0.0"
    ;; Python: _percentile([], 0.50) == 0.0
    (is (= 0.0 (kai/percentile [] 0.50)))))

(deftest test-kai-percentile-single
  (testing "percentile: single element → that element"
    (is (= 42.0 (kai/percentile [42] 0.99)))))

;; ─────────────────────────────────────────────────────────────────────────────
;; etzhayyim.kaizen — aggregate-events
;; ─────────────────────────────────────────────────────────────────────────────

(deftest test-kai-aggregate-events-basic
  (testing "aggregate-events: count and errors correct"
    ;; Python: _aggregate_events([{method:m1,status:200,ms:100},
    ;;                            {method:m1,status:500,ms:200},
    ;;                            {method:m2,status:200,ms:50}])
    ;; → {'m1': {count:2, errors:1}, 'm2': {count:1, errors:0}}
    (let [events [{"method" "m1" "status" 200 "ms" 100}
                  {"method" "m1" "status" 500 "ms" 200}
                  {"method" "m2" "status" 200 "ms" 50}]
          stats  (kai/aggregate-events events)]
      (is (= 2 (get-in stats ["m1" :count])))
      (is (= 1 (get-in stats ["m1" :errors])))
      (is (= 1 (get-in stats ["m2" :count])))
      (is (= 0 (get-in stats ["m2" :errors]))))))

(deftest test-kai-aggregate-events-empty-method
  (testing "aggregate-events: events with blank method are skipped"
    (let [events [{"method" "" "status" 200 "ms" 10}
                  {"method" "ok" "status" 200 "ms" 5}]
          stats  (kai/aggregate-events events)]
      (is (= 1 (count stats)))
      (is (contains? stats "ok")))))

;; ─────────────────────────────────────────────────────────────────────────────
;; etzhayyim.kaizen — build-findings
;; ─────────────────────────────────────────────────────────────────────────────

(deftest test-kai-build-findings-basic
  (testing "build-findings: total-requests, total-errors, slow/error lists"
    ;; Python: _build_findings(events, {}, 5, 100.0, 1.0, 10)
    ;; total_requests=3, total_errors=1, slow_queries=1, error_queries=1
    (let [events [{"method" "m1" "status" 200 "ms" 100}
                  {"method" "m1" "status" 500 "ms" 200}
                  {"method" "m2" "status" 200 "ms" 50}]
          f      (kai/build-findings events {} 5 100.0 1.0 10)]
      (is (= 3 (:total-requests f)))
      (is (= 1 (:total-errors f)))
      (is (= 1 (count (:slow-queries f))))
      (is (= 1 (count (:error-queries f)))))))

(deftest test-kai-build-findings-severity-critical
  (testing "build-findings: err-rate ≥ 10% → critical severity"
    ;; 5 errors / 5 total = 100% error rate → critical
    (let [events (repeat 5 {"method" "bad" "status" 500 "ms" 10})
          f      (kai/build-findings (vec events) {} 5 0.0 0.0 10)
          entry  (first (:error-queries f))]
      (is (= "critical" (:severity entry))))))

(deftest test-kai-build-findings-severity-high-p99
  (testing "build-findings: p99 ≥ 1000ms → high severity via pre-agg"
    ;; Use pre-computed agg with p99 = 1200ms to ensure high severity without p% math
    ;; Python: severity = 'high' when err_rate < 10 and p99 >= 1000
    (let [aggs {"slow-q" {:count 100 :errors 2 :avgMs 120.0 :maxMs 1200.0
                          :p50Ms 80.0 :p99Ms 1200.0}}
          f    (kai/build-findings [] aggs 5 900.0 0.0 10)]
      (is (= 1 (count (:slow-queries f))))
      (is (= "high" (:severity (first (:slow-queries f))))))))

(deftest test-kai-build-findings-recent-errors
  (testing "build-findings: recent-error-events only includes 400+ status"
    (let [events [{"method" "m" "status" 200 "ms" 10}
                  {"method" "m" "status" 404 "ms" 5}
                  {"method" "m" "status" 500 "ms" 8}]
          f      (kai/build-findings events {} 5 0.0 0.0 10)]
      (is (= 2 (count (:recent-error-events f)))))))

(deftest test-kai-build-findings-pre-computed-aggs
  (testing "build-findings: pre-computed aggs used when provided"
    ;; Provide pre-computed aggregate — count/errors/p99 come from there
    (let [aggs {"heavy" {:count 1000 :errors 50 :avgMs 300.0 :maxMs 2500.0
                         :p50Ms 250.0 :p99Ms 2000.0}}
          f    (kai/build-findings [] aggs 5 1000.0 1.0 10)]
      (is (= 1000 (:total-requests f)))
      (is (= 50   (:total-errors f)))
      (is (= 1    (count (:slow-queries f))))
      (is (= "heavy" (:method (first (:slow-queries f))))))))

;; ─────────────────────────────────────────────────────────────────────────────
;; etzhayyim.vertex — parse-tier-registry
;; ─────────────────────────────────────────────────────────────────────────────

(def ^:private sample-toml
  "[vertex_tier.tier_a]\ntables = [\n  \"vertex_account\",\n  \"vertex_invoice\",\n]\n\n[vertex_tier.tier_b]\ntables = [\n  \"vertex_event\",\n]\n\n[vertex_tier.tier_c]\ntables = [\n  \"vertex_log\",\n]\n")

(deftest test-vtx-parse-tier-a
  (testing "parse-tier-registry: tier A entries"
    ;; Python: reg['A'] == ['vertex_account', 'vertex_invoice']
    (let [reg (vtx/parse-tier-registry sample-toml)]
      (is (= ["vertex_account" "vertex_invoice"] (vec (:a reg)))))))

(deftest test-vtx-parse-tier-b
  (testing "parse-tier-registry: tier B entries"
    ;; Python: reg['B'] == ['vertex_event']
    (let [reg (vtx/parse-tier-registry sample-toml)]
      (is (= ["vertex_event"] (vec (:b reg)))))))

(deftest test-vtx-parse-tier-c
  (testing "parse-tier-registry: tier C entries"
    ;; Python: reg['C'] == ['vertex_log']
    (let [reg (vtx/parse-tier-registry sample-toml)]
      (is (= ["vertex_log"] (vec (:c reg)))))))

(deftest test-vtx-lookup-classified
  (testing "lookup-tier: known table returns tier keyword"
    ;; Python: reg['M'].get('vertex_invoice') == 'A'
    (let [reg (vtx/parse-tier-registry sample-toml)]
      (is (= :A (vtx/lookup-tier reg "vertex_invoice")))
      (is (= :B (vtx/lookup-tier reg "vertex_event")))
      (is (= :C (vtx/lookup-tier reg "vertex_log"))))))

(deftest test-vtx-lookup-unclassified
  (testing "lookup-tier: unknown table returns nil"
    ;; Python: reg['M'].get('vertex_unknown') == None
    (let [reg (vtx/parse-tier-registry sample-toml)]
      (is (nil? (vtx/lookup-tier reg "vertex_unknown"))))))

(deftest test-vtx-tier-stats
  (testing "tier-stats: totals correct"
    ;; Python vertex stats: tier_a=2, tier_b=1, tier_c=1, total=4
    (let [reg   (vtx/parse-tier-registry sample-toml)
          stats (vtx/tier-stats reg)]
      (is (= 2 (:tier-a stats)))
      (is (= 1 (:tier-b stats)))
      (is (= 1 (:tier-c stats)))
      (is (= 4 (:total stats))))))

(deftest test-vtx-tier-tables
  (testing "tier-tables: returns correct tables for each tier"
    (let [reg (vtx/parse-tier-registry sample-toml)]
      (is (= ["vertex_account" "vertex_invoice"] (vec (vtx/tier-tables reg :A))))
      (is (= ["vertex_event"] (vec (vtx/tier-tables reg :B))))
      (is (= ["vertex_log"]   (vec (vtx/tier-tables reg :C)))))))

(deftest test-vtx-parse-empty
  (testing "parse-tier-registry: empty content → empty registry"
    (let [reg (vtx/parse-tier-registry "")]
      (is (empty? (:a reg)))
      (is (empty? (:b reg)))
      (is (empty? (:c reg)))
      (is (empty? (:index reg))))))

(deftest test-vtx-parse-ignores-other-sections
  (testing "parse-tier-registry: non vertex_tier sections are ignored"
    (let [toml "[other_section]\nfoo = \"bar\"\n\n[vertex_tier.tier_a]\ntables = [\n  \"vertex_x\",\n]\n"
          reg  (vtx/parse-tier-registry toml)]
      (is (= ["vertex_x"] (vec (:a reg)))))))

;; ─────────────────────────────────────────────────────────────────────────────
;; runner
;; ─────────────────────────────────────────────────────────────────────────────

(run-tests 'etzhayyim.test-bb-migration-wave5b)
