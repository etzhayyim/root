;; yamabiko 山彦 — kotoba-clj WASM Component entrypoint (ADR-2606230001, 2026-06-23)
;;
;; 9 Pregel cells assembled into ONE WASM Component.
;; safe-rewrite applied in THIS FILE ONLY (additive; bb-native state_machine.cljc untouched):
;;   Rewrite D: clojure.string/includes? (unqualified inline) → str-includes? (prelude, unqualified)
;;   Rewrite F/E: set literals #{"..."} → getter-defn returning vec; contains? → vec-contains?
;;
;; entrypoint: run: func(input: list<u8>) -> list<u8>
;; smoke output: "yamabiko:9/9:cells-ok"

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

;; ── cell 1: carbody_fabrication ─────────────────────────────────────────────

(defn- solve-carbody-fabrication [ctx]
  (let [trainset-id (get ctx "trainsetId" "YAMABIKO-TRAINSET-0001")
        robot-sigs [{"robotDid" "did:web:etzhayyim.com:tsugite-unit-1" "role" "fsw_lead"
                     "timestamp" "2026-05-26T08:00:00Z" "signature" "..."}
                    {"robotDid" "did:web:etzhayyim.com:mimi-precision-unit-1" "role" "metrology"
                     "timestamp" "2026-05-26T08:00:05Z" "signature" "..."}]
        result {"carbody_state" {"phase" "attestation_emitted"
                                 "trainsetId" trainset-id
                                 "carIndex" 0
                                 "completionPct" 100
                                 "extrusionLot" {"alloy" "Al-6N01" "lotId" "AL6N01-2026-05-LOT-0042"
                                                 "doubleSkin" true "thicknessMm" 2.5
                                                 "certCid" "bafkreialextrude..."}
                                 "fswSeams" [{"seam" "side-floor" "lengthM" 24.5 "tool_rpm" 800}
                                             {"seam" "side-roof"  "lengthM" 24.5 "tool_rpm" 800}
                                             {"seam" "end-front"  "lengthM" 3.2  "tool_rpm" 750}
                                             {"seam" "end-rear"   "lengthM" 3.2  "tool_rpm" 750}]
                                 "spotWelds" {"totalSpots" 1800 "robotPasses" 3
                                              "videoCid" "bafkreispot..."}
                                 "dimensionalQa" {"lengthMm" 25000 "widthMm" 3380
                                                  "heightMm" 3650 "accept" true}
                                 "robotSignatures" robot-sigs}
                "carbody_attestation" {"$type" "com.etzhayyim.yamabiko.carbodyAttestation"
                                       "trainsetId" trainset-id
                                       "carIndex" 0
                                       "attestingRobots" robot-sigs
                                       "recordedAt" "2026-05-26T08:00:10Z"}}]
    {"cell" "carbody_fabrication" "status" (cell-status result) "result" result}))

;; ── cell 2: bogie_assembly ──────────────────────────────────────────────────

(defn- solve-bogie-assembly [ctx]
  (let [trainset-id (get ctx "trainsetId" "YAMABIKO-TRAINSET-0001")
        robot-sigs [{"robotDid" "did:web:etzhayyim.com:wadasa-unit-1" "role" "bogie_lead"
                     "timestamp" "2026-05-26T10:00:00Z" "signature" "..."}
                    {"robotDid" "did:web:etzhayyim.com:mimi-precision-unit-1" "role" "alignment"
                     "timestamp" "2026-05-26T10:00:05Z" "signature" "..."}]
        result {"bogie_state" {"phase" "attestation_emitted"
                               "trainsetId" trainset-id
                               "bogieIndex" 0
                               "completionPct" 100
                               "frameLot" {"source" "external-cast-steel-R1"
                                           "note" "R3+ from igata Wave 2"
                                           "lotId" "BOGIE-FRAME-0011"}
                               "wheelSetLot" {"lotId" "WHEELSET-0011"
                                              "wheelDiameterMm" 860 "axleLoadT" 17}
                               "motorLot" {"type" "PMSM" "powerKw" 305
                                           "ratedVoltageV" 1100 "lotId" "TRACTION-MOTOR-0011"}
                               "brakeSystem" {"type" "tread-disc-hybrid"
                                              "regenerativeAllowed" true "emergencyDecelMsps" 1.3}
                               "airSpring" {"primary" "coil" "secondary" "air-bellows"
                                            "levelingControl" true}
                               "robotSignatures" robot-sigs}
                "bogie_attestation" {"$type" "com.etzhayyim.yamabiko.bogieAttestation"
                                     "trainsetId" trainset-id
                                     "bogieIndex" 0
                                     "attestingRobots" robot-sigs
                                     "recordedAt" "2026-05-26T10:00:10Z"}}]
    {"cell" "bogie_assembly" "status" (cell-status result) "result" result}))

