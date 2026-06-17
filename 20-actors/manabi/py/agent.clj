#!/usr/bin/env bb
;; Working Clojure port of py/agent.py (manabi open-curriculum education actor).
(ns manabi.py.agent
  "manabi 学び — open-curriculum education langgraph actor (kotoba WASM cell).

  ADR-2605261045, migration plan Phase 4. Runs in-WASM on kotoba :8077. Five handlers
  over one kotoba EAVT graph, mirroring the curriculum path:

    handle_literacy         reading + writing progression (phonemic awareness → written expression)
    handle_numeracy         counting → arithmetic → algebra → calculus
    handle_civics_charter   comparative governance + etzhayyim Charter understanding (anti-indoctrination G12)
    handle_vocational       practical skill demonstration (agriculture/construction/energy/pharma domains)
    handle_lifelong_inquiry open-ended learner-led exploration (no age-out, G11)

  LLM access is Murakumo-only via KotobaLLM (127.0.0.1:4000, gemma3:4b; G5). State is
  written back to the kotoba Datom log (G6). Anti-addiction UX enforced structurally (G3).
  Minor learners get aggregate-only attestations (G6 privacy). Anti-credentialism (G7):
  no degrees/transcripts, only skillAttestation (replayable demonstrations). Member signature
  on settlement only (G15). This R0 build computes and returns plans/records; it does not
  broadcast real settlements (G11-gated; settlement stops at :intent).

  Run:  bb --classpath 20-actors 20-actors/manabi/py/agent.clj")

;; ── constants ──────────────────────────────────────────────────────────────────
(def TITHE_BPS 1000)   ; 10% TitheRouter auto-split (constitutional), basis points

;; ── _murakumo_infer — Murakumo-only inference (G5) ───────────────────────────
(defn _murakumo_infer
  "Murakumo-only inference (G5). Returns offline sentinel when host not available."
  [_prompt]
  ;; In WASM host: would call (llm/infer model prompt). Offline sentinel matches agent.py.
  "LLM_NOT_AVAILABLE")

;; ── _validate_minor_aggregate_only — G6 privacy gate ─────────────────────────
(defn _validate_minor_aggregate_only
  "G6 enforcement: minors get aggregate-only fields only.
  Returns true if data is safe for the age_bucket; false if a forbidden PII key is present."
  [age-bucket data]
  (if (not= age-bucket "minor")
    true
    (let [forbidden #{"performancePercentile" "errorLogSummary" "timeOnTaskSec"}]
      (not (some #(contains? data %) forbidden)))))

;; ── handle_literacy ───────────────────────────────────────────────────────────
(defn handle_literacy
  "Reading + writing progression (phonemic awareness → written expression)."
  [state]
  (let [stage (get state "current_stage" "intro")
        flow  ["intro" "phonemic-awareness" "decoding" "fluency" "comprehension"
               "writing-mechanics" "written-expression"]
        idx   (.indexOf flow stage)]
    (if (and (>= idx 0) (< (inc idx) (count flow)))
      (let [next-stage (nth flow (inc idx))
            prompt     (str "Learner advancing from " stage " to " next-stage " in literacy. "
                            "Suggest a guided discovery activity (not worksheets).")]
        (_murakumo_infer prompt)
        (merge state
               {"current_stage"       next-stage
                "completion_fraction" (min 1.0 (+ (get state "completion_fraction" 0.0) 0.15))}))
      state)))

;; ── handle_numeracy ───────────────────────────────────────────────────────────
(defn handle_numeracy
  "Counting → arithmetic → algebra → calculus."
  [state]
  (let [stage (get state "current_stage" "counting")
        flow  ["counting" "place-value" "addition-subtraction" "multiplication-division"
               "fractions" "decimals" "algebra" "geometry" "calculus"]
        idx   (.indexOf flow stage)]
    (if (and (>= idx 0) (< (inc idx) (count flow)))
      (let [next-stage (nth flow (inc idx))
            prompt     (str "Learner advancing from " stage " to " next-stage " in numeracy. "
                            "Suggest hands-on discovery (manipulatives, real-world context).")]
        (_murakumo_infer prompt)
        (merge state
               {"current_stage"       next-stage
                "completion_fraction" (min 1.0 (+ (get state "completion_fraction" 0.0) 0.11))}))
      state)))

;; ── handle_civics_charter ─────────────────────────────────────────────────────
(defn handle_civics_charter
  "Comparative governance + etzhayyim Charter understanding (anti-indoctrination G12)."
  [state]
  (let [prompt  (str "Teach Charter understanding via comparative governance lens: "
                     "democracy, monarchy, theocracy, communalism, etc. Include etzhayyim as ONE example. "
                     "No single-truth framing (G12, G14). Learner-led inquiry encouraged.")
        _result (_murakumo_infer prompt)
        level   (get state "charter_understanding_level" "foundational")
        level   (if (= level "foundational") "intermediate" level)]
    (merge state
           {"charter_understanding_level" level
            "timestamp"                   "2026-06-02T10:00:00Z"})))

;; ── handle_vocational ─────────────────────────────────────────────────────────
(defn handle_vocational
  "Practical skill demonstration (agriculture/construction/energy/pharma)."
  [state]
  (let [domain  (get state "domain" "agriculture")
        prompt  (str "Learner demonstrating skill in " domain " domain. "
                     "Guide creation of replayable artifact (code, photo, project). "
                     "Output: demonstration CID for on-chain skill attestation (anti-credentialism G7).")
        _result (_murakumo_infer prompt)]
    (merge state
           {"demonstration_cid" "bafyreiexample-skill-artifact-placeholder"
            "skill_domain"      domain})))

;; ── handle_lifelong_inquiry ───────────────────────────────────────────────────
(defn handle_lifelong_inquiry
  "Open-ended learner-led exploration (no age-out, G11)."
  [state]
  (let [topic (get state "inquiry_topic" "")
        topic (if (empty? topic)
                (let [prompt "Learner is beginning lifelong inquiry. Help them formulate a genuine question about something they wonder."
                      result (_murakumo_infer prompt)]
                  (if (and result (pos? (count result)))
                    (subs result 0 (min 100 (count result)))
                    "open-exploration"))
                topic)
        prompt (str "Learner exploring: '" topic "'. "
                    "Guide resource discovery, synthesis, and self-paced project. "
                    "100% learner-led (G13). No age-out (G11).")]
    (_murakumo_infer prompt)
    (merge state
           {"inquiry_topic"       topic
            "completion_fraction" (min 1.0 (+ (get state "completion_fraction" 0.0) 0.20))})))

;; ── build_settlement_intent — USDC + TitheRouter (G7/G15) ────────────────────
(defn build_settlement_intent
  "Build USDC settlement intent (G7: non-fiat only, G15: member signature only).
  Stops at :intent unless member signature present (G11).
  Tithe split: 10% → Public Fund via TitheRouter (constitutional automatic)."
  ([gross-minor]
   (build_settlement_intent gross-minor nil))
  ([gross-minor buyer-sig-ref]
   (let [gross (long gross-minor)
         tithe (quot (* gross TITHE_BPS) 10000)
         factory-payout (- gross tithe)]
     {"gross_minor"         gross
      "tithe_minor"         tithe
      "factory_payout_minor" factory-payout
      "rail"                "usdc-base-l2"
      "state"               (if buyer-sig-ref "executed" "intent")
      "buyer_sig_ref"       buyer-sig-ref})))

;; ── check_domain_gate — domain gate enforcement ───────────────────────────────
(defn check_domain_gate
  "Domain gate enforcement (injected for testing).
  gate-fn defaults to nil with a built-in default behaviour (tsukuru injected-fn pattern).
  When gate-fn is provided, calls (gate-fn learner-did gate-name).
  Default: allowed=true, reason=no domain gate wired (R0)."
  ([learner-did gate-name]
   (check_domain_gate learner-did gate-name nil))
  ([learner-did gate-name gate-fn]
   (if (some? gate-fn)
     (gate-fn learner-did gate-name)
     {"allowed" true "reason" "no domain gate wired (R0)"})))

;; ── main (smoke demo) ─────────────────────────────────────────────────────────
(defn main [& _]
  (println "literacy advance:" (get (handle_literacy {"current_stage" "intro" "completion_fraction" 0.0}) "current_stage"))
  (println "numeracy advance:" (get (handle_numeracy {"current_stage" "counting" "completion_fraction" 0.0}) "current_stage"))
  (println "civics level:" (get (handle_civics_charter {"charter_understanding_level" "foundational"}) "charter_understanding_level"))
  (println "settlement:" (build_settlement_intent 1000000))
  (println "gate default:" (check_domain_gate "did:web:test" "G1"))
  (println "minor aggregate valid:" (_validate_minor_aggregate_only "minor" {"sessionDuration" 45}))
  (println "minor PII refused:" (_validate_minor_aggregate_only "minor" {"performancePercentile" 85})))

(when (= *file* (System/getProperty "babashka.file"))
  (main))
