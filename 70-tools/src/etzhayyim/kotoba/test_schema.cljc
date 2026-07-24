;; etzhayyim.kotoba.test-schema — attribute registry, conformance, uniqueness,
;; and cardinality-one auto-retraction. Run: bb test:kotoba
(ns etzhayyim.kotoba.test-schema
  (:require [clojure.test :refer [deftest is testing run-tests]]
            [etzhayyim.kotoba.datom :as d]
            [etzhayyim.kotoba.schema :as s]))

;; raw ident→spec attrs (the shape cardinality/one?/validate-datom/expand-tx read)
(def attrs
  {:p/name   {:db/valueType :db.type/string  :db/cardinality :db.cardinality/one  :db/unique :db.unique/identity}
   :p/tags   {:db/valueType :db.type/keyword :db/cardinality :db.cardinality/many}
   :p/age    {:db/valueType :db.type/long    :db/cardinality :db.cardinality/one}
   :p/status {:db/valueType :db.type/keyword :db/cardinality :db.cardinality/one :db/allowed [:active :dormant]}})

(deftest schema-vocabulary
  (is (= {:a 1 :b 2} (s/merge-schemas {:a 1} {:b 2})))
  (testing "declared-attrs across dialects (Datomic :attributes + vocab :node/attrs)"
    (is (= #{:p/name :p/age}
           (s/declared-attrs {:attributes [{:db/ident :p/name} {:db/ident :p/age}]})))
    (is (= #{:n/x} (s/declared-attrs {:node/attrs [{:attr :n/x}]}))))
  (testing "used-attrs drops :db/id; undeclared-attrs = drift"
    (is (= #{:p/name :p/age} (s/used-attrs [{:p/name "a" :db/id 1} {:p/age 5}])))
    (is (= #{:p/typo} (s/undeclared-attrs #{:p/name} [{:p/name "x" :p/typo 1}])))))

(deftest value-conformance
  (let [reg (s/attr-registry {:attributes [{:db/ident :p/status :db/valueType :db.type/keyword
                                            :db/allowed [:active :dormant]
                                            :db/cardinality :db.cardinality/one}]})]
    (is (empty? (s/value-violations reg [{:p/status :active}])))
    (is (= 1 (count (s/value-violations reg [{:p/status :bogus}]))))))

(deftest uniqueness
  (is (= #{:p/name} (s/unique-attrs attrs)))
  (testing "a different entity claiming a held unique value conflicts"
    (is (= 1 (count (s/unique-conflicts attrs #{["e1" :p/name "alice"]}
                                        [{:e "e2" :a :p/name :v "alice"}])))))
  (testing "the same entity re-asserting its own unique value is fine"
    (is (empty? (s/unique-conflicts attrs #{["e1" :p/name "alice"]}
                                    [{:e "e1" :a :p/name :v "alice"}])))))

(deftest cardinality-and-identity
  (is (= :db.cardinality/many (s/cardinality attrs :p/tags)))
  (is (= :db.cardinality/one (s/cardinality attrs :unknown)))   ;; default
  (is (true? (s/one? attrs :p/name)))
  (is (false? (s/one? attrs :p/tags)))
  (is (true? (s/identity-attr? attrs :p/name)))
  (is (false? (s/identity-attr? attrs :p/age))))

(deftest datom-validation
  (is (nil? (s/validate-datom attrs (d/datom "e" :p/age 5 1))))
  (is (= :type-mismatch (:kind (s/validate-datom attrs (d/datom "e" :p/age "nan" 1)))))
  (is (= :unknown-attr (:kind (s/validate-datom attrs (d/datom "e" :p/unknown 1 1)))))
  (testing "check-datom-value enforces the :db/allowed enum"
    (is (nil? (s/check-datom-value attrs (d/datom "e" :p/status :active 1))))
    (is (some? (s/check-datom-value attrs (d/datom "e" :p/status :bogus 1))))))

(deftest expand-tx-auto-retraction
  (testing "cardinality-one change retracts the prior value first"
    (is (= [(d/datom "e" :p/name "old" 5 :retract)
            (d/datom "e" :p/name "new" 5 :add)]
           (s/expand-tx attrs #{["e" :p/name "old"]} 5 [{:e "e" :a :p/name :v "new"}]))))
  (testing "cardinality-many accumulates (no retraction)"
    (is (= [(d/datom "e" :p/tags :y 5 :add)]
           (s/expand-tx attrs #{["e" :p/tags :x]} 5 [{:e "e" :a :p/tags :v :y}]))))
  (testing "re-asserting the same value emits no retraction"
    (is (= [(d/datom "e" :p/name "v" 5 :add)]
           (s/expand-tx attrs #{["e" :p/name "v"]} 5 [{:e "e" :a :p/name :v "v"}])))))

(defn -main [& _]
  (let [{:keys [fail error]} (run-tests 'etzhayyim.kotoba.test-schema)]
    (System/exit (if (pos? (+ fail error)) 1 0))))
