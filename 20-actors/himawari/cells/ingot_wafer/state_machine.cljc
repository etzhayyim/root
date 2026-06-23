(ns himawari.cells.ingot-wafer.state-machine
  "1:1 port of cells/ingot_wafer/cell.py — ingot growth + wafer slicing (ADR-2606021200).

  Ingot growth + wafer slicing + kerf-Si recovery. Enforces G5 (kerf circularity ≥90%)
  and G4 (renewable-only process energy) structurally. A batch failing either gate is
  returned accepted=False and is NOT transacted to kotoba. Recovered kerf-Si routes
  back to polysilicon_refine as recycled-kerf feedstock (closing the G5 loop).

  Pure-logic cell with no LangGraph/robot composition required."
  (:require [clojure.string :as str]))

;; G5: kerf-Si recovery must close the loop to ≥90% circular (basis points).
(def ^:private KERF_RECOVERY_MIN_BPS 9000)

;; G4: renewable-only process energy.
(defn- renewable-sources []
  ["hikari-solar" "hikari-wind" "hikari-hydro" "hikari-storage"])

;; Known ingot methods (mirrors lexicon).
(defn- ingot-methods []
  ["czochralski-monocrystalline" "directional-cast-multicrystalline"])

;; Kerf-loss fraction by saw technology (in hundredths: 40 = 40%).
;; Integer representation: 40 means 40/100 = 0.40 kerf fraction.
(defn- kerf-fraction []
  {"diamond-wire" 40
   "slurry-wire" 55})

;; SI density in mg/cm³ (2329 = 2.329 g/cm³)
(def ^:private SI_DENSITY_MG_PER_CM3 2329)

(defn- kerf-recovery-bps
  "Recovered kerf as a fraction of generated kerf, in basis points (0-10000)."
  [kerf-generated-g kerf-recovered-g]
  (if (<= kerf-generated-g 0)
    10000  ;; no kerf generated ⇒ trivially circular
    (min 10000 (quot (* (int kerf-recovered-g) 10000) (int kerf-generated-g)))))

