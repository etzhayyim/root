#!/usr/bin/env bb
;; Clojure port of py/test_agent.py — shukubo 宿坊 test harness.
(ns shukubo.py.test-agent
  "Verifies the structural invariants of ADR-2606071600:
    G2 no-commission      — no commission field on a stay; Ring1 gross = tithe + hostNet exactly;
                            Ring2 book is a handoff (shukubo never merchant-of-record)
    G4 commons-first      — discover resolves/orders commons → internal → external
    G7 tithe              — TitheRouter 10% split (Ring1)
    G8 no-server-key      — only a member-origin signature authorizes
    G12 hospitality-dignity — no guest/host score field; only space habitability
    G13 no-surge          — list_stay has no demand/dynamic-price field
    G14 privacy           — noSurveil ≡ true

  Run:  bb --classpath 20-actors 20-actors/shukubo/py/test_agent.clj"
  (:require [clojure.test :refer [deftest is testing run-tests]]
            [clojure.string :as str]
            [shukubo.py.agent :as agent]))

;; ── shared fixtures ───────────────────────────────────────────────────────────
(def ^:private sbt {"did:plc:pilgrim" true "did:plc:lapsed" false})

(defn- stay
  "Build a stay via list-stay with defaults matching test_agent.py's _stay()."
  [ring & {:keys [host-did kind title capacity cost-mode cost-minor habitability operator-url]
           :or {host-did "did:plc:host" kind "member-room" title "Quiet room"
                capacity 2 cost-mode "fixed" cost-minor 5000000
                habitability "water+heat+egress" operator-url ""}}]
  (agent/list-stay host-did ring kind
                   :title title :capacity capacity :cost-mode cost-mode
                   :cost-minor cost-minor :habitability habitability
                   :operator-url operator-url))

;; ── ListStay ─────────────────────────────────────────────────────────────────
(deftest test-no-commission-field
  (let [s (stay "internal")]
    (doseq [k (map name (keys s))]
      (is (not (str/includes? (str/lower-case k) "commission"))
          (str "unexpected commission key: " k)))))

(deftest test-no-surge-field
  (let [s (stay "internal")]
    (doseq [k (map name (keys s))]
      (is (not (str/includes? (str/lower-case k) "surge"))
          (str "unexpected surge key: " k))
      (is (not (str/includes? (str/lower-case k) "dynamic"))
          (str "unexpected dynamic key: " k)))))

(deftest test-no-person-score-field
  ;; G12: persons are never scored; only the space's habitability is attested
  (let [s (stay "internal")]
    (doseq [k (map name (keys s))]
      (is (not (str/includes? (str/lower-case k) "score"))
          (str "unexpected score key: " k))
      (is (not (str/includes? (str/lower-case k) "rating"))
          (str "unexpected rating key: " k)))
    (is (contains? s :habitability))))

(deftest test-no-surveil-invariant
  ;; G14
  (is (true? (:noSurveil (stay "internal")))))

;; ── Discover ─────────────────────────────────────────────────────────────────
(deftest test-commons-first
  (let [stays [(stay "external" :cost-minor 3000000)
               (stay "commons"  :cost-minor 0)
               (stay "internal" :cost-minor 5000000)]
        out   (agent/discover-stays "need a bed" stays)]
    (is (= (:resolved_ring out) "commons"))
    (is (= (get-in out [:candidates 0 :ring]) "commons"))   ; G4 ordering
    (is (= (map :ring (:candidates out))
           ["commons" "internal" "external"]))))

;; ── Settlement ───────────────────────────────────────────────────────────────
(deftest test-zero-commission-exact-split
  (let [s (agent/build-settlement-intent 5000000 "did:plc:host")]
    (is (= (:commissionMinor s) 0))          ; G2
    (is (= (:titheMinor s) 500000))          ; G7
    (is (= (:hostNetMinor s) 4500000))
    (is (= (:grossMinor s) (+ (:titheMinor s) (:hostNetMinor s))))))

(deftest test-no-server-key
  (is (false? (:serverHeldKey (agent/build-settlement-intent 1 "h")))))

(deftest test-only-member-signature
  (let [s   (agent/build-settlement-intent 1000000 "did:plc:host")
        srv (agent/authorize-settlement s {:origin "server" :ref "x"})
        mem (agent/authorize-settlement s {:origin "member" :ref "sig"})]
    (is (:refused srv))
    (is (str/includes? (:reason srv) "G8"))
    (is (:signed mem))))

;; ── Booking ──────────────────────────────────────────────────────────────────
(deftest test-consent-required
  (let [b (agent/book (stay "internal") "did:plc:pilgrim" "d1" "d2" "" sbt)]
    (is (= (:state b) "refused"))
    (is (str/includes? (:reason b) "G1"))))