;; ── cell 3: traction_electrical ─────────────────────────────────────────────
;; safe-rewrite D: clojure.string/includes? (bare inline) → str-includes? (prelude)
;; safe-rewrite F/E: #{"..."} set literal → vec (getter-defn style); contains? → vec-contains?

(defn- allowed-r0r1-propulsion []
  ["overhead-25kV-AC" "overhead-1500V-DC" "third-rail-750V-DC"
   "BEMU-LFP" "H2-fuel-cell-hybrid"])

(defn- solve-traction-electrical [ctx]
  (let [trainset-id  (get ctx "trainsetId" "YAMABIKO-TRAINSET-0001")
        selected     (get ctx "propulsionType" "overhead-25kV-AC")
        ;; Rewrite E: contains? on set → vec-contains? on vec
        accept       (vec-contains? (allowed-r0r1-propulsion) selected)
        ;; Rewrite D: str-includes? replaces bare clojure.string/includes?
        fw-license   "Apache 2.0 + Charter Compliance Rider v2.0"
        has-apache   (str-includes? fw-license "Apache 2.0")
        has-rider    (str-includes? fw-license "Charter Compliance Rider")
        result {"traction_state" {"phase" "attestation_emitted"
                                  "trainsetId" trainset-id
                                  "completionPct" 100
                                  "propulsionType" selected
                                  "propulsionGuard" {"g7Enforcement" "active"
                                                     "selected" selected
                                                     "accept" accept
                                                     "dieselGuard" "R2+ diesel prohibited (N4)"}
                                  "pantograph" {"count" 2 "type" "wing" "ratedVoltageV" 25000
                                                "currentA" 1000}
                                  "inverter" {"type" "SiC-MOSFET" "ratedPowerKw" 4880
                                              "efficiencyPct" 98.2}
                                  "atpAtoFirmware" {"atpStandard" "ETCS-Level-2"
                                                    "atoLevel" "GoA-3" "atoMaxLevel" 3
                                                    "firmwareLicense" fw-license
                                                    "flashTimestamp" "2026-05-26T14:00:00Z"}
                                  "openSourceVerification" {"g1Enforcement" "active"
                                                            "n5Enforcement" "active"
                                                            "firmwareLicense" fw-license
                                                            "containsApache2" has-apache
                                                            "containsCharterRider" has-rider
                                                            "proprietaryNdaPresent" false
                                                            "accept" (and has-apache has-rider)}}
                "traction_electrical_attestation" {"$type" "com.etzhayyim.yamabiko.tractionElectricalAttestation"
                                                   "trainsetId" trainset-id
                                                   "propulsionType" selected
                                                   "recordedAt" "2026-05-26T14:00:10Z"}}]
    {"cell" "traction_electrical" "status" (cell-status result) "result" result}))

;; ── cell 4: interior_hvac ───────────────────────────────────────────────────

