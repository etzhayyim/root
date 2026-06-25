;; etzhayyim.test-tithe — constitutional 10% Public-Fund split invariants (bb/clj side).
;; The cljs/squint side is proven byte-for-byte against the original tithe.ts in
;; 90-docs/poc/2606251200-squint-tithe; this pins the shared .cljc on the JVM/bb side
;; (the actor/TitheRouter face) so "write once, run both" holds.
(ns etzhayyim.test-tithe
  (:require [clojure.test :refer [deftest is testing run-tests]]
            [etzhayyim.tithe :as t]))

(deftest split-tithe-math
  (testing "10% split, integer-floored"
    (is (= {:gross 1000000N :tithe 100000N :net 900000N} (t/split-tithe 1000000N)))
    (is (= {:gross 1000N :tithe 100N :net 900N} (t/split-tithe 1000N)))
    (is (= {:gross 0N :tithe 0N :net 0N} (t/split-tithe 0N))))
  (testing "constitutional no-rounding-leak: 7 micros tithe to 0, never 0.7"
    (is (= 0N (:tithe (t/split-tithe 7N))))
    (is (= 7N (:net (t/split-tithe 7N))))
    (is (= 99N (:tithe (t/split-tithe 999N)))))   ;; floor(99.9) = 99
  (testing "tithe + net always reconstructs gross (no leak/dust)"
    (doseq [g [0N 1N 7N 999N 1000N 123456789012345N]]
      (let [{:keys [gross tithe net]} (t/split-tithe g)]
        (is (= gross (+ tithe net))))))
  (testing "negative gross throws"
    (is (thrown? clojure.lang.ExceptionInfo (t/split-tithe -1N)))))

(deftest parse-micros-validation
  (is (= 123N (t/parse-micros "123")))
  (is (= 0N (t/parse-micros "0")))
  (is (= 123456789012345N (t/parse-micros "123456789012345")))
  (testing "non-numeric / signed / empty input throws"
    (is (thrown? clojure.lang.ExceptionInfo (t/parse-micros "abc")))
    (is (thrown? clojure.lang.ExceptionInfo (t/parse-micros "-1")))
    (is (thrown? clojure.lang.ExceptionInfo (t/parse-micros "")))
    (is (thrown? clojure.lang.ExceptionInfo (t/parse-micros "12.5")))))

(deftest end-to-end-parse-then-split
  (let [{:keys [tithe net]} (t/split-tithe (t/parse-micros "1000000"))]
    (is (= 100000N tithe))
    (is (= 900000N net))))

(defn -main [& _]
  (let [{:keys [fail error]} (run-tests 'etzhayyim.test-tithe)]
    (System/exit (if (pos? (+ fail error)) 1 0))))
