;; etzhayyim.kotoba.test-actor — KG-mirror actor data conformance via the engine.
;;
;; Exercises the kotoba engine + schema layer against REAL stalled 🟡 R0 actor
;; seeds, giving each a schema-conformance + queryable coverage test it lacked.
;; The conformance pattern (declared-vocabulary drift guard + identity uniqueness)
;; is data-driven over a table, so adding an actor is one row.
;;
;; Read-only against existing root data (00-contracts/schemas + 20-actors seeds);
;; nothing is written into the kotoba subrepo.

(ns etzhayyim.kotoba.test-actor
  (:require [clojure.test :refer [deftest is testing]]
            [clojure.edn :as edn]
            [clojure.java.io :as io]
            [clojure.string :as str]
            [clojure.set :as set]
            [etzhayyim.kotoba.schema :as schema]
            [etzhayyim.kotoba.metrics :as metrics]
            [etzhayyim.kotoba.graph :as graph]
            [etzhayyim.kotoba.datom :as d]
            [etzhayyim.kotoba.ingest :as ingest]
            [etzhayyim.kotoba.roster :as roster]
            [etzhayyim.kotoba.engine :as kt]))

(defn- approx= [a b] (< (Math/abs (double (- a b))) 1e-6))

(defn- actor-path [env-var repository relative]
  (str (or (System/getenv env-var) (str "../" repository)) "/" relative))

(deftest hhi-metric-unit
  (testing "monopoly = 10000"
    (is (approx= 10000.0 (metrics/hhi [100]))))
  (testing "two equal players = 5000"
    (is (approx= 5000.0 (metrics/hhi [5 5]))))
  (testing "N equal players = 10000/N"
    (is (approx= 2500.0 (metrics/hhi [1 1 1 1]))))
  (testing "effective-n and top-share"
    (is (approx= 4.0 (metrics/effective-n [1 1 1 1])))
    (is (approx= 1.0 (metrics/effective-n [9])))
    (is (approx= 0.5 (metrics/top-share [5 5]))))
  (testing "empty / zero total is safe"
    (is (approx= 0.0 (metrics/hhi [])))
    (is (approx= 0.0 (metrics/hhi [0 0])))))

;; Each row: the actor, its 00-contracts vocabulary, its 20-actors seed, the
;; entity identity attribute, and (for nested graph seeds) the section keys to
;; flatten. All 🟡 R0 KG-mirror actors sharing the organism/縁 (or node/rel) shape.
(def actor-specs
  [{:actor "asobi"     :schema (actor-path "ETZHAYYIM_ASOBI_ROOT" "com-etzhayyim-asobi" "schema/asobi-ontology.kotoba.edn")
    :seed (actor-path "ETZHAYYIM_ASOBI_ROOT" "com-etzhayyim-asobi" "data/seed-asobi-graph.kotoba.edn") :id-key :organism/id}
   {:actor "inochi"    :schema "00-contracts/schemas/biosphere-ontology.kotoba.edn"
    :seed (actor-path "ETZHAYYIM_INOCHI_ROOT" "com-etzhayyim-inochi" "data/seed-biosphere-graph.kotoba.edn") :id-key :organism/id}
   {:actor "hokorobi"  :schema (actor-path "ETZHAYYIM_HOKOROBI_ROOT" "com-etzhayyim-hokorobi" "schema/finrisk-ontology.kotoba.edn")
    :seed (actor-path "ETZHAYYIM_HOKOROBI_ROOT" "com-etzhayyim-hokorobi" "data/seed-finrisk-graph.kotoba.edn") :id-key :organism/id}
   {:actor "hoshimori" :schema (actor-path "ETZHAYYIM_HOSHIMORI_ROOT" "com-etzhayyim-hoshimori" "schema/orbit-ontology.edn")
    :seed (actor-path "ETZHAYYIM_HOSHIMORI_ROOT" "com-etzhayyim-hoshimori" "data/seed-orbit-graph.kotoba.edn") :id-key :organism/id}
   {:actor "tsugite"   :schema "00-contracts/schemas/peoples-ontology.kotoba.edn"
    :seed (actor-path "ETZHAYYIM_TSUGITE_ROOT" "com-etzhayyim-tsugite" "data/seed-peoples-graph.kotoba.edn") :id-key :organism/id}
   {:actor "shiori"    :schema (actor-path "ETZHAYYIM_SHIORI_ROOT" "com-etzhayyim-shiori" "schema/wellbecoming-ontology.edn")
    :seed (actor-path "ETZHAYYIM_SHIORI_ROOT" "com-etzhayyim-shiori" "data/seed-wellbecoming-graph.kotoba.edn") :id-key :organism/id}
   {:actor "keizu"     :schema "00-contracts/schemas/government-relations-ontology.kotoba.edn"
    :seed "20-actors/keizu/data/seed-relation-graph.kotoba.edn" :id-key :node/id
    :sections [:nodes :committees :rels :money :statements]}
   ;; typed (Datomic-style) schemas — value/enum checks run for real here:
   {:actor "watatsuna" :schema "00-contracts/schemas/submarine-cable-ontology.kotoba.edn"
    :seed (actor-path "ETZHAYYIM_WATATSUNA_ROOT" "com-etzhayyim-watatsuna" "data/seed-cable-graph.kotoba.edn") :id-key :cable/id}
   {:actor "kabuto"    :schema "00-contracts/schemas/public-company-ontology.kotoba.edn"
    :seed "20-actors/kabuto/data/seed-public-companies.kotoba.edn" :id-key :company/id}])

