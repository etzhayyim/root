(ns etzhayyim.pds.datom-test
  "Invariants for the self-contained EAVT datom log + conjunctive datalog `q`
  that backs the PDS in-process store read path (ADR-2605312345)."
  (:require [clojure.test :refer [deftest is testing run-tests]]
            [etzhayyim.pds.datom :as d]))

(def datoms
  [[:p1 :type :person]  [:p1 :name "alice"]
   [:p2 :type :person]  [:p2 :name "bob"]
   [:c1 :type :company] [:c1 :name "acme"]])

(def db (d/build-db datoms))

(deftest build-db-indexes
  (testing "EAVT: entity → attr → value-set"
    (is (= #{"alice"} (get-in db [:eav :p1 :name])))
    (is (= #{:person} (get-in db [:eav :p1 :type]))))
  (testing "AVE: attr → value → entity-set (the inverted index)"
    (is (= #{:p1 :p2} (get-in db [:ave :type :person])))
    (is (= #{:c1} (get-in db [:ave :type :company]))))
  (testing "AEV: attr → entity → value-set"
    (is (= #{"bob"} (get-in db [:aev :name :p2]))))
  (testing "repeated [e a] accumulates into a value set"
    (let [db2 (d/build-db [[:e :tag "x"] [:e :tag "y"] [:e :tag "x"]])]
      (is (= #{"x" "y"} (get-in db2 [:eav :e :tag]))))))

(deftest q-entity-pattern
  (testing "bind attr+value for a fixed entity"
    (is (= #{[:type :person] [:name "alice"]}
           (d/q {:find ['?a '?v] :where [[:p1 '?a '?v]]} db)))))

(deftest q-attribute-and-value
  (testing "find entities by attribute"
    (is (= #{[:p1] [:p2]} (d/q {:find ['?e] :where [['?e :type :person]]} db))))
  (testing "find entity by attribute + constant value"
    (is (= #{[:p2]} (d/q {:find ['?e] :where [['?e :name "bob"]]} db))))
  (testing "no match → empty set"
    (is (= #{} (d/q {:find ['?e] :where [['?e :name "nobody"]]} db)))))

(deftest q-conjunctive-join
  (testing "two clauses sharing ?e = a join: names of all persons"
    (is (= #{["alice"] ["bob"]}
           (d/q {:find ['?n] :where [['?e :type :person] ['?e :name '?n]]} db))))
  (testing "join narrowed by a constant: the person named alice"
    (is (= #{[:p1]}
           (d/q {:find ['?e] :where [['?e :type :person] ['?e :name "alice"]]} db))))
  (testing "join with no overlap → empty"
    (is (= #{} (d/q {:find ['?e] :where [['?e :type :company] ['?e :name "bob"]]} db)))))

(defn -main [& _]
  (let [{:keys [fail error]} (run-tests 'etzhayyim.pds.datom-test)]
    (System/exit (if (pos? (+ fail error)) 1 0))))
