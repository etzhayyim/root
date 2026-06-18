#!/usr/bin/env bb
;; Working Clojure port of py/agent.py (yakushi pharmaceutical manufacturing actor).
(ns yakushi.py.agent
  "yakushi 薬師 — pharmaceutical R&D langgraph actor (kotoba WASM cell).

  ADR-2605250500, R0 scaffold. Runs in-WASM on kotoba :8077. Handlers over the
  pharmaceutical manufacturing schema (raw material / API synthesis / fill-finish /
  QC / adverse event / settlement), with yakushi's constitutional gates enforced:

    G1  OTC-only, three jurisdictions     perpetually off-patent in PMDA/FDA/EMA
    G2  published-literature routes       no proprietary synthesis; open literature only
    G3  silen-pharma-review baseline      Council Lv6+ >=3 required
    G4  QP-equivalent co-sign             Qualified Person signature on each lot
    G5  adverse-event aggregation         lot + severity + outcome only; no patient DID
    G7  CWC Schedule 3 screening          OPCW declaration for acetic anhydride, etc.
    G9  witness invariant                 N >=2 (operator DID + QP DID or sensor)
    G10 patient identity non-traceable   aggregate keys exclude patient DID
    G15 Murakumo-only inference           127.0.0.1:4000 gemma3:4b only
    G16 kotoba-EAVT-native state          no SQL/RisingWave/Cypher as canonical
    G17 tithe-non-fiat                    USDC Base L2 + ERC-4337 + TitheRouter 10%
    G18 no-server-key                     member/QP sign each settlement
    G19 consent-bound                     compute R0; settlement stops at :intent

  LLM access is Murakumo-only (127.0.0.1:4000, gemma3:4b; G15). State is
  written back to the kotoba Datom log (G16). Settlement is USDC on Base L2 +
  ERC-4337 + TitheRouter 10% only — no fiat (G17). The platform holds no key; the
  member/QP signs each settlement (G18). Compute-only R0; settlement stops at
  :intent (G19).

  Run:  bb --classpath 20-actors 20-actors/yakushi/py/agent.clj"
  (:require [clojure.string :as str]
            [clojure.set]))

;; ── constants ──────────────────────────────────────────────────────────────────
(def TITHE_BPS 1000)  ; 10% TitheRouter auto-split (G17), basis points

;; G5 adverse event aggregation: lot + severity + outcome only (no patient DID)
(def VALID_SEVERITIES #{"mild" "moderate" "severe"})
(def VALID_OUTCOMES #{"recovered" "not-recovered" "unknown"})

;; G1 Wave 1 reference APIs (perpetually off-patent, OTC in PMDA/FDA/EMA)
(def WAVE_1_APIS #{"sodium-cromoglicate"
                   "naphazoline-hydrochloride"
                   "chlorpheniramine-maleate"})

;; ── Wave 2 — disinfectants / antiseptics (消毒薬・殺菌剤) ──────────────────────────
;; ADR-2606171400. Unlike Wave 1/1b APIs (de-novo synthesized), Wave 2 actives are
;; FORMULATED (diluted / blended) from generic off-patent actives — the lowest-IP-risk,
;; highest-public-health-value category (§2(e) anti-gatekeeping). The manufacturing
;; verb is FORMULATION, not synthesis. All 7 actives are 公定書 (日局/USP/EP) monograph
;; grade with multi-generational safety records.
(def WAVE_2_DISINFECTANTS #{"ethanol"                 ; 消毒用エタノール
                            "isopropanol"             ; イソプロパノール (IPA)
                            "sodium-hypochlorite"     ; 次亜塩素酸ナトリウム
                            "benzalkonium-chloride"   ; 塩化ベンザルコニウム (逆性石鹸)
                            "povidone-iodine"         ; ポビドンヨード
                            "chlorhexidine-gluconate" ; クロルヘキシジングルコン酸塩
                            "hydrogen-peroxide"})     ; オキシドール (過酸化水素)

