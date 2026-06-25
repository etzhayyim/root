(ns akashi.methods.test-manifest-invariants
  "akashi — manifest invariants (ported from the manifest-reading half of
  70-tools/scripts/audit/test_akashi_invariants.py). Reads manifest.edn (:actor/manifest
  blob); the jsonld is retired. The lexicon-shape + Python cell-scaffold (import-raises)
  invariants stay in the Python audit suite."
  (:require [clojure.test :refer [deftest is run-tests]]
            [clojure.string :as str] [clojure.edn :as edn]))

(def ^:private here (.getParentFile (java.io.File. ^String *file*)))
(def ^:private actor-dir (.getParentFile here))
(def ^:private root (.. actor-dir getParentFile getParentFile))
(def ^:private lexdir (java.io.File. root "00-contracts/lexicons/com/etzhayyim/akashi"))
(defn- manifest [] (:actor/manifest (edn/read-string (slurp (java.io.File. actor-dir "manifest.edn")))))

(def ^:private discipline-keys
  #{"passiveOnly" "sourceProvenanceMandatory" "nonAdjudicating" "noPoliticalProfiling"
    "noTargetLists" "openMethod" "sourcePolicyRequired" "noAdSdk" "noCommercialAdIntel"
    "publicRecordMinimization" "murakumoOnlyInference" "transparentForce" "malakBridgeReview"})

(def ^:private expected-lexicons
  #{"sourcePolicySnapshot" "adDisclosureSnapshot" "advertiserIdentity" "creativeDisclosure"
    "deliveryDisclosure" "landingEvidence" "adDisclosureLink" "methodNote"
    "adTransparencyReport" "malakEvidenceCandidate"})

(def ^:private cell-names
  #{"akashi_source_registry" "akashi_disclosure_fetch" "akashi_normalize_creative"
    "akashi_landing_evidence" "akashi_cross_platform_link" "akashi_transparency_report"
    "akashi_malak_evidence_bridge"})

(deftest manifest-discipline-and-namespaces-match-disk
  (let [m (manifest)
        discipline (get m "constitutionalDiscipline")]
    (is (= (count discipline) 13))
    (doseq [k discipline-keys] (is (contains? discipline k) (str "missing discipline key " k)))
    (let [ns (get m "lexiconNamespaces")]
      (is (= (count ns) (count expected-lexicons)))
      (is (= (set (map #(last (str/split % #"\.")) ns)) expected-lexicons))
      (doseq [leaf expected-lexicons]
        (is (.exists (java.io.File. lexdir (str leaf ".json"))) (str "missing lexicon " leaf))))))

(deftest manifest-cell-modules-match-cell-names
  (is (= (set (map #(last (str/split (get % "module") #"\.")) (get (manifest) "cells")))
         cell-names)))

(defn -main [& _]
  (let [r (run-tests 'akashi.methods.test-manifest-invariants)]
    (System/exit (if (zero? (+ (:fail r) (:error r))) 0 1))))
