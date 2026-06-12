;; ported from 20-actors/kuni-umi/cells/site_survey/cell.py (unit_refactor stage 0)
;; SiteSurveyCell — Phase 1 of kuni-umi 4-phase deployment workflow.
(ns kuni-umi.cells.site-survey.cell
  (:require [clojure.string] [clojure.set] [clojure.edn]))

(declare site-survey-state allocate-scout-fleet collect-sensor-blob jurisdiction-eligibility witness-attest emit-survey build-graph state-from-event thread-id-from-event healthz-extra)

(def site-survey-state
  {:siteDid nil
   :siteCode nil
   :geo nil
   :utilityClass nil
   :domain nil
   :jurisdictionDid nil
   :stewardDid nil
   :intendedUse nil
   :intendedBeneficiaryDids nil
   :localLawAttestationCid nil
   :fleetId nil
   :surveyBlobCids nil
   :ecologyBaseline nil
   :witnessAttestations nil
   :accepted nil
   :rejectionReason nil
   :_event_uri nil
   :_event_cid nil
   :_event_nsid nil})

;; TODO: port-failed unit allocate_scout_fleet (/var/folders/px/b63lssbx5056kq_1t6pvc1f80000gn/T/tmpeq9hibu8/scratch.clj:3:10: e)
;; def allocate_scout_fleet(state: SiteSurveyState, deps: CellDeps) -> SiteSurveyState:
;;     """Request N ≥ 2 Giemon scout robots from open-robo fleet."""
;;     raise NotImplementedError(
;;         "Requires Giemon Otete + Mimi base-station fleet operational. "
;;         "See ADR-2605201500 hardware/DID provisioning checklist."
;;     )
(defn allocate-scout-fleet [& _]
  (throw (ex-info "TODO: port-failed" {:from "allocate_scout_fleet"})))

;; TODO: port-failed unit collect_sensor_blob (/var/folders/px/b63lssbx5056kq_1t6pvc1f80000gn/T/tmpagrrn5nr/scratch.clj:3:10: e)
;; def collect_sensor_blob(state: SiteSurveyState, deps: CellDeps) -> SiteSurveyState:
;;     """Collect RGB-D / LIDAR / chem-sensor / multispectral blobs and pin to IPFS."""
;;     raise NotImplementedError(
;;         "Requires deps.sdk for IPFS pin via @etzhayyim/sdk and live Giemon fleet."
;;     )
(defn collect-sensor-blob [& _]
  (throw (ex-info "TODO: port-failed" {:from "collect_sensor_blob"})))

(defn jurisdiction-eligibility [state deps]
  (assoc state :accepted true)
  (assoc state :rejectionReason nil))

(defn witness-attest [state deps]
  (throw (ex-info "Requires per-robot DID keypair registration and signing endpoint. Constitutional invariant: N >= 2 must hold (ADR-2605201400 §9)."
                {:state state :deps deps})))

;; TODO: port-failed unit emit_survey (/var/folders/px/b63lssbx5056kq_1t6pvc1f80000gn/T/tmpzdc9teeg/scratch.clj:2:22: w)
;; def emit_survey(state: SiteSurveyState, deps: CellDeps) -> SiteSurveyState:
;;     """Write `submitSiteSurvey` MST record via @etzhayyim/sdk."""
;;     raise NotImplementedError(
;;         "Requires deps.sdk (@etzhayyim/sdk subprocess RPC). "
;;         "Writes com.etzhayyim.apps.etzhayyim.kuniUmi.submitSiteSurvey to MST."
;;     )
(defn emit-survey [& _]
  (throw (ex-info "TODO: port-failed" {:from "emit_survey"})))

;; TODO: port-failed unit build_graph (/var/folders/px/b63lssbx5056kq_1t6pvc1f80000gn/T/tmp31twy_hi/scratch.clj:2:1: er)
;; def build_graph(deps: CellDeps):
;;     """Build the SiteSurveyCell LangGraph per ADR-2605202200 §1 contract."""
;;     g = StateGraph(SiteSurveyState)
;; 
;;     g.add_node("allocate_scout_fleet", lambda s: allocate_scout_fleet(s, deps))
;;     g.add_node("collect_sensor_blob", lambda s: collect_sensor_blob(s, deps))
;;     g.add_node("jurisdiction_eligibility", lambda s: jurisdiction_eligibility(s, deps))
;;     g.add_node("witness_attest", lambda s: witness_attest(s, deps))
;;     g.add_node("emit_survey", lambda s: emit_survey(s, deps))
;; 
;;     g.add_edge(START, "allocate_scout_fleet")
;;     g.add_edge("allocate_scout_fleet", "collect_sensor_blob")
;;     g.add_edge("collect_sensor_blob", "jurisdiction_eligibility")
;; 
;;     def router(state: SiteSurveyState) -> str:
;;         return "witness_attest" if state.get("accepted") else "emit_survey"
;; 
;;     g.add_conditional_edges("jurisdiction_eligibility", router)
;;     g.add_edge("witness_attest", "emit_survey")
;;     g.add_edge("emit_survey", END)
;; 
;;     return g.compile(checkpointer=deps.checkpointer)
(defn build-graph [& _]
  (throw (ex-info "TODO: port-failed" {:from "build_graph"})))

;; TODO: port-failed unit state_from_event (assembled-lint error)
;; def state_from_event(event_record: dict, nsid: str) -> dict:
;;     """Map defineDeploymentSite event to SiteSurveyState."""
;;     return default_state_from_event(event_record, nsid)
(defn state-from-event [& _]
  (throw (ex-info "TODO: port-failed" {:from "state_from_event"})))

(defn thread-id-from-event [event-record nsid]
  (let [value (get event-record "value")
        site-did (or (get value "siteDid")
                      (get value "siteCode")
                      (get event-record "rkey" "unknown"))]
    (str "SiteSurveyCell:" site-did)))

(defn healthz-extra [deps]
  {:phase "1-survey"
   :fleet-required ["otete" "mimi-base-station"]
   :witness-invariant-min 2
   :trigger-nsid "com.etzhayyim.apps.etzhayyim.kuniUmi.defineDeploymentSite"})

