(ns minori.measure
  "Real grounding of the η and Φ levers from OBSERVED data (the 観測/計測 step), replacing
   the cold-start stubs:
     η  ← the live ie-flow scoreboard (colony order-export, mean of per-actor η components)
     Φ  ← the ACTUAL roster size: realized coupling ln(adopted) vs the ln(n=18342)≈9.8 ceiling.
   Read-only, no-server-key, fail-open (absent scoreboard ⇒ loop keeps its own estimate)."
  (:require [clojure.edn :as edn]
            [clojure.java.io :as io]))

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
  "Read-only observation snapshot taken every beat (for transparency in the ledger)."
  [{:keys [scoreboard]} adopted]
  {:colony-eta   (colony-eta scoreboard)
   :realized-phi (realized-phi adopted)})

(defn ground
  "Apply the observation to state (the 実装/計測 step) — used when a :measure lever fires.
   η-estimate rises toward the observed colony mean (monotone: never lowers a hard-won η);
   φ-realized is set to the real ln(adopted). Grounding replaces the stub with the truth —
   which honestly reveals η≈colony-mean (still <1 ⇒ net-taker, the phase transition not yet won)."
  [state obs]
  (cond-> state
    (get-in obs [:colony-eta :mean])
      (update :eta-estimate (fnil max 0.0) (get-in obs [:colony-eta :mean]))
    (:realized-phi obs)
      (assoc :phi-realized (:realized-phi obs))))
