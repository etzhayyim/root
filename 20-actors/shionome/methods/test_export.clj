#!/usr/bin/env bb
;; Clojure port of test_export.py — 潮目 (shionome) → kanae render export. ADR-2606072200.
(ns shionome.methods.test-export
  "test_export.clj — 潮目 (shionome) → kanae render export. ADR-2606072200."
  (:require [clojure.test :refer [deftest is run-tests]]
            [clojure.string :as str]
            [cheshire.core :as json]
            [shionome.methods.export :as ex]
            [shionome.methods.weave :as w]
            [shionome.methods.edn :as sedn]))

(def ^:private SEED
  (str (-> *file* java.io.File. .getAbsoluteFile .getParentFile .getParentFile
           (java.io.File. "data/seed-capital-flow-graph.kotoba.edn"))))

(defn- g []
  (w/weave (sedn/load-edn SEED)))

;; ── helpers ──────────────────────────────────────────────────────────────────

(defmacro ^:private expect-raises
  "Assert that body throws an exception whose message contains `contains-str`."
  [contains-str & body]
  `(let [caught# (try ~@body nil (catch Exception e# e#))]
     (is (some? caught#) "expected an exception, none raised")
     (when (seq ~contains-str)
       (is (str/includes? (ex-message caught#) ~contains-str)
           (str "raised but missing " (pr-str ~contains-str) ": " (ex-message caught#))))))

;; ── tests ────────────────────────────────────────────────────────────────────

(deftest test-to-kanae-flow-ok
  (let [e (ex/to-kanae-flow {":flow/id" "f" ":flow/source" "a" ":flow/target" "b"
                              ":flow/kind" ":rotation" ":flow/magnitude" 5.0
                              ":flow/unit" "usd-bn" ":flow/sources" ["x" "y"]})]
    (is (= "rotation" (get e "flowType")))
    (is (true? (get e "noTrade")))))

(deftest test-to-kanae-flow-rejects-observation-kind
  (expect-raises "observation"
    (ex/to-kanae-flow {":flow/kind" ":cross-correlation"})))

(deftest test-to-kanae-flows-skips-observations
  (let [kf (ex/to-kanae-flows (g))]
    (is (= 3 (get kf "skipped_count")))   ; 2 correlation + 1 price-move
    (is (= 8 (count (get kf "flows"))))))

(deftest test-render-payload-flags
  (let [p (ex/render-payload (w/concentration (g)))]
    (is (true? (get p "isMirror")))
    (is (true? (get p "noTrade")))
    (is (= "shionome" (get p "actor")))))

(deftest test-render-json-serializable
  (let [s (ex/render-json (w/concentration (g)))
        obj (json/parse-string s)]
    (is (= "risk-on" (get-in obj ["regime" "regime"])))
    (is (vector? (get obj "inflow_shares")))))

(deftest test-render-payload-has-no-per-bucket-score
  ;; G4 — the render payload must never expose a per-bucket rating/signal/score
  (let [s (str/lower-case (ex/render-json (w/concentration (g))))]
    (doseq [forbidden ["\"rating\"" "\"signal\"" "\"target_price\"" "\"recommendation\""]]
      (is (not (str/includes? s forbidden))
          (str "forbidden token found: " forbidden)))))

(when (= *file* (System/getProperty "babashka.file"))
  (let [{:keys [fail error]} (clojure.test/run-tests 'shionome.methods.test-export)]
    (System/exit (if (zero? (+ fail error)) 0 1))))
