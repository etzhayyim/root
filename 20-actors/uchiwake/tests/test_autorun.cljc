(ns uchiwake.tests.test-autorun
  "uchiwake 内訳 — autonomous heartbeat + kotoba Datom-log invariants (clojure.test).
  1:1 Clojure port of the PURE assertions in methods/test_autorun.py (ADR-2606081800).

  Guards the autonomy + persistence + non-target/non-recipe contract for the Clojure heartbeat:
  one content-addressed tx per beat to an append-only log; a verifiable commit-DAG (every CID
  recomputes; tamper detected); deterministic / resume-safe (same cycles → same CIDs); G5
  derived-:synthesized; G2/G4 resilience-not-target / not-a-recipe; append-only :db/add.

  DEFERRED (network/adapter legs — a separate unit, mirroring the inochi/rasen precedent already
  noted in test_uchiwake.cljc): the ingest live OFF fetch (G7) + the bridge live-node push (G7)
  gate assertions live in the Python test_autorun.py; the .cljc heartbeat is the ported unit."
  (:require [clojure.test :refer [deftest is testing run-tests]]
            [clojure.string :as str]
            [clojure.java.io :as io]
            [uchiwake.methods.autorun :as autorun]
            [uchiwake.methods.kotoba :as k]))

(def ^:private seed-path "20-actors/uchiwake/data/seed-products.kotoba.edn")

(defn- tmp-log []
  (let [f (java.io.File/createTempFile "uchiwake-test" ".datoms.kotoba.edn")]
    (.delete f)
    (str f)))

(deftest heartbeat-persists
  (let [log (tmp-log)]
    (try
      (let [res (autorun/run-autonomous 3 seed-path log)]
        (is (= 3 (:log-length res)) "one tx per heartbeat")
        (is (every? #(pos? (:datoms %)) (:beats res)) "every heartbeat persisted datoms")
        (is (every? #(pos? (:concentration %)) (:beats res)) "derived concentration persisted")
        (is (:ok (:chain res)) "commit-DAG verifies (chain OK)")
        (is (str/starts-with? (:head-cid res) "b") "head CID is content-addressed"))
      (finally (.delete (io/file log))))))

(deftest deterministic-resume-safe
  (let [a (tmp-log) b (tmp-log)]
    (try
      (let [ra (autorun/run-autonomous 3 seed-path a)
            rb (autorun/run-autonomous 3 seed-path b)]
        (is (= (map :cid (:beats ra)) (map :cid (:beats rb)))
            "same cycles → same CIDs (deterministic / resume-safe)"))
      (finally (.delete (io/file a)) (.delete (io/file b))))))

(deftest append-only-and-tamper
  (let [log (tmp-log)]
    (try
      (autorun/run-cycle 1 seed-path log)
      (let [first-txs (k/read-log log)]
        (autorun/run-cycle 2 seed-path log)
        (let [second-txs (k/read-log log)]
          (is (= (inc (count first-txs)) (count second-txs)) "second beat appends, no rewrite")
          (is (= (get (second second-txs) ":tx/prev") (get (first first-txs) ":tx/cid"))
              "tx 2 links tx 1's CID (commit-DAG)"))
        ;; tamper an earlier tx → the chain must break at 0
        (let [lines (str/split-lines (slurp log))
              tampered (map (fn [ln]
                              (if (str/includes? ln ":tx/id 1 ")
                                (str/replace-first ln ":concentration/sourcing :synthesized"
                                                   ":concentration/sourcing :authoritative")
                                ln))
                            lines)]
          (spit log (str (str/join "\n" tampered) "\n"))
          (let [v (k/verify-chain log)]
            (is (and (not (:ok v)) (= 0 (:broken-at v))) "tampering an earlier tx breaks the chain"))))
      (finally (.delete (io/file log))))))

(defn- entity-attrs [tx]
  (reduce (fn [m d] (assoc-in m [(nth d 1) (nth d 2)] (nth d 3))) {} (get tx ":tx/datoms")))

(deftest g5-derived-synthesized
  (let [log (tmp-log)]
    (try
      (autorun/run-cycle 1 seed-path log)
      (let [tx (first (k/read-log log))
            ents (entity-attrs tx)
            derived (filter (fn [[_e at]]
                              (some #(str/starts-with? (str %) ":concentration/") (keys at)))
                            ents)]
        (is (seq derived) "derived :concentration entities persisted")
        (doseq [[e at] derived]
          (is (= ":synthesized" (get at ":concentration/sourcing"))
              (str "derived " e " declares :sourcing :synthesized (G5)"))
          (is (true? (get at ":concentration/derived"))
              (str "derived " e " carries :concentration/derived true (never re-ingested)"))))
      (finally (.delete (io/file log))))))

(deftest g2-g4-not-target-not-recipe
  (let [log (tmp-log)]
    (try
      (autorun/run-cycle 1 seed-path log)
      (let [tx (first (k/read-log log))
            attrs (set (map #(str (nth % 2)) (get tx ":tx/datoms")))
            ops (set (map first (get tx ":tx/datoms")))]
        (doseq [forbidden [":concentration/target" ":concentration/rank-to-hit" ":target"
                           ":product/clone" ":product/counterfeit" ":bom.edge/full-recipe"
                           ":bom.edge/exact-formulation" ":material/exact-quantity"]]
          (is (not (contains? attrs forbidden))
              (str "no target/recipe attr `" forbidden "` in the log (G2/G4)")))
        (is (= #{":db/add"} ops) "every datom is append-only :db/add (G11)"))
      (finally (.delete (io/file log))))))

(deftest cid-byte-parity-with-python
  ;; The graph_datoms CID over the seed must equal the Python value (kotoba.py byte-parity).
  (let [rows (uchiwake.methods.uchiwake-edn/load-edn seed-path)]
    (is (= "bccd2fa317cf3c10c9f1834da8155c6c2a0ecdebb3447f083a84355bc3230c67a"
           (k/tx-cid (k/graph-datoms rows) ""))
        "graph_datoms tx CID is byte-identical to the Python kotoba.py output")))

(when (= *file* (System/getProperty "babashka.file"))
  (let [r (run-tests 'uchiwake.tests.test-autorun)]
    (when (pos? (+ (:fail r) (:error r))) (System/exit 1))))
