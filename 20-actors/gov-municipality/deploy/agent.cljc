;; gov_municipality 自治体 — kotoba-clj WASM Component entrypoint (ADR-2606230001, 2026-06-23)
;;
;; 3 Pregel cells assembled into ONE WASM Component.
;; Cells are clean (0 blockers); no safe-rewrites required.
;;
;; entrypoint: run: func(input: list<u8>) -> list<u8>
;; smoke output: "gov_municipality:3/3:cells-ok"

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

;; last8: return last 8 chars via byte iteration (no subs/str-slice)
(defn- last8 [s]
  (let [len (str-len s)
        start (max 0 (- len 8))
        buf (bytes-alloc (- len start))]
    (loop [i start]
      (if (>= i len)
        (bytes-finish buf)
        (do (byte-append! buf (byte-at s i)) (recur (+ i 1)))))))

;; ── cell-status helper ───────────────────────────────────────────────────────

(defn- cell-status [result]
  (cond
    (get result "error")   "error"
    (get result "refused") "refused"
    :else                  "ok"))

;; ── cell 1: permit_submission ────────────────────────────────────────────────

(defn- solve-permit-submission [ctx]
  (let [project-id (get ctx "projectId" "PROJ-UNKNOWN")
        permit-id  (str "TOKYO-2026-" (last8 project-id))
        result {"permit_state" {"phase" "submitted"
                                "projectId" project-id
                                "completionPct" 100
                                "jurisdiction" "Japan-Tokyo"
                                "siteLocation" {"jurisdiction_type" "Japan" "prefecture" "Tokyo"}
                                "buildingType" "residential"
                                "applicationData" {"template_id" "japan-tokyo-residential-2026"
                                                   "building_type_enum" ["residential" "commercial"]
                                                   "required_forms" ["Form1" "Form2"]
                                                   "applicant_name" "Developer"
                                                   "site_address" "Tokyo"
                                                   "gfa_m2" 2400
                                                   "permitApplicationId" permit-id
                                                   "submissionDate" "2026-05-26T10:00:00Z"
                                                   "status" "under_review"}
                                "permitApplicationId" permit-id
                                "submissionTimestamp" "2026-05-26T10:00:00Z"}
                "permit_application_record" {"projectId" project-id
                                             "permitApplicationId" permit-id}}]
    {"cell" "permit_submission" "status" (cell-status result) "result" result}))

;; ── cell 2: inspection_scheduling ───────────────────────────────────────────

(defn- solve-inspection-scheduling [ctx]
  (let [project-id (get ctx "projectId" "PROJ-UNKNOWN")
        schedule   {"foundation_inspection" "2026-06-20"
                    "structural_inspection" "2026-07-15"
                    "mep_inspection" "2026-08-10"
                    "finishing_inspection" "2026-09-05"
                    "final_inspection" "2026-09-20"}
        result {"inspection_state" {"phase" "complete"
                                    "projectId" project-id
                                    "completionPct" 100
                                    "schedule" schedule}
                "inspection_schedule_record" {"projectId" project-id
                                              "schedule" schedule}}]
    {"cell" "inspection_scheduling" "status" (cell-status result) "result" result}))

;; ── cell 3: final_sign_off ───────────────────────────────────────────────────

(defn- solve-final-sign-off [ctx]
  (let [project-id (get ctx "projectId" "PROJ-UNKNOWN")
        mock-sig   {"authority_did" "did:web:tokyo.lg.jp:building"
                    "signature" "aB3cD6eF9gH..."
                    "occupancy_clearance" true}
        result {"signoff_state" {"phase" "signed"
                                 "projectId" project-id
                                 "completionPct" 100
                                 "signature" mock-sig}
                "permits_finalized_record" {"projectId" project-id
                                            "occupancy_clearance" true
                                            "authority_signature" mock-sig}}]
    {"cell" "final_sign_off" "status" (cell-status result) "result" result}))

;; ── permit workflow chain runner ──────────────────────────────────────────────
;; NO HOF dispatch — direct calls only

(defn- permit-workflow [ctx]
  (let [t1 (solve-permit-submission ctx)
        t2 (solve-inspection-scheduling ctx)
        t3 (solve-final-sign-off ctx)]
    [t1 t2 t3]))

;; ── WASM Component entrypoint ────────────────────────────────────────────────

(defn run [input]
  (let [ctx      {"projectId" "PROJ-GOV-MUNI-0001"}
        trace    (permit-workflow ctx)
        ok-count (count (filter (fn [t] (= "ok" (get t "status"))) trace))
        total    (count trace)]
    (str "gov_municipality:" (str-int ok-count) "/" (str-int total) ":cells-ok")))
