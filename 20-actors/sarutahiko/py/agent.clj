#!/usr/bin/env bb
;; Working Clojure port of py/agent.py (sarutahiko heavy Class-8 truck manufacturing actor).
(ns sarutahiko.py.agent
  "sarutahiko 猿田彦 — Heavy Class-8 truck manufacturing langgraph actor (kotoba WASM cell).

  ADR-2605252500, R0 scaffold. Runs in-WASM on kotoba :8077. Handlers manage the
  vehicle manufacturing lifecycle:

    handle-vehicle-order       Create and manage vehicle orders
    handle-production-progress Update production stages and record attestations
    handle-quality             Record quality inspection results
    handle-vin-attestation     Bind VIN to kotoba-datomic with attestations

  LLM access is Murakumo-only via KotobaLLM (127.0.0.1:4000, gemma3:4b; G16). State is
  written back to the kotoba Datom log (G17). Settlement is USDC on Base L2 +
  ERC-4337 + TitheRouter 10% only — no fiat, no Stripe (G18). The platform holds
  no key; the member signs each settlement with their own passkey/smart-account
  (G15). Every stage is recorded as a Datom — no silent truncation.

  This R0 build computes and returns plans/records; it does not dispatch real factory
  work and does not broadcast settlements (both G11-gated; settlement stops at :intent).

  Run:  bb --classpath 20-actors 20-actors/sarutahiko/py/agent.clj")

;; ── constants ──────────────────────────────────────────────────────────────────
(def ^:private tithe-bps 1000)  ; 10% TitheRouter auto-split (G18), basis points

;; Vehicle order states
(def vehicle-order-flow
  ["draft" "placed" "in-production" "qc" "ready" "shipped" "cancelled"])

;; Production progress stages
(def production-stages
  ["frame-fabrication" "powertrain-assembly" "cab-body-forming" "final-marriage"
   "paint-finishing" "electrical-integration" "quality-road-test"
   "emissions-audit" "vin-attestation-binder"])

;; ── helper fns ─────────────────────────────────────────────────────────────────

(defn get-current-timestamp
  "Fixed ISO stub for R0/testing; py agent.py also returns a hardcoded value."
  []
  "2026-06-02T00:00:00Z")

(defn infer-llm
  "Murakumo-only LLM inference (G16). Returns offline sentinel when host not available."
  [_prompt]
  ;; In WASM host: would call (llm/infer model prompt). Offline sentinel matches agent.py.
  "LLM_NOT_AVAILABLE")

;; ── build-settlement-intent — MUST be defined before handlers that call it ─────
(defn build-settlement-intent
  "Compute the USDC settlement split. 10% tithe → Public Fund.
  Stops at :intent — broadcast needs a member signature (G15).
  NOTE: R0 behaviour — state is 'executed' when buyer-sig-ref is provided, else 'intent'.
  This matches agent.py exactly (unlike the R2 Autonomous omise/ainori where executed
  is unconditional)."
  ([gross-minor]
   (build-settlement-intent gross-minor nil))
  ([gross-minor buyer-sig-ref]
   (let [gross (long gross-minor)
         tithe (quot (* gross tithe-bps) 10000)
         factory-payout (- gross tithe)]
     {:rail              "usdc-base-l2"
      :grossMinor        gross
      :titheMinor        tithe
      :factoryPayoutMinor factory-payout
      :titheRouter       "50-infra/etzhayyim-tithe-router"
      :state             (if buyer-sig-ref "executed" "intent")
      :buyerSigRef       (or buyer-sig-ref "")})))

;; ── handle-vehicle-order — Create and manage vehicle orders ────────────────────
(defn handle-vehicle-order
  "Create and manage vehicle orders.
  Requires buyer DID + active SBT (G14 equivalent). Returns vehicle order record or error."
  [state]
  (let [order-id       (get state :order_id (get state "order_id"))
        buyer-did      (or (get state :buyer_did) (get state "buyer_did"))
        specs          (or (get state :specs) (get state "specs"))
        initial-state  (or (get state :initial_state) (get state "initial_state") "draft")
        sbt-active     (or (get state :sbt_active) (get state "sbt_active") false)]

    (if (or (nil? buyer-did) (not sbt-active))
      {"error" "Buyer DID missing or SBT not active (G14 equivalent)"
       "state" "cancelled"}

      (let [oid (or order-id
                    (str "vo.new.order." (mod (Math/abs (hash (or specs ""))) 10000)))
            order-record {":vehicle-order/id"        oid
                          ":vehicle-order/buyer-did"  buyer-did
                          ":vehicle-order/specs"      specs
                          ":vehicle-order/state"      initial-state}]
        {"vehicle_order" order-record}))))

;; ── handle-production-progress — Update production stages ────────────────────────
(defn handle-production-progress
  "Update production stages and record attestations.
  If a CID is provided (G3: IPFS-pinned media), an attestation record is also emitted."
  [state]
  (let [order-id  (or (get state :order_id) (get state "order_id"))
        stage     (or (get state :stage) (get state "stage"))
        cid       (or (get state :cid) (get state "cid"))
        details   (or (get state :details) (get state "details") "")
        timestamp (or (get state :timestamp) (get state "timestamp") (get-current-timestamp))]

    (if (or (nil? order-id) (nil? stage))
      {"error" "Order ID or stage missing"}

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
         "attestation"         attestation-record}))))

