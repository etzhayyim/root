;; ported from 60-apps/etzhayyim-organism-viz/src/etzhayyim_organism_viz/pruning.py
;; — real port replacing the unit_refactor stage-0 "TODO: port-failed" stubs.
;; NS fixed (the broken stub carried a wrong source-root segment
;; "etzhayyim-organism-viz.src.etzhayyim-organism-viz.pruning"; the correct ns drops
;; the "src" source-root and mirrors the Python module etzhayyim_organism_viz.pruning).
;; .cljc; host file/dir I/O lives behind #?(:clj ...). Self-contained (no sibling requires).
(ns etzhayyim-organism-viz.pruning
  "pruning.py — Pruning candidate detector — operator workflow surface (盆栽 剪定).

  The daemon NEVER prunes. Per §1.3 (anti-individualist, decision attribution =
  etzhayyim) the daemon's job is to *surface* candidates honestly; the operator
  decides whether to `git rm` them.

  A candidate (string-keyed map, matching the Python @dataclass field order) has:
    - \"id\"        (entity id)
    - \"kind\"      (cell / app)
    - \"path\"      (repo-relative path)
    - \"idle_days\" (float)
    - \"severity\"  (int, 1 mild → 3 strong)
    - \"reasons\"   (list of free-text observations)

  Heuristics v0:
    - cells idle > 90 days with no docstring → severity 3
    - cells idle > 90 days with docstring → severity 2
    - cells idle > 30 days, < 90 days → severity 1
    - apps idle > 180 days → severity 2
    - apps idle > 90 days < 180 days → severity 1

  House style: keep candidate maps string-keyed, byte-for-byte the same shape
  the Python @dataclass(asdict) produced; pure fns; host/file I/O at the #?(:clj) edge.
  (The Python __main__ demo is omitted — not ported.)"
  (:require [clojure.string :as str]))

;; The Python @dataclass Candidate field order (kept for parity / documentation).
(def candidate-fields ["id" "kind" "path" "idle_days" "severity" "reasons"])

(defn candidate
  "Build a candidate map (string-keyed, matching the Python @dataclass shape)."
  [id kind path idle-days severity reasons]
  {"id"        id
   "kind"      kind
   "path"      path
   "idle_days" idle-days
   "severity"  severity
   "reasons"   (vec reasons)})

;; ── round-to-1-decimal (Python round(x, 1), banker's rounding) ───────────────
(defn- round1
  "Round to 1 decimal place. Matches Python round(x, 1) (round-half-to-even)."
  [x]
  #?(:clj  (-> (java.math.BigDecimal/valueOf (double x))
               (.setScale 1 java.math.RoundingMode/HALF_EVEN)
               (.doubleValue))
     :cljs (let [scaled (* x 10)
                 fl     (js/Math.floor scaled)
                 diff   (- scaled fl)
                 r      (cond
                          (< diff 0.5) fl
                          (> diff 0.5) (inc fl)
                          ;; exactly .5 → round to even
                          (even? fl)   fl
                          :else        (inc fl))]
             (/ r 10))
     :default (/ (Math/round (* (double x) 10.0)) 10.0)))

