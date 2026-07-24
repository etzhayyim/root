;; etzhayyim.bunseki — Architecture and process analysis (cljc port, wave-4b).
;;
;; Pure-logic port of 70-tools/etzhayyim-py/src/etzhayyim/bunseki.py
;; (no click, no httpx, no subprocess — OCEL / XRPC legs are IO-deferred).
;;
;; OCEL process-mining functions (operate on event maps):
;;   (arch-grade             score)            → "A" | "B" | "C" | "D" | "F"
;;   (build-traces           events object-type) → {trace-id [activity...]}
;;   (build-dfg              traces)           → [{:from :to :count :freq_pct}]
;;   (analyze-variants       traces)           → [{:variant :count :freq_pct}]
;;   (analyze-performance    events)           → [{:activity :count :avg_ms :p50_ms :p95_ms :slow}]
;;   (check-conformance      traces)           → [{:trace_id :variant :expected}]
;;   (compute-score          events traces)    → {:score :conformance_rate_pct :top_variant_pct
;;                                                 :slow_activities :total_traces :total_events}
;;
;; Architecture analysis functions (operate on haisen-style edge/app maps):
;;   (arch-dfg               edges top)        → [{:from :to :type :count}]
;;   (arch-variants          apps edges top)   → [{:pattern :count :pct :apps}]
;;   (arch-conformance       apps edges)       → [{:rule :description :total :conformant :rate :violations}]
;;   (arch-cycles            adj top)          → {:cycles total_cycles}
;;   (arch-score             conformance)      → score float
;;
;; Event map keys (OCEL v2): :activity :auth :method :duration_ms :type
;; Edge map keys (haisen):   :from_nanoid :to_nanoid :edge_type
;; App map keys (haisen):    :nanoid
;;
;; IO legs (deferred, operator-gated):
;;   fetchBunsenEvents — httpx/CF Analytics call; call explicitly at runtime.
;;
;; bb usage (classpath 70-tools/src):
;;   (require '[etzhayyim.bunseki :as b])
;;   (b/arch-grade 85)

(ns etzhayyim.bunseki
  (:require [clojure.string :as str]))

;; ── arch grade ────────────────────────────────────────────────────────────────

(defn arch-grade
  "Map a conformance score to an arch grade.
   Mirrors _arch_grade in bunseki.py."
  [score]
  (cond
    (>= score 90) "A"
    (>= score 80) "B"
    (>= score 70) "C"
    (>= score 60) "D"
    :else         "F"))

;; ── OCEL process-mining helpers ───────────────────────────────────────────────

(defn build-traces
  "Group events into traces by auth/object key.
   `events`      – seq of maps with :auth / :method / :activity / :type keys
   `object-type` – if non-empty, filters events where :type equals object-type
   Returns {trace-id [activity ...]} map.
   Mirrors _build_traces in bunseki.py."
  ([events] (build-traces events ""))
  ([events object-type]
   (reduce (fn [acc e]
             (if (or (str/blank? object-type)
                     (= (get e :type "") object-type))
               (let [k   (or (not-empty (get e :auth "")) (get e :method "unknown"))
                     act (or (not-empty (get e :activity "")) (get e :method "?"))]
                 (update acc k (fnil conj []) act))
               acc))
           {}
           events)))

(defn build-dfg
  "Directly-Follows Graph: count (from→to) activity pairs.
   `traces` – map from build-traces
   Returns list of {:from :to :count :freq_pct} sorted by -count.
   Mirrors _build_dfg in bunseki.py."
  [traces]
  (let [counts (reduce (fn [acc acts]
                         (reduce (fn [m [a b]]
                                   (update m [a b] (fnil inc 0)))
                                 acc
                                 (map vector acts (rest acts))))
                       {}
                       (vals traces))
        total  (apply + 0 (vals counts))]
    (sort-by #(- (:count %))
             (map (fn [[[from to] cnt]]
                    {:from    from
                     :to      to
                     :count   cnt
                     :freq_pct (-> (/ (* 100.0 cnt) (max total 1))
                                   (Math/round)
                                   (double)
                                   (/ 10.0)
                                   (* 10.0))})
                  counts))))

(defn analyze-variants
  "Process variants (trace signatures) grouped by '→'-joined sequence.
   `traces` – map from build-traces
   Returns list of {:variant :count :freq_pct} sorted by -count.
   Mirrors _analyze_variants in bunseki.py."
  [traces]
  (let [total (count traces)
        counts (reduce (fn [acc acts]
                         (let [sig (str/join "→" acts)]
                           (update acc sig (fnil inc 0))))
                       {}
                       (vals traces))]
    (sort-by #(- (:count %))
             (map (fn [[sig cnt]]
                    {:variant  sig
                     :count    cnt
                     :freq_pct (-> (/ (* cnt 100.0) (max total 1))
                                   (* 10.0) Math/round (/ 10.0))})
                  counts))))

(defn- percentile
  "Return the value at the given percentile (0–1) of a sorted collection."
  [sorted-coll p]
  (let [n (count sorted-coll)
        i (min (dec n) (int (* n p)))]
    (nth sorted-coll (max 0 i))))

(defn analyze-performance
  "Per-activity duration statistics.
   `events` – seq of maps with :activity / :method / :duration_ms keys
   Returns list of {:activity :count :avg_ms :p50_ms :p95_ms :slow} sorted by -p95_ms.
   Mirrors _analyze_performance in bunseki.py."
  [events]
  (let [by-act (reduce (fn [acc e]
                         (let [act (or (not-empty (get e :activity "")) (get e :method "?"))
                               dur (double (or (get e :duration_ms 0) 0))]
                           (update acc act (fnil conj []) dur)))
                       {}
                       events)]
    (sort-by #(- (:p95_ms %))
             (map (fn [[act durs]]
                    (let [sorted-d (sort durs)
                          n        (count sorted-d)
                          avg-ms   (-> (/ (apply + sorted-d) (max n 1)) (double)
                                       (* 10.0) Math/round (/ 10.0))
                          p50-ms   (double (percentile sorted-d 0.5))
                          p95-ms   (double (percentile sorted-d 0.95))]
                      {:activity act
                       :count    n
                       :avg_ms   avg-ms
                       :p50_ms   p50-ms
                       :p95_ms   p95-ms
                       :slow     (> p95-ms 500.0)}))
                  by-act))))

(defn check-conformance
  "Check each trace against the most-common variant.
   Returns list of {:trace_id :variant :expected} for deviating traces.
   Mirrors _check_conformance in bunseki.py."
  [traces]
  (let [variants      (analyze-variants traces)
        expected-sig  (:variant (first variants) "")]
    (when (seq variants)
      (keep (fn [[tid acts]]
              (let [sig (str/join "→" acts)]
                (when (not= sig expected-sig)
                  {:trace_id tid :variant sig :expected expected-sig})))
            traces))))

(defn compute-score
  "Compute overall process health score from events + traces.
   Returns {:score :conformance_rate_pct :top_variant_pct :slow_activities
            :total_traces :total_events}.
   Mirrors _compute_score in bunseki.py."
  [events traces]
  (let [perf           (analyze-performance events)
        variants       (analyze-variants traces)
        deviations     (check-conformance traces)
        slow-count     (count (filter :slow perf))
        n-traces       (count traces)
        n-devs         (count deviations)
        conformance-r  (-> (/ (* (- n-traces n-devs) 100.0) (max n-traces 1))
                           (* 10.0) Math/round (/ 10.0))
        top-var-pct    (or (:freq_pct (first variants)) 0.0)
        score          (-> (+ (* conformance-r 0.5)
                               (* top-var-pct 0.3)
                               (* (max 0 (- 100 (* slow-count 10))) 0.2))
                           (* 10.0) Math/round (/ 10.0))]
    {:score                 score
     :conformance_rate_pct  conformance-r
     :top_variant_pct       top-var-pct
     :slow_activities       slow-count
     :total_traces          n-traces
     :total_events          (count events)}))

;; ── architecture DFG (haisen-edge level) ─────────────────────────────────────

(defn arch-dfg
  "Build DFG at the architecture level from haisen edges.
   `edges` – seq of {:from_nanoid :to_nanoid :edge_type}
   `top`   – max rows to return (default 10)
   Returns list of {:from :to :type :count} sorted by -count.
   Mirrors pair_counts logic in arch_dfg / arch_scan in bunseki.py."
  ([edges] (arch-dfg edges 10))
  ([edges top]
   (let [pair-counts
         (reduce (fn [acc {:keys [from_nanoid to_nanoid edge_type]}]
                   (let [k [from_nanoid to_nanoid]]
                     (if (contains? acc k)
                       (update-in acc [k :count] inc)
                       (assoc acc k {:from  from_nanoid
                                     :to    to_nanoid
                                     :type  edge_type
                                     :count 1}))))
                 {}
                 edges)]
     (take top (sort-by #(- (:count %)) (vals pair-counts))))))

(defn arch-variants
  "Classify apps by architectural pattern from haisen edges.
   `apps`  – seq of {:nanoid}
   `edges` – seq of {:from_nanoid :to_nanoid :edge_type}
   `top`   – max patterns to return
   Returns list of {:pattern :count :pct :apps}.
   Mirrors pattern_groups logic in arch_variants / arch_scan in bunseki.py."
  ([apps edges] (arch-variants apps edges 10))
  ([apps edges top]
   (let [invoke-set    (into #{} (keep #(when (= (:edge_type %) "invoke") (:from_nanoid %)) edges))
         subscribe-set (into #{} (keep #(when (= (:edge_type %) "subscribe") (:from_nanoid %)) edges))
         connected-set (into #{}
                             (mapcat (fn [e] [(:from_nanoid e) (:to_nanoid e)]) edges))
         rw-set        (into #{} (keep #(when (#{"writes" "reads"} (:edge_type %)) (:from_nanoid %)) edges))
         total-apps    (count apps)
         pattern-groups
         (reduce (fn [acc {:keys [nanoid]}]
                   (let [pat (cond
                               (invoke-set nanoid)    "active"
                               (subscribe-set nanoid) "event-driven"
                               (rw-set nanoid)        "passive"
                               (connected-set nanoid) "passive"
                               :else                  "isolated")]
                     (update acc pat (fnil conj []) nanoid)))
                 {}
                 apps)]
     (take top
           (sort-by #(- (:count %))
                    (map (fn [[pat app-list]]
                           {:pattern pat
                            :count   (count app-list)
                            :pct     (-> (/ (* (count app-list) 100.0) (max total-apps 1))
                                         (* 10.0) Math/round (/ 10.0))
                            :apps    (take 5 app-list)})
                         pattern-groups))))))

(defn arch-conformance
  "Design rule conformance checks on haisen data.
   Returns list of 3 rule maps (naming-convention / has-edges / single-project).
   Mirrors arch_conformance command logic in bunseki.py."
  [apps edges]
  (let [total-apps    (count apps)
        connected-set (into #{} (mapcat (fn [e] [(:from_nanoid e) (:to_nanoid e)]) edges))
        nanoid-re     #"^[a-z0-9]{7}$"
        ;; rule 1: naming
        naming-ok     (filter #(re-matches nanoid-re (:nanoid %)) apps)
        naming-viols  (take 5 (map :nanoid (remove #(re-matches nanoid-re (:nanoid %)) apps)))
        ;; rule 2: has-edges
        edge-ok-count (count (filter #(connected-set (:nanoid %)) apps))
        edge-viols    (take 5 (map :nanoid (remove #(connected-set (:nanoid %)) apps)))
        ;; rule 3: single-project (trivially OK — HaisenApp has no project field)
        proj-viols    []]
    [{:rule        "naming-convention"
      :description "nanoid matches [a-z0-9]{7}"
      :total       total-apps
      :conformant  (count naming-ok)
      :rate        (-> (/ (count naming-ok) (max total-apps 1)) double (* 1000) Math/round (/ 1000.0))
      :violations  naming-viols}
     {:rule        "has-edges"
      :description "app has at least 1 edge"
      :total       total-apps
      :conformant  edge-ok-count
      :rate        (-> (/ edge-ok-count (max total-apps 1)) double (* 1000) Math/round (/ 1000.0))
      :violations  edge-viols}
     {:rule        "single-project"
      :description "app assigned to exactly 1 project"
      :total       total-apps
      :conformant  (- total-apps (count proj-viols))
      :rate        (-> (/ (- total-apps (count proj-viols)) (max total-apps 1)) double (* 1000) Math/round (/ 1000.0))
      :violations  proj-viols}]))

(defn arch-score
  "Weighted score from conformance rule list.
   Mirrors conf_score in arch_scan in bunseki.py."
  [conformance]
  (if (empty? conformance)
    100.0
    (-> (/ (apply + (map :rate conformance)) (count conformance))
        (* 100.0)
        (double))))

(defn arch-cycles
  "Detect circular dependencies in adj map via DFS.
   `adj` – {nanoid [to-nanoid ...]}
   `top` – max cycles to report
   Returns {:cycles [[...]] :total_cycles int}.
   Mirrors arch_cycles command logic in bunseki.py."
  ([adj] (arch-cycles adj 10))
  ([adj top]
   (let [max-cycles 50
         max-len    8
         cycles     (atom [])
         seen-canon (atom #{})
         canon-fn   (fn [path]
                      (if (empty? path)
                        ""
                        (let [;; find the index of the lexicographically smallest element
                              min-idx (reduce (fn [best-i i]
                                                (if (neg? (compare (nth path i) (nth path best-i)))
                                                  i best-i))
                                              0
                                              (range (count path)))
                              rotated (mapv #(nth path (mod (+ % min-idx) (count path)))
                                            (range (count path)))]
                          (str/join "->" rotated))))]
     (doseq [start (sort (keys adj))
             :while (< (count @cycles) max-cycles)]
       (let [visit (fn visit [node path visited-stack]
                     (when (and (< (count @cycles) max-cycles)
                                (<= (count path) max-len))
                       (doseq [nxt (get adj node [])]
                         (cond
                           (and (= nxt start) (>= (count path) 2))
                           (let [cyc   (conj path start)
                                 canon (canon-fn path)]
                             (when (not (contains? @seen-canon canon))
                               (swap! seen-canon conj canon)
                               (swap! cycles conj cyc)))
                           (not (contains? visited-stack nxt))
                           (visit nxt (conj path nxt) (conj visited-stack nxt))))))]
         (visit start [start] #{start})))
     {:cycles       (vec (take top @cycles))
      :total_cycles (count @cycles)})))

;; ── CLI entrypoint (JVM/bb only) ──────────────────────────────────────────────
;; Mirrors the Python click group `bunseki` (bunseki.py): top-level group prints
;; the subcommand hint; `arch` is a subgroup (scan/dfg/variants/conformance/cycles)
;; that needs a haisen workspace scan (IO leg NOT in this twin); `bi`/`domain` +
;; the OCEL leaves (scan/dfg/variants/conformance/performance/recommendations)
;; need the PDS/CF-Analytics fetch (network). All such data legs are GUARDED here
;; — the ported pure analytics fns (arch-grade/build-dfg/analyze-variants/…) are
;; available for callers that already hold the edges/apps/events.

#?(:clj
   (do
     (def ^:private arch-subs #{"scan" "dfg" "variants" "conformance" "cycles"})
     (def ^:private ocel-subs #{"scan" "dfg" "variants" "conformance" "performance" "recommendations"})

     (defn- usage []
       (println "bunseki (分析): subcommands: arch, bi, domain")
       (println "  arch <scan|dfg|variants|conformance|cycles> [--workspace-dir D] [--top N] [--json]")
       (println "  bi [--metric M] [--json] | domain [--json]")
       (println "  <scan|dfg|variants|conformance|performance|recommendations> [--minutes N] [--limit N] [--top N] [--object-type T] [--json]  (OCEL)"))

     (defn -main [& args]
       (let [sub (first args)]
         (cond
           (nil? sub) (usage)

           (= sub "arch")
           (let [a2 (second args)]
             (if (contains? arch-subs a2)
               (println (str "bunseki arch " a2 " (guarded): needs a haisen workspace scan "
                             "(_scan_workspace IO leg, not in this twin). Pure analytics "
                             "(arch-dfg/arch-variants/arch-conformance/arch-cycles/arch-grade) "
                             "are available once edges+apps are supplied."))
               (println "bunseki arch: subcommands: scan, dfg, variants, conformance, cycles")))

           (= sub "bi")
           (println "bunseki bi (guarded): would GET com.etzhayyim.bunseki.getBIMetrics (network). Run the Python CLI for live BI.")

           (= sub "domain")
           (println "bunseki domain (guarded): would GET com.etzhayyim.bunseki.getDomainAnalysis (network). Run the Python CLI for live domain analysis.")

           (contains? ocel-subs sub)
           (println (str "bunseki " sub " (guarded): needs the OCEL event fetch "
                         "(CF Analytics / PDS _pds/ocel, network). Pure process-mining "
                         "(build-traces/build-dfg/analyze-variants/analyze-performance/"
                         "check-conformance/compute-score) are available once events are supplied."))

           :else
           (do (binding [*out* *err*] (println (str "bunseki: unknown subcommand: " sub)))
               (usage)))))))
