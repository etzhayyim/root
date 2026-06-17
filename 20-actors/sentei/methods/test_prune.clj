#!/usr/bin/env bb
;; Clojure mirror of methods/test_prune.py — sentei 剪定 structural-invariant tests.
(ns sentei.methods.test-prune
  "1:1 port of the prune.py invariant suite: G1 no-prior-restraint, G2 append-only +
  as-of time-travel, G3 growth-unstoppable, G4/G7 transparent-care (no verdict token),
  G5 no-server-key, Council floor + contested vote, G6 reversible, datom serialization.
  Also pins the sha256 prune-id digest to parity with python (prune.py `_digest`).

  Run:  bb --classpath 20-actors 20-actors/sentei/methods/test_prune.clj"
  (:require [sentei.methods.prune :as p]
            [clojure.test :refer [deftest is run-tests]]))

(def AT "2026-06-07T20:00:00.000Z")
(def COUNCIL "did:web:etzhayyim.com:council#5of7")
(def MANIFESTED {"id" "kanae.fundFlowEdge:jp-mext-2024-outlay" "manifested" true})
(def BUD {"id" "kanae.fundFlowEdge:jp-mext-2025-draft" "manifested" false})

(defn- raises? [f] (try (f) false (catch Exception _ true)))

;; ── G1 no-prior-restraint ──
(deftest g1-cannot-prune-unmanifested
  (is (raises? #(p/prune BUD "quarantine" "anything" COUNCIL {:at AT :council-level 7}))))

(deftest g1-can-prune-after-manifest
  (let [d (p/prune MANIFESTED "quarantine" "G10 review" COUNCIL {:at AT :council-level 6})]
    (is (= "quarantine" (get d "action")))
    (is (= {(get MANIFESTED "id") "quarantine"} (p/apply-log [d])))))

;; ── digest parity with python ──
(deftest digest-parity
  (let [d (p/prune MANIFESTED "quarantine" "G10 review" COUNCIL {:at AT :council-level 6})]
    (is (= "prune:kanae.fundFlowEdge:jp-mext-2024-outlay:quarantine:a4067d4a7c437fcd7b50201e"
           (get d "id")))))

;; ── G2 append-only + as-of time-travel ──
(deftest g2-as-of-time-travel
  (let [d (p/prune MANIFESTED "quarantine" "g10" COUNCIL {:at "2026-06-07T20:00:00.000Z" :council-level 6})
        r (p/regraft d COUNCIL {:at "2026-06-08T09:00:00.000Z"})]
    (is (= "live"       (get (p/apply-log [d r]) (get MANIFESTED "id"))))            ; current: healed
    (is (= "quarantine" (get (p/apply-log [d r] "2026-06-07") (get MANIFESTED "id")))) ; past: pruned
    (is (= {}           (p/apply-log [d r] "2026-06-05")))))                          ; before: nothing

;; ── G3 growth-unstoppable ──
(deftest g3-no-halt-or-delete-action
  (doseq [bad ["delete" "halt-organism" "prior-restraint" "verdict"]]
    (is (not (contains? p/PRUNE-ACTIONS bad)))
    (is (raises? #(p/prune MANIFESTED bad "x" COUNCIL {:at AT :council-level 7})))))

;; ── G4/G7 transparent care ──
(deftest g7-verdict-token-rejected
  (is (raises? #(p/assert-no-verdict "this branch is 違法 and the awardee is guilty")))
  (is (raises? #(p/prune MANIFESTED "revoke" "punish the 犯罪" COUNCIL {:at AT :council-level 7}))))

(deftest g7-basis-required
  (is (raises? #(p/prune MANIFESTED "quarantine" "   " COUNCIL {:at AT :council-level 6}))))

(deftest g7-non-adjudicating-flag
  (is (true? (get (p/prune MANIFESTED "quarantine" "g10 review" COUNCIL {:at AT :council-level 6})
                  "nonAdjudicating"))))

;; ── G5 no-server-key ──
(deftest g5-server-cannot-sign
  (is (raises? #(p/prune MANIFESTED "quarantine" "g10" "server" {:at AT :council-level 7})))
  (is (false? (get (p/prune MANIFESTED "quarantine" "g10" COUNCIL {:at AT :council-level 6})
                   "serverHeldKey"))))

;; ── Council floor + contested vote ──
(deftest council-invariant-needs-lv7
  (is (raises? #(p/prune MANIFESTED "rollback" "§2(a) hit" COUNCIL
                         {:at AT :council-level 6 :invariant-adjacent true})))
  (is (= 7 (get (p/prune MANIFESTED "rollback" "§2(a) hit" COUNCIL
                         {:at AT :council-level 7 :invariant-adjacent true})
                "councilLevel"))))

(deftest contested-prune-needs-majority
  (is (raises? #(p/prune MANIFESTED "quarantine" "contested" COUNCIL
                         {:at AT :council-level 6 :contested-vote {"yes" 2 "no" 5}})))
  (is (= "quarantine" (get (p/prune MANIFESTED "quarantine" "contested" COUNCIL
                                    {:at AT :council-level 6 :contested-vote {"yes" 6 "no" 1}})
                           "action"))))

;; ── G6 reversible ──
(deftest g6-regraft-heals
  (let [d (p/prune MANIFESTED "quarantine" "mistaken cut" COUNCIL {:at AT :council-level 6})
        r (p/regraft d COUNCIL {:at "2026-06-09T00:00:00.000Z"})]
    (is (= "regraft" (get r "kind")))
    (is (= "live" (get (p/apply-log [d r]) (get MANIFESTED "id")))))
  (let [d (p/prune MANIFESTED "quarantine" "x" COUNCIL {:at AT :council-level 6})]
    (is (raises? #(p/regraft d "server" {:at AT})))))

;; ── datom serialization ──
(deftest to-datoms-namespace
  (let [d (p/prune MANIFESTED "quarantine" "g10" COUNCIL {:at AT :council-level 6})
        datoms (p/to-datoms d)]
    (is (every? #(clojure.string/starts-with? (get % "a") ":sentei.prune/") datoms))
    (is (some #(= (get % "a") ":sentei.prune/action") datoms))
    (is (some #(= (get % "v_edn") "\"quarantine\"") datoms))))

(when (= *file* (System/getProperty "babashka.file"))
  (let [{:keys [fail error]} (run-tests 'sentei.methods.test-prune)]
    (System/exit (if (zero? (+ fail error)) 0 1))))
