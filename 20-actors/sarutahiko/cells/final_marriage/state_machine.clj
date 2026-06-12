;; ported from 20-actors/sarutahiko/cells/final_marriage/state_machine.py (unit_refactor stage 0)
;; Final marriage state machine — ADR-2605252500 L4.
(ns sarutahiko.cells.final-marriage.state-machine
  (:require [clojure.string] [clojure.set] [clojure.edn]))

(declare marriage-phase marriage-state transition-to-inputs-verified transition-to-chassis-lowered transition-to-cab-dropped transition-to-powertrain-mounted transition-to-harness-connected transition-to-attestation-emitted)

(def marriage-phase
  {:init "init"
   :inputs-verified "inputs_verified"
   :chassis-lowered "chassis_lowered"
   :cab-dropped "cab_dropped"
   :powertrain-mounted "powertrain_mounted"
   :harness-connected "harness_connected"
   :attestation-emitted "attestation_emitted"})

(def marriage-state-initial-values {:phase nil :chassis-id nil :completion-pct 0 :inputs nil :critical-torques nil :robot-signatures nil})

(defn marriage-state [this]
  (let [phase (:phase this)
        chassis-id (:chassis-id this)
        completion-pct (:completion-pct this)
        inputs (:inputs this)
        critical-torques (:critical-torques this)
        robot-signatures (:robot-signatures this)]
    {:phase phase
     :chassis-id chassis-id
     :completion-pct completion-pct
     :inputs inputs
     :critical-torques critical-torques
     :robot-signatures robot-signatures}))

(defn transition-to-inputs-verified [state]
  (let [s (merge {} state) ; Assuming state is a map representing the current state structure
        marriage-state (get s :marriage-state {})
        new-inputs {"frameAttestationCid" "bafkreiframeatt..."
                   "powertrainAttestationCid" "bafkreiptatt..."
                   "cabBodyAttestationCid" "bafkreicabatt..."}
        s-with-inputs (assoc marriage-state :inputs new-inputs)
        s-with-phase (assoc s-with-inputs :phase :INPUTS_VERIFIED) ; Assuming MarriagePhase is represented by symbols or strings
        s-final (assoc s-with-phase :completionPct 15)]
    {:marriage-state s-final, :next-node "lower"}))

(defn transition-to-chassis-lowered [state]
  (let [marriage-state (get state "marriage_state")
        s (if marriage-state
              ;; Assuming MarriageState is a class/struct that can be initialized from a map
              ;; In Clojure, we treat this as updating an immutable map representation of the state.
              (merge {} marriage-state)
              {})
    new-state (assoc s :phase :CHASSIS_LOWERED
                    :completionPct 35)]
    {:marriage-state new-state
     :next-node "cab"}))

(defn transition-to-cab-dropped [state]
  (let [s (merge (get state "marriage_state" {})
                 {:criticalTorques
                  [{:fastener "cab_mount_1" :torqueNm 320 :specNm 320 :tolerancePct 5}
                   {:fastener "cab_mount_2" :torqueNm 315 :specNm 320 :tolerancePct 5}
                   {:fastener "cab_mount_3" :torqueNm 322 :specNm 320 :tolerancePct 5}
                   {:fastener "cab_mount_4" :torqueNm 318 :specNm 320 :tolerancePct 5}]
                  :phase :CAB_DROPPED
                  :completionPct 55})]
    {:marriage-state s, :next-node "powertrain"}))

(defn transition-to-powertrain-mounted [state]
  (let [s (merge state {} (:marriage-state state)) ; Simulating object creation from dict
        extra [{:fastener "engine_mount_left" :torqueNm 450 :specNm 450 :tolerancePct 5}
                {:fastener "engine_mount_right" :torqueNm 448 :specNm 450 :tolerancePct 5}
                {:fastener "transmission_mount" :torqueNm 280 :specNm 280 :tolerancePct 5}]
        current-critical-torques (get state :marriage-state.criticalTorques)
        new-critical-torques (if current-critical-torques
                               (concat current-critical-torques extra)
                               extra)
        updated-state (assoc s
                           :phase MarriagePhase/POWERTRAIN_MOUNTED
                           :completionPct 75
                           :criticalTorques new-critical-torques)]
    {:marriage-state updated-state :next-node "harness"}))

(defn transition-to-harness-connected [state]
  (let [s (merge {} state) ; Assuming state is a map representing the current state structure
        marriage-state (get s :marriage-state)
        new-state (assoc marriage-state :phase :HARNESS_CONNECTED :completion-pct 90)]
    {:marriage-state new-state :next-node "attestation"}))

(defn transition-to-attestation-emitted [state]
  (let [s (merge {} state) ; Assuming state is a map representing the current state structure
        ;; In a real scenario, we'd need definitions for MarriageState and MarriagePhase.
        ;; Here we simulate setting attributes on a mutable map representation of 's'.
        marriage-state-map (get s :marriage_state {})
        s-with-signatures (assoc marriage-state-map
                                 :robotSignatures
                                 [{:robotDid "did:web:etzhayyim.com:otete-heavy-unit-1" :role "marriage_lead" :timestamp "2026-05-26T13:00:00Z" :signature "..."}
                                  {:robotDid "did:web:etzhayyim.com:mimi-precision-unit-1" :role "alignment_witness" :timestamp "2026-05-26T13:00:05Z" :signature "..."}])
        s-with-phase (assoc s-with-signatures :phase :ATTESTATION_EMITTED) ; Assuming ATTESTATION_EMITTED is a constant/symbol
        s-final (assoc s-with-phase :completionPct 100)]

    (let [record {:type "com.etzhayyim.sarutahiko.marriageAttestation"
                :chassisId (:chassisId s)
                :inputs (:inputs s)
                :criticalTorques (:criticalTorques s)
                :attestingRobots (:robotSignatures s-final)
                :recordedAt "2026-05-26T13:00:10Z"}]
      {:marriage_state s-final
       :marriage_attestation record
       :next_node "end"})))

