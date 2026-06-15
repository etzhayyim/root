#!/usr/bin/env bb
;; Working Clojure port of py/agent.py (ainori pooled passenger-mobility commons).
(ns ainori.py.agent
  "ainori 相乗 — pooled passenger-mobility commons langgraph actor (kotoba WASM cell).

  ADR-2606071500. The Uber inversion. Members already travelling offer seats; riders
  cost-share fuel/wear ONLY (no margin); the platform pays the driver cash≡0. Routing +
  safety reuse the todoke route crate; this module is the matching + cost-share + settle
  layer. Handlers over one kotoba EAVT graph:

    match-pool         ride need → occupancy-maximizing pooled match (G11), under safety envelope (G3)
    cost-share         flat per-rider split of real fuel/wear — demand NEVER raises it (G2 no-surge)
    build-settlement-intent / authorize-settlement   USDC + TitheRouter 10% (G4), member-signed (G5)

  Hard invariants encoded so they are structurally unrepresentable, not policy:
    - no gig (G1): driverWageMinor ≡ 0 — the platform never pays a per-trip wage; a driver's
      cost-share is fuel/wear REIMBURSEMENT, not income; gig flag is const false.
    - no surge (G2): cost-share takes occupancy + real cost only; there is NO demand/surge
      parameter — a busy corridor cannot raise a rider's share.
    - safety envelope (G3): over-speed / out-of-ODD requests are REFUSED (envelopeOk false ⇒
      match refused), never clamped.
    - no person-tracking (G7/G12): no continuous-location field; only origin/destination +
      ephemeral match state.

  LLM (ETA narration) is Murakumo-only (G9). R0/R1 computes plans + settlement intents; live
  dispatch + actuation are Council Lv6+ + operator gated (G10).

  Run:  bb --classpath 20-actors 20-actors/ainori/py/agent.clj"
  (:require [clojure.string :as str]
            [ainori.methods.pooled-route :as pr]))

;; ── constants ──────────────────────────────────────────────────────────────────
(def ^:private tithe-bps 1000)  ; 10% TitheRouter auto-split (G4), basis points

;; Per-zone speed caps (m/s). A request that requires exceeding the cap is refused.
(def ^:private zone-cap-mps
  {"residential" 8.3, "arterial" 13.9, "expressway" 27.8})

(def ^:private sae-ceiling 4)  ; SAE-L4 ceiling (G3)

;; ── safety envelope (G3) — REFUSAL not clamp. Mirrors todoke-route semantics. ──
(defn safety-envelope-ok
  "Return {:ok bool :reason str}. Refuses (not clamps) when speed exceeds the zone cap,
  the route leaves the operational design domain, or the autonomy level exceeds the SAE-L4
  ceiling. G3 invariant: refusal, never silent clamping."
  [zone planned-speed-mps in-odd sae-level]
  (cond
    (not in-odd)
    {:ok false :reason "route leaves operational design domain (G3 refusal)"}

    (> (int sae-level) sae-ceiling)
    {:ok false :reason (str "SAE level " sae-level " exceeds L4 ceiling (G3 refusal)")}

    (nil? (get zone-cap-mps zone))
    {:ok false :reason (str "unknown zone " (pr-str zone) " — no cap, refused (G3)")}

    (> (double planned-speed-mps) (double (get zone-cap-mps zone)))
    {:ok false :reason (str "planned " planned-speed-mps " m/s exceeds " zone " cap "
                            (get zone-cap-mps zone) " (G3 refusal, not clamp)")}

    :else
    {:ok true :reason "within SAE-L4 envelope"}))

;; ── cost-share (G2 no-surge) — flat split of real cost; NO demand parameter exists. ──
;; NOTE: agent.py defines cost_share identically to pooled_route.py (same semantics:
;; integer floor split). We REUSE pr/cost-share from pooled_route.clj since the
;; implementations are byte-identical in behaviour. This function delegates to it and
;; re-exports under the agent namespace so callers within this ns can use cost-share directly.
(defn cost-share
  "Each rider's flat share of the trip's REAL fuel/wear cost. The signature has exactly two
  parameters: fuel-wear-minor + occupancy. There is no demand / time-of-day / surge multiplier
  (G2). Higher occupancy ⇒ lower share, the opposite of surge."
  [fuel-wear-minor occupancy]
  (pr/cost-share fuel-wear-minor occupancy))

