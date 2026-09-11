;; ported from 70-tools/baien-moemoekyun-train/scripts/bench_trained_mbppplus.py
;; — real 1:1 port replacing the unit_refactor stage-0 "TODO: port-failed" stub.
;; bench_trained_mbppplus.py — moemoekyun ckpt MBPP+ bench via HF transformers.
;;
;; The pure prompt/extraction helpers (make-instruction, extract-code) are ported
;; faithfully. The Python main() is a torch/transformers/datasets harness (model
;; load + generate + subprocess exec); that is host-only ML I/O that cannot run
;; without those libraries, so its __main__ demo is intentionally OMITTED. The
;; remaining I/O-shaped helpers (envelope build + jsonl append) are ported as
;; pure data + a #?(:clj ...) file-append edge so the file LOADS cleanly.
(ns baien-moemoekyun-train.scripts.bench-trained-mbppplus
  (:require [clojure.string :as str]))

;; ── make_instruction ─────────────────────────────────────────────────────────
;; def make_instruction(description, test_list):
;;     first_test = test_list[0] if test_list else ""
;;     return (f"Write a Python function ... ```python code block, no explanations.")
(defn make-instruction
  [description test-list]
  (let [first-test (if (seq test-list) (first test-list) "")]
    (str "Write a Python function that satisfies the following description.\n\n"
         "Description: " description "\n\n"
         "Example test:\n" first-test "\n\n"
         "Output only the Python function in a ```python code block, no explanations.")))

;; ── extract_code ─────────────────────────────────────────────────────────────
;; def extract_code(gen_text):
;;     if "```" in gen_text:
;;         m = re.search(r"```(?:python|py)?\s*\n?(.*?)(?:\n```|```|$)", gen_text, re.DOTALL)
;;         if m: gen_text = m.group(1)
;;     ... line-walk extracting the def/import block ...
(def ^:private code-fence-re
  ;; Python: r"```(?:python|py)?\s*\n?(.*?)(?:\n```|```|$)" with re.DOTALL.
  ;; (?s) = DOTALL; .*? non-greedy; the trailing $ alternative requires multiline
  ;; not be set so $ is end-of-input (Python default for $ w/o re.MULTILINE matches
  ;; end-of-string or just-before-final-newline). We match the same shape.
  #?(:clj  (re-pattern "(?s)```(?:python|py)?\\s*\\n?(.*?)(?:\\n```|```|$)")
     :cljs (re-pattern "```(?:python|py)?\\s*\\n?([\\s\\S]*?)(?:\\n```|```|$)")))

(defn- starts-with-any?
  "True if (lstrip-aware where noted) s starts with any of prefixes."
  [^String s prefixes]
  (boolean (some #(str/starts-with? s %) prefixes)))

(defn extract-code
  [gen-text]
  (let [gen-text (if (str/includes? gen-text "```")
                   (if-let [m (re-find code-fence-re gen-text)]
                     (nth m 1)
                     gen-text)
                   gen-text)
        ;; Python str.splitlines(): split on line boundaries, no trailing empty
        ;; element for a trailing newline. clojure (str/split-lines) matches.
        lines (str/split-lines gen-text)]
    (loop [lines lines, out [], in-def false]
      (if (empty? lines)
        (str/join "\n" out)
        (let [ln (first lines)]
          (if-not in-def
            (let [enter? (starts-with-any? (str/triml ln) ["def " "import " "from "])]
              (recur (rest lines) (conj out ln) (or in-def enter?)))
            ;; in_def branch
            (if (and (seq ln)
                     (not (starts-with-any? ln [" " "\t" "#"]))
                     (not (starts-with-any? (str/triml ln) ["def " "import " "from " "@"])))
              (str/join "\n" out)            ; break
              (recur (rest lines) (conj out ln) in-def))))))))

;; ── envelope (the result record main() appends to the jsonl) ──────────────────
;; Pure data builder; the Python main() builds this dict then json.dumps-appends it.
(defn build-envelope
  "Construct the bench result envelope (string-keyed, json.dumps shape).
  `now-iso` is the caller-supplied UTC ISO timestamp (datetime.now(timezone.utc).isoformat())."
  [{:keys [now-iso model checkpoint n-done n-pass pass1 baseline-pass1
           delta-pp total-wall n-experts n-moe]}]
  {"schema"             "etzhayyim.baien.bench.v1"
   "ran_at"             now-iso
   "host"               "runpod-rtx5090"
   "model"              (str model " + moemoekyun MoE residual (ckpt " checkpoint ")")
   "harness"            "HF transformers + chat template + mbppplus extract_code + exec subprocess"
   "task"               "mbppplus_chat_trained"
   "n_tasks_evaluated"  n-done
   "n_pass"             n-pass
   "pass1"              pass1
   "baseline_pass1"     baseline-pass1
   "delta_pp"           delta-pp
   "wall_sec"           total-wall
   "n_experts"          n-experts
   "n_moe_layers"       n-moe
   "checkpoint"         checkpoint})

;; The torch/transformers/datasets main() generation+exec harness is host-only ML
;; I/O and is intentionally not ported (no runnable equivalent on this classpath).
