#!/usr/bin/env bb
;; Working Clojure port of py/agent.py (silicon fab-orchestration actor).
(ns silicon.py.agent
  "silicon 珪 — fab-orchestration kotoba agent (gate-enforcing, R0).

  ADR-2605242500 / 2605242545 · ADR-2606021139. Enforces:
    G1  §2(a)(c) force-review gate — litho/implant require a clearing force-review
    G2  chip inalienability — chips are LEASED, never sold/transferred/burned
    G8  append-only lot traceability — monotonic step indexing

  Pure compute; no platform key held (G7); operator/Council DIDs sign.
  LLM access is Murakumo-only (ADR-2605215000); this module needs none.

  Run:  bb --classpath 20-actors 20-actors/silicon/py/agent.clj"
  (:require [clojure.string :as str]))

;; ── constants ──────────────────────────────────────────────────────────────────
;; 8 fab process steps (lexicon knownValues, ADR-2605242545)
(def PROCESS_STEPS ["litho" "deposition" "etch" "implant" "cmp" "metrology" "test" "packaging"])

;; steps that carry HIGH §2(a)(c) weapons/surveillance-diversion risk → force-review REQUIRED (G1)
(def FORCE_REVIEW_REQUIRED #{"litho" "implant"})

;; verdicts that permit a gated step to proceed
(def CLEARING_VERDICTS #{"approve" "approve-with-conditions"})

;; ── G1 — §2(a)(c) force-review gate ───────────────────────────────────────────
(defn force-review-gate
  "Decide whether a process step may run. litho/implant require a force-review with
  a clearing verdict; an unresolved/denied review blocks (never auto-passes, G1)."
  [process review]
  (if (not (contains? FORCE_REVIEW_REQUIRED process))
    {:allowed true :reason "not a §2(a)(c)-gated step"}
    (if (nil? review)
      {:allowed false :reason (str process " requires a silenForceReview (G1)")}
      (let [verdict (get review :verdict (get review "verdict"))]
        (if (contains? CLEARING_VERDICTS verdict)
          {:allowed true :reason (str "force-review " verdict)}
          {:allowed false :reason (str "force-review verdict '" verdict "' does not clear (G1)")})))))

;; ── G8 — append-only lot traceability ─────────────────────────────────────────
(defn record-process-step
  "Append one process-step attestation to a lot's history. Enforces the force-review
  gate (G1) and monotonic step indexing (G8 — never rewrites prior steps)."
  ([lot process equipment-did completed-at]
   (record-process-step lot process equipment-did completed-at nil "ok"))
  ([lot process equipment-did completed-at review]
   (record-process-step lot process equipment-did completed-at review "ok"))
  ([lot process equipment-did completed-at review outcome]
   (if (not (some #{process} PROCESS_STEPS))
     {:error (str "unknown process '" process "'")}
     (let [gate (force-review-gate process review)]
       (if (not (:allowed gate))
         {:error (:reason gate) :blocked true}
         (let [history    (vec (get lot :history (get lot "history" [])))
               step-index (count history)
               step       (cond-> {:stepIndex    step-index
                                   :process      process
                                   :equipmentDid equipment-did
                                   :outcome      outcome
                                   :completedAt  completed-at}
                            (some? review)
                            (assoc :forceReviewUri (get review :id (get review "id" ""))))
               history'   (conj history step)
               state      (cond
                            (and (= process "packaging") (= outcome "ok")) "verified"
                            (or (= outcome "scrapped") (= outcome "quarantined")) outcome
                            :else (get lot :state (get lot "state" "in-fab")))]
           (assoc lot
                  :history history'
                  :currentStepIndex step-index
                  :state state)))))))

(defn lot-traceable
  "A lot is traceable iff its step indices form a gap-free monotonic 0..n chain (G8)."
  [lot]
  (let [history (get lot :history (get lot "history" []))
        idx     (mapv #(get % :stepIndex (get % "stepIndex")) history)]
    (= idx (vec (range (count idx))))))

;; ── G2 — chip inalienability (LEASE only, never sell/transfer) ────────────────
(defn lease-chip
  "Lease a manufactured die to an SBT-holder. A chip is never owned/sold/transferred
  (land-trust-analogue inalienability, G2). Ship requires a force-review (G1)."
  [chip lessee-did force-review-uri]
  (if (nil? force-review-uri)
    {:error "ship/lease requires a force-review (G1)" :blocked true}
    (assoc chip :leasedToDid lessee-did :forceReviewUri force-review-uri)))

(defn assert-no-transfer
  "Reject any sale/transfer/burn of silicon assets (G2). Only :lease is permitted."
  [action]
  (let [prohibited #{"sell" "transfer" "burn" "set-owner" "gift"}]
    (if (contains? prohibited action)
      {:allowed false
       :reason  (str "'" action "' violates silicon inalienability (G2); only lease-to-SBT is permitted")}
      {:allowed (= action "lease")
       :reason  (if (= action "lease")
                  "lease permitted"
                  (str "unknown action '" action "'"))})))

;; ── main (smoke demo) ─────────────────────────────────────────────────────────
(defn main [& _]
  (let [lot    {:id "LOT-DEMO" :history []}
        review {:id "fr.litho" :verdict "approve"}
        lot'   (record-process-step lot "litho" "equip/litho-01" "2026-06-02T00:00:00Z" review)]
    (println "after litho:" (:currentStepIndex lot') (:state lot'))
    (let [blocked (record-process-step lot' "implant" "equip/imp-01" "2026-06-02T01:00:00Z" nil)]
      (println "implant without review:" (:blocked blocked) (:error blocked)))
    (println "sell attempt:" (assert-no-transfer "sell"))))

(when (= *file* (System/getProperty "babashka.file"))
  (main))
