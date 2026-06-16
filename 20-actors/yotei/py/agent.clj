#!/usr/bin/env bb
;; Working Clojure port of py/agent.py (yotei scheduling commons actor).
(ns yotei.py.agent
  "yotei — kotoba-native scheduling commons langgraph actor (kotoba WASM cell).

  ADR-2606072200. Replaces the legacy RisingWave/Cypher calendar graph with
  append-only bookings on the kotoba Datom log. Handlers over one kotoba EAVT graph:

    generate-slots     availability window → free slot grid (minus confirmed bookings, G4)
    propose-booking    consent (G8) + no-double-book (G4) → proposed booking
    confirm-booking    re-check free at confirm time (race-safe) → member-signed confirm (G5)
    cancel-booking     append-only cancellation; frees slot (G3)
    reschedule-booking member-signed (G5); new slot re-checked (G4); self-exclusion

  Hard invariants structurally unrepresentable:
    - no-double-book (G4): slot overlapping any confirmed booking on the calendar is REFUSED;
      confirmation re-checks (a racing confirm cannot create an overlap).
    - no-server-key (G5): only a member signature confirms; a server signature is refused.
    - no-harvest (G2): booker contact lives only as an encrypted envelope ref.
    - append-only (G3): status transitions append; a confirmed booking is never overwritten.

  Run:  bb --classpath 20-actors 20-actors/yotei/py/agent.clj")

;; ── interval overlap (core of no-double-book, G4) ──────────────────────────────
(defn overlaps
  "Half-open interval overlap [start, start+dur). Touching ends do NOT overlap."
  [a-start a-dur b-start b-dur]
  (and (< a-start (+ b-start b-dur))
       (< b-start (+ a-start a-dur))))

(defn is-free
  "True iff the proposed slot overlaps no CONFIRMED booking on this calendar (G4)."
  [calendar-did start-epoch-min duration-min confirmed-bookings]
  (not (some (fn [b]
               (and (= (get b :status) "confirmed")
                    (= (get b :calendarDid) calendar-did)
                    (overlaps start-epoch-min duration-min
                              (long (get b :startEpochMin 0))
                              (long (get b :durationMin 0)))))
             confirmed-bookings)))

;; ── slot generation ─────────────────────────────────────────────────────────────
(defn generate-slots
  "Enumerate free slots within an availability window for a given day (the day's midnight as
  epoch minutes). Honest availability only (G6): booked slots are simply absent. Returns a
  list of {:startEpochMin t :durationMin step}."
  [availability day-start-epoch-min confirmed-bookings]
  (let [start (+ day-start-epoch-min (long (get availability :startMin)))
        end   (+ day-start-epoch-min (long (get availability :endMin)))
        step  (long (get availability :slotMin 30))
        cal   (get availability :calendarDid)]
    (loop [t start slots []]
      (if (> (+ t step) end)
        slots
        (recur (+ t step)
               (if (is-free cal t step confirmed-bookings)
                 (conj slots {:startEpochMin t :durationMin step})
                 slots))))))

;; ── propose / confirm ──────────────────────────────────────────────────────────
(defn propose-booking
  "Propose a booking. Requires consent (G8); refuses if the slot overlaps a confirmed
  booking (G4). Booker contact is carried only as an encrypted envelope ref (G2). Returns a
  :proposed booking (unsigned) or a refusal."
  [req confirmed-bookings]
  (cond
    (not (seq (get req :consentRef)))
    {:state "refused" :reason "missing DID-signed consent (G8)"}

    (not (is-free (get req :calendarDid)
                  (long (get req :startEpochMin))
                  (long (get req :durationMin))
                  confirmed-bookings))
    {:state "refused" :reason "slot overlaps a confirmed booking (G4 no-double-book)"}

    :else
    {:state        "proposed"
     :bookingId    (get req :bookingId)
     :calendarDid  (get req :calendarDid)
     :requesterDid (get req :requesterDid)
     :responderDid (get req :responderDid "")
     :startEpochMin (long (get req :startEpochMin))
     :durationMin  (long (get req :durationMin))
     :consentRef   (get req :consentRef)
     :contactRef   (get req :contactRef "")   ; encrypted envelope only (G2)
     :status       "proposed"
     :confirmedSig nil
     :appendOnly   true}))

