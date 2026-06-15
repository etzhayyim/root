#!/usr/bin/env bb
;; Clojure port of methods/grounding.py — 潮目 (shionome) stock-layer entity-grounding bridge.
(ns shionome.methods.grounding
  "grounding.clj — 潮目 (shionome) stock-layer ENTITY-GROUNDING bridge. ADR-2606072200 (R1).

  The stock pyramid (weave/stock-pyramid) sizes each money-and-markets LAYER as an aggregate.
  This bridge answers the next question HONESTLY: *who is inside each layer?* — it decomposes a
  pyramid layer into the NAMED real entities that sibling actors already mirror, and reports the
  COVERAGE gap (how much of the layer is actually grounded vs still illustrative).

    - the EQUITIES layer ← kabuto 兜 listed-company ledger (org.corp.* — name/ticker/market-cap)
    - a cross-cutting SYSTEMIC-INSTITUTIONS overlay ← hokorobi 綻び (G-SIB banks / insurers /
      pensions / CCPs span equities+debt+pensions, so they are an overlay, NOT one pyramid layer)

  DISCIPLINE (unchanged from the actor's gates):
    - G2 トレードはしない — a market-cap / institution count is a SIZE, descriptive, never a
      rating / signal / target / solvency verdict. Every report carries no_trade_notice = true.
    - G1 — the grounded entities are PUBLIC companies / systemic institutions already mirrored by
      kabuto / hokorobi; shionome adds no new entity, only a read-side view.
    - HONESTY — value_coverage is a stated LOWER BOUND; the count denominator is a :representative
      universe figure, not a live count; ungrounded_layers names exactly what is NOT yet backed.
    - FAIL-OPEN — a missing/unreadable sibling ledger yields [] (the layer is reported ungrounded).

  Stdlib only. Pure functions take already-loaded record lists; only load-ledger touches disk."
  (:require [clojure.string :as str]
            [shionome.methods.edn :as sedn]
            [clojure.java.io :as io]))

;; ── kw* inlined from weave.cljc (private there — babashka cannot reach cross-ns private vars) ──
;; Mirror of weave.cljc `kw*` which mirrors weave.py `_kw`:
;;   str(v or "").lstrip(":") → split("/")[-1].lower()
(defn- kw*
  "Normalize an edn keyword/string to a bare lowercase token (':flow/kind' → 'kind').
  Inlined mirror of weave.cljc `kw*` (private there). Do NOT modify independently."
  [v]
  (let [s (-> (str (or v "")) (str/replace #"^:+" ""))]
    (-> (last (str/split s #"/" -1)) str/lower-case)))

;; A :representative universe denominator used ONLY to express count coverage as an honest
;; fraction. ~50k–58k companies are exchange-listed worldwide (WFE statistics order of magnitude).
(def LISTED_UNIVERSE 55000)

;; ── per-layer grounding ROADMAP ──────────────────────────────────────────────────────────────────
;; For every money-pyramid asset-class: which sibling actor's entity ledger (if any) can decompose
;; it, and — where it CANNOT yet — the explicit reason.
(def LAYER_GROUNDING
  {"equities"    {"source_actor" "kabuto"
                  "status"       "grounded"
                  "reason"       "listed-company ledger (org.corp.*) decomposes the layer by named issuer; kanjō adds disclosure depth"}
   "debt"        {"source_actor" nil
                  "status"       "ungroundable-at-r0"
                  "reason"       "bond-market SIZE is a SIFMA/BIS aggregate; no per-issuer debt-outstanding ledger (kanjō discloses corporate BS, NOT tradable debt-securities outstanding — conflating them would mis-size the layer). Candidate issuers: ooyake (sovereign) + kabuto (corporate)"}
   "broad-money" {"source_actor" nil
                  "status"       "ungroundable-at-r0"
                  "reason"       "M2 is a central-bank / banking-system aggregate (BIS / World Bank); not entity-decomposable"}
   "cash"        {"source_actor" nil
                  "status"       "ungroundable-at-r0"
                  "reason"       "physical currency outstanding is a central-bank aggregate; no holder ledger (G1 bars holder-tracking)"}
   "real-estate" {"source_actor" nil
                  "status"       "ungroundable-at-r0"
                  "reason"       "no real-estate-entity / parcel ledger in the repo; total value is a Savills aggregate"}
   "gold"        {"source_actor" nil
                  "status"       "ungroundable-at-r0"
                  "reason"       "above-ground stock value is a World Gold Council aggregate; no holder ledger (G1 bars holder-tracking)"}
   "crypto"      {"source_actor" nil
                  "status"       "ungroundable-at-r0"
                  "reason"       "total market-cap aggregate; no issuer ledger in the repo"}
   "derivatives" {"source_actor" nil
                  "status"       "ungroundable-at-r0"
                  "reason"       "OTC gross-notional is a BIS aggregate; not entity-decomposable from any repo ledger"}})

;; ── helpers ──────────────────────────────────────────────────────────────────────────────────────

(defn- round-n
  "Round x to n decimal places (matches Python round(x, n))."
  [x n]
  (/ (Math/round (* (double x) (Math/pow 10 n))) (Math/pow 10 n)))

(defn load-ledger
  "Load a sibling actor's EDN ledger (a top-level vector of records). FAIL-OPEN: a missing or
  unreadable ledger returns [] — the bridge degrades to 'ungrounded', it never crashes shionome."
  [path]
  (let [f (io/file (str path))]
    (if-not (.exists f)
      []
      (try
        (let [data (sedn/load-edn f)]
          (if (sequential? data) (vec data) []))
        (catch Exception _ [])))))

;; ── constituent extraction ────────────────────────────────────────────────────────────────────────

(defn kabuto-equity-constituents
  "Named listed-company constituents of the global EQUITIES layer, from a kabuto ledger. A
  company record carries :company/name (address / contact / supply-edge / process records do
  not, so they are skipped). :company/market-cap-busd is a FACTUAL public-record size, never a
  rating (G2); it may be absent (the company is then named-but-unsized)."
  [records]
  (reduce
   (fn [out r]
     (if (and (map? r) (get r ":company/name"))
       (let [mc (get r ":company/market-cap-busd")]
         (conj out
               {"id"             (get r ":company/id")
                "name"           (get r ":company/name")
                "ticker"         (get r ":company/ticker")
                "country"        (get r ":company/country")
                "sector"         (when (get r ":company/sector")
                                   (kw* (get r ":company/sector")))
                "market_cap_busd" (when (some? mc) (double mc))
                "sourcing"       (when (get r ":company/sourcing")
                                   (kw* (get r ":company/sourcing")))}))
       out))
   []
   records))

(defn hokorobi-institutions
  "Systemic financial INSTITUTIONS from a hokorobi ledger (:organism/kind :institution). A
  cross-cutting overlay (G-SIB banks / insurers / pensions / CCPs span equities+debt+pensions).
  Resilience overlay, never a solvency verdict (G2)."
  [records]
  (reduce
   (fn [out r]
     (if (and (map? r) (= (kw* (get r ":organism/kind")) "institution"))
       (conj out
             {"id"           (get r ":organism/id")
              "label"        (get r ":organism/label")
              "sector"       (when (get r ":inst/sector")
                               (kw* (get r ":inst/sector")))
              "sii"          (when (get r ":inst/sii")
                               (kw* (get r ":inst/sii")))
              "jurisdiction" (get r ":inst/jurisdiction")
              "sourcing"     (when (get r ":organism/sourcing")
                               (kw* (get r ":organism/sourcing")))})
       out))
   []
   records))

(defn kanjo-disclosed-companies
  "The set of org.corp.* company ids that have ≥1 DISCLOSED filing in a kanjō ledger
  (:fin.filing/company). Used to measure DISCLOSURE DEPTH of the equities layer."
  [records]
  (reduce
   (fn [out r]
     (if (and (map? r) (get r ":fin.filing/company"))
       (conj out (get r ":fin.filing/company"))
       out))
   #{}
   records))

;; ── grounding math ────────────────────────────────────────────────────────────────────────────────

(defn ground-equities
  "Ground the EQUITIES stock layer in named listed companies, reporting HONESTLY."
  ([layer-usd-tn constituents] (ground-equities layer-usd-tn constituents LISTED_UNIVERSE nil))
  ([layer-usd-tn constituents universe] (ground-equities layer-usd-tn constituents universe nil))
  ([layer-usd-tn constituents universe disclosed-ids]
   (let [disclosed-ids  (or disclosed-ids #{})
         n              (count constituents)
         sized          (filter #(some? (get % "market_cap_busd")) constituents)
         sized-v        (vec sized)
         mcap-tn        (/ (reduce + 0.0 (map #(double (get % "market_cap_busd")) sized-v))
                           1000.0)    ; USD billions → USD trillions
         top            (vec (take 10 (sort-by #(- (double (get % "market_cap_busd"))) sized-v)))
         disclosed-cons (filter #(contains? disclosed-ids (get % "id")) constituents)]
     {"layer"                      "equities"
      "layer_usd_tn"               (round-n (double layer-usd-tn) 4)
      "grounded_entities"          n
      "entities_with_size"         (count sized-v)
      "grounded_market_cap_usd_tn" (round-n mcap-tn 4)
      "value_coverage_of_layer"    (if (> (double layer-usd-tn) 0.0)
                                     (round-n (/ mcap-tn (double layer-usd-tn)) 4)
                                     0.0)
      "value_coverage_is_lower_bound" (< (count sized-v) n)
      "count_coverage_of_universe" (if (> (int universe) 0)
                                     (round-n (/ (double n) (double universe)) 5)
                                     0.0)
      "universe_denominator"       universe
      "universe_sourcing"          "representative"   ; WFE order-of-magnitude, NOT a live count
      "with_disclosed_financials"  (count disclosed-cons)
      "disclosed_sample"           (vec (take 10 (map #(get % "name") disclosed-cons)))
      "top_constituents"           (mapv (fn [c] {"name"           (get c "name")
                                                   "ticker"         (get c "ticker")
                                                   "market_cap_busd" (get c "market_cap_busd")})
                                         top)
      "no_trade_notice"            true})))

(defn grounding-roadmap
  "Per-layer grounding STATUS for every money-pyramid layer — the honest map of what is
  entity-grounded vs what cannot be (and why), from the LAYER_GROUNDING registry."
  [pyramid]
  (mapv (fn [l]
          (let [ac   (get l "asset_class")
                spec (get LAYER_GROUNDING ac
                          {"source_actor" nil
                           "status"       "unmapped"
                           "reason"       "no grounding spec for this asset class"})]
            {"asset_class"   ac
             "layer_usd_tn"  (get l "usd_tn")
             "source_actor"  (get spec "source_actor")
             "status"        (get spec "status")
             "reason"        (get spec "reason")}))
        (get pyramid "layers" [])))

(defn systemic-overlay
  "The cross-cutting systemic-institution overlay (from hokorobi). Counts by sector + sourcing
  honesty; it sizes nothing against a single layer. Resilience map, never a solvency verdict (G2)."
  [institutions]
  (let [by-sector (reduce (fn [m i]
                            (let [s (or (get i "sector") "(unknown)")]
                              (update m s (fnil inc 0))))
                          (sorted-map)
                          institutions)
        auth      (count (filter #(= (get % "sourcing") "authoritative") institutions))]
    {"institutions"  (count institutions)
     "by_sector"     by-sector
     "authoritative" auth
     "representative" (- (count institutions) auth)
     "note"          (str "cross-cutting systemic overlay — G-SIB banks / insurers / pensions / CCPs span "
                          "equities+debt+pensions, not one pyramid layer; resilience map, never a solvency verdict")
     "no_trade_notice" true}))

(defn ground
  "The full stock-layer grounding report: decompose pyramid layers into named real entities
  WHERE a sibling ledger exists, add disclosure DEPTH (kanjō) to the equities layer, and stay
  HONEST about the rest via the per-layer roadmap."
  ([pyramid kabuto-records hokorobi-records]
   (ground pyramid kabuto-records hokorobi-records nil))
  ([pyramid kabuto-records hokorobi-records kanjo-records]
   (let [layers         (into {} (map (juxt #(get % "asset_class") identity)
                                      (get pyramid "layers" [])))
         eq-layer       (double (get (get layers "equities" {}) "usd_tn" 0.0))
         disclosed      (kanjo-disclosed-companies (or kanjo-records []))
         constituents   (kabuto-equity-constituents kabuto-records)
         equities       (ground-equities eq-layer constituents LISTED_UNIVERSE disclosed)
         overlay        (systemic-overlay (hokorobi-institutions hokorobi-records))
         grounded-cls   (if (> (get equities "grounded_entities") 0) #{"equities"} #{})
         ungrounded     (vec (keep (fn [l]
                                     (let [ac (get l "asset_class")]
                                       (when-not (contains? grounded-cls ac) ac)))
                                   (get pyramid "layers" [])))]
     {"equities"                       equities
      "systemic_institutions_overlay"  overlay
      "roadmap"                        (grounding-roadmap pyramid)
      "ungrounded_layers"              ungrounded
      "summary"                        {"pyramid_layers"               (count (get pyramid "layers" []))
                                        "layers_with_entity_grounding" (count grounded-cls)
                                        "total_named_entities"         (+ (get equities "grounded_entities")
                                                                          (get overlay "institutions"))
                                        "no_trade_notice"              true}})))
