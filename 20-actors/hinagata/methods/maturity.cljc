(ns hinagata.methods.maturity
  "hinagata 雛形 — maturity dashboard generator (ADR-2606111954).
  1:1 Clojure port of `methods/maturity.py`.

  Rolls up every measured dimension of the legal-template commons — size, statute grounding,
  legal-system / language / per-jurisdiction breadth, integrity, and the eight globally-grounded
  core clauses — into a single MATURITY.md scorecard with an honest readiness assessment.

  SELF-CONTAINED: the Python module imports `validate.py` for the integrity gate; that sibling
  has no .cljc port, so its `validate(nodes, edges) -> (errors, warnings)` is INLINED here
  faithfully (1:1 with validate.py) rather than required, per the house no-sibling-stub rule.
  The analyze sibling (load-file*/CITE_KINDS) is required only at the #?(:clj) CLI edge.

  House style: ':…' strings stay strings; pure fns; file I/O only behind #?(:clj …). Python
  `__main__` writer is behind #?(:clj …)."
  (:require [clojure.string :as str]
            [clojure.set]))

(def cite-kinds #{":cites-statute" ":mandated-by"})   ;; mirrors analyze.CITE_KINDS

(def ^:private sign-clause "cl.signature-esign")

(def ^:private core-clauses
  ;; the eight cross-cutting clauses the commons aims to ground worldwide
  ["cl.signature-esign" "cl.data-subject-rights" "cl.warranty-conformity"
   "cl.employment-termination" "cl.lease-term-generic" "cl.ip-assignment"
   "cl.cooling-off" "cl.dispute-arbitration"])

;; ── inlined validate (1:1 with validate.py validate()) ──────────────────────
(defn validate
  "Return [errors warnings] — each a vector of strings. Faithful port of validate.py."
  [nodes edges]
  (let [by-kind (reduce (fn [m [nid n]]
                          (update m (get n ":lt/kind") (fnil conj #{}) nid))
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

    ;; 4. template completeness
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

      ;; 5. clause usage
      (let [used-clauses (reduce into #{} (vals has-clause))
            instantiated (set (for [e edges :when (= ":instantiates" (get e ":en/kind"))] (get e ":en/from")))]
        (doseq [cid clauses]
          (when-not (contains? used-clauses cid) (W (str "clause " cid " is not used by any template")))
          (when (and (not (contains? instantiated cid)) (not= cid "cl.definitions"))
            (W (str "clause " cid " does not :instantiate any concept")))))

      ;; 6. statute grounding
      (let [cited (set (for [e edges :when (contains? cite-kinds (get e ":en/kind"))] (get e ":en/to")))]
        (doseq [sid statutes]
          (when-not (contains? cited sid)
            (W (str "statute " sid " is registered but not cited by any clause (registry-only)")))))

      ;; 7. translation consistency
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

      ;; 8. concept usage
      (let [used-concepts (set (for [e edges :when (= ":instantiates" (get e ":en/kind"))] (get e ":en/to")))]
        (doseq [cid concepts]
          (when-not (contains? used-concepts cid)
            (W (str "concept " cid " is not instantiated by any clause"))))))

    [(persistent! errors) (persistent! warnings)]))

;; ── maturity scorecard ──────────────────────────────────────────────────────
(defn- by-kind [nodes kind]
  (filter #(= kind (get % ":lt/kind")) (vals nodes)))

(defn maturity
  "Port of maturity(nodes, edges) → MATURITY.md text."
  [nodes edges]
  (let [tmpls (by-kind nodes ":template")
        clauses (by-kind nodes ":clause")
        statutes (by-kind nodes ":statute")
        jurisdictions (by-kind nodes ":jurisdiction")
        concepts (by-kind nodes ":concept")
        [errors warnings] (validate nodes edges)
        langs (frequencies (map #(get % ":template/lang") tmpls))
        systems (set (map #(get % ":jurisdiction/system") jurisdictions))
        cited (set (for [e edges :when (contains? cite-kinds (get e ":en/kind"))] (get e ":en/to")))
        bound-clauses (set (for [e edges
                                 :when (and (contains? cite-kinds (get e ":en/kind"))
                                            (= ":clause" (get-in nodes [(get e ":en/from") ":lt/kind"])))]
                             (get e ":en/from")))
        translated (set (for [e edges :when (= ":translates" (get e ":en/kind"))] (get e ":en/from")))
        st-jx (into {} (map (fn [s] [(get s ":lt/id") (get s ":statute/jurisdiction")]) statutes))
        core-reach (into {}
                         (for [cl core-clauses]
                           (let [jx (set (for [e edges
                                               :when (and (contains? cite-kinds (get e ":en/kind"))
                                                          (= cl (get e ":en/from")))]
                                           (get st-jx (get e ":en/to"))))]
                             [cl (count (filter some? jx))])))
        L (transient [])
        P (fn [s] (conj! L s))]
    (P "# hinagata 雛形 — maturity scorecard\n")
    (P (str "> GENERATED by `methods/maturity.py` from the kotoba-EDN graph — do not hand-edit. "
            "ADR-2606111954.\n"))
    (P "## Size\n")
    (P "| dimension | count |")
    (P "|---|---:|")
    (P (str "| templates | " (count tmpls) " |"))
    (P (str "| clauses | " (count clauses) " |"))
    (P (str "| statutes | " (count statutes) " |"))
    (P (str "| jurisdictions | " (count jurisdictions) " |"))
    (P (str "| concepts | " (count concepts) " |"))
    (P (str "| 縁 (edges) | " (count edges) " |"))
    (P (str "| languages | " (count (filter some? (keys langs))) " |"))

    (P "\n## Quality gates\n")
    (P "| gate | status |")
    (P "|---|:--|")
    (P (str "| integrity (validate.py) | "
            (cond
              (and (empty? errors) (empty? warnings)) "✅ 0 errors / 0 warnings"
              (seq errors) (str "❌ " (count errors) " errors")
              :else (str "⚠ " (count warnings) " warnings"))
            " |"))
    (P (str "| clause statute-binding | " (count bound-clauses) "/" (count clauses) " bound |"))
    (P (str "| statute grounding | "
            (count (filter #(contains? cited (get % ":lt/id")) statutes)) "/" (count statutes) " cited |"))
    (P (str "| legal systems | " (count (filter some? systems)) "/6 represented |"))
    (P (str "| translation linkage | " (count translated) "/" (count tmpls) " templates linked |"))

    (P "\n## Core-clause worldwide grounding (the 8 most cross-cutting concerns)\n")
    (P "| clause | jurisdictions grounded |")
    (P "|---|---:|")
    (doseq [cl core-clauses]
      (let [label (get-in nodes [cl ":lt/label"] cl)]
        (P (str "| " label " | " (get core-reach cl 0) " |"))))

    (let [ok (and (empty? errors)
                  (= 6 (count (filter some? systems)))
                  (>= (count langs) 6)
                  (>= (count bound-clauses) (- (count clauses) 3)))]
      (P "\n## Readiness\n")
      (P (if ok
           (str "**R1 — mature**: clean integrity, all 6 legal systems, multilingual, core clauses "
                "globally grounded. Live legal-corpus binding + IPFS pin/IPNS remain G7-gated.")
           "**R0/R1 — in progress**: see gaps above.")))
    (P "\n---\n_hinagata 雛形 · ADR-2606111954 · generated maturity scorecard._\n")
    (str/join "\n" (persistent! L))))

#?(:clj
   (defn -main
     "CLI entry: write MATURITY.md from a seed EDN graph (file I/O at the edge)."
     [& argv]
     (let [argv (vec argv)
           load-file* (requiring-resolve 'hinagata.methods.analyze/load-file*)
           here (-> *file* clojure.java.io/file .getParentFile .getParentFile)
           seed (if (and (seq argv) (not (str/starts-with? (first argv) "--")))
                  (clojure.java.io/file (first argv))
                  (clojure.java.io/file here "data" "seed-legal-template-graph.kotoba.edn"))
           {:keys [nodes edges]} (load-file* seed)]
       (spit (clojure.java.io/file here "MATURITY.md") (maturity nodes edges))
       (println (str "hinagata maturity → " (clojure.java.io/file here "MATURITY.md")))
       0)))
