;; etzhayyim.kosei — Structural compliance analysis (cljc port, wave 6c).
;;
;; Pure-logic port of the REMAINING logic from
;; 70-tools/etzhayyim-py/src/etzhayyim/kosei.py
;; that was NOT already covered by etzhayyim.kosei-tiers (wave 2).
;;
;; etzhayyim.kosei-tiers (wave 2) already covers:
;;   tier-eta / tier-order / default-tier / valid-tier? / tier-eta-of
;;   suggest-tier / tier-index / next-tier / prev-tier
;; → This namespace REQUIRES kosei-tiers and reuses all of those.
;;
;; NEW pure logic ported here:
;;   Data record constructors + accessors:
;;     make-violation       — KoseiViolation record map
;;     violation->dict      — {:rule :severity :path :detail} serialization
;;     make-app-result      — KoseiAppResult record map
;;     app-result-ok?       — ok property (no missing files, no error violations)
;;     app-result->dict     — dict serialization
;;     make-report          — KoseiReport record map
;;     compliance-pct       — ok_apps / max(total_apps,1) * 100
;;     report->dict         — dict serialization
;;
;;   Pure text transforms:
;;     strip-jsonc-comments — pure JSONC comment stripper (char-by-char)
;;     norm-line            — lowercase + strip markdown markers + collapse spaces
;;
;;   Pure scan-app-stack helpers (pure portions only):
;;     detect-language      — infer language from file-presence flags map
;;     detect-npm-features  — feature flags from dep-string
;;     system-eta           — system η from tier-count map
;;     tier-distribution    — {:T1 n :T2 n :T3 n :unassigned n :total n :system-eta …}
;;
;; IO legs (scan_kosei, _check_app, _scan_app_stack, CLI commands, duckdb,
;;          config.json r/w, history) are NOT ported here — operator-gated.
;;
;; bb usage (classpath 70-tools/src):
;;   (require '[etzhayyim.kosei :as ko]
;;            '[etzhayyim.kosei-tiers :as kt])
;;   (ko/compliance-pct 8 10)       ;=> 80.0
;;   (ko/app-result-ok? {:missing-files [] :violations []}) ;=> true
;;   (ko/system-eta {:T1 2 :T2 3 :T3 1}) ;=> ~0.6328...

(ns etzhayyim.kosei
  (:require [clojure.string :as str]
            [etzhayyim.kosei-tiers :as kt]))

;; ── constants ─────────────────────────────────────────────────────────────────

(def required-files
  "Files required to be present in a compliant app directory."
  ["kotodama.jsonld" "src/app.ts" "wrangler.jsonc"])

(def skip-dirs
  "Directory names to skip during scanning."
  #{"node_modules" ".git" "__pycache__" ".venv" "dist" "build"})

;; ── data record constructors ──────────────────────────────────────────────────

(defn make-violation
  "Construct a KoseiViolation map.
   rule     — violation rule name string
   severity — \"error\" or \"warning\"
   path     — relative file path string
   detail   — optional detail string (default \"\")"
  ([rule severity path]
   (make-violation rule severity path ""))
  ([rule severity path detail]
   {:rule rule :severity severity :path path :detail detail}))

(defn violation->dict
  "Serialize a violation map to a plain string-keyed map (JSON-ready)."
  [v]
  {"rule"     (:rule v "")
   "severity" (:severity v "")
   "path"     (:path v "")
   "detail"   (:detail v "")})

(defn make-app-result
  "Construct a KoseiAppResult map.
   app-dir        — relative directory string
   missing-files  — seq of missing required file names (default [])
   violations     — seq of violation maps (default [])"
  ([app-dir]
   (make-app-result app-dir [] []))
  ([app-dir missing-files violations]
   {:app-dir       app-dir
    :missing-files (vec missing-files)
    :violations    (vec violations)}))

(defn app-result-ok?
  "Return true if the app-result has no missing files and no error violations.
   Mirrors Python KoseiAppResult.ok property."
  [result]
  (and (empty? (:missing-files result))
       (not (some #(= "error" (:severity %)) (:violations result)))))

(defn app-result->dict
  "Serialize an app-result map to a plain string-keyed map (JSON-ready)."
  [result]
  {"app_dir"       (:app-dir result "")
   "ok"            (app-result-ok? result)
   "missing_files" (vec (:missing-files result []))
   "violations"    (mapv violation->dict (:violations result []))})

(defn make-report
  "Construct a KoseiReport map.
   evaluated-at        — ISO-8601 timestamp string
   total-apps          — integer
   ok-apps             — integer
   results             — seq of app-result maps
   global-violations   — seq of violation maps (default [])"
  ([evaluated-at total-apps ok-apps results]
   (make-report evaluated-at total-apps ok-apps results []))
  ([evaluated-at total-apps ok-apps results global-violations]
   {:evaluated-at      evaluated-at
    :total-apps        total-apps
    :ok-apps           ok-apps
    :results           (vec results)
    :global-violations (vec global-violations)}))

(defn compliance-pct
  "Compute compliance percentage: ok-apps / max(total-apps,1) * 100.
   Mirrors Python KoseiReport.compliance_pct property."
  [ok-apps total-apps]
  (* (/ (double ok-apps) (max total-apps 1)) 100.0))

(defn report->dict
  "Serialize a report map to a plain string-keyed map (JSON-ready)."
  [report]
  (let [pct (compliance-pct (:ok-apps report 0) (:total-apps report 0))]
    {"evaluated_at"      (:evaluated-at report "")
     "total_apps"        (:total-apps report 0)
     "ok_apps"           (:ok-apps report 0)
     "compliance_pct"    (let [scale 10.0]
                           (/ (Math/rint (* pct scale)) scale))
     "results"           (mapv app-result->dict (:results report []))
     "global_violations" (mapv violation->dict (:global-violations report []))}))

;; ── pure text helpers ─────────────────────────────────────────────────────────

(defn strip-jsonc-comments
  "Strip // line comments and /* block comments */ from JSONC text.
   Pure char-by-char state machine — no IO.
   Mirrors Python _strip_jsonc_comments."
  [text]
  (let [n (count text)]
    (loop [i      0
           in-str false
           esc    false
           out    (transient [])]
      (if (>= i n)
        (str/join (persistent! out))
        (let [ch (.charAt text i)]
          (cond
            ;; escape character inside string
            esc
            (recur (inc i) in-str false (conj! out ch))

            ;; inside string
            in-str
            (cond
              (= ch \\)  (recur (inc i) true  false (conj! out ch))
              (= ch \")  (recur (inc i) false false (conj! out ch))
              :else       (recur (inc i) true  false (conj! out ch)))

            ;; start of string
            (= ch \")
            (recur (inc i) true false (conj! out ch))

            ;; potential comment start
            (and (= ch \/) (< (inc i) n))
            (let [nx (.charAt text (inc i))]
              (cond
                ;; line comment: skip to end of line (keep the newline itself)
                (= nx \/)
                (let [eol (or (str/index-of text "\n" i) n)]
                  (recur eol false false out))

                ;; block comment: skip to */
                (= nx \*)
                (let [end-idx (str/index-of text "*/" (+ i 2))]
                  (if end-idx
                    (recur (+ end-idx 2) false false out)
                    ;; unterminated block comment → consume rest
                    (recur n false false out)))

                :else
                (recur (inc i) false false (conj! out ch))))

            :else
            (recur (inc i) false false (conj! out ch))))))))

(defn norm-line
  "Normalize a documentation line: lowercase, strip markdown markers
   (**, *, backtick), collapse whitespace.
   Mirrors Python _norm_line."
  [s]
  (-> s
      str/lower-case
      str/trim
      (str/replace "**" "")
      (str/replace "*"  "")
      (str/replace "`"  "")
      (str/split #"\s+")
      (->> (str/join " "))))

;; ── pure stack-analysis helpers ───────────────────────────────────────────────

(defn detect-language
  "Infer the primary language of an app from a feature-presence map.
   Mirrors the language-detection block in Python _scan_app_stack.

   flags map keys (all boolean):
     :has-cargo  — Cargo.toml exists
     :has-go-mod — go.mod exists
     :has-python — pyproject.toml or requirements.txt exists

   Returns \"rust\" / \"go\" / \"python\" / \"typescript\"."
  [flags]
  (cond
    (:has-cargo  flags) "rust"
    (:has-go-mod flags) "go"
    (:has-python flags) "python"
    :else               "typescript"))

(defn detect-npm-features
  "Infer feature flags from a joined string of npm dependency names (lower-case).
   Returns a map of boolean feature flags.
   Mirrors the dep_str checks in Python _scan_app_stack."
  [dep-str]
  {:has-onnx   (str/includes? dep-str "onnx")
   :has-webgpu (or (str/includes? dep-str "webgpu")
                   (str/includes? dep-str "wgpu"))
   :has-fido2  (or (str/includes? dep-str "fido")
                   (str/includes? dep-str "webauthn"))
   :has-mcp    (or (str/includes? dep-str "@modelcontextprotocol")
                   (str/includes? dep-str "mcp-server"))
   :has-wasm   (str/includes? dep-str "wasm")})

(defn detect-cargo-features
  "Infer feature flags from a joined string of Cargo crate names (lower-case).
   Returns a map of boolean feature flags.
   Mirrors the crates/joined checks in Python _scan_app_stack."
  [joined]
  {:has-webgpu (str/includes? joined "wgpu")
   :has-onnx   (or (str/includes? joined "ort")
                   (str/includes? joined "onnx"))
   :has-fido2  (str/includes? joined "webauthn")})

;; ── pure tier statistics ──────────────────────────────────────────────────────

(defn system-eta
  "Compute system η (weighted average efficiency) from a tier-count map.
   tier-counts: {:T1 n :T2 n :T3 n}  (unassigned keys ignored)
   Mirrors the system_eta calculation in Python kosei_stats.

   Returns 0.0 when no apps are assigned to any tier."
  [tier-counts]
  (let [eta-sum      (reduce-kv (fn [acc tier n]
                                  (+ acc (* (kt/tier-eta-of (name tier)) (double n))))
                                0.0
                                (select-keys tier-counts [:T1 :T2 :T3]))
        assigned-n   (reduce + 0 (vals (select-keys tier-counts [:T1 :T2 :T3])))]
    (if (pos? assigned-n)
      (/ eta-sum assigned-n)
      0.0)))

(defn tier-distribution
  "Compute tier distribution statistics from a seq of tier strings (or nil).
   Elements that are nil, empty, or not in #{\"T1\" \"T2\" \"T3\"} count as unassigned.

   Returns a map:
     {:T1 n :T2 n :T3 n :unassigned n :total n :system-eta f}

   Mirrors the counts loop in Python kosei_stats."
  [tier-seq]
  (let [counts (reduce (fn [acc tier]
                         (if (kt/valid-tier? tier)
                           (update acc (keyword tier) inc)
                           (update acc :unassigned inc)))
                       {:T1 0 :T2 0 :T3 0 :unassigned 0}
                       tier-seq)
        total  (count tier-seq)
        eta    (system-eta counts)]
    (assoc counts
      :total     total
      :system-eta eta)))
