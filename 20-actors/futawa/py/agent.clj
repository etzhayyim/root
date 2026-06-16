#!/usr/bin/env bb
;; Working Clojure port of py/agent.py (futawa motorcycle manufacturing actor).
(ns futawa.py.agent
  "futawa 二輪 — motorcycle manufacturing langgraph actor (kotoba WASM cell).

  ADR-2605261330, R0 scaffold. Runs in-WASM on kotoba :8077. Handlers over the
  motorcycle manufacturing schema (frame welding / engine / drivetrain / electrical /
  suspension / body / assembly / test / provenance) with futawa's constitutional gates:

    G7  ABS-mandatory       >=125cc / >=6kW; NO ABS-delete (safety non-negotiable)
    G8  anti-surveillance  NO GPS / telematics / connected-app / V2X / proprietary-DRM
    G11 capacity caps       <=250cc / <=15kW / <=200kg dry weight
    G12 right-to-repair     IPFS-pinned parts catalog + CAD + firmware source + manual
    G13 recycled materials  >=10% recycled mass; hodoki VIN pre-registration
    G14 30-year service     frame + engine + transmission designed 30y fatigue + wear

  LLM access is Murakumo-only via KotobaLLM (127.0.0.1:4000, gemma3:4b; G9). State is
  written back to the kotoba Datom log (G15). Settlement is USDC on Base L2 + ERC-4337
  + TitheRouter 10% only — no fiat (G16). The platform holds no key; the member signs
  each settlement (G17). Compute-only R0; settlement stops at :intent (G18).

  Run:  bb --classpath 20-actors 20-actors/futawa/py/agent.clj"
  (:require [clojure.string :as str]))

;; ── constants ──────────────────────────────────────────────────────────────────
(def TITHE_BPS 1000)              ; 10% TitheRouter auto-split (G16), basis points

;; G11 capacity caps
(def MAX_DISPLACEMENT_CC 250)
(def MAX_POWER_KW 15.0)
(def MAX_DRY_WEIGHT_KG 200.0)

;; G6 sound limit
(def SOUND_LIMIT_DB 80.0)

