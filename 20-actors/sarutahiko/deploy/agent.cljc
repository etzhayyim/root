;; sarutahiko 猿田彦 — kotoba-clj WASM Component entrypoint (ADR-2606230001, 2026-06-23)
;;
;; 9 Pregel cells assembled into ONE WASM Component.
;; safe-rewrites applied in THIS FILE ONLY (additive; bb-native state_machine.cljc untouched):
;;   Rewrite D: clojure.string/includes? / str/includes? → str-includes? (prelude, unqualified)
;;   Rewrite F/E: set literals #{"..."} → getter-defn returning vec; contains? → vec-contains?
;;
;; entrypoint: run: func(input: list<u8>) -> list<u8>
;; smoke output: "sarutahiko:9/9:cells-ok"

;; ── shared helpers (kotoba-clj kais prelude) ────────────────────────────────

(defn- djb2 [s]
  (let [len (str-len s)]
    (loop [i 0 h 5381]
      (if (= i len)
        h
        (recur (+ i 1) (+ (* h 33) (byte-at s i)))))))

(defn- int-to-hex8 [n]
  ;; B: manual hex-8, no str-slice (vec-make/bytes-alloc pattern from himawari)
  (let [digits (vec-make 8)
        m0 (bit-and n 4294967295)]
    (loop [m m0 i 0]
      (if (>= i 8) 0
        (do
          (vec-conj! digits (let [d (bit-and m 15)]
                               (if (< d 10) (+ 48 d) (+ 87 d))))
          (recur (bit-shift-right m 4) (+ i 1)))))
    (let [buf (bytes-alloc 8)]
      (loop [i 7]
        (if (< i 0)
          (bytes-finish buf)
          (do (byte-append! buf (vec-nth digits i)) (recur (- i 1))))))))

(defn- cid8 [prefix s]
  (str prefix (int-to-hex8 (djb2 s))))

;; ── cell-status helper ───────────────────────────────────────────────────────

(defn- cell-status [result]
  (cond
    (get result "error")   "error"
    (get result "refused") "refused"
    :else                  "ok"))

;; ── cell 1: frame_fabrication ────────────────────────────────────────────────

(defn- solve-frame-fabrication [ctx]
  (let [chassis-id (get ctx "chassisId" "SARUTAHIKO-CHASSIS-0001")
        robot-sigs [{"robotDid" "did:web:etzhayyim.com:kasane-unit-1" "role" "weld_lead"
                     "timestamp" "2026-05-26T08:00:00Z" "signature" "..."}
                    {"robotDid" "did:web:etzhayyim.com:mimi-precision-unit-1" "role" "metrology"
                     "timestamp" "2026-05-26T08:00:05Z" "signature" "..."}]
        result {"frame_state" {"phase" "attestation_emitted"
                               "chassisId" chassis-id
                               "completionPct" 100
                               "steelLot" {"grade" "HSLA-780" "lotId" "HSLA780-2026-05-LOT-0042"
                                           "certCid" "bafkreihsla..." "yieldStrengthMpa" 780
                                           "tensileStrengthMpa" 850}
                               "railPositions" [{"rail" "left_long" "lengthMm" 9500 "offsetMm" 0}
                                                {"rail" "right_long" "lengthMm" 9500 "offsetMm" 1100}]
                               "weldPasses" [{"crossMemberIdx" 0 "process" "MIG-multi-pass" "passes" 3}
                                             {"crossMemberIdx" 1 "process" "MIG-multi-pass" "passes" 3}
                                             {"crossMemberIdx" 2 "process" "MAG-multi-pass" "passes" 3}]
                               "straightnessMmPerM" 0.6
                               "robotSignatures" robot-sigs}
                "frame_attestation" {"$type" "com.etzhayyim.sarutahiko.frameAttestation"
                                     "chassisId" chassis-id
                                     "attestingRobots" robot-sigs
                                     "accept" true
                                     "recordedAt" "2026-05-26T08:00:10Z"}}]
    {"cell" "frame_fabrication" "status" (cell-status result) "result" result}))

