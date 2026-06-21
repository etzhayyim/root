(ns etzhayyim.explorer.coverage2-test
  "Second coverage batch: the bonsai SVG renderer, the aliveness liveness +
   read-path of the 5-tuple, and the Datom log line parser."
  (:require [cljs.test :refer-macros [deftest is testing]]
            [etzhayyim.explorer.organism.bonsai :as bonsai]
            [etzhayyim.explorer.organism.aliveness :as a]
            [etzhayyim.explorer.chain.datom :as d]))

;; ── bonsai tree (pure hiccup/SVG) ───────────────────────────────────────────
(def ^:private scores
  (mapv (fn [[k en ja] s] {:key k :en en :ja ja :score s})
        a/axes (range 10 0 -1)))

(deftest bonsai-tree-renders-svg
  (testing "tree returns an :svg.bonsai hiccup vector"
    (let [svg (bonsai/tree scores {:lands 3 :members 7})]
      (is (vector? svg))
      (is (= :svg.bonsai (first svg)))
      (is (map? (second svg)))))
  (testing "a single-axis tree does not divide-by-zero (n=1 guard)"
    (is (= :svg.bonsai (first (bonsai/tree [{:key :a :en "A" :ja "あ" :score 5}])))))
  (testing "a missing score (nil) still renders the branch"
    (is (= :svg.bonsai (first (bonsai/tree [{:key :a :en "A" :ja "あ" :score nil}]))))))

;; ── aliveness liveness + read-path ──────────────────────────────────────────
(deftest aliveness-alive?
  (testing "alive when no computed metric is unknown and nothing is low"
    (is (a/alive? [{:source :computed :status :ok}
                   {:source :computed :status :ok}
                   {:source :read :status :high}])))
  (testing "a :low metric → not alive"
    (is (not (a/alive? [{:source :computed :status :ok}
                        {:source :read :status :low}]))))
  (testing "a computed :unknown metric → not alive"
    (is (not (a/alive? [{:source :computed :status :unknown}]))))
  (testing "empty tuple → not alive"
    (is (not (a/alive? [])))))

(deftest aliveness-compute-reads-cpg
  (testing "C/P/G are READ from vitals (any of the accepted keys), M/D computed"
    (let [tuple (a/compute {:trajectory {:runs [{:run 1 :sum 100 :alive 1 :dormant 2 :stub 0}
                                                {:run 2 :sum 140 :alive 1 :dormant 2 :stub 1}]}
                            :vitals {:C 0.4 :pruning 0.1 :mgi 1.5}})
          by-key (into {} (map (juxt :key identity) tuple))]
      (is (= :read (:source (by-key :C))))
      (is (= 0.4 (:value (by-key :C))))
      (is (= :ok (:status (by-key :C))))
      (is (= 0.1 (:value (by-key :P))))         ; via :pruning alias
      (is (= 1.5 (:value (by-key :G))))         ; via :mgi alias
      (is (= :computed (:source (by-key :M))))
      (is (pos? (:value (by-key :M)))))))

;; ── Datom log line parser ───────────────────────────────────────────────────
(deftest datom-parse-log-skips-comments
  (testing "parse-log skips ';' comments + blank lines, normalises datoms"
    (let [text (str ";; kotoba Datom log header — do not edit\n"
                    "\n"
                    "{:tx/id 1 :tx/prev \"\" :tx/cid \"b0\" :tx/count 1 "
                    ":tx/datoms [[:db/add \"e\" :a/x \"v\"]]}\n")
          txs (d/parse-log text)]
      (is (= 1 (count txs)))
      (is (= 1 (:tx/id (first txs))))
      (testing "keywords in datoms are normalised to \":…\" strings"
        (is (= [":db/add" "e" ":a/x" "v"] (first (:tx/datoms (first txs)))))))))
