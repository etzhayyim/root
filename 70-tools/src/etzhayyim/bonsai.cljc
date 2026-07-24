;; etzhayyim.bonsai — Workspace growth/prune analysis (cljc port, wave 1).
;;
;; Pure-logic port of 70-tools/etzhayyim-py/src/etzhayyim/bonsai.py
;; (no click, no subprocess, no network I/O — just file-scan scoring logic).
;;
;; 6-tier bonsai model: fruit / flower / leaf / branch / trunk / seed
;;
;; API:
;;   (classify-tier  filename ext)            → tier keyword
;;   (score-node     filename content)        → {:prune-score 0-100 :signals [...]}
;;   (scan-workspace files prune-threshold)   → BonsaiReport map
;;   (growth-health  report)                  → :healthy | :needs-pruning | :overgrown
;;
;; files = seq of {:path str :content str} — callers supply pre-read content.
;; This matches the pattern used by etzhayyim.identifier-audit so both can be
;; driven from the same bb host loop.
;;
;; bb usage (classpath 70-tools/src):
;;   (require '[etzhayyim.bonsai :as bonsai])
;;   (bonsai/scan-workspace
;;     [{:path "src/foo.ts" :content (slurp "src/foo.ts")}] 50)

(ns etzhayyim.bonsai
  (:require [clojure.string :as str]))

;; ── constants (mirrors bonsai.py) ───────────────────────────────────────────────

(def prune-tiers ["fruit" "flower" "leaf" "branch" "trunk" "seed"])

;; Ordered vector of [tier hints] pairs — MOST SPECIFIC first so "seed" wins
;; before the generic ".md" hint in "leaf" can claim CLAUDE.md.
(def ^:private tier-hints
  [["seed"   ["deps.toml" "CLAUDE.md"]]
   ["trunk"  ["kotodama.jsonld" "wrangler.jsonc" "pyproject.toml"]]
   ["fruit"  ["TODO" "FIXME" "HACK" "TEMP" "xxx"]]
   ["flower" ["test_" "_test" ".spec." ".test."]]
   ["leaf"   [".md" ".txt" ".yaml" ".yml" ".toml"]]
   ["branch" [".ts" ".py" ".go"]]])

(def ^:private source-exts #{".ts" ".py" ".go" ".rs" ".svelte"})
(def ^:private ignore-exts #{".lock" ".pckl" ".pyc" ".wasm"})
(def ^:private skip-dirs   #{"node_modules" ".git" "__pycache__" ".venv" "dist" "build" ".langgraph_api"})

;; ── tier classification ─────────────────────────────────────────────────────────

(defn classify-tier
  "Classify a file's bonsai tier from its basename.
   Returns a string: fruit | flower | leaf | branch | trunk | seed."
  [filename]
  (or (some (fn [[tier hints]]
              (when (some #(str/includes? filename %) hints)
                tier))
            tier-hints)
      (cond
        (some #(str/ends-with? filename %) source-exts) "branch"
        :else "leaf")))

;; ── prune scoring ───────────────────────────────────────────────────────────────

(def ^:private re-todo  #"(?i)\b(TODO|FIXME|HACK|TEMP|XXX)\b")
(def ^:private re-dead  #"(?i)//\s*(?:dead|unused|legacy|deprecated)\b")
(def ^:private re-legacy-name #"(?i)(?:^|_)(deprecated|legacy|old|backup|bak)(?:_|$|\.)")

(defn score-node
  "Compute a prune score (0–100) and signals for a file's content.
   Returns {:prune-score N :signals [...]}."
  [filename content]
  (let [todos  (count (re-seq re-todo (or content "")))
        dead   (count (re-seq re-dead (or content "")))
        ;; Treat nil/blank string as 0 lines (empty file).
        ;; `str/split-lines ""` returns [""] (1 element in bb/Clojure),
        ;; so we check blanks explicitly.
        lines  (if (str/blank? (or content ""))
                 0
                 (count (str/split-lines content)))
        ;; Mirror Python elif semantics: empty-file and trivial are mutually exclusive.
        score  (cond-> 0
                 (pos? todos)            (+ (min (* todos 10) 30))
                 (pos? dead)             (+ 20)
                 (zero? lines)           (+ 40)
                 (and (pos? lines)
                      (< lines 5))       (+ 20)
                 (re-find re-legacy-name filename) (+ 30))
        sigs   (cond-> []
                 (pos? todos)  (conj (str todos " TODO/FIXME"))
                 (pos? dead)   (conj "dead code comments")
                 (zero? lines) (conj "empty file")
                 (and (pos? lines) (< lines 5)) (conj (str "trivial (" lines " lines)"))
                 (re-find re-legacy-name filename) (conj "legacy name"))]
    {:prune-score (min score 100)
     :signals     sigs}))

;; ── helpers ─────────────────────────────────────────────────────────────────────

(defn- skip-path?
  "Return true if any path segment is in skip-dirs."
  [path]
  (some skip-dirs (str/split path #"/")))

(defn- ext-of
  "Return the file extension including the dot, e.g. \".ts\"."
  [path]
  (let [base (last (str/split path #"/"))
        dot  (str/last-index-of base ".")]
    (if (and dot (pos? dot))
      (subs base dot)
      "")))

;; ── scan-workspace ──────────────────────────────────────────────────────────────

(defn scan-workspace
  "Scan a collection of {:path str :content str} file maps.
   Returns a BonsaiReport map:
     {:evaluated-at str
      :total-files  N
      :total-lines  N
      :tier-counts  {\"fruit\" N ...}
      :prune-candidates [{:path :tier :lines :prune-score :signals} ...]
      :growth-score 0-100}"
  [files & [prune-threshold]]
  (let [threshold (or prune-threshold 50)
        init-counts (into {} (map #(vector % 0) prune-tiers))
        {:keys [tier-counts nodes total-lines]}
        (reduce
         (fn [acc {:keys [path content]}]
           (if (skip-path? path)
             acc
             (let [ext      (ext-of path)
                   basename (last (str/split path #"/"))]
               (if (ignore-exts ext)
                 acc
                 (let [tier     (classify-tier basename)
                       acc2     (update-in acc [:tier-counts tier] (fnil inc 0))]
                   (if (source-exts ext)
                     (let [c                   (or content "")
                           lines               (if (str/blank? c) 0 (count (str/split-lines c)))
                           {:keys [prune-score
                                   signals]}   (score-node basename c)
                           node                {:path path :tier tier
                                                :lines lines
                                                :prune-score prune-score
                                                :signals signals}]
                       (-> acc2
                           (update :total-lines + lines)
                           (update :nodes conj node)))
                     acc2))))))
         {:tier-counts init-counts :nodes [] :total-lines 0}
         files)

        candidates (->> nodes
                        (filter #(>= (:prune-score %) threshold))
                        (sort-by :prune-score >))

        total-files  (apply + (vals tier-counts))
        fruit-count  (+ (get tier-counts "fruit" 0)
                        (get tier-counts "flower" 0))
        growth-score (max 0 (- 100 (int (/ (* fruit-count 100) (max total-files 1)))))]

    {:evaluated-at   #?(:clj  (str (java.time.Instant/now))
                        :cljs (.toISOString (js/Date.)))
     :total-files    total-files
     :total-lines    total-lines
     :tier-counts    tier-counts
     :prune-candidates (vec candidates)
     :growth-score   growth-score}))

;; ── health classification ────────────────────────────────────────────────────────

(defn growth-health
  "Classify ecosystem health from a BonsaiReport map.
   Returns :healthy | :needs-pruning | :overgrown."
  [{:keys [growth-score]}]
  (cond
    (>= growth-score 70) :healthy
    (>= growth-score 40) :needs-pruning
    :else                :overgrown))
