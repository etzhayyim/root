;; test_standard.clj — matsurigoto COFOG e-gov standard: validate + coverage parity with
;; standard.py + charter-invariant detection. Run via `bb test:matsurigoto`. ADR-2606142300.
(ns matsurigoto.methods.test-standard
  (:require [clojure.test :refer [deftest is testing run-tests]]
            [clojure.string :as str]
            [matsurigoto.methods.standard :as std]))

(def ^:private doc (std/load-standard))

(deftest standard-validates
  (testing "the shipped COFOG standard passes structural + charter validation (0 errors)"
    (is (= [] (std/validate doc)))))

(deftest coverage-parity
  (testing "honest coverage figures match standard.py goldens"
    (let [c (std/coverage doc)]
      (is (= 3 (:divisions-covered c)))
      (is (= 10 (:divisions-total c)))
      (is (= 6 (:groups-covered c)))
      (is (= 69 (:groups-total c)))
      (is (= 22 (:services-total c)))
      (is (= 0 (:executable-services c)))                   ; R0 — all modules raise
      (is (= 8 (:countries c)))
      (is (= [":civil-registry" ":corp-registry" ":identity-credential" ":taxation"]
             (sort (:required-domains-covered c))))
      (is (= [] (:required-domains-missing c)))
      (is (= {":taxation" 6 ":civil-registry" 5 ":corp-registry" 3 ":identity-credential" 4
              ":social-protection" 3 ":interop" 1} (:by-domain c)))
      (is (= {":reference-impl" 15 ":planned" 6 ":standard-draft" 1} (:by-maturity c))))))

(deftest charter-invariant-detection
  (testing "validate catches a G1 invariant violation (a service that claims a server-held key)"
    (let [poisoned (update doc :services
                           (fn [ss] (cons (assoc-in (first ss) [:egov.service/invariants :server-held-authority] true)
                                          (rest ss))))
          errs (std/validate poisoned)]
      (is (some #(str/includes? % "invariant :server-held-authority") errs)))))

(deftest authority-separation-detection
  (testing "validate catches a G3 violation (a polity not governed by the Council)"
    (let [polities (:polity-profiles doc)]
      (when (seq polities)
        (let [poisoned (assoc doc :polity-profiles
                              (cons (assoc (first polities) :polity-profile/operated-by ":adopting-government")
                                    (rest polities)))
              errs (std/validate poisoned)]
          (is (some #(str/includes? % ":etzhayyim-council/:sovereign-governance") errs))))
      ;; allow-list itself is keyword-string based
      (is (contains? std/allowed-operated-by ":etzhayyim-council")))))

(deftest report-renders
  (testing "render-report produces a markdown coverage report"
    (let [r (std/render-report doc (std/coverage doc) (std/validate doc))]
      (is (str/includes? r "✅ PASS"))
      (is (str/includes? r "divisions covered: **3/10**"))
      (is (str/includes? r "standardized services: **22**")))))

(when (= *file* (System/getProperty "babashka.file"))
  (let [{:keys [fail error]} (run-tests 'matsurigoto.methods.test-standard)]
    (System/exit (if (pos? (+ fail error)) 1 0))))