;; ── cell 2: cab_body_forming ─────────────────────────────────────────────────

(defn- solve-cab-body-forming [ctx]
  (let [chassis-id (get ctx "chassisId" "SARUTAHIKO-CHASSIS-0001")
        result {"cab_state" {"phase" "attestation_emitted"
                             "chassisId" chassis-id
                             "completionPct" 100
                             "sheetLot" {"source" "external-commodity-R1"
                                         "lotId" "STEEL-SHEET-2026-05-0021"
                                         "thicknessMm" 0.8}
                             "stampedPanels" [{"panel" "roof" "stampingTempC" 900}
                                              {"panel" "left_side" "stampingTempC" 900}
                                              {"panel" "right_side" "stampingTempC" 900}
                                              {"panel" "rear" "stampingTempC" 900}
                                              {"panel" "floor" "stampingTempC" 900}]
                             "spotWelds" {"totalSpots" 2400 "robotPasses" 4}
                             "leakTestResult" {"method" "pressure-decay" "leakRatePaPerS" 1.2
                                               "limitPaPerS" 5.0 "accept" true}}
                "cab_body_attestation" {"$type" "com.etzhayyim.sarutahiko.cabBodyAttestation"
                                        "chassisId" chassis-id
                                        "recordedAt" "2026-05-26T11:00:00Z"}}]
    {"cell" "cab_body_forming" "status" (cell-status result) "result" result}))

;; ── cell 3: powertrain_assembly ──────────────────────────────────────────────
;; safe-rewrite F/E: #{"B100-biodiesel-hybrid" ...} set literal → getter-defn vec
;;                   contains? on set → vec-contains?

(defn- allowed-powertrain-r0r1 []
  ["B100-biodiesel-hybrid" "diesel-hybrid" "LFP-battery"
   "H2-fuel-cell" "NH3-fuel-cell" "methanol-fuel-cell"])

(defn- solve-powertrain-assembly [ctx]
  (let [chassis-id (get ctx "chassisId" "SARUTAHIKO-CHASSIS-0001")
        selected   (get ctx "powerTrainType" "B100-biodiesel-hybrid")
        ;; Rewrite E: contains? on set → vec-contains? on vec
        accept     (vec-contains? (allowed-powertrain-r0r1) selected)
        result {"powertrain_state" {"phase" "attestation_emitted"
                                    "chassisId" chassis-id
                                    "completionPct" 100
                                    "powerTrainType" selected
                                    "fuelGuard" {"g7Enforcement" "active"
                                                 "selected" selected
                                                 "accept" accept
                                                 "pureFossilGuard" "pure-fossil prohibited; B100 biodiesel + diesel hybrid acceptable as R0/R1 transition only"}
                                    "engineLot" {"type" selected "lotId" "ENGINE-2026-05-LOT-0011"
                                                 "powerKw" 350 "torqueNm" 2200}
                                    "transmissionLot" {"ratio_steps" 12 "lotId" "TRANS-2026-05-LOT-0011"}
                                    "axleLots" [{"position" "front_steer" "lotId" "AXLE-FRONT-0011"}
                                                {"position" "rear_drive_1" "lotId" "AXLE-REAR-0011"}
                                                {"position" "rear_drive_2" "lotId" "AXLE-REAR-0012"}]
                                    "brakeSystem" {"type" "EBS-disc" "regenerativeAllowed" true}}
                "powertrain_attestation" {"$type" "com.etzhayyim.sarutahiko.powertrainAttestation"
                                          "chassisId" chassis-id
                                          "powerTrainType" selected
                                          "recordedAt" "2026-05-26T09:30:00Z"}}]
    {"cell" "powertrain_assembly" "status" (cell-status result) "result" result}))

