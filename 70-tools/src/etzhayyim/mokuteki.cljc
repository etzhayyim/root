;; etzhayyim.mokuteki — Purpose-driven 4-layer Shannon optimization evaluator (cljc port, wave 3b).
;;
;; Pure-logic port of 70-tools/etzhayyim-py/src/etzhayyim/mokuteki.py
;; (no click, no subprocess, no webbrowser, no duckdb I/O).
;;
;; Ported (pure):
;;   rank-ladder, resolve-rank, next-rank, weighted-score, derive-axes,
;;   eval-layer-b-stub, eval-layer-c-stub, diagnosis, build-mokuteki-report (pure parts),
;;   flatten-report, bar, all data constructors / to-dict shapes.
;;
;; Deferred (I/O / subprocess):
;;   scan-app-meta          — filesystem walk (kotodama.jsonld)
;;   eval-layer-a           — calls scan-app-meta + run-all-checks (shannon)
;;   eval-layer-d           — calls scan-app-meta
;;   build-mokuteki-report  — wires A/D layer evaluation
;;   kashika HTML render    — webbrowser.open
;;   store / query / history — duckdb subprocess
;;   These are all available via #?(:clj ...) helpers at the bottom.
;;
;; API (pure — platform-neutral):
;;   (rank-ladder)                         → seq of rank maps
;;   (resolve-rank score)                  → rank map {:name :color :min-score}
;;   (next-rank score)                     → [next-rank-name pts-needed]
;;   (weighted-score components)           → float
;;   (derive-axes a b c d)                 → seq of axis maps
;;   (eval-layer-b-stub)                   → layer map
;;   (eval-layer-c-stub)                   → layer map
;;   (layer-diagnosis layers axes total)   → seq of diagnosis strings
;;   (build-mokuteki-report-from layers axes) → full report map
;;   (flatten-report report)               → string-keyed flat map (for storage)
;;   (bar score width)                     → ASCII bar string
;;
;; bb usage (classpath 70-tools/src):
;;   (require '[etzhayyim.mokuteki :as m])
;;   (m/resolve-rank 1500)   ;; → {:name "Kyu 1" :color "#8B4513" :min-score 1500}

(ns etzhayyim.mokuteki
  (:require [clojure.string :as str]
            #?(:clj [cheshire.core :as json])))

;; ── rank ladder ───────────────────────────────────────────────────────────────

(def rank-ladder
  "Kyu/Dan rank ladder — matches Python RANK_LADDER order (highest first)."
  [{:name "Dan 10" :color "#000000" :min-score 12000}
   {:name "Dan 9"  :color "#000000" :min-score 11000}
   {:name "Dan 8"  :color "#000000" :min-score 10000}
   {:name "Dan 7"  :color "#000000" :min-score  9000}
   {:name "Dan 6"  :color "#000000" :min-score  8000}
   {:name "Dan 5"  :color "#000000" :min-score  7000}
   {:name "Dan 4"  :color "#000000" :min-score  6000}
   {:name "Dan 3"  :color "#000000" :min-score  5000}
   {:name "Dan 2"  :color "#000000" :min-score  4000}
   {:name "Dan 1"  :color "#000000" :min-score  2000}
   {:name "Kyu 1"  :color "#8B4513" :min-score  1500}
   {:name "Kyu 2"  :color "#3B82F6" :min-score  1000}
   {:name "Kyu 3"  :color "#22C55E" :min-score   600}
   {:name "Kyu 4"  :color "#FF8C00" :min-score   300}
   {:name "Kyu 5"  :color "#FFD700" :min-score   100}
   {:name "Kyu 6"  :color "#FFFFFF" :min-score     0}])

(defn resolve-rank
  "Return the rank map for a given score. Mirrors Python resolve_rank."
  [score]
  (or (some #(when (>= score (:min-score %)) %) rank-ladder)
      (last rank-ladder)))

(defn next-rank
  "Return [next-rank-name pts-needed] or [\"\" 0] if already Dan 10.
   Mirrors Python next_rank."
  [score]
  ;; Scan reversed (ascending min-score) to find first rank above current score
  (let [ascending (reverse rank-ladder)
        found     (some #(when (< score (:min-score %)) %) ascending)]
    (if found
      [(:name found) (- (:min-score found) score)]
      ["" 0])))

;; ── component / layer constructors ───────────────────────────────────────────

(defn make-component
  "Build a MokutekiComponent map. Mirrors Python MokutekiComponent."
  [name weight score details]
  {:name name :weight weight :score (double score) :details details})

(defn component->dict [c]
  {"name" (:name c) "score" (:score c) "weight" (:weight c) "details" (:details c)})

(defn make-layer
  "Build a MokutekiLayer map. Mirrors Python MokutekiLayer."
  [id name name-jp weight score points components]
  {:id id :name name :name-jp name-jp
   :weight weight :score (double score) :points points
   :components components})

(defn layer->dict [l]
  {"id"         (:id l)
   "name"       (:name l)
   "name_jp"    (:name-jp l)
   "weight"     (:weight l)
   "score"      (:score l)
   "points"     (:points l)
   "components" (mapv component->dict (:components l))})

(defn make-axis
  "Build a MokutekiAxis map. Mirrors Python MokutekiAxis."
  [name weight score points source details]
  {:name name :weight weight :score (double score) :points points
   :source source :details details})

(defn axis->dict [a]
  {"name"    (:name a)
   "weight"  (:weight a)
   "score"   (:score a)
   "points"  (:points a)
   "source"  (:source a)
   "details" (:details a)})

;; ── pure scoring ──────────────────────────────────────────────────────────────

(defn weighted-score
  "Σ component.score × component.weight. Mirrors Python _weighted_score."
  [components]
  (reduce + 0.0 (map #(* (:score %) (:weight %)) components)))

;; ── stub layers (B and C require Go binary) ──────────────────────────────────

(defn eval-layer-b-stub []
  (let [c (make-component
           "BayesNet/causal/bottleneck (Go binary required)" 1.0 50.0
           "run `etzhayyim shannon bayesnet` + `etzhayyim shannon bottleneck` for full evaluation")
        score  50.0
        points (int (* score 0.25 120))]
    (make-layer "B" "Uncertainty" "不確実性" 0.25 score points [c])))

(defn eval-layer-c-stub []
  (let [c (make-component
           "POMDP/MPC/bandit (Go binary required)" 1.0 50.0
           "run `etzhayyim mokuteki` (Go binary) for full evaluation")
        score  50.0
        points (int (* score 0.20 120))]
    (make-layer "C" "Control" "制御" 0.20 score points [c])))

;; ── axes derivation ───────────────────────────────────────────────────────────

(defn derive-axes
  "Derive the 5 Well-Becoming axes from layer scores.
   Mirrors Python derive_axes."
  [layer-a layer-b layer-c layer-d]
  (let [as (:score layer-a)
        bs (:score layer-b)
        cs (:score layer-c)
        ds (:score layer-d)
        engagement   (+ (* as 0.5) (* ds 0.5))
        competence   (+ (* as 0.6) (* bs 0.4))
        contribution (+ (* bs 0.4) (* cs 0.6))
        growth       (+ (* cs 0.5) (* as 0.5))
        resilience   (+ (* bs 0.5) (* ds 0.5))]
    [(make-axis "Engagement (参与)"   0.25 engagement   (int (* engagement   0.25 120)) "Layer A + D" "")
     (make-axis "Competence (能力)"   0.25 competence   (int (* competence   0.25 120)) "Layer A + B" "")
     (make-axis "Contribution (貢献)" 0.20 contribution (int (* contribution 0.20 120)) "Layer B + C" "")
     (make-axis "Growth (成長)"       0.20 growth       (int (* growth       0.20 120)) "Layer C + A" "")
     (make-axis "Resilience (回復)"   0.10 resilience   (int (* resilience   0.10 120)) "Layer B + D" "")]))

;; ── diagnosis ────────────────────────────────────────────────────────────────

(defn layer-diagnosis
  "Build diagnosis strings from layers + axes + total score.
   Mirrors Python build_mokuteki_report diagnosis section."
  [layers axes total-score]
  (let [diag (atom [])]
    ;; Layer checks
    (doseq [l layers]
      (when (< (:score l) 30)
        (swap! diag conj (format "[CRITICAL] Layer %s (%s): %.0f/100"
                                 (:id l) (:name-jp l) (:score l))))
      (when (and (>= (:score l) 30) (< (:score l) 60))
        (swap! diag conj (format "[IMPROVE] Layer %s (%s): %.0f/100"
                                 (:id l) (:name-jp l) (:score l))))
      (doseq [c (:components l)]
        (when (and (< (:score c) 30) (>= (:weight c) 0.15))
          (swap! diag conj (format "  └ %s: %.0f/100 — %s"
                                   (:name c) (:score c) (:details c))))))
    ;; Axes checks (sorted ascending)
    (doseq [ax (sort-by :score axes)]
      (when (< (:score ax) 50)
        (swap! diag conj (format "[WELLBEING] %s: %.0f/100 ← %s"
                                 (:name ax) (:score ax) (:source ax)))))
    ;; Next rank
    (let [[next-r pts] (next-rank total-score)
          rank         (resolve-rank total-score)]
      (when (seq next-r)
        (swap! diag conj (format "[NEXT] %s → %s (need %d pts)"
                                 (:name rank) next-r pts))))

    (if (seq @diag)
      @diag
      ["all layers aligned with mokuteki"])))

;; ── report assembly ───────────────────────────────────────────────────────────

(defn build-mokuteki-report-from
  "Assemble a full MokutekiReport from pre-evaluated layers + timestamp string.
   Mirrors Python build_mokuteki_report (composition step)."
  [layer-a layer-b layer-c layer-d generated-at]
  (let [layers      [layer-a layer-b layer-c layer-d]
        axes        (derive-axes layer-a layer-b layer-c layer-d)
        total-score (reduce + 0 (map :points layers))
        rank        (resolve-rank total-score)
        diagnosis   (layer-diagnosis layers axes total-score)]
    {:generated-at generated-at
     :mokuteki     "Global Well-Becoming Generative Society"
     :principle    "DSMで依存構造を表現し、Bayesで不確実性を伝播させ、POMDPで観測と制御を最適化する"
     :layers       layers
     :axes         axes
     :total-score  total-score
     :max-score    12000
     :rank         rank
     :diagnosis    diagnosis}))

(defn report->dict
  "Serialise a MokutekiReport to a string-keyed nested map (matches Python to_dict)."
  [r]
  {"generated_at" (:generated-at r)
   "mokuteki"     (:mokuteki r)
   "principle"    (:principle r)
   "layers"       (mapv layer->dict (:layers r))
   "axes"         (mapv axis->dict (:axes r))
   "total_score"  (:total-score r)
   "max_score"    (:max-score r)
   "rank"         {"name"      (:name (:rank r))
                   "color"     (:color (:rank r))
                   "min_score" (:min-score (:rank r))}
   "diagnosis"    (:diagnosis r)})

;; ── flatten-report (for storage / Parquet) ───────────────────────────────────

(defn- re-key [s]
  (-> s str/lower-case (str/replace #"[^a-z0-9]+" "_") (str/replace #"^_|_$" "")))

(defn flatten-report
  "Flatten a MokutekiReport (Clojure keyword map) to a string-keyed flat map.
   Mirrors Python _flatten_report."
  [report]
  (let [d (report->dict report)
        flat (atom {"generated_at" (get d "generated_at")
                    "total_score"  (get d "total_score")
                    "max_score"    (get d "max_score")
                    "rank_name"    (get-in d ["rank" "name"])})]
    (doseq [layer (get d "layers")]
      (let [lid (str/lower-case (get layer "id"))]
        (swap! flat assoc
               (str "layer_" lid "_score")  (get layer "score")
               (str "layer_" lid "_points") (get layer "points"))))
    (doseq [axis (get d "axes")]
      (let [k (str "axis_" (re-key (get axis "name")) "_points")]
        (swap! flat assoc k (get axis "points"))))
    (swap! flat assoc "diagnosis"
           #?(:clj  (json/generate-string (get d "diagnosis"))
              :cljs (str (get d "diagnosis"))))
    @flat))

;; ── ASCII bar ─────────────────────────────────────────────────────────────────

(defn bar
  "Render a score (0-100) as a filled ASCII bar. Mirrors Python _bar."
  ([score] (bar score 20))
  ([score width]
   (let [filled (min (int (/ (* score width) 100)) width)
         empty  (- width filled)]
     (str "[" (apply str (repeat filled "█")) (apply str (repeat empty "░")) "]"))))

;; ── I/O edge (Clojure/bb only) ────────────────────────────────────────────────

#?(:clj
   (do
     (require '[babashka.fs :as fs])

     (defn- read-jsonld-safe [path]
       (try
         (json/parse-string (slurp path))
         (catch Exception _ {})))

     (defn scan-app-meta
       "Scan kotodama.jsonld files under ws-path. Returns {nanoid → meta-map}.
       Mirrors Python _scan_app_meta."
       [ws-path]
       (let [ws          (fs/file ws-path)
             jsonld-files (filter #(str/ends-with? (str %) "kotodama.jsonld")
                                  (file-seq ws))]
         (into {}
               (for [f jsonld-files
                     :let [data (read-jsonld-safe f)]
                     :let [nanoid (or (get data "nanoid") (get data "id") "")]
                     :when (seq nanoid)]
                 [nanoid
                  {:did          (or (get data "did") (get data "defaultDid") "")
                   :display-name (or (get data "displayName") (get data "name") "")
                   :collections  (get data "collections" [])
                   :wit-imports  (get data "witImports" [])
                   :wit-exports  (get data "witExports" [])}]))))

     (defn eval-layer-a
       "Layer A: Structure — Shannon redundancy, app count, collections.
       Mirrors Python eval_layer_a (filesystem I/O)."
       [ws-path]
       (let [meta         (scan-app-meta ws-path)
             total-apps   (count meta)
             ;; A1: Shannon redundancy — use stub 50 (full eval needs run-all-checks/shannon)
             a1 (make-component "Shannon redundancy" 0.40 50.0
                                "full eval requires etzhayyim.shannon-scores")
             ;; A2: app connectivity (apps with collections)
             apps-with-coll (count (filter (fn [[_ m]] (seq (:collections m))) meta))
             conn-score     (min 100.0 (if (pos? total-apps)
                                         (* (/ apps-with-coll total-apps) 100.0)
                                         0.0))
             a2 (make-component "Directed graph connectivity (proxy)" 0.30 conn-score
                                (str "apps_with_collections=" apps-with-coll "/" total-apps))
             ;; A3: Hypergraph coupling — fewer multi-writer collections = better
             coll-writers (reduce (fn [acc [nanoid m]]
                                    (reduce (fn [a c] (update a c (fnil conj #{}) nanoid))
                                            acc (:collections m)))
                                  {} meta)
             total-colls   (count coll-writers)
             multi         (count (filter (fn [[_ ws]] (> (count ws) 1)) coll-writers))
             hyper-score   (if (pos? total-colls)
                             (* 100.0 (- 1.0 (/ multi total-colls)))
                             100.0)
             a3 (make-component "Hypergraph coupling" 0.15 hyper-score
                                (str "collections=" total-colls ", multi_writer=" multi))
             ;; A4: Type system (WIT exports coverage)
             with-exports  (count (filter (fn [[_ m]] (seq (:wit-exports m))) meta))
             type-score    (if (pos? total-apps) (* (/ with-exports total-apps) 100.0) 0.0)
             a4 (make-component "Category/type system" 0.15 type-score
                                (str "typed=" with-exports "/" total-apps))

             components [a1 a2 a3 a4]
             score      (weighted-score components)
             points     (int (* score 0.30 120))]
         (make-layer "A" "Structure" "構造" 0.30 score points components)))

     (defn eval-layer-d
       "Layer D: Implementation — local filesystem scan.
       Mirrors Python eval_layer_d."
       [ws-path]
       (let [meta       (scan-app-meta ws-path)
             total      (count meta)
             ;; D1: Event sourcing — apps with collections
             with-trigger (count (filter (fn [[_ m]] (seq (:collections m))) meta))
             d1-score     (if (pos? total) (* (/ with-trigger total) 100.0) 0.0)
             d1 (make-component "Event sourcing (Design E)" 0.25 d1-score
                                (str "reactive=" with-trigger "/" total))
             ;; D2: Immutable log — apps with a DID
             with-did    (count (filter (fn [[_ m]] (seq (:did m))) meta))
             d2-score    (if (pos? total) (* (/ with-did total) 100.0) 0.0)
             d2 (make-component "Immutable log (AT Protocol)" 0.20 d2-score
                                (str "with_DID=" with-did "/" total))
             ;; D3: Policy as code — CLAUDE.md presence per project dir
             project-dirs (into #{}
                                 (for [f (file-seq (fs/file ws-path))
                                       :when (str/ends-with? (str f) "kotodama.jsonld")]
                                   (.getParent (.getParentFile (fs/file f)))))
             with-claude  (count (filter #(fs/exists? (fs/file % "CLAUDE.md")) project-dirs))
             d3-score     (if (seq project-dirs)
                            (* (/ with-claude (count project-dirs)) 100.0) 0.0)
             d3 (make-component "Policy as code (CLAUDE.md coverage)" 0.15 d3-score
                                (str "with_CLAUDE.md=" with-claude "/" (count project-dirs)))
             ;; D4: Typed schema — WIT exports
             with-exports (count (filter (fn [[_ m]] (seq (:wit-exports m))) meta))
             d4-score     (if (pos? total) (* (/ with-exports total) 100.0) 0.0)
             d4 (make-component "Typed schema (WIT)" 0.20 d4-score
                                (str "with_exports=" with-exports "/" total))
             ;; D5: Attestation — DID + display_name
             attested     (count (filter (fn [[_ m]]
                                           (and (seq (:did m)) (seq (:display-name m))))
                                         meta))
             d5-score     (if (pos? total) (* (/ attested total) 100.0) 0.0)
             d5 (make-component "Attestation (DID+profile)" 0.20 d5-score
                                (str "attested=" attested "/" total))

             components [d1 d2 d3 d4 d5]
             score      (weighted-score components)
             points     (int (* score 0.25 120))]
         (make-layer "D" "Implementation" "実装" 0.25 score points components)))

     (defn build-mokuteki-report
       "Full report requiring filesystem I/O. Mirrors Python build_mokuteki_report."
       [ws-path]
       (let [now     (str (java.time.Instant/now))
             layer-a (eval-layer-a ws-path)
             layer-b (eval-layer-b-stub)
             layer-c (eval-layer-c-stub)
             layer-d (eval-layer-d ws-path)]
         (build-mokuteki-report-from layer-a layer-b layer-c layer-d now)))))
