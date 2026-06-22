;; etzhayyim.kosei-tiers — Kosei tier classification pure logic (cljc port, wave 2).
;;
;; Pure-logic port of the tier-management section of
;; 70-tools/etzhayyim-py/src/etzhayyim/kosei.py
;; (no click, no subprocess, no duckdb, no filesystem — pure classification logic).
;;
;; Ported constants and functions:
;;   tier-eta       — tier name → η (eta efficiency) map
;;   tier-order     — canonical [T1 T2 T3] ordering
;;   default-tier   — "T2"
;;   suggest-tier   — heuristic: infer best tier from app metadata map
;;   tier-eta-of    — look up η for a tier name (0.0 if unknown)
;;   valid-tier?    — true if name is T1/T2/T3
;;   next-tier      — T1→T2→T3 promotion step
;;   prev-tier      — T3→T2→T1 demotion step
;;
;; IO functions (scan_kosei, CLI commands, duckdb snapshot, JSON r/w) are
;; NOT ported here; they stay in the Python module.
;;
;; bb usage (classpath 70-tools/src):
;;   (require '[etzhayyim.kosei-tiers :as kt])
;;   (kt/suggest-tier {"name" "gateway" "dir" "50-infra/..."}) ;=> "T3"
;;   (kt/next-tier "T1")                                       ;=> "T2"

(ns etzhayyim.kosei-tiers
  (:require [clojure.string :as str]))

;; ── constants ────────────────────────────────────────────────────────────────────

(def tier-eta
  "Tier name → η (execution efficiency) map."
  {"T1" 0.667
   "T2" 0.500
   "T3" 0.910})

(def tier-order
  "Canonical tier ordering from lowest to highest: [T1 T2 T3]."
  ["T1" "T2" "T3"])

(def default-tier
  "Default tier assigned when none is set."
  "T2")

;; ── pure classification helpers ──────────────────────────────────────────────────

(defn valid-tier?
  "Return true if tier is one of T1 / T2 / T3."
  [tier]
  (contains? tier-eta tier))

(defn tier-eta-of
  "Return η for tier, or 0.0 if tier is unrecognised."
  [tier]
  (get tier-eta tier 0.0))

(defn suggest-tier
  "Heuristic tier suggestion from an app metadata map.
   meta-map keys: \"name\" \"dir\" \"performerType\" (mirrors Python _suggest_tier).

   Rules (in priority order):
     T3 — name/dir contains infra keyword, or performerType = \"system\",
           or dir is under 50-infra
     T1 — dir is under 20-actors, or name contains \"kotodama\",
           or performerType = \"actor\"
     T2 — default

   Returns one of \"T1\" / \"T2\" / \"T3\"."
  [meta-map]
  (let [name-s  (str/lower-case (str (get meta-map "name" "")))
        dir-s   (str (get meta-map "dir" ""))
        pt      (str/lower-case (str (get meta-map "performerType" "")))
        combined (str name-s " " (str/lower-case dir-s))
        infra-kws ["infra" "gateway" "auth" "pds" "graph" "router" "proxy" "platform"]]
    (cond
      (or (some #(str/includes? combined %) infra-kws)
          (= pt "system")
          (str/includes? dir-s "50-infra"))
      "T3"

      (or (str/includes? dir-s "20-actors")
          (str/includes? name-s "kotodama")
          (= pt "actor"))
      "T1"

      :else "T2")))

(defn tier-index
  "Return 0-based index of tier in tier-order, or -1 if unrecognised."
  [tier]
  (let [idx (first (keep-indexed (fn [i t] (when (= t tier) i)) tier-order))]
    (if (nil? idx) -1 idx)))

(defn next-tier
  "Return the next (promoted) tier, or nil if already at max.
   T1 → T2 → T3 → nil."
  [tier]
  (let [idx (tier-index tier)]
    (when (and (>= idx 0) (< idx (dec (count tier-order))))
      (nth tier-order (inc idx)))))

(defn prev-tier
  "Return the previous (demoted) tier, or nil if already at min.
   T3 → T2 → T1 → nil."
  [tier]
  (let [idx (tier-index tier)]
    (when (> idx 0)
      (nth tier-order (dec idx)))))