(defn confirm-booking
  "Confirm a proposed booking. Re-checks no-double-book at confirm time so a racing confirm
  cannot create an overlap (G4). ONLY a member-origin signature confirms (G5 no-server-key);
  a server signature is refused. Append-only (G3)."
  [booking signature confirmed-bookings]
  (cond
    (not= (get booking :state) "proposed")
    (merge booking {:refused true :reason "booking is not in :proposed state"})

    (not= (get signature :origin) "member")
    (merge booking {:refused true
                    :reason  "only a member passkey/wallet signature confirms (G5 no-server-key)"})

    ;; race-safe re-check (G4)
    (not (is-free (get booking :calendarDid)
                  (long (get booking :startEpochMin))
                  (long (get booking :durationMin))
                  confirmed-bookings))
    (merge booking {:refused true
                    :reason  "slot was taken before confirm — overlap refused (G4)"})

    :else
    (merge booking {:state        "confirmed"
                    :status       "confirmed"
                    :confirmedSig (get signature :ref)})))

;; ── cancel / reschedule ────────────────────────────────────────────────────────
(defn cancel-booking
  "Cancel a booking. A cancelled booking no longer blocks availability (is-free counts only
  :confirmed), so the slot is immediately re-bookable. Append-only state transition (G3)."
  [booking]
  (merge booking {:state "cancelled" :status "cancelled"}))

(defn reschedule-booking
  "Move a confirmed booking to a new slot. Member-signed (G5). The new slot is re-checked for
  no-double-book (G4), EXCLUDING this booking's own current slot from the conflict set (moving a
  booking must not collide with itself). Refuses a non-confirmed booking or an occupied slot."
  [booking new-start-epoch-min new-duration-min confirmed-bookings signature]
  (cond
    (not= (get booking :status) "confirmed")
    (merge booking {:refused true :reason "only a confirmed booking can be rescheduled"})

    (not= (get signature :origin) "member")
    (merge booking {:refused true
                    :reason  "only a member passkey/wallet signature reschedules (G5 no-server-key)"})

    :else
    (let [others (filter #(not= (get % :bookingId) (get booking :bookingId))
                         confirmed-bookings)]
      (if (not (is-free (get booking :calendarDid)
                        (long new-start-epoch-min)
                        (long new-duration-min)
                        others))
        (merge booking {:refused true
                        :reason  "target slot overlaps another confirmed booking (G4 no-double-book)"})
        (merge booking {:startEpochMin (long new-start-epoch-min)
                        :durationMin   (long new-duration-min)
                        :status        "confirmed"
                        :rescheduled   true
                        :confirmedSig  (get signature :ref)})))))

;; ── main (smoke demo) ─────────────────────────────────────────────────────────
(defn main [& _]
  (let [cal     "did:web:yotei.etzhayyim.com:calendar:alice"
        avail   {:calendarDid cal :startMin 0 :endMin 90 :slotMin 30}
        slots   (generate-slots avail 0 [])
        req     {:bookingId "bk1" :calendarDid cal :requesterDid "did:plc:bob"
                 :responderDid "did:plc:alice" :startEpochMin 600 :durationMin 30
                 :consentRef "consent-1"}
        prop    (propose-booking req [])
        conf    (confirm-booking prop {:origin "member" :ref "sig-1"} [])]
    (println "slots:" (mapv :startEpochMin slots))
    (println "proposed:" (:state prop))
    (println "confirmed:" (:status conf) "sig:" (:confirmedSig conf))))

(when (= *file* (System/getProperty "babashka.file"))
  (main))
