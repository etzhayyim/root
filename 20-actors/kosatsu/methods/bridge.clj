#!/usr/bin/env bb
;; Working Clojure port of methods/bridge.py.
(ns kosatsu.methods.bridge
  "bridge.clj — 高札 (kosatsu) cross-actor SoS composition. ADR-2606072000.

  kosatsu is the competing-claim BOARD; the SoS intel value comes from composing its divergence
  view with the sibling accountability/intel actors over the SHARED kotoba Datom log. This module
  computes the JOIN KEYS kosatsu exposes so a downstream actor can link a designation subject to
  its other observations — WITHOUT kosatsu reaching into another actor's graph (each actor owns
  its own datoms; bridge only emits the keys).

    - tadori 辿   : a :designated-wallet subject → on-chain attribution case (authorized only)
    - keizu 系図  : a :designated-org/entity subject → public power-relations node (if public role)
    - tsumugi 紡ぎ: a subject's asserter → power-entity 縁 (who designates whom, as influence)
    - kanae 鼎    : the by-authority / divergence aggregates → fiscal/atlas render
    - tasuke 助   : never — a victim-support flow is person-consented, disjoint (no auto-link)

  The bridge is MAP-ONLY (G9): it surfaces a join key for resilience/awareness/due-process, never
  an enforcement instruction. It NEVER promotes a contested designation to a verdict.

  Stdlib only. Deterministic.

  Run:  bb --classpath 20-actors 20-actors/kosatsu/methods/bridge.clj"
  (:require [kosatsu.methods.weave :as w]
            [kosatsu.methods.edn :as e]
            [clojure.java.io :as io]
            [clojure.string :as str]))

(def ^:private this-file *file*)
(defn- actor-root [] (-> this-file io/file .getAbsoluteFile .getParentFile .getParentFile))

;; subject kind → the sibling actor that can further observe it (join target). Person/org subjects
;; only bridge to a PUBLIC-role actor when they are already a public power role (keizu's own G1
;; decides admissibility downstream); kosatsu only emits the key, never the link.
(def ^:private bridge-targets
  {"designated-wallet" "tadori"
   "designated-domain" "tadori"
   "designated-org"    "keizu"
   "designated-entity" "keizu"})

(defn- lstrip-colon
  "str(x).lstrip(':') — strip ALL leading colons (matches Python lstrip(':') semantics)."
  [v]
  (str/replace (str (or v "")) #"^:+" ""))

(defn join-keys
  "For each currently-LISTED-by-someone subject, emit a cross-actor join key + its divergence
  class. Delisted-everywhere / silent subjects are skipped (nothing live to compose). The key
  is advisory routing only (G9)."
  ([g] (join-keys g nil))
  ([g ts]
   (let [subjects (get g "subjects")
         out (reduce
              (fn [acc [sid s]]
                (let [div (w/divergence g sid ts)]
                  (if (empty? (get div "listing"))
                    acc  ; nobody currently lists it → no live composition
                    (let [kind   (lstrip-colon (get s ":subject/kind" ""))
                          target (get bridge-targets kind)]
                      (conj acc
                            {"subject"          sid
                             "subject_kind"     kind
                             "divergence_class" (get div "class")
                             "listing_asserters" (get div "listing")
                             "bridge_to"        target
                             "note"             "advisory join key for SoS awareness; never an enforcement instruction (G9)"})))))
              []
              subjects)]
     ;; sort by (bridge_to or "~", subject) — None → "~" sort sentinel
     (vec (sort-by (fn [x] [(or (get x "bridge_to") "~") (get x "subject")]) out)))))

(defn tsumugi-en-edges
  "tsumugi 縁 projection: each currently-listed designation is an asserter→subject INFLUENCE
  edge (who exercises designating power over whom). Edge-primary, attributed; never a per-node
  score. Feeds tsumugi's power-entity 縁 weave."
  ([g] (tsumugi-en-edges g nil))
  ([g ts]
   (let [out (reduce
              (fn [acc d]
                (let [sub (get d ":designation/subject")
                      ass (get d ":designation/asserter")]
                  (if (= (w/status-as-of g sub ass ts) "listed")
                    (conj acc
                          {"from"    ass
                           "to"      sub
                           "kind"    "designation-power"
                           "measure" (lstrip-colon (get d ":designation/measure" ""))
                           "as_of"   (get d ":designation/posted-at")})
                    acc)))
              []
              (get g "designations"))]
     (vec (sort-by (juxt #(get % "from") #(get % "to")) out)))))

(defn main [& _argv]
  (let [seed (e/load-edn (io/file (actor-root) "data" "seed-designation-graph.kotoba.edn"))
        g    (w/weave seed)]
    (println "# kosatsu cross-actor join keys (advisory, G9)\n")
    (doseq [k (join-keys g)]
      (println (str "- " (get k "subject")
                    " [" (get k "divergence_class") "]"
                    " kind=" (get k "subject_kind")
                    " → " (get k "bridge_to")
                    " (listed by " (get k "listing_asserters") ")")))
    (println (str "\n# tsumugi 縁 edges: " (count (tsumugi-en-edges g)) " designation-power edges"))))

(when (= *file* (System/getProperty "babashka.file"))
  (apply main *command-line-args*))
