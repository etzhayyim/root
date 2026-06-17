(ns kaname.tests.test-kotoba
  "kaname 要 — kotoba commit-DAG persistence tests (ADR-2606172100 R1). The leverage readout projects
  to clean EAVT datoms (no ':'-prefixed values), persists idempotent-by-content, and the chain
  verifies (tamper-evident)."
  (:require [clojure.test :refer [deftest is testing run-tests]]
            [clojure.string :as str]
            #?(:clj [clojure.java.io :as io])
            [kaname.methods.sos :as sos]
            [kaname.methods.centrality :as c]
            [kaname.methods.kotoba :as kkot]
            [kotoba.datom :as kd]))

#?(:clj (def actor-dir (-> *file* io/file .getParentFile .getParentFile)))
#?(:clj (def seed (io/file actor-dir "data" "seed-sos.kotoba.edn")))

#?(:clj
   (defn- res1- []
     (let [{:keys [nodes edges]} (sos/load-file* seed)
           res (sos/leverage nodes edges)]
       [nodes (c/leverage-r1 nodes edges res)])))

(deftest test-datoms-clean
  (testing "every datom value is a string-without-leading-colon or a number (kotoba-safe)"
    (let [[nodes res1] (res1-)
          ds (kkot/leverage->datoms nodes res1 [:chie :tsumugi])]
      (is (seq ds))
      (is (every? (fn [[op _ _ v]]
                    (and (= op ":db/add")
                         (or (number? v)
                             (and (string? v) (not (str/starts-with? v ":"))))))
                  ds))
      (testing "the summary mirrors-joined value has no leading colon (regression on the comma-split bug)"
        (let [mj (some (fn [[_ _ a v]] (when (= a ":kaname/mirrors-joined") v)) ds)]
          (is (= "chie,tsumugi" mj)))))))

#?(:clj
   (deftest test-persist-idempotent-and-verifies
     (let [[nodes res1] (res1-)
           ds (kkot/leverage->datoms nodes res1 [:chie :tsumugi])
           tmp (str (java.io.File/createTempFile "kaname-kotoba" ".edn"))]
       (.delete (io/file tmp))
       (testing "first append writes a tx"
         (let [r (kkot/persist! ds {:tx-id "t0" :as-of "as-of:0" :log-path tmp})]
           (is (true? (:appended r)))))
       (testing "re-append of identical datoms is a no-op (idempotent-by-content)"
         (let [r (kkot/persist! ds {:tx-id "t1" :as-of "as-of:1" :log-path tmp})]
           (is (false? (:appended r)))
           (is (= :no-change (:reason r)))))
       (testing "the commit-DAG verifies (tamper-evident, intact)"
         (let [v (kd/verify-chain tmp)]
           (is (true? (:ok v)))
           (is (= 1 (:length v)))))
       (.delete (io/file tmp)))))