(defn- solve-interior-hvac [ctx]
  (let [trainset-id (get ctx "trainsetId" "YAMABIKO-TRAINSET-0001")
        result {"interior_state" {"phase" "attestation_emitted"
                                  "trainsetId" trainset-id
                                  "carIndex" 0
                                  "completionPct" 100
                                  "floor" {"material" "Al-honeycomb-with-vinyl"
                                           "thicknessMm" 35
                                           "fireClass" "EN 45545 R1 HL2"}
                                  "seating" {"type" "fire-retardant-fabric-EN 45545 R1"
                                             "pitch_mm" 990 "rowCount" 17
                                             "wheelchairBays" 2}
                                  "accessibility" {"wheelchairAccessibleToiletM2" 2.4
                                                   "rampsCount" 2
                                                   "tactileMarkingPath" "full"
                                                   "vacuumWasteSystem" true}
                                  "hvac" {"type" "heat-pump" "hepaFilter" "H13"
                                          "freshAirM3PerHourPerPax" 30
                                          "co2SensorActive" true}
                                  "pisConfig" {"languages" ["ja" "en" "local"]
                                               "g5Trilingual" true
                                               "contentTypes" ["route-info" "safety-info"
                                                               "next-station" "emergency"]
                                               "n6AdvertisingPresent" false
                                               "n8FaceRecognitionPresent" false
                                               "accept" true}}
                "interior_attestation" {"$type" "com.etzhayyim.yamabiko.interiorAttestation"
                                        "trainsetId" trainset-id
                                        "carIndex" 0
                                        "recordedAt" "2026-05-26T12:00:00Z"}}]
    {"cell" "interior_hvac" "status" (cell-status result) "result" result}))

;; ── cell 5: final_assembly ──────────────────────────────────────────────────

(defn- solve-final-assembly [ctx]
  (let [trainset-id (get ctx "trainsetId" "YAMABIKO-TRAINSET-0001")
        robot-sigs [{"robotDid" "did:web:etzhayyim.com:otete-heavy-unit-1" "role" "marriage_lead"
                     "timestamp" "2026-05-26T16:00:00Z" "signature" "..."}
                    {"robotDid" "did:web:etzhayyim.com:mimi-precision-unit-1" "role" "alignment"
                     "timestamp" "2026-05-26T16:00:05Z" "signature" "..."}]
        result {"final_state" {"phase" "attestation_emitted"
                               "trainsetId" trainset-id
                               "completionPct" 100
                               "inputs" {"carbodyCids" ["bafkreicar1..." "bafkreicar2..."
                                                        "bafkreicar3..." "bafkreicar4..."]
                                         "bogieCids" ["bafkreibog1..." "bafkreibog2..."
                                                      "bafkreibog3..." "bafkreibog4..."]
                                         "interiorCids" ["bafkreiint1..." "bafkreiint2..."]
                                         "tractionCid" "bafkreitr..."}
                               "marriage" {"carCount" 4 "bogiesPerCar" 2
                                           "marriageFastenerTorqueNm" 850
                                           "marriageFastenerSpecNm" 850}
                               "livery" {"scheme" "OEM-default-white-with-route-band"
                                         "n6AdvertisingFreeAccept" true
                                         "vocGPerL" 88}
                               "robotSignatures" robot-sigs}
                "final_assembly_attestation" {"$type" "com.etzhayyim.yamabiko.finalAssemblyAttestation"
                                              "trainsetId" trainset-id
                                              "attestingRobots" robot-sigs
                                              "recordedAt" "2026-05-26T16:00:10Z"}}]
    {"cell" "final_assembly" "status" (cell-status result) "result" result}))

;; ── cell 6: dynamic_test ────────────────────────────────────────────────────

