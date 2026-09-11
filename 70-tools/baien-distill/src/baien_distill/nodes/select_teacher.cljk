(ns baien-distill.nodes.select-teacher
  "(2) select_teacher: pick an on-fleet OSS teacher meeting ADR constraints.

  1:1 Clojure port of `nodes/select_teacher.py` (ADR-2605231300 §2).

  Constraints (all must hold):
  - OSS license (Apache / MIT / Llama-Community); no commercial API
  - Endpoint is on etzhayyim fleet LAN (not external)
  - Verified throughput >= 8 tok/s (for data-gen feasibility)
  - Significantly stronger than baien on the target categories

  House style: pure fns; data stays string-keyed maps; the Python `DistillState`
  TypedDict and the `TeacherSpec`/`CategorySpec` dataclasses are represented as
  string-keyed maps so the port is host-portable .cljc with no Python dependency.
  The Python `__main__`/module demo is omitted (none present)."
  (:require [clojure.set :as set]))

;; Candidates derived from fleet.toml + ADR-2605202345 + recent verification.
;; "throughput-tok-per-sec" is from manual measurement; nil means unverified.
(def teacher-candidates
  [{"model_id" "qwen3-32b-awq"
    "endpoint_url" "http://192.168.1.22:11434/v1"  ; EVO-X2 ollama
    "license" "apache-2.0"
    "throughput_tok_per_sec" 8.0                    ; estimated; verify on first run
    "rationale" "primary teacher per ADR §2 (Apache 2.0, JP/code strong, mid throughput)"}
   {"model_id" "llama3.3:70b"
    "endpoint_url" "http://192.168.1.22:11434/v1"
    "license" "llama3-community"
    "throughput_tok_per_sec" 1.18
    "rationale" "strong but very slow; use for ≤200-prompt STEM/coding bursts only"}
   {"model_id" "llama3.2:3b"
    "endpoint_url" "http://192.168.1.22:11434/v1"
    "license" "llama3-community"
    "throughput_tok_per_sec" 83.0
    "rationale" "same scale as baien; marginal teacher signal — fallback only"}
   {"model_id" "gemma3:4b"
    "endpoint_url" "http://192.168.1.17:4000/v1"   ; judah LiteLLM gateway
    "license" "gemma-terms-of-use"
    "throughput_tok_per_sec" nil
    "rationale" "multi-node parallel via judah gateway; restrictive license — review before publish"}])

(defn- append-note
  "Faithful port of `state.setdefault(\"notes\", []).append(msg)` and
  `state[\"notes\"].append(msg)` — appends to the (vector) notes list, creating it."
  [state msg]
  (update state "notes" (fnil conj []) msg))

(defn select-teacher
  "Port of `select_teacher(state)`: choose an on-fleet OSS teacher per ADR §2.

  `state` is a string-keyed map; `weak_categories` is a seq of string-keyed
  CategorySpec maps (each with a \"name\")."
  [state]
  (let [state (append-note state "[select_teacher] choosing per ADR §2 rule")
        targets (set (map #(get % "name") (get state "weak_categories")))
        has-stem-or-coding (boolean (seq (set/intersection targets #{"GPQA Diamond" "Reasoning"})))
        has-multilingual (contains? targets "Multilingual")
        ;; First pass: first candidate meeting the ADR rule.
        chosen (loop [cands teacher-candidates]
                 (when-let [cand (first cands)]
                   (let [tput (get cand "throughput_tok_per_sec")]
                     (cond
                       ;; unverified throughput — try only if nothing else qualifies
                       (nil? tput) (recur (rest cands))
                       ;; too slow to be worth except for STEM
                       (and (< tput 5.0) (not has-stem-or-coding)) (recur (rest cands))
                       ;; (prefer qwen for multilingual; fine for general too — keep)
                       :else cand))))
        ;; Fallback: first candidate with any verified throughput.
        chosen (or chosen
                   (loop [cands teacher-candidates]
                     (when-let [cand (first cands)]
                       (if (some? (get cand "throughput_tok_per_sec"))
                         cand
                         (recur (rest cands))))))]
    (if (nil? chosen)
      (-> state
          (append-note "[select_teacher] no qualifying teacher — abort")
          (assoc "decision" "abort"))
      (-> state
          (assoc "teacher" chosen)
          (append-note (str "[select_teacher] chose " (get chosen "model_id")
                            " (" (get chosen "license") ") "
                            "@ " (get chosen "endpoint_url") " — " (get chosen "rationale")))))))
