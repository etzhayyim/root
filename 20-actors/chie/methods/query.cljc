(ns chie.methods.query
  "chie 智慧 — knowledge-graph query interface over the AI-ecosystem graph (ADR-2606171200).

  Maturity / usability: the kotoba Datom EDN is a knowledge graph, not a flat list — this
  module exposes the practical observatory queries that prove it (the point of the Datalog
  substrate). All queries are pure graph traversals over the loaded {:nodes :edges}; nothing
  is stored, nothing mutates (N1). The 取-concentration queries reuse chie.methods.analyze so
  every answer is the same on-read integral the report uses — no second source of truth.

    node / label                  — a node map / its display label
    incident (id)                 — {:inbound :outbound} 縁 of a node
    funders-of (lab)              — :invests-in sources (capital) into a lab
    compute-suppliers-of (lab)    — :compute-deal sources (compute) into a lab
    governed-by (lab)             — :governs / :sets-standard sources (policy reach) over a node
    rounds-of (lab)               — :ai.invest/round nodes linked to a lab
    subsidiaries (parent)         — nodes that :organism/nests-in the parent
    concentration-in (axis)       — ranked accumulators on one axis (compute/capital/talent/policy)
    opening-worklist              — ranked :bond/opening-priority (who most needs OPENING)

  CONSTITUTIONAL: G1 — OPENING map, never a winner-rank; queries surface accumulation routed
  to opening, never a capability/forecast verdict (N3/G4). Persons only as public-role nodes."
  (:require [chie.methods.analyze :as analyze]))

(defn node [nodes id] (get nodes id))
(defn label [nodes id] (get-in nodes [id ":organism/label"] id))

(defn incident
  "All 縁 touching `id`, split by direction."
  [edges id]
  {:inbound  (filterv #(= id (get % ":en/to")) edges)
   :outbound (filterv #(= id (get % ":en/from")) edges)})

(defn- sources-by-kind
  "Source ids of edges of any kind in `kinds` whose :en/to = `dst`, sorted."
  [edges dst kinds]
  (sort (set (for [e edges
                   :when (and (contains? kinds (get e ":en/kind"))
                              (= dst (get e ":en/to")))]
               (get e ":en/from")))))

(defn funders-of          [edges lab] (sources-by-kind edges lab #{":invests-in"}))
(defn compute-suppliers-of [edges lab] (sources-by-kind edges lab #{":compute-deal"}))
(defn governed-by         [edges lab] (sources-by-kind edges lab #{":governs" ":sets-standard"}))

(defn rounds-of
  "Round nodes (:ai.invest/round) structurally linked to `lab` (round → lab :partners edge)."
  [nodes edges lab]
  (sort (set (for [e edges
                   :when (and (= ":partners" (get e ":en/kind"))
                              (= lab (get e ":en/to"))
                              (= ":ai.invest/round" (get-in nodes [(get e ":en/from") ":organism/kind"])))]
               (get e ":en/from")))))

(defn subsidiaries
  "Node ids that :organism/nests-in `parent`, sorted."
  [nodes parent]
  (sort (for [[nid n] nodes :when (= parent (get n ":organism/nests-in"))] nid)))

(defn concentration-in
  "Ranked [id label load] accumulators on one axis (reuses the analyze integral)."
  ([nodes edges axis] (concentration-in nodes edges axis 10))
  ([nodes edges axis limit]
   (let [res (analyze/analyze nodes edges)
         d (into {} (keep (fn [[nid m]] (when-let [v (get m axis)] [nid v]))
                          (:concentration res)))]
     (analyze/rank d nodes limit))))

(defn opening-worklist
  "Ranked [id label opening-priority] — the actionable 'who most needs OPENING' list."
  ([nodes edges] (opening-worklist nodes edges 10))
  ([nodes edges limit]
   (analyze/rank (:opening (analyze/analyze nodes edges)) nodes limit)))

#?(:clj
   (defn -main
     "CLI: a few example queries over the seed (file I/O at the edge)."
     [& argv]
     (let [here (-> *file* clojure.java.io/file .getParentFile .getParentFile)
           seed (clojure.java.io/file here "data" "seed-ai-ecosystem.kotoba.edn")
           {:keys [nodes edges]} (analyze/load-file* seed)
           lab (or (first argv) "ai.lab.openai")]
       (println (str "funders-of " lab ": " (funders-of edges lab)))
       (println (str "compute-suppliers-of " lab ": " (compute-suppliers-of edges lab)))
       (println (str "governed-by " lab ": " (governed-by edges lab)))
       (println (str "rounds-of " lab ": " (rounds-of nodes edges lab)))
       (println (str "opening-worklist (top 3): "
                     (mapv second (opening-worklist nodes edges 3))))
       0)))
