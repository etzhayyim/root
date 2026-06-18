#!/usr/bin/env bb
;; Clojure port of test_grounding.py — 潮目 (shionome) stock-layer entity-grounding bridge.
(ns shionome.methods.test-grounding
  "test_grounding.clj — 潮目 (shionome) stock-layer entity-grounding bridge. ADR-2606072200."
  (:require [clojure.test :refer [deftest is testing run-tests]]
            [shionome.methods.grounding :as g]))

(def ^:private ROOT
  (-> *file* java.io.File. .getAbsoluteFile .getParentFile
      .getParentFile .getParentFile .getParentFile))

;; ── kabuto constituent extraction ────────────────────────────────────────────────
(defn- kab-fixture []
  [{":company/id"              "org.corp.us.apple"
    ":company/name"            "Apple"
    ":company/ticker"          "AAPL"
    ":company/country"         "US"
    ":company/sector"          ":electronics"
    ":company/market-cap-busd" 3300.0
    ":company/sourcing"        ":representative"}
   {":company/id"              "org.corp.tw.tsmc"
    ":company/name"            "TSMC"
    ":company/ticker"          "2330.TW"
    ":company/market-cap-busd" 950.0
    ":company/sourcing"        ":representative"}
   {":company/id"     "org.corp.jp.x"
    ":company/name"   "Unsized Co"
    ":company/ticker" "9999.T"}                    ; no market-cap
   {":address/of" "org.corp.us.apple"
    ":address/city" "Cupertino"}                   ; NOT a company record
   {":supply.edge/from" "a" ":supply.edge/to" "b"} ; NOT a company record
   ])

