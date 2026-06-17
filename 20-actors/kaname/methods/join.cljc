(ns kaname.methods.join
  "kaname 要 — live mirror JOIN (ADR-2606172100 R1). The system-of-systems join leg: read a sibling
  mirror's ALREADY-PRODUCED kotoba Datom-log output and LIFT its 縁 into a kaname domain layer of
  the multiplex, then reconcile entities across layers by label. Running a mirror to (re)produce its
  output is the G7/Council-gated step; joining its committed output is what kaname does here.

  Demonstrated on chie 智慧's REAL output (20-actors/chie/out/ai-ecosystem-datoms.kotoba.edn): its
  AI-ecosystem 縁 (invests-in / compute-deal / talent-flow / governs / sets-standard / depends-on)
  become the :ai layer of kaname's graph; kaname then computes leverage natively over the lifted
  real subgraph. When TWO+ mirrors are joined, an entity present in several (reconcile-by-label)
  gains domains across layers — and THAT cross-domain spanning is what makes it the 要.

  G1/G4 preserved: lifted nodes are :sos/entity structural positions; person nodes are dropped
  (a mirror's public-ROLE nodes lift as roles, private profiles are never present upstream).
  Pure fns; reuses kaname.methods.sos. Portable .cljc."
  (:require [clojure.string :as str]
            [kaname.methods.sos :as sos]
            #?(:clj [clojure.java.io :as io])))

;; ── parse a [e a v tx op] Datom-log into {:nodes :edges} ───────────────────────

(defn datoms->graph
  "Reconstruct {:nodes {id node} :node-order [..] :edges [edge]} from a vector of [e a v tx op]
  datoms (op :add only; later wins). Entities whose id starts \"en.\" with :en/from become edges;
  entities with :organism/kind become nodes."
  [datoms]
  (let [by-e (reduce
              (fn [m d]
                (if (and (vector? d) (>= (count d) 5) (= ":add" (nth d 4)))
                  (let [[e a v] d]
                    (-> m
                        (update-in [:attrs e] (fnil assoc {}) a v)
                        (update :order (fn [o] (if (contains? (:attrs m) e) o (conj o e))))))
                  m))
              {:attrs {} :order []}
              datoms)
        attrs (:attrs by-e)]
    (reduce
     (fn [acc e]
       (let [m (get attrs e)]
         (cond
           (and (str/starts-with? e "en.") (contains? m ":en/from"))
           (update acc :edges conj (assoc m ":en/id" e))
           (contains? m ":organism/kind")
           (-> acc
               (assoc-in [:nodes e] (assoc m ":organism/id" e))
               (update :node-order conj e))
           :else acc)))
     {:nodes {} :node-order [] :edges []}
     (:order by-e))))

#?(:clj
   (defn read-datom-log
     "Read a mirror's Datom-log EDN file → {:nodes :node-order :edges}."
     [path]
     (datoms->graph (sos/read-edn (slurp (str path))))))

;; ── lift a mirror graph into a kaname domain layer ────────────────────────────

(def default-kind-map
  "Generic mirror 縁-kind → kaname kind. Accumulation/dependence/standard-setting map onto kaname
  vocabulary; reciprocal/structural kinds (:partners) drop (no axis)."
  {":compute-deal"  ":concentrates"   ":invests-in"   ":concentrates"
   ":talent-flow"   ":concentrates"   ":supplies"     ":concentrates"
   ":controls"      ":concentrates"   ":influences"   ":influences"
   ":governs"       ":gates"          ":sets-standard" ":gates"
   ":depends-on"    ":depends-on"     ":couples"      ":couples"})

(defn lift
  "Lift a mirror {:nodes :edges} into kaname forms (vector of node + edge maps) in `domain`,
  tagged `source-actor`. Node ids are namespaced \"<tag>/<id>\" so distinct mirrors never collide
  pre-reconcile. Person ROLE nodes are kept as :sos/role; everything else as :sos/entity.
  Edges with an unmapped kind are dropped (honest — no fabricated axis)."
  [{:keys [nodes node-order edges]} domain source-actor & [kind-map]]
  (let [km (merge default-kind-map kind-map)
        tag (str (if (str/starts-with? (str source-actor) ":") (subs source-actor 1) source-actor) "/")
        pfx (fn [id] (str tag id))
        role? (fn [n] (let [k (str (get n ":organism/kind"))]
                        (boolean (re-find #"(?i)role|person" k))))
        node-forms
        (mapv (fn [id]
                (let [n (get nodes id)
                      open? (let [o (get n ":ai/open?")] (true? o))]
                  (cond-> {":organism/id"   (pfx id)
                           ":organism/kind" (if (role? n) ":sos/role" ":sos/entity")
                           ":organism/label" (get n ":organism/label" id)
                           ":organism/sourcing" ":representative"
                           ":sos/source-actors" [source-actor]
                           ":sos/open?"     open?}
                    (get n ":sos/role") (assoc ":sos/role" (get n ":sos/role")))))
              (or (seq node-order) (keys nodes)))
        edge-forms
        (->> edges
             (keep (fn [e]
                     (when-let [k (get km (get e ":en/kind"))]
                       (let [l (get e ":en/grasping-load")]
                         {":en/from" (pfx (get e ":en/from"))
                          ":en/to"   (pfx (get e ":en/to"))
                          ":en/kind" k
                          ":en/domain" domain
                          ":en/grasping-load" (if (number? l) (double l) 0.0)
                          ":en/sourcing" ":representative"}))))
             vec)]
    (into node-forms edge-forms)))

;; ── reconcile entities across layers by label ─────────────────────────────────

(defn- norm-label [s]
  (-> (str s) str/lower-case str/trim (str/replace #"\s+" " ")))

(defn reconcile-by-label
  "Merge kaname node-forms that share a normalized label into one canonical node (lowest id wins),
  unioning :sos/source-actors; rewrite every edge endpoint to the canonical id. THIS is what lets a
  shared entity span multiple domain layers (→ higher versatility → the 要). Returns rewritten forms."
  [forms]
  (let [nodes (filter #(contains? % ":organism/id") forms)
        edges (filter #(contains? % ":en/from") forms)
        ;; label → canonical id (deterministic: lowest id)
        canon (reduce (fn [m n]
                        (let [lab (norm-label (get n ":organism/label"))
                              id  (get n ":organism/id")]
                          (update m lab (fn [cur] (if (or (nil? cur) (neg? (compare id cur))) id cur)))))
                      {} nodes)
        id->canon (into {} (map (fn [n]
                                  [(get n ":organism/id")
                                   (get canon (norm-label (get n ":organism/label")))])
                                nodes))
        ;; merge nodes onto canonical id, unioning source-actors + OR-ing open?
        merged (reduce (fn [m n]
                         (let [cid (id->canon (get n ":organism/id"))
                               cur (get m cid)
                               srcs (into (set (get cur ":sos/source-actors" []))
                                          (get n ":sos/source-actors" []))]
                           (assoc m cid
                                  (-> (or cur n)
                                      (assoc ":organism/id" cid)
                                      (assoc ":sos/source-actors" (vec (sort srcs)))
                                      (assoc ":sos/open?" (or (true? (get cur ":sos/open?"))
                                                              (true? (get n ":sos/open?"))))))))
                       {} nodes)
        node-forms (vec (vals merged))
        edge-forms (mapv (fn [e]
                           (-> e
                               (assoc ":en/from" (id->canon (get e ":en/from") (get e ":en/from")))
                               (assoc ":en/to"   (id->canon (get e ":en/to")   (get e ":en/to")))))
                         edges)]
    (into node-forms edge-forms)))

(defn forms->graph
  "Convenience: forms (node + edge maps) → sos/load-graph result."
  [forms]
  (sos/load-graph forms))

#?(:clj
   (defn -main
     "Demo: JOIN chie 智慧's real output into kaname's :ai layer and compute leverage over it.
     Args: [mirror-datom-log] [domain] [source-actor]. Defaults to chie / :ai / :chie."
     [& argv]
     (let [argv (vec argv)
           here (-> *file* io/file .getParentFile .getParentFile)
           mirror (if (and (seq argv) (not (str/starts-with? (first argv) "--")))
                    (first argv)
                    (str (io/file here ".." "chie" "out" "ai-ecosystem-datoms.kotoba.edn")))
           domain (if (>= (count argv) 2) (nth argv 1) ":ai")
           src    (if (>= (count argv) 3) (nth argv 2) ":chie")
           outdir (io/file here "out")
           g (read-datom-log mirror)
           lifted (lift g domain src)
           recon  (reconcile-by-label lifted)
           {:keys [nodes edges]} (forms->graph recon)
           res (sos/leverage nodes edges)]
       (.mkdirs outdir)
       (spit (io/file outdir "joined-ai-leverage.md") (sos/report-md nodes edges res))
       (println (str "kaname join: lifted " (count (:nodes g)) " nodes / " (count (:edges g))
                     " 縁 from " mirror " into layer " domain))
       (println (str "  joined graph: " (count nodes) " nodes, " (count edges)
                     " kaname 縁 → out/joined-ai-leverage.md"))
       (doseq [[nid label v] (sos/rank (:C res) nodes 5)]
         (println (str "  top " domain " concentration: " label " (" (format "%.3f" v) ")")))
       0)))
