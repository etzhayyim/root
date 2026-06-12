;; ported from 60-apps/etzhayyim-project-kyber/lg/lg_kyber/graphs/business_operating_react.py (unit_refactor stage 0)
;; kyber business_operating_react — active-inference ReAct loop.
(ns lg.lg-kyber.graphs.business-operating-react
  (:require [clojure.string] [clojure.set] [clojure.edn]))

(declare log business-operating-react-state load-context react-loop synthesize notify build graph)

(def _max-react-iters 3)

(def business-operating-react-state
  {:product-id nil
   :run-date nil
   :context nil
   :react-steps nil
   :final-observation nil
   :risks-flagged nil
   :report nil
   :notified nil})

;; TODO: port-failed unit load_context (/var/folders/px/b63lssbx5056kq_1t6pvc1f80000gn/T/tmp65odcku5/scratch.clj:2:1: er)
;; async def load_context(state: BusinessOperatingReactState) -> BusinessOperatingReactState:
;;     today = date.today().isoformat()
;;     ctx: dict[str, Any] = {
;;         "product": "kyber",
;;         "description": "GL/AP/AR + HR + 在庫 SaaS — 脱出できる ERP (AT Protocol DID-native)",
;;         "phase": "Phase 1 — OSS Developer Adoption",
;;         "revenue_model": "Free/¥3,800/¥12,000/¥38,000/Enterprise",
;;         "arr_target_2026q4_jpy": 3_000_000,
;;         "date": today,
;;     }
;;     try:
;;         ctx["oss_stars_30d"] = int(await fetchval(
;;             "SELECT COUNT(*) FROM vertex_kyber_oss_event WHERE event_type='star' AND created_at >= NOW() - INTERVAL '30 days'"
;;         ) or 0)
;;     except Exception:
;;         ctx["oss_stars_30d"] = None
;;     try:
;;         ctx["cloud_tenants_paid"] = int(await fetchval(
;;             "SELECT COUNT(*) FROM vertex_kyber_tenant WHERE tier != 'free' AND status = 'active'"
;;         ) or 0)
;;     except Exception:
;;         ctx["cloud_tenants_paid"] = None
;;     try:
;;         ctx["cloud_mrr_jpy"] = int(await fetchval(
;;             """
;;             SELECT COALESCE(SUM(qty), 0) FROM vertex_kyber_billing_event
;;             WHERE metric = 'mrr_jpy'
;;               AND ts_ms >= EXTRACT(EPOCH FROM date_trunc('month', NOW())) * 1000
;;             """
;;         ) or 0)
;;     except Exception:
;;         ctx["cloud_mrr_jpy"] = None
;;     try:
;;         rows = await fetch(
;;             "SELECT slug, block, statement, status FROM vertex_kyber_bmc_hypothesis WHERE status = 'active' LIMIT 5"
;;         )
;;         ctx["active_hypotheses"] = [dict(r) for r in rows]
;;     except Exception:
;;         ctx["active_hypotheses"] = []
;; 
;;     return {**state, "run_date": today, "context": ctx, "react_steps": [], "risks_flagged": []}
(defn load-context [& _]
  (throw (ex-info "TODO: port-failed" {:from "load_context"})))

;; TODO: port-failed unit react_loop (/var/folders/px/b63lssbx5056kq_1t6pvc1f80000gn/T/tmp8j_el3da/scratch.clj:2:1: er)
;; async def react_loop(state: BusinessOperatingReactState) -> BusinessOperatingReactState:
;;     steps = list(state.get("react_steps") or [])
;;     ctx = state.get("context") or {}
;;     risks = list(state.get("risks_flagged") or [])
;;     final_obs = ""
;; 
;;     system_prompt = (
;;         "You are the kyber active-inference business operating agent.\n"
;;         "kyber is GL/AP/AR + HR + 在庫 SaaS targeting Japan SMB. Phase 1: OSS developer adoption.\n"
;;         "ARR target: ¥3M by 2026 Q4.\n"
;;         "Analyze the given context and produce a JSON object:\n"
;;         '{ "observation": "...", "action": {"type": "bmc_update_hypothesis"|"flag_risk"|"no_action", "detail": "..."} }\n'
;;         "Be concise (≤200 chars per field). Japanese is fine."
;;     )
;; 
;;     for i in range(_MAX_REACT_ITERS):
;;         user_prompt = json.dumps({
;;             "context": ctx,
;;             "steps_so_far": steps,
;;             "iteration": i + 1,
;;         }, ensure_ascii=False, default=str)
;;         parsed, source = _llm.call_llm_json(
;;             f"{system_prompt}\n\n{user_prompt}", max_tokens=300,
;;         )
;;         if not parsed:
;;             break
;;         obs = str(parsed.get("observation", ""))[:200]
;;         action = parsed.get("action") or {}
;;         action_type = str(action.get("type", "no_action"))
;;         detail = str(action.get("detail", ""))[:200]
;;         steps.append({"iteration": i + 1, "observation": obs, "action_type": action_type, "detail": detail, "source": source})
;;         final_obs = obs
;;         if action_type == "flag_risk":
;;             risks.append({"severity": "medium", "summary": detail, "source": f"react-iter-{i+1}"})
;;         if action_type == "no_action":
;;             break
;; 
;;     return {**state, "react_steps": steps, "final_observation": final_obs, "risks_flagged": risks}
(defn react-loop [& _]
  (throw (ex-info "TODO: port-failed" {:from "react_loop"})))