;; ── host file/dir helpers (file/network I/O behind #?(:clj ...)) ─────────────
#?(:clj
   (do
     (defn- ^java.io.File as-file [p] (clojure.java.io/file (str p)))

     (defn dir-mtime
       "_dir_mtime(d) — newest last-modified (seconds) of any regular file under d
       (recursively); falls back to d's own mtime when empty; 0.0 on I/O error."
       [d]
       (try
         (let [root (as-file d)
               files (->> (file-seq root)
                          (filter #(.isFile ^java.io.File %)))]
           (if (seq files)
             (/ (double (apply max (map #(.lastModified ^java.io.File %) files))) 1000.0)
             (/ (double (.lastModified root)) 1000.0)))
         (catch java.io.IOException _ 0.0)
         (catch SecurityException _ 0.0)))

     (defn- now-seconds [] (/ (double (System/currentTimeMillis)) 1000.0))

     (defn- list-dirs
       "Immediate sub-entries of `parent` that are directories."
       [parent]
       (let [^java.io.File f (as-file parent)
             kids (.listFiles f)]
         (->> (or kids (make-array java.io.File 0))
              (filter #(.isDirectory ^java.io.File %)))))

     (defn- rel-path
       "repo-relative path string of `child` under `repo` (forward-slashed)."
       [repo child]
       (let [rp (.toPath (as-file repo))
             cp (.toPath (as-file child))]
         (str (.relativize rp cp))))

     (defn scan-cells
       "scan_cells(repo) — surface stale / docstring-less kotodama cells."
       [repo]
       (let [cells (as-file (str repo "/orgs/kotoba-lang/kotodama/cells"))]
         (if-not (.isDirectory cells)
           []
           (let [now (now-seconds)]
             (vec
              (for [^java.io.File d (list-dirs cells)
                    :let [cell-py (as-file (str (.getPath d) "/cell.py"))
                          idle    (/ (- now (dir-mtime d)) 86400.0)
                          init    {:reasons [] :sev 0}
                          ;; idle-window severity (>90 → 2, elif >30 → 1)
                          a (cond
                              (> idle 90) {:reasons (conj (:reasons init)
                                                          (str "idle " (format "%.0f" idle) " days (>90)"))
                                           :sev (max (:sev init) 2)}
                              (> idle 30) {:reasons (conj (:reasons init)
                                                          (str "idle " (format "%.0f" idle) " days (>30)"))
                                           :sev (max (:sev init) 1)}
                              :else init)
                          ;; cell.py presence / size / docstring
                          b (cond
                              (not (.exists cell-py))
                              {:reasons (conj (:reasons a) "no cell.py") :sev (max (:sev a) 2)}
                              (< (.length cell-py) 200)
                              {:reasons (conj (:reasons a) "cell.py very small (<200 bytes)")
                               :sev (max (:sev a) 1)}
                              :else
                              (let [txt (slurp cell-py)]
                                (if-not (str/includes? txt "\"\"\"")
                                  {:reasons (conj (:reasons a) "no docstring") :sev (max (:sev a) 1)}
                                  a)))
                          ;; yorishiro idle nudge
                          c (if (and (str/starts-with? (.getName d) "yorishiro_") (> idle 60))
                              {:reasons (conj (:reasons b) "yorishiro idle >60 (exercise it or prune)")
                               :sev (max (:sev b) 1)}
                              b)]
                    :when (> (:sev c) 0)]
                (candidate (str "cell/" (.getName d)) "cell" (rel-path repo d)
                           (round1 idle) (:sev c) (:reasons c))))))))

     (defn scan-apps
       "scan_apps(repo) — surface stale / README-less 60-apps directories."
       [repo]
       (let [apps (as-file (str repo "/60-apps"))]
         (if-not (.isDirectory apps)
           []
           (let [now (now-seconds)]
             (vec
              (for [^java.io.File d (list-dirs apps)
                    :let [idle (/ (- now (dir-mtime d)) 86400.0)
                          ;; idle-window severity (>180 → 2, elif >90 → 1)
                          a (cond
                              (> idle 180) {:reasons [(str "idle " (format "%.0f" idle) " days (>180)")] :sev 2}
                              (> idle 90)  {:reasons [(str "idle " (format "%.0f" idle) " days (>90)")] :sev 1}
                              :else        {:reasons [] :sev 0})
                          ;; README missingness — only flag when also stale (idle > 30)
                          has-readme? (or (.exists (as-file (str (.getPath d) "/README.md")))
                                          (.exists (as-file (str (.getPath d) "/README"))))
                          b (if (and (> idle 30) (not has-readme?))
                              {:reasons (conj (:reasons a) "no README and stale") :sev (max (:sev a) 1)}
                              a)]
                    :when (> (:sev b) 0)]
                (candidate (str "app/" (.getName d)) "app" (rel-path repo d)
                           (round1 idle) (:sev b) (:reasons b))))))))

     (defn scan-all
       "scan_all(repo) — all candidates, sorted by (-severity, -idle_days)."
       [repo]
       (->> (concat (scan-cells repo) (scan-apps repo))
            (sort-by (juxt #(- (get % "severity")) #(- (get % "idle_days"))))
            vec))))

(defn to-markdown
  "to_markdown(repo, candidates) — render the candidate list as the operator-facing
  Markdown surface. Pure (the `repo` arg is unused, kept for 1:1 signature parity)."
  [_repo candidates]
  (if (empty? candidates)
    (str (str/join "\n"
                   ["# Pruning Candidates"
                    ""
                    (str "**Daemon does not prune.** Per ADR-2605192100 §1.3, decision attribution "
                         "= etzhayyim. The list below is the daemon's honest observation; "
                         "the operator decides what to `git rm`.")
                    ""
                    "_No candidates — the bonsai is currently in healthy growth without overgrowth._"])
         "\n")
    (str/join
     "\n"
     (concat
      ["# Pruning Candidates"
       ""
       (str "**Daemon does not prune.** Per ADR-2605192100 §1.3, decision attribution "
            "= etzhayyim. The list below is the daemon's honest observation; "
            "the operator decides what to `git rm`.")
       ""
       (str "## " (count candidates) " candidate(s) — sorted by severity")
       ""
       "| sev | id | path | idle (days) | reasons |"
       "|---|---|---|---|---|"]
      (for [c candidates
            :let [sev (get c "severity")
                  sev-str (str (apply str (repeat sev "🔴"))
                               (apply str (repeat (- 3 sev) "·")))]]
        (str "| " sev-str " | `" (get c "id") "` | `" (get c "path") "` | "
             (get c "idle_days") " | " (str/join "; " (get c "reasons")) " |"))
      [""
       "## Operator pruning protocol"
       ""
       "```"
       "# 1. Review the candidate (open the directory, read the docstring)"
       "# 2. If 'intentional dormancy', annotate in CLAUDE.md or the path README"
       "# 3. Otherwise:"
       "git rm -r <path>"
       "git commit -m 'prune: <id> — <reason>'"
       "# 4. Document in 90-docs/pruning/<YYMMDD>-<id>.md"
       "```"
       ""]))))

#?(:clj
   (defn emit
     "emit(repo) — write the rendered Markdown to
     <repo>/60-apps/etzhayyim-organism-viz/static/pruning-candidates.md; returns the path."
     [repo]
     (let [out-dir (clojure.java.io/file (str repo "/60-apps/etzhayyim-organism-viz/static"))]
       (.mkdirs out-dir)
       (let [candidates (scan-all repo)
             out (clojure.java.io/file out-dir "pruning-candidates.md")]
         (spit out (to-markdown repo candidates))
         (.getPath out)))))
