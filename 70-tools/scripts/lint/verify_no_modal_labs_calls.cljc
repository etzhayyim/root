(ns scripts.lint.verify-no-modal-labs-calls
  "CI grep gate — forbid Modal Labs server references in kotoba_murakumo source.

  Clojure (.cljc) port of `verify_no_modal_labs_calls.py` — replaces the
  stage-0 `port-failed` stub 1:1.

  Enforces ADR-2605282000 N1: NEVER call Modal Labs servers (modal.com /
  api.modal.com) from any kotoba_murakumo runtime code path. The violation
  regex + allow-list are a charter-enforcement gate; both port verbatim.

  Allow-list semantics (matched AFTER the violation regex, so an excluded
  line never triggers): README.md trademark notice + ADR-2605282000
  trademark mention. (The Python carries the allow-list in its docstring;
  this port makes it executable so the contract is testable — `allow-listed?`
  is consulted only on a line that already matched the violation regex.)

  Exit codes (the contract):
    0 — clean (no violations)
    1 — at least one violation found

  Pure scan fns (`violation-matches`, `scan-text`, `find-violations`) carry
  no I/O; the file walk + stdout/stderr + exit live at #?(:clj) edges
  (`-main`) via clojure.java.io — same I/O-at-edges discipline as
  20-actors/ibuki/methods/infer.cljc + orgs/etzhayyim/com-etzhayyim-mimamori/methods/bond.cljc.
  kebab keyword keys; closed argv vocab → ex-info."
  (:require [clojure.string :as str]
            #?(:clj [clojure.java.io :as io])))

;; Repo-root-relative path to the runtime source tree we guard.
;; kotoba_murakumo was re-integrated into the kotoba submodule (ADR-2606074000);
;; it now lives at 40-engine/kotoba/py/kotoba_murakumo/.
(def package-root "40-engine/kotoba/py/kotoba_murakumo/kotoba_murakumo")

;; Suffixes we walk (1:1 with Python `_EXTS = {".py"}`).
(def exts #{".py"})

;; Patterns that constitute a violation of ADR-2605282000 N1.
;; Word-boundary anchors keep false positives off (e.g. "promodal" doesn't
;; match). re.MULTILINE → (?m): in Java/JS `$` then matches end-of-line, so
;; `\bimport\s+modal\s*$` anchors to a line end exactly as the Python does.
(def ^:private violation-pattern-str
  ;; (?m) = re.MULTILINE: `$` matches end-of-line so `\bimport\s+modal\s*$`
  ;; anchors to a line end exactly as the Python does.
  (str "(?m)(?:\\bhttps?://(?:api\\.)?modal\\.com\\b"
       "|\\bapi\\.modal\\.com\\b"
       "|\\bmodal\\.com/[A-Za-z0-9_\\-/]+"
       "|\\bfrom\\s+modal\\s+import\\b"
       "|\\bimport\\s+modal\\s*$"
       "|\\bimport\\s+modal\\s+as\\b)"))

(def violation-re (re-pattern violation-pattern-str))

;; Allow-list — lines that, although they hit the violation regex, are a
;; documented trademark mention and so are EXCLUDED (matched after the
;; violation regex per the Python's allow-list-matched-after semantics).
;; Conservative + content-based (no path dependence): only a literal
;; trademark/ADR notice qualifies, never a live call or import.
(def allow-list-re
  (re-pattern
   (str "(?i)"
        "(?:trademark|商標"
        "|ADR-2605282000"
        "|modal labs(?:[^.]*?(?:trademark|商標|mention|owner|inc\\.?))?)")))

;; ── pure scan fns (no I/O) ───────────────────────────────────────

(defn allow-listed?
  "Is this single source line an allow-listed trademark/ADR mention? Consulted
  ONLY on a line that already matched the violation regex (allow-list matched
  AFTER the violation regex — Python docstring semantics, made executable)."
  [line]
  (boolean (re-find allow-list-re (str line))))

(defn- line-no-at
  "1-based line number of char index `idx` in `text` (Python:
  text[:m.start()].count('\\n') + 1)."
  [text idx]
  (inc (count (filter #(= % \newline) (subs text 0 idx)))))

(defn violation-matches
  "Every NON-allow-listed violation in `text`, as ordered
  {:line <1-based> :match <matched substring>} maps. Pure; the unit the test
  exercises on synthetic strings."
  [text]
  (let [text (str text)]
    #?(:clj
       (let [m (re-matcher violation-re text)]
         (loop [acc []]
           (if (.find m)
             (let [start (.start m)
                   match (.group m)
                   ln (line-no-at text start)
                   line (nth (str/split-lines text) (dec ln) "")]
               (recur (if (allow-listed? line)
                        acc
                        (conj acc {:line ln :match match}))))
             acc)))
       :default
       ;; portable fallback: scan line-by-line (the regex carries no
       ;; cross-line construct, so per-line == whole-text here).
       (let [lines (str/split-lines text)]
         (vec
          (keep-indexed
           (fn [i line]
             (when-let [match (re-find violation-re line)]
               (when-not (allow-listed? line)
                 {:line (inc i)
                  :match (if (vector? match) (first match) match)})))
           lines))))))

(defn scan-text
  "Convenience boolean: does `text` carry at least one non-allow-listed
  violation? (Used by tests + callers that only need clean/violation.)"
  [text]
  (boolean (seq (violation-matches text))))

;; ── file I/O at the #?(:clj) edge ────────────────────────────────

#?(:clj
   (defn- file-ext
     "The suffix of `path` incl. the dot (\".py\"), or \"\" if none — mirrors
     pathlib `Path.suffix`."
     [^String path]
     (let [name (.getName (io/file path))
           dot (.lastIndexOf name ".")]
       (if (pos? dot) (subs name dot) ""))))

#?(:clj
   (defn- walk-files
     "Sorted recursive list of regular files under `dir` whose suffix is in
     `exts` (1:1 with `sorted(pkg.rglob('*'))` + the suffix filter)."
     [dir]
     (let [root (io/file dir)]
       (->> (file-seq root)
            (filter #(.isFile ^java.io.File %))
            (filter #(contains? exts (file-ext (.getPath ^java.io.File %))))
            (map #(.getPath ^java.io.File %))
            sort))))

#?(:clj
   (defn find-violations
     "Walk the guarded package tree under `root` and collect every
     non-allow-listed violation as {:path <root-relative> :line <n>
     :match <s>}. Layout sanity (pkg absent) is a warning to *err*, NOT a
     violation (1:1 with the Python `find_violations`)."
     [root]
     (let [root-file (io/file root)
           pkg (io/file root-file package-root)]
       (if-not (.exists pkg)
         (do (binding [*out* *err*]
               (println (str "warning: " (.getPath pkg)
                             " not found (expected when running outside repo)")))
             [])
         (let [root-path (.getPath (.getAbsoluteFile root-file))]
           (vec
            (mapcat
             (fn [path]
               (let [text (try (slurp path)
                               (catch Exception _ nil))]
                 (when text
                   (map (fn [{:keys [line match]}]
                          (let [abs (.getPath (.getAbsoluteFile (io/file path)))
                                rel (if (str/starts-with? abs (str root-path "/"))
                                      (subs abs (inc (count root-path)))
                                      abs)]
                            {:path rel :line line :match match}))
                        (violation-matches text)))))
             (walk-files pkg))))))))

;; ── argv → opts (no eval) + exit-code contract ───────────────────

#?(:clj
   (defn parse-args
     "argparse → opts, pure + no eval. Supports `--root <path>` /
     `--root=<path>` (default: auto-detect = parents[3] of this script, i.e.
     the repo root four levels up from 70-tools/scripts/lint/). Unknown flags
     raise a closed-vocab ex-info."
     [argv default-root]
     (loop [opts {:root default-root}
            args (seq argv)]
       (if-not args
         opts
         (let [a (first args)]
           (cond
             (= a "--root")
             (if-let [v (second args)]
               (recur (assoc opts :root v) (nnext args))
               (throw (ex-info "--root requires a value"
                               {:lint/bad-args true :flag a})))

             (str/starts-with? a "--root=")
             (recur (assoc opts :root (subs a (count "--root="))) (next args))

             (or (= a "-h") (= a "--help"))
             (recur (assoc opts :help true) (next args))

             :else
             (throw (ex-info (str "unknown argument: " a)
                             {:lint/bad-args true :flag a}))))))))

#?(:clj
   (defn- default-root
     "Auto-detect the repo root the way the Python does
     (Path(__file__).resolve().parents[3]): four levels up from
     70-tools/scripts/lint/. Falls back to the process cwd if the script
     location is unknown."
     []
     (let [here (io/file *file*)]
       (if (.exists here)
         (loop [d (.getAbsoluteFile here) n 4]
           (if (zero? n)
             (.getPath d)
             (recur (.getParentFile d) (dec n))))
         (.getCanonicalPath (io/file "."))))))

#?(:clj
   (defn run
     "The exit-code contract as a pure-ish fn (I/O to *out*/*err* only).
     Returns 0 (clean) or 1 (violation). Mirrors Python `main`."
     [argv]
     (let [{:keys [root help]} (parse-args argv (default-root))]
       (if help
         (do (println "usage: verify_no_modal_labs_calls [--root <path>]")
             0)
         (let [findings (find-violations root)]
           (if (empty? findings)
             (do (println (str "no-modal-labs-calls gate: clean (kotoba_murakumo runtime "
                               "source does not reference modal.com / api.modal.com / modal import)"))
                 0)
             (do (binding [*out* *err*]
                   (println (str "ADR-2605282000 N1 violation: kotoba_murakumo source references "
                                 "Modal Labs (forbidden per Murakumo-only invariant ADR-2605215000):"))
                   (doseq [{:keys [path line match]} findings]
                     (println (str "  " path ":" line ": " (pr-str match)))))
                 1)))))))

#?(:clj
   (defn -main
     "CLI entry — exits with the gate's code (0 clean / 1 violation)."
     [& argv]
     (let [code (try (run argv)
                     (catch clojure.lang.ExceptionInfo e
                       (binding [*out* *err*] (println (ex-message e)))
                       2))]
       (flush)
       (System/exit code))))
