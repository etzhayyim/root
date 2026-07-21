;; kaizen.cljc — Domain coverage analysis + log quality analysis, pure logic.
;;
;; Ports the pure-logic subset of etzhayyim-py kaizen.py:
;;   - score-app        : regex-based 9-axis scoring on app.ts content strings
;;   - check-governance : nanoid + governance-uniqueness from a kotodama.jsonld map
;;   - build-kaizen-report : aggregate DomainAppReport list → KaizenReport
;;   - percentile       : sample-based percentile (p50/p99 etc.)
;;   - aggregate-events : per-method stats from raw event maps
;;   - build-findings   : slow/error finding lists from events + pre-aggregated stats
;;   - build-kaizen-logs-prompt : human-readable kaizen-logs LLM prompt text
;;
;; IO (fs walks, httpx, subprocess) is DEFERRED — operator bb legs only.
;;
;; ns: etzhayyim.kaizen
;; Load check: bb --classpath 70-tools/src -e "(require 'etzhayyim.kaizen)(println :ok)"

(ns etzhayyim.kaizen
  (:require [clojure.string :as str]))

;; ── regex patterns (ported from domain_coverage_check.go) ────────────────────

(def ^:private re-sql-label
  #"(?:MATCH\s*\(\w:|Graph\(\")([\w]+)")

(def ^:private re-collection-kind
  #"com\.etzhayyim\.apps\.\w+\.(\w+)")

(def ^:private re-template-cmds
  #"function cmd_(?:list|get|search|create|wave|stats|export|describe|summarize|ingest|audit|health)_\w+|function cmd(?:Stats|ExportData|Describe|Summarize|Audit|Ingest|GetInfo|GetStatus)\b")

(def ^:private re-custom-cmds
  #"function cmd[A-Z]\w+|function cmd_[a-z]\w+")

(def ^:private re-if-branch
  #"if\s*\(.+\)\s*\{")

(def ^:private re-switch-case
  #"\bswitch\b|\bcase\s+[\"']")

(def ^:private re-transform
  #"\.map\(|\.filter\(|\.reduce\(|\.sort\(|\.forEach\(")

(def ^:private re-rss-url
  #"https?://[^\s\"]+\.(?:xml|rss|rdf|atom|json)")

(def ^:private re-api-url
  #"https?://(?:api\.|www\.)[^\s\"]+")

(def ^:private re-did-path
  #"comAtprotoIdentityCreate\(\s*\"([^\"]+)\"")

(def ^:private re-writer-entity
  #"WriterEntity|writerDID|writer_did")

(def ^:private re-dc-interface
  #"(?m)^interface\s+\w+")

(def ^:private re-const-array
  #"const\s+\w+(?:\s*:\s*\w+\[\])?\s*=\s*\[")

(def ^:private re-new-map
  #"new Map")

(def ^:private generic-labels #{"Record" "n" "Entity"})
(def ^:private generic-kinds  #{"record"})
(def ^:private default-gov    "{\"raci\":\"responsible\",\"classification\":\"internal\",\"complianceFrameworks\":[]}")

;; ── regex helpers ─────────────────────────────────────────────────────────────

(defn- find-all-groups
  "Return distinct non-generic group-1 captures from re in s."
  [re s excludes]
  (->> (re-seq re s)
       (map second)                         ; group 1
       (remove nil?)
       (remove excludes)
       distinct
       sort
       vec))

(defn- count-matches [re s]
  (count (re-seq re s)))

;; ── scoring ───────────────────────────────────────────────────────────────────

(defn score-app
  "9-axis domain coverage scoring on a TypeScript app.ts content string.
   Returns a DomainAppReport map (keys are keywords).

   Python equivalent: _score_app(content, nanoid, project, app)"
  [content nanoid project app]
  (let [lines          (count (str/split-lines (str/trim content)))
        labels         (find-all-groups re-sql-label content generic-labels)
        kinds          (find-all-groups re-collection-kind content generic-kinds)
        ;; re-seq with non-capturing-only groups returns plain strings (not vectors)
        template-cmds  (set (re-seq re-template-cmds content))
        all-cmds       (re-seq re-custom-cmds content)
        custom-cmds    (vec (remove template-cmds all-cmds))
        br-if          (count-matches re-if-branch content)
        br-switch      (if (re-find re-switch-case content) 5 0)
        br-transform   (count-matches re-transform content)
        business-rules (+ br-if br-switch br-transform)
        data-sources   (+ (count-matches re-rss-url content)
                          (count-matches re-api-url content))
        did-paths      (vec (map second (re-seq re-did-path content)))
        has-writer     (boolean (re-find re-writer-entity content))
        custom-ifaces  (count-matches re-dc-interface content)
        const-arrays   (count-matches re-const-array content)
        const-maps     (count-matches re-new-map content)

        ;; scoring
        raw-score (cond-> 0
                    true (+ (min (* (count labels) 10) 30))
                    true (+ (min (* (count kinds)  10) 20))
                    true (+ (min (* (count custom-cmds) 5) 15))
                    true (+ (min business-rules 15))
                    true (+ (min (* (+ custom-ifaces const-arrays const-maps) 3) 10))
                    true (+ (min (* data-sources 3) 5))
                    true (+ (min (* (count did-paths) 3) 5))
                    has-writer (+ 3))
        ;; penalty: template-only
        penalised (if (and (empty? custom-cmds) (empty? labels) (empty? kinds))
                    (max (- raw-score 20) 0)
                    raw-score)
        score     (min penalised 100)
        grade     (cond (>= score 70) "S"
                        (>= score 50) "A"
                        (>= score 30) "B"
                        (>= score 15) "C"
                        :else         "D")
        missing   (cond-> []
                    (empty? labels)            (conj "graph_labels")
                    (empty? kinds)             (conj "collection_kinds")
                    (empty? custom-cmds)       (conj "custom_commands")
                    (< business-rules 5)       (conj "business_rules"))]
    {:project         project
     :app             app
     :nanoid          nanoid
     :domain-score    score
     :grade           grade
     :lines           lines
     :sql-labels      labels
     :collection-kinds kinds
     :custom-commands custom-cmds
     :template-cmds   (count template-cmds)
     :business-rules  business-rules
     :data-sources    data-sources
     :did-paths       did-paths
     :governance-unique false     ; caller applies gov check separately
     :has-writer-entity has-writer
     :missing         missing}))

;; ── governance check ──────────────────────────────────────────────────────────

(defn check-governance
  "Given the parsed JSON data map from kotodama.jsonld, return
   [nanoid governance-unique?].
   Pure function — caller supplies the already-parsed map.
   Uses cheshire.core for JSON serialisation (available in bb).

   Python equivalent: _check_governance(path) (file read extracted by caller)"
  [data]
  (let [nanoid (get data "nanoid" "")
        gov    (get data "governance" ::missing)]
    (if (= gov ::missing)
      [nanoid false]
      (try
        (let [gov-str (cheshire.core/generate-string gov)]
          [nanoid (not= gov-str default-gov)])
        (catch Exception _
          [nanoid true])))))

(defn check-governance-map
  "Accepts the parsed gov value directly (already extracted from kotodama.jsonld).
   Returns governance-unique? boolean. Pass nil for gov when key is absent."
  [_nanoid gov]
  (if (nil? gov)
    false
    (try
      (not= (cheshire.core/generate-string gov) default-gov)
      (catch Exception _
        true))))

;; ── apply governance adjustment ───────────────────────────────────────────────

(defn apply-governance
  "Apply governance uniqueness bonus to a DomainAppReport map.
   Returns updated report.

   Python equivalent: the gov_unique branch inside collect_and_score_domain_apps."
  [report gov-unique?]
  (if-not gov-unique?
    report
    (let [new-score (min (+ (:domain-score report) 5) 100)
          new-grade (cond (>= new-score 70) "S"
                          (>= new-score 50) "A"
                          (>= new-score 30) "B"
                          (>= new-score 15) "C"
                          :else             "D")]
      (assoc report
             :governance-unique true
             :domain-score      new-score
             :grade             new-grade
             :missing           (vec (remove #(= "governance" %) (:missing report)))))))

;; ── kaizen report ─────────────────────────────────────────────────────────────

(def ^:private impact-map
  {"graph_labels"    "critical — no domain graph model"
   "collection_kinds" "high — no typed records"
   "custom_commands" "high — only template CRUD"
   "governance"      "medium — default RACI"
   "business_rules"  "medium — no conditional logic"})

(defn build-kaizen-report
  "Aggregate a seq of DomainAppReport maps into a KaizenReport map.

   Python equivalent: build_kaizen_report(apps)"
  [apps]
  (let [total-score (reduce + 0 (map :domain-score apps))
        grades      (reduce (fn [acc a] (update acc (:grade a) (fnil inc 0))) {} apps)
        gap-counts  (reduce (fn [acc a]
                              (reduce #(update %1 %2 (fnil inc 0)) acc (:missing a)))
                            {} apps)
        avg         (if (seq apps)
                      (/ (double total-score) (count apps))
                      0.0)
        gaps        (->> gap-counts
                         (map (fn [[k v]] {:feature k :count v :impact (get impact-map k "")}))
                         (sort-by :count >)
                         vec)]
    {:evaluated-at   (let [now (java.time.Instant/now)]
                       (str now))
     :total-apps     (count apps)
     :avg-domain-score avg
     :grades         grades
     :gaps           gaps
     :apps           (vec apps)}))

;; ── log analysis: percentile ──────────────────────────────────────────────────

(defn percentile
  "Sample-based percentile. pct ∈ [0.0, 1.0].
   Returns 0.0 for empty samples.

   Python equivalent: _percentile(samples, pct)"
  [samples pct]
  (if (empty? samples)
    0.0
    (let [s   (sort samples)
          n   (count s)
          idx (max 0 (min (dec n) (dec (int (Math/ceil (* n pct))))))]
      (double (nth s idx)))))

;; ── log analysis: aggregate-events ───────────────────────────────────────────

(defn aggregate-events
  "Build per-method stats from raw event maps.
   Each event map has keys :method / \"method\", :status / \"status\", :ms / \"ms\".
   Returns {method → {:count :errors :ms-samples}}.

   Python equivalent: _aggregate_events(events)"
  [events]
  (reduce
   (fn [acc event]
     (let [m  (or (get event :method) (get event "method") "")]
       (if (str/blank? m)
         acc
         (-> acc
             (update-in [m :count]  (fnil inc 0))
             (update-in [m :errors] (fnil + 0)
                        (if (>= (int (or (get event :status) (get event "status") 0)) 400) 1 0))
             (update-in [m :ms-samples] (fnil conj [])
                        (let [ms (or (get event :ms) (get event "ms") 0)]
                          (int ms)))))))
   {}
   events))

;; ── log analysis: build-findings ─────────────────────────────────────────────

(defn- classify-severity [err-rate p99]
  (cond
    (or (>= err-rate 10) (>= p99 2000)) "critical"
    (or (>= err-rate 5)  (>= p99 1000)) "high"
    (or (>= err-rate 1)  (>= p99 500))  "medium"
    :else                                "low"))

(defn build-findings
  "Build slow/error findings from raw events + pre-computed aggregate maps.

  events       — seq of event maps (keys :method :status :ms)
  aggs         — {method → {:count :errors :avgMs :maxMs :p50Ms :p99Ms}} (may be empty)
  top          — max entries in slow/error lists
  p99-threshold — ms threshold for slow queries
  err-rate-threshold — % threshold for error queries
  show-events  — max recent error events to include

  Python equivalent: _build_findings(events, aggs, top, p99_threshold,
                                     err_rate_threshold, show_events)"
  [events aggs top p99-threshold err-rate-threshold show-events]
  (let [event-stats  (aggregate-events events)
        all-methods  (distinct (concat (keys event-stats) (keys aggs)))
        findings
        (for [method all-methods
              :let [es       (get event-stats method {})
                    ag       (get aggs method {})
                    count-n  (or (get ag :count) (get ag "count")
                                 (get es :count) 0)
                    errors   (or (get ag :errors) (get ag "errors")
                                 (get es :errors) 0)
                    err-rate (if (pos? count-n) (* (/ (double errors) count-n) 100) 0.0)
                    samples  (get es :ms-samples [])
                    p50      (or (get ag :p50Ms) (get ag "p50Ms")
                                 (if (seq samples) (percentile samples 0.50) 0.0))
                    p99      (or (get ag :p99Ms) (get ag "p99Ms")
                                 (if (seq samples) (percentile samples 0.99) 0.0))
                    avg-ms   (or (get ag :avgMs) (get ag "avgMs")
                                 (if (seq samples) (/ (double (reduce + samples)) (count samples)) 0.0))
                    max-ms   (or (get ag :maxMs) (get ag "maxMs")
                                 (if (seq samples) (double (apply max samples)) 0.0))]
              :when (pos? count-n)]
          {:method   method
           :count    count-n
           :errors   errors
           :err-rate (/ (Math/round (* err-rate 100.0)) 100.0)
           :avg-ms   (/ (Math/round (* avg-ms 100.0)) 100.0)
           :p50-ms   (/ (Math/round (* p50    100.0)) 100.0)
           :p99-ms   (/ (Math/round (* p99    100.0)) 100.0)
           :max-ms   (/ (Math/round (* max-ms 100.0)) 100.0)
           :severity (classify-severity err-rate p99)})

        slow        (->> findings
                         (filter #(>= (:p99-ms %) p99-threshold))
                         (sort-by (juxt #(- (:p99-ms %)) #(- (:err-rate %))))
                         (take top)
                         vec)
        errors-list (->> findings
                         (filter #(or (>= (:err-rate %) err-rate-threshold)
                                      (pos? (:errors %))))
                         (sort-by (juxt #(- (:err-rate %)) #(- (:errors %))))
                         (take top)
                         vec)
        recent-errs (->> events
                         (filter #(>= (int (or (get % :status) (get % "status") 0)) 400))
                         (take show-events)
                         vec)
        total-req   (reduce + 0 (map :count findings))
        total-err   (reduce + 0 (map :errors findings))
        overall-err (if (pos? total-req)
                      (/ (Math/round (* (/ (double total-err) total-req) 10000.0)) 100.0)
                      0.0)]
    {:total-requests      total-req
     :total-errors        total-err
     :overall-error-rate  overall-err
     :slow-queries        slow
     :error-queries       errors-list
     :recent-error-events recent-errs}))

;; ── kaizen-logs prompt builder ────────────────────────────────────────────────

(defn build-kaizen-logs-prompt
  "Build the murakumo/codex LLM prompt text for kaizen-logs --fix.
   Pure string assembly — no IO.

   Python equivalent: _build_kaizen_logs_prompt(summary, source)"
  [summary source]
  (str/join "\n"
    (concat
     ["ログ由来の性能/障害 kaizen を実施してください。"
      "目的: 遅い query と高エラー率メソッドの原因をコードから特定し、改善案と必要なら修正を行う。\n"
      "観測サマリ:"
      (str "  source: " source)
      (str "  total_requests: " (:total-requests summary))
      (str "  total_errors: " (:total-errors summary)
           " (" (format "%.2f" (double (:overall-error-rate summary))) "%)\n")
      "遅い query (p99上位):"]
     (map (fn [q]
            (format "  %s: p99=%.0fms p50=%.0fms avg=%.0fms errRate=%.2f%% count=%d"
                    (:method q) (double (:p99-ms q)) (double (:p50-ms q))
                    (double (:avg-ms q)) (double (:err-rate q)) (int (:count q))))
          (:slow-queries summary))
     ["\nエラー query (errRate上位):"]
     (map (fn [q]
            (format "  %s: errRate=%.2f%% errors=%d/%d p99=%.0fms"
                    (:method q) (double (:err-rate q))
                    (int (:errors q)) (int (:count q)) (double (:p99-ms q))))
          (:error-queries summary))
     (when (seq (:recent-error-events summary))
       (concat
        ["\n最近のエラーイベント:"]
        (map (fn [e]
               (let [ts (str (or (get e :ts) (get e "ts") ""))]
                 (format "  ts=%s status=%s ms=%s method=%s err=%s"
                         (subs ts 0 (min 19 (count ts)))
                         (or (get e :status) (get e "status") 0)
                         (or (get e :ms) (get e "ms") 0)
                         (or (get e :method) (get e "method") "")
                         (or (get e :err) (get e "err") ""))))
             (take 10 (:recent-error-events summary)))))
     ["\nやってほしいこと:"
      "1. 上記メソッド実装を特定し、遅延/失敗の主要因を列挙。"
      "2. すぐ効く改善を優先して実装 (N+1削減、不要I/O削減、キャッシュ、validation、error handling)。"
      "3. 変更点、想定改善効果、追加テストをまとめる。"
      "4. 実行可能な検証コマンドを提示する。"])))
