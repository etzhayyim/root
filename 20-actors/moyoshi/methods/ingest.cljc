(ns moyoshi.methods.ingest
  "moyoshi 催し — live kizuna 絆 ingest (ADR-2606272100 R2). Lifts a COMMITTED kizuna
  readout (its `beat`/`assess` output) into moyoshi's fragility input. Running kizuna is
  G7; JOINING its committed output is what moyoshi does — the kaname 要 join pattern
  (`kaname.methods.join`: run a mirror = G7, join a committed output = the actor's job).
  no-server-key (reads a committed edn / Datom, never a live key). Pure transform +
  a clj-only loader. Portable .cljc (bb)."
  (:require [clojure.edn :as edn]
            #?(:clj [clojure.java.io :as io])))

(defn kizuna->fragility
  "Lift kizuna's readout {:isolated [...] :leverage-actor id :assessment {id {:reciprocity ..}}}
  into moyoshi's fragility {:isolated :leverage-actor :low-reciprocity}. isolated +
  leverage-actor pass through; low-reciprocity = actors whose kizuna reciprocity ratio is
  below `recip-floor` (default 0.5) and are NOT already isolated (isolated dominates —
  an isolated actor has no ties to reciprocate, so it belongs to :isolated, not here).
  Deterministic (sorted), pure."
  [kizuna-out & [{:keys [recip-floor] :or {recip-floor 0.5}}]]
  (let [isolated (vec (sort (:isolated kizuna-out)))
        iso?     (set isolated)
        assess   (:assessment kizuna-out)
        low-recip (->> assess
                       (filter (fn [[id m]]
                                 (and (not (iso? id))
                                      (< (double (get m :reciprocity 1.0)) recip-floor))))
                       (map key) sort vec)]
    {:isolated        isolated
     :leverage-actor  (:leverage-actor kizuna-out)
     :low-reciprocity low-recip}))

(defn reciprocal-ties
  "Extract kizuna's reciprocal-pair set as canonical moyoshi tie-vectors (sorted 2-vecs),
  for use as the settlement baseline / now-graph. kizuna stores reciprocal pairs as
  #{a b} sets under :reciprocal (or a vector of pairs); normalize either form."
  [kizuna-out]
  (->> (or (:reciprocal kizuna-out) (:reciprocal-pairs-set kizuna-out) [])
       (map (fn [p] (vec (sort (seq p)))))
       (sort) vec))

#?(:clj
   (defn load-kizuna
     "Read a committed kizuna readout edn (the file kizuna's heartbeat persists, or any
     beat output dumped as edn). Returns the readout map."
     [path]
     (-> (slurp path) (edn/read-string))))
