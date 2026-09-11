(ns etzhayyim.actor-mesh
  "ADR-2606230001 — generalized 'root actor → kotoba mesh' pipeline.

  Given an actor name, gathers cljc cell entrypoints, runs static analysis for
  known compile blockers, generates a kotoba.app.edn mesh manifest, and writes it
  to orgs/etzhayyim/com-etzhayyim-<name>/kotoba.app.edn.

  Usage (bb task):
    bb actor:mesh <name> [--trigger on-http|on-kse|on-tick] [--dry-run] [--survey]

  kotoba-clj compile constraints (compile_str_with_prelude):
    - assoc is SINGLE key-value: (assoc m k v) — multi-pair must chain via ->
    - def = integer constants only (no strings/vectors/maps at top-level)
    - No JVM interop: .hashCode, Math/round, java.math.BigDecimal
    - No str/lower-case, str/trim, str/blank?, str/join, str/split,
      str/includes?, str/starts-with?
    - No throw, ex-info, pr-str, hex literals"
  #?(:clj (:require [clojure.string :as str]
                    [babashka.fs :as fs]
                    [clojure.pprint :refer [pprint]])
     :cljs (:require [clojure.string :as str]
                     [cljs.pprint :refer [pprint]])))

;; ── Compile blocker patterns ──────────────────────────────────────────────────

(def ^:private COMPILE-BLOCKERS
  ["Math/"
   ".hashCode"
   "java.math."
   "format \"%"
   "str/lower-case"
   "str/trim"
   "str/blank?"
   "str/join"
   "str/split"
   "str/includes?"
   "str/starts-with?"
   "throw"
   "ex-info"
   "pr-str"])

;; NOTE: (assoc m k1 v1 k2 v2) multi-pair causes a runtime arity error, not a text
;; pattern, so it is not detectable by string search. Safe rewrite: chain single-pair
;; calls via ->: (-> m (assoc k1 v1) (assoc k2 v2)).

;; ── Static analysis ──────────────────────────────────────────────────────────

(defn assess-cell
  "Returns {:cell path :status :clean/:needs-rewrite :blockers [...found patterns...]}"
  [cell-path]
  #?(:clj
     (let [src   (slurp cell-path)
           found (filterv #(str/includes? src %) COMPILE-BLOCKERS)]
       {:cell     (str cell-path)
        :status   (if (empty? found) :clean :needs-rewrite)
        :blockers found})
     :cljs {:cell (str cell-path) :status :unknown :blockers []}))

;; ── Cell discovery ───────────────────────────────────────────────────────────

(defn find-cells
  "Returns paths (strings) to all cells/*/state_machine.cljc under actor-dir."
  [actor-dir]
  #?(:clj
     (->> (fs/glob actor-dir "cells/*/state_machine.cljc")
          (map str)
          sort
          vec)
     :cljs []))

