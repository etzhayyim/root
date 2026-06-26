(ns minori.measure
  "Real grounding of the η and Φ levers from OBSERVED data (the 観測/計測 step), replacing
   the cold-start stubs:
     η  ← the live ie-flow scoreboard (colony order-export, mean of per-actor η components)
     Φ  ← the ACTUAL roster size: realized coupling ln(adopted) vs the ln(n=18342)≈9.8 ceiling.
   Read-only, no-server-key, fail-open (absent scoreboard ⇒ loop keeps its own estimate)."
  (:require [clojure.edn :as edn]
            [clojure.java.io :as io]
            [minori.capture :as capture]))

(defn read-edn [path] (when (.exists (io/file path)) (edn/read-string (slurp path))))

(defn colony-eta
  "Observed colony η = mean of the per-actor η components on the ie-flow scoreboard.
   nil if the scoreboard is absent (fail-open — the loop stays on its own estimate)."
  [scoreboard-path]
  (when-let [sb (read-edn scoreboard-path)]
    (let [etas (->> (:scored sb) (keep #(get-in % [:components :eta])) (map double))]
      (when (seq etas)
        {:n (count etas)
         :mean (/ (reduce + etas) (count etas))
         :min (apply min etas)
         :max (apply max etas)}))))

(defn realized-phi
  "Realized Φ multiplier = ln(adopted) — the coupling the current roster actually achieves —
   vs the ln(n=18342)≈9.8 ceiling. A REAL (not stub) reading of the Φ lever."
  [adopted]
  (when (and adopted (pos? adopted)) (Math/log (double adopted))))

(defn observe
  "Read-only observation snapshot taken every beat (for transparency in the ledger):
   η from the live scoreboard, Φ from the roster, capture from the operator capture snapshot
   (minori.capture — snapshot=SoT, G7). All read-only, no-server-key, fail-open."
  [{:keys [scoreboard capture-snapshot]} adopted]
  {:colony-eta    (colony-eta scoreboard)
   :realized-phi  (realized-phi adopted)
   :capture       (capture/captured-ratio capture-snapshot)})

(defn ground
  "Apply the observation to state (the 実装/計測 step). Sets GROUNDED fields (truth), distinct
   from the loop's stub estimates: :eta-grounded rises toward the observed colony mean (monotone),
   :phi-realized = real ln(adopted), :capture-grounded = the real pre-revenue ratio (≈0).
   Honestly reveals η≈colony-mean<1 (net-taker, transition not yet won) and capture≈0 (no live
   value captured) — grounding can LOWER the optimistic stub; that is the point."
  [state obs]
  (cond-> state
    (get-in obs [:colony-eta :mean])
      (update :eta-grounded (fnil max 0.0) (get-in obs [:colony-eta :mean]))
    (:realized-phi obs)
      (assoc :phi-realized (:realized-phi obs))
    (:capture obs)
      (assoc :capture-grounded (:ratio (:capture obs)))))
