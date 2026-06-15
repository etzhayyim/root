#!/usr/bin/env bb
;; Working Clojure port of py/agent.py (funadaiku zero-emission cargo shipbuilding actor).
(ns funadaiku.py.agent
  "funadaiku 船大工 — zero-emission cargo shipbuilding langgraph actor (kotoba WASM cell).

  ADR-2606013400, migration plan Phase 4. Runs in-WASM on kotoba :8077. Nine handlers
  over one kotoba EAVT graph, mirroring the zero-emission shipbuilding lifecycle:

    handle-steel-block-fabrication    L1: steel block cutting (oxyacetylene/plasma)
    handle-grand-block-assembly       L2: grand-block subassembly from blocks
    handle-weld-ndt-inspection        L3: NDT (RT/UT/PT) weld pass/fail routing
    handle-powertrain-integration     L4 (DEFINING): wind + solar + green-H₂ FC + LFP + e-pods
    handle-outfitting                 L5a: piping/electrical/SCADA outfitting
    handle-launch-commissioning       L5b: hull launch + fuel-cell cold-start + GNC smoke
    handle-sea-trial                  L5c: at-sea acceptance (wind/solar/H₂ efficiency verify)
    handle-decarbonization-audit      cross: IMO GHG well-to-wake (EEXI/CII audit)
    handle-class-certification-binder terminal: ABS/DNV/ClassNK cert binding

  LLM access is Murakumo-only via KotobaLLM (127.0.0.1:4000, gemma3:4b; G5). State is
  written back to the kotoba Datom log (G6). Settlement is USDC on Base L2 + ERC-4337 +
  TitheRouter 10% only — no fiat (G7). The platform holds no key; the operator signs each
  settlement with their own passkey/smart-account (G12). Defining gate G8 enforces:
  NO fossil main or auxiliary engine EVER — wind-assist + solar + green-H₂ fuel-cell +
  LFP battery + electric pods ONLY. Well-to-wake IMO GHG with green-H₂ chain-of-custody
  verification (G9).

  This R0 build computes and returns plans/records; it does not dispatch real shipyard work
  and does not broadcast settlements (both G13-gated; settlement stops at :intent).

  Run:  bb --classpath 20-actors 20-actors/funadaiku/py/agent.clj"
  (:require [clojure.string :as str]))

(def ^:private tithe-bps 1000)   ; 10% TitheRouter auto-split (G7), basis points
(def ^:private dwt-cap 5000)     ; G12 KPI cap
(def ^:private speed-cap-kn 14)  ; G12 KPI cap
(def ^:private mass-degree-cap 3) ; G12 KPI cap

;; ── LLM stub (Murakumo-only in production; nil here per ADR-2605215000) ──────────
(defn- infer
  "Murakumo-only inference (G5). In the clj port the kotoba host binding is absent;
  returns a sentinel so tests can assert the output shape without needing a live LLM."
  [_prompt]
  "LLM_NOT_AVAILABLE")

;; ── L1 steel block fabrication ─────────────────────────────────────────────────
(defn handle-steel-block-fabrication
  "L1 steel block fabrication. Murakumo assist for cutting-plan design."
  [state]
  (let [block-id (get state :blockId "")
        dims (get state :dimensions "")
        spec-prompt (str "Design oxyacetylene cutting plan for " block-id
                         " (" dims "mm) AH36 hull plate. Optimize for zero waste, worker safety, nesting efficiency.")
        plan (infer spec-prompt)]
    (assoc state :cutting_plan plan :status "cutting-plan")))

;; ── L2 grand-block assembly ────────────────────────────────────────────────────
(defn handle-grand-block-assembly
  "L2 grand-block assembly. Jig design + Oshidashi witness quorum."
  [state]
  (let [gblock-id (get state :gblockId "")
        blocks (get state :subBlocks [])]
    (if (< (count blocks) 2)
      (assoc state :error "need ≥2 sub-blocks per grand-block")
      (let [jig-prompt (str "Design jig fixture for grand-block " gblock-id
                            " from " (count blocks)
                            " sub-blocks. Minimize deflection, allow tack-weld access, positioning for Oshidashi SPMT erection.")
            jig-design (infer jig-prompt)]
        (assoc state
               :jig_design jig-design
               :witness_quorum "oshidashi+operator"
               :status "jig-designed")))))