(defn synthesize [state]
  (let [ctx (or state "context" {})
        steps (or (get state "react_steps") [])
        risks (or (get state "risks_flagged") [])
        run-date (get state "run_date" (java.time/LocalDate.now.toString))
        mrr (get ctx "cloud_mrr_jpy" 0)
        tenants (get ctx "cloud_tenants_paid" 0)
        stars (get ctx "oss_stars_30d" 0)
        final-obs (get state "final_observation" "異常なし")

        report {:run-id (str "kyber-bo-react-" run-date)
               :product "kyber"
               :date run-date
               :summary {:oss-stars-30d stars
                         :cloud-mrr-jpy mrr
                         :cloud-tenants-paid tenants
                         :react-iterations (count steps)
                         :risks-flagged (count risks)}
               :final-observation final-obs
               :react-steps steps
               :risks risks}]
    (assoc state :report report)))

;; TODO: port-failed unit notify (/var/folders/px/b63lssbx5056kq_1t6pvc1f80000gn/T/tmpquw9_m9i/scratch.clj:4:41: e)
;; async def notify(state: BusinessOperatingReactState) -> BusinessOperatingReactState:
;;     report = state.get("report") or {}
;;     run_date = state.get("run_date", date.today().isoformat())
;;     summary_text = (
;;         f"[{run_date}] kyber BO-React: "
;;         f"stars30d={report.get('summary', {}).get('oss_stars_30d', '?')} "
;;         f"tenants_paid={report.get('summary', {}).get('cloud_tenants_paid', '?')} "
;;         f"mrr=¥{report.get('summary', {}).get('cloud_mrr_jpy', 0):,} "
;;         f"| {report.get('final_observation', '')[:100]}"
;;     )
;; 
;;     webhook_url = os.environ.get("TEAMS_KYBER_WEBHOOK_URL", "")
;;     notified = False
;;     if webhook_url:
;;         try:
;;             payload = {
;;                 "type": "message",
;;                 "attachments": [{
;;                     "contentType": "application/vnd.microsoft.card.adaptive",
;;                     "content": {
;;                         "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
;;                         "type": "AdaptiveCard", "version": "1.4",
;;                         "body": [
;;                             {"type": "TextBlock", "text": "kyber Business Operating Daily", "weight": "Bolder", "size": "Medium"},
;;                             {"type": "TextBlock", "text": summary_text, "wrap": True},
;;                         ],
;;                     },
;;                 }],
;;             }
;;             async with httpx.AsyncClient(timeout=10) as client:
;;                 r = await client.post(webhook_url, json=payload)
;;                 r.raise_for_status()
;;             notified = True
;;         except Exception as e:
;;             _log.warning("[kyber.bo_react] Teams webhook failed: %s", e)
;; 
;;     if not notified:
;;         try:
;;             await execute(
;;                 """
;;                 INSERT INTO vertex_kyber_outbox
;;                   (vertex_id, org_did, kind, subject, body_text,
;;                    recipient_email, status, created_at)
;;                 VALUES ($1,$2,$3,$4,$5,$6,$7,$8)
;;                 """,
;;                 str(uuid.uuid4()),
;;                 "did:web:kyber.etzhayyim.com",
;;                 "bo-react-daily",
;;                 f"kyber BO-React Daily {run_date}",
;;                 summary_text,
;;                 "jun@etzhayyim.group",
;;                 "queued-no-recipient",
;;                 datetime.now(timezone.utc),
;;             )
;;             notified = True
;;         except Exception as e:
;;             _log.warning("[kyber.bo_react] outbox insert failed: %s", e)
;; 
;;     _log.info("[kyber.bo_react] %s", summary_text)
;;     return {**state, "notified": notified}
(defn notify [& _]
  (throw (ex-info "TODO: port-failed" {:from "notify"})))

;; TODO: port-failed unit _build (assembled-lint error)
;; def _build() -> Any:
;;     sg = StateGraph(BusinessOperatingReactState)
;;     sg.add_node("load_context", load_context)
;;     sg.add_node("react_loop", react_loop)
;;     sg.add_node("synthesize", synthesize)
;;     sg.add_node("notify", notify)
;;     sg.add_edge(START, "load_context")
;;     sg.add_edge("load_context", "react_loop")
;;     sg.add_edge("react_loop", "synthesize")
;;     sg.add_edge("synthesize", "notify")
;;     sg.add_edge("notify", END)
;;     return sg.compile()
(defn build [& _]
  (throw (ex-info "TODO: port-failed" {:from "_build"})))

;; TODO: port-failed unit GRAPH (assembled-lint error)
;; GRAPH = _build()
(def graph nil) ;; TODO: port-failed const