(defn- energy-is-renewable
  "True iff every declared process-energy source is hikari-renewable (G4)."
  [sources]
  (and (not (empty? sources))
       (every? (fn [s] (some #(= % s) (renewable-sources))) sources)))

(defn- wafer-mass-g
  "Per-wafer silicon mass in grams (integer approx; π ≈ 355/113).
  mass_g = π*(d_mm/20)²_cm² * (t_μm/10000)_cm * ρ_g/cm³
         = 355*d²*t*SI_DENSITY_MG_PER_CM3 / (113*400*10000*1000)"
  [thickness-um diameter-mm]
  (let [d (max 1 (int diameter-mm))
        t (max 1 (int thickness-um))
        numerator (* (* 355 d d) (* t SI_DENSITY_MG_PER_CM3))
        denominator (* (* 113 4) 1000000000)]
    (quot numerator denominator)))

(defn- robot-signature
  "Normalize one attesting robot into a lexicon #robotSignature object."
  [robot]
  (if (map? robot)
    (let [did (str (or (get robot "robotDid") (get robot "did") ""))
          sig (or (get robot "signature") (str "ed25519:" did ":wafer-batch-sig"))]
      (cond-> {"robotDid" did "signature" sig}
        (get robot "role") (assoc "role" (str (get robot "role")))
        (get robot "timestamp") (assoc "timestamp" (str (get robot "timestamp")))))
    (let [did (str robot)]
      {"robotDid" did
       "role" "mass_balance_witness"
       "signature" (str "ed25519:" did ":wafer-batch-sig")})))

(defn solve
  "Grow ingot → wire-saw wafer → recover kerf-Si → emit waferBatchRecord.

  Required input keys: batchId, polysiliconLotId, ingotMethod, waferCount,
  attestingRobots (≥2).
  Optional keys (with safe defaults): waferThicknessUm (150), waferDiameterMm (210),
  sliceMethod ('diamond-wire'), kerfRecoveredGrams (auto: 90%), yieldBps (9800),
  processEnergyWh (0), energySources (['hikari-solar']), recordedAt (''),
  attestingEngineerDid (''), transact (true).

  Returns state augmented with waferBatchRecord, accepted bool, and (when rejected)
  reason. Only accepted batches should be transacted."
  [state]
  (let [batch-id (str (get state "batchId" ""))
        lot-id (str (get state "polysiliconLotId" ""))
        method (str (get state "ingotMethod" ""))
        wafer-count (int (get state "waferCount" 0))
        robots (into [] (get state "attestingRobots" []))

        ;; Validation (raises on contract violation)
        _ (when (str/blank? batch-id) (throw (ex-info "ingot_wafer: batchId is required"
                                                      {:type ::invalid-input})))
        _ (when (str/blank? lot-id) (throw (ex-info "ingot_wafer: polysiliconLotId is required"
                                                    {:type ::invalid-input})))
        _ (when-not (some #(= % method) (ingot-methods))
            (throw (ex-info "ingot_wafer: ingotMethod not a known solar ingot method"
                            {:type ::invalid-input :method method})))
        _ (when (<= wafer-count 0)
            (throw (ex-info "ingot_wafer: waferCount must be > 0"
                            {:type ::invalid-input})))
        _ (when (< (count robots) 2)
            (throw (ex-info "ingot_wafer: ≥2 attesting robots required"
                            {:type ::invalid-input})))

        thickness-um (int (get state "waferThicknessUm" 150))
        diameter-mm (int (get state "waferDiameterMm" 210))
        slice-method (or (get state "sliceMethod") (get state "sawTech") "diamond-wire")
        ;; kerf-fraction-pct: integer percentage (40 = 40% kerf loss, 55 = 55%)
        kerf-fraction-pct (get (kerf-fraction) slice-method 40)

        ;; Process model: per-wafer mass + total kerf generated
        ;; kerf = wafered_si * (kf / (100 - kf))
        wafer-g (wafer-mass-g thickness-um diameter-mm)
        wafered-si-g (* wafer-g wafer-count)
        kerf-generated-g (quot (* wafered-si-g kerf-fraction-pct) (- 100 kerf-fraction-pct))

        ;; Kerf recovered: caller may report measured; otherwise model 90% of generated
        kerf-recovered-g (if (contains? state "kerfRecoveredGrams")
                           (int (get state "kerfRecoveredGrams"))
                           (quot (* kerf-generated-g 90) 100))

        recovery-bps (kerf-recovery-bps kerf-generated-g kerf-recovered-g)

        ;; Yield: good wafers / throughput (modelled default ~98%)
        yield-bps (int (get state "yieldBps" 9800))

        ;; G5 gate: kerf circularity ≥90%
        kerf-ok (>= recovery-bps KERF_RECOVERY_MIN_BPS)

        ;; G4 gate: renewable-only process energy
        energy-sources (into [] (get state "energySources" ["hikari-solar"]))
        process-energy-wh (int (get state "processEnergyWh" 0))
        renewable (energy-is-renewable energy-sources)
        energy-ok (or (zero? process-energy-wh) renewable)
        renewable-bps (if energy-ok 10000 0)

        ;; Build waferBatchRecord
        record {"$type" "com.etzhayyim.himawari.waferBatchRecord"
                "batchId" batch-id
                "polysiliconLotId" lot-id
                "ingotMethod" method
                "sliceMethod" slice-method
                "waferCount" wafer-count
                "attestingRobots" (mapv (fn [r] (robot-signature r)) robots)
                "waferThicknessUm" thickness-um
                "kerfRecoveredGrams" kerf-recovered-g
                "kerfRecoveryFractionBps" recovery-bps
                "yieldBps" yield-bps
                "processEnergyWh" process-energy-wh
                "renewableEnergyFractionBps" renewable-bps
                "recordedAt" (str (get state "recordedAt" ""))
                "attestingEngineerDid" (str (get state "attestingEngineerDid" ""))}

        accepted (and kerf-ok energy-ok)
        reason (cond
                 (not kerf-ok) (str "G5 violation: kerf-Si recovery " recovery-bps
                                    " bps < " KERF_RECOVERY_MIN_BPS " bps (≥90% circular required)")
                 (not energy-ok) (str "G4 violation: process energy sources " energy-sources
                                      " include non-hikari-renewable (fossil/nuclear) — forbidden"))

        result (cond-> (merge state
                               {"accepted" accepted
                                "waferBatchRecord" record
                                "kerfGeneratedGrams" kerf-generated-g
                                "kerfRecoveryBps" recovery-bps
                                "recycledKerfFeedstockGrams" kerf-recovered-g
                                "transacted" false})
                 reason (assoc "reason" reason)
                 (not reason) (dissoc "reason"))]
    result))
