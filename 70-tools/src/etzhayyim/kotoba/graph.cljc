;; etzhayyim.kotoba.graph — transitive reachability + tier-depth over edge sets.
;;
;; The supply-chain / power-relations mirror actors (kabuto tier-depth, watatsuna
;; routing, keizu chains) need RECURSIVE traversal the Datalog pattern engine
;; doesn't express. These are pure functions over [from to] edge pairs (which a
;; query already produces, e.g. {:find [?f ?t] :where [[?e :supply.edge/from ?f]
;; [?e :supply.edge/to ?t]]}). Cycle-safe.

(ns etzhayyim.kotoba.graph
  (:require [clojure.set :as set]))

(defn adjacency
  "{node -> #{successors}} from a seq of [from to] edge pairs."
  [edges]
  (reduce (fn [m [f t]] (update m f (fnil conj #{}) t)) {} edges))

(defn reachable
  "Set of nodes transitively reachable from `start` over `adj` (cycle-safe).
   `start` itself is included only if a cycle returns to it."
  [adj start]
  (loop [frontier (vec (get adj start)) seen #{}]
    (if (empty? frontier)
      seen
      (let [n (peek frontier) f (pop frontier)]
        (if (seen n)
          (recur f seen)
          (recur (into f (get adj n)) (conj seen n)))))))

(defn depth
  "BFS distance map {node -> hops-from-start} over `adj` (start = 0). Cycle-safe."
  [adj start]
  (loop [current #{start} dist {start 0} d 0]
    (let [nxt (into #{} (remove dist) (mapcat adj current))]
      (if (empty? nxt)
        dist
        (recur nxt (into dist (map #(vector % (inc d))) nxt) (inc d))))))

(defn tier-depth
  "Longest shortest-path hop count reachable from `start` (0 if a leaf)."
  [adj start]
  (apply max 0 (vals (depth adj start))))

(defn roots
  "Nodes that are a `from` but never a `to` (supply-chain origins / sources)."
  [edges]
  (let [froms (into #{} (map first) edges)
        tos (into #{} (map second) edges)]
    (sort (set/difference froms tos))))

(defn nodes [edges] (into #{} (mapcat identity) edges))

(defn components
  "Weakly-connected components: treat `edges` as undirected and partition the
   nodes into a set of node-sets. Surfaces network fragmentation — isolated
   sub-chains / unreachable segments (a resilience-gap signal for watatsuna /
   kabuto). Only nodes that appear in an edge are included."
  [edges]
  (let [adj (reduce (fn [m [f t]]
                      (-> m (update f (fnil conj #{}) t)
                            (update t (fnil conj #{}) f)))
                    {} edges)]
    (loop [unseen (nodes edges) comps #{}]
      (if (empty? unseen)
        comps
        (let [start (first unseen)
              comp (loop [frontier [start] seen #{}]
                     (if (empty? frontier)
                       seen
                       (let [n (peek frontier) f (pop frontier)]
                         (if (seen n)
                           (recur f seen)
                           (recur (into f (get adj n)) (conj seen n))))))]
          (recur (set/difference unseen comp) (conj comps comp)))))))

(defn component-count [edges] (count (components edges)))

(defn betweenness
  "Brandes betweenness centrality for the directed unweighted graph of `edges`.
   {node -> CB} where CB(v) = number of ordered shortest (s,t) paths through v.
   Identifies brokers / chokepoint SPOFs (watatsuna, kabuto ADR metric)."
  [edges]
  (let [adj (adjacency edges)
        vs (nodes edges)
        cb0 (zipmap vs (repeat 0.0))]
    (reduce
     (fn [cb s]
       ;; single-source: BFS order S, predecessors P, path counts sigma, dist d
       (let [{:keys [order P sigma]}
             (loop [q (conj clojure.lang.PersistentQueue/EMPTY s)
                    order [] P {} sigma {s 1} d {s 0}]
               (if (empty? q)
                 {:order order :P P :sigma sigma}
                 (let [v (peek q) q (pop q)
                       order (conj order v)
                       [q P sigma d]
                       (reduce
                        (fn [[q P sigma d] w]
                          (let [q (if (contains? d w) q (conj q w))
                                d (if (contains? d w) d (assoc d w (inc (d v))))]
                            (if (= (d w) (inc (d v)))
                              [q (update P w (fnil conj []) v)
                               (update sigma w (fnil + 0) (sigma v)) d]
                              [q P sigma d])))
                        [q P sigma d]
                        (get adj v))]
                   (recur q order P sigma d))))
             ;; accumulate dependencies in reverse BFS order
             delta (reduce
                    (fn [delta w]
                      (reduce (fn [delta v]
                                (update delta v (fnil + 0.0)
                                        (* (/ (double (sigma v)) (sigma w))
                                           (+ 1.0 (get delta w 0.0)))))
                              delta (get P w)))
                    {} (rseq order))]
         (reduce (fn [cb w] (if (= w s) cb (update cb w + (get delta w 0.0))))
                 cb vs)))
     cb0 vs)))