(defn cell-name-from-path
  "cells/intake_qa/state_machine.cljc → intake-qa"
  [cell-path]
  (-> (str cell-path)
      (str/replace #".*cells/" "")
      (str/replace "/state_machine.cljc" "")
      (str/replace "_" "-")))

;; ── App manifest generation ───────────────────────────────────────────────────

(defn trigger-spec
  "Returns the TriggerSpec map based on trigger keyword."
  [trigger actor-name cell-name]
  (case trigger
    :on-http {:type :http :route (str "/" actor-name "/" cell-name)}
    :on-kse  {:type :kse  :topic (str "etzhayyim/actor/" actor-name)}
    :on-tick {:type :cron :schedule "0 * * * *"}
    {:type :http :route (str "/" actor-name "/" cell-name)}))

(defn component-spec
  "Builds a ComponentSpec map for one cell path."
  [actor-name cell-path trigger actor-dir]
  (let [cell-name (cell-name-from-path cell-path)
        comp-name (str actor-name "-" cell-name)
        ;; relative src from actor dir
        src-rel   (str/replace (str cell-path)
                               (str actor-dir "/") "")]
    {:name     comp-name
     :src      src-rel
     :scale    1
     :triggers [(trigger-spec trigger actor-name cell-name)]
     :requires #{:cap/kqe}}))

(defn generate-app-edn
  "Returns kotoba.app.edn EDN string for actor-name, using only the given clean-cells."
  [actor-name clean-cells trigger actor-dir]
  (let [components (mapv #(component-spec actor-name % trigger actor-dir) clean-cells)
        manifest   {:kotoba.app/name      actor-name
                    :kotoba.app/version   "0.1.0"
                    :kotoba.app/components components
                    :kotoba.app/placement  {:spread :zone :require {:tier "edge"}}}]
    (with-out-str (pprint manifest))))

;; ── Pipeline orchestration ────────────────────────────────────────────────────

(defn pipeline!
  "Run the full pipeline for actor-name. Returns a result map.
   opts: {:trigger :on-http|:on-kse|:on-tick  :dry-run false  :repo-root \".\"}"
  [actor-name {:keys [trigger dry-run repo-root]
               :or   {trigger   :on-http
                      dry-run   false
                      repo-root "."}}]
  #?(:clj
     (let [actor-dir   (str repo-root "/orgs/etzhayyim/com-etzhayyim-" actor-name)
           cells       (find-cells actor-dir)
           assessments (mapv assess-cell cells)
           clean       (filterv #(= :clean   (:status %)) assessments)
           blocked     (filterv #(= :needs-rewrite (:status %)) assessments)
           edn-str     (generate-app-edn actor-name
                                         (mapv :cell clean)
                                         trigger
                                         actor-dir)
           out-path    (str actor-dir "/kotoba.app.edn")]
       (println (str "\n=== actor:mesh " actor-name " ==="))
       (println (str "Cells found:     " (count cells)))
       (println (str "Clean:           " (count clean)))
       (println (str "Needs-rewrite:   " (count blocked)))
       (when (seq blocked)
         (println "Blocked cells:")
         (doseq [b blocked]
           (println (str "  BLOCKED " (cell-name-from-path (:cell b))
                         " — " (str/join ", " (:blockers b))))))
       (when (seq clean)
         (println "Clean cells:")
         (doseq [c clean]
           (println (str "  OK      " (cell-name-from-path (:cell c))))))
       (if (empty? clean)
         (do (println "\nNo clean cells — kotoba.app.edn not written.")
             {:actor actor-name :cells (count cells) :clean 0
              :blocked (count blocked) :written false})
         (if dry-run
           (do (println "\n[dry-run] Generated kotoba.app.edn:")
               (println edn-str)
               {:actor actor-name :cells (count cells) :clean (count clean)
                :blocked (count blocked) :written false})
           (do (spit out-path edn-str)
               (println (str "\nWrote: " out-path))
               {:actor actor-name :cells (count cells) :clean (count clean)
                :blocked (count blocked) :written true :path out-path}))))
     :cljs {:actor actor-name :cells 0 :written false}))

;; ── Survey mode ──────────────────────────────────────────────────────────────

(defn survey!
  "Print a mesh-readiness survey for all non-compat actors with cljc."
  [repo-root]
  #?(:clj
     (let [actors-dir (str repo-root "/20-actors")
           actor-dirs (->> (fs/list-dir actors-dir)
                           (filter fs/directory?)
                           (map #(str (fs/file-name %)))
                           (remove #(str/ends-with? % "-compat"))
                           sort)]
       (println "=== actor:mesh --survey ===")
       (println (format "%-30s %6s %6s %8s  %s"
                        "actor" "cljc" "cells" "bkrs" "status"))
       (println (apply str (repeat 65 "-")))
       (doseq [actor actor-dirs]
         (let [actor-dir  (str actors-dir "/" actor)
               cljc-files (fs/glob actor-dir "**.cljc")
               cljc-count (count cljc-files)
               cells      (find-cells actor-dir)
               assessments (mapv assess-cell cells)
               clean-cnt  (count (filter #(= :clean (:status %)) assessments))
               bad-cnt    (count (filter #(= :needs-rewrite (:status %)) assessments))
               blocker-lines
               (->> cljc-files
                    (mapcat #(let [src (slurp (str %))]
                               (filter (fn [line]
                                         (some (fn [b] (str/includes? line b)) COMPILE-BLOCKERS))
                                       (str/split-lines src))))
                    count)
               status (cond
                        (and (pos? (count cells)) (zero? bad-cnt)) :mesh-ready
                        (and (pos? (count cells)) (pos? clean-cnt)) :cells-clean
                        (pos? (count cells))                        :needs-rewrite
                        (pos? cljc-count)                           :no-cells
                        :else                                       :scaffold-only)]
           (when (pos? cljc-count)
             (println (format "%-30s %6d %6d %8d  %s"
                              actor cljc-count (count cells)
                              blocker-lines (name status))))))
       (println "\nDone."))
     :cljs nil))

;; ── CLI entrypoint ────────────────────────────────────────────────────────────

#?(:clj
   (defn -main [& args]
     (let [argv      (vec args)
           survey?   (boolean (some #{"--survey"} argv))
           dry-run?  (boolean (some #{"--dry-run"} argv))
           trigger   (or (some identity
                               (map #(when (str/starts-with? % "--trigger=")
                                       (second (str/split % #"=")))
                                    argv))
                         "on-http")
           actor     (first (remove #(str/starts-with? % "--") argv))
           repo-root (or (System/getenv "REPO_ROOT") ".")]
       (if survey?
         (survey! repo-root)
         (if actor
           (pipeline! actor {:trigger   (keyword trigger)
                             :dry-run   dry-run?
                             :repo-root repo-root})
           (do (println "Usage: bb actor:mesh <actor-name> [--trigger on-http|on-kse|on-tick] [--dry-run]")
               (println "       bb actor:mesh --survey")
               (System/exit 1)))))))
