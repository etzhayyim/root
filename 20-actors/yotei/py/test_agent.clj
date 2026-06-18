#!/usr/bin/env bb
;; Clojure port of py/test_agent.py (yotei scheduling commons actor test harness).
(ns yotei.py.test-agent
  "yotei — test harness (clojure.test / babashka; no kotoba host needed).

  Verifies the structural invariants of ADR-2606072200:
    G4 no-double-book — overlapping slot refused at propose AND re-checked at confirm
    G5 no-server-key  — only a member signature confirms
    G8 consent-bound  — propose without consent refused
    G2 no-harvest     — booker contact only as an encrypted ref; no profile field
    slot generation   — booked slots absent, honest availability"
  (:require [clojure.test :refer [deftest is testing run-tests]]
            [yotei.py.agent :as agent]))

(def CAL "did:web:yotei.etzhayyim.com:calendar:alice")

(defn- confirmed [start dur]
  {:status "confirmed" :calendarDid CAL :startEpochMin start :durationMin dur})

(defn- req [start & {:keys [dur consentRef contactRef]
                     :or {dur 30 consentRef "consent-1"}}]
  (cond-> {:bookingId    "bk1"
           :calendarDid  CAL
           :requesterDid "did:plc:bob"
           :responderDid "did:plc:alice"
           :startEpochMin start
           :durationMin   dur
           :consentRef    consentRef}
    contactRef (assoc :contactRef contactRef)))

;; ── Overlap tests ──────────────────────────────────────────────────────────────
(deftest test-overlap-true
  (is (true? (agent/overlaps 100 30 110 30))))

(deftest test-touching-not-overlap
  ;; [100,130) and [130,160) — adjacent, NOT overlapping
  (is (false? (agent/overlaps 100 30 130 30))))

(deftest test-is-free-respects-only-confirmed
  (let [proposed {:status "proposed" :calendarDid CAL :startEpochMin 100 :durationMin 30}]
    ;; a proposed booking does not block availability
    (is (true?  (agent/is-free CAL 100 30 [proposed])))
    (is (false? (agent/is-free CAL 100 30 [(confirmed 100 30)])))))

;; ── Propose tests ──────────────────────────────────────────────────────────────
(deftest test-consent-required
  (let [out (agent/propose-booking (req 600 :consentRef "") [])]
    (is (= "refused" (:state out)))
    (is (clojure.string/includes? (:reason out) "G8"))))

(deftest test-free-slot-proposed
  (let [out (agent/propose-booking (req 600) [])]
    (is (= "proposed" (:state out)))
    (is (nil? (:confirmedSig out)))))

(deftest test-double-book-refused
  (let [out (agent/propose-booking (req 600) [(confirmed 600 30)])]
    (is (= "refused" (:state out)))
    (is (clojure.string/includes? (:reason out) "G4"))))

(deftest test-contact-is-ref-only
  (let [out (agent/propose-booking (req 600 :contactRef "com.etzhayyim.encrypted:abcd") [])]
    ;; no plaintext profile/email/phone field exists
    (doseq [k (keys out)]
      (is (not (clojure.string/includes? (clojure.string/lower-case (name k)) "email")))
      (is (not (clojure.string/includes? (clojure.string/lower-case (name k)) "phone")))
      (is (not (clojure.string/includes? (clojure.string/lower-case (name k)) "profile"))))
    (is (clojure.string/starts-with? (:contactRef out) "com.etzhayyim.encrypted:"))))

;; ── Confirm tests ──────────────────────────────────────────────────────────────
(deftest test-member-signature-confirms
  (let [proposed (agent/propose-booking (req 600) [])
        out      (agent/confirm-booking proposed {:origin "member" :ref "sig-1"} [])]
    (is (= "confirmed" (:status out)))
    (is (= "sig-1" (:confirmedSig out)))))

(deftest test-server-signature-refused
  (let [proposed (agent/propose-booking (req 600) [])
        out      (agent/confirm-booking proposed {:origin "server" :ref "x"} [])]
    (is (true? (:refused out)))
    (is (clojure.string/includes? (:reason out) "G5"))))

(deftest test-race-lost-refused
  ;; someone else's confirmed booking appears between propose and confirm
  (let [proposed (agent/propose-booking (req 600) [])
        out      (agent/confirm-booking proposed {:origin "member" :ref "s"}
                                        [(confirmed 600 30)])]
    (is (true? (:refused out)))
    (is (clojure.string/includes? (:reason out) "G4"))))

;; ── Slot generation tests ──────────────────────────────────────────────────────
(deftest test-booked-slot-absent
  ;; day midnight epoch = 0; window 0..90 → slots at 0,30,60. Book 30-60.
  (let [avail {:availabilityId "a1" :calendarDid CAL :dayOfWeek 0
               :startMin 0 :endMin 90 :slotMin 30}
        slots (agent/generate-slots avail 0 [(confirmed 30 30)])
        starts (mapv :startEpochMin slots)]
    ;; 30 absent (G4), no scarcity counter (G6)
    (is (= [0 60] starts))))

;; ── Cancel / Reschedule tests ──────────────────────────────────────────────────
(defn- make-confirmed []
  (let [proposed  (agent/propose-booking (req 600) [])
        confirmed (agent/confirm-booking proposed {:origin "member" :ref "s1"} [])]
    confirmed))

(deftest test-cancel-frees-slot
  (let [confirmed (make-confirmed)
        cancelled (agent/cancel-booking confirmed)]
    (is (= "cancelled" (:status cancelled)))
    ;; a cancelled booking does not block availability
    (is (true? (agent/is-free CAL 600 30 [cancelled])))))

(deftest test-reschedule-to-free-slot
  (let [confirmed (make-confirmed)
        out       (agent/reschedule-booking confirmed 720 30 [confirmed]
                                            {:origin "member" :ref "s2"})]
    (is (true? (:rescheduled out)))
    (is (= 720 (:startEpochMin out)))))

(deftest test-reschedule-excludes-own-slot
  ;; rescheduling to (almost) the same window must not collide with itself
  (let [confirmed (make-confirmed)
        out       (agent/reschedule-booking confirmed 605 30 [confirmed]
                                            {:origin "member" :ref "s2"})]
    (is (true? (:rescheduled out)))))

(deftest test-reschedule-into-conflict-refused
  (let [confirmed (make-confirmed)
        other     {:bookingId "bk2" :status "confirmed" :calendarDid CAL
                   :startEpochMin 720 :durationMin 30}
        out       (agent/reschedule-booking confirmed 720 30 [confirmed other]
                                            {:origin "member" :ref "s2"})]
    (is (true? (:refused out)))
    (is (clojure.string/includes? (:reason out) "G4"))))

(deftest test-reschedule-server-sig-refused
  (let [confirmed (make-confirmed)
        out       (agent/reschedule-booking confirmed 720 30 [confirmed]
                                            {:origin "server" :ref "x"})]
    (is (true? (:refused out)))
    (is (clojure.string/includes? (:reason out) "G5"))))

(deftest test-reschedule-nonconfirmed-refused
  (let [proposed (agent/propose-booking (req 900) [])
        out      (agent/reschedule-booking proposed 960 30 []
                                           {:origin "member" :ref "s"})]
    (is (true? (:refused out)))))

;; ── runner ─────────────────────────────────────────────────────────────────────
(when (= *file* (System/getProperty "babashka.file"))
  (let [{:keys [fail error]} (clojure.test/run-tests 'yotei.py.test-agent)]
    (System/exit (if (zero? (+ fail error)) 0 1))))
