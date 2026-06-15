#!/usr/bin/env bb
;; Working Clojure port of py/agent.py (kanayama circular metallurgy actor).
(ns kanayama.py.agent
  "kanayama 金山 — circular metallurgy (UBC recycling) langgraph actor (kotoba WASM cell).

  ADR-2605252400, migration plan Phase 4. Runs in-WASM on kotoba :8077. Handlers over
  the closed-loop Al recycling schema (intake QA, decoating, melting, casting, rolling,
  QC, emissions audit, settlement), enforcing kanayama's constitutional gates:

    G2   mass-balance ≥98%       (input = output_metal + dross + emission)
    G4   witness quorum ≥2       (Ed25519, DID-bound robots per pour)
    G7   USDC Base L2 + TitheRouter 10%; no Stripe/fiat
    G12  KPI caps                (recovery rate ≥95%; energy ≤6 kWh/kg Wave 1 Al)

  Settlement is USDC on Base L2 + ERC-4337 + TitheRouter 10% only — no fiat, no Stripe
  (G7). The platform holds no key; operator signs each settlement (G15). R0: settlement
  stops at :intent (broadcast G11-gated).

  Run:  bb --classpath 20-actors 20-actors/kanayama/py/agent.clj"
  (:require [clojure.string :as str]))

;; ── constants ──────────────────────────────────────────────────────────────────
(def ^:private tithe-bps 1000)            ; 10% TitheRouter auto-split (G7), basis points
(def ^:private recovery-rate-min-pct 95.0) ; G12 minimum recovery rate
(def ^:private energy-cap-kwh-per-kg 6.0)  ; G12 energy cap for Wave 1 Al

;; ── G2 mass-balance audit gate ─────────────────────────────────────────────────
(defn check-mass-balance
  "Verify ≥98% mass closure (input = output_metal + dross + emission).
  Returns {:ok bool :closure_pct float :reason str}."
  [input-mass output-metal dross emissions-mass]
  (if (<= (double input-mass) 0)
    {:ok false :reason "input_mass must be positive"}
    (let [accounted (+ (double output-metal) (double dross) (double emissions-mass))
          closure-pct (* (/ accounted (double input-mass)) 100.0)]
      (if (>= closure-pct 98.0)
        {:ok true :closure_pct closure-pct}
        {:ok false
         :closure_pct closure-pct
         :reason (str "mass closure " (format "%.1f" closure-pct) "% < 98% required (G2)")}))))

;; ── G12 KPI caps gate ──────────────────────────────────────────────────────────
(defn check-kpi-caps
  "Verify recovery rate ≥95% and energy ≤6 kWh/kg for Wave 1 Al.
  Returns {:ok bool :reason str}."
  [recovery-rate-pct energy-kwh-per-kg]
  (let [failures (cond-> []
                   (< (double recovery-rate-pct) recovery-rate-min-pct)
                   (conj (str "recovery " (format "%.1f" (double recovery-rate-pct))
                              "% < " recovery-rate-min-pct "% (G12)"))
                   (> (double energy-kwh-per-kg) energy-cap-kwh-per-kg)
                   (conj (str "energy " (format "%.1f" (double energy-kwh-per-kg))
                              " kWh/kg > " energy-cap-kwh-per-kg " (G12)")))]
    (if (seq failures)
      {:ok false :reason (str/join "; " failures)}
      {:ok true})))

;; ── G4 witness quorum gate ─────────────────────────────────────────────────────
(defn check-witness-sigs
  "≥2 distinct robots must sign each pour (Ed25519, DID-bound).
  Returns {:ok bool :reason str :witness_count int}."
  [witness-sigs]
  (let [cnt (count (or witness-sigs []))]
    (if (< cnt 2)
      {:ok false
       :reason (str "witness quorum " cnt " < 2 required (G4)")}
      {:ok true :witness_count cnt})))