(deftest test-kabuto-filters-non-company-records
  (let [cons (g/kabuto-equity-constituents (kab-fixture))]
    (is (= 3 (count cons)))   ; 3 companies; address + supply-edge skipped
    (is (= #{"Apple" "TSMC" "Unsized Co"} (set (map #(get % "name") cons))))))

(deftest test-kabuto-parses-size-and-sector
  (let [cons-map (into {} (map (fn [c] [(get c "name") c])
                               (g/kabuto-equity-constituents (kab-fixture))))]
    (is (= 3300.0 (get (get cons-map "Apple") "market_cap_busd")))
    (is (= "electronics" (get (get cons-map "Apple") "sector")))  ; keyword normalized
    (is (nil? (get (get cons-map "Unsized Co") "market_cap_busd")))))

;; ── hokorobi institution extraction ──────────────────────────────────────────────
(defn- hok-fixture []
  [{":organism/id"       "fin.inst.jpmorgan"
    ":organism/kind"     ":institution"
    ":organism/label"    "JPMorgan Chase"
    ":inst/sector"       ":bank"
    ":inst/sii"          ":g-sib"
    ":inst/jurisdiction" "US"
    ":organism/sourcing" ":authoritative"}
   {":organism/id"       "fin.inst.allianz"
    ":organism/kind"     ":institution"
    ":organism/label"    "Allianz"
    ":inst/sector"       ":insurer"
    ":inst/sii"          ":large"
    ":inst/jurisdiction" "DE"
    ":organism/sourcing" ":authoritative"}
   {":organism/id"       "fin.inst.regional"
    ":organism/kind"     ":institution"
    ":organism/label"    "Regional bank"
    ":inst/sector"       ":bank"
    ":inst/sii"          ":mid"
    ":inst/jurisdiction" "US"
    ":organism/sourcing" ":representative"}
   {":organism/id"   "risk.leverage"
    ":organism/kind" ":risk-source"}                ; NOT an institution
   {":en/from" "a" ":en/to" "b" ":en/risk-load" 0.7} ; an edge, NOT an institution
   ])

(deftest test-hokorobi-filters-to-institutions
  (let [insts (g/hokorobi-institutions (hok-fixture))]
    (is (= 3 (count insts)))  ; risk-source + edge skipped
    (is (= #{"JPMorgan Chase" "Allianz" "Regional bank"}
           (set (map #(get % "label") insts))))))

(deftest test-systemic-overlay-counts-and-sourcing
  (let [ov (g/systemic-overlay (g/hokorobi-institutions (hok-fixture)))]
    (is (= 3 (get ov "institutions")))
    (is (= {"bank" 2 "insurer" 1} (get ov "by_sector")))
    (is (= 2 (get ov "authoritative")))
    (is (= 1 (get ov "representative")))
    (is (true? (get ov "no_trade_notice")))))

;; ── equities grounding math (the honesty contract) ───────────────────────────────
(deftest test-ground-equities-value-coverage-math
  (let [cons (g/kabuto-equity-constituents (kab-fixture))
        ge   (g/ground-equities 115.0 cons 55000)]
    (is (= 3 (get ge "grounded_entities")))
    (is (= 2 (get ge "entities_with_size")))
    ;; (3300 + 950) busd = 4.25 tn → 4.25 / 115
    (is (< (Math/abs (- (get ge "grounded_market_cap_usd_tn") 4.25)) 1e-9))
    (is (< (Math/abs (- (get ge "value_coverage_of_layer")
                        (/ (Math/round (* (/ 4.25 115.0) 10000.0)) 10000.0)))
           1e-9))))

(deftest test-ground-equities-value-coverage-is-lower-bound
  ;; one sized + one unsized company → coverage is explicitly a lower bound
  (let [ge (g/ground-equities 115.0 (g/kabuto-equity-constituents (kab-fixture)))]
    (is (true? (get ge "value_coverage_is_lower_bound")))))

(deftest test-ground-equities-count-coverage-fraction
  (let [ge (g/ground-equities 115.0 (g/kabuto-equity-constituents (kab-fixture)) 55000)]
    (is (= "representative" (get ge "universe_sourcing")))  ; honesty: not a live count
    (is (< (Math/abs (- (get ge "count_coverage_of_universe")
                        (/ (Math/round (* (/ 3.0 55000.0) 100000.0)) 100000.0)))
           1e-9))))

(deftest test-ground-equities-top-constituents-sorted
  (let [ge   (g/ground-equities 115.0 (g/kabuto-equity-constituents (kab-fixture)))
        tops (get ge "top_constituents")]
    (is (= "Apple" (get (first tops) "name")))
    (is (= "TSMC"  (get (second tops) "name")))))

(deftest test-ground-equities-no-trade-notice
  (is (true? (get (g/ground-equities 115.0 []) "no_trade_notice"))))

(deftest test-ground-equities-empty-is-zero-not-crash
  (let [ge (g/ground-equities 115.0 [])]
    (is (= 0 (get ge "grounded_entities")))
    (is (= 0.0 (get ge "value_coverage_of_layer")))))

;; ── full report + ungrounded honesty ─────────────────────────────────────────────
(defn- pyramid-fixture []
  {"layers" [{"asset_class" "equities"    "usd_tn" 115.0}
             {"asset_class" "gold"        "usd_tn"  16.0}
             {"asset_class" "derivatives" "usd_tn" 600.0}]})

(deftest test-ground-full-report-shape
  (let [rep (g/ground (pyramid-fixture) (kab-fixture) (hok-fixture))]
    (doseq [k ["equities" "systemic_institutions_overlay" "ungrounded_layers" "summary"]]
      (is (contains? rep k)))
    (is (true? (get-in rep ["summary" "no_trade_notice"])))))

(deftest test-ground-names-ungrounded-layers
  (let [rep (g/ground (pyramid-fixture) (kab-fixture) (hok-fixture))]
    ;; equities is grounded (kabuto present); gold + derivatives are NOT
    (is (not (contains? (set (get rep "ungrounded_layers")) "equities")))
    (is (= #{"gold" "derivatives"} (set (get rep "ungrounded_layers"))))
    (is (= 1 (get-in rep ["summary" "layers_with_entity_grounding"])))
    (is (= 3 (get-in rep ["summary" "pyramid_layers"])))))

(deftest test-ground-total-named-entities
  (let [rep (g/ground (pyramid-fixture) (kab-fixture) (hok-fixture))]
    (is (= 6 (get-in rep ["summary" "total_named_entities"])))))  ; 3 cos + 3 institutions

(deftest test-no-kabuto-means-equities-ungrounded
  ;; fail-open: no kabuto ledger → equities falls into ungrounded, no crash
  (let [rep (g/ground (pyramid-fixture) [] (hok-fixture))]
    (is (contains? (set (get rep "ungrounded_layers")) "equities"))
    (is (= 0 (get-in rep ["summary" "layers_with_entity_grounding"])))))

;; ── kanjō disclosure depth (equities layer enrichment) ───────────────────────────
(defn- kanjo-fixture []
  [{":fin.filing/id"          "fil.a"
    ":fin.filing/company"     "org.corp.us.apple"
    ":fin.filing/fiscal-year" 2024}
   {":fin.filing/id"          "fil.t"
    ":fin.filing/company"     "org.corp.tw.tsmc"
    ":fin.filing/fiscal-year" 2024}
   {":fin.fact/id"      "fact.x"
    ":fin.fact/company" "org.corp.us.apple"}])  ; a fact, not a filing

(deftest test-kanjo-disclosed-companies-extracts-filing-companies
  (let [disc (g/kanjo-disclosed-companies (kanjo-fixture))]
    (is (= #{"org.corp.us.apple" "org.corp.tw.tsmc"} disc))))  ; facts ignored, dedup

(deftest test-ground-equities-disclosure-depth
  (let [cons (g/kabuto-equity-constituents (kab-fixture))  ; ids: apple, tsmc, jp.x
        ge   (g/ground-equities 115.0 cons g/LISTED_UNIVERSE
                                #{"org.corp.us.apple" "org.corp.tw.tsmc"})]
    (is (= 2 (get ge "with_disclosed_financials")))
    (is (= #{"Apple" "TSMC"} (set (get ge "disclosed_sample"))))))

(deftest test-ground-equities-depth-defaults-zero
  (let [ge (g/ground-equities 115.0 (g/kabuto-equity-constituents (kab-fixture)))]
    (is (= 0 (get ge "with_disclosed_financials")))))

;; ── per-layer grounding roadmap ───────────────────────────────────────────────────
(deftest test-roadmap-covers-every-layer
  (let [roadmap (g/grounding-roadmap (pyramid-fixture))]
    (is (= #{"equities" "gold" "derivatives"}
           (set (map #(get % "asset_class") roadmap))))))

(deftest test-roadmap-equities-grounded-rest-ungroundable
  (let [roadmap-m (into {} (map (fn [r] [(get r "asset_class") r])
                                (g/grounding-roadmap (pyramid-fixture))))]
    (is (= "grounded" (get (get roadmap-m "equities") "status")))
    (is (= "kabuto"   (get (get roadmap-m "equities") "source_actor")))
    (is (= "ungroundable-at-r0" (get (get roadmap-m "gold") "status")))
    (is (= "ungroundable-at-r0" (get (get roadmap-m "derivatives") "status")))
    ;; every ungroundable layer states a non-empty reason (honesty contract)
    (is (every? #(seq (get % "reason")) (vals roadmap-m)))))

(deftest test-layer-grounding-registry-well-formed
  (doseq [[ac spec] g/LAYER_GROUNDING]
    (is (contains? #{"grounded" "ungroundable-at-r0"} (get spec "status")))
    (is (seq (get spec "reason")))
    (when (= "grounded" (get spec "status"))
      (is (some? (get spec "source_actor"))))))

(deftest test-ground-report-has-roadmap-and-depth
  (let [rep (g/ground (pyramid-fixture) (kab-fixture) (hok-fixture) (kanjo-fixture))]
    (is (contains? rep "roadmap"))
    (is (= 3 (count (get rep "roadmap"))))
    (is (>= (get-in rep ["equities" "with_disclosed_financials"]) 1))))  ; apple overlaps

(deftest test-ground-without-kanjo-still-works
  (let [rep (g/ground (pyramid-fixture) (kab-fixture) (hok-fixture))]  ; kanjo omitted
    (is (= 0 (get-in rep ["equities" "with_disclosed_financials"])))))

;; ── fail-open loader ──────────────────────────────────────────────────────────────
(deftest test-load-ledger-missing-returns-empty
  (is (= [] (g/load-ledger (java.io.File. ROOT "20-actors/nonesuch/missing.edn")))))

(deftest test-real-sibling-ledgers-present-or-fail-open
  ;; exercises the REAL kabuto/hokorobi ledgers if checked out; green either way (fail-open).
  (let [kab (g/load-ledger (java.io.File. ROOT "20-actors/kabuto/data/seed-public-companies.kotoba.edn"))]
    (if (seq kab)
      (is (> (count (g/kabuto-equity-constituents kab)) 100))  ; the real seed has >100 companies
      (is (= [] (g/kabuto-equity-constituents kab))))))          ; fail-open path

(when (= *file* (System/getProperty "babashka.file"))
  (let [{:keys [fail error]} (clojure.test/run-tests 'shionome.methods.test-grounding)]
    (System/exit (if (zero? (+ fail error)) 0 1))))
