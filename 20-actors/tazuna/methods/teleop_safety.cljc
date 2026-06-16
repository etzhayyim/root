(ns tazuna.methods.teleop-safety
  "tazuna (手綱) teleop-safety reasoner — stdlib only (ADR-2606042100).

  1:1 Clojure port of `20-actors/tazuna/methods/teleop_safety.py`.

  The safety-critical core of the teleoperation control plane, kept pure and
  deterministic so it can be unit-tested offline. It answers four questions for
  every relayed command, in priority order:

    1. force-class admission (N1) — is the robot's force class representable +
       force-authorized (G3)?
    2. no-server-key (G4)        — is the command member-signed, with NO server
       signature?
    3. soft-RT supervision (G10) — has the deadman lapsed or the latency budget
       been breached?
    4. safe verdict             — what safe_state should the command carry
       (nominal / deadman-lapse / latency-breach / estopped /
       autonomy-fallback)?

  This is best-effort SOFT-real-time supervision, NOT a certified
  (IEC 61508 / ISO 13849) safety system; hard-RT and safety-rated live actuation
  are R5/Lv7+ (G10, kotoba-os N2 precedent). It never emits a live actuation
  (G7): the verdict is advisory + replayable, and the cell drops to a safe-stop
  on any breach.

  Pure Clojure (clojure.core only), no external deps. Portable .cljc."
  (:require [clojure.string :as str]))

;; ═════════════════════════════════════════════════════════════════════════════
;; Constants
;; ═════════════════════════════════════════════════════════════════════════════

(def ADMITTED-FORCE-CLASSES ["observational" "soft-actuation" "powered-actuation"])

(def ALWAYS-PERMITTED ["halt" "estop" "handback"])

(def ACTUATION-KINDS ["move" "manipulate"])

;; ═════════════════════════════════════════════════════════════════════════════
;; Records
;; ═════════════════════════════════════════════════════════════════════════════

;; In Python these are frozen dataclasses; in Clojure we use plain maps with the
;; same public shape. The port preserves field names as kebab keywords.

(defn make-command
  ([]           (make-command ""))
  ([kind]       (make-command kind "" "" 0 0))
  ([kind & {:keys [member-sig server-sig
                    elapsed-since-presence-ms observed-latency-ms]
             :or   {member-sig ""
                    server-sig ""
                    elapsed-since-presence-ms 0
                    observed-latency-ms 0}}]
   {:kind kind
    :member-sig member-sig
    :server-sig server-sig
    :elapsed-since-presence-ms elapsed-since-presence-ms
    :observed-latency-ms observed-latency-ms}))

(defn make-grant
  ([] (make-grant ""))
  ([force-class] (make-grant force-class "" 300 150))
  ([force-class force-auth-ref]
   (make-grant force-class force-auth-ref 300 150))
  ([force-class force-auth-ref deadman-ms latency-budget-ms]
   {:force-class force-class
    :force-auth-ref force-auth-ref
    :deadman-ms deadman-ms
    :latency-budget-ms latency-budget-ms}))

(defn make-verdict
  [safe-state actuates effective-kind reason]
  {:safe-state safe-state
   :actuates actuates
   :effective-kind effective-kind
   :reason reason})

;; ═════════════════════════════════════════════════════════════════════════════
;; Public API
;; ═════════════════════════════════════════════════════════════════════════════

(defn admit-session
  "N1 + G3: raise unless the force class is representable AND force-authorized.
  No return value."
  [grant]
  (let [fc (:force-class grant)]
    (when-not (some #(= % fc) ADMITTED-FORCE-CLASSES)
      (throw (ex-info
              (str "N1: force class " (pr-str fc) " is unrepresentable; "
                   "weaponizable / force-as-harm can never be admitted "
                   "(Mission Charter §1.12)")
              {:error :force-class
               :force-class fc
               :admitted ADMITTED-FORCE-CLASSES})))
    (when (str/blank? (:force-auth-ref grant))
      (throw (ex-info
              (str "G3: Transparent Force requires a force-authorization reference "
                   "(1 SBT=1 vote admission) before a teleop session is admitted")
              {:error :transparent-force
               :grant grant})))))

(defn evaluate
  "Return the safety verdict for one relayed command. Raises on N1/G3/G4
  violations.

  Priority: e-stop > deadman lapse > latency breach > nominal. A safety command
  (halt/estop/handback) is always permitted and never requires a signature. An
  actuation command (move/manipulate) requires a member signature, refuses any
  server signature, and is rewritten to a safe-stop (effective_kind='halt',
  autonomy-fallback) on any supervision breach."
  [command grant]
  (admit-session grant)

  ;; G4: a server signature is always refused, for any command.
  (when (seq (:server-sig command))
    (throw (ex-info
            (str "G4: server signature refused — the platform never signs a "
                 "physical-robot command (no-server-key, ADR-2605231525)")
            {:error :no-server-key
             :server-sig (:server-sig command)})))

  ;; E-stop and other safety commands are always honoured.
  (cond
    (= (:kind command) "estop")
    (make-verdict "estopped" false "estop" "emergency stop")

    (some #(= % (:kind command)) ["halt" "handback"])
    (make-verdict "nominal" false (:kind command) "safety command")

    :else
    (do
      (when-not (some #(= % (:kind command)) ACTUATION-KINDS)
        (throw (ex-info (str "unknown command kind " (pr-str (:kind command)))
                        {:error :unknown-command
                         :kind (:kind command)})))

      ;; G4: actuation requires a member signature.
      (when (str/blank? (:member-sig command))
        (throw (ex-info
                "G4: a member signature is required to relay an actuation command"
                {:error :no-server-key
                 :command command})))

      ;; G10: soft-RT supervision — deadman first, then latency.
      (cond
        (> (:elapsed-since-presence-ms command) (:deadman-ms grant))
        (make-verdict
         "autonomy-fallback" false "halt"
         (str "deadman lapse (" (:elapsed-since-presence-ms command)
              "ms > " (:deadman-ms grant) "ms)"))

        (> (:observed-latency-ms command) (:latency-budget-ms grant))
        (make-verdict
         "autonomy-fallback" false "halt"
         (str "latency breach (" (:observed-latency-ms command)
              "ms > " (:latency-budget-ms grant) "ms)"))

        :else
        ;; Nominal: the actuation passes — but still dry-run / outward-gated at
        ;; R0 (G7).
        (make-verdict "nominal" true (:kind command)
                      "member-signed, in-budget")))))