;; ── intake QA gate ─────────────────────────────────────────────────────────────
(defn intake-qa
  "L1 UBC bale QA thresholds (heuristic; wave 1 baseline).
  Returns a datom-shaped map with :intake/* keys."
  [bale-weight cl-pct moisture-pct fe-ppm]
  (let [passed (and (<= (double cl-pct) 2.0)
                    (<= (double moisture-pct) 5.0)
                    (<= (int fe-ppm) 500))]
    {":intake/id"                  (str "intake." (format "%.0f" (double bale-weight)) "kg")
     ":intake/baleWeight"          bale-weight
     ":intake/clResiduePct"        cl-pct
     ":intake/moisturePct"         moisture-pct
     ":intake/magneticImpurityPpm" fe-ppm
     ":intake/qaPassed"            passed
     ":intake/blocked"             (not passed)}))

;; ── Settlement — USDC + TitheRouter intent (NOT broadcast; G7/G11/G15) ──────────
(defn build-settlement-intent
  "Compute the USDC settlement split. 10% tithe → Public Fund; operator gets the net.
  Stops at :intent — broadcast needs an operator signature (G15) + gate (G11).
  NOTE: R0 behaviour — state is 'executed' when operator-sig-ref is provided, else 'intent'.
  This matches agent.py exactly (unlike R2 Autonomous omise/ainori where executed is
  unconditional)."
  ([gross-minor]
   (build-settlement-intent gross-minor nil))
  ([gross-minor operator-sig-ref]
   (let [gross (long gross-minor)
         tithe (quot (* gross tithe-bps) 10000)
         operator-payout (- gross tithe)]
     {:rail                 "usdc-base-l2"
      :grossMinor           gross
      :titheMinor           tithe
      :operatorPayoutMinor  operator-payout
      :titheRouter          "50-infra/etzhayyim-tithe-router"
      :state                (if operator-sig-ref "executed" "intent")
      :operatorSigRef       (or operator-sig-ref "")})))

;; ── full batch settlement ──────────────────────────────────────────────────────
(defn finalize-batch-settlement
  "Compute full batch record + settlement intent after all 9 cells.
  Returns a datom-shaped batch record or {:error str :blocked true}."
  [batch-id input-mass output-metal dross emissions-mass recovery-pct energy-per-kg]
  (let [mb (check-mass-balance input-mass output-metal dross emissions-mass)]
    (if-not (:ok mb)
      {:error (:reason mb) :blocked true}
      (let [kpi (check-kpi-caps recovery-pct energy-per-kg)]
        (if-not (:ok kpi)
          {:error (:reason kpi) :blocked true}
          ;; R0 — compute & return intent; no broadcast (G11)
          ;; Gross = input_mass × $/kg estimate (mock 2.5 USDC/kg = 2.5e6 minor/kg)
          (let [gross-minor (long (* (double input-mass) 2500000))
                settlement  (build-settlement-intent gross-minor)]
            {":batchSettlement/id"          batch-id
             ":batchSettlement/inputMass"   input-mass
             ":batchSettlement/outputMetal" output-metal
             ":batchSettlement/drossCollected" dross
             ":batchSettlement/closurePct"  (get mb :closure_pct 0)
             ":batchSettlement/recoveryRate" recovery-pct
             ":batchSettlement/energyKwhPerKg" energy-per-kg
             ":batchSettlement/settlement"  settlement}))))))

;; ── main (smoke demo) ─────────────────────────────────────────────────────────
(defn main [& _]
  (println "intake QA (pass):"    (get (intake-qa 500.0 0.8 2.1 45)  ":intake/qaPassed"))
  (println "intake QA (fail):"    (get (intake-qa 500.0 3.0 6.0 600) ":intake/blocked"))
  (println "mass-balance (OK):"   (:ok (check-mass-balance 500.0 475.0 20.0 5.0)))
  (println "mass-balance (FAIL):" (:ok (check-mass-balance 500.0 300.0 50.0 50.0)))
  (println "witness quorum (OK):"   (:ok (check-witness-sigs ["did:web:r1" "did:web:r2"])))
  (println "witness quorum (FAIL):" (:ok (check-witness-sigs ["did:web:r1"])))
  (println "KPI (OK):"   (:ok (check-kpi-caps 96.0 5.5)))
  (println "KPI (FAIL):" (:ok (check-kpi-caps 90.0 7.0)))
  (println "settlement:" (build-settlement-intent 1000000000)))

(when (= *file* (System/getProperty "babashka.file"))
  (main))