;; ── cell 4: paint_finishing ──────────────────────────────────────────────────

(defn- solve-paint-finishing [ctx]
  (let [chassis-id (get ctx "chassisId" "SARUTAHIKO-CHASSIS-0001")
        voc        92
        result {"paint_state" {"phase" "attestation_emitted"
                               "chassisId" chassis-id
                               "completionPct" 100
                               "pretreatmentResult" {"degreased" true "phosphatedNm" 1.2 "rinseRounds" 3}
                               "layers" [{"layer" "ktl-primer" "thicknessUm" 22}
                                         {"layer" "base-coat" "thicknessUm" 18 "color" "OEM-default-grey"}
                                         {"layer" "clear-coat" "thicknessUm" 40}]
                               "vocGPerL" voc
                               "cureRecord" {"tempC" 140 "durationMinutes" 30
                                             "tunnelType" "IR + convection"}}
                "paint_attestation" {"$type" "com.etzhayyim.sarutahiko.paintAttestation"
                                     "chassisId" chassis-id
                                     "vocGPerL" voc
                                     "vocLimitGPerL" 100
                                     "g8Accept" (< voc 100)
                                     "recordedAt" "2026-05-26T15:00:00Z"}}]
    {"cell" "paint_finishing" "status" (cell-status result) "result" result}))

;; ── cell 5: electrical_integration ──────────────────────────────────────────
;; safe-rewrite D: (:require [clojure.string :as str]) + str/includes? → str-includes? (prelude)

(defn- solve-electrical-integration [ctx]
  (let [chassis-id  (get ctx "chassisId" "SARUTAHIKO-CHASSIS-0001")
        fw-license  "Apache 2.0 + Charter Compliance Rider v2.0"
        ;; Rewrite D: str-includes? replaces str/includes? (was (:require [clojure.string :as str]))
        has-apache  (str-includes? fw-license "Apache 2.0")
        has-rider   (str-includes? fw-license "Charter Compliance Rider")
        result {"electrical_state" {"phase" "attestation_emitted"
                                    "chassisId" chassis-id
                                    "completionPct" 100
                                    "harnessLayout" {"totalWireMassKg" 28 "branchCount" 14
                                                     "routingCid" "bafkreiroute..." "akariUnits" 2}
                                    "ecuFlash" {"ecuModel" "etzhayyim-open-ecu-v1"
                                                "firmwareCid" "bafkreiopenecuFW..."
                                                "firmwareLicense" fw-license
                                                "flashTimestamp" "2026-05-26T16:30:00Z"}
                                    "openSourceVerification" {"g1Enforcement" "active"
                                                              "n8Enforcement" "active"
                                                              "firmwareLicense" fw-license
                                                              "containsApache2" has-apache
                                                              "containsCharterRider" has-rider
                                                              "proprietaryNdaPresent" false
                                                              "accept" (and has-apache has-rider)}
                                    "diagnostics" {"obdIIScan" "PASS" "canBusIntegrity" "PASS"
                                                   "wakeUpSleepCycle" "PASS" "shortCircuitCheck" "PASS"
                                                   "groundResistanceOhms" 0.04}}
                "electrical_attestation" {"$type" "com.etzhayyim.sarutahiko.electricalAttestation"
                                          "chassisId" chassis-id
                                          "recordedAt" "2026-05-26T17:00:00Z"}}]
    {"cell" "electrical_integration" "status" (cell-status result) "result" result}))

;; ── cell 6: final_marriage ───────────────────────────────────────────────────