;; G21 efficacy window — evidence-based active concentration in percent {:min :max}.
;; Out-of-window formulation is structurally blocked: too-weak = no kill, too-strong =
;; wasteful / harmful (e.g. ethanol >90% flash-evaporates before protein denaturation).
(def DISINFECTANT_EFFICACY_WINDOW
  {"ethanol"                 {:min 60.0  :max 90.0}   ; 消毒用エタノール 76.9–81.4 vol% は窓内
   "isopropanol"             {:min 60.0  :max 80.0}
   "sodium-hypochlorite"     {:min 0.05  :max 0.5}    ; surface, available chlorine %
   "benzalkonium-chloride"   {:min 0.01  :max 0.2}
   "povidone-iodine"         {:min 1.0   :max 10.0}
   "chlorhexidine-gluconate" {:min 0.05  :max 0.5}
   "hydrogen-peroxide"       {:min 1.0   :max 6.0}})  ; オキシドール 2.5–3.5% は窓内

;; G24 use class — each finished disinfectant declares one.
(def VALID_USE_CLASSES #{"surface" "skin-antiseptic" "hand-hygiene"})

;; G22 toxic-gas co-formulants — hypochlorite + acid → Cl₂ gas; hypochlorite + ammonia →
;; chloramine. A weaponizable gas formulation is constitutionally unrepresentable
;; (Charter §1.12 / Rider §2(a)): record_formulation REFUSES these combinations.
(def HYPOCHLORITE_INCOMPATIBLE
  #{"acid" "hydrochloric-acid" "citric-acid" "acetic-acid" "vinegar" "sulfuric-acid"
    "ammonia" "ammonium" "ammonium-chloride" "ammonium-hydroxide"})

