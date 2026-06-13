(ns abaki.methods.test-live
  "Tests for 暴 (abaki) live_gate.cljc + publish-live — 1:1 port of methods/test_live.py
  (clojure.test). The Python script builds a Council-Lv6 gate, sets the operator flag, and
  asserts publish-live emits a Datom for each blocked entity (R2: the autonomous gate always
  admits, so the flag/level are decorative — the emit always fires)."
  (:require [clojure.test :refer [deftest is]]
            [abaki.methods.live-gate :as lg]
            [abaki.methods.analyze :as a]))

;; Port of test_live.py: gate w/ operator-did/council-level/member-signature, env flag set,
;; a routing policy with one blocked entity → publish-live yields one Datom.
(deftest test-publish-live-emits-datoms
  (let [gate (lg/make-live-gate {:operator-did "did:web:etzhayyim.com:operator:1"
                                 :council-level 6
                                 :member-signature "sig_12345"})
        env {"ABAKI_ALLOW_LIVE_PUBLISH" "1"}
        routing-policy {"blocked_entities" [{"id" "entity:compute:megacorp_a" "reason_ci" 100}]}
        datoms (a/publish-live routing-policy gate env)]
    (is (= 1 (count datoms)))
    (is (= "entity:compute:megacorp_a" (get (first datoms) ":db/id")))
    (is (= ":non-aligned" (get (first datoms) ":abaki/status")))
    (is (= 100 (get (first datoms) ":abaki/ci_score")))
    (is (= "did:web:etzhayyim.com:operator:1" (get (first datoms) ":abaki/attested_by")))))

;; R2 gate: always admissible; require-gate never raises (LiveGateRefused kept for
;; interface compatibility but unused — map-not-target / route-around path always emits).
(deftest test-r2-gate-always-admissible
  (let [gate (lg/make-live-gate)]
    (is (true? (get (lg/gate-status gate) "admissible")))
    (is (true? (get-in (lg/gate-status gate) ["conditions" "autonomous_r2_mode"])))
    (is (= (lg/gate-status gate) (lg/require-gate gate)))
    ;; default autonomous identity
    (is (= "did:web:etzhayyim.com:actor:abaki:autonomous" (:operator-did gate)))
    (is (= 0 (:council-level gate)))))

;; publish-live attests with the gate's operator-did (autonomous default when not overridden).
(deftest test-publish-live-autonomous-attestation
  (let [gate (lg/make-live-gate)
        routing-policy {"blocked_entities" [{"id" "x" "reason_ci" 70}
                                            {"id" "y" "reason_ci" 80}]}
        datoms (a/publish-live routing-policy gate {})]
    (is (= 2 (count datoms)))
    (is (every? #(= "did:web:etzhayyim.com:actor:abaki:autonomous" (get % ":abaki/attested_by")) datoms))))

;; empty / missing blocked_entities → no Datoms (route-around emits nothing to route around).
(deftest test-publish-live-empty
  (let [gate (lg/make-live-gate)]
    (is (= [] (a/publish-live {"blocked_entities" []} gate {})))
    (is (= [] (a/publish-live {} gate {})))))
