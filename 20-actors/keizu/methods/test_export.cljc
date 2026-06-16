(ns keizu.methods.test-export
  "test_export.py — 系図 (keizu) → kanae render payload + round-trip. ADR-2606066000.
  1:1 Clojure port (stdlib _t harness → clojure.test). Loads the committed :representative seed
  via a *file*-relative path behind #?(:clj …); JSON round-trip via the keizu.methods.edn reader
  (render-json emits a sorted-key JSON string)."
  (:require [clojure.test :refer [deftest is run-tests]]
            #?(:clj [keizu.methods.edn :as kedn])
            #?(:clj [cheshire.core :as json])
            [keizu.methods.export :as export]
            [keizu.methods.bridge :as bridge]
            [keizu.methods.weave :as w]))

;; SEED = parents[1]/data/seed-relation-graph.kotoba.edn (keizu/data; *file* = keizu/methods/…)
#?(:clj
   (def ^:private SEED
     (java.io.File.
      (java.io.File. (.getParentFile (.getParentFile (java.io.File. ^String *file*))) "data")
      "seed-relation-graph.kotoba.edn")))

#?(:clj (defn- g [] (w/weave (kedn/load-edn SEED))))

;; JSON parse of the render-json string — must round-trip through real JSON (no sets/tuples),
;; mirroring the Python `json.loads(s)`.
#?(:clj (defn- parse-json [s] (json/parse-string s)))

(deftest test-fiscal-money-maps-to-kanae-flow
  (let [f (export/to-kanae-flow {":money/id" "m1" ":money/kind" ":procurement-award"
                                 ":money/payer" "a" ":money/payee" "b" ":money/amount" 100.0
                                 ":money/currency" "JPY" ":money/sources" ["u" "v"]})]
    (is (= "procurement" (get f "flowType")))
    (is (= "a" (get f "donor")))
    (is (= "b" (get f "recipient")))))

(deftest test-political-donation-not-a-kanae-flow
  (is (thrown-with-msg? #?(:clj Exception :cljs js/Error) #"not a kanae fiscal flow"
                        (export/to-kanae-flow {":money/id" "m" ":money/kind" ":political-donation"}))))

(deftest test-to-kanae-flows-skips-donations
  #?(:clj
     (let [kf (export/to-kanae-flows (g))]
       ;; the seed has 1 political-donation (m-donation-jp-1) → skipped, the rest exported
       (is (= 1 (get kf "skipped_count")))
       (is (= (dec (count (get (g) "money"))) (count (get kf "flows"))))
       (is (every? #(some #{(get % "flowType")} (vals export/KEIZU-KIND-TO-KANAE))
                   (get kf "flows"))))
     :cljs (is true)))

(deftest test-round-trip-through-bridge-preserves-kind
  ;; keizu :money → kanae flow → bridge back → keizu :money, kind + amount preserved
  (doseq [kind ["procurement-award" "subsidy" "grant" "budget-outlay"]]
    (let [m {":money/id" "x" ":money/kind" (str ":" kind) ":money/payer" "p"
             ":money/payee" "q" ":money/amount" 42.0 ":money/currency" "JPY"
             ":money/sources" ["u" "v"]}
          flow (assoc (export/to-kanae-flow m) "sources" ["u" "v"]) ;; bridge requires ≥2
          back (bridge/bridge-kanae-flow flow)]
      (is (= (str ":" kind) (get back ":money/kind")) (str kind " " (get back ":money/kind")))
      (is (= 42.0 (get back ":money/amount"))))))

(deftest test-render-payload-is-json-serializable
  #?(:clj
     (let [c (w/concentration (g))
           s (export/render-json c)
           obj (parse-json s)] ;; must round-trip through JSON with no sets/tuples
       (is (= "keizu" (get obj "actor")))
       (is (true? (get obj "isMirror")))
       (is (true? (get obj "nonAdjudicating")))
       (is (>= (get-in obj ["counts" "node_count"]) 15)))
     :cljs (is true)))

(deftest test-render-payload-empty-graph-safe
  #?(:clj
     (let [s (export/render-json (w/concentration (w/weave {})))
           obj (parse-json s)]
       (is (= 0 (get-in obj ["counts" "money_count"])))
       (is (= [] (get obj "money_by_payee")))
       (is (= 0 (get-in obj ["statement_index" "count"]))))
     :cljs (is true)))

#?(:clj (defn -main [& _] (run-tests 'keizu.methods.test-export)))