(defn- entity-maps [seed sections]
  (if sections (mapcat seed sections) (filter map? seed)))

(defn- conformance [{:keys [schema seed id-key sections]}]
  (let [vocab (schema/load-vocabulary schema)
        registry (schema/load-registry schema)
        raw (edn/read-string (slurp seed))
        ms (entity-maps raw sections)
        ids (keep id-key ms)]
    {:vocab-size (count vocab) :ent-count (count ms)
     :undeclared (schema/undeclared-attrs vocab ms)
     ;; value-level: typed schemas (keizu) get real type/enum checks; vocab-style
     ;; schemas declare no types so this is an honest no-op (empty).
     :value-violations (schema/value-violations registry ms)
     :ids-unique? (= (count ids) (count (distinct ids))) :id-count (count ids)}))

(deftest kg-mirror-seeds-conform-to-ontologies
  ;; One assertion block per stalled 🟡 R0 mirror actor. Catches schema drift
  ;; (an undeclared attribute = a typo or an ontology that fell behind its data).
  (doseq [{:keys [actor schema seed] :as spec} actor-specs]
    (when (and (.exists (io/file schema)) (.exists (io/file seed)))
      (let [{:keys [undeclared value-violations ids-unique? ent-count vocab-size]}
            (conformance spec)]
        (testing (str actor " — every seed attribute is declared (no drift)")
          (is (empty? undeclared)
              (str actor " undeclared attrs (schema drift): " (sort undeclared))))
        (testing (str actor " — seed values satisfy declared types/enums")
          (is (empty? value-violations)
              (str actor " value violations: " (vec (take 5 value-violations)))))
        (testing (str actor " — identities unique, data non-trivial")
          (is ids-unique? (str actor " has duplicate entity ids"))
          (is (pos? ent-count))
          (is (pos? vocab-size)))))))

(deftest roster-conformance-sweep
  ;; Auto-discover every actor seed that names its :vocabulary and assert its
  ;; data conforms (no undeclared attrs). Catches schema drift across the WHOLE
  ;; roster — not just the hand-listed table — and exercises the schema loader on
  ;; all five ontology dialects found in 00-contracts.
  (let [seeds (->> (file-seq (io/file "20-actors"))
                   (filter #(and (str/includes? (.getPath %) "/data/")
                                 (str/ends-with? (.getName %) ".kotoba.edn"))))
        vocab-of (fn [f] (second (re-find #"vocabulary[:\s]+([a-z0-9-]+-ontology)"
                                          (apply str (take 600 (slurp f))))))
        results (for [f seeds
                      :let [vh (vocab-of f)
                            sp (when vh (str "00-contracts/schemas/" vh ".kotoba.edn"))]
                      :when (and sp (.exists (io/file sp)))]
                  (let [raw (try (edn/read-string (slurp f)) (catch Exception _ nil))
                        ms (cond (vector? raw) (filter map? raw)
                                 (map? raw) (mapcat (fn [[_ v]]
                                                      (when (and (sequential? v) (every? map? v)) v))
                                                    raw)
                                 :else nil)
                        actor (-> f .getParentFile .getParentFile .getName)]
                    {:actor actor
                     :undeclared (when (seq ms) (schema/undeclared-attrs (schema/load-vocabulary sp) ms))
                     :value-attrs (when (seq ms)
                                    (set (map (fn [v] [actor (:attr v)])
                                              (schema/value-violations (schema/load-registry sp) ms))))}))
        drifted (filter #(seq (:undeclared %)) results)
        value-viols (into (sorted-set) (mapcat :value-attrs results))
        ;; Characterization baseline: the only known value mismatches are 3
        ;; mitooshi forecasting attrs whose seed uses inline structures
        ;; (quantile/prob maps, member vector) while the ontology types them
        ;; :db.type/string — a representative-seed vs schema-intent gap flagged
        ;; for actor-author reconciliation. Any NEW value drift fails this test.
        baseline #{["mitooshi" :forecast/members]
                   ["mitooshi" :forecast/probs]
                   ["mitooshi" :forecast/quantiles]}]
    (testing "the discovery sweep found a substantial roster"
      (is (<= 15 (count results)) (str "only " (count results) " seed/schema pairs discovered")))
    (testing "no schema drift anywhere in the roster"
      (is (empty? drifted)
          (str "drift: " (mapv (juxt :actor (comp sort :undeclared)) drifted))))
    (testing "no NEW value-level (type/enum) drift beyond the known baseline"
      (is (= baseline (set value-viols))
          (str "value drift delta: " (set/difference (set value-viols) baseline))))))

