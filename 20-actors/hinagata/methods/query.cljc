(ns hinagata.methods.query
  "hinagata 雛形 — knowledge-graph query interface over the legal-template commons.
  1:1 Clojure port of `methods/query.py` (ADR-2606111954).

  Maturity / usability: the kotoba Datom EDN is a knowledge graph, not just a flat list — this
  module exposes the practical drafter queries that prove it (the point of the kotoba Datalog
  substrate). All queries are PURE graph traversals over the loaded (nodes, edges); nothing is
  stored, nothing mutates (N1).

    templates-in-jurisdiction(jx)      — templates governed by a jurisdiction
    statutes-grounding-template(tmpl)  — every public statute a template rests on (clause→statute)
    translations-of(tmpl)              — its other-language versions (:translates, both directions)
    conflicting-clauses(clause)        — clauses a drafter must not combine with it (:conflicts-with)
    jurisdictions-for-concept(concept) — where a legal concept is grounded in real law
    coverage-gaps(concept)             — the inverse worklist over MAJOR-JURISDICTIONS

  House style: ':…' strings stay strings; pure fns; file I/O only behind #?(:clj …). Requires
  the good analyze.cljc sibling for the loader + CITE_KINDS. Python `__main__` CLI behind
  #?(:clj …)."
  (:require [clojure.string :as str]
            [hinagata.methods.analyze :as analyze]))

(def ^:private cite-kinds analyze/cite-kinds)   ;; mirrors analyze.CITE_KINDS

(defn- label
  "_label(nodes, nid): nodes.get(nid, {}).get(':lt/label', nid)."
  [nodes nid]
  (get-in nodes [nid ":lt/label"] nid))

(defn templates-in-jurisdiction
  [nodes edges jx]
  (->> edges
       (filter (fn [e] (and (= ":governed-by" (get e ":en/kind"))
                            (= jx (get e ":en/to"))
                            (= ":template" (get-in nodes [(get e ":en/from") ":lt/kind"])))))
       (map #(get % ":en/from"))
       set
       sort
       vec))

(defn statutes-grounding-template
  [_nodes edges tmpl]
  (let [clauses (set (for [e edges
                           :when (and (= ":has-clause" (get e ":en/kind"))
                                      (= tmpl (get e ":en/from")))]
                       (get e ":en/to")))]
    (->> edges
         (filter (fn [e] (and (contains? cite-kinds (get e ":en/kind"))
                              (contains? clauses (get e ":en/from")))))
         (map #(get % ":en/to"))
         set
         sort
         vec)))

(defn translations-of
  [_nodes edges tmpl]
  (let [out (transient #{})]
    (doseq [e edges :when (= ":translates" (get e ":en/kind"))]
      (cond
        (= tmpl (get e ":en/from")) (conj! out (get e ":en/to"))
        (= tmpl (get e ":en/to")) (conj! out (get e ":en/from"))))
    ;; siblings: other translations of the same original
    (let [originals (set (for [e edges
                               :when (and (= ":translates" (get e ":en/kind"))
                                          (= tmpl (get e ":en/from")))]
                           (get e ":en/to")))]
      (doseq [orig originals
              e edges
              :when (and (= ":translates" (get e ":en/kind"))
                         (= orig (get e ":en/to"))
                         (not= tmpl (get e ":en/from")))]
        (conj! out (get e ":en/from"))))
    (vec (sort (persistent! out)))))

(defn conflicting-clauses
  [_nodes edges clause]
  (let [out (transient #{})]
    (doseq [e edges :when (= ":conflicts-with" (get e ":en/kind"))]
      (cond
        (= clause (get e ":en/from")) (conj! out (get e ":en/to"))
        (= clause (get e ":en/to")) (conj! out (get e ":en/from"))))
    (vec (sort (persistent! out)))))

(defn jurisdictions-for-concept
  [nodes edges concept]
  ;; clauses that instantiate the concept → statutes they cite → those statutes' jurisdictions
  (let [clauses (set (for [e edges
                           :when (and (= ":instantiates" (get e ":en/kind"))
                                      (= concept (get e ":en/to")))]
                       (get e ":en/from")))
        jx (transient #{})]
    (doseq [e edges
            :when (and (contains? cite-kinds (get e ":en/kind"))
                       (contains? clauses (get e ":en/from")))]
      (let [j (get-in nodes [(get e ":en/to") ":statute/jurisdiction"])]
        (when j (conj! jx j))))
    (vec (sort (persistent! jx)))))

;; major national jurisdictions used as the gap-analysis denominator (exclude treaty/doctrinal ids)
(def major-jurisdictions
  ["jx.jp" "jx.us" "jx.eu" "jx.uk" "jx.de" "jx.fr" "jx.in" "jx.cn"
   "jx.kr" "jx.br" "jx.au" "jx.ca" "jx.es" "jx.sg" "jx.mx" "jx.id"
   "jx.ng" "jx.ae" "jx.it" "jx.ch" "jx.za" "jx.israel"])

(defn coverage-gaps
  "Major national jurisdictions that do NOT yet ground a concept — a self-documenting worklist.

  Turns the EDN into its own coverage roadmap: the inverse of jurisdictions-for-concept over the
  major-jurisdictions denominator (treaty / religious / customary ids are not counted as gaps)."
  [nodes edges concept]
  (let [have (set (jurisdictions-for-concept nodes edges concept))
        present (filter #(contains? nodes %) major-jurisdictions)]
    (vec (sort (filter #(not (contains? have %)) present)))))

;; ── CLI ─────────────────────────────────────────────────────────────────────
(def ^:private commands
  {"templates-in" ["templates_in_jurisdiction" "templates governed by"]
   "statutes-for" ["statutes_grounding_template" "statutes grounding"]
   "translations" ["translations_of" "translations of"]
   "conflicts" ["conflicting_clauses" "clauses conflicting with"]
   "jurisdictions-for" ["jurisdictions_for_concept" "jurisdictions grounding"]
   "gaps" ["coverage_gaps" "major jurisdictions still lacking grounding for"]})

(def ^:private dispatch
  {"templates_in_jurisdiction" templates-in-jurisdiction
   "statutes_grounding_template" statutes-grounding-template
   "translations_of" translations-of
   "conflicting_clauses" conflicting-clauses
   "jurisdictions_for_concept" jurisdictions-for-concept
   "coverage_gaps" coverage-gaps})

#?(:clj
   (defn -main
     "CLI entry: run a knowledge-graph query against the seed EDN graph (file I/O at the edge)."
     [& argv]
     (let [argv (vec (cons "query.clj" argv))   ;; argv[0] = program name, mirroring sys.argv
           here (-> *file* clojure.java.io/file .getParentFile .getParentFile)
           {:keys [nodes edges]} (analyze/load-file*
                                  (clojure.java.io/file here "data" "seed-legal-template-graph.kotoba.edn"))]
       (if (or (< (count argv) 3) (not (contains? commands (nth argv 1))))
         (do (binding [*out* *err*]
               (println (str "usage: query.py <" (str/join "|" (keys commands)) "> <id>")))
             2)
         (let [[fn-name verb] (get commands (nth argv 1))
               id (nth argv 2)
               res ((get dispatch fn-name) nodes edges id)]
           (println (str verb " " id " (" (label nodes id) "):"))
           (doseq [nid res]
             (println (str "  " nid "  —  " (label nodes nid))))
           (println (str "  [" (count res) " result(s)]"))
           0)))))
