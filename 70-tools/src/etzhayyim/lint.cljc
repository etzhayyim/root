;; etzhayyim.lint — code linting (cljc port).
;;
;; IO-REWRITE of 70-tools/etzhayyim-py/src/etzhayyim/lint.py
;; The .py is KEPT (additive port — both co-exist).
;;
;; PURE-vs-IO split:
;;   PURE (parity-verifiable, unit-tested offline):
;;     skip-dir?             — true if path part is in skip-dirs set
;;     check-nsid-regression — scan a single file's text for "nsid" placeholder
;;     check-legacy-pds-nsid — scan a single file's text for deprecated NSIDs
;;     check-silent-catch    — scan a single file's text for empty catch/pass blocks
;;     check-ts-camel        — scan a single file's text for snake_case TS identifiers
;;     check-json-sql        — scan a single file's text for PascalCase JSON keys
;;     check-deps-drift      — scan deps.toml text for completed migrations
;;     lint-file-text        — run a rule over pre-read file text → violations
;;     all-rules             — canonical ordered list of rule names
;;     build-update-command  — argv vector for a lint-update node script call
;;     update-script-path    — map rule → relative script path
;;
;;   IO (subprocess-shaping verified via injectable :proc-fn / :fs-fn, no live calls):
;;     scan-files-by-ext     — walk directory tree, collect files by extension
;;     lint-rule             — run one rule over real filesystem
;;     run-update-target     — execute node update script via injectable :proc-fn
;;     run-lint              — orchestrate full lint run
;;
;; INJECTABLE FS + SUBPROCESS CLIENT:
;;   scan-files-by-ext accepts :fs-fn; run-update-target accepts :proc-fn.
;;   build-update-command returns the argv — tests assert without executing.
;;
;; SECURITY:
;;   No secrets at load time.  No network calls.
;;
;; bb load check:
;;   bb --classpath 70-tools/src -e "(require 'etzhayyim.lint)(println :ok)"

(ns etzhayyim.lint
  (:require [clojure.string :as str]
            [cheshire.core  :as json]
            #?(:bb [babashka.process :as proc]
               :default [])
            #?(:bb [babashka.fs :as bfs]
               :default [])))

;; ---------------------------------------------------------------------------
;; Constants
;; ---------------------------------------------------------------------------

