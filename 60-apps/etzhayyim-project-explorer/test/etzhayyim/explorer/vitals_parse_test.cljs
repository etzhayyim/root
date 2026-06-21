(ns etzhayyim.explorer.vitals-parse-test
  "Reproduces (or clears) the Organism-view 'Could not load: vitals' failure the
   visual react loop surfaced: parse the REAL vitals snapshot with the exact
   cljs.reader logic data/fetch-edn uses."
  (:require [cljs.test :refer-macros [deftest is testing]]
            [cljs.reader :as edn]
            ["fs" :as fs]))

(def vitals-text
  (.readFileSync fs "public/organism/vitals.kotoba.edn" "utf8"))

(deftest vitals-parses-like-fetch-edn
  (testing "cljs.reader parses the real vitals snapshot without throwing"
    (let [parsed (binding [edn/*default-data-reader-fn* (atom (fn [_t v] v))]
                   (edn/read-string vitals-text))]
      (is (some? parsed))
      (is (vector? parsed))
      (is (pos? (count parsed))))))
