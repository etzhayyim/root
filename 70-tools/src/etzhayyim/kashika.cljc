;; etzhayyim.kashika — Visualization export for actor ecosystem (cljc port, wave 4a).
;;
;; Pure-logic port of 70-tools/etzhayyim-py/src/etzhayyim/kashika.py.
;; (no click, no subprocess, no network I/O — pure rendering / calculation logic)
;;
;; API (pure functions — no IO at load time):
;;   (to-mermaid    apps edges)              → Mermaid LR graph string
;;   (to-dot        apps edges)              → Graphviz DOT string
;;   (haisen-terminal data)                  → terminal table string
;;   (sla-effective  avail redundancy)       → effective availability float
;;   (downtime-per-year avail)               → human-readable downtime string
;;   (shinka-summary rows)                   → summary map
;;   (pct           n total)                 → "20.0%" string
;;
;; IO legs (deferred — operator-gated):
;;   The scan-workspace IO leg (_haisen_scan / _resolve_root / file writes) is NOT
;;   ported here; it lives in babashka host tasks that call haisen/source-graph.cljc.
;;   HTML generation (_haisen_html) intentionally omitted — it embeds large inline JS
;;   and carries no testable pure logic beyond the data-structure iteration done here.
;;
;; SLA components constant (from kashika.py _SLA_COMPONENTS) is preserved verbatim.
;;
;; bb usage (classpath 70-tools/src):
;;   (require '[etzhayyim.kashika :as kashika])
;;   (kashika/to-mermaid apps edges)

(ns etzhayyim.kashika
  "Visualization export (Mermaid/DOT/terminal/SLA/shinka) — pure rendering logic."
  (:require [clojure.string :as str]))

;; ── Mermaid export ─────────────────────────────────────────────────────────────

(defn to-mermaid
  "Render a Mermaid LR graph from apps + edges.
   apps  = seq of {:nanoid str :name str}
   edges = seq of {:from-nanoid str :to-nanoid str :edge-type str}
   Returns multi-line Mermaid string."
  [apps edges]
  (let [app-names (reduce (fn [m a]
                            (assoc m (get a :nanoid (get a "nanoid"))
                                   (or (not-empty (str (get a :name (get a "name"))))
                                       (get a :nanoid (get a "nanoid")))))
                          {} apps)
        lines (into ["graph LR"]
                    (map (fn [e]
                           (let [from (get e :from-nanoid (get e "from_nanoid" ""))
                                 to   (get e :to-nanoid   (get e "to_nanoid" ""))
                                 typ  (get e :edge-type   (get e "edge_type" ""))
                                 src  (get app-names from from)
                                 dst  (get app-names to to)]
                             (str "    " from "[\"" src "\"] -->|" typ "| " to "[\"" dst "\"]")))
                         edges))]
    (str/join "\n" lines)))

;; ── DOT export ─────────────────────────────────────────────────────────────────

(defn to-dot
  "Render a Graphviz DOT directed graph.
   apps + edges — same shape as to-mermaid.
   Returns multi-line DOT string."
  [apps edges]
  (let [app-names (reduce (fn [m a]
                            (assoc m (get a :nanoid (get a "nanoid"))
                                   (or (not-empty (str (get a :name (get a "name"))))
                                       (get a :nanoid (get a "nanoid")))))
                          {} apps)
        header ["digraph actors {" "  rankdir=\"LR\";" "  node [shape=box];"]
        node-lines (map (fn [a]
                          (let [nid   (get a :nanoid (get a "nanoid"))
                                label (get app-names nid nid)]
                            (str "  \"" nid "\" [label=\"" label "\"];")))
                        apps)
        edge-lines (map (fn [e]
                          (let [from (get e :from-nanoid (get e "from_nanoid" ""))
                                to   (get e :to-nanoid   (get e "to_nanoid" ""))
                                typ  (get e :edge-type   (get e "edge_type" ""))]
                            (str "  \"" from "\" -> \"" to "\" [label=\"" typ "\"];")))
                        edges)]
    (str/join "\n" (concat header node-lines edge-lines ["}"]))))

;; ── Terminal table ──────────────────────────────────────────────────────────────

(defn haisen-terminal
  "Render a plain-text terminal table from a haisen report dict (string-keyed).
   data = {:apps [...] :edges [...] :stats {...}} (or string-keyed equivalents)
   Returns multi-line string."
  [data]
  (let [apps  (or (get data :apps  (get data "apps"  [])))
        edges (or (get data :edges (get data "edges" [])))
        stats (or (get data :stats (get data "stats" {})) {})
        edge-count (reduce (fn [m e]
                             (let [k (get e :from-nanoid (get e "from_nanoid" ""))]
                               (assoc m k (inc (get m k 0)))))
                           {} edges)
        header-line (format "%-12s  %-28s  %-10s  EDGES" "NANOID" "NAME" "TYPE")
        app-rows (map (fn [a]
                        (let [nanoid (subs (str (get a :nanoid (get a "nanoid" ""))) 0
                                          (min 12 (count (str (get a :nanoid (get a "nanoid" ""))))))
                              name   (subs (str (get a :name (get a "name" ""))) 0
                                          (min 28 (count (str (get a :name (get a "name" ""))))))
                              ptype  (subs (str (get a :performer-type (get a "performer_type" ""))) 0
                                          (min 10 (count (str (get a :performer-type (get a "performer_type" ""))))))
                              ec     (get edge-count (str (get a :nanoid (get a "nanoid" ""))) 0)]
                          (format "%-12s  %-28s  %-10s  %d" nanoid name ptype ec)))
                      (take 50 apps))
        remaining  (- (count apps) 50)
        summary    [(str "Apps: " (count apps) "  Edges: " (count edges))
                    (str "  total_apps=" (get stats :total_apps (get stats "total_apps" (count apps)))
                         "  total_edges=" (get stats :total_edges (get stats "total_edges" (count edges))))
                    ""
                    header-line]]
    (str/join "\n"
              (cond-> (concat summary app-rows)
                (pos? remaining) (concat [(str "  ... " remaining " more")])))))

;; ── SLA analysis ───────────────────────────────────────────────────────────────

(defn sla-effective
  "Effective availability given single-instance availability and redundancy count.
   avail       = per-instance availability (e.g. 0.9999)
   redundancy  = number of independent instances
   Returns 1 - (1-avail)^redundancy."
  [avail redundancy]
  (let [fail (reduce (fn [f _] (* f (- 1.0 avail)))
                     1.0
                     (range redundancy))]
    (- 1.0 fail)))

(defn downtime-per-year
  "Human-readable annual downtime string for a given availability fraction.
   Matches Python:
     minutes < 1  → \"X.Xs\"
     minutes < 60 → \"X.Xm\"
     else         → \"X.XXh\""
  [avail]
  (let [minutes (* (- 1.0 avail) 365.25 24.0 60.0)]
    (cond
      (< minutes 1.0) (format "%.1fs" (* minutes 60.0))
      (< minutes 60.0) (format "%.1fm" minutes)
      :else            (format "%.2fh" (/ minutes 60.0)))))

;; ── SLA component catalog (preserved verbatim from kashika.py) ─────────────────

(def sla-components
  [{:name "CF Workers (Dispatcher)"     :layer "edge"     :avail 0.9999 :redundancy 1 :spof false
    :issues []
    :mitigations ["Anycast global, auto-failover across 300+ PoP"]}
   {:name "CF Workers (PDS)"            :layer "gateway"  :avail 0.9999 :redundancy 1 :spof true
    :issues ["Single Worker, no multi-region active-active"]
    :mitigations ["Circuit breaker (10s cooldown)" "Rate limiter 600/min"]}
   {:name "CF KV (PDS_KV)"              :layer "storage"  :avail 0.9999 :redundancy 1 :spof false
    :issues []
    :mitigations ["11 nines durability" "Global replication"]}
   {:name "yata Container"              :layer "compute"  :avail 0.9995 :redundancy 1 :spof true
    :issues ["Single instance (min_instances=1)" "CSR data lost on restart"]
    :mitigations ["Fire-and-forget write (KV authoritative)"]}
   {:name "CF Workers (App)"            :layer "compute"  :avail 0.9999 :redundancy 1 :spof false
    :issues []
    :mitigations ["V8 isolate per request"]}
   {:name "Vultr VKE (LangServer pods)" :layer "compute"  :avail 0.995  :redundancy 2 :spof true
    :issues ["Single region (LAX)" "Pod restarts lose in-flight LangGraph state"]
    :mitigations ["LangGraph checkpointer (Postgres)" "Granian multi-worker"]}
   {:name "Kotoba/Datomic (Vultr VKE)"  :layer "data"     :avail 0.999  :redundancy 1 :spof true
    :issues ["Single-region streaming DB" "B2 rps quota risk (incident 2026-04-25)"]
    :mitigations ["B2 defense-in-depth refill levels" "statement_timeout_secs=120"]}
   {:name "Cloudflare R2 (B2 via gateway)" :layer "storage" :avail 0.9999 :redundancy 1 :spof false
    :issues []
    :mitigations ["11 nines durability"]}
   {:name "Murakumo Fleet (Mac Mini)"   :layer "inference" :avail 0.99   :redundancy 4 :spof false
    :issues ["On-prem power/network dependency"]
    :mitigations ["4-node fleet" "Nomad rolling restart" "RunPod fallback"]}])

(def target-sla 0.9999)

(defn sla-report
  "Compute the full SLA analysis report.
   Returns map with :target :target-label :downtime-target :components :spof-count."
  []
  (let [components (map (fn [c]
                          (let [eff (sla-effective (:avail c) (:redundancy c))]
                            (assoc c
                                   :effective-avail eff
                                   :downtime-per-year (downtime-per-year eff)
                                   :meets-target (>= eff target-sla))))
                        sla-components)
        spofs (filter :spof components)]
    {:target        target-sla
     :target-label  (format "%.4f%%" (* target-sla 100.0))
     :downtime-target (downtime-per-year target-sla)
     :components    (vec components)
     :spof-count    (count spofs)}))

;; ── Shinka summary ─────────────────────────────────────────────────────────────

(defn shinka-summary
  "Aggregate shinka/hyoka health stats from a seq of row maps (string-keyed).
   Returns a string-keyed summary map — matches Python _shinka_summary."
  [rows]
  (let [total     (count rows)
        s-sum     (reduce + 0 (map #(get % "ShinkaScore" 0) rows))
        h-sum     (reduce + 0 (map #(get % "HyokaScore"  0) rows))
        max-hyoka (reduce max 0 (map #(get % "HyokaScore" 0) rows))
        top-actor (or (some (fn [r] (when (= (get r "HyokaScore" 0) max-hyoka)
                                      (get r "Nanoid" "")))
                            rows)
                      "")]
    {"total"     total
     "avg_shinka" (if (pos? total) (double (/ s-sum total)) 0.0)
     "avg_hyoka"  (if (pos? total) (double (/ h-sum total)) 0.0)
     "max_hyoka"  max-hyoka
     "top_actor"  top-actor
     "joucho"    (count (filter #(get % "HasJoucho")   rows))
     "inbox"     (count (filter #(get % "HasInbox")    rows))
     "cadence"   (count (filter #(get % "HasCadence")  rows))
     "drill"     (count (filter #(get % "HasDrill")    rows))
     "validate"  (count (filter #(get % "HasValidate") rows))
     "analyze"   (count (filter #(get % "HasAnalyze")  rows))
     "engage"    (count (filter #(get % "HasEngage")   rows))
     "old_timer" (count (filter #(get % "HasOldTimer") rows))}))

(defn pct
  "Format n/total as a percentage string (e.g. \"20.0%\").
   Returns \"0.0%\" when total is 0."
  [n total]
  (if (pos? total)
    (format "%.1f%%" (* (double (/ n total)) 100.0))
    "0.0%"))
