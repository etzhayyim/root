(ns etzhayyim.tithe
  "Constitutional 10% Public-Fund split (ADR-2605192100 / ADR-2605192115 TitheRouter).

  The canonical, single-source tithe math — replacing the near-duplicated
  `60-apps/{ec,real-estate,shopping}/kotoba/src/tithe.ts` (identical logic, only
  the error-prefix differed). Portable .cljc: runs on **bb/clj (JVM bigint)** for
  the actor/router side and compiles under **squint (native JS BigInt)** for the
  app/edge side (ADR-2606251200 squint PoC, 90-docs/poc/2606251200-squint-tithe).

  USDC base units (micros) as arbitrary-precision integers; the tithe is
  integer-floored — no rounding leak (a constitutional invariant: 7 micros tithe
  to 0, never 0.7).")

(def tithe-permille
  "10% expressed in per-mille (÷1000)."
  #?(:clj 100N :cljs (js/BigInt 100)))

(def ^:private thousand #?(:clj 1000N :cljs (js/BigInt 1000)))
(def ^:private zero     #?(:clj 0N    :cljs (js/BigInt 0)))

(defn- idiv
  "Integer (floor toward zero) division. clj `/` on bigints yields a Ratio, so
  use `quot`; squint/JS `/` on BigInt is already integer division."
  [a b]
  #?(:clj (quot a b) :cljs (/ a b)))

(defn split-tithe
  "Split `gross-micros` (a non-negative bigint) into {:gross :tithe :net}, where
  tithe = floor(gross · 100 / 1000) and net = gross − tithe. Throws on negative."
  [gross-micros]
  (when (< gross-micros zero)
    (throw (ex-info "[tithe] gross must be non-negative" {:gross gross-micros})))
  (let [tithe (idiv (* gross-micros tithe-permille) thousand)]
    {:gross gross-micros :tithe tithe :net (- gross-micros tithe)}))

(defn parse-micros
  "Parse a non-negative integer string into a bigint. Throws on any other input."
  [s]
  (when-not (re-matches #"^\d+$" s)
    (throw (ex-info (str "[tithe] micros must be a non-negative integer string, got \"" s "\"")
                    {:s s})))
  #?(:clj (bigint s) :cljs (js/BigInt s)))

;; ── order math (consolidates the pure core of 60-apps/*/kotoba/src/order.ts) ──

(defn- ->big [n] #?(:clj (bigint n) :cljs (js/BigInt n)))

(defn order-total-micros
  "Σ over order `lines` of parse-micros(unit-price) · qty. Each line is
  {:unit-price-micros <digit-string> :qty <int>}. Returns a bigint.
  Mirrors orderTotalMicros() in order.ts (used by ec/shopping/omise/okaimono…)."
  [lines]
  (reduce (fn [acc {:keys [unit-price-micros qty]}]
            (+ acc (* (parse-micros unit-price-micros) (->big qty))))
          zero
          lines))

(defn order-tithe
  "Order `lines` → {:gross :tithe :net}: the order total run through the
  constitutional 10% split. The pure heart of an order's settlement record."
  [lines]
  (split-tithe (order-total-micros lines)))
