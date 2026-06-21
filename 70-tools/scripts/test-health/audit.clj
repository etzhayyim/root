#!/usr/bin/env bb
;; test-health/audit.clj — repo-wide actor test-suite HEALTH audit (read-only).
;;
;; Institutionalises the manual "measure the debt" scans that surfaced the py->cljc
;; port-wave debt (PRs #2041 tsumugi seed-drift, #2042 uchiwake .clj shadows, #2043
;; broken `bb test:<actor>` shims). Run anytime to re-measure:
;;
;;   bb 70-tools/scripts/test-health/audit.clj            # print the triage summary
;;   bb 70-tools/scripts/test-health/audit.clj --write    # + write the markdown snapshot
;;
;; Two debt classes, both deterministic + safe to compute (no test execution, no writes
;; unless --write):
;;   1. .clj/.cljc SHADOW pairs — a `foo.clj` next to `foo.cljc` resolves to the SAME ns;
;;      babashka prefers `.clj`, so a STALE `.clj` shadows the canonical `.cljc` port
;;      (the uchiwake bug). Classified :identical (harmless dup) vs :different (stale-risk).
;;   2. broken run_tests.sh SHIMS — `exec bb test:<name>` pointing at a bb task that no
;;      longer exists (removed when `test:actors` auto-discovery superseded per-actor lists).
;;
;; NON-prescriptive: a :different shadow is a CANDIDATE for cleanup, not an auto-fix —
;; which of .clj/.cljc is canonical is the actor owner's call (sizes/scope can diverge).
(ns test-health.audit
  (:require [clojure.string :as str]
            [clojure.java.io :as io]
            [babashka.fs :as fs]
            [babashka.process :as p]))

(def roots ["20-actors" "70-tools"])
(def report-path "70-tools/scripts/test-health/AUDIT.md")

;; ── 1. .clj/.cljc shadow pairs ───────────────────────────────────────────────