;; G8 prohibited surveillance components (matched case-insensitively via str/includes?)
(def PROHIBITED_SURVEILLANCE #{"gps" "telematics" "connected-app" "v2x" "diagnostic-drm"})

;; ── _infer — Murakumo-only inference (G9) ─────────────────────────────────────
(defn _infer
  "Murakumo-only inference (G9). Returns offline sentinel when host not available."
  [_prompt]
  ;; In WASM host: would call (llm/infer model prompt). Offline sentinel matches agent.py.
  "LLM_NOT_AVAILABLE")

;; ── G7 — ABS mandatory gate ───────────────────────────────────────────────────
(defn g7_abs_mandatory
  "Check if ABS is mandatory (G7).
  Returns {:abs_mandatory bool :reason str}."
  [displacement-cc power-kw]
  (let [mandatory (and (>= (long displacement-cc) 125)
                       (>= (double power-kw) 6.0))]
    {:abs_mandatory mandatory
     :reason (if mandatory
               "ABS-mandatory >=125cc / >=6kW electric"
               "ABS optional")}))

;; ── G8 — anti-surveillance check ──────────────────────────────────────────────
(defn g8_surveillance_check
  "Check for prohibited surveillance components (G8).
  Returns {:ok bool :reason str}."
  [bom-items]
  (let [hits (filter (fn [item]
                       (let [lower (str/lower-case (str/trim (str item)))]
                         (some #(str/includes? lower %) PROHIBITED_SURVEILLANCE)))
                     bom-items)]
    (if (seq hits)
      {:ok false :reason (str "prohibited surveillance: " (vec hits) " (G8)")}
      {:ok true :reason "no surveillance components"})))

;; ── G11 — capacity caps gate ──────────────────────────────────────────────────
(defn g11_capacity_caps
  "Validate G11 capacity caps.
  Returns {:ok bool :reason str}."
  [displacement-cc power-kw dry-weight-kg]
  (cond
    (> (long displacement-cc) MAX_DISPLACEMENT_CC)
    {:ok false :reason (str "displacement " displacement-cc " > " MAX_DISPLACEMENT_CC "cc (G11)")}

    (> (double power-kw) MAX_POWER_KW)
    {:ok false :reason (str "power " power-kw " > " MAX_POWER_KW "kW (G11)")}

    (> (double dry-weight-kg) MAX_DRY_WEIGHT_KG)
    {:ok false :reason (str "dry weight " dry-weight-kg " > " MAX_DRY_WEIGHT_KG "kg (G11)")}

    :else
    {:ok true :reason "within G11 capacity caps"}))

;; ── G6 — sound check gate ─────────────────────────────────────────────────────
(defn g6_sound_check
  "Check sound emission limit (G6).
  Returns {:ok bool :reason str}."
  [sound-db]
  (if (> (double sound-db) SOUND_LIMIT_DB)
    {:ok false :reason (str "sound " sound-db " > " SOUND_LIMIT_DB " dB(A) (G6)")}
    {:ok true :reason (str "sound <=" SOUND_LIMIT_DB " dB(A)")}))

;; ── build_settlement_intent — USDC + TitheRouter (G16/G17/G18) ────────────────
(defn build_settlement_intent
  "USDC settlement split. 10% tithe -> Public Fund (G16). Stops at :intent.
  NOTE: R0 behaviour — state is 'executed' when buyer-sig-ref is provided, else 'intent'.
  This matches agent.py exactly."
  ([gross-minor]
   (build_settlement_intent gross-minor nil))
  ([gross-minor buyer-sig-ref]
   (let [gross (long gross-minor)
         tithe (quot (* gross TITHE_BPS) 10000)
         maker-payout (- gross tithe)]
     {:rail             "usdc-base-l2"
      :grossMinor       gross
      :titheMinor       tithe
      :makerPayoutMinor maker-payout
      :titheRouter      "50-infra/etzhayyim-tithe-router"
      :state            (if buyer-sig-ref "executed" "intent")
      :buyerSigRef      (or buyer-sig-ref "")})))

;; ── stage handlers ─────────────────────────────────────────────────────────────

(defn handle_frame_welding
  "L1 frame welding attestation (R0: returns intent, does not execute)."
  [state]
  (merge state
         {:frame_attestation
          {:id           (get state :frame_id (get state "frame_id" "frame-pending"))
           :material_lot (get state :material_lot (get state "material_lot" ""))
           :weld_quality (if (= "tig" (or (get state :weld_type) (get state "weld_type")))
                           "vision-guided-tig"
                           "vision-guided-mig")
           :roundness_um 0
           :status       "intent"}}))

(defn handle_engine_assembly
  "L2a engine assembly with G11 cap check."
  [state]
  (let [displacement-cc (or (get state :displacement_cc) (get state "displacement_cc") 0)
        power-kw        (or (get state :power_kw) (get state "power_kw") 0.0)
        dry-weight-kg   (or (get state :dry_weight_kg) (get state "dry_weight_kg") 0.0)
        caps            (g11_capacity_caps displacement-cc power-kw dry-weight-kg)]
    (if-not (:ok caps)
      (merge state {:engine_attestation {:error (:reason caps) :blocked true}})
      (merge state
             {:engine_attestation
              {:id              (or (get state :engine_id) (get state "engine_id") "engine-pending")
               :displacement_cc displacement-cc
               :power_kw        power-kw
               :torque_nm       (or (get state :torque_nm) (get state "torque_nm") 0.0)
               :g11_cap_verified true
               :status          "intent"}}))))

(defn handle_electrical_harness
  "L3a electrical harness + G8 surveillance check."
  [state]
  (let [bom-items (or (get state :bom_items) (get state "bom_items") [])
        bom       (g8_surveillance_check bom-items)]
    (if-not (:ok bom)
      (merge state {:electrical_attestation {:error (:reason bom) :blocked true}})
      (merge state
             {:electrical_attestation
              {:id                    (or (get state :electrical_id) (get state "electrical_id") "electrical-pending")
               :g8_surveillance_clear true
               :status                "intent"}}))))

(defn handle_suspension_brake
  "L3b suspension + brake with G7 ABS-mandatory check."
  [state]
  (let [displacement-cc (or (get state :displacement_cc) (get state "displacement_cc") 0)
        power-kw        (or (get state :power_kw) (get state "power_kw") 0.0)
        abs-check       (g7_abs_mandatory displacement-cc power-kw)]
    (merge state
           {:suspension_brake_attestation
            {:id                    (or (get state :suspension_brake_id) (get state "suspension_brake_id") "suspension-brake-pending")
             :abs_mandatory_certified (:abs_mandatory abs-check)
             :status                "intent"}})))

(defn handle_body_paint
  "L4 body paint (G5 Charter scan assumed passed)."
  [state]
  (merge state
         {:paint_attestation
          {:id                (or (get state :paint_id) (get state "paint_id") "paint-pending")
           :g5_charter_scan_pass true
           :status            "intent"}}))

(defn handle_final_assembly
  "L5a final assembly + G12 parts catalog + G13 hodoki pre-reg."
  [state]
  (merge state
         {:vehicle_lot_attestation
          {:id                 (or (get state :vehicle_lot_id) (get state "vehicle_lot_id") "vehicle-pending")
           :vin                (or (get state :vin) (get state "vin") "")
           :parts_catalog_cid  (or (get state :parts_catalog_cid) (get state "parts_catalog_cid") "")
           :hodoki_preregister_ok true
           :status             "intent"}}))

(defn handle_test_dyno_road
  "L5b dyno testing + G6 sound check."
  [state]
  (let [sound-db (or (get state :sound_db) (get state "sound_db") 0.0)
        sound-ok (g6_sound_check sound-db)]
    (if-not (:ok sound-ok)
      (merge state {:test_record {:error (:reason sound-ok) :blocked true}})
      (merge state
             {:test_record
              {:id        (or (get state :test_id) (get state "test_id") "test-pending")
               :power_kw  (or (get state :dyno_power_kw) (get state "dyno_power_kw") 0.0)
               :torque_nm (or (get state :dyno_torque_nm) (get state "dyno_torque_nm") 0.0)
               :sound_db  sound-db
               :abs_pass  (or (get state :abs_pass) (get state "abs_pass") false)
               :result    (if (:ok sound-ok) "pass" "fail")
               :status    "intent"}}))))

(defn handle_provenance_binder
  "L5c terminal provenance binder (Council gate, R0 stops at intent)."
  [state]
  (merge state
         {:silen_mobility_review
          {:id                    (or (get state :review_id) (get state "review_id") "review-pending")
           :provenance_chain_cid  (or (get state :provenance_cid) (get state "provenance_cid") "")
           :council_approval      "pending"
           :status                "intent"}}))

;; ── main (smoke demo) ─────────────────────────────────────────────────────────
(defn main [& _]
  (println "frame welding:"
           (get-in (handle_frame_welding {:frame_id "f1" :weld_type "tig"})
                   [:frame_attestation :id]))
  (println "engine (OK):"
           (get-in (handle_engine_assembly {:engine_id "e1" :displacement_cc 200 :power_kw 12.0 :dry_weight_kg 150.0})
                   [:engine_attestation :g11_cap_verified]))
  (println "engine (OVER):"
           (get-in (handle_engine_assembly {:engine_id "e2" :displacement_cc 300 :power_kw 12.0 :dry_weight_kg 150.0})
                   [:engine_attestation :blocked]))
  (println "surveillance:"
           (get-in (handle_electrical_harness {:bom_items ["harness" "GPS module"]})
                   [:electrical_attestation :blocked]))
  (println "ABS check:" (g7_abs_mandatory 150 10.0))
  (println "settlement:" (build_settlement_intent 10000000)))

(when (= *file* (System/getProperty "babashka.file"))
  (main))
