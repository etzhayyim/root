#!/usr/bin/env bb
;; Working Clojure port of py/agent.py (hodoki ELV disassembly + materials recovery actor).
(ns hodoki.py.agent
  "hodoki 解き — ELV disassembly + materials recovery langgraph actor (kotoba WASM cell).

  ADR-2605261215, R0 scaffold. Handlers over the ELV processing schema (intake audit,
  depollution, battery handling, parts harvest, catalyst recovery, shredding, data wipe,
  emissions audit, provenance binding), with hodoki's constitutional gates enforced:

    G2   mass-balance ≥98%       (kotoba-datomic-anchored audit)
    G5   charter-rider scan      (no military/weapon-carrying vehicles)
    G6   f-gas ≥95% capture      (UNEP Kigali Amendment alignment)
    G8   ecu-data-wipe mandatory (cryptographic destruction + witness ≥2 robots)
    G12  right-to-repair parts   (IPFS-pinned catalog with VIN provenance)
    G13  material recovery ≥95%  (cross-actor circular feed: kanayama + makura + silicon)
    G14  pgm recovery ≥95%       (PGM yield audit from catalytic converters)

  Settlement is USDC on Base L2 + ERC-4337 + TitheRouter 10% only — no fiat, no Stripe
  (S2). The platform holds no key; operator signs settlement (S3). R0: settlement stops
  at :intent (broadcast is S4-gated).

  Run:  bb --classpath 20-actors 20-actors/hodoki/py/agent.clj"
  (:require [clojure.string :as str])
  (:import [java.security MessageDigest]))

;; ── constants ──────────────────────────────────────────────────────────────────
(def ^:private tithe-bps 1000)   ; 10% TitheRouter auto-split (S2), basis points

;; ── G5 Charter Rider scan — no military/weapon/covert-modification vehicles ──────
(def ^:private prohibited-patterns
  ["military" "weapon" "armored" "ballistic" "surveillance"
   "drone" "robot-swarm" "autonomous-targeting" "covert"])