(defn shadow-pairs
  "Every foo.clj that has a sibling foo.cljc (same ns), classified by content equality."
  []
  (->> roots
       (mapcat #(fs/glob % "**.clj"))
       (map str)
       (keep (fn [clj]
               (let [cljc (str (subs clj 0 (count clj)) "c")] ; foo.clj -> foo.cljc
                 (when (fs/exists? cljc)
                   {:clj clj :cljc cljc
                    :class (if (= (slurp clj) (slurp cljc)) :identical :different)
                    :actor (second (str/split clj #"/"))}))))
       (sort-by :clj)
       vec))

;; ── 2. broken `bb test:<name>` shims ─────────────────────────────────────────

(defn defined-bb-tasks []
  (->> (slurp "bb.edn")
       (re-seq #"(?m)^\s+(test:[a-z-]+)")
       (map second)
       set))

(defn broken-shims
  "run_tests.sh files that `exec bb test:<name>` a task NOT defined in bb.edn."
  []
  (let [defined (defined-bb-tasks)]
    (->> (fs/glob "20-actors" "*/run_tests.sh")
         (map str)
         (keep (fn [sh]
                 ;; match the ACTUAL command (`exec bb test:<name>`), never a `bb test:<name>`
                 ;; mention inside a `#` comment (the #2043-fixed shims reference the old task
                 ;; name in their explanatory comment).
                 (when-let [task (some->> (slurp sh)
                                          str/split-lines
                                          (remove #(str/starts-with? (str/triml %) "#"))
                                          (some #(second (re-find #"\bexec bb (test:[a-z-]+)" %))))]
                   (when-not (contains? defined task)
                     {:run-tests sh :task task
                      :actor (second (str/split sh #"/"))}))))
         (sort-by :actor)
         vec)))

;; ── 2b. probe a broken shim: is it a clean repoint, or a deeper failure? ──────
;; Runs the actor's auto-discovered tests in an ISOLATED subprocess (a load error in
;; one actor must not abort the others). Classifies so the register says WHICH broken
;; shims are safe to repoint (#2043 pattern: green) vs surface a real pre-existing bug.

(defn probe-shim
  "Run `actor`'s discovery-filtered tests in a subprocess. Returns
  {:actor :status :detail} where :status ∈ {:clean-repoint :tests-fail :load-error}."
  [actor]
  (let [code (str "(require (quote etzhayyim.tools.discovery) (quote clojure.test) (quote clojure.string))"
                  "(let [all ((requiring-resolve (quote etzhayyim.tools.discovery/actor-test-nss)))"
                  "      mine (filter #(clojure.string/starts-with? (str %) \"" actor ".\") all)]"
                  "(apply require mine)"
                  "(let [r (apply clojure.test/run-tests mine)]"
                  "(println \"PROBE\" (:fail r) (:error r))))")
        {:keys [out err]} (p/sh {:continue true} "bb" "-e" code)
        text (str out err)
        ;; the subprocess prints `PROBE <fail> <error>` from run-tests; that is the source
        ;; of truth (NOT the bb exit code — the probe code does not System/exit on failures,
        ;; so a red suite still exits 0). Parse the counts; absence ⇒ load/require error.
        m (re-find #"PROBE (\d+) (\d+)" text)]
    (cond
      (and m (= "0" (nth m 1)) (= "0" (nth m 2)))
      {:actor actor :status :clean-repoint :detail "all tests pass once invocable"}
      m
      {:actor actor :status :tests-fail :detail (str (nth m 1) " fail / " (nth m 2) " error")}
      :else
      (let [msg (some->> (str/split-lines text)
                         (some #(second (re-find #"(?:Message:|Unable to resolve|No such file)\s*(.*)" %))))]
        {:actor actor :status :load-error :detail (or (some-> msg str/trim) "load/require error")}))))

(defn probe-shims [shims] (mapv (comp probe-shim :actor) shims))

;; ── report ───────────────────────────────────────────────────────────────────

(def ^:private probe-label
  {:clean-repoint "✅ clean-repoint (tests pass once invocable — safe #2043 fix)"
   :tests-fail    "❌ tests-fail (repoint surfaces a real pre-existing failure)"
   :load-error    "💥 load-error (a stale ns/symbol — deeper than the shim)"})

(defn render-md
  ([shadows shims] (render-md shadows shims nil))
  ([shadows shims probes]
  (let [diff (filter #(= :different (:class %)) shadows)
        same (filter #(= :identical (:class %)) shadows)
        by-actor (->> shadows (group-by :actor)
                      (map (fn [[a ps]] [a (count ps) (count (filter #(= :different (:class %)) ps))]))
                      (sort-by (comp - second)))]
    (str
     "# Repo test-health audit (py→cljc port-wave debt)\n\n"
     "_Generated by `70-tools/scripts/test-health/audit.clj` (read-only). Re-run to refresh._ "
     "Two deterministic debt classes from the py→clj/cljc port wave; this is the triage "
     "register for coordinated cleanup (PRs #2041/#2042/#2043 paid down the first slices).\n\n"
     "## 1. `.clj` / `.cljc` shadow pairs\n\n"
     "A `foo.clj` beside `foo.cljc` resolves to the SAME namespace; babashka prefers `.clj`, "
     "so a stale `.clj` shadows the canonical `.cljc` port (the uchiwake #2042 bug).\n\n"
     "- **" (count shadows) "** shadow pairs total · **" (count diff) "** `:different` "
     "(stale-risk, cleanup candidates) · **" (count same) "** `:identical` (harmless dup).\n\n"
     "| actor | shadow pairs | of which :different |\n|---|---|---|\n"
     (str/join "\n" (for [[a n d] by-actor] (str "| " a " | " n " | " d " |")))
     "\n\n## 2. Broken `bb test:<name>` shims\n\n"
     "`run_tests.sh` that `exec bb test:<name>` a task no longer in bb.edn (removed when "
     "`test:actors` auto-discovery superseded per-actor lists) → the suite never runs.\n\n"
     "- **" (count shims) "** broken shims.\n\n"
     (if (seq shims)
       (str "| actor | undefined task |"
            (when probes " probe (run via auto-discovery) |") "\n|---|---|"
            (when probes "---|") "\n"
            (let [pm (when probes (into {} (map (juxt :actor identity) probes)))]
              (str/join "\n" (for [s shims]
                               (str "| " (:actor s) " | `" (:task s) "` |"
                                    (when probes
                                      (let [pr (get pm (:actor s))]
                                        (str " " (probe-label (:status pr) (name (:status pr)))
                                             " — " (:detail pr) " |"))))))))
       "_(none — all repointed)_")
     (when probes
       (str "\n\n_Probe legend: **clean-repoint** = the actor's tests pass once invocable, so "
            "the run_tests.sh is a safe mechanical repoint (the #2043 pattern). **tests-fail** / "
            "**load-error** = repointing surfaces a real pre-existing failure (a stale test, or a "
            "stale `.clj` shadow whose symbol the `.cljc` lacks — e.g. `analyze/report`) that needs "
            "per-actor, owner-aware investigation. Truth source = the `PROBE` test counts, not the "
            "subprocess exit code._"))
     "\n\n## Cleanup guidance\n\n"
     "- A `:different` shadow is a CANDIDATE, not an auto-fix: which of `.clj`/`.cljc` is "
     "canonical is the actor owner's call (the uchiwake fix removed `.clj` only after the "
     "`.cljc` port proved complete via a green suite). Verify per-actor: remove the stale "
     "side, run the suite, keep only if green.\n"
     "- A broken shim is a safe mechanical fix IF the actor's tests pass once invocable "
     "(repoint to the auto-discovery filter, the #2043 pattern); else it surfaces a real "
     "pre-existing failure to triage separately.\n"))))

(defn self-check
  "Structural invariants over the scan (a self-test that doesn't depend on exact repo
  counts, which drift). Returns a vector of violation strings (empty = healthy detector)."
  [shadows shims defined]
  (cond-> []
    (not (vector? shadows)) (conj "shadow-pairs did not return a vector")
    (not (every? #(and (:clj %) (:cljc %) (#{:identical :different} (:class %)) (:actor %)) shadows))
    (conj "a shadow pair is missing :clj/:cljc/:class/:actor")
    (not (every? #(and (:actor %) (:task %) (str/starts-with? (:task %) "test:")) shims))
    (conj "a broken shim is missing :actor/:task")
    (not (contains? defined "test:actors")) (conj "bb.edn lost the canonical test:actors task")
    ;; a flagged shim's task must genuinely be undefined (the detector's core claim)
    (some #(contains? defined (:task %)) shims) (conj "a 'broken' shim's task is actually defined")))

(defn -main [& args]
  (let [shadows (shadow-pairs)
        shims (broken-shims)
        defined (defined-bb-tasks)
        diff (count (filter #(= :different (:class %)) shadows))]
    (println (str "test-health: " (count shadows) " .clj/.cljc shadow pairs ("
                  diff " :different / " (- (count shadows) diff) " :identical) · "
                  (count shims) " broken bb-test shims"))
    (when (seq shims)
      (println (str "  broken shims: " (str/join " " (map :actor shims)))))
    (when (some #{"--check"} args)
      (let [v (self-check shadows shims defined)]
        (if (seq v)
          (do (println "SELF-CHECK FAILED:") (run! #(println " -" %) v) (System/exit 1))
          (println "self-check: ok"))))
    (let [probes (when (and (some #{"--probe"} args) (seq shims))
                   (println "  probing broken shims (running each actor's tests in isolation)…")
                   (let [ps (probe-shims shims)]
                     (doseq [p ps] (println (str "    " (:actor p) " → " (name (:status p))
                                                 " (" (:detail p) ")")))
                     ps))]
      (when (some #{"--write"} args)
        (spit report-path (render-md shadows shims probes))
        (println (str "wrote " report-path))))))

(when (= *file* (System/getProperty "babashka.file"))
  (apply -main *command-line-args*))
