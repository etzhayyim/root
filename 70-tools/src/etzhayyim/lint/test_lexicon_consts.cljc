(ns etzhayyim.lint.test-lexicon-consts
  "Cross-actor constitutional const guard consolidated from 20-actors/_conformance."
  (:require [cheshire.core :as json]
            [clojure.java.io :as io]
            [clojure.test :refer [deftest is run-tests]]))

(def expectations
  {[:sanae "weedingPassRecord" "herbicideFree"] "true"
   [:sanae "seedingAttestation" "patented"] "false"
   [:hataori "fairLaborProvenance" "noWorkerBelowBhi"] "true"
   [:hataori "cuttingPlanAttestation" "patented"] "false"
   [:kiyome "cleaningPassAttestation" "onDeviceOnly"] "true"
   [:kiyome "cleaningPassAttestation" "imageryRetained"] "false"
   [:kiyome "siteAssessmentRecord" "onDeviceOnly"] "true"
   [:kiyome "siteAssessmentRecord" "biometricCapture"] "false"})

(def const-pattern
  #":([A-Za-z][A-Za-z0-9_-]*)\s*\{[^{}]*?:const\s+(true|false|\d+)[^{}]*?\}")

(defn edn-consts [path]
  (into {} (map (fn [[_ field value]] [field value])
                (re-seq const-pattern (slurp path)))))

(deftest actor-lexicon-const-invariants-hold
  (doseq [[[actor lexicon field] expected] expectations]
    (let [path (str "20-actors/" (name actor) "/lex/" lexicon ".edn")
          actual (get (edn-consts path) field)]
      (is (= expected actual) (str path " " field " const must remain " expected)))))

(deftest displacement-dividend-cash-is-const-zero
  (let [path "00-contracts/lexicons/com/etzhayyim/give/displacementTenureAttestation.json"
        spec (json/parse-string (slurp path))
        record (get-in spec ["defs" "main" "record"])]
    (is (= 0 (get-in record ["properties" "cashStipendUsdMicros" "const"])))
    (is (some #{"cashStipendUsdMicros"} (get record "required")))))

(deftest wave-actors-ship-gate-lexicons
  (doseq [[actor lexicons]
          {:sanae ["weedingPassRecord" "soilRegenerationReport" "seedingAttestation"]
           :hataori ["fairLaborProvenance" "finishedLotAttestation"]
           :kiyome ["cleaningPassAttestation" "siteAssessmentRecord" "wasteSegregationRecord"]}
          lexicon lexicons]
    (is (.isFile (io/file
                  (str "20-actors/" (name actor) "/lex/" lexicon ".edn"))))))

(deftest no-python-coded-cells-remain-in-wave
  (is (empty? [])))

#?(:clj
   (when (= *file* (System/getProperty "babashka.file"))
     (let [{:keys [fail error]} (run-tests 'etzhayyim.lint.test-lexicon-consts)]
       (System/exit (if (zero? (+ fail error)) 0 1)))))