(defn scan-charter-compliance
  "G5 Charter §2(a-h) scan: reject military/weapon-carrying vehicles.
  Returns {:ok bool :reason str :status str}."
  [vin vehicle-desc]
  (let [desc-lower (str/lower-case vehicle-desc)
        hits (filterv #(str/includes? desc-lower %) prohibited-patterns)]
    (if (seq hits)
      {:ok false
       ;; match py's f-string list repr exactly (Python list = single quotes, ", " sep), not
       ;; clj pr-str's double-quote/space vector form, so the reason is byte-identical (parity-caught).
       :reason (str "Charter violation: [" (str/join ", " (map #(str "'" % "'") hits)) "] (G5)")
       :status "failed"}
      {:ok true
       :reason "Charter scan passed"
       :status "passed"})))

;; ── G6 F-gas capture gate ──────────────────────────────────────────────────────
(defn check-fgas-compliance
  "G6 F-gas (HFC/HFO) capture ≥95% by mass; no atmospheric venting.
  Returns {:ok bool :reason str}."
  ([fgas-mass-g]
   (check-fgas-compliance fgas-mass-g 95.0))
  ([fgas-mass-g target-pct]
   (cond
     (< fgas-mass-g 0)
     {:ok false :reason "F-gas mass cannot be negative"}

     (< (double target-pct) 95.0)
     {:ok false :reason (str "F-gas capture " target-pct "% < 95% (G6)")}

     :else
     {:ok true :reason (str "F-gas capture " target-pct "% ≥ 95% (G6)")})))

;; ── G8 ECU data wipe gate — cryptographic destruction + witness ≥2 robots ────────
(defn ecu-data-wipe-mandatory
  "G8 CONSTITUTIONAL FIRST: MANDATORY ECU + infotainment + telematics wipe.
  Returns {:ok bool :reason str} and optionally {:blocked true}."
  [ecu-wiped witness-count]
  (cond
    (not ecu-wiped)
    {:ok false :reason "ECU data wipe NOT completed (G8)" :blocked true}

    (< (int witness-count) 2)
    {:ok false
     :reason (str "Witness count " witness-count " < 2 robots (G8)")
     :blocked true}

    :else
    {:ok true :reason "ECU wipe + witness quorum ≥2 (G8)"}))

;; ── G12 Right-to-repair invariant — parts catalog with VIN provenance + DID ─────
(defn issue-part-did
  "G12 Issue DID for harvested part (IPFS-pinned, VIN-provenanced)."
  [vin part-name]
  (let [md (MessageDigest/getInstance "SHA-256")
        data (.getBytes (str vin ":" part-name) "UTF-8")
        digest (.digest md data)
        hex (apply str (map #(format "%02x" (bit-and % 0xff)) digest))]
    (str "did:web:hodoki.etzhayyim.com:part:" (subs hex 0 16))))

;; ── G13 Material recovery ≥95% gate ────────────────────────────────────────────
(defn calc-recovery-rate
  "G13 Material recovery ≥95%; ASR <5% to landfill.
  Returns {:ok bool :reason str} and on success :recovery_pct :asr_landfill_pct."
  [ferrous-kg non-ferrous-kg copper-kg asr-kg input-mass-kg]
  (let [total-recovered (+ (double ferrous-kg) (double non-ferrous-kg) (double copper-kg))
        inp (double input-mass-kg)
        recovery-pct (if (> inp 0) (* (/ total-recovered inp) 100) 0.0)
        asr-pct (if (> inp 0) (* (/ (double asr-kg) inp) 100) 0.0)]
    (cond
      (< recovery-pct 95.0)
      {:ok false
       :reason (str "Recovery " recovery-pct "% < 95% (G13)")
       :blocked true}

      (>= asr-pct 5.0)
      {:ok false
       :reason (str "ASR landfill " asr-pct "% >= 5% (G13)")
       :blocked true}

      :else
      {:ok true
       :reason (str "Recovery " recovery-pct "% ≥ 95%, ASR " asr-pct "% < 5% (G13)")
       :recovery_pct (int recovery-pct)
       :asr_landfill_pct (int asr-pct)})))

;; ── G14 PGM recovery ≥95% gate ─────────────────────────────────────────────────
(defn audit-pgm-yield
  "G14 PGM (Pt/Pd/Rh) recovery ≥95% from catalytic converters.
  Returns {:ok bool :reason str} and optionally {:blocked true}."
  [pgm-yield-pct]
  (if (< (double pgm-yield-pct) 95.0)
    {:ok false
     :reason (str "PGM yield " pgm-yield-pct "% < 95% (G14)")
     :blocked true}
    {:ok true
     :reason (str "PGM yield " pgm-yield-pct "% ≥ 95% (G14)")}))

;; ── Settlement — USDC + TitheRouter intent (NOT broadcast; S4-gated) ─────────────
(defn build-settlement-intent
  "USDC settlement split. 10% tithe → Public Fund. Stops at :intent — broadcast
  needs operator signature (S3).
  NOTE: R0 behaviour — state is 'executed' when buyer-sig-ref is provided, else 'intent'.
  This matches agent.py exactly (unlike the R2 Autonomous omise/ainori agents where
  executed is unconditional)."
  ([gross-minor]
   (build-settlement-intent gross-minor nil))
  ([gross-minor buyer-sig-ref]
   (let [gross (long gross-minor)
         tithe (quot (* gross tithe-bps) 10000)
         operator-payout (- gross tithe)]
     {:rail "usdc-base-l2"
      :grossMinor gross
      :titheMinor tithe
      :operatorPayoutMinor operator-payout
      :titheRouter "50-infra/etzhayyim-tithe-router"
      :state (if buyer-sig-ref "executed" "intent")
      :operatorSigRef (or buyer-sig-ref "")})))

;; ── Main handlers ────────────────────────────────────────────────────────────────

(defn handle-intake-audit
  "L1a: Intake audit — VIN + title + consent + Charter scan."
  [state]
  (let [vin (get state :vin "")
        vehicle-desc (get state :vehicle_desc "")
        result (scan-charter-compliance vin vehicle-desc)]
    (assoc state :charter_status (get result :status "pending"))))

(defn handle-depollution
  "L1b: Depollution — fluid drain + F-gas capture + airbag disarm."
  [state]
  (let [ecu-result (ecu-data-wipe-mandatory
                    (get state :ecu_wiped false)
                    (get state :witness_count 0))
        fgas-result (check-fgas-compliance
                     (get state :fgas_mass_g 0)
                     (get state :fgas_target_pct 0))
        overall-ok (and (:ok ecu-result) (:ok fgas-result))]
    (assoc state :status (if overall-ok "passed" "blocked"))))

(defn handle-battery-handling
  "L2: Battery handling — SoH measurement + routing."
  [state]
  (let [soh (int (get state :soh_pct 0))
        routing (cond
                  (>= soh 70) "hikari-second-life"
                  (>= soh 40) "cell-recycle"
                  :else       "kanayama-reclaim")]
    (assoc state :routing_decision routing)))

(defn handle-parts-harvest
  "L3a: Parts harvest — grade + DID + IPFS catalog (G12)."
  [state]
  (let [vin (get state :vin "")
        part-name (get state :part_name "")
        part-did (issue-part-did vin part-name)]
    (assoc state :part_did part-did)))

(defn handle-catalyst-recovery
  "L3b: Catalyst recovery — PGM yield audit ≥95% (G14)."
  [state]
  (let [result (audit-pgm-yield (get state :pgm_yield_pct 0))]
    (assoc state :status (if (:ok result) "passed" "blocked"))))

(defn handle-body-shred
  "L4: Body shred — ferrous/non-ferrous/Cu/ASR sort (G13)."
  [state]
  (let [result (calc-recovery-rate
                (get state :ferrous_kg 0)
                (get state :non_ferrous_kg 0)
                (get state :copper_kg 0)
                (get state :asr_kg 0)
                (get state :input_mass_kg 0))]
    (if (:ok result)
      (assoc state
             :recovery_pct (:recovery_pct result)
             :asr_landfill_pct (:asr_landfill_pct result))
      state)))

;; ── main (smoke demo) ─────────────────────────────────────────────────────────
(defn main [& _]
  (println "Charter scan (ok):"
           (:status (scan-charter-compliance "ABC123DEF456GH" "2024 Toyota Corolla")))
  (println "Charter scan (blocked):"
           (:status (scan-charter-compliance "XYZ789" "Military armored platform")))
  (println "F-gas capture (ok):" (:ok (check-fgas-compliance 100.0 95.5)))
  (println "Material recovery (ok):" (:ok (calc-recovery-rate 800 150 50 20 1000)))
  (println "PGM yield (ok):" (:ok (audit-pgm-yield 96.0)))
  (println "Settlement:" (build-settlement-intent 10000000)))

(when (= *file* (System/getProperty "babashka.file"))
  (main))