;; ── handle-quality — Record quality inspection results ───────────────────────────
(defn handle-quality
  "Record quality inspection results.
  pass → order 'ready'; fail → 'cancelled'; rework → back to 'in-production'."
  [state]
  (let [order-id            (or (get state :order_id) (get state "order_id"))
        result              (or (get state :result) (get state "result"))
        defects             (or (get state :defects) (get state "defects") [])
        inspector-did       (or (get state :inspector_did) (get state "inspector_did"))
        timestamp           (or (get state :timestamp) (get state "timestamp") (get-current-timestamp))
        current-order-state (or (get state :current_order_state) (get state "current_order_state") "in-production")]

    (if (or (nil? order-id) (nil? result) (nil? inspector-did))
      {"error" "Order ID, result, or inspector DID missing"}

      (let [quality-record {":quality/id"           (str "qc." order-id "." timestamp)
                            ":quality/order"        order-id
                            ":quality/result"       result
                            ":quality/defects"      defects
                            ":quality/inspector-did" inspector-did
                            ":quality/timestamp"    timestamp}
            new-order-state (cond
                              (= result "pass")   "ready"
                              (= result "fail")   "cancelled"
                              (= result "rework") "in-production"
                              :else               current-order-state)]
        {"quality_record"   quality-record
         "new_order_state"  new-order-state}))))

;; ── handle-vin-attestation — Bind VIN to kotoba-datomic with attestations ─────────
(defn handle-vin-attestation
  "Bind VIN to kotoba-datomic with attestations.
  Creates a vehicle record with a did:web DID (G13)."
  [state]
  (let [order-id                (or (get state :order_id) (get state "order_id"))
        vin                     (or (get state :vin) (get state "vin"))
        emissions-audit-id      (or (get state :emissions_audit_id) (get state "emissions_audit_id"))
        silen-vehicle-review-id (or (get state :silen_vehicle_review_id) (get state "silen_vehicle_review_id"))
        attestation-ids         (or (get state :attestation_ids) (get state "attestation_ids") [])
        timestamp               (or (get state :timestamp) (get state "timestamp") (get-current-timestamp))]

    (if (or (nil? order-id) (nil? vin))
      {"error" "Order ID or VIN missing"}

      (let [vehicle-did    (str "did:web:etzhayyim.com:sarutahiko:vehicle:" vin)
            vehicle-record {":vehicle/vin"           vin
                            ":vehicle/order"         order-id
                            ":vehicle/did"           vehicle-did
                            ":vehicle/attestations"  attestation-ids
                            ":vehicle/emissions-audit" emissions-audit-id
                            ":vehicle/final-review"  silen-vehicle-review-id}]
        {"vehicle_record" vehicle-record}))))

;; ── main (smoke demo) ─────────────────────────────────────────────────────────
(defn -main [& _]
  (println "--- Vehicle Order Demo ---")
  (let [order-state (handle-vehicle-order
                     {"buyer_did"     "did:web:member.example.etzhayyim.com"
                      "specs"         "Class-8 heavy duty truck, 6x4, B100 biodiesel engine"
                      "initial_state" "placed"
                      "sbt_active"    true})]
    (println "Vehicle Order:" order-state)
    (when (get order-state "vehicle_order")
      (let [order-id (get (get order-state "vehicle_order") ":vehicle-order/id")]
        (println "\n--- Production Progress Demo ---")
        (let [pp-frame (handle-production-progress
                        {"order_id" order-id
                         "stage"    "frame-fabrication"
                         "cid"      "bafybeifx7yeb55gn3f77q233z2b3jqv3m5jznm6z7q2f43x5f2"
                         "details"  "High-strength steel frame."})]
          (println "Frame Fabrication:" pp-frame)
          (let [pp-paint (handle-production-progress
                          {"order_id" order-id
                           "stage"    "paint-finishing"
                           "cid"      "bafybeifx7yeb55gn3f77q233z2b3jqv3m5jznm6z7q2f43x5f4"
                           "details"  "White coat applied."})]
            (println "Paint Finishing:" pp-paint)
            (println "\n--- Quality Inspection Demo ---")
            (let [qc-result (handle-quality
                             {"order_id"            order-id
                              "result"              "pass"
                              "inspector_did"       "did:web:inspector.example.etzhayyim.com"
                              "current_order_state" "qc"})]
              (println "Quality Check:" qc-result)
              (println "\n--- VIN Attestation Demo ---")
              (let [vin-attest (handle-vin-attestation
                                {"order_id"               order-id
                                 "vin"                    "TRUCKVIN0000000001"
                                 "emissions_audit_id"     "pp_emissions_audit_record_id"
                                 "silen_vehicle_review_id" "silen_review_record_id"
                                 "attestation_ids"        [(get (get pp-frame "attestation") ":attestation/id")
                                                           (get (get pp-paint "attestation") ":attestation/id")]})]
                (println "VIN Attestation:" vin-attest)
                (println "\n--- Settlement Demo ---")
                (println "Settlement:" (build-settlement-intent 8000000000))))))))))

(when (= *file* (System/getProperty "babashka.file"))
  (-main))
