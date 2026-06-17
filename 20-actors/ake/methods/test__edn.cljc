(ns ake.methods.test--edn
  "test__edn.cljc — 朱 (ake) EDN reader. 1:1 Clojure port of `methods/test__edn.py`.
  `parse-edn` is pure over a string and runs on every platform; the `load-edn` file edge is
  #?(:clj). Pins the atom-level reads the whole seed/ontology load depends on."
  (:require [clojure.test :refer [deftest is run-tests]]
            [ake.methods._edn :as edn]
            #?(:clj [clojure.java.io :as io])))

(deftest test-reads-true-false-nil
  (is (= [true false nil] (edn/parse-edn "[true false nil]"))))

(deftest test-reads-int-and-float-and-negative
  (is (= [1 2.5 -3 0.65] (edn/parse-edn "[1 2.5 -3 0.65]"))))

(deftest test-keyword-stays-a-colon-string-and-bareword-falls-through-to-string
  (is (= ":edit/op" (edn/parse-edn ":edit/op")))
  (is (= "org.corp.x" (edn/parse-edn "org.corp.x"))))

(deftest test-reads-escaped-string
  (is (= "a \"q\" b" (edn/parse-edn "\"a \\\"q\\\" b\""))))

(deftest test-reads-nested-map-and-vector-with-comments-and-commas
  (let [src "; a leading comment
    {:edit/id \"e1\", :edit/tags [:a :b],
     :edit/ok true :edit/n 3}"]
    (is (= {":edit/id" "e1" ":edit/tags" [":a" ":b"] ":edit/ok" true ":edit/n" 3}
           (edn/parse-edn src)))))

#?(:clj
   (deftest test-load-edn-reads-a-file
     (let [f (java.io.File/createTempFile "ake-edn" ".edn")]
       (try
         (spit f "{:k [1 2.5 true nil \"s\"]}")
         (is (= {":k" [1 2.5 true nil "s"]} (edn/load-edn (.getPath f))))
         (finally (.delete f))))))

#?(:clj (defn -main [& _] (run-tests 'ake.methods.test--edn)))
