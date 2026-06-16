#!/usr/bin/env bb
;; Working Clojure port of py/agent.py (makura foam pillow manufacturing actor).
(ns makura.py.agent
  "makura 枕 — foam pillow manufacturing langgraph actor (kotoba WASM cell).

  ADR-2605261115, R0 scaffold. Runs in-WASM on kotoba :8077. Handlers over the foam
  pillow manufacturing schema (foam batch / fabric / pillow lot / QC / packaging /
  recycling / worker exposure), with makura's constitutional gates enforced:

    G6  isocyanate exposure   MDI <=5 ppb / TDI <=2 ppb 8h TWA (worker safety)
    G8  FR-chemistry exclusion no PBDE/TDCPP/TCEP/Sb2O3; baseline FR-free
    G11 KPI caps              foam mass <=2.0 kg / dims <=80x50x25 cm / combined <=4.0 kg
    G13 take-back / recycling  IPFS-pinned take-back QR; >=10% recycled crumb by R3
    G14 no embedded sensors    no RFID/NFC/IoT in the BoM (anti-surveillance consumer goods)

  LLM access is Murakumo-only via KotobaLLM (127.0.0.1:4000, gemma3:4b; G15). State is
  written back to the kotoba Datom log (G16). Settlement is USDC on Base L2 + ERC-4337
  + TitheRouter 10% only — no fiat (G17). The platform holds no key; the member signs
  each settlement (G18). Compute-only R0; settlement stops at :intent (G19).

  Run:  bb --classpath 20-actors 20-actors/makura/py/agent.clj"
  (:require [clojure.string :as str]))

;; ── constants ──────────────────────────────────────────────────────────────────
(def TITHE_BPS 1000)              ; 10% TitheRouter auto-split (G17), basis points

;; G11 KPI caps
(def MAX_FOAM_MASS_KG 2.0)
(def MAX_DIMS_CM [80.0 50.0 25.0])
(def MAX_COMBINED_KG 4.0)

;; G6 worker exposure ceilings (8h TWA, ppb)
(def MDI_CEILING_PPB 5.0)
(def TDI_CEILING_PPB 2.0)