(defn- solve-final-marriage [ctx]
  (let [chassis-id (get ctx "chassisId" "SARUTAHIKO-CHASSIS-0001")
        robot-sigs [{"robotDid" "did:web:etzhayyim.com:otete-heavy-unit-1" "role" "marriage_lead"
                     "timestamp" "2026-05-26T13:00:00Z" "signature" "..."}
                    {"robotDid" "did:web:etzhayyim.com:mimi-precision-unit-1" "role" "alignment_witness"
                     "timestamp" "2026-05-26T13:00:05Z" "signature" "..."}]
        result {"marriage_state" {"phase" "attestation_emitted"
                                  "chassisId" chassis-id
                                  "completionPct" 100
                                  "inputs" {"frameAttestationCid" "bafkreiframeatt..."
                                            "powertrainAttestationCid" "bafkreiptatt..."
                                            "cabBodyAttestationCid" "bafkreicabatt..."}
                                  "criticalTorques" [{"fastener" "cab_mount_1" "torqueNm" 320 "specNm" 320}
                                                     {"fastener" "cab_mount_2" "torqueNm" 315 "specNm" 320}
                                                     {"fastener" "engine_mount_left" "torqueNm" 450 "specNm" 450}
                                                     {"fastener" "transmission_mount" "torqueNm" 280 "specNm" 280}]
                                  "robotSignatures" robot-sigs}
                "marriage_attestation" {"$type" "com.etzhayyim.sarutahiko.marriageAttestation"
                                        "chassisId" chassis-id
                                        "attestingRobots" robot-sigs
                                        "recordedAt" "2026-05-26T13:00:10Z"}}]
    {"cell" "final_marriage" "status" (cell-status result) "result" result}))

;; ── cell 7: quality_road_test ─────────────────────────────────────────────────

(defn- solve-quality-road-test [ctx]
  (let [chassis-id (get ctx "chassisId" "SARUTAHIKO-CHASSIS-0001")
        result {"road_test_state" {"phase" "record_emitted"
                                   "chassisId" chassis-id
                                   "completionPct" 100
                                   "dynoResult" {"maxWheelPowerKw" 320 "maxWheelTorqueNm" 2100
                                                 "fuelConsumption_l_per_100km" 22.5
                                                 "brakeStoppingDistanceM" 38}
                                   "g12KpiCheck" {"maxSpeedKmh" 85 "maxSpeedLimitKmh" 90
                                                 "autonomyLevel" "L0-manual-R1" "autonomyMaxLevel" 4
                                                 "rangeKm" 850 "rangeMinKm" 800
                                                 "gvwrT" 36 "gvwrMaxT" 40 "accept" true}
                                   "publicRoadResult" {"routeDistanceKm" 50 "averageSpeedKmh" 65
                                                       "incidents" []
                                                       "videoCid" "bafkreiroadtest..."}
                                   "norimichiAttestation" {"norimichiDid" "did:web:etzhayyim.com:norimichi-unit-1"
                                                           "saeLevel" 3 "saeMaxLevel" 4
                                                           "timestamp" "2026-05-26T18:30:00Z"}}
                "road_test_record" {"$type" "com.etzhayyim.sarutahiko.roadTestRecord"
                                    "chassisId" chassis-id
                                    "overallAccept" true
                                    "recordedAt" "2026-05-26T18:35:00Z"}}]
    {"cell" "quality_road_test" "status" (cell-status result) "result" result}))

;; ── cell 8: vin_attestation_binder ───────────────────────────────────────────

