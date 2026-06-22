;; etzhayyim.hinshitsu — Code quality analysis for the actor fleet (cljc port, wave 3b).
;;
;; Pure-logic port of 70-tools/etzhayyim-py/src/etzhayyim/hinshitsu.py
;; I/O-heavy legs (httpx health checks, fleet scan, ThreadPoolExecutor) are DEFERRED;
;; pure-logic functions (scoring, grading, fix suggestions, diff-snap) are fully ported.
;;
;; Deferred (IO):
;;   health-check   — requires HTTP network (httpx); operator-gated
;;   scan-workspace — requires filesystem walk; available only in #?(:clj ...)
;;
;; API (pure — platform-neutral):
;;   (score-actor   actor)        → [score issues]  (actor = string-keyed map)
;;   (grade         score)        → "S"|"A"|"B"|"C"|"D"
;;   (build-actor-report actor)   → report map {:nanoid :name :score :grade :issues :dir}
;;   (fix-suggestions issues)     → seq of suggestion strings
;;   (diff-snap dids scan-map score-map) → summary map
;;
;; API (IO — Clojure/bb only):
;;   (discover-actors ws-path)    → seq of actor maps
;;
;; bb usage (classpath 70-tools/src):
;;   (require '[etzhayyim.hinshitsu :as h])
;;   (h/grade 92)  ;; → "S"

(ns etzhayyim.hinshitsu
  (:require [clojure.string :as str]
            #?(:clj [cheshire.core :as json])))

;; ── scoring ───────────────────────────────────────────────────────────────────

(defn score-actor
  "Score a single actor map (decoded kotodama.jsonld + extra keys :dir).
   Returns [score issues-vec] where score ∈ [0..100].
   Mirrors Python _score_actor."
  [actor]
  (let [dir      (get actor "dir" "")
        issues   (atom [])
        score    (atom 100)]

    ;; Required files check — filesystem calls happen in caller (discover-actors).
    ;; Here we use pre-populated :has-files map if present, else skip per-file deduction.
    ;; Format: actor has optional key "existing_files" set of path strings.
    (let [existing (set (get actor "existing_files" []))]
      (when (seq existing)
        (doseq [req ["kotodama.jsonld" "src/app.ts" "wrangler.jsonc"]]
          (when-not (contains? existing req)
            (swap! issues conj (str "missing:" req))
            (swap! score - 20)))))

    ;; Missing fields
    (doseq [fld ["name" "did" "performerType" "description"]]
      (when (str/blank? (str (get actor fld "")))
        (swap! issues conj (str "missing_field:" fld))
        (swap! score - 5)))

    ;; Source content checks — use pre-populated "app_ts_content" key
    (let [src (str (get actor "app_ts_content" ""))]
      (when (seq src)
        (when (str/includes? src "\"nsid\"")
          (swap! issues conj "nsid_placeholder")
          (swap! score - 10))
        (when (re-find #"\"(?:claude-3|gpt-4|gemini-|llama-)[^\"]*\""
                       (str/lower-case src))
          (swap! issues conj "hardcoded_model")
          (swap! score - 10))))

    [(max 0 @score) @issues]))

(defn grade
  "Map a numeric score 0-100 to S/A/B/C/D.
   Mirrors Python _grade."
  [score]
  (cond
    (>= score 90) "S"
    (>= score 70) "A"
    (>= score 50) "B"
    (>= score 30) "C"
    :else         "D"))

(defn build-actor-report
  "Build a report map from an actor map. Pure; uses score-actor + grade."
  [actor]
  (let [[score issues] (score-actor actor)]
    {"nanoid" (get actor "nanoid" "")
     "name"   (get actor "name" "")
     "score"  score
     "grade"  (grade score)
     "issues" issues
     "dir"    (get actor "dir" "")}))

(defn fix-suggestions
  "Return a seq of human-readable fix suggestion strings for a seq of issue codes.
   Mirrors Python _fix_suggestions."
  [issues]
  (vec
   (for [issue issues]
     (cond
       (str/starts-with? issue "missing:")
       (str "Create " (subs issue (count "missing:")))

       (str/starts-with? issue "missing_field:")
       (str "Add '" (subs issue (count "missing_field:")) "' field to kotodama.jsonld")

       (= issue "nsid_placeholder")
       "Replace \"nsid\" placeholder with proper NSID (com.etzhayyim.apps.<actor>.<method>)"

       (= issue "hardcoded_model")
       "Replace hardcoded model name with resolveModelId() / MURAKUMO_DEFAULT_MODEL"

       :else (str "Fix: " issue)))))

;; ── diff-snap (pure) ─────────────────────────────────────────────────────────

(defn- coerce-bool [v]
  (boolean (or v false)))

(defn diff-snap
  "Compute a before/after comparison snapshot from lists of DIDs and two report maps.
   Mirrors Python _diff_snap.
   dids      = seq of DID strings
   scan-map  = {did → scan-result-map}
   score-map = {did → score-result-map}"
  [dids scan-map score-map]
  (let [dids (vec dids)]
    {:scan-count  (count (filter #(contains? scan-map %) dids))
     :score-count (count (filter #(contains? score-map %) dids))
     :did-doc-reachable
     (count (filter (fn [d]
                      (let [m (get scan-map d {})]
                        (coerce-bool (or (get m "did_doc_reachable")
                                         (get m "DidDocReachable")))))
                    dids))
     :atproto-reachable
     (count (filter (fn [d]
                      (let [m (get scan-map d {})]
                        (coerce-bool (or (get m "atproto_did_reachable")
                                         (get m "AtprotoDidReachable")))))
                    dids))
     :with-posts
     (count (filter (fn [d]
                      (let [m (get scan-map d {})]
                        (coerce-bool (or (get m "with_posts")
                                         (get m "WithPosts")))))
                    dids))
     :avg-total-score
     (let [scores (vec (keep (fn [d]
                               (when-let [m (get score-map d)]
                                 (or (get m "total_score")
                                     (get m "TotalScore"))))
                             dids))]
       (if (seq scores)
         (/ (apply + scores) (double (count scores)))
         0.0))}))

(defn diff-delta
  "Compute the delta map between before-snap and after-snap (both from diff-snap)."
  [before after]
  {:scan-count         (- (:scan-count after)         (:scan-count before))
   :score-count        (- (:score-count after)        (:score-count before))
   :did-doc-reachable  (- (:did-doc-reachable after)  (:did-doc-reachable before))
   :atproto-reachable  (- (:atproto-reachable after)  (:atproto-reachable before))
   :with-posts         (- (:with-posts after)         (:with-posts before))
   :avg-total-score    (- (:avg-total-score after)    (:avg-total-score before))})

;; ── I/O edge (Clojure/bb only) ────────────────────────────────────────────────

#?(:clj
   (do
     (require '[babashka.fs :as fs])

     (defn- read-jsonld-safe [path]
       (try
         (json/parse-string (slurp path))
         (catch Exception _ {})))

     (defn- read-text-safe [path]
       (try (slurp path) (catch Exception _ "")))

     (defn discover-actors
       "Scan ws-path/20-actors (or whole ws if 20-actors absent) for kotodama.jsonld files.
       Returns a seq of actor maps enriched with existing_files and app_ts_content."
       [ws-path]
       (let [ws   (fs/file ws-path)
             base (let [b (fs/file ws "20-actors")]
                    (if (fs/exists? b) b ws))
             jsonld-files (filter #(str/ends-with? (str %) "kotodama.jsonld")
                                  (file-seq (fs/file base)))]
         (vec
          (for [p jsonld-files
                :let [data (read-jsonld-safe p)]
                :when (seq (get data "nanoid" ""))
                :let [dir      (.getParent (fs/file p))
                      req-files ["kotodama.jsonld" "src/app.ts" "wrangler.jsonc"]
                      existing  (set (filter #(fs/exists? (fs/file dir %)) req-files))
                      app-ts    (let [app-ts-path (fs/file dir "src" "app.ts")]
                                  (if (fs/exists? app-ts-path)
                                    (read-text-safe app-ts-path)
                                    ""))]]
            (merge data
                   {"dir"              dir
                    "manifest_path"    (str p)
                    "existing_files"   existing
                    "app_ts_content"   app-ts})))))))
