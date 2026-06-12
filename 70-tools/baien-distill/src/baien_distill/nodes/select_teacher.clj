;; ported from 70-tools/baien-distill/src/baien_distill/nodes/select_teacher.py (unit_refactor stage 0)
;; (2) select_teacher: pick an on-fleet OSS teacher meeting ADR constraints.
(ns src.baien-distill.nodes.select-teacher
  (:require [clojure.string] [clojure.set] [clojure.edn]))

(declare teacher-candidates select-teacher)

(def teacher-candidates [
  {:model-id "qwen3-32b-awq"
   :endpoint-url "http://192.168.1.22:11434/v1"
   :license "apache-2.0"
   :throughput-tok-per-sec 8.0
   :rationale "primary teacher per ADR §2 (Apache 2.0, JP/code strong, mid throughput)"}
  {:model-id "llama3.3:70b"
   :endpoint-url "http://192.168.1.22:11434/v1"
   :license "llama3-community"
   :throughput-tok-per-sec 1.18
   :rationale "strong but very slow; use for ≤200-prompt STEM/coding bursts only"}
  {:model-id "llama3.2:3b"
   :endpoint-url "http://192.168.1.22:11434/v1"
   :license "llama3-community"
   :throughput-tok-per-sec 83.0
   :rationale "same scale as baien; marginal teacher signal — fallback only"}
  {:model-id "gemma3:4b"
   :endpoint-url "http://192.168.1.17:4000/v1"
   :license "gemma-terms-of-use"
   :throughput-tok-per-sec nil
   :rationale "multi-node parallel via judah gateway; restrictive license — review before publish"}])

;; TODO: port-failed unit select_teacher (/var/folders/px/b63lssbx5056kq_1t6pvc1f80000gn/T/tmpcetefg5s/scratch.clj:3:8: er)
;; def select_teacher(state: DistillState) -> DistillState:
;;     state.setdefault("notes", []).append("[select_teacher] choosing per ADR §2 rule")
;; 
;;     targets = {c.name for c in state["weak_categories"]}
;;     has_stem_or_coding = bool(targets & {"GPQA Diamond", "Reasoning"})
;;     has_multilingual = "Multilingual" in targets
;; 
;;     chosen: TeacherSpec | None = None
;;     for cand in TEACHER_CANDIDATES:
;;         if cand.throughput_tok_per_sec is None:
;;             # unverified throughput — try only if nothing else qualifies
;;             continue
;;         if cand.throughput_tok_per_sec < 5.0 and not has_stem_or_coding:
;;             continue  # too slow to be worth except for STEM
;;         if cand.model_id.startswith("qwen") and not has_multilingual:
;;             # prefer qwen for multilingual; fine for general too — keep
;;             pass
;;         chosen = cand
;;         break
;; 
;;     if chosen is None:
;;         # fallback to first qualifying regardless
;;         for cand in TEACHER_CANDIDATES:
;;             if cand.throughput_tok_per_sec is not None:
;;                 chosen = cand
;;                 break
;; 
;;     if chosen is None:
;;         state["notes"].append("[select_teacher] no qualifying teacher — abort")
;;         state["decision"] = "abort"
;;         return state
;; 
;;     state["teacher"] = chosen
;;     state["notes"].append(
;;         f"[select_teacher] chose {chosen.model_id} ({chosen.license}) "
;;         f"@ {chosen.endpoint_url} — {chosen.rationale}"
;;     )
;;     return state
(defn select-teacher [& _]
  (throw (ex-info "TODO: port-failed" {:from "select_teacher"})))

