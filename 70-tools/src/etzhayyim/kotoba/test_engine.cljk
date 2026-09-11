;; etzhayyim.kotoba.test-engine — tests for the root-side Datom engine.
;; Run: bb test:kotoba   (see bb.edn)

(ns etzhayyim.kotoba.test-engine
  (:require [clojure.test :refer [deftest is testing]]
            [clojure.java.io :as io]
            [etzhayyim.kotoba.cid :as cid]
            [etzhayyim.kotoba.datom :as d]
            [etzhayyim.kotoba.query :as query]
            [etzhayyim.kotoba.schema :as schema]
            [etzhayyim.kotoba.log :as log]
            [etzhayyim.kotoba.boundary :as boundary]
            [etzhayyim.kotoba.graph :as graph]
            [etzhayyim.kotoba.engine :as kt]))

(deftest graph-reachability
  (let [edges [["a" "b"] ["b" "c"] ["c" "d"] ["a" "x"] ["x" "b"]]
        adj (graph/adjacency edges)]
    (testing "transitive reachability + BFS depth + tier-depth"
      (is (= #{"b" "c" "d" "x"} (graph/reachable adj "a")))
      (is (= {"a" 0 "b" 1 "x" 1 "c" 2 "d" 3} (graph/depth adj "a")))
      (is (= 3 (graph/tier-depth adj "a"))))
    (testing "cycle-safe"
      (let [cyc (graph/adjacency [["a" "b"] ["b" "a"]])]
        (is (= #{"a" "b"} (graph/reachable cyc "a")))
        (is (= 1 (graph/tier-depth cyc "a")))))
    (testing "roots = sources never a target"
      (is (= ["a"] (graph/roots edges))))
    (testing "betweenness centrality (Brandes, directed)"
      (is (= {"a" 0.0 "b" 2.0 "c" 2.0 "d" 0.0}
             (into {} (graph/betweenness [["a" "b"] ["b" "c"] ["c" "d"]]))))
      ;; diamond: a→d has two shortest paths, brokers b/c split the credit
      (is (= {"a" 0.0 "b" 0.5 "c" 0.5 "d" 0.0}
             (into {} (graph/betweenness [["a" "b"] ["a" "c"] ["b" "d"] ["c" "d"]])))))
    (testing "weakly-connected components (fragmentation)"
      (is (= #{#{"a" "b" "c" "d"}} (graph/components [["a" "b"] ["b" "c"] ["c" "d"]])))
      (is (= #{#{"a" "b"} #{"c" "d"}} (graph/components [["a" "b"] ["c" "d"]])))
      (is (= 2 (graph/component-count [["a" "b"] ["b" "a"] ["x" "y"]]))
          "a cycle is one component; a separate edge is another"))))

;; ── cid ──
(deftest cid-framing
  (testing "CIDv1 string is deterministic, base32, multibase-prefixed 'b'"
    (let [c1 (cid/cid "hello")
          c2 (cid/cid "hello")
          c3 (cid/cid "world")]
      (is (= c1 c2) "same content => same CID")
      (is (not= c1 c3) "different content => different CID")
      (is (clojure.string/starts-with? c1 "b") "multibase base32 prefix")
      (is (re-matches #"b[a-z2-7]+" c1) "lowercase base32 alphabet only")))
  (testing "cid-of-edn addresses the canonical value bytes"
    (is (= (cid/cid-of-edn [["e" :a 1 1 :add]])
           (cid/cid (pr-str [["e" :a 1 1 :add]]))))))

(deftest cid-genome-parity
  ;; The CID framing is byte-identical to `ipfs add --cid-version=1 --raw-leaves`
  ;; and to orgs/etzhayyim/com-etzhayyim-rasen/methods/cid.py. Lock that against the daemon-verified
  ;; CIDs recorded in 80-data/genome/publish-manifest.json. Skips if data absent.
  (let [graph "80-data/genome/genome-graph.kotoba.edn"
        datoms "80-data/genome/genome-datoms.kotoba.edn"]
    (when (.exists (io/file graph))
      (is (= "bafkreiamcn6vz4iuqtri6cbjtrse2koz7dfxxyde5rknfypx3ukj5elfvm"
             (cid/cid-of-file graph))
          "graph CID matches daemon-verified published CID"))
    (when (.exists (io/file datoms))
      (is (= "bafkreihsvbx4cs6qjfxkvipn4npsyq4wfmcrwttgzdtbe3w5t56wstpmay"
             (cid/cid-of-file datoms))
          "datoms CID matches daemon-verified published CID"))))

;; ── datom + indexes ──
(deftest live-and-index
  (let [logv [(d/datom "e1" :name "a" 1)
              (d/datom "e1" :age 10 1)
              (d/datom "e2" :name "b" 1)
              (d/datom "e1" :age 10 2 :retract)]
        live (d/live-datoms logv)
        idx (d/index live)]
    (is (= #{["e1" :name "a"] ["e2" :name "b"]} live) "retract removed [e1 :age 10]")
    (is (= #{"a"} (get-in idx [:eavt "e1" :name])))
    (is (= #{"e1" "e2"} (set (keys (:eavt idx)))))
    (is (= #{"e1"} (get-in idx [:avet :name "a"])) "AVET reverse lookup")))

;; ── datalog query ──
(deftest datalog
  (let [live #{["e1" :kind :gene] ["e1" :symbol "APC"]
               ["e2" :kind :gene] ["e2" :symbol "APOE"]
               ["e3" :kind :protein] ["e3" :symbol "p53"]}]
    (testing "pattern join across attributes"
      (is (= #{["e1" "APC"] ["e2" "APOE"]}
             (query/q '{:find [?e ?s]
                        :where [[?e :kind :gene]
                                [?e :symbol ?s]]}
                      live))))
    (testing ":in parameter binding"
      (is (= #{["APC"]}
             (query/q '{:find [?s] :in [?e]
                        :where [[?e :symbol ?s]]}
                      live "e1"))))
    (testing "predicate clause (allowlisted)"
      (is (= #{["e3" "p53"]}
             (query/q '{:find [?e ?s]
                        :where [[?e :symbol ?s]
                                [(not= ?s "APC")]
                                [(not= ?s "APOE")]]}
                      live))))
    (testing "q1 convenience"
      (is (= "APC" (query/q1 '{:find [?s] :where [[?e :kind :gene] [?e :symbol ?s] [(= ?s "APC")]]}
                             live))))))

(deftest datalog-not-or-and
  (let [live #{["g1" :kind :gene] ["g1" :access :public]
               ["g2" :kind :gene] ["g2" :access :private]
               ["p1" :kind :protein] ["p1" :access :public]}]
    (testing "negation: genes that are NOT public"
      (is (= #{["g2"]}
             (query/q '{:find [?e]
                        :where [[?e :kind :gene]
                                (not [?e :access :public])]}
                      live))))
    (testing "disjunction: entities that are gene OR protein with public access"
      (is (= #{["g1"] ["p1"]}
             (query/q '{:find [?e]
                        :where [[?e :access :public]
                                (or [?e :kind :gene]
                                    [?e :kind :protein])]}
                      live))))
    (testing "or with and-branches"
      (is (= #{["g1"] ["g2"]}
             (query/q '{:find [?e]
                        :where [(or (and [?e :kind :gene] [?e :access :public])
                                    (and [?e :kind :gene] [?e :access :private]))]}
                      live))))
    (testing "not removes everything when the negation always holds"
      (is (= #{} (query/q '{:find [?e]
                            :where [[?e :kind :gene]
                                    (not [?e :kind :gene])]}
                          live))))))

(deftest datalog-aggregates
  (let [live #{["e1" :kind :gene] ["e1" :len 10]
               ["e2" :kind :gene] ["e2" :len 30]
               ["e3" :kind :protein] ["e3" :len 50]}]
    (testing "global count"
      (is (= #{[3]} (query/q '{:find [(count ?e)] :where [[?e :kind _]]} live))))
    (testing "group-by + count (count per kind)"
      (is (= #{[:gene 2] [:protein 1]}
             (query/q '{:find [?k (count ?e)]
                        :where [[?e :kind ?k]]} live))))
    (testing "sum / min / max / avg over a group"
      (is (= #{[90]} (query/q '{:find [(sum ?l)] :where [[?e :len ?l]]} live)))
      (is (= #{[10]} (query/q '{:find [(min ?l)] :where [[?e :len ?l]]} live)))
      (is (= #{[50]} (query/q '{:find [(max ?l)] :where [[?e :len ?l]]} live)))
      (is (= #{[30]} (query/q '{:find [(avg ?l)] :where [[?e :len ?l]]} live))))
    (testing "count-distinct"
      (is (= #{[2]} (query/q '{:find [(count-distinct ?k)] :where [[?e :kind ?k]]} live))))
    (testing "grouped sum: total len per kind"
      (is (= #{[:gene 40] [:protein 50]}
             (query/q '{:find [?k (sum ?l)]
                        :where [[?e :kind ?k] [?e :len ?l]]} live))))))

;; ── schema ──
(deftest schema-apply
  (let [attrs {:p/name {:db/ident :p/name :db/valueType :db.type/string
                        :db/cardinality :db.cardinality/one}
               :p/tag  {:db/ident :p/tag :db/valueType :db.type/keyword
                        :db/cardinality :db.cardinality/many}}]
    (testing "cardinality-one auto-retraction"
      (let [live #{["e1" :p/name "old"]}
            out (schema/expand-tx attrs live 2 [{:e "e1" :a :p/name :v "new"}])]
        (is (= [(d/datom "e1" :p/name "old" 2 :retract)
                (d/datom "e1" :p/name "new" 2 :add)]
               (vec out)))))
    (testing "cardinality-many: no auto-retraction"
      (let [live #{["e1" :p/tag :x]}
            out (schema/expand-tx attrs live 2 [{:e "e1" :a :p/tag :v :y}])]
        (is (= [(d/datom "e1" :p/tag :y 2 :add)] (vec out)))))
    (testing "type validation"
      (is (nil? (schema/validate-datom attrs (d/datom "e1" :p/name "ok" 1))))
      (is (= :type-mismatch (:kind (schema/validate-datom attrs (d/datom "e1" :p/name 99 1)))))
      (is (= :unknown-attr (:kind (schema/validate-datom attrs (d/datom "e1" :p/unknown 1 1))))))))

;; ── engine end-to-end (tmp journal) ──
(deftest engine-e2e
  (let [tmp (str (System/getProperty "java.io.tmpdir")
                 "/etzhayyim-kotoba-test-" (System/nanoTime) ".edn")]
    (try
      (let [conn (kt/connect {:journal tmp})]
        (testing "transact entity maps then query"
          (kt/transact conn [{:db/id "ch_1" :charge/amount 500 :charge/currency "USDC"}
                             {:db/id "ch_2" :charge/amount 900 :charge/currency "USDC"}])
          (is (= #{["ch_1" 500] ["ch_2" 900]}
                 (kt/q conn '{:find [?e ?amt]
                              :where [[?e :charge/amount ?amt]]}))))
        (testing "entity pull"
          (is (= {:db/id "ch_1" :charge/amount 500 :charge/currency "USDC"}
                 (kt/entity conn "ch_1"))))
        (testing "head CID advances on commit"
          (let [h1 (kt/head-cid conn)]
            (kt/transact conn [{:db/id "ch_3" :charge/amount 100}])
            (is (not= h1 (kt/head-cid conn)))))
        (testing "durability: re-open journal sees prior datoms"
          (let [conn2 (kt/connect {:journal tmp})]
            (is (= #{["ch_1"] ["ch_2"] ["ch_3"]}
                   (kt/q conn2 '{:find [?e] :where [[?e :charge/amount _]]})))))
        (testing "time-travel as-of excludes later tx"
          (let [live-t1 (kt/as-of conn 1)]
            (is (contains? live-t1 ["ch_1" :charge/amount 500]))
            (is (not (contains? live-t1 ["ch_3" :charge/amount 100]))))))
      (finally (io/delete-file tmp true)))))

(defn- hexkey ^bytes [s]
  (let [n (/ (count s) 2) a (byte-array n)]
    (dotimes [i n]
      (aset a i (unchecked-byte (Integer/parseInt (subs s (* 2 i) (+ 2 (* 2 i))) 16))))
    a))

(deftest subrepo-data-boundary-clean
  ;; The directive: no religious-corp data inside the kotoba subrepo. Lock it.
  (testing "no *.kotoba.edn / *-datoms / *-graph artifacts inside 40-engine/kotoba"
    (let [{:keys [clean? violations root]} (boundary/check)]
      (is clean? (str "data artifacts found inside " root ": " (vec violations)))))
  (testing "the guard actually detects a planted violation (not vacuously green)"
    (let [tmp (str (System/getProperty "java.io.tmpdir") "/etz-bnd-" (System/nanoTime))]
      (io/make-parents (io/file tmp "crates" "x.kotoba.edn"))
      (spit (io/file tmp "crates" "x.kotoba.edn") "[]")
      (try
        (is (false? (:clean? (boundary/check tmp))))
        (is (= 1 (count (:violations (boundary/check tmp)))))
        (finally (io/delete-file (io/file tmp "crates" "x.kotoba.edn") true))))))

(deftest snapshot-lifecycle
  ;; ADR-2605262130 data lifecycle: ingest → append-only log → materialize a
  ;; canonical .kotoba.edn snapshot → the snapshot reproduces the live state and
  ;; is itself queryable (the 80-data publish format).
  (let [tmp (str (System/getProperty "java.io.tmpdir") "/etz-snap-j-" (System/nanoTime) ".edn")
        out (str (System/getProperty "java.io.tmpdir") "/etz-snap-" (System/nanoTime) ".kotoba.edn")]
    (try
      (let [conn (kt/connect {:journal tmp})]
        (kt/transact conn [{:db/id "a" :k/x 1 :k/y "hi"} {:db/id "b" :k/x 2}])
        (kt/transact conn [{:db/id "a" :k/x 9}])   ; supersedes a's :k/x (cardinality-one default)
        (let [{:keys [rows head]} (kt/snapshot! conn out)
              snap (clojure.edn/read-string (slurp out))]
          (testing "snapshot is a vector of canonical [e a v tx op] 5-tuples"
            (is (vector? snap))
            (is (every? #(= 5 (count %)) snap))
            (is (= rows (count snap))))
          (testing "snapshot reproduces the engine's live state (supersede applied)"
            (is (= (:live (kt/db conn)) (d/live-datoms snap)))
            (is (contains? (d/live-datoms snap) ["a" :k/x 9]))
            (is (not (contains? (d/live-datoms snap) ["a" :k/x 1]))))
          (testing "the snapshot is itself queryable (publish format)"
            (is (= #{["a" 9] ["b" 2]}
                   (query/q '{:find [?e ?x] :where [[?e :k/x ?x]]} (d/live-datoms snap)))))
          (testing "snapshot head CID is the deterministic content address of the log"
            (is (= head (kt/head-cid conn)))
            (is (clojure.string/starts-with? head "bafkrei")))))
      (finally (io/delete-file tmp true) (io/delete-file out true)))))

(deftest pull-patterns
  (let [tmp (str (System/getProperty "java.io.tmpdir") "/etz-pull-" (System/nanoTime) ".edn")]
    (try
      (let [conn (kt/connect {:journal tmp})]
        (kt/transact conn [{:db/id "alice" :person/name "Alice" :person/city "tokyo"}
                           {:db/id "bob" :person/name "Bob" :friend/of "alice"}
                           {:db/id "tokyo" :city/name "Tokyo" :city/pop 14}])
        (testing "scalar attr pull"
          (is (= {:db/id "alice" :person/name "Alice"}
                 (kt/pull conn "alice" [:person/name]))))
        (testing "wildcard pulls all attrs"
          (is (= {:db/id "alice" :person/name "Alice" :person/city "tokyo"}
                 (kt/pull conn "alice" '[*]))))
        (testing "nested ref pull (bob -> alice -> tokyo)"
          (is (= {:db/id "bob" :person/name "Bob"
                  :friend/of {:db/id "alice" :person/name "Alice"
                              :person/city {:db/id "tokyo" :city/name "Tokyo"}}}
                 (kt/pull conn "bob"
                          [:person/name
                           {:friend/of [:person/name
                                        {:person/city [:city/name]}]}]))))
        (testing "reverse ref pull (who lives in tokyo)"
          (is (= {:db/id "tokyo" :city/name "Tokyo" :city/pop 14
                  :person/_city [{:db/id "alice" :person/name "Alice"}]}
                 (kt/pull conn "tokyo" '[* {:person/_city [:person/name]}]))))
        (testing "ref to a leaf with no datoms keeps the raw id"
          (kt/transact conn [{:db/id "carol" :friend/of "nobody"}])
          (is (= {:db/id "carol" :friend/of "nobody"}
                 (kt/pull conn "carol" [{:friend/of [:person/name]}]))))
        (testing "pull of an unknown entity is nil"
          (is (nil? (kt/pull conn "ghost" '[*])))))
      (finally (io/delete-file tmp true)))))

(deftest transact-time-validation
  ;; The engine's :validate? write-path hook rejects values that violate the
  ;; schema's declared :db/valueType / :db/allowed — before anything is written.
  (let [tmp (str (System/getProperty "java.io.tmpdir") "/etz-val-" (System/nanoTime) ".edn")
        schema-file (str tmp ".schema.edn")]
    (spit schema-file
          (pr-str {:attributes [{:db/ident :t/n :db/valueType :db.type/long}
                                {:db/ident :t/scope :db/valueType :db.type/keyword
                                 :db/allowed [:a :b]}]}))
    (try
      (let [conn (kt/connect {:journal tmp :schemas [schema-file] :validate? true})]
        (testing "conforming tx is accepted"
          (kt/transact conn [{:db/id "ok" :t/n 5 :t/scope :a}])
          (is (= #{[5]} (kt/q conn '{:find [?n] :where [["ok" :t/n ?n]]}))))
        (testing "wrong-typed value is rejected"
          (is (thrown-with-msg? Exception #"validation failed"
                (kt/transact conn [{:db/id "bad1" :t/n "not-a-number"}]))))
        (testing "out-of-enum value is rejected"
          (is (thrown-with-msg? Exception #"validation failed"
                (kt/transact conn [{:db/id "bad2" :t/scope :z}]))))
        (testing "rejected tx wrote NOTHING (atomic)"
          (is (empty? (kt/q conn '{:find [?e] :where [["bad1" :t/n ?e]]})))
          (is (empty? (kt/q conn '{:find [?e] :where [["bad2" :t/scope ?e]]})))
          (is (not (clojure.string/includes? (slurp tmp) "not-a-number"))))
        (testing "unknown attrs pass (open-world even with :validate?)"
          (kt/transact conn [{:db/id "ok2" :t/undeclared "anything"}])
          (is (= #{["anything"]} (kt/q conn '{:find [?v] :where [["ok2" :t/undeclared ?v]]})))))
      (finally (io/delete-file tmp true) (io/delete-file schema-file true)))))

(deftest transact-time-unique-identity
  ;; :db.unique/identity / :db.unique/value enforced at write time: a unique
  ;; value may belong to at most one entity.
  (let [tmp (str (System/getProperty "java.io.tmpdir") "/etz-uniq-" (System/nanoTime) ".edn")
        schema-file (str tmp ".schema.edn")]
    (spit schema-file
          (pr-str {:attributes [{:db/ident :u/id :db/valueType :db.type/string
                                 :db/unique :db.unique/identity}]}))
    (try
      (let [conn (kt/connect {:journal tmp :schemas [schema-file] :validate? true})]
        (testing "first claim of a unique value is accepted"
          (kt/transact conn [{:db/id "a" :u/id "X"}])
          (is (= #{["a"]} (kt/q conn '{:find [?e] :where [[?e :u/id "X"]]}))))
        (testing "same entity re-asserting the same unique value is fine (no upsert conflict)"
          (kt/transact conn [{:db/id "a" :u/id "X"}])
          (is (= #{["a"]} (kt/q conn '{:find [?e] :where [[?e :u/id "X"]]}))))
        (testing "a DIFFERENT entity claiming the held unique value is rejected"
          (is (thrown-with-msg? Exception #"validation failed"
                (kt/transact conn [{:db/id "b" :u/id "X"}])))
          (is (= #{["a"]} (kt/q conn '{:find [?e] :where [[?e :u/id "X"]]}))
              "the rejected claim wrote nothing"))
        (testing "in-tx collision (two distinct entities, same unique value) is rejected"
          (is (thrown-with-msg? Exception #"validation failed"
                (kt/transact conn [{:db/id "c" :u/id "Y"} {:db/id "d" :u/id "Y"}])))
          (is (empty? (kt/q conn '{:find [?e] :where [[?e :u/id "Y"]]})))))
      (finally (io/delete-file tmp true) (io/delete-file schema-file true)))))

(deftest confidential-datoms-e2e
  ;; Integration of increment #1 (log) + #2 (envelope): a sealed record stored
  ;; as datoms; plaintext never on the log; only a key-holder can read it back.
  (let [tmp (str (System/getProperty "java.io.tmpdir")
                 "/etzhayyim-kotoba-enc-" (System/nanoTime) ".edn")
        key (hexkey "808182838485868788898a8b8c8d8e8f909192939495969798999a9b9c9d9e9f")
        nonce (hexkey "404142434445464748494a4b4c4d4e4f5051525354555657")]
    (try
      (let [conn (kt/connect {:journal tmp})
            secret {:proposal "ratify ADR-X" :votes 7}
            {:keys [cid]} (kt/transact-encrypted conn key nonce "rec_1" secret
                            {:sender "did:web:etzhayyim.com"
                             :innerType "com.etzhayyim.governance.proposal"
                             :createdAt "2026-06-14T00:00:00Z"
                             :recipients ["did:web:alice.example" "did:web:bob.example"]})]
        (testing "envelope CID is queryable on the log"
          (is (= #{[cid]} (kt/q conn '{:find [?c] :where [["rec_1" :enc/cid ?c]]}))))
        (testing "plaintext is NOT present anywhere on the log"
          (let [blob (slurp tmp)]
            (is (not (clojure.string/includes? blob "ratify ADR-X")))
            (is (not (clojure.string/includes? blob ":votes")))))
        (testing "key-holder decrypts the record back"
          (is (= secret (kt/read-encrypted conn key "rec_1"))))
        (testing "wrong key fails (AEAD)"
          (is (thrown? Exception (kt/read-encrypted conn (byte-array 32) "rec_1"))))
        (testing "keyWraps enumerate read-cap holders"
          (is (= #{"did:web:alice.example" "did:web:bob.example"}
                 (set (kt/recipients-of conn cid)))))
        (testing "survives journal re-open (durable confidential datoms)"
          (let [conn2 (kt/connect {:journal tmp})]
            (is (= secret (kt/read-encrypted conn2 key "rec_1"))))))
      (finally (io/delete-file tmp true)))))