(defn- solve-dynamic-test [ctx]
  (let [trainset-id (get ctx "trainsetId" "YAMABIKO-TRAINSET-0001")
        result {"dynamic_state" {"phase" "record_emitted"
                                 "trainsetId" trainset-id
                                 "completionPct" 100
                                 "staticTestResult" {"weightDistribution" "PASS"
                                                     "pneumaticPressure" "PASS"
                                                     "doorOperation" "PASS"
                                                     "emergencyBrake" "PASS"
                                                     "hvacCalibration" "PASS"}
                                 "g12KpiCheck" {"designSpeedKmh" 320
                                               "maxSpeedLimitKmh" 320
                                               "trainsetLengthM" 100
                                               "maxTrainsetLengthM" 450
                                               "atoLevel" "GoA-3"
                                               "atoMaxLevel" 3
                                               "accept" true}
                                 "dynamicRunResult" {"testTrackLengthKm" 105
                                                     "totalDistanceKm" 1240
                                                     "maxAchievedSpeedKmh" 318
                                                     "rideQualityRMSM" 0.18
                                                     "videoCid" "bafkreidyntest..."}}
                "dynamic_test_record" {"$type" "com.etzhayyim.yamabiko.dynamicTestRecord"
                                       "trainsetId" trainset-id
                                       "overallAccept" true
                                       "recordedAt" "2026-05-27T10:00:00Z"}}]
    {"cell" "dynamic_test" "status" (cell-status result) "result" result}))

;; ── cell 7: emissions_acoustic_audit ────────────────────────────────────────

(defn- solve-emissions-acoustic-audit [ctx]
  (let [trainset-id (get ctx "trainsetId" "YAMABIKO-TRAINSET-0001")
        result {"acoustic_state" {"phase" "record_emitted"
                                  "trainsetId" trainset-id
                                  "completionPct" 100
                                  "waysideNoise" {"standard" "ISO 3095"
                                                  "dbAAt25mAtSpeed_300kmh" 88
                                                  "limit_dbA" 95
                                                  "dbAStandstill" 68
                                                  "limitStandstill_dbA" 70
                                                  "accept" true}
                                  "vibration" {"standard" "日本 騒音規制法"
                                               "dbVibrationAtTrackside" 58
                                               "limit_dbVibration" 60
                                               "accept" true}
                                  "emcResult" {"standard" "IEC 62236"
                                               "emissionPass" true
                                               "immunityPass" true
                                               "accept" true}
                                  "overallAccept" true}
                "acoustic_emissions_audit_record" {"$type" "com.etzhayyim.yamabiko.acousticEmissionsAuditRecord"
                                                   "trainsetId" trainset-id
                                                   "overallAccept" true
                                                   "recordedAt" "2026-05-27T15:00:00Z"}}]
    {"cell" "emissions_acoustic_audit" "status" (cell-status result) "result" result}))

;; ── cell 8: homologation_binder ─────────────────────────────────────────────

(defn- solve-homologation-binder [ctx]
  (let [trainset-id  (get ctx "trainsetId" "YAMABIKO-TRAINSET-0001")
        serial       "ETZYAMABIKO-2026-05-0001"
        trainset-did (str "did:web:etzhayyim.com:yamabiko:trainset:" serial)
        result {"homologation_state" {"phase" "record_emitted"
                                      "trainsetId" trainset-id
                                      "completionPct" 100
                                      "serial" serial
                                      "trainsetDid" trainset-did
                                      "upstreamRecords" {"carbodyAttestations" "bafkreicarbodybundle..."
                                                         "bogieAttestations" "bafkreibogibundle..."
                                                         "interiorAttestations" "bafkreiintbundle..."
                                                         "tractionElectricalAttestation" "bafkreitr..."
                                                         "finalAssemblyAttestation" "bafkreifinal..."
                                                         "dynamicTestRecord" "bafkreidyn..."
                                                         "acousticEmissionsAuditRecord" "bafkreiac..."}
                                      "authorityReview" {"ramsStandards" ["EN 50126" "EN 50128" "EN 50129"]
                                                         "jurisdiction" "JP"
                                                         "homologationRegime" "日本 鉄道事業法"
                                                         "decision" "ISSUE_TYPE_APPROVAL"
                                                         "timestamp" "2026-05-27T13:00:00Z"}
                                      "kotoba_datomicAnchor" {"g2Compliant" true
                                                              "openTrainsetRegistry" true
                                                              "l2Chain" "Base Sepolia (R0 dry-run)"}}
                "homologation_record" {"$type" "com.etzhayyim.yamabiko.homologationRecord"
                                       "trainsetId" trainset-id
                                       "serial" serial
                                       "trainsetDid" trainset-did
                                       "recordedAt" "2026-05-27T13:30:00Z"}}]
    {"cell" "homologation_binder" "status" (cell-status result) "result" result}))

