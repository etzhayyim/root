(ns kotoba-actors.datomic
  "A minimal, in-process kotoba-datomic-style substrate: turn kotoba-EDN entity
  rows into EAVT datoms, index them, and query them with a tiny datalog.

  This is the parallel-Clojure refactor of the Python actors' hand-rolled
  map-walking: instead of filtering vectors of maps, we model each fact as a
  datom [e a v] and answer questions with `q`. The Python actors are untouched.

  ── CONTRACT (the kotoba-code task is to implement every `todo` below) ────────
  A `db` is whatever `build-db` returns (an EAVT index of your choosing).
  `q` is a tiny conjunctive datalog: a query is

    {:find  [?sym ...]        ; symbols starting with ? are logic vars
     :where [[?e :attr ?v]    ; each clause is an [e a v] triple-pattern;
             [?e :a2 const]]} ; non-?-symbols / keywords / literals are constants

  `q` returns a SET of tuples (vectors), one per :find symbol, for every
  consistent binding of the where-clauses (joins share vars across clauses)."
  (:require [clojure.edn :as edn]))

;; ── ingest ───────────────────────────────────────────────────────────────────

(defn load-rows
  "Read a kotoba-EDN seed file (a single top-level vector of entity maps).
  Returns the vector of maps. (This edge is allowed to do file I/O.)"
  [path]
  (edn/read-string (slurp path)))

(defn rows->datoms
  "Flatten entity-map rows into a seq of [e a v] datoms.

  The entity id `e` is the value of the row's `*/id` attribute (e.g. the value
  under :company/id, :supply.edge/id, :product/id, :part/id, :material/id,
  :bom.edge/id). Every OTHER key/value in the row becomes a datom [e k v].
  Rows without any `*/id` key are skipped."
  [rows]
  (for [row rows
        :let [id-k (some #(when (.endsWith (name %) "id") %) (keys row))]
        :when id-k
        :let [e (get row id-k)]
        [k v] row
        :when (not= k id-k)]
    [e k v]))

(defn build-db
  "Build an EAVT-indexed db from a seq of [e a v] datoms. Shape is your choice
  (e.g. {:eav {e {a #{v}}} :aev {a {e #{v}}} :ave {a {v #{e}}}}) as long as `q`
  can answer triple-pattern joins against it."
  [datoms]
  (let [index (fn [acc [e a v]]
                (-> acc
                    (update-in [:eav e a] (fnil conj #{}) v)
                    (update-in [:aev a e] (fnil conj #{}) v)
                    (update-in [:ave a v] (fnil conj #{}) e)))]
    (reduce index {} datoms)))

(defn db-from-seed
  "Convenience: path -> rows -> datoms -> db."
  [path]
  (-> path load-rows rows->datoms build-db))

;; ── query ─────────────────────────────────────────────────────────────────────

(defn- lvar? [x]
  (and (symbol? x) (.startsWith (name x) "?")))

(defn- clause-vars [clause]
  (distinct (filter lvar? clause)))

(defn- match-clause
  "Given a binding map and a clause [e-pattern a-pattern v-pattern], return the
  subset of datoms that match the (possibly partially bound) pattern."
  [db binding clause]
  (let [[ep ap vp] clause
        e-const (when-not (lvar? ep) (get binding ep ep))
        a-const (when-not (lvar? ap) (get binding ap ap))
        v-const (when-not (lvar? vp) (get binding vp vp))]
    (cond
      ;; E is bound/constant: scan the entity sub-index.
      e-const
      (for [[a vs] (get-in db [:eav e-const])
            :when (or (nil? a-const) (= a a-const))
            v vs
            :when (or (nil? v-const) (= v v-const))]
        [e-const a v])

      ;; A is bound/constant: scan the attribute sub-index.
      a-const
      (let [es (get-in db [:aev a-const])]
        (for [[e vs] es
               v (if v-const (if (contains? (set vs) v-const) [v-const] []) vs)]
          [e a-const v]))

      ;; No constants at all: full datom scan.
      :else
      (for [[e avs] (:eav db)
            [a vs] avs
            v vs]
        [e a v]))))

(defn- project-clause
  "Apply a clause to a binding map, returning a seq of extended binding maps.

  A logic var in the clause must UNIFY with the incoming binding: if it is
  already bound, the datom value must equal the existing binding; if it is free,
  it is bound to the datom value. This makes shared variables across clauses act
  as joins rather than cross-products."
  [db binding clause]
  (for [datom (match-clause db binding clause)
        :let [[ep ap vp] clause
              [e a v] datom]
        :when (and (or (not (lvar? ep)) (= (get binding ep e) e))
                   (or (not (lvar? ap)) (= (get binding ap a) a))
                   (or (not (lvar? vp)) (= (get binding vp v) v)))
        :let [b2 (-> binding
                     (cond-> (lvar? ep) (assoc ep e))
                     (cond-> (lvar? ap) (assoc ap a))
                     (cond-> (lvar? vp) (assoc vp v)))]]
    b2))

(defn q
  "Tiny conjunctive datalog. See ns docstring for the query shape.
  Returns a set of result tuples (vectors aligned to :find)."
  [query db]
  (let [find-syms (:find query)
        clauses (:where query)
        results (reduce (fn [bindings clause]
                          (mapcat #(project-clause db % clause) bindings))
                        [{}]
                        clauses)]
    (into #{} (map (fn [b] (mapv #(get b %) find-syms))) results)))
