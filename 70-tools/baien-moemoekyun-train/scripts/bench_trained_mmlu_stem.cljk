;; ported from 70-tools/baien-moemoekyun-train/scripts/bench_trained_mmlu_stem.py
;; — real 1:1 port replacing the unit_refactor stage-0 "TODO: port-failed" stub.
;;
;; The pure helpers (make-instruction, extract-answer) are ported faithfully.
;; The Python main() is a torch/transformers/datasets harness (model load +
;; generate); that is host-only ML I/O with no runnable equivalent here, so its
;; __main__ demo is intentionally OMITTED. The result envelope is ported as a pure
;; data builder so the file LOADS cleanly.
(ns baien-moemoekyun-train.scripts.bench-trained-mmlu-stem
  (:require [clojure.string :as str]))

;; ── make_instruction ─────────────────────────────────────────────────────────
;; def make_instruction(question, choices):
;;     options = "\n".join(f"{chr(65+i)}. {c}" for i, c in enumerate(choices))
;;     return (f"Answer the following multiple-choice STEM question.\n\n"
;;             f"Question: {question}\n\nOptions:\n{options}\n\nAnswer with just the letter A, B, C, or D.")
(defn make-instruction
  [question choices]
  (let [options (str/join "\n"
                          (map-indexed
                           (fn [i c] (str (char (+ 65 i)) ". " c))
                           choices))]
    (str "Answer the following multiple-choice STEM question.\n\n"
         "Question: " question "\n\nOptions:\n" options
         "\n\nAnswer with just the letter A, B, C, or D.")))

;; ── extract_answer ───────────────────────────────────────────────────────────
;; def extract_answer(gen_text):
;;     for pat in [r"\b([ABCD])\b", r"(?:answer\s*[:=]\s*|is\s+)([ABCD])", r"\(([ABCD])\)"]:
;;         m = re.search(pat, gen_text, re.IGNORECASE)
;;         if m: return ord(m.group(1).upper()) - ord("A")
;;     return None
(def ^:private answer-patterns
  ;; re.IGNORECASE -> (?i). Each pattern keeps capture group 1 = the letter.
  [#"(?i)\b([ABCD])\b"
   #"(?i)(?:answer\s*[:=]\s*|is\s+)([ABCD])"
   #"(?i)\(([ABCD])\)"])

(defn extract-answer
  "Returns the 0-based answer index (A=0..D=3) of the first matching pattern, or nil."
  [gen-text]
  (loop [pats answer-patterns]
    (if (empty? pats)
      nil
      (if-let [m (re-find (first pats) gen-text)]
        (let [letter (-> (nth m 1) str/upper-case (.charAt 0))]
          (- (int letter) (int \A)))
        (recur (rest pats))))))

;; ── envelope (the result record main() appends to the jsonl) ──────────────────
(defn build-envelope
  "Construct the bench result envelope (string-keyed, json.dumps shape).
  `now-iso` is the caller-supplied UTC ISO timestamp."
  [{:keys [now-iso checkpoint n-done n-correct accuracy baseline-accuracy
           delta-pp total-wall]}]
  {"schema"             "etzhayyim.baien.bench.v1"
   "ran_at"             now-iso
   "task"               "mmlu_stem_chat_trained"
   "n_tasks_evaluated"  n-done
   "n_correct"          n-correct
   "accuracy"           accuracy
   "baseline_accuracy"  baseline-accuracy
   "delta_pp"           delta-pp
   "wall_sec"           total-wall
   "checkpoint"         checkpoint})

;; The torch/transformers/datasets main() generation harness is host-only ML I/O
;; and is intentionally not ported (no runnable equivalent on this classpath).