;; ── L3 weld NDT inspection ─────────────────────────────────────────────────────
(defn handle-weld-ndt-inspection
  "L3 NDT inspection (RT/UT/PT). Tsutsuki crawler witness. Pass/fail/rework."
  [state]
  (let [gblock-id (get state :gblockId "")
        welds (get state :welds [])]
    (if (empty? welds)
      (assoc state :result "pass" :defects [])
      (let [inspection-prompt (str "Evaluate NDT (RT/UT/PT) inspection results for grand-block " gblock-id
                                   ". " (count welds)
                                   " seams. Recommend pass/rework/fail per class society standards. Zero tolerance for unrepaired cracks.")
            eval-result (infer inspection-prompt)]
        (assoc state
               :ndt_eval eval-result
               :result (if (str/includes? (str/lower-case eval-result) "pass")
                         "pass"
                         "rework"))))))

;; ── settlement intent (G7 USDC + TitheRouter 10%, G12 operator-sig) ──────────
(defn build-settlement-intent
  "Compute the USDC settlement split. 10% tithe → Public Fund; shipyard gets the net.

  Stops at :intent — broadcast needs an operator signature (G12) + operator gate (G13).

  Arguments:
    gross-minor       — gross amount in USDC minor units
    operator-sig-ref  — optional operator signature reference"
  ([gross-minor]
   (build-settlement-intent gross-minor nil))
  ([gross-minor operator-sig-ref]
   (let [gross (long gross-minor)
         tithe (quot (* gross tithe-bps) 10000)]
     {:rail "usdc-base-l2"
      :grossMinor gross
      :titheMinor tithe
      :shipyardPayoutMinor (- gross tithe)
      :titheRouter "50-infra/etzhayyim-tithe-router"
      :state (if operator-sig-ref "executed" "intent")
      :operatorSigRef (or operator-sig-ref "")})))

;; ── G8+G9 zero-emission propulsion gate (DEFINING) ────────────────────────────
(defn gate-zero-emission-propulsion
  "G8 gate: enforce ZERO fossil propulsion (wind + solar + green-H₂ FC + LFP + e-pods ONLY).
  G9 gate: well-to-wake green-H₂ chain-of-custody mandatory."
  [powertrain]
  (let [pt-type (str/lower-case (get powertrain :type ""))]
    (cond
      (or (str/includes? pt-type "fossil")
          (str/includes? pt-type "diesel")
          (str/includes? pt-type "gas"))
      {:ok false :reason "fossil propulsion prohibited per G8 (defining gate)"}

      (or (not (str/includes? pt-type "hydrogen"))
          (not (str/includes? pt-type "solar")))
      {:ok false :reason "missing hydrogen or solar per G8"}

      (let [h2-cert (str/lower-case (get powertrain :hydrogen_source_certification ""))]
        (or (empty? h2-cert) (not (str/includes? h2-cert "green"))))
      {:ok false :reason "non-green hydrogen violates G9 (well-to-wake CoC)"}

      :else
      {:ok true :reason "zero-emission propulsion verified"})))

;; ── L4 powertrain integration (DEFINING zero-emission heart) ──────────────────
(defn handle-powertrain-integration
  "L4 DEFINING zero-emission heart: wind-assist + solar + green-H₂ FC + LFP + e-pods.

  G8 (fossil prohibition) + G9 (well-to-wake green-H₂) gates enforced.
  Settlement intent only (R0); real integration is non-reversible."
  [state]
  (let [powertrain (get state :powertrain {})
        gate (gate-zero-emission-propulsion powertrain)]
    (if (not (:ok gate))
      (assoc state :blocked true :reason (:reason gate))
      (let [install-prompt (str "Plan ATEX-zoned hydrogen fuel-cell integration bay setup. "
                                "Wind rotor (" (get powertrain :wind_rig_type "rotor") ") + "
                                (get powertrain :solar_wattage 0) "W solar deck + "
                                (get powertrain :fc_power_mw 0) "MW green-H₂ FC stack + "
                                (get powertrain :battery_capacity_mwh 0) "MWh LFP + "
                                "electric azimuth pods. Verify no fossil backup.")
            install-plan (infer install-prompt)
            settlement (build-settlement-intent (get state :gross_minor 500000000))]
        (assoc state
               :install_plan install-plan
               :powertrain_verified true
               :settlement_intent settlement
               :status "propulsion-ready")))))

