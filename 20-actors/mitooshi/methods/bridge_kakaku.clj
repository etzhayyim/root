#!/usr/bin/env bb
;; Working Clojure port of methods/bridge_kakaku.py.
(ns mitooshi.methods.bridge-kakaku
  "mitooshi 見通し — kakaku 価格 price / supply-demand bridge (R0, offline).

  ADR-2606051800 (mitooshi) × ADR-2605091200 (kakaku). The cross-actor composition that
  lets mitooshi FORECAST the very price / supply-demand series kakaku OBSERVES — the price
  analogue of the watari/watatsuna chokepoint bridge (bridge.clj). kakaku derives two public,
  :representative observation kinds per canonical product:

    kakaku :ph/* (price history)   :ph/product + :ph/total-price → kind :price-level        (minor)
    kakaku :sd/* (supply/demand)   :sd/product + :sd/index       → kind :supply-demand-index (index)

  This bridge maps them into mitooshi `:series` + `:obs` datoms keyed on the product. Running
  it over successive snapshots builds the append-only as-of trail mitooshi forecasts (非終末論).

  CONSTITUTIONAL (mitooshi gates G2/G3/G4/G11):
    - kakaku's outputs are DERIVED public observations of merchant prices; the bridge ingests
      them as :representative / :public-broadcast, NEVER as authoritative fact, tagging
      :obs/source-actor \"kakaku\" (G11 honesty, G4 source-class).
    - mitooshi forecasts these series as DISTRIBUTIONS routed to RESILIENCE (where will
      scarcity arise?), never a price target and never a trade (G2 non-speculative). The
      bridge emits only series+obs; the forecast (distribution, :forecast/use :resilience)
      stays in forecast.clj.
    - Non-price/SD records (offers, merchants, spreads) are ignored — spread is a
      present-state transparency reading, not a forecastable series here.
    - Live wiring to kakaku's live output is G10-gated; R0 reads a static snapshot file.

  Run:  bb --classpath 20-actors 20-actors/mitooshi/methods/bridge_kakaku.clj
            --kakaku ../data/bridge/kakaku-sample.edn --at 1 [--out OUTDIR]"
  (:require [clojure.java.io :as io]
            [clojure.string :as str]
            [mitooshi.methods.analyze :as analyze]))

;; ── helpers ───────────────────────────────────────────────────────────────────

(defn- pslug
  "Slugify a kakaku product id (e.g. 'jan_4901777300443') for a series id.
  Strips a leading colon, replaces underscores and dots with dashes, lowercases.
  1:1 with _pslug in bridge_kakaku.py."
  [pid]
  (-> (str pid)
      (str/replace #"^:" "")
      (str/replace "_" "-")
      (str/replace "." "-")
      str/lower-case))

(defn- make-series
  "Build a :series/* map for the given product-slug, suffix, kind, and unit.
  1:1 with _series in bridge_kakaku.py."
  [pid suffix kind unit]
  (let [sid (str "s-" (pslug pid) "-" suffix)]
    {":series/id"           sid
     ":series/name"         (str (pslug pid) " " kind)
     ":series/kind"         (str ":" kind)
     ":series/unit"         unit
     ":series/freq"         ":daily"
     ":series/source"       "kakaku price roll-up (DERIVED, public)"
     ":series/source-class" ":public-broadcast"
     ":series/sourcing"     ":representative"}))

;; ── core bridge ──────────────────────────────────────────────────────────────

(defn bridge-kakaku
  "records = kakaku-shaped :ph/* and :sd/* observation maps (string-keyed, from load-edn).
  Returns {\"series\" {sid map}, \"obs\" [map], \"skipped\" n}.

  A :price-level series per product carrying :ph/total-price, and a :supply-demand-index
  series per product carrying :sd/index. Records lacking a product key are skipped.
  G2/G4/G11: source-class :public-broadcast, sourcing :representative, source-actor kakaku;
  no forecast, no trade."
  [records observed-at]
  (let [series  (atom {})
        obs     (atom [])
        skipped (atom 0)]

    (doseq [rec (or records [])]
      (cond
        ;; kakaku :ph/* price-history record
        (and (contains? rec ":ph/product") (contains? rec ":ph/total-price"))
        (let [pid (get rec ":ph/product")
              s   (make-series pid "price" "price-level" "minor")]
          (swap! series assoc (get s ":series/id") s)
          (swap! obs conj
                 {":obs/id"          (str "obs." (get s ":series/id") "." observed-at)
                  ":obs/series"       (get s ":series/id")
                  ":obs/observed-at"  observed-at
                  ":obs/value"        (double (get rec ":ph/total-price"))
                  ":obs/source-actor" "kakaku"}))

        ;; kakaku :sd/* supply-demand record
        (and (contains? rec ":sd/product") (contains? rec ":sd/index"))
        (let [pid (get rec ":sd/product")
              s   (make-series pid "supply-demand" "supply-demand-index" "index")]
          (swap! series assoc (get s ":series/id") s)
          (swap! obs conj
                 {":obs/id"          (str "obs." (get s ":series/id") "." observed-at)
                  ":obs/series"       (get s ":series/id")
                  ":obs/observed-at"  observed-at
                  ":obs/value"        (double (get rec ":sd/index"))
                  ":obs/source-actor" "kakaku"}))

        ;; non-price/SD records (offers, merchants, spreads) — ignored (G2)
        :else
        (swap! skipped inc)))

    {"series"  @series
     "obs"     @obs
     "skipped" @skipped}))

;; ── EDN emitter ──────────────────────────────────────────────────────────────

(defn emit-edn
  "Render the bridge result to a kotoba EDN string.
  1:1 with _emit_edn in bridge_kakaku.py."
  [b observed-at]
  (str/join
   "\n"
   (concat
    [(str ";; kakaku-observations.kotoba.edn — bridged from kakaku 価格 @ ts=" observed-at ".")
     ";; DERIVED public :representative observations (NOT authoritative). ADR-2606051800."
     ""
     "["]
    (for [s (vals (get b "series"))]
      (str " {:series/id \"" (get s ":series/id") "\" :series/kind " (get s ":series/kind")
           " :series/unit \"" (get s ":series/unit") "\" :series/source-class :public-broadcast"
           " :series/sourcing :representative}"))
    (for [o (get b "obs")]
      (str " {:obs/id \"" (get o ":obs/id") "\" :obs/series \"" (get o ":obs/series") "\""
           " :obs/observed-at " (get o ":obs/observed-at")
           " :obs/value " (get o ":obs/value")
           " :obs/source-actor \"" (get o ":obs/source-actor") "\"}"))
    ["]" ""])))

;; ── main / CLI ───────────────────────────────────────────────────────────────

(defn main [& argv]
  (let [args   (vec argv)
        idx-at (.indexOf args "--at")
        idx-kk (.indexOf args "--kakaku")]
    (when (or (< idx-at 0) (< idx-kk 0))
      (println "bridge_kakaku: --at <ts> and --kakaku <edn> are both required")
      (System/exit 1))
    (let [observed-at (Long/parseLong (nth args (inc idx-at)))
          records     (analyze/load-edn (io/file (nth args (inc idx-kk))))
          b           (bridge-kakaku records observed-at)
          idx-out     (.indexOf args "--out")]
      (when (>= idx-out 0)
        (let [outdir (io/file (nth args (inc idx-out)))]
          (.mkdirs outdir)
          (spit (io/file outdir "kakaku-observations.kotoba.edn")
                (emit-edn b observed-at))))
      (println (format "mitooshi kakaku-bridge @ ts=%d: %d series, %d obs; %d non-price/SD records ignored"
                       observed-at
                       (count (get b "series"))
                       (count (get b "obs"))
                       (get b "skipped")))
      (doseq [c (sort (keys (get b "series")))]
        (println (str "  → " c))))))

(when (= *file* (System/getProperty "babashka.file"))
  (apply main *command-line-args*))
