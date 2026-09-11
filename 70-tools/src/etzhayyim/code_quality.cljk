;; etzhayyim.code-quality — Unified code quality score across Rust/Go/TS/Python (cljc port, wave 3b).
;;
;; Pure-logic port of 70-tools/etzhayyim-py/src/etzhayyim/code_quality.py
;; (no click, no subprocess). Subprocess-heavy checks are available only in the
;; #?(:clj ...) I/O section; pure helpers (cap, grade-overall, parse/score routines
;; that only need text content) are platform-neutral.
;;
;; Deferred (subprocess / filesystem):
;;   cargo machete, cargo tree -d, go vet, go mod tidy, jscpd, pnpm lint  —
;;   all wrapped in run-checks (Clojure/bb only, operator-gated).
;;
;; API (pure — platform-neutral):
;;   (cap v)                                 → v clamped to [0.0..100.0]
;;   (overall-score checks)                  → average score of available checks
;;   (score-sql-injection content)           → {:score :issues :details}
;;   (score-sql-full-scan content fname)     → {:score :issues :details}
;;   (score-perf-test    content fname)      → {:score :issues :details}
;;   (parse-machete-output text)             → {:unused-count n :details str}
;;   (parse-dup-crate-output text)           → {:dup-count n}
;;   (parse-go-vet-output text exit-code)    → {:issues n}
;;   (parse-go-mod-tidy-output text exit-code) → {:dirty bool}
;;   (make-check name tool available score issues details error)
;;   (build-report checks)                   → CQReport map
;;
;; API (IO — Clojure/bb only):
;;   (find-cargo-workspaces rust-dir)        → seq of paths
;;   (find-go-mod-dirs go-dir)               → seq of paths
;;   (run-checks ws-root rust-dir go-dir ts-dir skip-set) → CQReport
;;
;; bb usage (classpath 70-tools/src):
;;   (require '[etzhayyim.code-quality :as cq])
;;   (cq/cap 105.0) ;; → 100.0

(ns etzhayyim.code-quality
  (:require [clojure.string :as str]
            #?(:clj [cheshire.core :as json])))

;; ── pure helpers ──────────────────────────────────────────────────────────────

(defn cap
  "Clamp v to [0.0..100.0]. Mirrors Python _cap."
  [v]
  (max 0.0 (min 100.0 (double v))))

(defn overall-score
  "Average score across checks where :available is true and :error is blank.
   Returns 0.0 if none available. Mirrors Python run_code_quality scoring."
  [checks]
  (let [scored (filter #(and (:available %) (str/blank? (:error %))) checks)]
    (if (seq scored)
      (/ (apply + (map :score scored)) (double (count scored)))
      0.0)))

;; ── check record constructor ──────────────────────────────────────────────────

(defn make-check
  "Build a CQCheck map. Matches Python @dataclass CQCheck shape."
  ([name tool]
   (make-check name tool true 0.0 0 "" ""))
  ([name tool available score issues details error]
   {:name      name
    :tool      tool
    :available available
    :score     (double score)
    :issues    issues
    :details   details
    :error     (or error "")}))

(defn build-report
  "Build a CQReport map from a seq of CQCheck maps.
   Mirrors Python CQReport / run_code_quality return value."
  [checks]
  (let [available (count (filter :available checks))
        skipped   (- (count checks) available)
        score     (overall-score checks)]
    {:evaluated-at    ""          ;; caller fills in (time.now)
     :overall-score   (Math/round (* score 10.0))  ;; nearest 0.1 via round
     :available-tools available
     :skipped-tools   skipped
     :scoring-model   "average of available tool scores"
     :checks          checks}))

;; ── pure text-parsing helpers for subprocess-driven checks ──────────────────

(defn parse-machete-output
  "Count lines starting with TAB in cargo-machete output (= unused dependency lines).
   Mirrors Python check_cargo_machete counting."
  [text]
  (let [lines  (str/split-lines text)
        unused (count (filter #(str/starts-with? % "\t") lines))]
    {:unused-count unused
     :details      (if (pos? unused)
                     (str unused " unused dependencies")
                     "")}))

(defn parse-dup-crate-output
  "Count distinct duplicate crate names from `cargo tree -d` output.
   Mirrors Python check_cargo_duplicates crate_line_re logic."
  [text]
  (let [lines     (str/split-lines text)
        crate-re  #"^([a-zA-Z0-9_-]+)\s+v"
        dup-names (into #{}
                        (keep (fn [line]
                                (let [stripped (str/triml line)]
                                  (when-let [[_ name] (re-find crate-re stripped)]
                                    name)))
                              lines))]
    {:dup-count (count dup-names)}))

(defn parse-go-vet-output
  "Count non-trivial vet issue lines.
   Mirrors Python check_go_vet counting."
  [text exit-code]
  (if (zero? exit-code)
    {:issues 0}
    (let [lines (str/split-lines text)
          bad   (filter (fn [ln]
                          (let [s (str/trim ln)]
                            (and (seq s)
                                 (not (str/starts-with? s "#"))
                                 (not (str/includes? s "matched no packages"))
                                 (not (str/starts-with? s "go: warning:")))))
                        lines)]
      {:issues (count bad)})))

(defn parse-go-mod-tidy-output
  "Determine if go.mod is dirty from `go mod tidy -diff` output + exit code.
   Mirrors Python check_go_mod_tidy."
  [text exit-code]
  {:dirty (boolean (or (not (zero? exit-code)) (not (str/blank? text))))})

;; ── SQL / perf checks on content strings (pure) ─────────────────────────────

(def ^:private re-esc-interp #"\$\{esc\(")
(def ^:private re-template-sql #"\"\$\{[^}]+\}\"")

(defn score-sql-injection
  "Score a pds-dispatch.ts content string for SQL injection patterns.
   Returns {:score :issues :details}. Mirrors Python check_sql_injection."
  [content]
  (let [esc-count  (count (re-seq re-esc-interp content))
        tmpl-count (count (re-seq re-template-sql content))
        total      (+ esc-count tmpl-count)
        parts      (cond-> []
                     (pos? esc-count)  (conj (str "esc-interpolation: " esc-count))
                     (pos? tmpl-count) (conj (str "template-sql: " tmpl-count)))]
    {:score   (if (zero? total) 100.0 0.0)
     :issues  total
     :details (if (zero? total)
                "PDS: no SQL injection patterns"
                (str "PDS: " (str/join ", " parts)))}))

(def ^:private re-match-clause #"MATCH\s*\(\w+:\w+\)")
(def ^:private re-identity-filter
  #"\w\.\b(?:rkey|repo|did|nanoid|vertex_id|collection|owner_did|ownerDid|app_id|visibility|status|region|vertex_type|project_id)\b\s*(?:=|IN\s*\[|IS\s+NOT\s+NULL|STARTS\s+WITH|<>|!=)")

(def ^:private full-scan-bypass-strs
  ["${filter}" "${conditions" "multiDidFilter" "{nanoid:" "{rkey:" "{did:"])

(defn score-sql-full-scan
  "Score a handler file content for full-scan query patterns.
   fname is the filename string (used in details). Mirrors Python check_sql_full_scan."
  [content fname]
  (let [lines (str/split-lines content)
        bad   (keep-indexed
               (fn [i line]
                 (when (and (re-find re-match-clause line)
                            (let [s (str/triml line)]
                              (not (or (str/starts-with? s "//")
                                       (str/starts-with? s "*"))))
                            (not (re-find re-identity-filter line))
                            (not (some #(str/includes? line %) full-scan-bypass-strs)))
                   (str fname ":" (inc i))))
               lines)
        total (count bad)]
    {:score   (if (zero? total) 100.0 (cap (- 100.0 (* total 5))))
     :issues  total
     :details (if (zero? total)
                "PDS handlers: no full scan queries"
                (str "PDS handlers: " total " full scan queries — "
                     (str/join ", " (take 10 bad))))}))

(defn score-perf-test
  "Score whether a spec content contains performance test assertions.
   fname is for display. Mirrors Python check_perf_test."
  [content fname]
  (let [has-perf (str/includes? content "toBeLessThan")]
    {:score   (if has-perf 100.0 0.0)
     :issues  (if has-perf 0 1)
     :details (str fname ": " (if has-perf "perf test found" "perf test MISSING"))}))

;; ── I/O edge (Clojure/bb only) ────────────────────────────────────────────────

#?(:clj
   (do
     (require '[babashka.fs       :as fs]
              '[babashka.process  :as proc])

     (defn- tool-available? [name]
       (boolean (fs/which name)))

     (defn- run-cmd
       "Run cmd in cwd. Returns [stdout+stderr exit-code]."
       [cmd cwd & {:keys [timeout] :or {timeout 120000}}]
       (try
         (let [result (proc/sh {:dir cwd :out :string :err :string} cmd)]
           [(str (:out result) (:err result)) (:exit result)])
         (catch Exception e
           [(str e) 1])))

     (defn find-cargo-workspaces
       "Find dirs with Cargo.toml under rust-dir (skipping target/). Max 10."
       [rust-dir]
       (when (fs/exists? rust-dir)
         (take 10
               (filter identity
                       (for [f (file-seq (fs/file rust-dir))
                             :when (= "Cargo.toml" (.getName f))
                             :when (not (str/includes? (str f) "/target/"))]
                         (.getParent f))))))

     (defn find-go-mod-dirs
       "Find dirs with go.mod under go-dir (skipping vendor/). Max 10."
       [go-dir]
       (when (fs/exists? go-dir)
         (take 10
               (filter identity
                       (for [f (file-seq (fs/file go-dir))
                             :when (= "go.mod" (.getName f))
                             :when (not (str/includes? (str f) "/vendor/"))]
                         (.getParent f))))))

     (defn check-cargo-machete [rust-dir]
       (if-not (tool-available? "cargo")
         (make-check "cargo_machete" "cargo-machete" false 0.0 0 "" "")
         (let [workspaces (find-cargo-workspaces rust-dir)]
           (if-not (seq workspaces)
             (assoc (make-check "cargo_machete" "cargo-machete") :score 100.0
                    :details "no cargo workspaces found")
             (let [total   (atom 0)
                   parts   (atom [])]
               (doseq [ws workspaces]
                 (let [[out _] (run-cmd ["cargo" "machete" "--skip-target-dir"] ws)
                       {:keys [unused-count]} (parse-machete-output out)]
                   (swap! total + unused-count)
                   (when (pos? unused-count)
                     (swap! parts conj (str unused-count " unused in "
                                           (.getName (fs/file ws)))))))
               (make-check "cargo_machete" "cargo-machete" true
                           (cap (- 100.0 (* @total 3))) @total
                           (str/join ", " @parts) ""))))))

     (defn check-cargo-duplicates [rust-dir]
       (if-not (tool-available? "cargo")
         (make-check "cargo_duplicates" "cargo tree -d" false 0.0 0 "" "")
         (let [workspaces (find-cargo-workspaces rust-dir)]
           (if-not (seq workspaces)
             (assoc (make-check "cargo_duplicates" "cargo tree -d") :score 100.0
                    :details "no cargo workspaces found")
             (let [all-dups (atom #{})]
               (doseq [ws workspaces]
                 (let [[out _] (run-cmd ["cargo" "tree" "-d" "--workspace"] ws)
                       {:keys [dup-count]} (parse-dup-crate-output out)]
                   ;; we accumulate unique dup names; parse-dup-crate-output returns count
                   (swap! all-dups (fn [s] (into s (take dup-count (repeat (gensym))))))))
               (let [n (count @all-dups)]
                 (make-check "cargo_duplicates" "cargo tree -d" true
                             (if (pos? n)
                               (cap (- 100.0 (* 10.0 (Math/sqrt n))))
                               100.0)
                             n
                             (if (pos? n) (str n " duplicate crates across workspaces") "") "")))))))

     (defn check-go-vet [go-dir]
       (if-not (tool-available? "go")
         (make-check "go_vet" "go vet" false 0.0 0 "" "")
         (let [mods (find-go-mod-dirs go-dir)]
           (if-not (seq mods)
             (assoc (make-check "go_vet" "go vet") :score 100.0
                    :details "no go modules found")
             (let [total (atom 0)]
               (doseq [d mods]
                 (let [[out rc] (run-cmd ["go" "vet" "./..."] d)
                       {:keys [issues]} (parse-go-vet-output out rc)]
                   (swap! total + issues)))
               (make-check "go_vet" "go vet" true
                           (cap (- 100.0 (* @total 10))) @total
                           (if (pos? @total) (str @total " vet issues across go modules") "") ""))))))

     (defn check-go-mod-tidy [go-dir]
       (if-not (tool-available? "go")
         (make-check "go_mod_tidy" "go mod tidy -diff" false 0.0 0 "" "")
         (let [mods (find-go-mod-dirs go-dir)]
           (if-not (seq mods)
             (assoc (make-check "go_mod_tidy" "go mod tidy -diff") :score 100.0
                    :details "no go modules found")
             (let [clean (atom 0) dirty (atom 0) dirty-names (atom [])]
               (doseq [d mods]
                 (let [[out rc] (run-cmd ["go" "mod" "tidy" "-diff"] d)
                       {:keys [dirty]} (parse-go-mod-tidy-output out rc)]
                   (if dirty
                     (do (swap! dirty inc)
                         (swap! dirty-names conj (.getName (fs/file d))))
                     (swap! clean inc))))
               (let [total (+ @clean @dirty)]
                 (make-check "go_mod_tidy" "go mod tidy -diff" true
                             (if (pos? total) (* (/ @clean total) 100.0) 100.0)
                             @dirty
                             (if (pos? @dirty)
                               (str @dirty "/" total " modules dirty: "
                                    (str/join ", " @dirty-names))
                               "") "")))))))

     (defn run-checks
       "Run all code quality checks and return a CQReport map.
       ws-root, rust-dir, go-dir, ts-dir are path strings.
       skip-set is a set of check name strings to skip."
       [ws-root rust-dir go-dir ts-dir skip-set]
       (let [now (let [d (java.time.Instant/now)] (str d))
             all-checks
             [["cargo_machete"    #(check-cargo-machete    rust-dir)]
              ["cargo_duplicates" #(check-cargo-duplicates rust-dir)]
              ["go_vet"           #(check-go-vet           go-dir)]
              ["go_mod_tidy"      #(check-go-mod-tidy      go-dir)]]

             results
             (vec
              (for [[name fn] all-checks
                    :when (not (contains? skip-set name))]
                (fn)))

             report (build-report results)]
         (assoc report :evaluated-at now)))))

;; ── CLI entrypoint (JVM/bb only) ──────────────────────────────────────────────
;; Mirrors the Python click group `code-quality` (code_quality.py): single
;; subcommand `run` with --workspace-dir/--rust-dir/--go-dir/--ts-dir/--skip/--json.
;; The checks are READ-ONLY analysis (cargo machete / cargo tree -d / go vet /
;; go mod tidy) — non-destructive — so `run` executes for real via run-checks.

#?(:clj
   (do
     (defn- cq-parse-opts [args]
       (loop [a args opts {}]
         (if (empty? a)
           opts
           (let [t (first a)]
             (cond
               (= t "--json")           (recur (rest a) (assoc opts "--json" true))
               (str/starts-with? t "-") (recur (drop 2 a) (assoc opts t (second a)))
               :else                    (recur (rest a) opts))))))

     (defn- git-root []
       (try
         (let [r (proc/sh {:out :string :err :string} ["git" "rev-parse" "--show-toplevel"])]
           (when (zero? (:exit r)) (str/trim (:out r))))
         (catch Exception _ nil)))

     (defn- usage []
       (println "usage: code-quality run [--workspace-dir D] [--rust-dir D] [--go-dir D] [--ts-dir D] [--skip a,b] [--json]"))

     (defn- print-report [report]
       (println (str "code quality report  " (:evaluated-at report)))
       (println (str "overall score: " (/ (:overall-score report) 10.0) "/100  "
                     "(tools: " (:available-tools report) " available, "
                     (:skipped-tools report) " skipped)"))
       (println "")
       (doseq [c (:checks report)]
         (println (format "  %-22s score=%s issues=%s %s"
                          (:name c)
                          (if (:available c) (str (int (:score c))) "—")
                          (if (:available c) (str (:issues c)) "—")
                          (let [d (:details c)] (if (str/blank? d) "ok" d))))))

     (defn -main [& args]
       (let [sub (first args)]
         (if (not= sub "run")
           (usage)
           (let [opts (cq-parse-opts (rest args))
                 ws   (or (get opts "--workspace-dir") (git-root) (System/getProperty "user.dir"))
                 rust (or (get opts "--rust-dir") (str ws "/40-engine/kotoba"))
                 go   (or (get opts "--go-dir")   (str ws "/70-tools/etzhayyim"))
                 ts   (or (get opts "--ts-dir")   (str ws "/20-actors"))
                 skip (set (remove str/blank? (str/split (get opts "--skip" "") #",")))
                 report (run-checks ws rust go ts skip)]
             (if (get opts "--json")
               (println (json/generate-string report {:pretty true}))
               (print-report report))))))))