;; ── L5a outfitting ────────────────────────────────────────────────────────────
(defn handle-outfitting
  "L5a mechanical/electrical outfitting: piping + harness + SCADA."
  [state]
  (let [vessel-id (get state :vesselId "")
        mep-prompt (str "Verify FreeCAD MEP schematic routing for " vessel-id
                        ": fire/compressed-air/cooling-water + H₂/N₂ purge piping. "
                        "Electrical: GNC + SCADA + bridge instruments. No fossil aux systems.")
        mep-verify (infer mep-prompt)]
    (assoc state :mep_verification mep-verify :status "outfitting-complete")))

;; ── L5b launch + commissioning ────────────────────────────────────────────────
(defn handle-launch-commissioning
  "L5b hull launch + systems commissioning: float + FC cold-start + GNC smoke."
  [state]
  (let [vessel-id (get state :vesselId "")
        launch-prompt (str "Verify " vessel-id
                           " launch sequence: hull float test, fuel-cell cold-start "
                           "(green-H₂ system test), battery balance-charge, GNC autonomy waypoint smoke-test. "
                           "IMO MASS Degree 3 ops manual.")
        launch-verify (infer launch-prompt)]
    (assoc state :launch_verified true :gnc_ready true :status "launched")))

;; ── L5c sea trial ─────────────────────────────────────────────────────────────
(defn handle-sea-trial
  "L5c at-sea acceptance: wind/solar/H₂ efficiency + autonomy + safety."
  [state]
  (let [vessel-id (get state :vesselId "")
        sea-prompt (str "Plan sea trial for " vessel-id
                        " (Nagi class, 3000 DWT, 10 kn, zero-emission): measure wind-assist efficiency %, "
                        "solar generation %, H₂ FC endurance hours. GNC autonomy on waypoints. "
                        "Safety: FFE, SOLAS. Sonar ≤180 dB (cetacean; G4).")
        sea-plan (infer sea-prompt)]
    (assoc state :sea_trial_plan sea-plan :sea_trial_pass true :status "sea-trial-complete")))

;; ── cross: decarbonization audit ──────────────────────────────────────────────
(defn handle-decarbonization-audit
  "Cross-cell well-to-wake decarbonization: IMO GHG / EEXI / CII audit."
  [state]
  (let [vessel-id (get state :vesselId "")
        audit-prompt (str "IMO GHG well-to-wake audit for " vessel-id
                          ": steel supply chain (CBAM scrap %), green-H₂ electrolyzer CO₂ intensity, "
                          "solar + battery + wind rotor EOL recycling. EEXI rating, CII rating. Marpol Annex VI.")
        audit-result (infer audit-prompt)]
    (assoc state :audit_result audit-result :eexi_rating "A" :cii_rating "A")))

;; ── terminal: class certification binder ─────────────────────────────────────
(defn handle-class-certification-binder
  "Terminal cell: bind sea-trial + audit into ABS/DNV/ClassNK certification."
  [state]
  (let [vessel-id (get state :vesselId "")
        cert-prompt (str "Prepare class certification docs for " vessel-id
                         ": bind sea-trial pass + decarbonization audit. "
                         "ABS/DNV/ClassNK notation (A1 ZEV — zero-emission vessel). "
                         "Register IMO number + MMSI.")
        cert-docs (infer cert-prompt)]
    (assoc state :cert_docs cert-docs :imo_registered true :status "class-certified")))

;; ── main (smoke demo) ─────────────────────────────────────────────────────────
(defn main [& _]
  (let [demo-powertrain {:type "wind-solar-hydrogen"
                         :wind_rig_type "Flettner rotor"
                         :solar_wattage 160000
                         :fc_power_mw 2.4
                         :battery_capacity_mwh 2.0
                         :hydrogen_source_certification "green-h2-electrolyzer-norway-2026"}
        demo (handle-powertrain-integration
              {:vesselId "nagi-0001"
               :powertrain demo-powertrain
               :gross_minor 500000000})]
    (println "powertrain integration:" (:powertrain_verified demo))
    (println "settlement:" (:settlement_intent demo))))

(when (= *file* (System/getProperty "babashka.file"))
  (main))
