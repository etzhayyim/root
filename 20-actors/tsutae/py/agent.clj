#!/usr/bin/env bb
;; Working Clojure port of py/agent.py (tsutae handheld comms device manufacturing actor).
(ns tsutae.py.agent
  "tsutae 伝え — handheld communication device manufacturing langgraph actor (kotoba WASM cell).

  ADR-2605261300, R0 scaffold. Runs in-WASM on kotoba :8077. Handlers manage the
  device manufacturing lifecycle:

    handle-device-order        Create and manage member device orders (SBT-gated)
    handle-production-progress Update the 8-stage assembly + record attestations
    handle-quality             Record QC / RF / functional results
    handle-device-attestation  Bind serial → per-device DID + BoM lineage (≥2 robot sig)

  LLM access is Murakumo-only via KotobaLLM (127.0.0.1:4000, gemma3:4b; G16). State is
  written back to the kotoba Datom log (G17). Settlement is USDC on Base L2 +
  ERC-4337 + TitheRouter 10% only — no fiat, no Stripe (G18); SBT↔SBT internal only
  (N9). The platform holds no key; the member signs each settlement (G15). Every
  stage is recorded as a Datom — no silent truncation.

  This R0 build computes and returns plans/records; it does not dispatch real factory
  work and does not broadcast settlements (both G11/G13-gated; settlement stops at
  :intent). Open SoC only (G9) — proprietary SoC is rejected, never assembled (N1).

  Run:  bb --classpath 20-actors 20-actors/tsutae/py/agent.clj")

;; ── constants ──────────────────────────────────────────────────────────────────
(def ^:private tithe-bps 1000)  ; 10% TitheRouter auto-split (G18), basis points

;; Device order states
(def device-order-flow
  ["draft" "placed" "in-production" "qc" "ready" "shipped" "cancelled"])

;; Production stages = the 8 tsutae Pregel cells (CLAUDE.md + manifest.edn)
(def production-stages
  ["pcb-smt" "chassis-assembly" "display-attachment" "firmware-load"
   "final-qc" "packaging" "device-attestation" "recycling-intake"])

;; G9: open SoC allow-list (R1 open RISC-V; R2+ iwakura). Proprietary = rejected (N1).
(def open-soc-allowlist
  #{"StarFive-JH7110" "SiFive-HiFive-Unmatched" "Allwinner-D1" "iwakura"})

(def proprietary-soc
  #{"Snapdragon" "Apple-A" "Exynos" "Helio" "Dimensity"})

;; ── helper fns ─────────────────────────────────────────────────────────────────

(defn _now
  "Fixed ISO stub for R0/testing; py agent.py also returns a hardcoded value."
  []
  "2026-06-02T00:00:00Z")

(defn _infer_llm
  "Murakumo-only LLM inference (G16). Returns offline sentinel when host not available.
  Replicates the try/except → LLM_INFERENCE_FAILED structure; offline path → LLM_NOT_AVAILABLE."
  [_prompt]
  ;; In WASM host: would call (llm/infer model prompt).
  ;; try branch → LLM_INFERENCE_FAILED; no-llm branch → LLM_NOT_AVAILABLE (offline default).
  "LLM_NOT_AVAILABLE")

(defn is_open_soc
  "G9 enforcement: open RISC-V only; proprietary SoC rejected (N1).
  Only an OPEN_SOC_ALLOWLIST prefix match is open; a PROPRIETARY_SOC (or unknown) is NOT open."
  [soc]
  ;; Reject if any proprietary prefix matches first (mirrors Python logic)
  (if (some #(clojure.string/starts-with? soc %) proprietary-soc)
    false
    (boolean (some #(clojure.string/starts-with? soc %) open-soc-allowlist))))

;; ── build-settlement-intent — MUST be defined before handlers ─────────────────
(defn build_settlement_intent
  "Compute the USDC settlement split. 10% tithe → Public Fund.
  Stops at :intent — broadcast needs a member signature (G15).
  NOTE: R0 behaviour — state is 'executed' when buyer-sig-ref is provided, else 'intent'.
  This matches agent.py exactly."
  ([gross-minor]
   (build_settlement_intent gross-minor nil))
  ([gross-minor buyer-sig-ref]
   (let [gross (long gross-minor)
         tithe (quot (* gross tithe-bps) 10000)
         factory-payout (- gross tithe)]
     {"rail"               "usdc-base-l2"
      "grossMinor"         gross
      "titheMinor"         tithe
      "factoryPayoutMinor" factory-payout
      "titheRouter"        "50-infra/etzhayyim-tithe-router"
      "state"              (if buyer-sig-ref "executed" "intent")
      "buyerSigRef"        (or buyer-sig-ref "")})))

;; ── handle-device-order — SBT-gated member order intake ───────────────────────
(defn handle_device_order
  "Create and manage member device orders.
  Requires buyer DID + active SBT (N9 SBT↔SBT internal). Open SoC only (G9/N1)."
  [state]
  (let [order-id      (or (get state :order_id) (get state "order_id"))
        buyer-did     (or (get state :buyer_did) (get state "buyer_did"))
        specs         (or (get state :specs) (get state "specs"))
        soc           (or (get state :soc) (get state "soc") "StarFive-JH7110")
        initial-state (or (get state :initial_state) (get state "initial_state") "draft")
        sbt-active    (or (get state :sbt_active) (get state "sbt_active") false)]

    (if (or (nil? buyer-did) (not sbt-active))
      {"error" "Buyer DID missing or SBT not active (N9 SBT↔SBT internal)"
       "state" "cancelled"}

      (if (not (is_open_soc soc))
        {"error" (str "SoC " soc " rejected — open RISC-V only (G9/N1)")
         "state" "cancelled"}

        (let [oid (or order-id
                      (str "do.new.order." (mod (Math/abs (hash (or specs ""))) 10000)))
              order-record {":device-order/id"        oid
                            ":device-order/buyer-did" buyer-did
                            ":device-order/specs"     specs
                            ":device-order/soc"       soc
                            ":device-order/state"     initial-state}]
          {"device_order" order-record})))))

;; ── handle-production-progress — 8-stage assembly + attestation ───────────────
(defn handle_production_progress
  "Update the 8-stage assembly + record attestations.
  If a CID is provided (G14: IPFS-pinned per-stage evidence), an attestation record is emitted."
  [state]
  (let [order-id  (or (get state :order_id) (get state "order_id"))
        stage     (or (get state :stage) (get state "stage"))
        cid       (or (get state :cid) (get state "cid"))
        details   (or (get state :details) (get state "details") "")
        timestamp (or (get state :timestamp) (get state "timestamp") (_now))]

    (if (or (nil? order-id) (nil? stage))
      {"error" "Order ID or stage missing"}

      (if (not (some #{stage} production-stages))
        {"error" (str "unknown stage " stage " (not one of the 8 tsutae cells)")}

        (let [progress-record {":production-progress/id"        (str "pp." order-id "." stage)
                               ":production-progress/order"     order-id
                               ":production-progress/stage"     stage
                               ":production-progress/timestamp" timestamp
                               ":production-progress/note"      (str "Stage " stage " completed."
                                                                      (when (seq details)
                                                                        (str " Details: " details)))}
              attestation-record (when cid
                                   {":attestation/id"        (str "attest." order-id "." stage)
                                    ":attestation/order"     order-id
                                    ":attestation/type"      stage
                                    ":attestation/cid"       cid
                                    ":attestation/timestamp" timestamp
                                    ":attestation/details"   details})]
          {"production_progress" progress-record
           "attestation"         attestation-record})))))

;; ── handle-quality — QC / RF / functional result ─────────────────────────────
(defn handle_quality
  "Record QC / RF / functional result.
  pass → order 'ready'; fail → 'cancelled'; rework → back to 'in-production'."
  [state]
  (let [order-id            (or (get state :order_id) (get state "order_id"))
        result              (or (get state :result) (get state "result"))
        defects             (or (get state :defects) (get state "defects") [])
        inspector-did       (or (get state :inspector_did) (get state "inspector_did"))
        timestamp           (or (get state :timestamp) (get state "timestamp") (_now))
        current-order-state (or (get state :current_order_state) (get state "current_order_state") "in-production")]

    (if (or (nil? order-id) (nil? result) (nil? inspector-did))
      {"error" "Order ID, result, or inspector DID missing"}

      (let [quality-record {":quality/id"            (str "qc." order-id "." timestamp)
                            ":quality/order"         order-id
                            ":quality/result"        result
                            ":quality/defects"       defects
                            ":quality/inspector-did" inspector-did
                            ":quality/timestamp"     timestamp}
            new-order-state (cond
                              (= result "pass")   "ready"
                              (= result "fail")   "cancelled"
                              (= result "rework") "in-production"
                              :else               current-order-state)]
        {"quality_record"  quality-record
         "new_order_state" new-order-state}))))

;; ── handle-device-attestation — serial → per-device DID + BoM lineage ─────────
(defn handle_device_attestation
  "Bind serial → per-device DID + BoM lineage (G4/G14).
  Requires ≥2 distinct robot signers (G4 witness quorum)."
  [state]
  (let [order-id          (or (get state :order_id) (get state "order_id"))
        serial            (or (get state :serial) (get state "serial"))
        bom-lineage-cids  (or (get state :bom_lineage_cids) (get state "bom_lineage_cids") [])
        robot-signers     (or (get state :robot_signers) (get state "robot_signers") [])
        timestamp         (or (get state :timestamp) (get state "timestamp") (_now))]

    (if (or (nil? order-id) (nil? serial))
      {"error" "Order ID or serial missing"}

      ;; G4: witness quorum ≥2 distinct robot signers
      (if (< (count (set robot-signers)) 2)
        {"error" "G4: fewer than 2 distinct robot signers"
         "accept" false}

        (let [device-did    (str "did:web:etzhayyim.com:tsutae:device:" serial)  ; G14
              device-record {":device/serial"             serial
                             ":device/order"              order-id
                             ":device/did"                device-did
                             ":device/bom-lineage"        bom-lineage-cids
                             ":device/signers"            (vec (set robot-signers))
                             ":device/repair-event-ready" true}]  ; G14
          {"device_record" device-record
           "accept"        true})))))

;; ── main (smoke demo) ─────────────────────────────────────────────────────────
(defn -main [& _]
  (println "--- Device Order Demo ---")
  (let [od (handle_device_order
            {"buyer_did"     "did:web:member.example.etzhayyim.com"
             "specs"         "≤200g handheld, open RISC-V, LCD, removable cellular"
             "soc"           "StarFive-JH7110"
             "initial_state" "placed"
             "sbt_active"    true})]
    (println "Device Order:" od)
    (println "\n--- Proprietary SoC refusal (G9/N1) ---")
    (println (handle_device_order {"buyer_did" "did:web:m" "soc" "Snapdragon-8" "sbt_active" true}))
    (println "\n--- Settlement Demo ---")
    (println "Settlement:" (build_settlement_intent 60000000))))

(when (= *file* (System/getProperty "babashka.file"))
  (-main))
