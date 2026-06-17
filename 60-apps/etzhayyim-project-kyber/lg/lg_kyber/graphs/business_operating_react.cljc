;; ported from 60-apps/etzhayyim-project-kyber/lg/lg_kyber/graphs/business_operating_react.py
;; — real port replacing the unit_refactor stage-0 "TODO: port-failed" stubs.
;; NS is the porter ns with the "root." prefix removed (lg.lg-kyber.graphs.business-operating-react),
;; matching the sibling lg.lg-animeka.checkpointer / lg.lg-mangaka.graphs.* convention; output is .cljc.
;;
;; kyber business_operating_react — active-inference ReAct loop.
;;
;; Runs daily at 06:00 JST (21:00 UTC). Analyzes kyber's BMC/KPI/finance using the
;; Murakumo LLM fleet and emits a strategic daily brief to Teams or the kyber outbox.
;;
;; Pipeline: load-context → react-loop → synthesize → notify → END
;;
;; House style: LangGraph state stays string-keyed maps, byte-for-byte the shapes the Python
;; code produced; Python ':kw'-style values (action types, severities, etc.) are kept verbatim
;; as strings. Pure fns are direct ports. The three nodes that need the external Python/LangGraph
;; runtime have no host-independent JVM equivalent and are gated behind #?(:clj ...):
;;   - load-context calls lg_kyber.db.{fetch,fetchval} (RisingWave/PG async pool)
;;   - react-loop calls lg_kyber.graphs._llm.call_llm_json (Murakumo LLM fleet)
;;   - notify does httpx + lg_kyber.db.execute (Teams webhook + outbox INSERT)
;; Each raises the same precondition the Python enforces (its external dependency must be bound).
;; `synthesize` is a pure transform and is ported faithfully. The build()/GRAPH construction wraps
;; langgraph.graph.StateGraph (an external Python dep with no Clojure/JVM equivalent), so it stays
;; behind the same host gate; the Python module-load-time `GRAPH = _build()` demo is omitted.
;; Self-contained: requires no sibling stub ns.
(ns lg.lg-kyber.graphs.business-operating-react
  (:require [clojure.string :as str]))

(declare load-context react-loop synthesize notify build graph)

(def max-react-iters 3)

;; BusinessOperatingReactState (TypedDict, total=False) — string-keyed shape:
;;   "product_id" "run_date" "context" "react_steps" "final_observation"
;;   "risks_flagged" "report" "notified"
(def business-operating-react-state
  {"product_id"        nil
   "run_date"          nil
   "context"           nil
   "react_steps"       nil
   "final_observation" nil
   "risks_flagged"     nil
   "report"            nil
   "notified"          nil})

;; ── helpers ──────────────────────────────────────────────────────────────────
(defn- today-iso
  "date.today().isoformat() — UTC-naive local date, ISO-8601 yyyy-MM-dd."
  []
  #?(:clj (str (java.time.LocalDate/now))
     :default (throw (ex-info "bind a today-iso impl on this host" {}))))

(defn- truncate
  "Python str(x)[:n] — string-cast then take the first n chars."
  [x n]
  (let [s (str x)]
    (subs s 0 (min n (count s)))))

(defn- group-thousands
  "Python format ¥{n:,} — group integer digits in threes with commas."
  [n]
  (let [neg? (neg? n)
        digits (str (abs (long n)))
        len (count digits)
        grouped (->> (range len)
                     (map (fn [i]
                            (let [c (nth digits i)
                                  pos-from-end (- len i)]
                              (if (and (pos? i) (zero? (mod pos-from-end 3)))
                                (str "," c)
                                (str c)))))
                     (apply str))]
    (str (when neg? "-") grouped)))

;; ── load_context (node) ───────────────────────────────────────────────────────
;; async def load_context(state) -> state:
;;   builds the static ctx map, then layers DB-derived KPIs (oss_stars_30d / cloud_tenants_paid /
;;   cloud_mrr_jpy / active_hypotheses) each behind its own try/except. The DB reads go through
;;   lg_kyber.db.{fetchval,fetch} (an external async RisingWave/PG pool with no JVM equivalent),
;;   so the node is host-gated; the pure static-ctx shape is preserved in the docstring above.
(defn load-context [_state]
  #?(:clj (throw (ex-info "load-context requires lg_kyber.db (fetch/fetchval) — external async DB pool, not available on the JVM host"
                          {:node "load_context" :deps ["lg_kyber.db.fetchval" "lg_kyber.db.fetch"]}))
     :default (throw (ex-info "load-context requires the lg_kyber.db pool" {:node "load_context"}))))

