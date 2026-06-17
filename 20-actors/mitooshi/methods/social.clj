#!/usr/bin/env bb
;; Working Clojure port of methods/social.py (aggregate-first resilience advisory + AT Proto post; live posting is the operator leg).
(ns mitooshi.methods.social
  "mitooshi 見通し — aggregate-first resilience advisory + social post (R1, offline).

  ADR-2606051800. The non-adjudicating delivery layer: turns a forecast DISTRIBUTION over a
  public series into an aggregate-first resilience advisory and an AT Proto social post,
  routed to a PLANNER — never rendered as advice. The charter-clean inverse of a 'price call'.

  Gates (all preserved exactly from social.py):
    G1 distribution-only   — a forecast with pointAsserted=true is REFUSED at the door.
    G2 non-speculative     — use must be in ALLOWED-USE; trade/speculation refused.
    G3 non-adjudicating    — every advisory MUST name a planner (danjo/kanae/watari).
    G4 aggregate-first     — posts are anonymized aggregates (shape == 'aggregate').
    no-server-key          — live broadcast is operator-gated; default is :draft.

  stdlib only.
  Run:  bb --classpath 20-actors 20-actors/mitooshi/methods/social.clj --series s-demo --mean 0.2 --sd 0.3 --route danjo"
  (:require [clojure.string :as str]))

;; G2 — the only non-speculative uses; trade/speculation/wager/position are NOT members.
(def ALLOWED-USE #{":resilience" ":planning" ":nowcast" ":early-warning" ":research"})
;; G3 — the planners mitooshi may route a resilience advisory to (it never decides itself).
(def PLANNERS #{"danjo" "kanae" "watari"})

;; ── py-faithful message rendering ─────────────────────────────────────────────
;; The refusal messages mirror social.py's f-strings, which render the Python TUPLEs
;; ALLOWED_USE / PLANNERS as `('a', 'b', …)` (ordered, single-quoted, comma-space) and a
;; scalar `{x!r}` as `'x'`. clj sets are unordered + pr-str uses double quotes, so we keep the
;; sets for membership but render the message from these ordered tuples (parity-caught).
(def ^:private ALLOWED-USE-TUPLE [":resilience" ":planning" ":nowcast" ":early-warning" ":research"])
(def ^:private PLANNERS-TUPLE ["danjo" "kanae" "watari"])
(defn- py-repr [x] (str "'" x "'"))
(defn- py-tuple-repr [xs] (str "(" (str/join ", " (map py-repr xs)) ")"))

(defn- round4
  "Round x to 4 decimal places (mirrors Python's round(x, 4))."
  [x]
  (/ (Math/round (* (double x) (Math/pow 10 4))) (Math/pow 10 4)))

(defn- _narrate
  "Optional Murakumo-only narration (G6). Returns nil when llm host binding is absent (offline)."
  [_series _lo _hi]
  ;; kotoba llm host binding is not available in babashka/offline — fail-open to nil.
  nil)

(defn compose-resilience-advisory
  "Compose ONE aggregate-first resilience advisory from a forecast distribution. Refuses
  (ex-info) a point assertion (G1), an illegal use (G2), or a missing/invalid planner
  route (G3). The text states a BAND, never a single value.

  Args mirror social.py: series mean sd target use point-asserted route-to"
  ([series mean sd target] (compose-resilience-advisory series mean sd target ":resilience" false "danjo"))
  ([series mean sd target use] (compose-resilience-advisory series mean sd target use false "danjo"))
  ([series mean sd target use point-asserted] (compose-resilience-advisory series mean sd target use point-asserted "danjo"))
  ([series mean sd target use point-asserted route-to]
   (when point-asserted
     (throw (ex-info "G1: mitooshi cannot post a point-asserted forecast (distribution-only)"
                     {:gate :G1})))
   (when-not (contains? ALLOWED-USE use)
     (throw (ex-info (str "G2: use " (py-repr use) " not in the non-speculative set " (py-tuple-repr ALLOWED-USE-TUPLE))
                     {:gate :G2})))
   (when-not (contains? PLANNERS route-to)
     (throw (ex-info (str "G3: a resilience advisory must route to a planner " (py-tuple-repr PLANNERS-TUPLE)
                          ", got " (py-repr route-to))
                     {:gate :G3})))
   (let [lo (round4 (- mean sd))
         hi (round4 (+ mean sd))
         mean4 (round4 mean)
         text (str "見通し(分布): 系列 " series " の t=" target
                   " 期待値は概ね [" lo ", " hi "] の範囲"
                   "(中心 " mean4 ")。これは確率分布であり断定的な予測ではありません。"
                   "レジリエンス対応は " route-to " が判断します。")]
     {"series"        series
      "text"          text
      "shape"         "aggregate"   ;; G4
      "use"           use           ;; G2
      "pointAsserted" false         ;; G1
      "band68"        [lo hi]
      "routeTo"       route-to      ;; G3 — planner decides, mitooshi only states
      "lexicon"       "app.bsky.feed.post"
      "narration"     (_narrate series lo hi)})))

(defn handle-social-post
  "Compose aggregate resilience advisories from forecast records and (optionally) post.
  Each forecast = {:series :mean :sd :target [:use] [:pointAsserted] [:routeTo]}.
  A point assertion (G1), illegal use (G2), or missing planner route (G3) is refused
  per-item with a reason. Live broadcast is operator-gated (no-server-key): without
  operatorRef posts are :draft. Aggregate-share is 100% (G4)."
  [state]
  (let [operator-ref (get state "operatorRef")
        forecasts    (get state "forecasts" [])
        posts        (atom [])
        refused      (atom [])]
    (doseq [f forecasts]
      (let [series        (get f "series" "?")
            mean          (double (get f "mean" 0.0))
            sd            (double (get f "sd" 1.0))
            target        (int (get f "target" 0))
            use           (get f "use" ":resilience")
            point-assert  (boolean (get f "pointAsserted" false))
            route-to      (get f "routeTo" "danjo")]
        (try
          (let [adv (compose-resilience-advisory series mean sd target use point-assert route-to)
                adv+ (assoc adv "state" (if operator-ref "posted" "draft"))]
            (swap! posts conj adv+))
          (catch Exception e
            (swap! refused conj {"series" series "reason" (ex-message e)})))))
    (merge state
           {"posts"             @posts
            "refused"           @refused
            "broadcast"         (boolean operator-ref)
            "aggregateSharePct" (if (seq @posts) 100 0)})))

(defn main [& argv]
  (let [args (vec argv)
        opt  (fn [flag default] (let [i (.indexOf args flag)]
                                  (if (>= i 0) (nth args (inc i)) default)))
        adv  (compose-resilience-advisory
              (opt "--series" "s-demo")
              (Double/parseDouble (opt "--mean" "0.0"))
              (Double/parseDouble (opt "--sd" "1.0"))
              (Integer/parseInt (opt "--target" "7"))
              ":resilience"
              false
              (opt "--route" "danjo"))]
    (println (get adv "text"))
    (println (str "  use=" (get adv "use")
                  " point=" (get adv "pointAsserted")
                  " route→" (get adv "routeTo")
                  " shape=" (get adv "shape")))))

(when (= *file* (System/getProperty "babashka.file"))
  (apply main *command-line-args*))
