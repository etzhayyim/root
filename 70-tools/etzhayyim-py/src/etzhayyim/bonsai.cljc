;; ported from 70-tools/etzhayyim-py/src/etzhayyim/bonsai.py — real port replacing the
;; unit_refactor stage-0 "TODO: port-failed" stubs. NS fixed
;; (etzhayyim-py.src.etzhayyim.bonsai -> etzhayyim.bonsai, the src/ source-root package
;; matching src/etzhayyim/bonsai.py per pyproject.toml [tool.hatch ... packages = src/etzhayyim]).
;; Self-contained: the sibling shannon._resolve_root helper is inlined (find-git-root +
;; resolve-root) rather than (:require)-ing the sibling stub namespace; all host/file/time
;; I/O is behind #?(:clj ...). Python "__main__"/CLI-only echo formatting is preserved in the
;; report builders; the click group/command wiring is the host CLI edge.
;;
;; bonsai — Workspace growth/prune analysis (ADR-2605080100, ADR-2605091300).
;; 6-tier pruning: fruit/flower/leaf/branch/trunk/seed.
(ns etzhayyim.bonsai
  "bonsai — Workspace growth/prune analysis.
  1:1 Clojure port of `src/etzhayyim/bonsai.py`. Pure analysis; host/file/time I/O at the
  #?(:clj ...) edge only. BonsaiNode / BonsaiReport dataclasses become string-keyed maps
  (the same shapes Python's to_dict() produced)."
  (:require [clojure.string :as str]))

;; ── pruning tiers ─────────────────────────────────────────────────────────────
(def prune-tiers ["fruit" "flower" "leaf" "branch" "trunk" "seed"])

(def ^:private tier-hints
  ;; insertion order matters (Python dict iteration order) — use an ordered seq of pairs.
  [["fruit"  ["TODO" "FIXME" "HACK" "TEMP" "xxx"]]
   ["flower" ["test_" "_test" ".spec." ".test."]]
   ["leaf"   [".md" ".txt" ".yaml" ".yml" ".toml"]]
   ["branch" [".ts" ".py" ".go"]]
   ["trunk"  ["kotodama.jsonld" "wrangler.jsonc" "pyproject.toml"]]
   ["seed"   ["deps.toml" "CLAUDE.md"]]])

(def ^:private skip-dirs #{"node_modules" ".git" "__pycache__" ".venv" "dist" "build" ".langgraph_api"})
(def ^:private source-exts #{".ts" ".py" ".go" ".rs" ".svelte"})
(def ^:private ignore-exts #{".lock" ".pckl" ".pyc" ".wasm"})

;; ── BonsaiNode / BonsaiReport to-dict (string-keyed maps) ─────────────────────
(defn bonsai-node->dict [node]
  {"path"        (get node "path")
   "tier"        (get node "tier")
   "lines"       (get node "lines")
   "prune_score" (get node "prune_score")
   "signals"     (get node "signals")})

(defn bonsai-report->dict [report]
  {"evaluated_at"     (get report "evaluated_at")
   "total_files"      (get report "total_files")
   "total_lines"      (get report "total_lines")
   "tier_counts"      (get report "tier_counts")
   "prune_candidates" (mapv bonsai-node->dict (get report "prune_candidates"))
   "growth_score"     (get report "growth_score")})

;; ── path helpers (faithful to pathlib .name / .suffix / .parts) ───────────────
(defn- path-name
  "pathlib Path.name — the final path component."
  [path]
  (let [parts (str/split path #"/")]
    (or (last (remove str/blank? parts)) "")))

(defn- path-suffix
  "pathlib Path.suffix — the final dotted extension of the name (incl. leading dot), or ''."
  [path]
  (let [nm (path-name path)
        i  (str/last-index-of nm ".")]
    ;; Python: a leading-dot dotfile (no other dot) has suffix '' (i == 0 → none).
    (if (and i (pos? i)) (subs nm i) "")))

(defn- path-parts
  "pathlib Path.parts approximation — the non-empty path components."
  [path]
  (vec (remove str/blank? (str/split path #"/"))))

;; ── classification ────────────────────────────────────────────────────────────
(defn classify-tier [path]
  (let [name   (path-name path)
        suffix (path-suffix path)]
    (or
     (some (fn [[tier hints]]
             (when (some #(str/includes? name %) hints) tier))
           tier-hints)
     (cond
       (contains? source-exts suffix) "branch"
       (contains? #{".md" ".txt" ".yaml" ".yml" ".toml" ".json"} suffix) "leaf"
       :else "leaf"))))

;; ── scoring ───────────────────────────────────────────────────────────────────
(def ^:private re-todo
  #?(:clj (java.util.regex.Pattern/compile "\\b(TODO|FIXME|HACK|TEMP|XXX)\\b" java.util.regex.Pattern/CASE_INSENSITIVE)
     :cljs (js/RegExp. "\\b(TODO|FIXME|HACK|TEMP|XXX)\\b" "gi")
     :default nil))

(def ^:private re-dead-code
  #?(:clj (java.util.regex.Pattern/compile "//\\s*(?:dead|unused|legacy|deprecated)\\b" java.util.regex.Pattern/CASE_INSENSITIVE)
     :cljs (js/RegExp. "//\\s*(?:dead|unused|legacy|deprecated)\\b" "gi")
     :default nil))

(def ^:private re-legacy-name
  #?(:clj (java.util.regex.Pattern/compile "(?:^|_)(deprecated|legacy|old|backup|bak)(?:_|$|\\.)" java.util.regex.Pattern/CASE_INSENSITIVE)
     :cljs (js/RegExp. "(?:^|_)(deprecated|legacy|old|backup|bak)(?:_|$|\\.)" "i")
     :default nil))

(defn- count-matches
  "Number of (non-overlapping) matches of a regex in s — mirrors len(re.findall(...))."
  [re s]
  #?(:clj (let [m (re-matcher re s)]
            (loop [n 0] (if (.find m) (recur (inc n)) n)))
     :cljs (let [ms (.match s re)] (if ms (.-length ms) 0))
     :default (throw (ex-info "bind a regex impl on this host" {}))))

(defn- re-search?
  "Whether re matches anywhere in s — mirrors bool(re.search(...))."
  [re s]
  #?(:clj (.find (re-matcher re s))
     :cljs (boolean (.match s re))
     :default (throw (ex-info "bind a regex impl on this host" {}))))

(defn- count-newlines [s]
  (count (filter #(= % \newline) s)))

(defn score-node
  "(path, content) -> [score signals]. Pure. 0–100, higher = more pruneable."
  [path content]
  (let [todos (count-matches re-todo content)
        dead? (re-search? re-dead-code content)
        lines (count-newlines content)
        s0    {:score 0 :signals []}
        s1    (if (pos? todos)
                (-> s0
                    (update :score + (min (* todos 10) 30))
                    (update :signals conj (str todos " TODO/FIXME")))
                s0)
        s2    (if dead?
                (-> s1 (update :score + 20)
                    (update :signals conj "dead code comments"))
                s1)
        s3    (cond
                (zero? lines) (-> s2 (update :score + 40)
                                  (update :signals conj "empty file"))
                (< lines 5)   (-> s2 (update :score + 20)
                                  (update :signals conj (str "trivial (" lines " lines)")))
                :else         s2)
        s4    (if (re-search? re-legacy-name (path-name path))
                (-> s3 (update :score + 30)
                    (update :signals conj "legacy name"))
                s3)]
    [(min (:score s4) 100) (:signals s4)]))

;; ── workspace scan ────────────────────────────────────────────────────────────
#?(:clj
   (defn- list-files
     "All regular files under root (recursive); paths absolute strings."
     [root]
     (->> (file-seq (clojure.java.io/file root))
          (filter #(.isFile ^java.io.File %))
          (map #(.getPath ^java.io.File %)))))

#?(:clj
   (defn- relative-to [^String path ^String root]
     (let [root (str/replace root #"/+$" "")
           pfx  (str root "/")]
       (if (str/starts-with? path pfx)
         (subs path (count pfx))
         path))))

#?(:clj
   (defn scan-workspace
     "Scan a workspace (a directory path) → a BonsaiReport map. File I/O edge."
     ([ws] (scan-workspace ws 50))
     ([ws prune-threshold]
      (let [ws (str ws)
            init-counts (into {} (map (fn [t] [t 0])) prune-tiers)
            files (list-files ws)
            {:keys [tier-counts nodes total-lines]}
            (reduce
             (fn [acc p]
               (cond
                 (some #(contains? skip-dirs %) (path-parts p)) acc
                 (contains? ignore-exts (path-suffix p)) acc
                 :else
                 (let [tier (classify-tier p)
                       acc  (update-in acc [:tier-counts tier] (fnil inc 0))]
                   (if-not (contains? source-exts (path-suffix p))
                     acc
                     (let [content (try (slurp p) (catch java.io.IOException _ nil))]
                       (if (nil? content)
                         acc
                         (let [lines (count-newlines content)
                               [prune-score signals] (score-node p content)
                               rel   (relative-to p ws)]
                           (-> acc
                               (update :total-lines + lines)
                               (update :nodes conj
                                       {"path" rel "tier" tier "lines" lines
                                        "prune_score" prune-score "signals" signals})))))))))
             {:tier-counts init-counts :nodes [] :total-lines 0}
             files)
            candidates  (->> nodes
                             (filter #(>= (get % "prune_score") prune-threshold))
                             (sort-by #(get % "prune_score") >)
                             vec)
            total-files (reduce + (vals tier-counts))
            fruit-count (+ (get tier-counts "fruit" 0) (get tier-counts "flower" 0))
            growth-score (max 0 (- 100 (int (* (/ (double fruit-count) (max total-files 1)) 100))))]
        {"evaluated_at"     (let [fmt (java.text.SimpleDateFormat. "yyyy-MM-dd'T'HH:mm:ss'Z'")]
                              (.setTimeZone fmt (java.util.TimeZone/getTimeZone "UTC"))
                              (.format fmt (java.util.Date.)))
         "total_files"      total-files
         "total_lines"      total-lines
         "tier_counts"      tier-counts
         "prune_candidates" candidates
         "growth_score"     growth-score}))))

;; ── workspace-root resolution (inlined shannon._resolve_root / _find_git_root) ─
#?(:clj
   (defn- find-git-root [start]
     (loop [p (.getCanonicalFile (clojure.java.io/file start))]
       (let [parent (.getParentFile p)]
         (cond
           (.exists (clojure.java.io/file p ".git")) (.getPath p)
           (nil? parent) (.getPath p)
           :else (recur parent))))))

#?(:clj
   (defn resolve-root [override]
     (if (and override (not (str/blank? (str override))))
       (.getPath (.getCanonicalFile (clojure.java.io/file (str override))))
       (find-git-root (System/getProperty "user.dir")))))

;; ── CLI verbs (host edge). Return the textual lines a click.echo would emit, OR
;;    raise the "use the Go binary" ex-info the DB-backed verbs raised. ───────────
#?(:clj
   (defn bonsai
     "Top-level bonsai group body (invoke_without_command)."
     ([] (bonsai nil false))
     ([workspace-dir json-out]
      (let [ws (resolve-root workspace-dir)
            report (scan-workspace ws)]
        (if json-out
          (bonsai-report->dict report)
          (str/join "\n"
                    (concat
                     [(str "bonsai: growth=" (get report "growth_score")
                           "  files=" (get report "total_files")
                           "  lines=" (get report "total_lines"))
                      (str "  tiers: "
                           (str/join "  " (map #(str % "=" (get (get report "tier_counts") % 0)) prune-tiers)))]
                     (when (seq (get report "prune_candidates"))
                       [(str "  prune candidates: " (count (get report "prune_candidates")))]))))))))

#?(:clj
   (defn bonsai-scan
     ([] (bonsai-scan nil false))
     ([workspace-dir json-out]
      (let [ws (resolve-root workspace-dir)
            report (scan-workspace ws)]
        (if json-out
          (bonsai-report->dict report)
          (str "files=" (get report "total_files")
               "  lines=" (get report "total_lines")
               "  growth=" (get report "growth_score")))))))

#?(:clj
   (defn bonsai-prune
     ([] (bonsai-prune nil false 50 20))
     ([workspace-dir json-out threshold top]
      (let [ws (resolve-root workspace-dir)
            report (scan-workspace ws threshold)
            candidates (vec (take top (get report "prune_candidates")))]
        (if json-out
          (mapv bonsai-node->dict candidates)
          (if (empty? candidates)
            "  no prune candidates above threshold"
            (str/join "\n"
                      (map (fn [n]
                             (str "  [" (format "%3d" (get n "prune_score")) "] ["
                                  (format "%-6s" (get n "tier")) "] " (get n "path")
                                  "  (" (str/join ", " (get n "signals")) ")"))
                           candidates))))))))

#?(:clj
   (defn bonsai-status
     ([] (bonsai-status nil false))
     ([workspace-dir json-out]
      (let [ws (resolve-root workspace-dir)
            report (scan-workspace ws)
            growth (get report "growth_score")
            health (cond (>= growth 70) "healthy"
                         (>= growth 40) "needs pruning"
                         :else "overgrown")]
        (if json-out
          {"health" health
           "growth_score" growth
           "prune_candidates" (count (get report "prune_candidates"))}
          (str "bonsai status: " health "  growth=" growth
               "  prune_candidates=" (count (get report "prune_candidates"))))))))

;; ── DB-backed verbs: faithful to the Python ClickException raises ──────────────
(defn bonsai-canopy [min-eta max-eta status-filter limit json-out]
  (throw (ex-info "bonsai canopy requires direct Kotoba/Datomic access (etzhayyimdb). Use the Go binary: etzhayyim bonsai canopy" {})))

(defn bonsai-growth [growth-type limit json-out]
  (throw (ex-info "bonsai growth requires direct Kotoba/Datomic access (etzhayyimdb). Use the Go binary: etzhayyim bonsai growth" {})))

(defn bonsai-release [actor-did json-out yes]
  (throw (ex-info "bonsai release requires direct Kotoba/Datomic access (etzhayyimdb). Use the Go binary: etzhayyim bonsai release"
                  {:actor-did actor-did :json-out json-out :yes yes})))
