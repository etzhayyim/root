(ns hinagata.methods.validate
  "hinagata 雛形 — legal-template-commons integrity validator.
  1:1 Clojure port of `methods/validate.py` (ADR-2606111954).

  Maturity tooling: checks the kotoba-EDN graph's internal integrity beyond what the analyzer
  needs to run — referential integrity, statute grounding, template completeness, clause usage,
  and translation consistency. ERRORS are structural defects that must be fixed; WARNINGS are
  honestly-surfaced soft issues (e.g. a registered-but-unused statute) that are allowed but
  worth seeing (G5 sourcing honesty).

  House style: ':…' strings stay strings; pure fns; file I/O only behind #?(:clj …). Requires
  the good analyze.cljc sibling for the loader at the CLI edge. Python `__main__` writer is
  behind #?(:clj …)."
  (:require [clojure.string :as str]
            [clojure.set]))

(def ^:private sign-clause "cl.signature-esign")
(def ^:private cite-kinds #{":cites-statute" ":mandated-by"})

(defn validate
  "Return [errors warnings] — each a vector of strings. Faithful 1:1 port of validate.py."
  [nodes edges]
  (let [by-kind (reduce (fn [m [_nid n]]
                          (update m (get n ":lt/kind") (fnil conj #{}) (get n ":lt/id")))
                        {} nodes)
        templates (get by-kind ":template" #{})
        clauses (get by-kind ":clause" #{})
        statutes (get by-kind ":statute" #{})
        jurisdictions (get by-kind ":jurisdiction" #{})
        concepts (get by-kind ":concept" #{})
        errors (transient [])
        warnings (transient [])
        E (fn [m] (conj! errors m))
        W (fn [m] (conj! warnings m))
        kind-of (fn [id] (get-in nodes [id ":lt/kind"]))]

    ;; 1. referential integrity — no dangling 縁
    (doseq [e edges]
      (when-not (contains? nodes (get e ":en/from"))
        (E (str "dangling :en/from " (get e ":en/from") " (" (get e ":en/kind") ")")))
      (when-not (contains? nodes (get e ":en/to"))
        (E (str "dangling :en/to " (get e ":en/to") " (" (get e ":en/kind") ")"))))

    ;; 2. statute → jurisdiction referential integrity
    (doseq [sid statutes]
      (let [jx (get-in nodes [sid ":statute/jurisdiction"])]
        (when (and jx (not (contains? jurisdictions jx)))
          (E (str "statute " sid " :statute/jurisdiction " jx " is not a jurisdiction node")))
        (when-not (str/starts-with? (str (get-in nodes [sid ":statute/url"] "")) "http")
          (E (str "statute " sid " has no public :statute/url")))))

    ;; 3. edge-target kind sanity
    (doseq [e edges]
      (let [k (get e ":en/kind")
            to-kind (kind-of (get e ":en/to"))
            from-kind (kind-of (get e ":en/from"))]
        (when (and (contains? cite-kinds k) (not= to-kind ":statute"))
          (E (str k " target " (get e ":en/to") " is " to-kind ", expected :statute")))
        (when (and (= k ":instantiates") (not= to-kind ":concept"))
          (E (str ":instantiates target " (get e ":en/to") " is " to-kind ", expected :concept")))
        (when (and (contains? #{":governed-by" ":applies-in"} k) (not= to-kind ":jurisdiction"))
          (E (str k " target " (get e ":en/to") " is " to-kind ", expected :jurisdiction")))
        (when (and (= k ":translates") (not= to-kind ":template"))
          (E (str ":translates target " (get e ":en/to") " is " to-kind ", expected :template")))
        (when (and (= k ":conflicts-with") (not (and (= from-kind ":clause") (= to-kind ":clause"))))
          (E (str ":conflicts-with must be clause↔clause, got " from-kind "→" to-kind " (" (get e ":en/from") ")")))
        (when (and (= k ":derived-from") (not (and (= from-kind ":template") (= to-kind ":template"))))
          (E (str ":derived-from must be template→template, got " from-kind "→" to-kind " (" (get e ":en/from") ")")))
        (when (and (= k ":supersedes") (not (and (= from-kind ":template") (= to-kind ":template"))))
          (E (str ":supersedes must be template→template, got " from-kind "→" to-kind " (" (get e ":en/from") ")")))
        (when (and (= k ":conflicts-with") (= (get e ":en/from") (get e ":en/to")))
          (E (str ":conflicts-with self-loop on " (get e ":en/from"))))))

    ;; 4. template completeness — clauses, a governing jurisdiction, a signature clause
    (let [has-clause (reduce (fn [m e]
                               (if (= ":has-clause" (get e ":en/kind"))
                                 (update m (get e ":en/from") (fnil conj #{}) (get e ":en/to"))
                                 m))
                             {} edges)
          governed (set (for [e edges :when (= ":governed-by" (get e ":en/kind"))] (get e ":en/from")))]
      (doseq [tid templates]
        (let [cls (get has-clause tid #{})]
          (when (empty? cls) (E (str "template " tid " has no clauses")))
          (when-not (contains? governed tid) (E (str "template " tid " has no :governed-by jurisdiction")))
          (when-not (contains? cls sign-clause)
            (W (str "template " tid " has no signature clause (" sign-clause ")")))))

      ;; 5. clause usage — every clause used by ≥1 template and instantiating ≥1 concept
      (let [used-clauses (reduce into #{} (vals has-clause))
            instantiated (set (for [e edges :when (= ":instantiates" (get e ":en/kind"))] (get e ":en/from")))]
        (doseq [cid clauses]
          (when-not (contains? used-clauses cid) (W (str "clause " cid " is not used by any template")))
          (when (and (not (contains? instantiated cid)) (not= cid "cl.definitions"))
            (W (str "clause " cid " does not :instantiate any concept")))))

      ;; 6. statute grounding — every statute cited by ≥1 clause/template (else registry-only)
      (let [cited (set (for [e edges :when (contains? cite-kinds (get e ":en/kind"))] (get e ":en/to")))]
        (doseq [sid statutes]
          (when-not (contains? cited sid)
            (W (str "statute " sid " is registered but not cited by any clause (registry-only)")))))

      ;; 7. translation consistency — a translation's clause-concepts ⊆ its original's
      (letfn [(concepts-of [tid]
                (set (for [cl (get has-clause tid #{})
                           e edges
                           :when (and (= ":instantiates" (get e ":en/kind")) (= cl (get e ":en/from")))]
                       (get e ":en/to"))))]
        (doseq [e edges :when (= ":translates" (get e ":en/kind"))]
          (let [tr (get e ":en/from") orig (get e ":en/to")
                extra (clojure.set/difference (concepts-of tr) (concepts-of orig))]
            (when (seq extra)
              (W (str "translation " tr " introduces concepts not in original " orig ": " (vec (sort extra))))))))

      ;; 8. concept usage — every concept instantiated by ≥1 clause
      (let [used-concepts (set (for [e edges :when (= ":instantiates" (get e ":en/kind"))] (get e ":en/to")))]
        (doseq [cid concepts]
          (when-not (contains? used-concepts cid)
            (W (str "concept " cid " is not instantiated by any clause"))))))

    [(persistent! errors) (persistent! warnings)]))

#?(:clj
   (defn -main
     "CLI entry: validate a seed EDN graph → print report, exit 1 on any ERROR."
     [& argv]
     (let [analyze (requiring-resolve 'hinagata.methods.analyze/load-file*)
           argv (vec argv)
           here (-> *file* clojure.java.io/file .getParentFile .getParentFile)
           seed (if (and (seq argv) (not (str/starts-with? (first argv) "--")))
                  (clojure.java.io/file (first argv))
                  (clojure.java.io/file here "data" "seed-legal-template-graph.kotoba.edn"))
           {:keys [nodes edges]} (analyze seed)
           [errors warnings] (validate nodes edges)]
       (println (str "hinagata validate: " (count nodes) " nodes, " (count edges) " 縁 — "
                     (count errors) " errors, " (count warnings) " warnings"))
       (doseq [m errors] (println (str "  ERROR  " m)))
       (doseq [m warnings] (println (str "  warn   " m)))
       (if (seq errors) 1 0))))