;; ── cell 9: silen_rail_review ────────────────────────────────────────────────

(defn- solve-silen-rail-review [ctx]
  (let [review-id (get ctx "reviewSubjectId" "REVIEW-001")
        result {"review_state" {"phase" "record_emitted"
                                "reviewSubjectId" review-id
                                "completionPct" 100
                                "scope" (get ctx "scope" "r0-scaffold-baseline")
                                "councilSafeAddress" "0xCouncilSafe5of7..."
                                "councilSignatures" [{"councilMemberDid" "did:web:etzhayyim.com:council-member-1"
                                                      "signature" "..." "timestamp" "2026-05-27T16:00:00Z"}
                                                     {"councilMemberDid" "did:web:etzhayyim.com:council-member-2"
                                                      "signature" "..." "timestamp" "2026-05-27T16:00:05Z"}
                                                     {"councilMemberDid" "did:web:etzhayyim.com:council-member-3"
                                                      "signature" "..." "timestamp" "2026-05-27T16:00:10Z"}
                                                     {"councilMemberDid" "did:web:etzhayyim.com:council-member-4"
                                                      "signature" "..." "timestamp" "2026-05-27T16:00:15Z"}
                                                     {"councilMemberDid" "did:web:etzhayyim.com:council-member-5"
                                                      "signature" "..." "timestamp" "2026-05-27T16:00:20Z"}]
                                "decision" "approve"
                                "rationale" "Wave 1 R0 scaffold baseline review — approved."}
                "silen_rail_review" {"$type" "com.etzhayyim.yamabiko.silenRailReview"
                                     "reviewSubjectId" review-id
                                     "scope" (get ctx "scope" "r0-scaffold-baseline")
                                     "decision" "approve"
                                     "recordedAt" "2026-05-27T16:01:00Z"}}]
    {"cell" "silen_rail_review" "status" (cell-status result) "result" result}))

;; ── manufacture chain runner ─────────────────────────────────────────────────
;; NO HOF dispatch — direct calls only (kotoba-clj kais does not support
;; program-defined HOFs at WASM component-model tier)

(defn- manufacture [ctx]
  (let [t1 (solve-carbody-fabrication ctx)
        t2 (solve-bogie-assembly ctx)
        t3 (solve-traction-electrical ctx)
        t4 (solve-interior-hvac ctx)
        t5 (solve-final-assembly ctx)
        t6 (solve-dynamic-test ctx)
        t7 (solve-emissions-acoustic-audit ctx)
        t8 (solve-homologation-binder ctx)
        t9 (solve-silen-rail-review ctx)]
    [t1 t2 t3 t4 t5 t6 t7 t8 t9]))

;; ── WASM Component entrypoint ────────────────────────────────────────────────

(defn run [input]
  (let [ctx {"trainsetId" "YAMABIKO-TRAINSET-0001"
             "reviewSubjectId" "REVIEW-001"}
        trace     (manufacture ctx)
        ok-count  (count (filter (fn [t] (= "ok" (get t "status"))) trace))
        total     (count trace)]
    (str "yamabiko:" (str-int ok-count) "/" (str-int total) ":cells-ok")))