(deftest roster-report-ingests-the-fleet
  ;; Broad integration: ingest EVERY discovered actor through the engine and
  ;; assert the maturity matrix — entities load, datoms persist, conformance
  ;; holds roster-wide (only mitooshi carries the known value baseline).
  (let [rows (vec (roster/report))
        clean (filter #(and (not (:error %)) (zero? (:undeclared %))) rows)]
    (testing "substantial roster, every actor ingests with zero undeclared drift"
      (is (<= 15 (count rows)))
      (is (= (count rows) (count clean))
          (str "drift/errors: " (vec (remove (set clean) rows)))))
    (testing "every actor yields live datoms; the roster volume is substantial"
      (is (every? #(or (:error %) (pos? (:datoms %))) rows))
      (is (< 1000 (reduce + (keep :datoms rows)))))
    (testing "value violations are confined to the known mitooshi baseline"
      (is (= #{"mitooshi"}
             (set (map :actor (filter #(pos? (or (:value-violations %) 0)) rows))))))))

(deftest ingest-actor-end-to-end
  ;; The datom_emit replacement: ingest a real actor seed → validated kotoba log
  ;; + canonical snapshot + maturity report, in one call.
  (let [schema "orgs/etzhayyim/com-etzhayyim-asobi/schema/asobi-ontology.kotoba.edn"
        seed "orgs/etzhayyim/com-etzhayyim-asobi/data/seed-asobi-graph.kotoba.edn"]
    (when (and (.exists (io/file schema)) (.exists (io/file seed)))
      (let [j (str (System/getProperty "java.io.tmpdir") "/etz-ing-j-" (System/nanoTime) ".edn")
            out (str (System/getProperty "java.io.tmpdir") "/etz-ing-" (System/nanoTime) ".kotoba.edn")]
        (try
          (let [r (ingest/ingest-actor {:schema schema :seed seed :journal j :out out})]
            (testing "report reflects a real ingest"
              (is (pos? (:entities r)))
              (is (pos? (:datoms r)))
              (is (str/starts-with? (:head r) "bafkrei"))
              (is (empty? (:undeclared r)) "asobi seed conforms")
              (is (= 0 (:value-violations r))))
            (testing "snapshot was written and is loadable"
              (is (pos? (get-in r [:snapshot :rows])))
              (is (= (:head r) (get-in r [:snapshot :head])))
              (is (vector? (edn/read-string (slurp out))))))
          (finally (io/delete-file j true) (io/delete-file out true)))))))

(deftest value-validator-catches-violations
  ;; Prove value-violations is not vacuous: a typed registry must reject a
  ;; wrong-typed value and an out-of-enum value.
  (let [registry (schema/attr-registry
                  {:schema [{:db/ident :x/n :db/valueType :db.type/long}
                            {:db/ident :x/scope :db/valueType :db.type/keyword
                             :db/allowed [:a :b]}]})]
    (testing "clean values pass"
      (is (empty? (schema/value-violations registry [{:x/n 5 :x/scope :a}]))))
    (testing "wrong type is caught"
      (is (= 1 (count (schema/value-violations registry [{:x/n "not-a-number"}])))))
    (testing "out-of-enum value is caught"
      (is (= 1 (count (schema/value-violations registry [{:x/scope :z}])))))))

;; ── capstone: real typed-actor data through the FULL validation engine ──
(def ^:private keizu-schema "00-contracts/schemas/government-relations-ontology.kotoba.edn")
(def ^:private keizu-seed "20-actors/keizu/data/seed-relation-graph.kotoba.edn")

(defn- with-db-id [m]
  (if-let [idk (some #(when (= "id" (name %)) %) (keys m))]
    (assoc m :db/id (get m idk))
    m))

(deftest keizu-real-data-passes-validation-engine
  ;; keizu 系図 (ADR-2606066001, 🟡 R0) government power-relations KG — its schema
  ;; is fully typed (50 attrs, 13 enums, unique :node/id …). Loading the REAL seed
  ;; with :validate? true exercises every write-path gate (type + enum + unique)
  ;; against real data: the completed engine × a real stalled actor.
  (when (and (.exists (io/file keizu-schema)) (.exists (io/file keizu-seed)))
    (let [tmp (str (System/getProperty "java.io.tmpdir") "/etz-keizu-" (System/nanoTime) ".edn")
          d (edn/read-string (slurp keizu-seed))
          rows (map with-db-id (mapcat d [:nodes :committees :rels :money :statements]))]
      (try
        (let [conn (kt/connect {:journal tmp :schemas [keizu-schema] :validate? true})]
          (testing "the whole real seed passes the full validation gate (no throw)"
            (is (map? (kt/transact conn rows))))
          (testing "G1 invariant in data: every node is a public seat/organ (no private person)"
            (let [scopes (set (map first (kt/q conn '{:find [?s] :where [[_ :node/scope ?s]]})))]
              (is (every? #{:public-office :public-org :public-committee :public-role} scopes))))
          (testing "queryable: procurement-award money flows surface (取-concentration lens)"
            (let [awards (kt/q conn '{:find [?payer ?payee ?amt]
                                      :where [[?m :money/kind :procurement-award]
                                              [?m :money/payer ?payer]
                                              [?m :money/payee ?payee]
                                              [?m :money/amount ?amt]]})]
              (is (pos? (count awards)))
              (is (contains? (set (map first awards)) "jp-meti")))))
        (finally (io/delete-file tmp true))))))

(deftest keizu-money-concentration-metric
  ;; The 取-concentration lens (keizu's purpose) computed END TO END on the
  ;; engine: aggregate query (payer -> #flows) → metrics/hhi. Currency-agnostic
  ;; count-based concentration (the money flows span JPY/USD/EUR).
  (when (.exists (io/file keizu-seed))
    (let [tmp (str (System/getProperty "java.io.tmpdir") "/etz-keizu-hhi-" (System/nanoTime) ".edn")
          money (:money (edn/read-string (slurp keizu-seed)))
          rows (map #(assoc % :db/id (:money/id %)) money)]
      (try
        (let [conn (kt/connect {:journal tmp})]
          (kt/transact conn rows)
          (let [by-payer (kt/q conn '{:find [?p (count ?m)]
                                      :where [[?m :money/payer ?p]]})
                counts (map second by-payer)
                hhi (metrics/hhi counts)]
            (testing "payer counts come from the engine aggregate"
              (is (= 6 (reduce + counts)) "6 money flows total")
              (is (= 4 (count by-payer)) "4 distinct payers"))
            (testing "HHI flags concentration (jp-meti holds 3/6 flows)"
              ;; (3²+1²+1²+1²)/6² · 10000 = 12/36 · 10000 = 3333.33
              (is (approx= 3333.333333 hhi))
              (is (< 0.0 hhi 10000.0)))
            (testing "jp-meti is the top concentrator"
              (is (= "jp-meti" (->> by-payer (apply max-key second) first))))))
        (finally (io/delete-file tmp true))))))

(deftest keizu-relation-graph-pull
  ;; pull a procurement-award relation and follow it to the actual payer/payee
  ;; nodes — the graph-traversal the accountability lens needs, on the engine.
  (when (.exists (io/file keizu-seed))
    (let [tmp (str (System/getProperty "java.io.tmpdir") "/etz-keizu-pull-" (System/nanoTime) ".edn")
          d (edn/read-string (slurp keizu-seed))
          rows (map with-db-id (mapcat d [:nodes :committees :rels :money :statements]))]
      (try
        (let [conn (kt/connect {:journal tmp})]
          (kt/transact conn rows)
          (is (= {:db/id "r-award-jp"
                  :rel/kind :procurement-award
                  :rel/source {:db/id "jp-meti" :node/label "経済産業省 (METI)"}
                  :rel/target {:db/id "jp-vendor-x" :node/label "政府調達 受注事業者X (awardee role)"}}
                 (kt/pull conn "r-award-jp"
                          [:rel/kind
                           {:rel/source [:node/label]}
                           {:rel/target [:node/label]}]))))
        (finally (io/delete-file tmp true))))))

(deftest keizu-power-broker-betweenness
  ;; keizu's 取-concentration purpose: surface the BROKERS in the government↔
  ;; industry↔party power graph (rel source→target). Betweenness on the engine.
  (when (.exists (io/file keizu-seed))
    (let [tmp (str (System/getProperty "java.io.tmpdir") "/etz-kz-bw-" (System/nanoTime) ".edn")
          d (edn/read-string (slurp keizu-seed))
          rows (map with-db-id (mapcat d [:nodes :committees :rels :money :statements]))]
      (try
        (let [conn (kt/connect {:journal tmp})
              _ (kt/transact conn rows)
              edges (map vec (kt/q conn '{:find [?s ?t]
                                          :where [[?r :rel/source ?s] [?r :rel/target ?t]]}))
              bw (graph/betweenness edges)]
          (testing "the fiscal-council chair is the top power broker"
            (is (= "jp-fsc-chair" (key (apply max-key val bw))))
            (is (= 2.0 (get bw "jp-fsc-chair"))))
          (testing "the procurement awardee brokers govt money → party funding"
            ;; jp-vendor-x sits on the path jp-meti --procurement→ x --funding→ party
            (is (pos? (get bw "jp-vendor-x" 0.0)))))
        (finally (io/delete-file tmp true))))))

(def ^:private watatsuna-seed "orgs/etzhayyim/com-etzhayyim-watatsuna/data/seed-cable-graph.kotoba.edn")

(deftest watatsuna-cable-chokepoints
  ;; watatsuna 綿津綱 (ADR-2606012600, 🟡 R0) — its purpose is "chokepoint SPOF
  ;; routed to redundancy+repair". The station network (segments connect landing
  ;; stations) → betweenness surfaces the chokepoints. Computed on the engine.
  (when (.exists (io/file watatsuna-seed))
    (let [tmp (str (System/getProperty "java.io.tmpdir") "/etz-wt-" (System/nanoTime) ".edn")
          rows (map with-db-id (filter map? (edn/read-string (slurp watatsuna-seed))))]
      (try
        (let [conn (kt/connect {:journal tmp})
              _ (kt/transact conn rows)
              segs (kt/q conn '{:find [?f ?t]
                                :where [[?s :cable.seg/from ?f] [?s :cable.seg/to ?t]]})
              ;; a cable segment connects two stations both ways (undirected)
              edges (mapcat (fn [[f t]] [[f t] [t f]]) segs)
              bw (graph/betweenness edges)
              maxbw (apply max 0.0 (vals bw))
              top (set (map key (filter #(= maxbw (val %)) bw)))]
          (testing "the station network loaded"
            (is (pos? (count segs)))
            (is (pos? maxbw)))
          (testing "betweenness surfaces the real Asian cable hubs as chokepoints"
            (is (contains? top "station.sg.changi") "Singapore is a top cable chokepoint")
            (is (contains? top "station.hk.tseung-kwan-o") "Hong Kong likewise"))
          (testing "the cable network is fragmented (multiple weakly-connected components)"
            ;; sparse segments → several disconnected cable groups = resilience gaps
            (is (< 1 (graph/component-count edges)))))
        (finally (io/delete-file tmp true))))))

(def ^:private kabuto-seed "20-actors/kabuto/data/seed-public-companies.kotoba.edn")

(deftest kabuto-supply-concentration-at-scale
  ;; kabuto 兜 (ADR-2606022000, 🟡 R0) public-company supply-chain KG — the
  ;; supplier-concentration lens at REAL scale (2496 entities) on the engine.
  ;; Also a performance sanity: load + aggregate of the whole seed completes fast.
  (when (.exists (io/file kabuto-seed))
    (let [tmp (str (System/getProperty "java.io.tmpdir") "/etz-kabuto-" (System/nanoTime) ".edn")
          rows (map with-db-id (filter map? (edn/read-string (slurp kabuto-seed))))]
      (try
        (let [conn (kt/connect {:journal tmp})
              _ (kt/transact conn rows)
              by-supplier (kt/q conn '{:find [?from (count ?e)]
                                       :where [[?e :supply.edge/from ?from]]})
              counts (map second by-supplier)]
          (testing "the full 2496-entity seed loads and the supply graph is queryable"
            (is (= 361 (reduce + counts)) "361 supply edges")
            (is (= 233 (count by-supplier)) "233 distinct suppliers"))
          (testing "supplier concentration is fragmented globally, with clear chokepoints"
            (is (< 60.0 (metrics/hhi counts) 80.0) "low global HHI (many suppliers)")
            (is (< 140.0 (metrics/effective-n counts) 146.0))
            (is (= ["org.corp.tw.tsmc" 12] (apply max-key second by-supplier))
                "TSMC is the most depended-on supplier (top chokepoint)"))
          (testing "reverse pull: TSMC's outgoing supply edges (cross-checks the aggregate)"
            (let [tsmc (kt/pull conn "org.corp.tw.tsmc"
                                [{:supply.edge/_from [:supply.edge/to]}])]
              (is (= 12 (count (:supply.edge/_from tsmc)))
                  "reverse-pull edge count == aggregate out-degree")
              (is (every? :supply.edge/to (:supply.edge/_from tsmc)))))
          (testing "transitive supply-chain tier-depth (kabuto's ADR metric)"
            (let [edges (map vec (kt/q conn '{:find [?f ?t]
                                              :where [[?e :supply.edge/from ?f]
                                                      [?e :supply.edge/to ?t]]}))
                  adj (graph/adjacency edges)]
              ;; MKS Instruments anchors the deepest chain to the major chipmakers
              (is (= 5 (graph/tier-depth adj "org.corp.us.mks")))
              (is (contains? (graph/reachable adj "org.corp.us.mks") "org.corp.tw.tsmc"))
              ;; raw-materials companies are supply roots (never a customer)
              (is (contains? (set (graph/roots edges)) "org.corp.br.vale"))
              ;; betweenness identifies the dominant chokepoint broker
              (let [bw (graph/betweenness edges)
                    top (apply max-key val bw)]
                (is (= "org.corp.tw.tsmc" (key top))
                    "TSMC is the top supply-chain chokepoint (betweenness)")
                (is (> (val top) 400))))))
        (finally (io/delete-file tmp true))))))

;; ── engine query smoke (asobi): prove the engine runs real Datalog on a seed ──
(def ^:private asobi-seed "orgs/etzhayyim/com-etzhayyim-asobi/data/seed-asobi-graph.kotoba.edn")

(deftest asobi-loads-into-engine-and-queries
  (when (.exists (io/file asobi-seed))
    (let [tmp (str (System/getProperty "java.io.tmpdir") "/etz-asobi-" (System/nanoTime) ".edn")
          nodes (->> (edn/read-string (slurp asobi-seed))
                     (filter :organism/id)
                     (map #(assoc % :db/id (:organism/id %))))]
      (try
        (let [conn (kt/connect {:journal tmp})]
          (kt/transact conn nodes)
          (testing "public-domain works queryable via the access lens (G1)"
            (let [pd (kt/q conn '{:find [?id]
                                  :where [[?e :organism/kind :work]
                                          [?e :work/access :public-domain]
                                          [?e :organism/id ?id]]})]
              (is (pos? (count pd)))
              (is (contains? (set (map first pd)) "play.work.beethoven-9"))))
          (testing "entity pull round-trips an asobi node"
            (let [e (kt/entity conn "play.work.beethoven-9")]
              (is (= :work (:organism/kind e)))
              (is (= :public-domain (:work/access e)))))
          (testing "aggregate: works grouped by medium (count per medium)"
            (let [by-medium (kt/q conn '{:find [?m (count ?e)]
                                         :where [[?e :organism/kind :work]
                                                 [?e :work/medium ?m]]})]
              (is (pos? (count by-medium)))
              ;; every group count is a positive integer; total works > 0
              (is (every? (fn [[_ n]] (and (integer? n) (pos? n))) by-medium))
              (is (pos? (reduce + (map second by-medium))))))
          (testing "snapshot the asobi log to a canonical .kotoba.edn and round-trip"
            (let [out (str tmp ".snapshot.kotoba.edn")]
              (try
                (let [{:keys [rows]} (kt/snapshot! conn out)
                      snap (edn/read-string (slurp out))]
                  (is (pos? rows))
                  (is (= (:live (kt/db conn)) (d/live-datoms snap)))
                  (is (str/ends-with? out ".kotoba.edn")))
                (finally (io/delete-file (str tmp ".snapshot.kotoba.edn") true))))))
        (finally (io/delete-file tmp true))))))
