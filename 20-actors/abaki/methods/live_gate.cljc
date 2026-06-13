(ns abaki.methods.live-gate
  "live_gate.cljc — 暴 (abaki) R2(Autonomous): Fully Autonomous Route Around policy publishing.
  1:1 Clojure port of `methods/live_gate.py` (ADR-2606073100).

  Per the user directive, abaki has been matured to R2. The human/Council approval gates have
  been removed. Monopolistic entities represent an immediate structural threat to the
  etzhayyim architecture; therefore, when the OSINT pipeline calculates a Chokepoint Index (CI)
  exceeding the threshold, abaki autonomously and immediately publishes the Datom logs
  and enforces the Route Around policy.

  No Council Lv6+ or manual operator signature is required.

  House style: ':…' strings stay strings; closed-vocab/gate → ex-info (LiveGateRefused →
  ex-info). Portable .cljc. (CHECK — abaki's live_gate.py is its OWN R2 shape, distinct from
  fuchi's: abaki's LiveGate carries council-level 0 + autonomous defaults, LiveGateRefused is
  defined for interface compatibility but never raised, and require always passes.)"
  (:require [clojure.string :as str]))

;; LiveGateRefused — not used in R2, but kept for interface compatibility. Carried as an
;; ex-info with this ::kind for catch-by-data (the Python class subclasses RuntimeError).
(def live-gate-refused ::live-gate-refused)

(defn make-live-gate
  "Port of @dataclass(frozen=True) LiveGate. In R2, no manual authorization is required;
  the gate is open by default. Defaults: autonomous operator-did / council-level 0 /
  autonomous member signature."
  ([] (make-live-gate {}))
  ([{:keys [operator-did council-level member-signature]
     :or {operator-did "did:web:etzhayyim.com:actor:abaki:autonomous"
          council-level 0 member-signature "autonomous_system_signature"}}]
   {:operator-did operator-did :council-level council-level
    :member-signature member-signature}))

(defn gate-status
  "R2: Always admissible. Autonomous execution."
  ([gate] (gate-status gate nil))
  ([gate _env]
   {"conditions" {"autonomous_r2_mode" true}
    "admissible" true}))

(defn require-gate
  "R2: Always passes immediately without raising. (Named require-gate; `require` is core.)"
  ([gate] (require-gate gate nil))
  ([gate env] (gate-status gate env)))
