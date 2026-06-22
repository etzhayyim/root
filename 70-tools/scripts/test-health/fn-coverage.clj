#!/usr/bin/env bb
;; fn-coverage.clj — per-actor public-function test-coverage auditor for 20-actors/*/methods/.
;;
;; For every PUBLIC (defn, not defn-) function in an actor's methods/*.cljc, classify it by how it
;; is reached from tests:
;;
;;   tested     — a test_*.cljc in the actor mentions the function by name (directly exercised)
;;   internal   — no test names it, but another method fn calls it (likely exercised INDIRECTLY
;;                through a tested wrapper — lower priority)
;;   ISOLATED   — no test names it AND no sibling method fn calls it → the strongest candidate for
;;                a genuine coverage gap (this is exactly how suji #2169 / funamori #2175 /
;;                busshi #2179 / iryo #2185 were found)
;;
;; HONEST CAVEATS (this is a TRIAGE aid, not a verdict):
;;   - an ISOLATED fn may still be exercised by an integration test that builds it via data, or be
;;     a CLI entry point (-main / -report) that needs no unit test — VERIFY before adding a test;
;;   - name matching is textual (word-boundary-precise), so a fn only ever called dynamically
;;     (resolve / requiring-resolve) reads as ISOLATED.
;;
;; Run from repo root:
;;   bb 70-tools/scripts/test-health/fn-coverage.clj            # summary table, all actors
;;   bb 70-tools/scripts/test-health/fn-coverage.clj --isolated # + list every ISOLATED candidate
;;   bb 70-tools/scripts/test-health/fn-coverage.clj <actor>    # one actor, full per-fn breakdown
(require '[clojure.string :as str]
         '[babashka.fs :as fs])

(def actors-root "20-actors")

(defn- public-defns [path]
  (->> (str/split-lines (slurp (str path)))
       (keep #(second (re-find #"^\(defn ([a-z][a-zA-Z0-9*?!<>=+.-]*)" %)))
       (distinct)))

(defn- name-re [nm]
  (re-pattern (str "(?<![\\w-])" (java.util.regex.Pattern/quote nm) "(?![\\w-])")))

(defn- mentions? [text nm] (boolean (re-find (name-re nm) text)))
(defn- n-mentions [text nm] (count (re-seq (name-re nm) text)))

(defn- actor-names []
  (->> (fs/list-dir actors-root) (filter fs/directory?) (map fs/file-name) sort))

(defn- analyze [actor]
  (let [files (->> (fs/glob (str actors-root "/" actor) "**.cljc") (map str))
        test? #(str/starts-with? (fs/file-name %) "test_")
        method? #(and (str/includes? % "/methods/") (not (test? %)))
        method-files (filter method? files)
        test-text   (->> files (filter test?) (map slurp) (str/join "\n"))
        method-text (->> method-files (map slurp) (str/join "\n"))]
    (for [f method-files, nm (public-defns f)]
      (let [tested (mentions? test-text nm)]
        {:actor actor :file (fs/file-name f) :fn nm
         :class (cond tested :tested
                      (> (n-mentions method-text nm) 1) :internal
                      :else :isolated)}))))

(let [args (set *command-line-args*)
      one-actor (first (remove #(str/starts-with? % "--") *command-line-args*))
      actors (if one-actor [one-actor] (actor-names))
      rows (mapcat analyze actors)
      by-actor (group-by :actor rows)]
  (println "fn-coverage — public methods/ functions by how tests reach them")
  (println "  tested / internal(indirect) / ISOLATED(gap candidate). Triage aid — verify before testing.\n")
  (if one-actor
    (do
      (println (format "%-32s %s" (str one-actor "/<fn>") "class"))
      (doseq [r (sort-by (juxt :class :file :fn) (by-actor one-actor))]
        (println (format "  %-30s %s" (str (:file r) "/" (:fn r)) (name (:class r))))))
    (do
      (println (format "%-24s %7s %9s %9s" "actor" "tested" "internal" "ISOLATED"))
      (doseq [a (sort-by (fn [a] (- (count (filter #(= :isolated (:class %)) (by-actor a))))) actors)]
        (let [rs (by-actor a)
              c #(count (filter (fn [r] (= % (:class r))) rs))]
          (when (seq rs)
            (println (format "%-24s %7d %9d %9d" a (c :tested) (c :internal) (c :isolated))))))
      (let [iso (filter #(= :isolated (:class %)) rows)]
        (println (format "\nTOTAL ISOLATED candidates: %d across %d actors"
                         (count iso) (count (distinct (map :actor iso)))))
        (when (args "--isolated")
          (println "\n=== ISOLATED candidates (verify, then test) ===")
          (doseq [r (sort-by (juxt :actor :file :fn) iso)]
            (println (format "  %s/%s/%s" (:actor r) (:file r) (:fn r)))))))))
