#!/usr/bin/env bb
;; test_kamado_invariants.clj — Lock-in tests for the kamado (竈) constitutional
;; invariants (ADR-2606051500). bb/cljc port of the retired test_kamado_invariants.py
;; (kamado py→cljc port wave, ADR-2606160842): the guard is now `feedstock_guard.cljc`,
;; so its invariant is exercised in Clojure, not by exec'ing a (deleted) .py.
;;
;; Pins the structural properties so a future refactor cannot silently weaken a
;; constitutional invariant. The signature kamado invariant is G1: a refining feedstock
;; MUST be closed-loop carbon; `:fossil-virgin-crude` is structurally UNREPRESENTABLE.
;; kamado declares the invariant THREE times and this suite proves all three agree:
;;   #1 ontology  (00-contracts/schemas/refining-ontology.kotoba.edn) :feedstock/class :db/allowed
;;   #2 lexicons  (orgs/etzhayyim/com-etzhayyim-kamado/wire/lex/*.json)  feedstockClass enum + consts
;;   #3 guard     (orgs/etzhayyim/com-etzhayyim-kamado/methods/feedstock_guard.cljc)      screen-feedstock raises on fossil
;;
;; Run: bb 70-tools/scripts/audit/test_kamado_invariants.clj   (exit 1 on any drift)
(ns test-kamado-invariants
  (:require [clojure.string :as str]
            [clojure.java.io :as io]
            [cheshire.core :as json]))

(def repo
  ;; this file lives at <repo>/70-tools/scripts/audit/ — repo root is 3 dirs up.
  (-> (io/file *file*) .getAbsoluteFile .getParentFile .getParentFile .getParentFile .getParentFile))

(defn- p [& parts] (str (apply io/file repo parts)))
(def ontology (p "00-contracts" "schemas" "refining-ontology.kotoba.edn"))
(def lexdir   (p "00-contracts" "lexicons" "com" "etzhayyim" "kamado"))
(def guard    (p "20-actors" "kamado" "methods" "feedstock_guard.cljc"))

