#!/usr/bin/env bb
;; fn-coverage.clj — per-actor public-function test-coverage auditor for flat west actor repositories.
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
         '[babashka.fs :as fs]
         '[babashka.classpath :refer [add-classpath]])

(def actors-root "orgs/etzhayyim")
(def actor-prefix "com-etzhayyim-")

;; Ground-truth which actors the canonical `bb test:actors` discovery runner actually executes:
;; some actors (ibuki / mimamori / yobel, and hyphenated-dir actors) are EXCLUDED from it and run
;; by their own dedicated bb task, so a gap closed with a new test_*.cljc there must be verified via
;; that task, not the discovery runner. We ask the real discovery rather than re-deriving its rules.
(def ^:private discovery-run?
  (try
    (add-classpath "70-tools/src:orgs/kotoba-lang/kotodama/src")
    (let [nss (set (map str ((requiring-resolve 'etzhayyim.tools.discovery/actor-test-nss))))]
      (fn [actor]
        (let [prefix (str (str/replace actor "_" "-") ".")]
          (boolean (some #(str/starts-with? % prefix) nss)))))
    (catch Throwable _ (constantly :unknown))))

(defn- public-defns [path]
  (->> (str/split-lines (slurp (str path)))
       (keep #(second (re-find #"^\(defn ([a-z][a-zA-Z0-9*?!<>=+.-]*)" %)))
       (distinct)))

(defn- name-re [nm]
  (re-pattern (str "(?<![\\w-])" (java.util.regex.Pattern/quote nm) "(?![\\w-])")))

(defn- mentions? [text nm] (boolean (re-find (name-re nm) text)))
(defn- n-mentions [text nm] (count (re-seq (name-re nm) text)))

(defn- actor-names []
  (->> (fs/list-dir actors-root)
       (filter fs/directory?)
       (map fs/file-name)
       (filter #(str/starts-with? % actor-prefix))
       (map #(subs % (count actor-prefix)))
       sort))

(defn- analyze [actor]
  (let [files (->> (fs/glob (str actors-root "/" actor-prefix actor) "**.cljc") (map str))
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
      by-actor (group-by :actor rows)
      ded? (fn [a] (false? (discovery-run? a)))]   ; has cljc tests but NOT in the discovery runner
  (println "fn-coverage — public methods/ functions by how tests reach them")
  (println "  tested / internal(indirect) / ISOLATED(gap candidate). Triage aid — verify before testing.")
  (println "  † = run by a DEDICATED bb task, not `bb test:actors` — verify a new test there.\n")
  (if one-actor
    (do
      (println (format "%-32s %s" (str one-actor (when (ded? one-actor) " †") "/<fn>") "class"))
      (doseq [r (sort-by (juxt :class :file :fn) (by-actor one-actor))]
        (println (format "  %-30s %s" (str (:file r) "/" (:fn r)) (name (:class r))))))
    (do
      (println (format "%-24s %7s %9s %9s" "actor" "tested" "internal" "ISOLATED"))
      (doseq [a (sort-by (fn [a] (- (count (filter #(= :isolated (:class %)) (by-actor a))))) actors)]
        (let [rs (by-actor a)
              c #(count (filter (fn [r] (= % (:class r))) rs))]
          (when (seq rs)
            (println (format "%-24s %7d %9d %9d" (str a (when (ded? a) " †")) (c :tested) (c :internal) (c :isolated))))))
      (let [iso (filter #(= :isolated (:class %)) rows)]
        (println (format "\nTOTAL ISOLATED candidates: %d across %d actors († = dedicated runner)"
                         (count iso) (count (distinct (map :actor iso)))))
        (when (args "--isolated")
          (println "\n=== ISOLATED candidates (verify, then test) ===")
          (doseq [r (sort-by (juxt :actor :file :fn) iso)]
            (println (format "  %s%s/%s/%s" (:actor r) (if (ded? (:actor r)) " †" "") (:file r) (:fn r)))))))))