;; G8 prohibited flame-retardant chemistries
(def PROHIBITED_FR #{"pbde" "tdcpp" "tcep" "sb2o3" "antimony trioxide"})

;; G14 prohibited embedded electronics in the BoM
(def PROHIBITED_EMBEDDED #{"rfid" "nfc" "iot" "sensor" "bluetooth" "smart-chip"})

;; ── _infer — Murakumo-only inference (G15) ─────────────────────────────────────
(defn _infer
  "Murakumo-only inference (G15). Returns offline sentinel when host not available."
  [_prompt]
  ;; In WASM host: would call (llm/infer model prompt). Offline sentinel matches agent.py.
  "LLM_NOT_AVAILABLE")

;; ── G11 — KPI caps (foam mass / dimensions / combined) ────────────────────────
(defn kpi_caps_ok
  "Verify foam_mass ≤ MAX_FOAM_MASS_KG, each dim ≤ MAX_DIMS_CM, combined ≤ MAX_COMBINED_KG.
  Returns {:ok bool :reason str}."
  [foam-mass-kg dims-cm combined-kg]
  (cond
    (> (double foam-mass-kg) MAX_FOAM_MASS_KG)
    {:ok false :reason (str "foam mass " foam-mass-kg " > " MAX_FOAM_MASS_KG " kg (G11)")}

    (some true? (map (fn [d m] (> (double d) (double m))) dims-cm MAX_DIMS_CM))
    {:ok false :reason (str "dims " (vec dims-cm) " exceed " MAX_DIMS_CM " cm (G11)")}

    (> (double combined-kg) MAX_COMBINED_KG)
    {:ok false :reason (str "combined " combined-kg " > " MAX_COMBINED_KG " kg (G11)")}

    :else
    {:ok true :reason "within KPI caps"}))

;; ── G6 — isocyanate worker exposure gate ───────────────────────────────────────
(defn exposure_ok
  "Verify MDI ≤ MDI_CEILING_PPB and TDI ≤ TDI_CEILING_PPB (8h TWA).
  Returns {:ok bool :reason str}."
  [mdi-ppb tdi-ppb]
  (cond
    (> (double mdi-ppb) MDI_CEILING_PPB)
    {:ok false :reason (str "MDI " mdi-ppb " > " MDI_CEILING_PPB " ppb 8h TWA (G6)")}

    (> (double tdi-ppb) TDI_CEILING_PPB)
    {:ok false :reason (str "TDI " tdi-ppb " > " TDI_CEILING_PPB " ppb 8h TWA (G6)")}

    :else
    {:ok true :reason "exposure within ceilings"}))

;; ── G8 — flame-retardant chemistry exclusion ───────────────────────────────────
(defn fr_chemistry_ok
  "Check that no prohibited FR chemistry term is present (case-insensitive).
  Returns {:ok bool :reason str}."
  [chemistry-terms]
  (let [hits (filter #(contains? PROHIBITED_FR (str/lower-case (str/trim %))) chemistry-terms)]
    (if (seq hits)
      {:ok false :reason (str "prohibited FR chemistry: " (vec hits) " (G8)")}
      {:ok true :reason "FR-free"})))

;; ── G14 — no embedded sensors in the BoM ──────────────────────────────────────
(defn bom_no_embedded
  "Check that no BoM item contains a prohibited embedded electronics term.
  Returns {:ok bool :reason str}."
  [bom-items]
  (let [hits (filter (fn [item]
                       (let [lower (str/lower-case (str/trim item))]
                         (some #(str/includes? lower %) PROHIBITED_EMBEDDED)))
                     bom-items)]
    (if (seq hits)
      {:ok false :reason (str "embedded electronics prohibited: " (vec hits) " (G14)")}
      {:ok true :reason "no embedded sensors"})))

;; ── build_settlement_intent — USDC + TitheRouter (G17/G18/G19) ────────────────
(defn build_settlement_intent
  "USDC settlement split. 10% tithe -> Public Fund. Stops at :intent —
  broadcast needs a member signature (G18).
  NOTE: R0 behaviour — state is 'executed' when buyer-sig-ref is provided, else 'intent'.
  This matches agent.py exactly."
  ([gross-minor]
   (build_settlement_intent gross-minor nil))
  ([gross-minor buyer-sig-ref]
   (let [gross (long gross-minor)
         tithe (quot (* gross TITHE_BPS) 10000)
         maker-payout (- gross tithe)]
     {:rail              "usdc-base-l2"
      :grossMinor        gross
      :titheMinor        tithe
      :makerPayoutMinor  maker-payout
      :titheRouter       "50-infra/etzhayyim-tithe-router"
      :state             (if buyer-sig-ref "executed" "intent")
      :buyerSigRef       (or buyer-sig-ref "")})))

;; ── foam batch attestation (gates G6 + G8 enforced before record) ──────────────
(defn record_foam_batch
  "Record foam batch with FR-chemistry (G8) and exposure (G6) gates enforced.
  Returns datom-shaped map or {:error str :blocked true}."
  ([batch-id chemistry-terms mdi-ppb tdi-ppb]
   (record_foam_batch batch-id chemistry-terms mdi-ppb tdi-ppb "" ""))
  ([batch-id chemistry-terms mdi-ppb tdi-ppb density voc-test]
   (let [fr (fr_chemistry_ok chemistry-terms)]
     (if-not (:ok fr)
       {:error (:reason fr) :blocked true}
       (let [exp (exposure_ok mdi-ppb tdi-ppb)]
         (if-not (:ok exp)
           {:error (:reason exp) :blocked true}
           {":foamBatchAttestation/id"         batch-id
            ":foamBatchAttestation/chemistry"  (str/join "," chemistry-terms)
            ":foamBatchAttestation/density"    density
            ":foamBatchAttestation/vocTest"    voc-test}))))))

;; ── QC record + pillow lot (KPI caps enforced) ─────────────────────────────────
(defn record_qc
  "Return a QC record map."
  ([lot-id result]
   (record_qc lot-id result "0"))
  ([lot-id result reject-pct]
   {":qcRecord/id"              (str "qc." lot-id)
    ":qcRecord/visual"          result
    ":qcRecord/rejectPercentage" reject-pct}))

(defn finalize_pillow_lot
  "Finalize pillow lot after enforcing KPI caps (G11) and no-embedded-sensors (G14).
  Returns datom-shaped map or {:error str :blocked true}."
  [lot-id foam-mass-kg dims-cm combined-kg bom-items]
  (let [caps (kpi_caps_ok foam-mass-kg dims-cm combined-kg)]
    (if-not (:ok caps)
      {:error (:reason caps) :blocked true}
      (let [bom (bom_no_embedded bom-items)]
        (if-not (:ok bom)
          {:error (:reason bom) :blocked true}
          {":pillowLotAttestation/id"       lot-id
           ":pillowLotAttestation/fillWeight" (str foam-mass-kg "kg")
           ":pillowLotAttestation/lotDid"   (str "did:web:makura.etzhayyim.com:lot:" lot-id)})))))

;; ── main (smoke demo) ─────────────────────────────────────────────────────────
(defn main [& _]
  (println "foam batch (FR-free, safe):"
           (get (record_foam_batch "b1" ["polyol" "mdi"] 3.0 1.0)
                ":foamBatchAttestation/id"))
  (println "foam batch (PBDE):"
           (:blocked (record_foam_batch "b2" ["pbde"] 1.0 1.0)))
  (println "lot over KPI:"
           (:blocked (finalize_pillow_lot "l1" 3.0 [50 40 20] 3.0 [])))
  (println "settlement:" (build_settlement_intent 20000000)))

(when (= *file* (System/getProperty "babashka.file"))
  (main))
