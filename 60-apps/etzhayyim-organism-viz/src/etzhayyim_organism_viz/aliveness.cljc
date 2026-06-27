;; ported from 60-apps/etzhayyim-organism-viz/src/etzhayyim_organism_viz/aliveness.py
;; — faithful clj port of the aliveness functional A(t) = ⟨M,D,C,P,G⟩ (5-tuple,
;; NOT a scalar — §1.15 anti-eschatology: no scalar sum, no trade-offs between
;; dimensions). Pure math (Shannon entropy / Pearson correlation / axis-Δ motion /
;; tended-cell ratio) lives in cljc; host file/dir I/O lives behind #?(:clj ...),
;; mirroring pruning.cljc. ns drops the "src" source-root and mirrors the Python
;; module etzhayyim_organism_viz.aliveness.
(ns etzhayyim-organism-viz.aliveness
  "aliveness.py — Aliveness functional A(t) = ⟨M,D,C,P,G⟩.

    M = motion       — Σ |Δ_axis| over recent cycles + 0.3·creation/day
    D = diversity    — Shannon entropy over distinct cell types (nats)
    C = coupling     — mean pairwise Pearson correlation of axis trajectories
    P = pruning      — tended_cells / total_cells (bonsai-tending ratio)
    G = generational — MGI proxy from LANDS.md/MEMBERS.md + gen-mark lift

  We DO NOT compute a scalar sum — that would re-introduce eschatology by allowing
  trade-offs between dimensions. The dashboard renders 5 dials; the operator reads
  all five. House style: pure fns in cljc, host I/O at the #?(:clj) edge, ex-info
  for errors. (The Python module-level helpers map 1:1 to fns below.)"
  (:require [clojure.string :as str]))

;; ── pure: rounding (Python round(x, n), round-half-to-even) ──────────────────
(defn round-n
  "Round x to n decimals. Matches Python round(x, n) (round-half-to-even / banker's)."
  [x n]
  #?(:clj  (-> (java.math.BigDecimal/valueOf (double x))
               (.setScale (int n) java.math.RoundingMode/HALF_EVEN)
               (.doubleValue))
     :cljs (let [p (js/Math.pow 10 n)
                 scaled (* (double x) p)
                 fl     (js/Math.floor scaled)
                 diff   (- scaled fl)
                 r      (cond
                          (< diff 0.5) fl
                          (> diff 0.5) (inc fl)
                          (even? fl)   fl
                          :else        (inc fl))]
             (/ r p))
     :default (/ (Math/round (* (double x) (Math/pow 10.0 n))) (Math/pow 10.0 n))))

;; ── pure: AliveTuple ─────────────────────────────────────────────────────────
(defn alive-tuple
  "Build the aliveness 5-tuple map (mirrors the Python @dataclass AliveTuple)."
  ([m d c p g] (alive-tuple m d c p g "" []))
  ([m d c p g timestamp notes]
   {:M m :D d :C c :P p :G g :timestamp timestamp :notes (vec notes)}))

(defn as-dict
  "AliveTuple.as_dict() — string-keyed map with M/D/C/P/G rounded to 4 dp."
  [a]
  {"M_motion"       (round-n (:M a) 4)
   "D_diversity"    (round-n (:D a) 4)
   "C_coupling"     (round-n (:C a) 4)
   "P_pruning"      (round-n (:P a) 4)
   "G_generational" (round-n (:G a) 4)
   "timestamp"      (:timestamp a)
   "notes"          (vec (:notes a))})

(defn in-healthy-band
  "in_healthy_band(a) — per-dimension band membership (NOT a scalar pass/fail)."
  [a]
  {"M" (> (:M a) 0.5)
   "D" (> (:D a) 1.5)
   "C" (and (<= 0.2 (:C a)) (<= (:C a) 0.7))
   "P" (and (<= 0.5 (:P a)) (<= (:P a) 1.0))   ; bonsai-tending ratio
   "G" (> (:G a) 1.0)})

;; ── pure: cycle parsing (the _AXIS_ROW regex) ────────────────────────────────
(def ^:private axis-row-re
  ;; ^| n | **Name** … | **score / 10  (MULTILINE). Java/JS regex syntax differs
  ;; only in the inline-flag form; both branches encode the same grammar.
  #?(:clj  #"(?m)^\|\s*\d+\s*\|\s*\*{0,2}([A-Za-z][A-Za-z\- ]*[A-Za-z])\*{0,2}[^|]*\|\s*\*{0,2}(\d+)\s*/\s*10"
     :cljs (js/RegExp. "^\\|\\s*\\d+\\s*\\|\\s*\\*{0,2}([A-Za-z][A-Za-z\\- ]*[A-Za-z])\\*{0,2}[^|]*\\|\\s*\\*{0,2}(\\d+)\\s*/\\s*10" "gm")))

