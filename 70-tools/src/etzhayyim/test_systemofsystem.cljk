;; etzhayyim.test-systemofsystem — SoS coupling/cohesion pure invariants (cljc port; IO-free).
;; Run via the aggregate: bb test:helpers
;; Covers cohesion · cluster-layer · build-nanoid-map · coupling-score · cohesion-score ·
;; sos-health-verdict · sos-health · cross-cluster-pairs · layer-groups.
(ns etzhayyim.test-systemofsystem
  (:require [clojure.test :refer [deftest is testing run-tests]]
            [etzhayyim.systemofsystem :as sos]))

(def clusters [{:name "c1" :nanoids ["a" "b"]} {:name "c2" :nanoids ["x"]}])
(def nmap (sos/build-nanoid-map clusters))

(deftest cohesion-ratio
  (is (= 0.8 (sos/cohesion {:internal_edges 8 :external_edges 2})))
  (is (= 0.0 (sos/cohesion {:internal_edges 0 :external_edges 0}))))   ;; guards div-by-zero

(deftest cluster-layer-classification
  (is (= "identity" (sos/cluster-layer "auth-service")))
  (is (= "interface" (sos/cluster-layer "yoro-ui")))
  (is (= "infra" (sos/cluster-layer "pds-deploy")))
  (is (= "inference" (sos/cluster-layer "murakumo-node")))
  (is (= "data" (sos/cluster-layer "graph-db")))
  (is (= "app" (sos/cluster-layer "something-else"))))

(deftest nanoid-map-lookup
  (is (= {"a" "c1" "b" "c1" "x" "c2"} nmap)))

(deftest coupling-and-cohesion-scores
  (let [edges [{:from_nanoid "a" :to_nanoid "b"}    ;; intra c1
               {:from_nanoid "a" :to_nanoid "x"}]]  ;; cross c1→c2
    (is (= 50.0 (sos/coupling-score edges nmap)))
    (is (= 50.0 (sos/cohesion-score edges nmap))))
  (testing "empty edges → 0.0 (guarded total)"
    (is (= 0.0 (sos/coupling-score [] nmap)))
    (is (= 0.0 (sos/cohesion-score [] nmap)))))

(deftest health-verdict-bands
  (is (= "HEALTHY" (sos/sos-health-verdict 10 70)))
  (is (= "ACCEPTABLE" (sos/sos-health-verdict 30 50)))
  (is (= "NEEDS ATTENTION" (sos/sos-health-verdict 50 30))))

(deftest sos-health-aggregate
  (let [h (sos/sos-health clusters
                          [{:nanoid "a"} {:nanoid "b"} {:nanoid "x"}]
                          [{:from_nanoid "a" :to_nanoid "b"} {:from_nanoid "a" :to_nanoid "x"}])]
    (is (= 2 (:clusters h)))
    (is (= 3 (:actors h)))
    (is (= 2 (:edges h)))
    (is (= 50.0 (:coupling_score h)))
    (is (= 50.0 (:cohesion_score h)))
    (is (= "NEEDS ATTENTION" (:verdict h)))))

(deftest cross-cluster-pairs-aggregation
  (testing "inter-cluster edges aggregated by (from,to); intra excluded"
    (let [pairs (sos/cross-cluster-pairs
                 clusters
                 [{:from_nanoid "a" :to_nanoid "x"}    ;; c1→c2
                  {:from_nanoid "b" :to_nanoid "x"}    ;; c1→c2
                  {:from_nanoid "a" :to_nanoid "b"}])] ;; intra, dropped
      (is (= [{:from "c1" :to "c2" :edge_count 2}] pairs)))))

(deftest layer-groups-grouping
  (is (= {"identity" ["auth-x" "auth-y"] "data" ["graph-db"]}
         (sos/layer-groups [{:name "auth-x"} {:name "graph-db"} {:name "auth-y"}]))))

(defn -main [& _]
  (let [{:keys [fail error]} (run-tests 'etzhayyim.test-systemofsystem)]
    (System/exit (if (pos? (+ fail error)) 1 0))))