(deftest test-commons-free-no-settlement
  (let [b (agent/book (stay "commons" :cost-mode "free" :cost-minor 0)
                      "did:plc:anyone" "d1" "d2" "consent" sbt)]
    (is (= (:state b) "confirmed"))
    (is (= (:settlement b) "commons-none"))
    (is (= (:titheMinor b) 0))))

(deftest test-internal-requires-sbt-and-settles
  (let [ok (agent/book (stay "internal") "did:plc:pilgrim" "d1" "d2" "consent" sbt)
        no (agent/book (stay "internal") "did:plc:lapsed"  "d1" "d2" "consent" sbt)]
    (is (= (:state ok) "settle-intent"))
    (is (= (get-in ok [:settlement :commissionMinor]) 0))   ; G2
    (is (= (:titheMinor ok) 500000))                        ; G7
    (is (= (:state no) "refused"))))

(deftest test-external-is-handoff-no-inflow
  (let [b (agent/book (stay "external" :operator-url "https://inn.example/book")
                      "did:plc:pilgrim" "d1" "d2" "consent" sbt)]
    (is (= (:state b) "self-book-handoff"))
    (is (= (:principal b) "member"))             ; shukubo is NOT the buyer (G2)
    (is (= (:settlement b) "external-none"))
    (is (= (:titheMinor b) 0))
    (is (= (:handoffUrl b) "https://inn.example/book"))))

;; ── NoDoubleBook ─────────────────────────────────────────────────────────────
(deftest test-dates-overlap
  (is (agent/dates-overlap "2026-06-01" "2026-06-05" "2026-06-03" "2026-06-08")))

(deftest test-adjacent-not-overlap
  ;; checkout == next checkin → no overlap (half-open)
  (is (not (agent/dates-overlap "2026-06-01" "2026-06-05" "2026-06-05" "2026-06-08"))))

(deftest test-stay-available-when-no-conflict
  (let [confirmed [{:stayId "s1" :state "confirmed" :checkIn "2026-06-10" :checkOut "2026-06-12"}]]
    (is (agent/stay-available "s1" "2026-06-01" "2026-06-05" confirmed))))

(deftest test-internal-booking-refused-on-overlap
  (let [s         (stay "internal")
        confirmed [{:stayId (:stayId s) :state "confirmed"
                    :checkIn "2026-06-01" :checkOut "2026-06-05"}]
        out       (agent/book s "did:plc:pilgrim" "2026-06-03" "2026-06-07"
                               "consent" sbt confirmed)]
    (is (= (:state out) "refused"))
    (is (str/includes? (:reason out) "no-double-book"))))

(deftest test-internal-booking-ok-when-free
  (let [s         (stay "internal")
        confirmed [{:stayId (:stayId s) :state "confirmed"
                    :checkIn "2026-06-10" :checkOut "2026-06-12"}]
        out       (agent/book s "did:plc:pilgrim" "2026-06-01" "2026-06-05"
                               "consent" sbt confirmed)]
    (is (= (:state out) "settle-intent"))))

(deftest test-external-not-blocked-by-availability
  ;; external-mirror stays aren't shukubo inventory; availability is the operator's
  (let [s         (stay "external")
        confirmed [{:stayId (:stayId s) :state "confirmed"
                    :checkIn "2026-06-01" :checkOut "2026-06-30"}]
        out       (agent/book (stay "external" :operator-url "https://inn/x")
                               "did:plc:pilgrim" "2026-06-02" "2026-06-04"
                               "consent" sbt confirmed)]
    (is (= (:state out) "self-book-handoff"))))

;; ── HostRegistration ─────────────────────────────────────────────────────────
(deftest test-registers-with-habitability
  (let [out (agent/register-host "did:plc:host"
                                  (stay "internal" :habitability "water+heat+egress"))]
    (is (= (:state out) "registered"))
    (doseq [k (map name (keys out))]
      (is (not (str/includes? (str/lower-case k) "score"))
          (str "unexpected score key: " k))
      (is (not (str/includes? (str/lower-case k) "rating"))
          (str "unexpected rating key: " k)))))

(deftest test-missing-habitability-refused
  (let [out (agent/register-host "did:plc:host"
                                  (stay "internal" :habitability "water"))]
    (is (= (:state out) "refused"))
    (is (str/includes? (:reason out) "G12"))))

;; ── runner ───────────────────────────────────────────────────────────────────
(when (= *file* (System/getProperty "babashka.file"))
  (let [{:keys [fail error]} (run-tests 'shukubo.py.test-agent)]
    (System/exit (if (zero? (+ fail error)) 0 1))))