(defn parse-axis-table
  "Parse an observation-cycle body → {axis-name-lowercased score-int}.
  Mirrors the Python `for name, score in _AXIS_ROW.findall(body)` loop."
  [body]
  #?(:clj  (reduce (fn [m [_ name score]]
                     (assoc m (str/lower-case (str/trim name)) (Integer/parseInt score)))
                   {}
                   (re-seq axis-row-re body))
     :cljs (loop [m {}]
             ;; re-seq with a stateful global RegExp; simplest is a manual scan.
             (let [acc (atom {})]
               (.replace body axis-row-re
                         (fn [_ name score]
                           (swap! acc assoc (str/lower-case (str/trim name)) (js/parseInt score 10))
                           ""))
               (merge m @acc)))))

;; ── pure: the five dimensions, computed from already-parsed data ─────────────
(defn shannon-entropy
  "Shannon entropy (nats) over a seq of positive counts. -Σ (c/total) ln(c/total)."
  [counts]
  (let [total (double (reduce + 0 counts))]
    (if (zero? total)
      0.0
      (- (reduce (fn [acc c]
                   (let [p (/ (double c) total)]
                     (+ acc (* p #?(:clj (Math/log p) :cljs (js/Math.log p))))))
                 0.0 counts)))))

(defn pearson
  "Pearson correlation of xs/ys, or nil when undefined (n<2 or a flat series)."
  [xs ys]
  (let [n (count xs)]
    (when (>= n 2)
      (let [mx (/ (reduce + 0.0 xs) n)
            my (/ (reduce + 0.0 ys) n)
            num (reduce + 0.0 (map (fn [a b] (* (- a mx) (- b my))) xs ys))
            sq  (fn [s m] #?(:clj (Math/sqrt (reduce + 0.0 (map #(let [d (- % m)] (* d d)) s)))
                             :cljs (js/Math.sqrt (reduce + 0.0 (map #(let [d (- % m)] (* d d)) s)))))
            dx (sq xs mx)
            dy (sq ys my)]
        (when (and (pos? dx) (pos? dy))
          (/ num (* dx dy)))))))

(defn mean
  "Arithmetic mean; 0.0 for an empty seq (caller decides emptiness semantics)."
  [xs]
  (if (seq xs) (/ (reduce + 0.0 xs) (count xs)) 0.0))

(defn axis-motion
  "Axis-trajectory motion from parsed cycles `[[n axes] ...]` (sorted).
  Returns [axis-M transitions]: mean |Δ| over union of axis keys across the last
  (window+1) cycles. Mirrors aliveness.motion's axis term (creation term is added
  by `motion`, the I/O fn)."
  [cycles window]
  (if (< (count cycles) 2)
    [0.0 0]
    (let [recent (vec (take-last (inc window) cycles))
          deltas (for [[[_ a] [_ b]] (map vector recent (rest recent))
                       k (into #{} (concat (keys a) (keys b)))]
                   (#?(:clj Math/abs :cljs js/Math.abs)
                    (double (- (get b k 0) (get a k 0)))))]
      (if (seq deltas)
        [(mean deltas) (dec (count recent))]
        [0.0 0]))))

(defn coupling-from
  "Mean pairwise Pearson correlation across axis trajectories of parsed `cycles`.
  Returns [C n-pairs]; C=0.0/n=0 when <3 cycles (undefined)."
  [cycles]
  (if (< (count cycles) 3)
    [0.0 0]
    (let [axis-keys (sort (into #{} (mapcat (comp keys second) cycles)))
          series (into {} (map (fn [k] [k (mapv (fn [[_ a]] (double (get a k 0))) cycles)]) axis-keys))
          corrs (for [i (range (count axis-keys))
                      j (range (inc i) (count axis-keys))
                      :let [r (pearson (series (nth axis-keys i)) (series (nth axis-keys j)))]
                      :when (and r (not (#?(:clj Double/isNaN :cljs js/isNaN) r)))]
                  r)]
      (if (seq corrs)
        [(mean corrs) (count corrs)]
        [0.0 0]))))

(defn generational-from
  "MGI proxy: base 1.0 when LANDS present, +0.05 per 10 gen-marks (NEVER caps —
  non-eschatological). Returns G (or nil meaning 'LANDS missing → undefined')."
  [lands? gen-marks]
  (when lands?
    (+ 1.0 (* 0.05 (quot gen-marks 10)))))

;; ── host file/dir I/O (behind #?(:clj ...), mirroring pruning.cljc) ──────────
#?(:clj
   (do
     (require '[clojure.java.io :as io])

     (defn- ^java.io.File as-file [p] (io/file (str p)))

     (defn- slurp-safe
       "read_text(errors='ignore') analogue — empty string on any I/O error."
       [f]
       (try (slurp f) (catch java.io.IOException _ "") (catch java.io.FileNotFoundException _ "")))

     (defn- glob-sorted
       "Immediate files of `dir` whose name matches `re`, sorted by filename
       (mirrors Python sorted(dir.glob(...)))."
       [dir re]
       (let [^java.io.File d (as-file dir)
             kids (.listFiles d)]
         (->> (or kids (make-array java.io.File 0))
              (filter #(.isFile ^java.io.File %))
              (filter #(re-find re (.getName ^java.io.File %)))
              (sort-by #(.getName ^java.io.File %)))))

     (def ^:private cycle-file-re #"-cycle-(\d+)\.md$")

     (defn read-cycles
       "_read_cycles(observations_dir) → [[cycle-number axes-map] ...] sorted by filename."
       [obs-dir]
       (vec
        (keep (fn [^java.io.File f]
                (when-let [m (re-find cycle-file-re (.getName f))]
                  (let [axes (parse-axis-table (slurp-safe f))]
                    (when (seq axes)
                      [(Integer/parseInt (second m)) axes]))))
              (glob-sorted obs-dir cycle-file-re))))

     (defn- list-dirs [parent]
       (let [^java.io.File f (as-file parent)
             kids (.listFiles f)]
         (->> (or kids (make-array java.io.File 0))
              (filter #(.isDirectory ^java.io.File %)))))

     (defn motion
       "motion(observations_dir, repo, window=7) → [M notes].
       M = axis_Δ_per_cycle + 0.3·creation/day (creation only when repo given —
       filename-dated ADRs + cycle obs in the last `window` days)."
       ([obs-dir] (motion obs-dir nil 7))
       ([obs-dir repo] (motion obs-dir repo 7))
       ([obs-dir repo window]
        (let [cycles (read-cycles obs-dir)
              [axis-m transitions] (axis-motion cycles window)
              ;; creation rate (filename-encoded YYMMDDHHMM[SS] timestamps)
              ts-re #"^(\d{10,12})[-_.]"
              now (/ (double (System/currentTimeMillis)) 1000.0)
              cutoff (- now (* window 86400))
              fname-ts (fn [^java.io.File p]
                         (when-let [m (re-find ts-re (.getName p))]
                           (let [raw (second m)
                                 fmt (case (count raw) 10 "yyMMddHHmm" 12 "yyMMddHHmmss" nil)]
                             (when fmt
                               (try
                                 (let [sdf (doto (java.text.SimpleDateFormat. fmt)
                                             (.setTimeZone (java.util.TimeZone/getTimeZone "GMT+09:00")))]
                                   (/ (double (.getTime (.parse sdf raw))) 1000.0))
                                 (catch java.text.ParseException _ nil))))))
              count-recent (fn [dir re]
                             (->> (glob-sorted dir re)
                                  (keep fname-ts)
                                  (filter #(> % cutoff))
                                  count))
              new-adrs (if repo
                         (let [adr-dir (as-file (str repo "/90-docs/adr"))]
                           (if (.isDirectory adr-dir) (count-recent adr-dir #"\.md$") 0))
                         0)
              new-obs (if (and repo (.isDirectory (as-file obs-dir)))
                        (count-recent obs-dir cycle-file-re)
                        0)
              creation-per-day (/ (double (+ new-adrs new-obs)) (max 1 window))
              m (+ axis-m (* 0.3 creation-per-day))]
          [m [(format "motion: axis_Δ=%.3f/cycle (%d transitions) + 0.3·creation=%.2f/day → M=%.3f"
                      axis-m transitions creation-per-day m)
              (format "  creation last %dd (filename-dated): %d ADR + %d cycle obs"
                      window new-adrs new-obs)]])))

     (defn diversity
       "diversity(repo) → [H notes]. Shannon entropy over distinct cell dirs (八百万)."
       [repo]
       (let [cells (as-file (str repo "/20-actors/kotodama/cells"))]
         (if-not (.isDirectory cells)
           [0.0 ["diversity: cells dir missing"]]
           (let [n (count (list-dirs cells))]
             (if (zero? n)
               [0.0 ["diversity: no cells"]]
               (let [h (shannon-entropy (repeat n 1))]
                 [h [(format "diversity: H = %.3f nats over %d distinct cells (八百万)" h n)]]))))))

     (defn coupling
       "coupling(observations_dir) → [C notes]. Mean pairwise Pearson r across axes."
       [obs-dir]
       (let [cycles (read-cycles obs-dir)]
         (if (< (count cycles) 3)
           [0.0 ["coupling: <3 cycles → undefined; returning 0"]]
           (let [[c npairs] (coupling-from cycles)]
             (if (zero? npairs)
               [0.0 ["coupling: no valid correlations"]]
               [c [(format "coupling: mean pairwise r = %.3f across %d axis pairs" c npairs)]])))))

     (defn pruning
       "pruning(repo) → [P notes]. Bonsai-tending ratio: cells with cell.py +
       docstring + >200 bytes / total. mtime-independent (content-based)."
       [repo]
       (let [cells (as-file (str repo "/20-actors/kotodama/cells"))]
         (if-not (.isDirectory cells)
           [0.0 ["pruning: cells dir missing"]]
           (let [ds (list-dirs cells)
                 total (count ds)
                 tended (count
                         (filter (fn [^java.io.File d]
                                   (let [cell-py (as-file (str (.getPath d) "/cell.py"))]
                                     (and (.exists cell-py)
                                          (let [txt (slurp-safe cell-py)]
                                            (and (str/includes? txt "\"\"\"")
                                                 (> (count txt) 200))))))
                                 ds))]
             (if (zero? total)
               [0.0 ["pruning: 0 cells"]]
               (let [p (/ (double tended) total)]
                 [p [(format "pruning: %d/%d cells with cell.py + docstring + >200 bytes → P=%.3f"
                             tended total p)]]))))))

     (defn generational
       "generational(repo) → [G notes]. MGI proxy from LANDS.md/MEMBERS.md presence
       + gen-mark lift over _observations cycle bodies."
       [repo]
       (let [lands (as-file (str repo "/LANDS.md"))
             members (as-file (str repo "/MEMBERS.md"))]
         (if-not (.exists lands)
           [0.0 ["generational: LANDS.md missing → MGI undefined"]]
           (let [notes (cond-> ["LANDS.md present (inalienable inheritance roster)"]
                         (.exists members) (conj "MEMBERS.md present (multi-gen roster)"))
                 obs (as-file (str repo "/_observations"))
                 count-sub (fn [^String hay ^String needle]
                             (loop [from 0 n 0]
                               (let [i (.indexOf hay needle from)]
                                 (if (neg? i) n (recur (+ i (.length needle)) (inc n))))))
                 gen-marks (if (.isDirectory obs)
                             (reduce (fn [acc ^java.io.File f]
                                       (let [t (slurp-safe f)]
                                         (+ acc (count-sub t "Gen 0") (count-sub t "Gen 1")
                                            (count-sub t "multi-generation"))))
                                     0 (glob-sorted obs cycle-file-re))
                             0)
                 g (generational-from true gen-marks)]
             [g (conj notes (format "generational: gen_marks=%d → MGI≈%.3f" gen-marks g))]))))

     (defn compute
       "compute(repo) → AliveTuple assembling all five dimensions + JST timestamp."
       [repo]
       (let [obs (str repo "/_observations")
             [m n1] (motion obs repo)
             [d n2] (diversity repo)
             [c n3] (coupling obs)
             [p n4] (pruning repo)
             [g n5] (generational repo)
             ts (let [sdf (doto (java.text.SimpleDateFormat. "yyyy-MM-dd'T'HH:mm:ssXXX")
                            (.setTimeZone (java.util.TimeZone/getTimeZone "GMT+09:00")))]
                  (.format sdf (java.util.Date.)))]
         (alive-tuple m d c p g ts (concat n1 n2 n3 n4 n5))))))
