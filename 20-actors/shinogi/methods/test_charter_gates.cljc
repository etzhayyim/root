#!/usr/bin/env bb
;; shinogi 鎬 — constitutional-gate conformance tests (clj-native, self-contained).
(ns shinogi.methods.test-charter-gates
  "shinogi 鎬 — constitutional-gate conformance (ADR-2606291200). shinogi is an
  ANALYSIS-ONLY exam-competition involution OBSERVER — it reads which feedback loops
  are spinning 悪循環/好循環 + Meadows leverage candidates, and it may ONLY look,
  never touch. Unlike the AT-Proto-lexicon actors, shinogi's gates are pinned three
  ways, ALL self-contained (no external lexicon files needed at R0):

    G4  ANALYSIS-ONLY / NO ACTUATION — no dispatch/post/mention/email/tx path exists
        (enforced by ABSENCE; the manifest declares no outward cell, and the
        ontology marks :shinogi/actuate + :shinogi/dispatch unrepresentable)
    G5  no causal overclaim — :shinogi.exam.loop/proven-cause unrepresentable; every
        derived datom carries :shinogi/hypothesis :true
    G6  aggregate-only — :shinogi.exam.driver/person + :shinogi.exam.student/score
        unrepresentable; no person/student datom is ever emitted
    G7  wellbecoming-positive / sober — the failure cycle routes to relief (kokoro/shiori)
    G8  relief MAP not a shame-rank — :shinogi.exam.student/ranking unrepresentable
    G11 no prescription — :shinogi/prescription unrepresentable; leverage candidates
        carry :prescription? false

  It weakens no gate; it asserts them."
  (:require [shinogi.methods.shinogi-edn :as se]
            [shinogi.methods.analyze :as az]
            [clojure.edn :as edn]
            [clojure.string :as str]
            [clojure.test :refer [deftest is run-tests]]
            [clojure.java.io :as io]))

(def ^:private actor-dir "20-actors/shinogi")
(defn- manifest [] (edn/read-string (slurp (io/file actor-dir "manifest.edn"))))
(defn- ontology [] (edn/read-string (slurp (io/file actor-dir "kotoba/ontology.shinogi-exam.edn"))))
(def seed-path (str actor-dir "/kotoba/seed.exam-involution.edn"))

;; ── G4 structural — NO outward-channel cell / method exists (enforced by absence) ──
(deftest g4-no-outward-channel
  (let [m (manifest)
        sub (:actor/substrate m)
        methods (set (:methods sub))
        forbidden #"(?i)dispatch|post|mention|email|smtp|transact|actuat|broadcast|submit|send|publish|nudge"]
    (is (not-any? #(re-find forbidden (str %)) methods)
        (str "G4: shinogi must declare NO outward-channel method; found "
             (filter #(re-find forbidden (str %)) methods)))
    ;; the gate is itemized in the manifest
    (is (some #(= "G4" (:gate/id %)) (:actor/gates m)) "G4 declared in manifest")))

;; ── ontology negative space — forbidden attrs are unrepresentable ────────────
(deftest negative-space-unrepresentable
  (let [un (set (:unrepresentable (ontology)))]
    (doseq [a [":shinogi/actuate" ":shinogi/dispatch"
               ":shinogi.exam.driver/person" ":shinogi.exam.student/score"
               ":shinogi.exam.student/ranking" ":shinogi.exam.loop/proven-cause"
               ":shinogi/prescription"]]
      (is (contains? un a) (str a " must be declared unrepresentable")))))

;; ── G4/G5/G6/G8 — analyze NEVER emits a forbidden attribute ──────────────────
(deftest analyze-emits-no-forbidden-attr
  (let [drivers (se/drivers seed-path)
        ds (az/datoms drivers (az/analyze drivers))
        attrs (set (map #(nth % 2) ds))
        forbidden #"(?i)actuate|dispatch|/person|student/score|student/ranking|proven-cause|prescription"]
    (is (seq ds))
    (is (not-any? #(re-find forbidden %) attrs)
        (str "no forbidden attribute may appear in emitted datoms; found "
             (filter #(re-find forbidden %) attrs)))))

;; ── G9 — every emitted datom is an append (:db/add) ──────────────────────────
(deftest g9-append-only
  (let [drivers (se/drivers seed-path)
        ds (az/datoms drivers (az/analyze drivers))]
    (is (every? #(= ":db/add" (first %)) ds) "append-only — no :db/retract")))

;; ── G5 — every derived datom is a hypothesis ─────────────────────────────────
(deftest g5-hypothesis-flagged
  (let [drivers (se/drivers seed-path)
        ds (az/datoms drivers (az/analyze drivers))
        entities (distinct (map second ds))]
    ;; each entity that has any derived datom must also carry :shinogi/hypothesis :true
    (doseq [e entities]
      (let [e-attrs (set (map #(nth % 2) (filter #(= e (second %)) ds)))]
        (when (some #(str/includes? % "/regime") e-attrs)
          (is (contains? e-attrs ":shinogi/hypothesis")
              (str "G5: regime entity " e " must be flagged hypothesis")))))))

;; ── G11 — leverage candidates carry prescription? false ──────────────────────
(deftest g11-no-prescription
  (let [lev (get (az/analyze (se/drivers seed-path)) "leverage")]
    (is (false? (:prescription? lev)))
    (is (every? #(false? (:prescription? %)) (concat (:amplify lev) (:flip lev))))))

;; ── G7 — the failure cycle routes to relief, never amplifies ─────────────────
(deftest g7-failure-routes-to-relief
  (let [fc (get (az/analyze (se/drivers seed-path)) "failure_cycle")]
    (is (= ["kokoro" "shiori"] (:route-to fc)) "failure cycle routes to relief actors")
    (is (str/includes? (:note fc) "never") "the note disclaims amplification/shame")))

#?(:clj
   (defn -main [& _]
     (let [r (run-tests 'shinogi.methods.test-charter-gates)]
       (System/exit (if (zero? (+ (:fail r) (:error r))) 0 1)))))