;; The closed-loop carbon classes — the ONLY representable feedstocks (G1).
(def EXPECTED-FEEDSTOCK #{"biogenic" "captured-co2" "recycled-carbon" "existing-inventory-decommission"})
;; §2(d): the ONLY representable interventions on an existing fossil asset (G3).
(def EXPECTED-INTERVENTION #{"decommission" "remediate" "convert" "monitor"})
(def FORBIDDEN-FEEDSTOCK    #{"fossil-virgin-crude" "fossil" "crude" "virgin-crude"})
(def FORBIDDEN-INTERVENTION #{"expand" "restart-fossil" "revamp-throughput"})

(def ^:dynamic *fails* (atom []))
(defn- check [ok? msg] (when-not ok? (swap! *fails* conj msg)))
(defn- raises? [f] (try (f) false (catch Throwable _ true)))

(defn- load-json [name] (json/parse-string (slurp (str (io/file lexdir name)))))
(defn- record-props [lex] (get-in lex ["defs" "main" "record" "properties"]))
(defn- lstrip-colon [s] (str/replace (str s) #"^:+" ""))

(defn- ontology-feedstock-allowed
  "Extract the :feedstock/class :db/allowed keyword set from the ontology (regex, mirrors the .py)."
  []
  (let [text (slurp ontology)
        m (re-find #"(?s):feedstock/class\s*\{.*?:db/allowed\s*\[(.*?)\]" text)]
    (check (some? m) "could not locate :feedstock/class :db/allowed in the ontology")
    (set (map lstrip-colon (re-seq #":[a-z0-9-]+" (or (second m) ""))))))

;; ── load the guard (enforcement point #3) ──
(load-file guard)
(def ALLOWED-FEEDSTOCK    @(resolve 'kamado.methods.feedstock-guard/ALLOWED-FEEDSTOCK))
(def ALLOWED-INTERVENTION @(resolve 'kamado.methods.feedstock-guard/ALLOWED-INTERVENTION))
(def screen-feedstock    (resolve 'kamado.methods.feedstock-guard/screen-feedstock))
(def screen-intervention (resolve 'kamado.methods.feedstock-guard/screen-intervention))

;; 1. G1 — ontology :feedstock/class :db/allowed excludes fossil
(let [allowed (ontology-feedstock-allowed)]
  (check (= allowed EXPECTED-FEEDSTOCK) (str "G1: ontology :feedstock/class drifted; got " (sort allowed)))
  (doseq [bad FORBIDDEN-FEEDSTOCK]
    (check (not (contains? allowed bad)) (str "G1 VIOLATION: fossil feedstock " (pr-str bad) " became representable in the ontology"))))

;; 2. G1 — lexicon feedstockClass enum + closedLoop/screened consts
(doseq [name ["feedstockProvenance.json" "synthesisRun.json"]]
  (let [enum (set (get-in (record-props (load-json name)) ["feedstockClass" "enum"]))]
    (check (= enum EXPECTED-FEEDSTOCK) (str "G1: " name " feedstockClass enum drifted; got " (sort enum)))
    (doseq [bad FORBIDDEN-FEEDSTOCK]
      (check (not (contains? enum bad)) (str "G1 VIOLATION: " name " feedstockClass admits fossil " (pr-str bad))))))
(let [props (record-props (load-json "feedstockProvenance.json"))]
  (doseq [field ["closedLoop" "screened"]]
    (check (= true (get-in props [field "const"])) (str "G1: feedstockProvenance." field " MUST be const true"))))

;; 3. G1 — the guard raises on fossil, passes on each allowed class
(check (= (set (map lstrip-colon ALLOWED-FEEDSTOCK)) EXPECTED-FEEDSTOCK)
       (str "G1: guard ALLOWED-FEEDSTOCK drifted; got " ALLOWED-FEEDSTOCK))
(check (raises? #(screen-feedstock ":fossil-virgin-crude")) "G1: guard must raise on :fossil-virgin-crude")
(doseq [cls EXPECTED-FEEDSTOCK]
  (check (not (raises? #(screen-feedstock (str ":" cls)))) (str "G1: guard must ACCEPT closed-loop " cls)))

;; 4. G3 — intervention wind-down/convert set only; never expand/restart-fossil
(let [enum (set (get-in (record-props (load-json "decommissionPlan.json")) ["intervention" "enum"]))]
  (check (= enum EXPECTED-INTERVENTION) (str "G3: decommissionPlan.intervention enum drifted; got " (sort enum)))
  (doseq [bad FORBIDDEN-INTERVENTION]
    (check (not (contains? enum bad)) (str "G3 VIOLATION: fossil life-extension " (pr-str bad) " became representable"))))
(check (= (set (map lstrip-colon ALLOWED-INTERVENTION)) EXPECTED-INTERVENTION)
       (str "G3: guard ALLOWED-INTERVENTION drifted; got " ALLOWED-INTERVENTION))
(check (raises? #(screen-intervention ":expand")) "G3: guard must raise on :expand")
(check (raises? #(screen-intervention ":restart-fossil")) "G3: guard must raise on :restart-fossil")

;; 5. G4 — refineryAsset observes (observe ≠ operate)
(check (= true (get-in (record-props (load-json "refineryAsset.json")) ["isObservation" "const"]))
       "G4: refineryAsset.isObservation MUST be const true (observation ≠ operation; not a target-list)")

;; 6 + 7. G5 / G8 — decommissionPlan no-server-key + outward-gated
(let [props (record-props (load-json "decommissionPlan.json"))]
  (check (= false (get-in props ["serverHeldKey" "const"])) "G5: decommissionPlan.serverHeldKey MUST be const false (no-server-key)")
  (check (= true  (get-in props ["outwardGated" "const"]))  "G8: decommissionPlan.outwardGated MUST be const true"))

;; 8. G7 — carbonBalance is a derived analyzer output
(let [sourcing (get (record-props (load-json "carbonBalance.json")) "sourcing")]
  (check (= "derived" (get sourcing "const")) "G7: carbonBalance.sourcing MUST be const 'derived'")
  (check (= ["derived"] (get sourcing "enum")) (str "G7: carbonBalance.sourcing enum MUST be [\"derived\"]; got " (get sourcing "enum"))))

;; ── report ──
(let [fails @*fails*]
  (if (seq fails)
    (do (println (str "kamado-invariants: " (count fails) " FAILURE(S):"))
        (doseq [f fails] (println "  ✗" f))
        (System/exit 1))
    (println "kamado-invariants: all 8 invariant groups green (G1 ontology+lexicon+guard / G3 / G4 / G5 / G7 / G8)")))
