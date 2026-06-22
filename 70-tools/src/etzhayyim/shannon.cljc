;; etzhayyim.shannon — Shannon redundancy analysis (cljc port, wave 6c).
;;
;; Pure-logic port of the REMAINING logic from
;; 70-tools/etzhayyim-py/src/etzhayyim/shannon.py
;; that was NOT already covered by etzhayyim.shannon-scores (wave 2).
;;
;; etzhayyim.shannon-scores (wave 2) already covers:
;;   weights / cap / sh-entropy / build-report
;;   dsm-cuthill-mckee / dsm-detect-cycles / dsm-find-clusters / build-dsm-report
;;   bayes-dijkstra-from / build-bayesnet-report
;;   build-bottleneck-report
;;   minimize-merge-proposals / minimize-split-proposals / minimize-move-proposals
;;   build-minimize-report
;; → This namespace REQUIRES shannon-scores and reuses all of those.
;;
;; NEW pure logic ported here:
;;   Data record constructors + serialization:
;;     make-item         — ShannonItem record map
;;     item->dict        — serialization
;;     make-check        — ShannonCheck record map
;;     check->dict       — serialization
;;     make-report-meta  — ShannonReport record map
;;     report-meta->dict — serialization
;;
;;   Pure text/hash helpers:
;;     norm-line         — doc-line normalizer (lowercase + strip markdown)
;;     hash8             — SHA-256 first 16 hex chars of a string
;;     dedup-items       — deduplicate ShannonItem seq by path|kind|detail key
;;
;;   Pure check helpers (logic only, no IO):
;;     go-only-stub         — factory for Go-AST stubs (score=100, not-available note)
;;     make-check-result    — build a ShannonCheck from scored parameters
;;     run-checks-from-list — assemble ordered check list from a provided checks map
;;
;; IO functions (_walk, _sh_scan, check_claude_md_duplication,
;;              check_config_redundancy, check_dead_code_entropy,
;;              check_doc_code_drift, check_stale_symbol_entropy,
;;              CLI click commands, subprocess) are NOT ported here;
;; they stay in the Python module or will arrive in a later IO wave.
;;
;; bb usage (classpath 70-tools/src):
;;   (require '[etzhayyim.shannon :as sh]
;;            '[etzhayyim.shannon-scores :as ss])
;;   (sh/hash8 "hello")        ;=> "2cf24dba5fb0a30e"
;;   (sh/norm-line "**Foo** `bar`") ;=> "foo bar"
;;   (sh/go-only-stub "code_clone_cross")
;;   ;=> {:name "code_clone_cross" :score 100.0 :weight 0.0 :violations 0
;;   ;    :details "not available in Python port — use Go binary: etzhayyim shannon scan"
;;   ;    :items []}

(ns etzhayyim.shannon
  (:require [clojure.string :as str]
            [etzhayyim.shannon-scores :as ss])
  #?(:clj (:import [java.security MessageDigest])))

;; ── data record constructors ──────────────────────────────────────────────────

(defn make-item
  "Construct a ShannonItem record map.
   path        — relative file path string
   kind        — check name / category string
   redundancy  — float 0.0–1.0
   duplicate-of — optional: path of the original (default \"\")
   detail       — optional: human-readable detail (default \"\")"
  ([path kind redundancy]
   (make-item path kind redundancy "" ""))
  ([path kind redundancy duplicate-of detail]
   {:path         path
    :kind         kind
    :redundancy   (double redundancy)
    :duplicate-of duplicate-of
    :detail       detail}))

(defn item->dict
  "Serialize a ShannonItem to a plain string-keyed map (JSON-ready).
   Mirrors Python ShannonItem.to_dict."
  [item]
  (let [base {"path"       (:path item "")
               "kind"       (:kind item "")
               "redundancy" (double (:redundancy item 0.0))}]
    (cond-> base
      (seq (:duplicate-of item "")) (assoc "duplicate_of" (:duplicate-of item ""))
      (seq (:detail item ""))        (assoc "detail"       (:detail item "")))))

(defn make-check
  "Construct a ShannonCheck record map.
   name        — check identifier string
   score       — float 0.0–100.0 (default 100.0)
   weight      — float weight (default 0.0, filled in by build-report)
   violations  — integer violation count (default 0)
   details     — human-readable summary string (default \"\")
   items       — seq of ShannonItem maps (default [])"
  ([name]
   (make-check name 100.0 0.0 0 "" []))
  ([name score weight violations details items]
   {:name       name
    :score      (double score)
    :weight     (double weight)
    :violations violations
    :details    details
    :items      (vec items)}))

(defn check->dict
  "Serialize a ShannonCheck to a plain string-keyed map (JSON-ready).
   Mirrors Python ShannonCheck.to_dict."
  [chk]
  {"name"       (:name chk "")
   "score"      (double (:score chk 100.0))
   "weight"     (double (:weight chk 0.0))
   "violations" (:violations chk 0)
   "details"    (:details chk "")
   "items"      (mapv item->dict (:items chk []))})

(defn make-report-meta
  "Construct a ShannonReport record map.
   evaluated-at          — ISO-8601 timestamp string
   overall-score         — float
   redundancy-rate       — float
   checks                — seq of ShannonCheck maps
   hotspots              — seq of ShannonItem maps
   scoring-model         — string"
  [evaluated-at overall-score redundancy-rate checks hotspots scoring-model]
  {:evaluated-at    evaluated-at
   :overall-score   overall-score
   :redundancy-rate redundancy-rate
   :checks          (vec checks)
   :hotspots        (vec hotspots)
   :scoring-model   scoring-model})

(defn report-meta->dict
  "Serialize a ShannonReport to a plain string-keyed map (JSON-ready).
   Mirrors Python ShannonReport.to_dict."
  [r]
  {"evaluated_at"     (:evaluated-at r "")
   "overall_score"    (double (:overall-score r 100.0))
   "redundancy_rate"  (double (:redundancy-rate r 0.0))
   "checks"           (mapv check->dict (:checks r []))
   "hotspots"         (mapv item->dict (:hotspots r []))
   "scoring_model"    (:scoring-model r "")})

;; ── pure text / hash helpers ──────────────────────────────────────────────────

(defn norm-line
  "Normalize a documentation line for duplication comparison:
   lowercase, strip markdown markers (**, *, backtick), collapse whitespace.
   Mirrors Python _norm_line."
  [s]
  (-> s
      str/lower-case
      str/trim
      (str/replace "**" "")
      (str/replace "*"  "")
      (str/replace "`"  "")
      (str/split #"\s+")
      (->> (str/join " "))))

(defn hash8
  "Return the first 16 hex characters of the SHA-256 hash of string s.
   Mirrors Python _hash8 (sha256.hexdigest()[:16])."
  [s]
  #?(:clj
     (let [digest (MessageDigest/getInstance "SHA-256")
           bytes  (.digest digest (.getBytes s "UTF-8"))]
       (apply str (map #(format "%02x" (bit-and % 0xff)) (take 8 bytes))))
     :cljs
     ;; In ClojureScript / SCI we fall back to a simple djb2-style hash
     ;; (pure, deterministic, not SHA-256 — acceptable for bb/SCI smoke tests)
     (let [h (reduce (fn [acc ch]
                       (bit-and (unchecked-add (unchecked-multiply acc 31)
                                               (.charCodeAt s (.indexOf s (str ch))))
                                0xffffffff))
                     5381
                     (seq s))]
       (format "%016x" (bit-and h 0xffffffffffffffff)))))

(defn dedup-items
  "Deduplicate a seq of ShannonItem maps by the key path|kind|detail.
   Preserves first occurrence of each unique key.
   Mirrors Python _dedup."
  [items]
  (let [seen (atom #{})]
    (reduce (fn [acc item]
              (let [k (str (:path item "") "|"
                           (:kind item "") "|"
                           (:detail item ""))]
                (if (@seen k)
                  acc
                  (do (swap! seen conj k)
                      (conj acc item)))))
            []
            items)))

;; ── pure check helpers ─────────────────────────────────────────────────────────

(defn go-only-stub
  "Return a ShannonCheck stub for checks that require Go AST / haisen graph.
   Score is 100.0 (no data → no penalty).
   Mirrors Python _go_only_stub."
  [check-name]
  (make-check check-name 100.0 0.0 0
              "not available in Python port — use Go binary: etzhayyim shannon scan"
              []))

(defn make-check-result
  "Build a ShannonCheck from scored parameters.
   Convenience constructor used by IO-layer callers (operator-gated).

   Params:
     check-name  — string
     violations  — integer count
     total       — integer total (used for score = 100 - violations/total * 100)
     items       — seq of ShannonItem maps
     details     — optional detail string

   Score is clamped via ss/cap. Score = 100 when total = 0."
  ([check-name violations total items]
   (make-check-result check-name violations total items ""))
  ([check-name violations total items details]
   (let [score (if (pos? total)
                 (ss/cap (- 100.0 (* (/ (double violations) total) 100.0)))
                 100.0)]
     (make-check check-name score 0.0 violations details (vec items)))))

(defn ordered-check-names
  "Return the canonical ordered sequence of check names as used by run_all_checks.
   Mirrors the ordering in Python run_all_checks."
  []
  ["claude_md_duplication"
   "code_clone_cross"
   "collection_write_fan"
   "wit_type_duplication"
   "config_redundancy"
   "dead_code_entropy"
   "doc_code_drift"
   "rust_duplication"
   "stale_symbol_entropy"])

(defn assemble-checks
  "Assemble an ordered check list for build-report.
   checks-map: {check-name → ShannonCheck-map}
     — for Go-AST checks not present in the map, go-only-stub is used.

   Returns a vector of ShannonCheck maps in canonical order.
   Mirrors the run_all_checks logic in Python."
  [checks-map]
  (let [go-stubs #{"code_clone_cross" "collection_write_fan"
                   "wit_type_duplication" "rust_duplication"}]
    (mapv (fn [n]
            (or (get checks-map n)
                (if (go-stubs n)
                  (go-only-stub n)
                  (make-check n))))
          (ordered-check-names))))
