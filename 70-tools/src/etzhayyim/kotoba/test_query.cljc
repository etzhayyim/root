;; etzhayyim.kotoba.test-query — Datalog subset over a live EAVT triple set. Run: bb test:kotoba
;; Pins patterns, joins, :in inputs, predicate/not/or clauses, and aggregates.
(ns etzhayyim.kotoba.test-query
  (:require [clojure.test :refer [deftest is testing run-tests]]
            [etzhayyim.kotoba.query :as q]))

(def live
  #{["p1" :type :person]  ["p1" :name "alice"] ["p1" :age 30]
    ["p2" :type :person]  ["p2" :name "bob"]   ["p2" :age 17]
    ["c1" :type :company] ["c1" :name "acme"]})

(deftest pattern-and-join
  (testing "data pattern binds matching entities"
    (is (= #{["p1"] ["p2"]} (q/q '{:find [?e] :where [[?e :type :person]]} live))))
  (testing "two clauses sharing ?e join (names of persons)"
    (is (= #{["alice"] ["bob"]}
           (q/q '{:find [?n] :where [[?e :type :person] [?e :name ?n]]} live))))
  (testing "constant value filters"
    (is (= #{["p2"]} (q/q '{:find [?e] :where [[?e :name "bob"]]} live)))))

(deftest input-binding
  (testing ":in binds positional inputs"
    (is (= #{["c1"]} (q/q '{:find [?e] :in [?t] :where [[?e :type ?t]]} live :company)))))

(deftest predicate-clause
  (testing "allowlisted predicate filters bound values"
    (is (= #{["p1"]} (q/q '{:find [?e] :where [[?e :age ?a] [(> ?a 18)]]} live))))
  (testing "an unsupported predicate throws"
    (is (thrown? clojure.lang.ExceptionInfo
                 (q/q '{:find [?e] :where [[?e :age ?a] [(bogus ?a 1)]]} live)))))

(deftest not-and-or-clauses
  (testing "(not …) = negation-as-failure"
    (is (= #{["p2"]} (q/q '{:find [?e] :where [[?e :type :person] (not [?e :name "alice"])]} live))))
  (testing "(or …) = union of branch solutions"
    (is (= #{["p1"] ["p2"] ["c1"]}
           (q/q '{:find [?e] :where [(or [?e :type :person] [?e :type :company])]} live)))))

(deftest aggregates
  (testing "count over all matches"
    (is (= #{[2]} (q/q '{:find [(count ?e)] :where [[?e :type :person]]} live))))
  (testing "group-by the non-aggregate find var"
    (is (= #{[:person 2] [:company 1]}
           (q/q '{:find [?t (count ?e)] :where [[?e :type ?t]]} live))))
  (testing "sum over a grouped value"
    (is (= #{[47]} (q/q '{:find [(sum ?a)] :where [[?e :type :person] [?e :age ?a]]} live)))))

(deftest q1-convenience
  (is (= "acme" (q/q1 '{:find [?n] :where [[?e :type :company] [?e :name ?n]]} live)))
  (testing "q1 of an empty result is nil"
    (is (nil? (q/q1 '{:find [?n] :where [[?e :type :alien] [?e :name ?n]]} live)))))

(defn -main [& _]
  (let [{:keys [fail error]} (run-tests 'etzhayyim.kotoba.test-query)]
    (System/exit (if (pos? (+ fail error)) 1 0))))
