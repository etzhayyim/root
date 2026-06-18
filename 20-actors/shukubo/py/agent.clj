#!/usr/bin/env bb
;; Working Clojure port of py/agent.py (shukubo pilgrim-lodging commons actor).
(ns shukubo.py.agent
  "shukubo 宿坊 — pilgrim-lodging commons langgraph actor (kotoba WASM cell).

  ADR-2606071600. The Airbnb/Hotels inversion. Three concentric rings (commons → internal →
  external), mirroring okaimono's shape for lodging. Handlers over one kotoba EAVT graph:

    list-stay              register a lodging offer (no commission/surge/person-score fields)
    discover-stays         stay need → commons-first ranked stays (G4 Ring ordering)
    book                   consent → reservation; Ring0 free/cost-share | Ring1 member-signed
                             settle | Ring2 self-book handoff
    build-settlement-intent / authorize-settlement   Ring1 USDC + TitheRouter 10% (G7), member-signed (G8)
    dates-overlap          half-open date-interval overlap predicate
    stay-available         no-double-book guard
    register-host          space habitability attestation (G12 — never person-scored)

  Hard invariants structurally unrepresentable:
    - no commission (G2): no commission/take-rate field; Ring1 gross = tithe + hostNet exactly;
      Ring2 booking is a handoff to the operator's OWN page — shukubo is never merchant-of-record.
    - no surge (G13): a stay's cost is flat/cost-share; there is no demand/dynamic-price field.
    - hospitality-dignity (G12): no guest/host score field exists; only the SPACE's habitability
      + safety is attested. Pilgrim-welcome default.
    - privacy (G14/G9): noSurveil ≡ true (no in-stay cameras/biometrics as a feature); booking
      PII via com.etzhayyim.encrypted.*.

  Run:  bb --classpath 20-actors 20-actors/shukubo/py/agent.clj"
  (:require [clojure.string :as str]))

;; ── constants ──────────────────────────────────────────────────────────────────
(def ^:private tithe-bps 1000)   ; 10% TitheRouter auto-split (G7), basis points

;; Ring ordering is constitutional (G4): covenantal hospitality before internal before external.
(def ring-order ["commons" "internal" "external"])

;; Required habitability fields: the SPACE, never the person (G12).
(def ^:private required-habitability ["water" "heat" "egress"])

