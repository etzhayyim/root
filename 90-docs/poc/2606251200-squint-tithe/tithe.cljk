(ns tithe)
(def TITHE-PERMILLE (js/BigInt 100))
(def ^:private THOUSAND (js/BigInt 1000))
(def ^:private ZERO (js/BigInt 0))
(defn split-tithe [gross-micros]
  (when (< gross-micros ZERO)
    (throw (js/RangeError. "[tithe] gross must be non-negative")))
  (let [tithe (/ (* gross-micros TITHE-PERMILLE) THOUSAND)]
    #js {:gross gross-micros :tithe tithe :net (- gross-micros tithe)}))
(defn parse-micros [s]
  (when (identical? false (.test #"^\d+$" s))         ;; === → native boolean, no truth_
    (throw (js/TypeError. (str "[tithe] micros must be a non-negative integer string, got \"" s "\""))))
  (js/BigInt s))
