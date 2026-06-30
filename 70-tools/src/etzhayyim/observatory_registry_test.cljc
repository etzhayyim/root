(ns etzhayyim.observatory-registry-test
  "Tests for kotoba-genome W4-live R0 registry regeneration (ADR-2606302205 D4)."
  (:require [clojure.test :refer [deftest is testing]]
            [clojure.string]
            [etzhayyim.channel :as channel]
            [etzhayyim.observatory-registry :as reg]))

(deftest parses-keyless-handles
  (testing "entity-entries reads [handle subject] pairs from the gen.ts"
    (let [es (reg/entity-entries "cable")]
      (is (= 14 (count es)))                          ; CABLE_TOTAL_COUNT
      (is (every? (fn [[h d]] (and (string? h) (string? d))) es))
      (is (some (fn [[h _]] (= "cable-2africa" h)) es))
      (is (some (fn [[_ d]] (= "Asia Direct Cable (ADC)" d)) es)))))   ; parens in subject

(deftest regenerates-first-party-disclosure-honest
  (channel/default-registry!)
  (testing "each keyless mirror → a first-party observatory actor that grew + posted (dry-run)"
    (let [r (reg/regen-ns "cable" :limit 5)]
      (is (= 14 (:total r)))
      (is (= 5 (:sampled r)))
      (is (every? #(= "etzhayyim" (:voiceOf %)) (:actors r)))          ; disclosure
      (is (every? :isObservatory (:actors r)))
      (is (every? #(= :present-only-leashed (:keyed %)) (:actors r)))  ; keyed, not keyless
      (is (every? #(= :first-party-observatory (:now %)) (:actors r)))
      (is (every? :grew? (:actors r)))                                 ; learned (genome beat)
      (is (every? :postEmitted (:actors r)))                          ; posted (dry-run)
      (is (every? :postDryRun (:actors r)))                           ; DRY-RUN — no live
      (is (every? #(clojure.string/starts-with? (:did %) "did:web:etzhayyim.com:actor:cable-") (:actors r))))))

(deftest small-namespaces-regen-fully
  (channel/default-registry!)
  (testing "cable+station+craft (49) all regenerate to first-party, all dry-run"
    (let [results (mapv #(reg/regen-ns % :limit 100) ["cable" "station" "craft"])
          total (reduce + (map :total results))]
      (is (= 49 total))                                ; 14 + 22 + 13
      (is (every? (fn [r] (every? :postDryRun (:actors r))) results))   ; nothing live
      (is (every? (fn [r] (every? #(= "etzhayyim" (:voiceOf %)) (:actors r))) results)))))

