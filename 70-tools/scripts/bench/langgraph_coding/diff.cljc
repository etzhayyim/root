(ns scripts.bench.langgraph-coding.diff
  "Compute the pass-rate delta between two langgraph-coding result files.
  Clojure port of `diff.py` (ADR-2605250400 §1.5). Used by the
  gemma-coder-distill evaluate node to gate commit.

  Each result file is NDJSON — one JSON object per line, keyed on `\"id\"`,
  carrying `\"passed\"` (truthy → 1) and an optional `\"category\"` (default
  `\"?\"`). The delta is computed over the IDs common to both files:

    delta_pp = 100 * (new_pass - base_pass) / n

  plus a per-category breakdown. The report wording + the `:+.1f`pp number
  format + the exit-code contract (0 ok / 1 gate-fail / 2 no-overlap) are
  verbatim from the Python so any caller that string-matches the report holds.

  Convention parity (root CLAUDE.md / kanjo analyze.cljc / bond.cljc):
  result rows are maps with STRING JSON keys (`\"id\"`, `\"passed\"`,
  `\"category\"`) — JSON keys from the files stay strings; internal opts use
  kebab keyword keys. Pure delta-computation fns; JSON read + stdout/exit at
  the #?(:clj) edge. JSON is parsed through a statically declared host codec."
  (:require [clojure.string :as str]
            [clojure.set :as set]
            #?(:clj [clojure.java.io :as io])
            #?(:clj [cheshire.core :as json])))

;; ── pure: truthiness + summation (mirror Python int(row["passed"])) ──────────

(defn passed?->int
  "Python `int(x)` over a result row's `\"passed\"`: 1 when truthy, 0 otherwise.
  In Python a missing key would KeyError; here a missing/`nil`/`false`/`0`/empty
  value is 0 and any other value (true / non-zero number / non-empty) is 1 —
  which matches `int(bool-or-number)` for the JSON values these files carry."
  [v]
  (cond
    (nil? v)     0
    (boolean? v) (if v 1 0)
    (number? v)  (if (zero? v) 0 1)
    (string? v)  (if (str/blank? v) 0 1)
    :else 1))

(defn index-by-id
  "Rows → {id row}, last wins on duplicate id (mirrors Python `out[row[\"id\"]] = row`)."
  [rows]
  (reduce (fn [m r] (assoc m (get r "id") r)) {} rows))

(defn common-ids
  "Set of ids present in BOTH indexed maps (Python `set(base) & set(new)`)."
  [base new]
  (set/intersection (set (keys base)) (set (keys new))))

(defn overall-delta
  "Pure overall computation over an explicit id set. Returns
   {:base-pass int :new-pass int :n int :delta-pp double}.
   delta-pp = 100*(new-pass - base-pass)/n. Caller guarantees (seq common)."
  [base new common]
  (let [ids       (seq common)
        base-pass (reduce + 0 (map #(passed?->int (get (get base %) "passed")) ids))
        new-pass  (reduce + 0 (map #(passed?->int (get (get new %)  "passed")) ids))
        n         (count common)]
    {:base-pass base-pass
     :new-pass  new-pass
     :n         n
     :delta-pp  (/ (* 100.0 (- new-pass base-pass)) n)}))

(defn by-category
  "Per-category breakdown over the common ids. Category is taken from the
  BASELINE row's `\"category\"` (default `\"?\"`), mirroring the Python.
  Returns {category {:base int :new int :total int}} — kebab keys internal."
  [base new common]
  (reduce
   (fn [acc id]
     (let [cat (get (get base id) "category" "?")
           a   (get acc cat {:base 0 :new 0 :total 0})]
       (assoc acc cat
              {:base  (+ (:base a)  (passed?->int (get (get base id) "passed")))
               :new   (+ (:new a)   (passed?->int (get (get new id)  "passed")))
               :total (+ (:total a) 1)})))
   {} common))

;; ── pure: Python-exact number formatting ─────────────────────────────────────

(defn- round-half-even-1
  "round(x*10)/10 with HALF_EVEN — matches CPython's `format(x, '.1f')` which
  rounds the actual double to 1 fractional place, ties to even."
  [x]
  #?(:clj (.doubleValue (.setScale (bigdec (double x)) 1 java.math.RoundingMode/HALF_EVEN))
     :cljs (let [r (js/Math.round (* (double x) 10))
                 ;; emulate ties-to-even for the *.?5 boundary
                 r (if (= 0.5 (- (* (double x) 10) (Math/floor (* (double x) 10))))
                     (let [f (Math/floor (* (double x) 10))]
                       (if (even? f) f (+ f 1)))
                     r)]
             (/ r 10))))

(defn fmt-pp
  "Python `f\"{x:+.1f}\"` — always-signed, 1 decimal, ties-to-even. e.g.
  0.0→\"+0.0\", 33.333→\"+33.3\", -16.666→\"-16.7\", 18.75→\"+18.8\"."
  [x]
  (let [r   (round-half-even-1 x)
        ;; format the rounded magnitude to exactly 1 decimal, prepend our own sign
        mag (Math/abs r)
        body #?(:clj (format "%.1f" mag) :cljs (.toFixed mag 1))
        sign (if (< r 0) "-" "+")]
    (str sign body)))

(defn- lpad-cat
  "Python `f\"{cat:20s}\"` — left-justified to width 20 (pad right with spaces;
  never truncates)."
  [cat]
  (let [s (str cat)]
    (if (>= (count s) 20) s (str s (apply str (repeat (- 20 (count s)) \space))))))

;; ── pure: the report (stdout lines) + exit code, given a loaded pair ─────────

(defn diff-report
  "Pure compute → {:exit int :out [str…] :err [str…]} for an indexed
  baseline/new pair + a `gate-pp` threshold (double, default 0.0).
  Mirrors `diff.py main()` exactly (lines, order, format, exit codes)."
  ([base new] (diff-report base new 0.0))
  ([base new gate-pp]
   (let [common (common-ids base new)]
     (if (empty? common)
       {:exit 2 :out [] :err ["[diff] no overlap between baseline and new"]}
       (let [{:keys [base-pass new-pass n delta-pp]} (overall-delta base new common)
             cats (by-category base new common)
             out  (into
                   [(str "overall: baseline=" base-pass "/" n
                         " new=" new-pass "/" n
                         " delta=" (fmt-pp delta-pp) "pp")]
                   (for [[cat {:keys [base new total]}] (sort-by key cats)]
                     (str "  " (lpad-cat cat) ": " base "/" total " → " new "/" total
                          "  (" (fmt-pp (/ (* 100.0 (- new base)) total)) "pp)")))]
         (if (< delta-pp gate-pp)
           {:exit 1 :out out
            :err [(str "\nGATE FAIL: delta " (fmt-pp delta-pp)
                       "pp < required " gate-pp "pp")]}
           {:exit 0 :out out :err []}))))))

;; ── I/O edge: NDJSON load, argparse, -main ──────────────────────────────────

#?(:clj
   (defn load
     "Read an NDJSON result file → {id row}. One JSON object per non-blank line,
     keyed on `\"id\"` (string JSON keys preserved)."
     [path]
     (with-open [r (io/reader path)]
       (->> (line-seq r)
            (remove str/blank?)
            (mapv #(json/parse-string % false)) ;; false → keep JSON keys as STRINGS
            index-by-id))))

#?(:clj
   (defn parse-args
     "argparse → opts (no eval). Recognizes --baseline X / --new X / --gate-pp F.
     Returns {:baseline str :new str :gate-pp double} or throws ex-info on a
     missing required flag / unknown arg (mirrors argparse's required + error)."
     [args]
     (loop [a args, opts {:gate-pp 0.0}]
       (if (empty? a)
         (do
           (when-not (:baseline opts) (throw (ex-info "the following arguments are required: --baseline" {:arg "--baseline"})))
           (when-not (:new opts)      (throw (ex-info "the following arguments are required: --new" {:arg "--new"})))
           opts)
         (let [[k v & more] a]
           (case k
             "--baseline" (recur more (assoc opts :baseline v))
             "--new"      (recur more (assoc opts :new v))
             "--gate-pp"  (recur more (assoc opts :gate-pp (Double/parseDouble v)))
             (throw (ex-info (str "unrecognized arguments: " k) {:arg k}))))))))

#?(:clj
   (defn -main
     "CLI entry. Loads both files, prints the report to stdout, gate failures /
     no-overlap to stderr, and exits with 0 / 1 / 2 (Python parity)."
     [& args]
     (let [{:keys [baseline new gate-pp]} (parse-args args)
           {:keys [exit out err]} (diff-report (load baseline) (load new) gate-pp)]
       (doseq [l out] (println l))
       (doseq [l err] (binding [*out* *err*] (println l)))
       (flush)
       (System/exit exit))))
