;; kudamori 管守 — end-to-end sewer-cleaning analyzer (orchestrator).
;;
;; Loads the sewer-network seed and runs the R0 sim pipeline:
;;   1. confined-space ENTRY GATE (★ G5) — check the entry-manhole gas reading; if
;;      unsafe, model purge-to-entry (forced ventilation) and only then admit entry;
;;      an atmosphere that never passes leaves entry refused (no human, no robot).
;;   2. in-pipe NAVIGATION — diameter-fit-checked shortest route from the access
;;      manhole to the target segment, routing around other blocked segments.
;;   3. JETTING — pressure-safe (★ G7) hydro-jet of the target, with debris-removal
;;      estimate + water reuse balance (G2; residual effluent → mizuho).
;;
;; Pure Clojure, no deps → babashka-runnable AND kotoba-pywasm-portable.
;; Per ADR-2606142030 (kudamori R0).
(ns kudamori.methods.analyze
  (:require [clojure.edn :as edn]
            [kudamori.methods.atmosphere :as atm]
            [kudamori.methods.pipe-nav :as nav]
            [kudamori.methods.jetting :as jet]))

(defn load-seed
  "Read the sewer-network EDN seed into a Clojure map."
  [path]
  (edn/read-string (slurp path)))

(defn- seg-by-id [segments sid] (first (filter #(= (:id %) sid) segments)))

(defn run
  "Run the full R0 analysis over a loaded seed map. Returns a report map.
   The entry gate comes FIRST: an atmosphere that cannot be made safe leaves
   :entry {:permitted? false …} and the downstream legs report :gated."
  [seed]
  (let [segments (:segments seed)
        robot (:robot seed)
        job (:job seed)
        reading (:gas-reading seed)
        blower (:blower seed)
        ;; 1. confined-space entry gate (★ G5)
        raw-ok (atm/entry-permitted? reading)
        purge (when-not raw-ok
                (atm/purge-to-entry reading (:air-changes-per-min blower) 60))
        permitted (or raw-ok (boolean (:entry-permitted? purge)))
        entry {:permitted? permitted
               :raw-safe? raw-ok
               :raw-hazards (atm/hazards reading)
               :purge (when purge (select-keys purge [:entry-permitted? :minutes :hazards]))}]
    (if-not permitted
      ;; entry refused — no navigation, no jetting (the human/robot stays out)
      {:entry entry :navigation :gated :jetting :gated}
      (let [nav-plan (nav/plan-nav robot segments (:access job) (:target-segment job))
            tseg (seg-by-id segments (:target-segment job))
            clean (jet/clean-segment tseg (:jet robot) (:debris-frac job) 30)]
        {:entry entry
         :navigation nav-plan
         :jetting clean}))))

(defn report-str
  "Human-readable report (for out/ and Murakumo narration input, G6)."
  [res]
  (let [e (:entry res)]
    (str ";; kudamori 管守 — sewer-cleaning R0 analysis\n"
         "entry permitted: " (:permitted? e)
         (when-not (:raw-safe? e)
           (str " (after purge "
                (get-in e [:purge :minutes]) " min)"))
         "\n"
         (if (= :gated (:navigation res))
           "navigation: GATED (unsafe atmosphere — entry refused, G5)\n"
           (str "route hops: " (get-in res [:navigation :hops])
                "  target-blocked: " (get-in res [:navigation :target-blocked?]) "\n"))
         (if (= :gated (:jetting res))
           "jetting: GATED\n"
           (str "jet pressure (bar): " (format "%.0f" (get-in res [:jetting :pressure-bar]))
                " / rating " (format "%.0f" (get-in res [:jetting :rating-bar])) "\n"
                "debris removed (m³): " (format "%.3f" (get-in res [:jetting :debris-removed-m3])) "\n"
                "water reuse frac: " (format "%.2f" (get-in res [:jetting :water :reuse-frac]))
                "  effluent→mizuho (L): " (format "%.1f" (get-in res [:jetting :water :effluent-l])) "\n")))))

(defn -main [& args]
  (let [path (or (first args) "20-actors/kudamori/data/network.edn")
        res (run (load-seed path))]
    (print (report-str res))
    (flush)))