(defn- solve-vin-attestation-binder [ctx]
  (let [chassis-id   (get ctx "chassisId" "SARUTAHIKO-CHASSIS-0001")
        vin          "ETZSARUTAHIKO00000A0001"
        vehicle-did  (str "did:web:etzhayyim.com:sarutahiko:vehicle:" vin)
        result {"binder_state" {"phase" "record_emitted"
                                "chassisId" chassis-id
                                "completionPct" 100
                                "vin" vin
                                "vehicleDid" vehicle-did
                                "upstreamRecords" {"frameAttestation" "bafkreiframe..."
                                                   "powertrainAttestation" "bafkreipt..."
                                                   "cabBodyAttestation" "bafkreicab..."
                                                   "marriageAttestation" "bafkreimarry..."
                                                   "paintAttestation" "bafkreipaint..."
                                                   "electricalAttestation" "bafkreielec..."
                                                   "roadTestRecord" "bafkreiroad..."
                                                   "emissionsAuditRecord" "bafkreiemis..."}
                                "kotoba_datomicAnchor" {"g2Compliant" true
                                                        "openVinRegistry" true
                                                        "l2Chain" "Base Sepolia (R0 dry-run)"}}
                "vehicle_manufacture_record" {"$type" "etzhayyim:sarutahiko:vehicleManufactureRecord"
                                              "chassisId" chassis-id
                                              "vin" vin
                                              "vehicleDid" vehicle-did
                                              "recordedAt" "2026-05-26T20:00:00Z"}}]
    {"cell" "vin_attestation_binder" "status" (cell-status result) "result" result}))

;; ── cell 9: emissions_audit ──────────────────────────────────────────────────

(defn- solve-emissions-audit [ctx]
  (let [chassis-id (get ctx "chassisId" "SARUTAHIKO-CHASSIS-0001")
        euro7-ok   true
        japan-ok   true
        bharat-ok  true
        overall    (and euro7-ok japan-ok bharat-ok)
        result {"emissions_state" {"phase" "record_emitted"
                                   "chassisId" chassis-id
                                   "completionPct" 100
                                   "euro7Findings" {"nox_mg_per_km" 90 "nox_limit_mg_per_km" 200
                                                    "particulate_mg_per_km" 4.5 "particulate_limit_mg_per_km" 10
                                                    "co_mg_per_km" 750 "co_limit_mg_per_km" 1500 "accept" euro7-ok}
                                   "japanPostNLTFindings" {"nox_g_per_kWh" 0.30 "nox_limit_g_per_kWh" 0.40
                                                           "particulate_g_per_kWh" 0.008
                                                           "particulate_limit_g_per_kWh" 0.010
                                                           "accept" japan-ok}
                                   "bharatViFindings" {"nox_g_per_kWh" 0.42 "nox_limit_g_per_kWh" 0.46
                                                       "particulate_g_per_kWh" 0.009
                                                       "particulate_limit_g_per_kWh" 0.010
                                                       "accept" bharat-ok}
                                   "overallAccept" overall}
                "emissions_audit_record" {"$type" "com.etzhayyim.sarutahiko.emissionsAuditRecord"
                                          "chassisId" chassis-id
                                          "overallAccept" overall
                                          "recordedAt" "2026-05-26T19:00:00Z"}}]
    {"cell" "emissions_audit" "status" (cell-status result) "result" result}))

;; ── manufacture chain runner ─────────────────────────────────────────────────
;; NO HOF dispatch — direct calls only (kotoba-clj kais does not support
;; program-defined HOFs at WASM component-model tier)

(defn- manufacture [ctx]
  (let [t1 (solve-frame-fabrication ctx)
        t2 (solve-cab-body-forming ctx)
        t3 (solve-powertrain-assembly ctx)
        t4 (solve-paint-finishing ctx)
        t5 (solve-electrical-integration ctx)
        t6 (solve-final-marriage ctx)
        t7 (solve-quality-road-test ctx)
        t8 (solve-vin-attestation-binder ctx)
        t9 (solve-emissions-audit ctx)]
    [t1 t2 t3 t4 t5 t6 t7 t8 t9]))

;; ── WASM Component entrypoint ────────────────────────────────────────────────

(defn run [input]
  (let [ctx      {"chassisId" "SARUTAHIKO-CHASSIS-0001"
                  "powerTrainType" "B100-biodiesel-hybrid"}
        trace    (manufacture ctx)
        ok-count (count (filter (fn [t] (= "ok" (get t "status"))) trace))
        total    (count trace)]
    (str "sarutahiko:" (str-int ok-count) "/" (str-int total) ":cells-ok")))
