;; etzhayyim.test-haisen — haisen wiring-graph pure invariants (cljc port).
;; Run: bb test:haisen
;; Covers make-app · app->dict · edge->dict · app-from-jsonld · orphans ·
;; coupling · report->dict · build-edges (subscribe edges).
(ns etzhayyim.test-haisen
  (:require [clojure.test :refer [deftest is testing run-tests]]
            [etzhayyim.haisen :as h]))

(deftest app-construction-and-serialisation
  (testing "make-app maps jsonld fields with defaults"
    (is (= {:nanoid "n1" :did "did:x" :name "foo" :performer-type ""
            :ui-type "" :runtime-type "" :collections ["c1"] :wit-imports [] :wit-exports []}
           (h/make-app {"nanoid" "n1" "did" "did:x" "name" "foo" "collections" ["c1"]}))))
  (testing "app->dict round-trips make-app to string keys"
    (let [d (h/app->dict (h/make-app {"nanoid" "n1" "name" "foo"}))]
      (is (= "n1" (get d "nanoid")))
      (is (= "foo" (get d "name")))
      (is (= [] (get d "collections")))))
  (testing "app-from-jsonld requires a nanoid"
    (is (some? (h/app-from-jsonld {"nanoid" "n1"})))
    (is (nil? (h/app-from-jsonld {})))
    (is (nil? (h/app-from-jsonld {"nanoid" ""})))))

(deftest edge->dict-stringifies-type
  (is (= {"from" "a" "to" "b" "type" "invoke"}
         (h/edge->dict {:from "a" :to "b" :type :invoke}))))

(deftest orphans-and-coupling
  (testing "orphans = apps not appearing in any edge endpoint"
    (is (= [{:nanoid "c"}]
           (h/orphans {:apps  [{:nanoid "a"} {:nanoid "b"} {:nanoid "c"}]
                       :edges [{:from "a" :to "b" :type :subscribe}]}))))
  (testing "coupling = in-degree counts, descending"
    (is (= [["x" 2] ["y" 1]]
           (h/coupling {:edges [{:to "x"} {:to "x"} {:to "y"}]})))))

(deftest report->dict-shape
  (let [r (h/report->dict {:apps  [(h/make-app {"nanoid" "a" "name" "alpha"})]
                           :edges [{:from "a" :to "b" :type :subscribe}]})]
    (is (= 1 (count (get r "apps"))))
    (is (= "a" (get-in r ["apps" 0 "nanoid"])))
    (is (= [{"from" "a" "to" "b" "type" "subscribe"}] (get r "edges")))))

(deftest build-edges-subscribe
  (testing "explicit subscribes list → :subscribe edges (known nanoids only, no self-loop)"
    (let [edges (h/build-edges [{"nanoid" "a" "subscribes" ["b" "unknown" "a"]}
                                {"nanoid" "b"}]
                               {})]
      (is (= [{:from "a" :to "b" :type :subscribe}] (vec edges))))))

(defn -main [& _]
  (let [{:keys [fail error]} (run-tests 'etzhayyim.test-haisen)]
    (System/exit (if (pos? (+ fail error)) 1 0))))