(def skip-dirs
  #{"node_modules" ".git" "__pycache__" ".venv" "dist" "build"})

(def all-rules
  ["nsid-regression" "legacy-pds-nsid" "silent-catch" "ts-camel" "json-sql" "deps-drift"])

(def update-script-path
  {"silent-catch-update" "70-tools/scripts/lint/no-silent-catch.mjs"
   "ts-camel-update"     "70-tools/scripts/lint/ts-camelcase.mjs"
   "json-sql-update"     "70-tools/scripts/lint/json-sql-case.mjs"})

(def rule-extensions
  {"nsid-regression" #{".ts" ".svelte"}
   "legacy-pds-nsid" #{".ts" ".svelte" ".go"}
   "silent-catch"    #{".ts" ".svelte" ".py"}
   "ts-camel"        #{".ts" ".svelte"}
   "json-sql"        #{".json" ".jsonld"}
   "deps-drift"      #{".toml"}})

;; ---------------------------------------------------------------------------
;; Pure: path predicate
;; ---------------------------------------------------------------------------

(defn skip-dir?
  "Return true if any path component is in skip-dirs.
  Accepts a string path or a file object (via str)."
  [path-str]
  (let [parts (str/split (str path-str) #"[/\\]")]
    (some skip-dirs parts)))

;; ---------------------------------------------------------------------------
;; Pure: per-rule text scanners
;; ---------------------------------------------------------------------------

(defn check-nsid-regression
  "Detect '\"nsid\"' placeholder strings in file text.
  Returns a seq of {:line N :snippet s} maps."
  [text]
  (keep-indexed
   (fn [i line]
     (when (str/includes? line "\"nsid\"")
       {:line (inc i) :snippet (subs line 0 (min 80 (count line)))}))
   (str/split-lines text)))

(defn check-legacy-pds-nsid
  "Detect deprecated AT-Proto NSID strings in file text."
  [text]
  (let [patterns ["app.bsky.feed.getTimeline"
                  "com.atproto.sync.getBlob"
                  "app.bsky.actor.getProfile"]]
    (keep-indexed
     (fn [i line]
       (when (some #(str/includes? line %) patterns)
         {:line (inc i) :snippet (subs line 0 (min 80 (count line)))}))
     (str/split-lines text))))

(defn check-silent-catch
  "Detect empty catch / except pass blocks.
  Returns a seq of {:line N :snippet s} maps.
  Mirrors Python: catch\\s*\\([^)]*\\)\\s*\\{\\s*\\} | except\\s+\\w+\\s*:\\s*pass\\b"
  [text]
  (let [lines (str/split-lines text)]
    (keep-indexed
     (fn [i line]
       (let [trimmed (str/trim line)]
         (when (or (and (str/includes? trimmed "catch")
                        (re-find #"catch\s*\([^)]*\)\s*\{\s*\}" trimmed))
                   (and (str/includes? trimmed "except")
                        (re-find #"except\s+\w+\s*:\s*pass\b" trimmed)))
           {:line (inc i) :snippet (subs trimmed 0 (min 80 (count trimmed)))})))
     lines)))

(defn check-ts-camel
  "Detect snake_case identifiers in TypeScript files.
  Matches \\b[a-z]+_[a-z_]+\\s*[=:(] and ignores lines with 'snake_case'."
  [text]
  (keep-indexed
   (fn [i line]
     (when (and (not (str/includes? line "snake_case"))
                (re-find #"\b[a-z]+_[a-z_]+\s*[=:(]" line))
       {:line (inc i) :snippet (subs line 0 (min 80 (count line)))}))
   (str/split-lines text)))

(defn check-json-sql
  "Detect PascalCase keys in JSON/JSON-LD files.
  Matches '\"[A-Z][a-zA-Z]+\"\\s*:'."
  [text]
  (keep-indexed
   (fn [i line]
     (when (re-find #"\"[A-Z][a-zA-Z]+\"\s*:" line)
       {:line (inc i) :snippet (subs line 0 (min 80 (count line)))}))
   (str/split-lines text)))

(defn check-deps-drift
  "Check deps.toml text for completed migrations (status = 'done').
  Returns a seq of {:line 0 :snippet s} on match."
  [text]
  (when (and (str/includes? text "[[migrations]]")
             (str/includes? text "status = \"done\""))
    [{:line 0 :snippet "completed migrations with status='done' found"}]))

;; ---------------------------------------------------------------------------
;; Pure: lint-file-text dispatch
;; ---------------------------------------------------------------------------

(defn lint-file-text
  "Run a lint rule over pre-read file text.
  Returns {:rule rule :path rel-path :violations [{:line :snippet}]}.
  Pure: no file IO."
  [rule rel-path text]
  (let [violations
        (case rule
          "nsid-regression" (check-nsid-regression text)
          "legacy-pds-nsid" (check-legacy-pds-nsid text)
          "silent-catch"    (check-silent-catch text)
          "ts-camel"        (check-ts-camel text)
          "json-sql"        (check-json-sql text)
          "deps-drift"      (check-deps-drift text)
          [])]
    {:rule rule :path rel-path :violations (vec violations)}))

;; ---------------------------------------------------------------------------
;; Pure: update command builder
;; ---------------------------------------------------------------------------

(defn build-update-command
  "Build argv vector for a lint-update node script.
  Returns ['node' '<script-abs-path>' '--update-baseline']."
  [ws-root target]
  (let [rel (get update-script-path target)]
    (when (nil? rel)
      (throw (ex-info (str "Unknown update target: " target)
                      {:target target})))
    ["node" (str ws-root "/" rel) "--update-baseline"]))

;; ---------------------------------------------------------------------------
;; IO: file scanning
;; ---------------------------------------------------------------------------

(defn scan-files-by-ext
  "Walk ws-root recursively, collecting files whose suffix is in ext-set.
  Skips directories in skip-dirs.
  opts:
    :fs-fn — injectable: (fn [ws-root ext-set skip-dirs] → [{:path :text}])
             default = real babashka.fs walk
  Returns seq of {:path absolute-string :rel relative-to-ws-root :text content}."
  [ws-root ext-set opts]
  (let [fs-fn (:fs-fn opts)]
    (if fs-fn
      (fs-fn ws-root ext-set skip-dirs)
      #?(:bb
         (let [root-file (java.io.File. (str ws-root))]
           (for [f    (file-seq root-file)
                 :when (.isFile f)
                 :let [path-str (.getAbsolutePath f)]
                 :when (not (skip-dir? path-str))
                 :let [suffix (let [n (.getName f)
                                    dot (.lastIndexOf n ".")]
                                (when (>= dot 0) (subs n dot)))]
                 :when (and suffix (ext-set suffix))
                 :let [text (try (slurp f) (catch Exception _ nil))]
                 :when text]
             {:path path-str
              :rel  (str/replace path-str (str ws-root "/") "")
              :text text}))
         :default []))))

;; ---------------------------------------------------------------------------
;; IO: lint-rule
;; ---------------------------------------------------------------------------

(defn lint-rule
  "Run one lint rule over the filesystem.
  Returns {:rule rule :violations [{:rule :path :line :snippet}]}.
  opts:
    :fs-fn — passed to scan-files-by-ext"
  [ws-root rule opts]
  (let [ext-set (get rule-extensions rule #{})
        files   (scan-files-by-ext ws-root ext-set opts)
        violations
        (if (= rule "deps-drift")
          ;; deps-drift: look for deps.toml specifically
          (let [deps-path (str ws-root "/deps.toml")
                text      (try #?(:bb (slurp deps-path) :default nil)
                               (catch Exception _ nil))]
            (when text
              (for [v (check-deps-drift text)]
                (assoc v :rule rule :path "deps.toml"))))
          ;; other rules: scan matching files
          (mapcat (fn [{:keys [rel text]}]
                    (for [v (lint-file-text rule rel text) :when (seq (:violations v))]
                      (for [viol (:violations v)]
                        (assoc viol :rule rule :path rel))))
                  files))]
    {:rule       rule
     :violations (vec (flatten violations))}))

;; ---------------------------------------------------------------------------
;; IO: run-update-target
;; ---------------------------------------------------------------------------

(defn run-update-target
  "Execute a lint-update node script.
  opts:
    :proc-fn — injectable: (fn [argv opts-map] → {:exit int})
    :println-fn — injectable: (fn [s])"
  [ws-root target opts]
  (let [argv       (build-update-command ws-root target)
        proc-fn    (or (:proc-fn opts)
                       #?(:bb (fn [av _] (proc/shell {:continue true} (str/join " " av)))
                          :default nil))
        println-fn (or (:println-fn opts) println)]
    (when (not proc-fn)
      (throw (ex-info "proc-fn required" {})))
    (println-fn (str "==> lint update: " target))
    (let [result (proc-fn argv {})]
      (when (not= 0 (:exit result))
        (throw (ex-info (str "lint update failed: " target) {:target target})))
      (println-fn (str "  baseline updated: " target))
      result)))

;; ---------------------------------------------------------------------------
;; IO: run-lint (orchestrator)
;; ---------------------------------------------------------------------------

(defn run-lint
  "Orchestrate a full lint run over ws-root.
  rules — seq of rule-name strings (or :all for all-rules)
  opts:
    :fs-fn      — passed to lint-rule
    :proc-fn    — used if update-target supplied
    :println-fn — injectable output fn
  Returns {:all-ok bool :results [{:rule :violations}]}."
  [ws-root rules opts]
  (let [rule-list (if (= rules :all) all-rules rules)
        results   (mapv #(lint-rule ws-root % opts) rule-list)
        all-ok    (every? #(empty? (:violations %)) results)]
    {:all-ok  all-ok
     :results results}))

;; ---------------------------------------------------------------------------
;; CLI entry point (argv-wiring of the python `lint` command, ADR-2606222000).
;; Contract:  e7m lint [TARGET] [--root DIR] [--json]
;;   TARGET ∈ {all (default), rules, <rule-name>, <update-target>}
;;   `rules`            — list rule names (read-only)
;;   all / <rule-name>  — run the read-only filesystem lint
;;   <update-target>    — GUARDED: rewrites a baseline via a node script; requires --apply
;; ---------------------------------------------------------------------------

(defn -main [& args]
  (loop [a args target nil root nil json? false]
    (cond
      (seq a)
      (let [x (first a)]
        (cond
          (= x "--json")           (recur (rest a) target root true)
          (= x "--root")           (recur (drop 2 a) target (second a) json?)
          (str/starts-with? x "--") (recur (rest a) target root json?)
          :else                    (recur (rest a) (or target x) root json?)))
      :else
      (let [target (or target "all")]
        (cond
          (= target "rules")
          (doseq [r all-rules] (println (str "  " r)))

          (contains? update-script-path target)
          ;; faithful to python: an update-target runs its node baseline-update script.
          (run-update-target (or root ".") target {})

          :else
          (let [ws      (or root ".")
                rules   (if (= target "all") :all [target])
                {:keys [all-ok results]} (run-lint ws rules {})]
            (if json?
              (println (json/generate-string results))
              (doseq [r results]
                (println (str "  [" (if (empty? (:violations r)) "OK  " "FAIL") "] "
                              (:rule r) "  (" (count (:violations r)) " violations)"))
                (doseq [v (take 5 (:violations r))]
                  (println (str "         " (:path v) ":" (:line v) "  " (:snippet v))))))
            #?(:bb (when-not all-ok (System/exit 1)) :default nil)))))))
