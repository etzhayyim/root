;; etzhayyim.identifier-audit — Identifier consistency audit (cljc port, wave 1).
;;
;; Pure-logic port of 70-tools/etzhayyim-py/src/etzhayyim/identifier_audit.py
;; (no network I/O, no subprocess, no click — just regex + file-scan logic).
;;
;; Checks:
;;   nanoid-format    — kotodama.jsonld "nanoid" must be 8-12 chars [A-Za-z0-9_-]
;;   did-format       — "did" must start with did:plc|web|key|pkh
;;   name-lowercase   — actor "name" should be kebab-case (no UPPER / underscore)
;;
;; API (ClojureScript-compatible, no java.* APIs):
;;   (audit-jsonld-data  m rel-path)  → seq of violation maps
;;   (run-audit          files)       → seq of violation maps  (files = seq of {:path p :content s})
;;   (violations->report violations) → {:total N :by-rule {...}}
;;
;; CLJC portability note:
;;   The pure logic (regex matching, map transformations) is CLJC.
;;   JSON parsing uses #?(:clj .../:cljs ...) reader conditionals so the ns
;;   loads cleanly in both bb and ClojureScript hosts.
;;   Callers that pre-parse JSON to a Clojure map can pass :data directly —
;;   no JSON parsing occurs in that path.
;;
;; bb usage (classpath 70-tools/src):
;;   (require '[etzhayyim.identifier-audit :as ia])
;;   (ia/run-audit [{:path "kotodama.jsonld" :content (slurp "kotodama.jsonld")}])

(ns etzhayyim.identifier-audit
  (:require #?(:clj [cheshire.core :as json])
            [clojure.string :as str]))

;; ── regex patterns ──────────────────────────────────────────────────────────────

(def ^:private re-valid-nanoid #"^[A-Za-z0-9_-]{8,12}$")
(def ^:private re-valid-did    #"^did:(plc|web|key|pkh):[A-Za-z0-9._:\%-]+$")
(def ^:private re-name-bad     #"[A-Z_]")
;; Inline-nanoid in .ts / .svelte: "nanoid": "..."
(def ^:private re-ts-nanoid    #"\"nanoid\"\s*:\s*\"([^\"]+)\"")

;; ── data constructors ───────────────────────────────────────────────────────────

(defn- violation
  "Build a violation map (mirrors Python AuditViolation.to_dict())."
  [rule path value detail]
  {:rule rule :path path :value value :detail detail})

;; ── per-format auditors ─────────────────────────────────────────────────────────

(defn audit-jsonld-data
  "Audit a parsed kotodama.jsonld map (already JSON-decoded → Clojure map with
   string keys, as returned by cheshire or clojure.data.json).
   rel-path is used only for the violation :path field.
   Returns a vector of violation maps (empty when clean)."
  [data rel-path]
  (let [nanoid (get data "nanoid" "")
        did    (get data "did" "")
        name   (get data "name" "")]
    (cond-> []
      (and (seq nanoid)
           (not (re-matches re-valid-nanoid nanoid)))
      (conj (violation "nanoid-format" rel-path nanoid
                       "nanoid must be 8-12 chars [A-Za-z0-9_-]"))

      (and (seq did)
           (not (re-matches re-valid-did did)))
      (conj (violation "did-format" rel-path did
                       "unsupported DID method (expected plc/web/key/pkh)"))

      (and (seq name)
           (re-find re-name-bad name))
      (conj (violation "name-lowercase" rel-path name
                       "actor name should be kebab-case lowercase")))))

(defn- audit-ts-content
  "Scan TypeScript/Svelte source text for inline nanoid literals.
   Returns a vector of violation maps."
  [content rel-path]
  (->> (re-seq re-ts-nanoid content)
       (keep (fn [[_ nanoid]]
               (when (not (re-matches re-valid-nanoid nanoid))
                 (violation "nanoid-format" rel-path nanoid
                            "invalid nanoid format"))))
       vec))

;; ── JSON parsing (host-specific) ────────────────────────────────────────────────

(defn- parse-json
  "Best-effort JSON parse to Clojure map with string keys.
   Returns nil on failure. Only called when no :data is supplied."
  [content]
  (when (seq content)
    #?(:clj  (try
               (json/parse-string content)
               (catch Throwable _ nil))
       :cljs (try
               (js->clj (js/JSON.parse content))
               (catch js/Error _ nil)))))

;; ── main entry point ────────────────────────────────────────────────────────────

(defn run-audit
  "Audit a seq of {:path str :content str} maps (and optionally :data map for
   pre-parsed JSON). Returns a seq of violation maps (empty when clean).

   For kotodama.jsonld: pass :data (decoded JSON) OR :content (raw JSON string).
   For .ts/.svelte:     pass :content.
   Other extensions are ignored."
  [files]
  (mapcat
   (fn [{:keys [path content data]}]
     (let [basename (last (str/split path #"/"))
           ext      (last (str/split path #"\."))]
       (cond
         ;; kotodama.jsonld or any .jsonld
         (or (= basename "kotodama.jsonld")
             (str/ends-with? path ".jsonld"))
         (let [m (or data (parse-json content))]
           (if m
             (audit-jsonld-data m path)
             []))

         ;; .ts / .svelte — scan for inline nanoid literals
         (#{"ts" "svelte"} ext)
         (audit-ts-content (or content "") path)

         :else [])))
   files))

;; ── aggregate report ────────────────────────────────────────────────────────────

(defn violations->report
  "Summarize a seq of violation maps into:
   {:total N  :by-rule {\"nanoid-format\" N ...}  :violations [...]}"
  [violations]
  {:total      (count violations)
   :by-rule    (frequencies (map :rule violations))
   :violations (vec violations)})

;; ── rule registry (mirrors ia_rules in the Python port) ─────────────────────────

(def rules
  "Available audit rule names."
  ["nanoid-format" "did-format" "name-lowercase"])
