(ns etzhayyim.pds.datom
  "Self-contained kotoba-Datom-log primitive for the PDS: an append-only log of
  EAVT datoms + a tiny conjunctive datalog `q` to read it back.

  This mirrors the substrate contract of `kotoba-actors.datomic`
  (`orgs/etzhayyim/com-etzhayyim-kotoba-actors-clj`) — entities are [e a v]
  datoms, queries are triple-pattern
  joins — but is vendored here so the PDS deploys as one independent artifact.
  The canonical state is the ordered datom log; an EAVT index is derived for
  reads (ADR-2605312345: the Datom log is first-class, the index materializes
  it, not vice-versa)."
  (:require [clojure.string :as str]))

(defn build-db
  "Fold a seq of [e a v] datoms into an EAVT/AEV/AVE index."
  [datoms]
  (reduce (fn [acc [e a v]]
            (-> acc
                (update-in [:eav e a] (fnil conj #{}) v)
                (update-in [:aev a e] (fnil conj #{}) v)
                (update-in [:ave a v] (fnil conj #{}) e)))
          {}
          datoms))

(defn- lvar? [x]
  (and (symbol? x) (str/starts-with? (name x) "?")))

(defn- match-clause [db binding clause]
  (let [[ep ap vp] clause
        e-const (when-not (lvar? ep) (get binding ep ep))
        a-const (when-not (lvar? ap) (get binding ap ap))
        v-const (when-not (lvar? vp) (get binding vp vp))]
    (cond
      e-const
      (for [[a vs] (get-in db [:eav e-const])
            :when (or (nil? a-const) (= a a-const))
            v vs
            :when (or (nil? v-const) (= v v-const))]
        [e-const a v])

      a-const
      (for [[e vs] (get-in db [:aev a-const])
            v (if v-const (if (contains? (set vs) v-const) [v-const] []) vs)]
        [e a-const v])

      :else
      (for [[e avs] (:eav db)
            [a vs] avs
            v vs]
        [e a v]))))

(defn- project-clause [db binding clause]
  (for [[e a v] (match-clause db binding clause)
        :let [[ep ap vp] clause]
        :when (and (or (not (lvar? ep)) (= (get binding ep e) e))
                   (or (not (lvar? ap)) (= (get binding ap a) a))
                   (or (not (lvar? vp)) (= (get binding vp v) v)))
        :let [b2 (-> binding
                     (cond-> (lvar? ep) (assoc ep e))
                     (cond-> (lvar? ap) (assoc ap a))
                     (cond-> (lvar? vp) (assoc vp v)))]]
    b2))

(defn q
  "Tiny conjunctive datalog. query = {:find [?a ..] :where [[e a v] ..]}.
  Returns a set of result tuples aligned to :find."
  [query db]
  (let [results (reduce (fn [bindings clause]
                          (mapcat #(project-clause db % clause) bindings))
                        [{}]
                        (:where query))]
    (into #{} (map (fn [b] (mapv #(get b %) (:find query)))) results)))
