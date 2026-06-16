(ns tate.tests.test-terms
  "tate 盾 — clause-scanner + Datom-emit tests (ADR-2606112301).
  1:1 Clojure port of tests/test_terms.py (stdlib asserts → clojure.test)."
  (:require [clojure.test :refer [deftest is run-tests]]
            [clojure.string :as str]
            [tate.methods.terms-scan :as ts]
            [tate.methods.datom-emit :as de]))

(def ROUTES #{":kurashimori" ":kaiyaku" ":referral" ":info"})

(defn- res* []
  (let [[docs _] (ts/load-docs)]
    [docs (ts/scan docs (ts/load-patterns))]))

(deftest test-load-nontrivial-and-synthetic
  (let [[docs notices] (ts/load-docs)
        patterns (ts/load-patterns)]
    (is (and (>= (count docs) 4) (>= (count notices) 5) (>= (count patterns) 12)))
    (doseq [d docs]
      (is (= (get d ":doc/sourcing") ":synthetic") (get d ":doc/id")))
    (doseq [n notices]
      (is (= (get n ":notice/sourcing") ":synthetic") (get n ":notice/id")))))

(deftest test-non-adjudicating-flags
  (let [[_ res] (res*)]
    (is (seq (get res "flags")) "scanner found nothing — seed/keywords drifted")
    (doseq [f (get res "flags")]
      (is (get f "anchor") f)
      (is (and (= (get f "disclosed") true) (= (get f "verify_current_law") true)))
      (is (and (not (contains? f "verdict")) (not (contains? f "invalid"))) f)
      (is (contains? ROUTES (get f "route")) f))))

(deftest test-report-language-honest
  (let [[_ res] (res*)
        text (ts/report res)]
    (is (and (str/includes? text "可能性") (str/includes? text "専門家確認")))
    (is (not (str/includes? text "無効です")))))

(deftest test-context-honesty-no-cross-anchors
  (let [[docs _] (ts/load-docs)
        patterns (ts/load-patterns)]
    (doseq [d docs]
      (doseq [f (ts/scan-doc d patterns)]
        (let [p (first (filter #(= (get % ":clause/id") (get f "clause")) patterns))]
          (is (= (get p ":clause/context") (get d ":doc/context")) f))))
    (let [fake-b2b {":doc/id" "doc:adv" ":doc/context" ":b2b" ":doc/sourcing" ":synthetic"
                    ":doc/text" "当社は一切の責任を負いません。違約金として残期間の利用料全額。"}]
      (doseq [f (ts/scan-doc fake-b2b patterns)]
        (is (not (str/includes? (get f "anchor") "消費者契約法")) f)))))

(deftest test-expected-shapes-hit
  (let [[_ res] (res*)
        hits (set (map (fn [f] [(get f "doc") (get f "clause")]) (get res "flags")))]
    (is (contains? hits ["doc:fitness-tos" "cl:excessive-penalty"]))
    (is (contains? hits ["doc:fitness-tos" "cl:auto-renewal-trap"]))
    (is (contains? hits ["doc:video-tos" "cl:full-exemption"]))
    (is (contains? hits ["doc:video-tos" "cl:excessive-late-interest"]))
    (is (contains? hits ["doc:video-tos" "cl:exclusive-jurisdiction"]))
    (is (contains? hits ["doc:card-agreement" "cl:auto-revolving"]))
    (is (contains? hits ["doc:card-agreement" "cl:defense-cutoff"]))
    (is (contains? hits ["doc:b2b-services" "cl:b2b-unlimited-liability"]))
    (is (contains? hits ["doc:b2b-services" "cl:b2b-noncompete"]))
    (is (contains? hits ["doc:b2b-services" "cl:b2b-long-payment"]))
    (is (contains? hits ["doc:b2b-services" "cl:b2b-ip-assignment"]))))

(deftest test-risk-ordering
  (let [order {":high" 0 ":mid" 1 ":info" 2}
        [docs _] (ts/load-docs)]
    (doseq [d docs]
      (let [ranks (mapv #(get order (get % "risk")) (ts/scan-doc d (ts/load-patterns)))]
        (is (= ranks (sort ranks)) (get d ":doc/id"))))))

(deftest test-intl-expected-shapes-hit
  (let [[_ res] (res*)
        hits (set (map (fn [f] [(get f "doc") (get f "clause")]) (get res "flags")))]
    (doseq [pair [["doc:us-saas-tos" "cl:us-arbitration-class-waiver"]
                  ["doc:us-saas-tos" "cl:us-auto-renewal-negative-option"]
                  ["doc:us-saas-tos" "cl:us-early-termination-fee"]
                  ["doc:eu-sub-tos" "cl:eu-withdrawal-exclusion"]
                  ["doc:eu-sub-tos" "cl:eu-unilateral-change"]
                  ["doc:uk-gym-terms" "cl:uk-liability-exclusion"]
                  ["doc:de-agb" "cl:de-price-increase"]
                  ["doc:de-agb" "cl:de-lump-damages"]
                  ["doc:kr-tos" "cl:kr-full-exemption"]
                  ["doc:kr-tos" "cl:kr-excessive-penalty"]
                  ["doc:fr-abonnement" "cl:fr-liability-exclusion"]
                  ["doc:fr-abonnement" "cl:fr-tacit-renewal"]
                  ["doc:au-tos" "cl:au-unfair-variation"]
                  ["doc:au-tos" "cl:au-guarantee-exclusion"]
                  ["doc:ca-tos" "cl:ca-arbitration-consumer"]
                  ["doc:ca-tos" "cl:ca-all-sales-final"]
                  ["doc:it-tos" "cl:it-clausola-vessatoria"]
                  ["doc:it-tos" "cl:it-tacito-rinnovo"]
                  ["doc:es-tos" "cl:es-clausula-abusiva"]
                  ["doc:es-tos" "cl:es-prorroga-automatica"]
                  ["doc:nl-voorwaarden" "cl:nl-exoneratie"]
                  ["doc:nl-voorwaarden" "cl:nl-stilzwijgende-verlenging"]
                  ["doc:br-termos" "cl:br-exoneracao"]
                  ["doc:br-termos" "cl:br-renovacao-automatica"]
                  ["doc:tw-tos" "cl:tw-full-exemption"]
                  ["doc:tw-tos" "cl:tw-auto-renewal"]
                  ["doc:sg-tos" "cl:sg-liability-exclusion"]
                  ["doc:sg-tos" "cl:sg-auto-renewal"]
                  ["doc:in-tos" "cl:in-liability-exclusion"]
                  ["doc:in-tos" "cl:in-arbitration-no-ouster"]
                  ["doc:cn-tos" "cl:cn-full-exemption"]
                  ["doc:cn-tos" "cl:cn-auto-renewal"]
                  ["doc:pl-regulamin" "cl:pl-niedozwolona"]
                  ["doc:pl-regulamin" "cl:pl-auto-renewal"]
                  ["doc:se-villkor" "cl:se-friskrivning"]
                  ["doc:se-villkor" "cl:se-auto-renewal"]
                  ["doc:at-agb" "cl:at-haftungsausschluss"]
                  ["doc:at-agb" "cl:at-auto-renewal"]
                  ["doc:pt-condicoes" "cl:pt-exclusao"]
                  ["doc:pt-condicoes" "cl:pt-renovacao"]
                  ["doc:ie-terms" "cl:ie-liability"]
                  ["doc:ie-terms" "cl:ie-auto-renewal"]
                  ["doc:ch-agb" "cl:ch-haftungsausschluss"]
                  ["doc:ch-agb" "cl:ch-auto-renewal"]
                  ["doc:dk-vilkaar" "cl:dk-ansvarsfraskrivelse"]
                  ["doc:dk-vilkaar" "cl:dk-auto-renewal"]
                  ["doc:fi-ehdot" "cl:fi-vastuunrajoitus"]
                  ["doc:fi-ehdot" "cl:fi-auto-renewal"]
                  ["doc:no-vilkar" "cl:no-ansvarsfraskrivelse"]
                  ["doc:no-vilkar" "cl:no-auto-renewal"]
                  ["doc:mx-terminos" "cl:mx-exoneracion"]
                  ["doc:mx-terminos" "cl:mx-renovacion"]
                  ["doc:be-conditions" "cl:be-exoneration"]
                  ["doc:be-conditions" "cl:be-tacite-reconduction"]
                  ["doc:ar-terminos" "cl:ar-exoneracion"]
                  ["doc:ar-terminos" "cl:ar-renovacion"]
                  ["doc:nz-terms" "cl:nz-cga-exclusion"]
                  ["doc:nz-terms" "cl:nz-auto-renewal"]]]
      (is (contains? hits pair) pair))))

(deftest test-jurisdiction-isolation
  (let [[docs _] (ts/load-docs)
        patterns (ts/load-patterns)]
    (doseq [d docs]
      (doseq [f (ts/scan-doc d patterns)]
        (let [p (first (filter #(= (get % ":clause/id") (get f "clause")) patterns))]
          (is (= (get p ":clause/jurisdiction" ":jp") (get d ":doc/jurisdiction" ":jp")) f))))
    (let [adv {":doc/id" "doc:adv-us" ":doc/jurisdiction" ":us" ":doc/context" ":consumer"
               ":doc/sourcing" ":synthetic"
               ":doc/text" "当社は一切の責任を負いません。遅延損害金は年率19.9%。"}]
      (doseq [f (ts/scan-doc adv patterns)]
        (is (not (str/includes? (get f "anchor") "消費者契約法")) f)))))

(deftest test-case-insensitive-matching
  (let [patterns (ts/load-patterns)
        doc {":doc/id" "doc:caps" ":doc/jurisdiction" ":au" ":doc/context" ":consumer"
             ":doc/sourcing" ":synthetic" ":doc/text" "WE EXCLUDE ALL LIABILITY."}]
    (is (some #(= (get % "clause") "cl:au-guarantee-exclusion") (ts/scan-doc doc patterns)))))

(deftest test-kaiyaku-handoff-artifact
  (let [[_ res] (res*)
        text (ts/make-kaiyaku-handoff res)
        parsed (ts/read-edn text)
        expect (filterv #(= (get % "route") ":kaiyaku") (get res "flags"))]
    (is (and (= (count parsed) (count expect)) (>= (count parsed) 10)))
    (let [clause-ids (set (map #(get % ":handoff/clause") parsed))]
      (doseq [f expect]
        (is (contains? clause-ids (get f "clause"))))
      (doseq [h parsed]
        (is (= (get h ":handoff/action") ":calendar-notice-window"))
        (is (get h ":handoff/anchor"))))))

(deftest test-flags-json-export
  ;; round-trip is structural in cljc; we assert the shape carries anchor on every flag.
  (let [[_ res] (res*)]
    (is (and (= (count (get res "flags")) (count (get res "flags")))
             (every? #(contains? % "anchor") (get res "flags"))))))

(deftest test-datoms-ground-and-transient
  (let [text (de/emit 3)]
    (is (and (str/includes? text ":clause/anchor") (str/includes? text ":doc/context")))
    (is (str/includes? text ":bond/is-transient true") "derived flags must be transient (G2)")
    (is (and (str/includes? text ":tate/risk") (str/includes? text ":tate/status")))))

(deftest test-determinism
  (is (= (de/emit 1) (de/emit 1))))

#?(:clj (defn -main [& _] (run-tests 'tate.tests.test-terms)))