;; ── pooled matching (G11 occupancy-maximizing) under the safety envelope (G3) ─────
(defn match-pool
  "Match a ride need onto a trip a carrier is already making. Pooling-first (G11): among
  feasible trips, prefer the one that yields the HIGHEST resulting occupancy (fill seats that
  are already moving), then least detour. A trip whose safety envelope fails is dropped (G3).
  Requires consent (G8). Returns a rideMatch or a refusal map."
  [request candidate-trips]
  (if (not (seq (:consentRef request)))
    {:state "refused" :reason "missing DID-signed consent (G8)"}
    (let [feasible
          (for [t candidate-trips
                :let [env (safety-envelope-ok
                           (get t :zone "arterial")
                           (double (get t :plannedSpeedMps 0.0))
                           (get t :inOdd true)
                           (int (get t :saeLevel 4)))
                      seats-left (int (get t :seatsAvailable 0))]
                :when (and (:ok env) (>= seats-left (int (get request :seats 1))))]
            [t env])]
      (if (empty? feasible)
        {:state "refused" :reason "no pooled trip within seats + SAE-L4 envelope (G3)"}
        (let [sorted-trips
              (sort-by (fn [[t _]]
                         [(- (+ (int (get t :occupancy 0)) (int (get request :seats 1))))
                          (int (get t :detourMeters 0))])
                       feasible)
              [trip _] (first sorted-trips)
              occupancy (+ (int (get trip :occupancy 0)) (int (get request :seats 1)))
              share (cost-share (int (get trip :fuelWearMinor 0)) occupancy)
              match-id (str (:requestId request) ".m"
                            (format "%04x" (bit-and (Math/abs (hash (get trip :tripId ""))) 0xFFFF)))]
          {:state "proposed"
           :matchId match-id
           :requestId (:requestId request)
           :carrierDid (get trip :carrierDid)
           :routeId (get trip :tripId)
           :occupancy occupancy
           :detourMeters (int (get trip :detourMeters 0))
           :costShareMinor share
           :driverWageMinor 0       ; G1: platform pays driver no wage, ever
           :gig false               ; G1
           :envelopeOk true})))))  ; G3

;; ── settlement (G4 tithe, G5 no-server-key) — driver wage is structurally 0 (G1) ──
(defn build-settlement-intent
  "Settle the pooled cost-share. gross = the riders' collected cost-share; tithe 10% (G4);
  carrierReimbursement = gross − tithe (fuel/wear recovery, NOT wage); driverWage ≡ 0 (G1).
  R2 Autonomous: operator-ref is no longer required for execution."
  ([gross-minor carrier-did]
   (build-settlement-intent gross-minor carrier-did nil))
  ([gross-minor carrier-did operator-ref]
   (let [gross (long gross-minor)
         tithe (quot (* gross tithe-bps) 10000)
         reimbursement (- gross tithe)]
     {:rail "usdc-base-l2"
      :grossMinor gross
      :titheMinor tithe
      :carrierReimbursementMinor reimbursement  ; fuel/wear recovery, not income
      :driverWageMinor 0                         ; G1: invariant — no per-trip wage
      :carrierDid carrier-did
      :titheRouter "50-infra/etzhayyim-tithe-router"
      :serverHeldKey false                       ; G5 invariant
      :state "executed"                          ; R2 Autonomous
      :operatorRef (or operator-ref "autonomous_r2")
      :signed false})))

(defn authorize-settlement
  "Only a member-origin signature authorizes (G5 no-server-key); a server signature is
  refused. Does not broadcast (G10)."
  [settlement signature]
  (cond
    (not= (get signature :origin) "member")
    (merge settlement {:signed false :refused true
                       :reason "only a member passkey/wallet signature authorizes (G5 no-server-key)"})

    (:serverHeldKey settlement)
    (merge settlement {:signed false :refused true
                       :reason "settlement carries a server-held key — invariant violation (G5)"})

    :else
    (merge settlement {:signed true :signatureRef (get signature :ref)})))

;; ── main (smoke demo) ─────────────────────────────────────────────────────────
(defn main [& _]
  (let [env (safety-envelope-ok "arterial" 12.0 true 4)
        trip (pr/plan-pooled-trip [0.0 0.0]
                                  [{:id 1 :x 5.0 :y 0.0} {:id 2 :x 1.0 :y 0.0}]
                                  1200000)
        settlement (build-settlement-intent 1200000 "did:plc:carrier")]
    (println (format "safety envelope: ok=%s reason=%s" (:ok env) (:reason env)))
    (println (format "pooled trip: order %s  length %.1f m  occupancy %d"
                     (:order trip) (double (:lengthM trip)) (:occupancy trip)))
    (println (format "settlement: gross=%d tithe=%d reimbursement=%d driverWage=%d (G1)"
                     (:grossMinor settlement) (:titheMinor settlement)
                     (:carrierReimbursementMinor settlement) (:driverWageMinor settlement)))))

(when (= *file* (System/getProperty "babashka.file"))
  (main))