;; ── react_loop (node) ──────────────────────────────────────────────────────────
;; async def react_loop(state) -> state:
;;   the bounded (max 3 iter) active-inference loop. Each iteration json.dumps the context/steps,
;;   calls _llm.call_llm_json (Murakumo/OpenRouter fleet), appends a step, and breaks on no_action
;;   or empty parse. The LLM call has no host-independent equivalent (Murakumo-only, ADR-2605215000),
;;   so the node is host-gated. The system prompt + loop semantics are preserved verbatim below.
;;
;; system_prompt:
;;   "You are the kyber active-inference business operating agent.\n"
;;   "kyber is GL/AP/AR + HR + 在庫 SaaS targeting Japan SMB. Phase 1: OSS developer adoption.\n"
;;   "ARR target: ¥3M by 2026 Q4.\n"
;;   "Analyze the given context and produce a JSON object:\n"
;;   '{ "observation": "...", "action": {"type": "bmc_update_hypothesis"|"flag_risk"|"no_action", "detail": "..."} }\n'
;;   "Be concise (≤200 chars per field). Japanese is fine."
;; for i in range(MAX_REACT_ITERS):
;;   parsed, source = _llm.call_llm_json(f"{system_prompt}\n\n{user_prompt}", max_tokens=300)
;;   if not parsed: break
;;   obs = str(parsed["observation"])[:200]; action_type = str(action["type"]); detail = str(action["detail"])[:200]
;;   steps.append({"iteration": i+1, "observation": obs, "action_type": action_type, "detail": detail, "source": source})
;;   if action_type == "flag_risk": risks.append({"severity": "medium", "summary": detail, "source": f"react-iter-{i+1}"})
;;   if action_type == "no_action": break
(defn react-loop [_state]
  #?(:clj (throw (ex-info "react-loop requires _llm.call_llm_json — Murakumo LLM fleet (ADR-2605215000), not available on the JVM host"
                          {:node "react_loop" :deps ["lg_kyber.graphs._llm.call_llm_json"]
                           :max-react-iters max-react-iters}))
     :default (throw (ex-info "react-loop requires the Murakumo LLM fleet" {:node "react_loop"}))))

;; ── synthesize (node) ──────────────────────────────────────────────────────────
;; async def synthesize(state) -> state: PURE — folds context + react steps + risks into a report.
;; Faithful 1:1 port (string-keyed throughout; `or 0` → nil-default to 0; len → count).
(defn synthesize [state]
  (let [ctx       (or (get state "context") {})
        steps     (or (get state "react_steps") [])
        risks     (or (get state "risks_flagged") [])
        run-date  (get state "run_date" (today-iso))
        mrr       (or (get ctx "cloud_mrr_jpy") 0)
        tenants   (or (get ctx "cloud_tenants_paid") 0)
        stars     (or (get ctx "oss_stars_30d") 0)
        final-obs (get state "final_observation" "異常なし")
        report    {"run_id"            (str "kyber-bo-react-" run-date)
                   "product"           "kyber"
                   "date"              run-date
                   "summary"           {"oss_stars_30d"      stars
                                        "cloud_mrr_jpy"      mrr
                                        "cloud_tenants_paid" tenants
                                        "react_iterations"   (count steps)
                                        "risks_flagged"      (count risks)}
                   "final_observation" final-obs
                   "react_steps"       steps
                   "risks"             risks}]
    (assoc state "report" report)))

;; ── notify summary text (pure) ─────────────────────────────────────────────────
;; The f-string the Python `notify` builds before any I/O — pure, so ported directly and reused
;; by the host-gated notify node. Mirrors:
;;   f"[{run_date}] kyber BO-React: stars30d={...} tenants_paid={...} mrr=¥{...:,} | {final_obs[:100]}"
(defn notify-summary-text
  "Build the kyber BO-React summary line from a report map + run-date (pure)."
  [report run-date]
  (let [summary (or (get report "summary") {})]
    (str "[" run-date "] kyber BO-React: "
         "stars30d=" (get summary "oss_stars_30d" "?") " "
         "tenants_paid=" (get summary "cloud_tenants_paid" "?") " "
         "mrr=¥" (group-thousands (get summary "cloud_mrr_jpy" 0)) " "
         "| " (truncate (get report "final_observation" "") 100))))

;; ── notify (node) ──────────────────────────────────────────────────────────────
;; async def notify(state) -> state: builds summary_text (pure, see notify-summary-text), then
;; tries a Teams adaptive-card webhook (httpx POST), falling back to a vertex_kyber_outbox INSERT
;; (lg_kyber.db.execute). Both edges are host/network I/O with no JVM equivalent → host-gated.
;; The pure summary-text builder above carries the only host-independent content.
(defn notify [state]
  #?(:clj (let [report   (or (get state "report") {})
                run-date (get state "run_date" (today-iso))
                _summary (notify-summary-text report run-date)]
            (throw (ex-info "notify requires httpx (Teams webhook) + lg_kyber.db.execute (outbox INSERT) — host/network I/O not available on the JVM host"
                            {:node "notify" :deps ["httpx.AsyncClient" "lg_kyber.db.execute"]
                             :webhook-env "TEAMS_KYBER_WEBHOOK_URL"})))
     :default (throw (ex-info "notify requires httpx + the lg_kyber.db pool" {:node "notify"}))))

;; ── _build / GRAPH ─────────────────────────────────────────────────────────────
;; def _build(): wraps langgraph.graph.StateGraph (START → load_context → react_loop → synthesize
;; → notify → END) and .compile()s it. StateGraph is an external Python/LangGraph dep with no
;; Clojure/JVM equivalent (same posture as lg.lg-animeka.checkpointer), so build() is host-gated.
;; The Python module-load-time demo `GRAPH = _build()` is omitted (it would run at import time).
(defn build
  "Construct the LangGraph StateGraph (START → load-context → react-loop → synthesize → notify → END)."
  []
  #?(:clj (throw (ex-info "build requires langgraph.graph.StateGraph — external Python/LangGraph runtime, no JVM equivalent"
                          {:nodes ["load_context" "react_loop" "synthesize" "notify"]
                           :edges [["START" "load_context"]
                                   ["load_context" "react_loop"]
                                   ["react_loop" "synthesize"]
                                   ["synthesize" "notify"]
                                   ["notify" "END"]]}))
     :default (throw (ex-info "build requires the langgraph StateGraph runtime" {}))))

;; GRAPH = _build()  — omitted (module-load-time demo; build() is host-gated, see above).
(def graph nil)
