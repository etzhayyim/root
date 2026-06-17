(ns maps.methods.test-methods
  "test_methods.py — kotoba-native methods tests (ADR-2606064500). unittest → clojure.test.
  1:1 port; the Python __main__ unittest.main() runner is omitted.

  Reads the seed EDN + sample JSON fixtures via *file*-relative paths (host I/O behind #?(:clj))."
  (:require [clojure.test :refer [deftest is]]
            [clojure.string :as str]
            [maps.methods.analyze :as analyze]
            [maps.methods.ingest :as ingest]))

#?(:clj
   (def ^:private here (-> (java.io.File. (str *file*)) .getAbsoluteFile .getParentFile)))
#?(:clj
   (def ^:private root (.getParentFile here)))
#?(:clj
   (def ^:private seed (str (java.io.File. (java.io.File. root "data") "seed-spatial-graph.kotoba.edn"))))
#?(:clj
   (def ^:private sample (str (-> (java.io.File. root "data") (java.io.File. "ingest") (java.io.File. "sample-vertex-spatial.json")))))

;; ── TestAnalyze ──────────────────────────────────────────────────────────────
#?(:clj
   (defn- analyze-fixture []
     (let [rows (analyze/load-edn seed)
           [features rels aliases] (analyze/classify rows)
           a (analyze/analyze features rels aliases)]
       {:features features :rels rels :aliases aliases :a a})))

(deftest test-seed-classifies
  #?(:clj
     (let [{:keys [features rels aliases]} (analyze-fixture)]
       (is (>= (count features) 10))
       (is (>= (count rels) 1))
       (is (>= (count aliases) 1)))))

(deftest test-every-feature-has-sourcing
  #?(:clj
     (let [{:keys [features]} (analyze-fixture)]
       (doseq [f (vals features)]
         (is (contains? f ":feature/sourcing") (get f ":feature/id"))))))

(deftest test-labels-collapsed
  #?(:clj
     (let [{:keys [a]} (analyze-fixture)]
       (is (contains? (get a "label_count") ":building"))
       (is (contains? (get a "label_count") ":station")))))

(deftest test-coverage-fraction-is-honest-and-tiny
  #?(:clj
     (let [{:keys [a]} (analyze-fixture)
           den (analyze/h3-cells-at-res 6)]
       (is (= den 14117882))
       (is (> (count (get a "cells_r6")) 0))
       (is (< (/ (double (count (get a "cells_r6"))) den) 1e-3)))))

(deftest test-bbox-and-anchor
  #?(:clj
     (let [{:keys [a]} (analyze-fixture)]
       (is (some? (get a "bbox")))
       (is (some? (get a "densest")))
       (let [[[la lo] _n] (get a "densest")]
         (is (< (Math/abs (- (double la) 35.68)) 0.1))
         (is (< (Math/abs (- (double lo) 139.76)) 0.1))))))

(deftest test-report-renders
  #?(:clj
     (let [{:keys [features a]} (analyze-fixture)
           rep (analyze/render-report features a)]
       (is (str/includes? rep "coverage report"))
       (is (str/includes? rep "res-6"))
       (let [dat (analyze/render-datoms a)]
         (is (str/includes? dat ":coverage/feature-count"))
         (is (str/includes? dat ":coverage/derived true"))))))

;; ── TestIngest ───────────────────────────────────────────────────────────────
#?(:clj
   (defn- export-fixture [] (ingest/parse-json (slurp sample))))

(deftest test-label-map
  (is (= (ingest/label* "Building") ":building"))
  (is (= (ingest/label* "Station") ":station"))
  (is (= (ingest/label* "LegalEntity") ":legal-entity"))
  (is (= (ingest/label* "WeirdThing") ":weirdthing")))

(deftest test-normalize-row
  #?(:clj
     (let [row (first (get (export-fixture) "rows"))   ; Marunouchi Building
           f (ingest/normalize-row row)]
       (is (= (get f ":feature/label") ":building"))
       (is (= (get f ":feature/height-m") 179.0))
       (is (= (get f ":feature/levels") 37))
       (is (= (get f ":feature/sourcing") ":representative"))
       (is (contains? f ":feature/geometry"))
       (is (some? (ingest/parse-json (get f ":feature/geometry")))))))

(deftest test-props-bag-excludes-promoted-keys
  #?(:clj
     (let [row (first (get (export-fixture) "rows"))
           f (ingest/normalize-row row)]
       (when (contains? f ":feature/props")
         (let [bag (ingest/parse-json (get f ":feature/props"))]
           (is (not (contains? bag "heightM")))
           (is (not (contains? bag "levels")))
           (is (not (contains? bag "geometry"))))))))

(deftest test-normalize-batch
  #?(:clj
     (let [[feats stamped unstamped] (ingest/normalize (export-fixture))]
       (is (= (count feats) 4))
       (is (= (+ stamped unstamped) 4)))))

(deftest test-to-kg-batch-shape
  #?(:clj
     (let [[feats _ _] (ingest/normalize (export-fixture))
           batch (ingest/to-kg-batch feats)
           e (first (get batch "entities"))]
       (is (contains? batch "entities"))
       (doseq [k ["id" "type" "label_en" "claims" "relations"]]
         (is (contains? e k)))
       (is (= (get e "type") "maps-feature"))
       (is (not (some #(= (get % "pred") "feature/id") (get e "claims")))))))

(deftest test-push-gate-refuses-without-operator
  ;; G7 — invoke main(--push) with the gate OFF; main throws the G7 refusal before any network
  ;; call. Mirrors the Python os.environ.pop("MAPS_OPERATOR_GATE") by binding *getenv* to a map
  ;; that omits the gate (env access is behind that indirection on the JVM).
  #?(:clj
     (binding [ingest/*getenv* (constantly nil)]
       (let [ex (try (ingest/main ["ingest.py" "--export" sample "--push"]) nil
                     (catch clojure.lang.ExceptionInfo e e)
                     (catch Exception e e))]
         (is (some? ex))
         (is (str/includes? (str (or (ex-message ex) ex)) "G7"))))))

(deftest test-push-gate-refuses-without-auth-even-when-gated
  ;; With the gate ON but no KOTOBA_AUTH/ENDPOINT, --push still refuses (G4 no-server-key).
  ;; Mirrors the Python env mutation via the *getenv* indirection.
  #?(:clj
     (binding [ingest/*getenv* (fn [k] (when (= k "MAPS_OPERATOR_GATE") "1"))]
       (let [ex (try (ingest/main ["ingest.py" "--export" sample "--push"]) nil
                     (catch clojure.lang.ExceptionInfo e e)
                     (catch Exception e e))]
         (is (some? ex))
         (is (str/includes? (str/lower-case (str (or (ex-message ex) ex))) "no server key"))))))
