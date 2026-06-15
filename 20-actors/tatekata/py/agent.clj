#!/usr/bin/env bb
;; Working Clojure port of py/agent.py (tatekata 建方 construction actor).
(ns tatekata.py.agent
  "tatekata 建方 — construction langgraph actor (kotoba WASM cell).

  ADR-2605250715, R0 scaffold. Runs in-WASM on kotoba :8077. Handlers over the
  construction project lifecycle (5 phases: foundation → structural → mep →
  finishing → commissioning), with tatekata's constitutional gates enforced:

    G1  open-source firmware         all robot firmware open-source (Apache 2.0 + Charter Rider)
    G2  IPFS-pinned site attestation site survey photos + depth maps pinned before human enters
    G3  witness-quorum robots        progress records signed by ≥2 distinct robots (G3)
    G5  charter-rider sourcing       sourcing audit + no conflict minerals (R0 scope)
    G6  trajectory determinism       Giemon joint angles logged @ 10 Hz; WASM state machine sealed
    G11 KPI caps                     ≤2 stories / ≤5000 m² footprint (prevents scope creep)
    G13 murakumo-only                inference via KotobaLLM 127.0.0.1:4000; external LLM prohibited
    G14 kotoba-eavt-native           state is kotoba Datom log (no SQL/RisingWave/Cypher)
    G15 tithe-non-fiat               USDC Base L2 + ERC-4337 + TitheRouter 10% only (no fiat)
    G16 no-server-key                platform holds no key; owner/operator signs attestations
    G17 consent-bound                compute-only R0; settlement stops at :intent

  LLM access is Murakumo-only via KotobaLLM (127.0.0.1:4000, gemma3:4b; G13). State
  is written back to the kotoba Datom log (G14). Settlement is USDC on Base L2 +
  ERC-4337 + TitheRouter 10% only — no fiat, no Stripe (G15). The platform holds no
  key; the owner signs each settlement with their own passkey/smart-account (G16).
  All phase boundaries are recorded as Datoms — no silent truncation. Every progress
  record requires ≥2 robot witness signatures (G3).

  This R0 build computes and returns plans/records; it does not dispatch real
  construction work and does not broadcast settlements (both G17-gated; settlement
  stops at :intent).

  Run:  bb --classpath 20-actors 20-actors/tatekata/py/agent.clj")

;; ── constants ──────────────────────────────────────────────────────────────────
(def TITHE_BPS 1000)  ; 10% TitheRouter auto-split (G15), basis points
;; G11 KPI caps
(def MAX_STORIES 2)
(def MAX_FOOTPRINT_M2 5000)
;; linear phase trajectory (G17) — every transition is a recorded stage
(def PHASES ["foundation" "structural" "mep" "finishing" "commissioning"])

;; --------------------------------------------------------------------------- ;;
;; G11 — KPI caps (stories / footprint)
;; --------------------------------------------------------------------------- ;;
(defn kpi-caps-ok
  "Check project scope against KPI caps (G11)."
  [stories footprint-m2]
  (cond
    (> stories MAX_STORIES)
    {:ok false :reason (str "stories " stories " > " MAX_STORIES " (G11)")}

    (> footprint-m2 MAX_FOOTPRINT_M2)
    {:ok false :reason (str "footprint " footprint-m2 " m² > " MAX_FOOTPRINT_M2 " (G11)")}

    :else
    {:ok true :reason "within KPI caps"}))

;; --------------------------------------------------------------------------- ;;
;; G3 — witness quorum (≥2 distinct robot DIDs per phase boundary)
;; --------------------------------------------------------------------------- ;;
(defn witness-quorum-ok
  "Verify ≥2 distinct robot DIDs witness the phase boundary (G3)."
  [robot-dids]
  (let [distinct (count (set robot-dids))]
    (if (< distinct 2)
      {:ok false :reason (str "witness count " distinct " < 2 (G3)")}
      {:ok true :reason "witness quorum satisfied"})))

;; --------------------------------------------------------------------------- ;;
;; Phase advancement state machine (G17 — every stage recorded)
;; --------------------------------------------------------------------------- ;;
(defn advance-phase
  "Advance one phase along PHASES. Return error if already terminal (G17)."
  [current-phase]
  (if (not (some #(= current-phase %) PHASES))
    {:state current-phase :blocked "unknown phase"}
    (let [idx (.indexOf PHASES current-phase)
          nxt-idx (inc idx)]
      (if (>= nxt-idx (count PHASES))
        {:state current-phase :blocked "already terminal (commissioning)"}
        {:state (nth PHASES nxt-idx) :blocked nil}))))

;; --------------------------------------------------------------------------- ;;
;; foundation_excavation handler
;; --------------------------------------------------------------------------- ;;
(defn handle-foundation-excavation
  "Parse site plan, survey utilities, generate giemon excavation plan, approve (G17)."
  [state]
  (let [spec (get state "spec" "")]
    (if (empty? spec)
      (assoc state "blocked" "spec required")
      (let [plan {"phase"              "foundation"
                  "spec"               spec
                  "giemon_plan_type"   "excavation-grid-5m-spacing"
                  "trajectory_logged"  true}]
        (assoc state "plan" plan)))))

;; --------------------------------------------------------------------------- ;;
;; structural_assembly handler
;; --------------------------------------------------------------------------- ;;
(defn handle-structural-assembly
  "Load BIM, validate foundations, coordinate robots, get metrology witness (G17)."
  [state]
  (let [bim-ref (get state "bim_ref" "")]
    (if (empty? bim-ref)
      (assoc state "blocked" "BIM reference required")
      (let [plan {"phase"              "structural"
                  "bim_ref"            bim-ref
                  "robot_coordination" "giemon-otete-shoring-sequence"
                  "metrology"          "mimi-witness-plumb-level"}]
        (assoc state "plan" plan)))))

;; --------------------------------------------------------------------------- ;;
;; mep_installation handler
;; --------------------------------------------------------------------------- ;;
(defn handle-mep-installation
  "Route ductwork, conduit, piping; perform pressure testing (G17)."
  [state]
  (let [mep-design (get state "mep_design" "")]
    (if (empty? mep-design)
      (assoc state "blocked" "MEP design required")
      (let [plan {"phase"              "mep"
                  "ductwork_route"     "otete-arm-3d-trajectory"
                  "conduit_route"      "otete-arm-conduit-chase"
                  "piping_route"       "otete-arm-press-fit-sequence"
                  "pressure_test_type" "pneumatic-5-bar-15min"}]
        (assoc state "plan" plan)))))

;; --------------------------------------------------------------------------- ;;
;; finishing_handoff handler
;; --------------------------------------------------------------------------- ;;
(defn handle-finishing-handoff
  "Prep surfaces, drywall/tape/mud (R0 manual), paint, trim install (G17)."
  [state]
  (let [phase-input (get state "phase_input" "")]
    (if (empty? phase-input)
      (assoc state "blocked" "phase input required")
      (let [plan {"phase"        "finishing"
                  "surface_prep" "giemon-substrate-clean"
                  "drywall"      "manual-subcontractor-r0"
                  "paint"        "spray-cure-r0"
                  "trim"         "manual-installation-r0"}]
        (assoc state "plan" plan)))))

;; --------------------------------------------------------------------------- ;;
;; commissioning handler
;; --------------------------------------------------------------------------- ;;
(defn handle-commissioning
  "Final systems test, defect walkdown, waste inventory, sign-off (G17)."
  [state]
  (let [phase-input (get state "phase_input" "")]
    (if (empty? phase-input)
      (assoc state "blocked" "phase input required")
      (let [plan {"phase"               "commissioning"
                  "hvac_test"           "airflow-temp-control-verify"
                  "electrical_test"     "circuit-continuity-load-test"
                  "plumbing_test"       "water-pressure-flow-rate"
                  "defect_walkdown"     "photo-punch-list-generation"
                  "waste_categorization" "reuse/recycle/landfill percent"}]
        (assoc state "plan" plan)))))

;; --------------------------------------------------------------------------- ;;
;; progress record — all phase boundaries recorded as Datoms (G17)
;; --------------------------------------------------------------------------- ;;
(defn record-phase-progress
  "Create a phase-boundary progress record. Requires ≥2 robot witnesses (G3/G17)."
  ([phase project-did robot-dids]
   (record-phase-progress phase project-did robot-dids "" ""))
  ([phase project-did robot-dids photo-cid depth-map-cid]
   (let [witness (witness-quorum-ok robot-dids)]
     (if (not (:ok witness))
       {:error (:reason witness) :blocked true}
       {":progress/phase"         phase
        ":progress/project-did"   project-did
        ":progress/robot-dids"    robot-dids
        ":progress/photo-cid"     (or photo-cid "")
        ":progress/depth-map-cid" (or depth-map-cid "")}))))

;; --------------------------------------------------------------------------- ;;
;; settlement — USDC + TitheRouter intent (NOT broadcast; G15/G16/G17)
;; --------------------------------------------------------------------------- ;;
(defn build-settlement-intent
  "Compute the USDC settlement split. 10% tithe → Public Fund. Stops at :intent —
  broadcast needs an owner signature (G16) + operator gate (G17).
  R0 behaviour: state is 'executed' when owner-sig-ref is provided, else 'intent'.
  This matches agent.py exactly."
  ([gross-minor]
   (build-settlement-intent gross-minor nil))
  ([gross-minor owner-sig-ref]
   (let [gross (long gross-minor)
         tithe (quot (* gross TITHE_BPS) 10000)
         owner-payout (- gross tithe)]
     {:rail              "usdc-base-l2"
      :grossMinor        gross
      :titheMinor        tithe
      :ownerPayoutMinor  owner-payout
      :titheRouter       "50-infra/etzhayyim-tithe-router"
      ;; owner signs with their own passkey/smart-account; platform holds no key (G16)
      :state             (if owner-sig-ref "executed" "intent")
      :ownerSigRef       (or owner-sig-ref "")})))

;; ── main (smoke demo) ─────────────────────────────────────────────────────────
(defn -main [& _]
  (let [demo-foundation (handle-foundation-excavation {"spec" "site survey + grid excavation"})]
    (println "foundation plan:" (get (get demo-foundation "plan") "phase")))
  (let [demo-settlement (build-settlement-intent 50000000)]
    (println "settlement:" demo-settlement)))

(when (= *file* (System/getProperty "babashka.file"))
  (-main))