;; G23 flammable actives — require 火気厳禁 (keep-away-from-fire) on the label.
(def FLAMMABLE_ACTIVES #{"ethanol" "isopropanol"})

;; ── _infer — Murakumo-only inference (G15) ─────────────────────────────────────
(defn _infer
  "Murakumo-only inference (G15). Returns offline sentinel when host not available."
  [_prompt]
  ;; In WASM host: would call (llm/infer model prompt). Offline sentinel matches agent.py.
  "LLM_NOT_AVAILABLE")

;; ── G1 — OTC-only, perpetually off-patent (Wave 1 reference) ──────────────────
(defn api_otc_ok
  "Check if API is in Wave 1 OTC reference set."
  [api-inn-slug]
  (if-not (contains? WAVE_1_APIS (str/lower-case api-inn-slug))
    {:ok false :reason (str "API " api-inn-slug " not in Wave 1 OTC reference (G1)")}
    {:ok true :reason "OTC off-patent confirmed (Wave 1)"}))

;; ── G3 — silen-pharma-review baseline (Council Lv6+ >= 3) ────────────────────
(defn review_attested
  "Check if silen-pharma-review passed."
  [review-verdict review-scope]
  (if (not= (str/lower-case review-verdict) "approve")
    {:ok false :reason (str "silen-pharma-review verdict is " review-verdict " (G3)")}
    {:ok true :reason (str "silen-pharma-review approved for " review-scope)}))

;; ── G4 — QP-equivalent co-sign (no-server-key enforcement) ──────────────────
(defn qp_signature_ok
  "Verify QP DID and signature ref (member holds the key, G18)."
  [qp-did qp-sig-ref]
  (if (or (str/blank? qp-did) (str/blank? qp-sig-ref))
    {:ok false :reason "QP DID and signature reference required (G4)"}
    {:ok true :reason (str "QP " qp-did " signature registered")}))

;; ── G5 — adverse event aggregation (lot + severity + outcome only, no patient) ─
(defn adverse_event_ok
  "Validate adverse event aggregation (no patient DID, G5/G10)."
  [lot-id severity outcome]
  (cond
    (str/blank? lot-id)
    {:ok false :reason "lot_id required; patient DID prohibited (G5/G10)"}

    (not (contains? VALID_SEVERITIES (str/lower-case severity)))
    {:ok false :reason (str "severity " severity " not in " VALID_SEVERITIES)}

    (not (contains? VALID_OUTCOMES (str/lower-case outcome)))
    {:ok false :reason (str "outcome " outcome " not in " VALID_OUTCOMES)}

    :else
    {:ok true :reason (str "AE aggregation by lot " lot-id " (no patient identity)")}))

;; ── G9 — witness invariant (N >= 2) ──────────────────────────────────────────
(defn witness_quorum_ok
  "Verify witness count >= 2 (operator DID + QP or sensor)."
  [witness-dids]
  (let [cnt (count (or witness-dids []))]
    (if (< cnt 2)
      {:ok false :reason (str "witness count " cnt " < 2 (G9)")}
      {:ok true :reason (str "witness quorum N=" cnt " >= 2")})))

;; ── build_settlement_intent — USDC + TitheRouter (G17/G18/G19) ──────────────
(defn build_settlement_intent
  "USDC settlement split. 10% tithe -> Public Fund. Stops at :intent —
  broadcast needs a member/QP signature (G18).
  NOTE: R0 behaviour — state is 'executed' when qp-sig-ref is provided, else 'intent'.
  This matches agent.py exactly."
  ([gross-minor]
   (build_settlement_intent gross-minor nil))
  ([gross-minor qp-sig-ref]
   (let [gross (long gross-minor)
         tithe (quot (* gross TITHE_BPS) 10000)
         maker-payout (- gross tithe)]
     {:rail              "usdc-base-l2"
      :grossMinor        gross
      :titheMinor        tithe
      :makerPayoutMinor  maker-payout
      :titheRouter       "50-infra/etzhayyim-tithe-router"
      :state             (if qp-sig-ref "executed" "intent")
      :qpSigRef          (or qp-sig-ref "")})))

;; ── record_raw_material (gates G1 + G7 screened) ────────────────────────────
(defn record_raw_material
  "Record raw material attestation (公定 or 劇物 grade)."
  [material-name grade hazard-class]
  (if-not (contains? #{"公定" "劇物" "koujou" "gekibutsu"} (str/lower-case grade))
    {:error (str "grade " grade " must be 公定 or 劇物") :blocked true}
    {":rawMaterialAttestation/id"           (str "rm:" material-name)
     ":rawMaterialAttestation/materialName" material-name
     ":rawMaterialAttestation/grade"        grade
     ":rawMaterialAttestation/hazardClass"  hazard-class}))

;; ── record_synthesis (gates G1 + G2 + G9 enforced) ──────────────────────────
(defn record_synthesis
  "Record API synthesis attestation with published literature route (G2)."
  [api-inn-slug route witness-dids]
  (let [api-check (api_otc_ok api-inn-slug)]
    (if-not (:ok api-check)
      {:error (:reason api-check) :blocked true}
      (let [witness-check (witness_quorum_ok witness-dids)]
        (if-not (:ok witness-check)
          {:error (:reason witness-check) :blocked true}
          {":apiSynthesisAttestation/id"       (str "syn:" api-inn-slug)
           ":apiSynthesisAttestation/apiName"  api-inn-slug
           ":apiSynthesisAttestation/route"    route
           ":apiSynthesisAttestation/witness1" (if (>= (count witness-dids) 1)
                                                 (nth witness-dids 0)
                                                 "")
           ":apiSynthesisAttestation/witness2" (if (>= (count witness-dids) 2)
                                                 (nth witness-dids 1)
                                                 "")})))))

;; ── record_fill (gates G8 sterilization enforced) ────────────────────────────
(defn record_fill
  "Record fill-finish attestation (aseptic or autoclave)."
  [product-form sterile-process witness-operator witness-qp]
  (if-not (contains? #{"aseptic-0.22µm-filter" "terminal-autoclave"}
                     (str/lower-case sterile-process))
    {:error (str "sterile_process " sterile-process " must be aseptic or autoclave (G8)")
     :blocked true}
    {":fillFinishAttestation/id"              (str "ff:" product-form)
     ":fillFinishAttestation/productForm"     product-form
     ":fillFinishAttestation/sterileProcess"  sterile-process
     ":fillFinishAttestation/witnessOperator" witness-operator
     ":fillFinishAttestation/witnessQp"       witness-qp}))

;; ── record_qc (gates G4 QP co-sign + G13 no-server-key enforced) ────────────
(defn record_qc
  "Record QC attestation + lot release by QP (G4/G13)."
  [lot-id test-results qp-did verdict]
  (let [qp-check (qp_signature_ok qp-did "passkey-ref")]  ; server doesn't hold the key
    (if-not (:ok qp-check)
      {:error (:reason qp-check) :blocked true}
      {":qcAttestation/id"          (str "qc:" lot-id)
       ":qcAttestation/lotId"       lot-id
       ":qcAttestation/testResults" test-results
       ":qcAttestation/qpDid"       qp-did
       ":qcAttestation/verdict"     verdict})))

;; ── record_ae (gates G5 + G10 enforced: no patient DID, aggregate by lot) ───
(defn record_ae
  "Record adverse event (lot + severity + outcome only; no patient identity)."
  ([lot-id severity outcome]
   (record_ae lot-id severity outcome ""))
  ([lot-id severity outcome event-cid]
   (let [ae-check (adverse_event_ok lot-id severity outcome)]
     (if-not (:ok ae-check)
       {:error (:reason ae-check) :blocked true}
       {":adverseEventReport/id"       (str "ae:" lot-id ":" severity)
        ":adverseEventReport/lotId"    lot-id
        ":adverseEventReport/severity" severity
        ":adverseEventReport/outcome"  outcome
        ":adverseEventReport/eventCid" (or event-cid "")}))))

;; ════════════════════════════════════════════════════════════════════════════════
;; Wave 2 — disinfectant / antiseptic formulation (ADR-2606171400)
;; ════════════════════════════════════════════════════════════════════════════════

;; ── G1(Wave 2) — active is a Wave 2 公定書 disinfectant ───────────────────────────
(defn disinfectant_ok
  "Check if active is in the Wave 2 disinfectant reference set."
  [inn-slug]
  (if-not (contains? WAVE_2_DISINFECTANTS (str/lower-case inn-slug))
    {:ok false :reason (str "active " inn-slug " not in Wave 2 disinfectant reference (G1)")}
    {:ok true :reason "公定書 disinfectant confirmed (Wave 2)"}))

;; ── G21 — efficacy-window check (active concentration in percent) ────────────────
(defn disinfectant_efficacy_ok
  "Verify the active concentration falls inside its evidence-based efficacy window."
  [inn-slug conc-percent]
  (let [slug   (str/lower-case inn-slug)
        window (get DISINFECTANT_EFFICACY_WINDOW slug)]
    (cond
      (nil? window)
      {:ok false :reason (str "no efficacy window for " inn-slug " (G21)")}

      (or (nil? conc-percent) (not (number? conc-percent)))
      {:ok false :reason "concentration (percent) required (G21)"}

      (< (double conc-percent) (:min window))
      {:ok false :reason (str conc-percent "% below efficacy floor " (:min window) "% — no kill (G21)")}

      (> (double conc-percent) (:max window))
      {:ok false :reason (str conc-percent "% above efficacy ceiling " (:max window) "% — wasteful/harmful (G21)")}

      :else
      {:ok true :reason (str conc-percent "% within [" (:min window) "–" (:max window) "]% (G21)")})))

;; ── G22 — no toxic-gas formulation (hypochlorite + acid/ammonia unrepresentable) ─
(defn no_toxic_gas_ok
  "Refuse co-formulating sodium hypochlorite with any acid (Cl₂) or ammonia (chloramine).
  Weaponizable gas is constitutionally unrepresentable (§1.12 / Rider §2(a))."
  [inn-slug co-formulants]
  (let [slug (str/lower-case inn-slug)
        cos  (set (map str/lower-case (or co-formulants [])))]
    (if (and (= slug "sodium-hypochlorite")
             (seq (clojure.set/intersection cos HYPOCHLORITE_INCOMPATIBLE)))
      {:ok false :reason (str "hypochlorite + " (first (clojure.set/intersection cos HYPOCHLORITE_INCOMPATIBLE))
                              " generates toxic gas — unrepresentable (G22)")}
      {:ok true :reason "no toxic-gas co-formulation (G22)"})))

;; ── G24 — use-class validation ───────────────────────────────────────────────────
(defn use_class_ok
  "Validate the declared use class (surface / skin-antiseptic / hand-hygiene)."
  [use-class]
  (if-not (contains? VALID_USE_CLASSES (str/lower-case (or use-class "")))
    {:ok false :reason (str "use-class " use-class " not in " VALID_USE_CLASSES " (G24)")}
    {:ok true :reason (str "use-class " use-class " valid (G24)")}))

;; ── G23 — flammable-label lint (alcohol actives require 火気厳禁) ─────────────────
(defn flammable_label_ok
  "Alcohol-based products MUST carry a 火気厳禁 / flammable warning on the label."
  [inn-slug label-text]
  (let [slug  (str/lower-case inn-slug)
        label (or label-text "")]
    (if (and (contains? FLAMMABLE_ACTIVES slug)
             (not (or (str/includes? label "火気厳禁")
                      (str/includes? (str/lower-case label) "flammable"))))
      {:ok false :reason (str slug " is flammable — label MUST contain 火気厳禁 / flammable (G23)")}
      {:ok true :reason "flammable labelling satisfied (G23)"})))

;; ── record_formulation (gates G1/Wave2 + G21 + G22 + G23 + G24 + G9 enforced) ────
(defn record_formulation
  "Record a disinfectant formulation attestation. Wave 2 actives are FORMULATED
  (diluted/blended), not synthesized. Enforces the efficacy window (G21),
  toxic-gas refusal (G22), flammable labelling (G23), use class (G24) and the
  witness invariant (G9) before emitting the attestation datoms."
  ([inn-slug conc-percent use-class witness-dids]
   (record_formulation inn-slug conc-percent use-class [] "" witness-dids))
  ([inn-slug conc-percent use-class co-formulants label-text witness-dids]
   (let [checks [(disinfectant_ok inn-slug)
                 (disinfectant_efficacy_ok inn-slug conc-percent)
                 (no_toxic_gas_ok inn-slug co-formulants)
                 (use_class_ok use-class)
                 (flammable_label_ok inn-slug label-text)
                 (witness_quorum_ok witness-dids)]
         failed (first (remove :ok checks))]
     (if failed
       {:error (:reason failed) :blocked true}
       {":formulationAttestation/id"          (str "fml:" (str/lower-case inn-slug) ":" conc-percent)
        ":formulationAttestation/activeName"  (str/lower-case inn-slug)
        ":formulationAttestation/concPercent" (double conc-percent)
        ":formulationAttestation/useClass"    use-class
        ":formulationAttestation/coFormulants" (str/join "," (or co-formulants []))
        ":formulationAttestation/witness1"    (if (>= (count witness-dids) 1) (nth witness-dids 0) "")
        ":formulationAttestation/witness2"    (if (>= (count witness-dids) 2) (nth witness-dids 1) "")}))))

;; ── main (smoke demo) ─────────────────────────────────────────────────────────
(defn main [& _]
  (println "API OTC check (Wave 1):"
           (:ok (api_otc_ok "sodium-cromoglicate")))
  (println "API check (not Wave 1):"
           (:ok (api_otc_ok "omeprazole")))
  (println "AE aggregation (valid):"
           (:ok (adverse_event_ok "lot:w1:001" "mild" "recovered")))
  (println "AE aggregation (invalid severity):"
           (:ok (adverse_event_ok "lot:w1:001" "extreme" "unknown")))
  (println "witness quorum (N=2):"
           (:ok (witness_quorum_ok ["did:web:...op1" "did:web:...qp1"])))
  (println "settlement intent:" (build_settlement_intent 10000000))
  ;; Wave 2 — disinfectants (ADR-2606171400)
  (println "disinfectant (消毒用エタノール 80%):"
           (:ok (disinfectant_efficacy_ok "ethanol" 80.0)))
  (println "disinfectant (ethanol 50% — too weak):"
           (:ok (disinfectant_efficacy_ok "ethanol" 50.0)))
  (println "no-toxic-gas (hypochlorite + vinegar — REFUSED):"
           (:ok (no_toxic_gas_ok "sodium-hypochlorite" ["vinegar"])))
  (println "formulation (povidone-iodine 10% skin-antiseptic):"
           (not (:blocked (record_formulation "povidone-iodine" 10.0 "skin-antiseptic"
                                              ["did:op" "did:qp"])))))

(when (= *file* (System/getProperty "babashka.file"))
  (main))