;; ── list-stay (G2/G12/G13/G14 — no commission/score/surge fields; privacy invariant) ──
(defn list-stay
  "Register a lodging offer. Note the field set: there is NO commission, NO surge/dynamic
  price, and NO guest/host score — only the SPACE's habitability is attested (G12). noSurveil
  is a constant invariant (G14). If ring is unknown, raises (matches Python ValueError)."
  [host-did ring kind
   & {:keys [title capacity cost-mode cost-minor habitability operator-url availability sourcing]
      :or {capacity 1 cost-mode "cost-share" cost-minor 0
           habitability "water+heat+egress" operator-url ""
           availability "available" sourcing "authoritative"}}]
  (when-not (some #{ring} ring-order)
    (throw (ex-info (str "unknown ring " (pr-str ring)) {:ring ring})))
  {:stayId      (str "shukubo." kind "."
                     (format "%04x" (bit-and (Math/abs (hash (str host-did title))) 0xFFFF)))
   :ring        ring
   :kind        kind
   :hostDid     host-did
   :title       (or title "")
   :capacity    (int capacity)
   :costMode    cost-mode     ; free | cost-share | fixed — never demand-priced (G13)
   :costMinor   (int cost-minor)
   :habitability habitability  ; the SPACE is attested, never the person (G12)
   :noSurveil   true           ; G14 invariant — no in-stay cameras/biometrics
   :operatorUrl operator-url   ; external ring only: operator's OWN booking page
   :availability availability
   :sourcing    sourcing})     ; G10 honesty

;; ── discover-stays (G4 commons-first) ─────────────────────────────────────────
(defn discover-stays
  "need → Ring 0 commons → Ring 1 internal → Ring 2 external. Returns the first ring with
  candidates as `resolved_ring` (commons-first, G4), but carries the full set so the member
  sees the covenantal/cost-share alternatives even when an outer ring is chosen."
  [_need-text stays]
  (let [by-ring (into {}
                      (map (fn [r]
                             [r (sort-by #(int (get % :costMinor 0))
                                         (filter #(= (get % :ring) r) stays))])
                           ring-order))
        resolved (or (first (filter #(seq (get by-ring %)) ring-order)) "unresolved")
        ordered  (for [r ring-order, s (get by-ring r)] s)]
    {:resolved_ring resolved
     :candidates    (vec ordered)}))

;; ── settlement (Ring 1 only) — G2 no-commission, G7 tithe, G8 no-server-key ──
(defn build-settlement-intent
  "Ring-1 stay settlement. gross = flat cost-share; tithe 10% (G7); hostNet = gross − tithe;
  NO platform commission (G2: gross = tithe + hostNet exactly).
  R2 Autonomous: operator-ref is no longer required for execution.
  Note: key is :hostNetMinor/:hostDid (stays use host, not seller)."
  ([gross-minor host-did]
   (build-settlement-intent gross-minor host-did nil))
  ([gross-minor host-did operator-ref]
   (let [gross    (long gross-minor)
         tithe    (quot (* gross tithe-bps) 10000)
         host-net (- gross tithe)]   ; tithe rounds down ⇒ hostNet absorbs remainder; sum exact
     {:rail           "usdc-base-l2"
      :grossMinor     gross
      :commissionMinor 0              ; G2: structural zero — shukubo takes nothing
      :titheMinor     tithe
      :hostNetMinor   host-net
      :hostDid        host-did
      :titheRouter    "50-infra/etzhayyim-tithe-router"
      :serverHeldKey  false           ; G8 invariant
      :state          "executed"      ; R2 Autonomous
      :operatorRef    (or operator-ref "autonomous_r2")
      :signed         false})))

(defn authorize-settlement
  "Authorize a settlement intent. ONLY a member-origin signature authorizes (G8 no-server-key);
  server signature refused."
  [settlement signature]
  (cond
    (not= (get signature :origin) "member")
    (merge settlement {:signed  false
                       :refused true
                       :reason  "only a member passkey/wallet signature authorizes (G8 no-server-key)"})

    (:serverHeldKey settlement)
    (merge settlement {:signed  false
                       :refused true
                       :reason  "settlement carries a server-held key — invariant violation (G8)"})

    :else
    (merge settlement {:signed       true
                       :signatureRef (get signature :ref)})))

;; ── book — Ring-routed reservation (G1 consent, G2 boundary) ─────────────────
(defn dates-overlap
  "Half-open date-interval overlap [checkIn, checkOut). Adjacent stays (one's checkout ==
  the next's checkin) do NOT overlap. ISO date strings compare lexically."
  [in1 out1 in2 out2]
  (and (neg? (compare in1 out2))    ; in1 < out2
       (neg? (compare in2 out1))))  ; in2 < out1

(defn stay-available
  "True iff no CONFIRMED booking for this stay overlaps the requested dates (no-double-book).
  The lodging analogue of yotei's slot guard (G2 hospitality / G13 honest availability)."
  [stay-id check-in check-out confirmed-bookings]
  (not (some (fn [b]
               (and (= (get b :stayId) stay-id)
                    (contains? #{"confirmed" "settle-intent"} (get b :state))
                    (dates-overlap check-in check-out
                                   (get b :checkIn "") (get b :checkOut ""))))
             confirmed-bookings)))

(defn book
  "Route a reservation by ring:
    Ring 0 (commons)  — covenantal/cost-share; no platform settlement.
    Ring 1 (internal) — SBT↔SBT; member-signed settlement intent (G7/G8); zero commission (G2).
    Ring 2 (external) — self-book HANDOFF to the operator's own page; shukubo is never the
                        merchant-of-record and takes no inflow (G2); no tithe.
  Requires consent (G1). For commons/internal stays (shukubo-held inventory), refuses a date
  range that overlaps a confirmed booking (no-double-book); external-mirror stays are not
  shukubo's inventory so availability is the operator's to assert."
  ([stay guest-did check-in check-out consent-ref sbt-registry]
   (book stay guest-did check-in check-out consent-ref sbt-registry nil))
  ([stay guest-did check-in check-out consent-ref sbt-registry confirmed-bookings]
   (if (not (seq consent-ref))
     {:state "refused" :reason "missing DID-signed consent (G1)"}
     (let [ring   (get stay :ring)
           common {:bookingId   (str (get stay :stayId "") ".bk."
                                     (format "%04x"
                                             (bit-and (Math/abs (hash (str guest-did check-in))) 0xFFFF)))
                   :stayId      (get stay :stayId)
                   :guestDid    guest-did
                   :ring        ring
                   :checkIn     check-in
                   :checkOut    check-out
                   :consentRef  consent-ref
                   :recordEnc   true}]      ; G9: booking PII encrypted
       (cond
         ;; double-book guard (commons + internal only — external is operator-managed)
         (and (contains? #{"commons" "internal"} ring)
              (seq confirmed-bookings)
              (not (stay-available (get stay :stayId) check-in check-out confirmed-bookings)))
         {:state "refused" :reason "stay already booked for those dates (no-double-book)"}

         (= ring "commons")
         (merge common {:state         "confirmed"
                        :costShareMinor (int (get stay :costMinor 0))
                        :settlement     "commons-none"
                        :titheMinor     0})

         (= ring "internal")
         (if-not (get sbt-registry guest-did false)
           (merge common {:state  "refused"
                          :reason "guest not an active Adherent SBT holder (§3)"})
           (let [settlement (build-settlement-intent (int (get stay :costMinor 0))
                                                     (get stay :hostDid))]
             (merge common {:state      "settle-intent"
                            :settlement settlement
                            :titheMinor (:titheMinor settlement)})))

         (= ring "external")
         ;; member transacts directly with the operator; shukubo never charges (G2)
         (merge common {:state      "self-book-handoff"
                        :principal  "member"
                        :handoffUrl (get stay :operatorUrl "")
                        :settlement "external-none"
                        :titheMinor 0})

         :else
         (merge common {:state "refused" :reason (str "unknown ring " (pr-str ring))}))))))

;; ── host registration (G12 hospitality-dignity, G14 privacy) ─────────────────
(defn register-host
  "Register a stay's host. Attests the SPACE's habitability (G12 — the space, never the
  person) and enforces the privacy invariant (G14 — noSurveil). A stay that advertises
  in-stay surveillance, or that lacks the minimum habitability attestation, is refused.
  There is no host/guest score field to set (G12 — persons are never rated)."
  [host-did stay]
  (if-not (true? (get stay :noSurveil))
    {:state "refused" :reason "in-stay surveillance not permitted as a feature (G14)"}
    (let [habit   (str/lower-case (or (get stay :habitability) ""))
          missing (filterv #(not (str/includes? habit %)) required-habitability)]
      (if (seq missing)
        {:state "refused" :reason (str "habitability attestation missing " missing " (G12)")}
        {:state       "registered"
         :hostDid     host-did
         :stayId      (get stay :stayId)
         :ring        (get stay :ring)
         :habitability (get stay :habitability)
         :noSurveil   true
         ;; NOTE: deliberately no host/guest score, rating, or rank field (G12)
         }))))

;; ── main (smoke demo) ─────────────────────────────────────────────────────────
(defn main [& _]
  (let [stay       (list-stay "did:plc:host" "commons" "pilgrim-room"
                              :title "Quiet commons room"
                              :capacity 2 :cost-mode "cost-share" :cost-minor 0)
        settlement (build-settlement-intent 5000000 "did:plc:host")]
    (println "stay ring:" (:ring stay) "noSurveil:" (:noSurveil stay))
    (println "settlement: gross=" (:grossMinor settlement)
             "tithe=" (:titheMinor settlement)
             "hostNet=" (:hostNetMinor settlement)
             "commission=" (:commissionMinor settlement)
             "state=" (:state settlement))))

(when (= *file* (System/getProperty "babashka.file"))
  (main))
