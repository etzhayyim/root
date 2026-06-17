(ns watari.methods.test-ingest
  "test_ingest.py — watari 渡り offline AIS/ADS-B normalizer tests. ADR-2606041827.
  1:1 Clojure port of methods/test_ingest.py (pytest assert → clojure.test/is).

  Covers offline normalization (public-broadcast → :craft/:craft.fix records, all
  :representative) AND the G7 outward gate: a live network fetch is REFUSED unless the operator
  attestation env var is set. Fixtures load via *file*-relative paths behind #?(:clj …)."
  (:require [clojure.test :refer [deftest is run-tests]]
            [clojure.set]
            #?(:clj [clojure.java.io :as io])
            [watari.methods.ingest :as ingest]))

#?(:clj (def ^:private batch-path
          (-> *file* io/file .getAbsoluteFile .getParentFile .getParentFile
              (io/file "data" "ingest" "sample-batch.json"))))

#?(:clj (defn- batch [] (ingest/load-json batch-path)))

(deftest test-normalize-emits-vessel-and-aircraft-craft
  (let [[craft fixes] (ingest/normalize (batch))
        kinds (set (map #(get % ":craft/kind") (vals craft)))]
    (is (and (contains? kinds ":vessel") (contains? kinds ":aircraft")))
    (is (>= (count fixes) (count craft)))))   ;; at least one fix per craft

(deftest test-normalized-records-are-representative
  (let [[craft fixes] (ingest/normalize (batch))]
    (is (every? #(= ":representative" (get % ":craft/sourcing")) (vals craft)))
    (is (every? #(= ":representative" (get % ":craft.fix/sourcing")) fixes))))

(deftest test-fix-carries-source-tag
  (let [[_ fixes] (ingest/normalize (batch))
        sources (set (map #(get % ":craft.fix/source") fixes))]
    (is (clojure.set/subset? sources #{":ais" ":adsb"}))))   ;; only public-broadcast sources

(deftest test-g4-no-person-fields-in-normalized-output
  (let [[craft fixes] (ingest/normalize (batch))]
    (doseq [rec (concat (vals craft) fixes)]
      (doseq [k (keys rec)]
        (is (not (.contains ^String k ":person")))))))   ;; craft, never a person (G4)

(deftest test-g7-live-fetch-refused-without-operator-gate
  ;; default mode (no WATARI_OPERATOR_GATE) must REFUSE --live
  (is (thrown? #?(:clj Exception :cljs js/Error) (ingest/main ["ingest.py" "--live"]))
      "--live must refuse without the operator gate"))

#?(:clj
   (do
     (defn -main [& _] (run-tests 'watari.methods.test-ingest))
     (when (= *file* (System/getProperty "babashka.file")) (-main))))
