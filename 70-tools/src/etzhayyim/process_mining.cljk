;; etzhayyim.process-mining — PDS handler static analysis (cljc port, wave-4b).
;;
;; Pure-logic port of 70-tools/etzhayyim-py/src/etzhayyim/process_mining.py
;; (no click, no subprocess, no network I/O — file I/O is a deferred leg).
;;
;; API:
;;   (analyze-handler-content nsid content) → {:nsid :bottleneck_count :bottlenecks}
;;   (compute-pm-summary  handlers)         → {:total_handlers :total_bottlenecks :critical :high
;;                                              :medium :low :score :grade}
;;
;; IO leg (deferred, operator-gated):
;;   `scan-handler-dir` reads *.ts from a Path and calls analyze-handler-content.
;;   Not loaded at namespace-load time — call explicitly when running on live fs.
;;
;; bb usage (classpath 70-tools/src):
;;   (require '[etzhayyim.process-mining :as pm])
;;   (pm/compute-pm-summary [])

(ns etzhayyim.process-mining
  (:require [clojure.string :as str]))

;; ── bottleneck patterns ───────────────────────────────────────────────────────
;;
;; Each entry: [regex-str severity pattern-name detail]
;; Mirrors the `patterns` list in process_mining.py exactly.

(def ^:private bottleneck-patterns
  [["await.*await"                                        "critical" "nested-await"
    "Multiple sequential awaits may serialize I/O"]
   ["throw new Error.*\\b(400|401|403|404)\\b|status.*\\b(400|401|403)\\b"
    "low" "error-response"
    "Error response with HTTP status code"]
   ["setTimeout|setInterval"                             "medium" "timer"
    "Timers in handlers cause latency spikes"]
   ["fetch\\(|new Request\\("                             "high" "outbound-fetch"
    "Outbound fetch in hot path adds tail latency"]
   ["while\\s*\\(\\s*true\\s*\\)|for\\s*\\(\\s*;;\\s*\\)" "critical" "infinite-loop"
    "Infinite loop detected in handler"]
   ["catch\\s*\\([^)]*\\)\\s*\\{\\s*\\}|catch\\s*\\([^)]*\\)\\s*//" "high" "silent-catch"
    "Empty or silent catch swallows errors"]])

;; ── pure core ─────────────────────────────────────────────────────────────────

(defn analyze-handler-content
  "Analyze TypeScript handler source text for performance bottlenecks.
   `nsid`    – NSID string (stem.replace('-','.') from filename)
   `content` – full source text string
   Returns a map compatible with _analyze_handler_file in process_mining.py."
  [nsid content]
  (let [;; Helper: find all match start positions for a pattern in content.
        ;; bb re-seq returns strings, not Matcher objects, so we use re-matcher loop.
        find-matches (fn [pat-str]
                       (let [m (re-matcher (re-pattern pat-str) content)]
                         (loop [acc []]
                           (if (re-find m)
                             (recur (conj acc (.start m)))
                             acc))))

        ;; Line number from char offset
        line-of (fn [offset]
                  (inc (count (filter #{\newline} (subs content 0 offset)))))

        ;; standard patterns
        bottlenecks
        (reduce (fn [acc [regex severity pname detail]]
                  (if (= pname "repeated-json-parse")
                    acc
                    (let [starts (find-matches (str "(?i)" regex))]
                      (reduce (fn [a start-pos]
                                (conj a {:pattern  pname
                                         :severity severity
                                         :line_no  (line-of start-pos)
                                         :detail   detail}))
                              acc
                              starts))))
                []
                bottleneck-patterns)

        ;; repeated JSON.parse/stringify
        json-starts (find-matches "JSON\\.parse|JSON\\.stringify")
        bottlenecks (if (> (count json-starts) 2)
                      (conj bottlenecks
                            {:pattern  "repeated-json-parse"
                             :severity "medium"
                             :line_no  (if (seq json-starts) (line-of (first json-starts)) 1)
                             :detail   (str "JSON.parse/stringify called "
                                            (count json-starts)
                                            " times — consider caching")})
                      bottlenecks)]
    {:nsid             nsid
     :bottleneck_count (count bottlenecks)
     :bottlenecks      bottlenecks}))

(defn compute-pm-summary
  "Aggregate bottleneck counts across a seq of handler analysis maps.
   Mirrors _compute_pm_summary in process_mining.py.
   handlers — seq of maps from analyze-handler-content (or _analyze_handler_file)."
  [handlers]
  (let [all-bs    (mapcat :bottlenecks handlers)
        critical  (count (filter #(= "critical" (:severity %)) all-bs))
        high      (count (filter #(= "high"     (:severity %)) all-bs))
        medium    (count (filter #(= "medium"   (:severity %)) all-bs))
        low       (count (filter #(= "low"      (:severity %)) all-bs))
        score     (max 0.0 (- 100.0 (* critical 25) (* high 10) (* medium 5) (* low 2)))
        grade     (cond
                    (>= score 90) "S"
                    (>= score 70) "A"
                    (>= score 50) "B"
                    (>= score 30) "C"
                    :else         "D")]
    {:total_handlers    (count handlers)
     :total_bottlenecks (count all-bs)
     :critical          critical
     :high              high
     :medium            medium
     :low               low
     :score             score
     :grade             grade}))

;; ── deferred IO leg ───────────────────────────────────────────────────────────
;;
;; scan-handler-dir is NOT called at load time.  Invoke explicitly when you have
;; babashka.fs available and a live filesystem.
;;
;; (require '[babashka.fs :as fs])
;; (defn scan-handler-dir [handler-dir]
;;   (let [ts-files (sort (fs/glob handler-dir "**/*.ts"))]
;;     (mapv (fn [p]
;;             (let [content (slurp (str p))
;;                   nsid    (-> (fs/file-name p)
;;                               (str/replace #"\.ts$" "")
;;                               (str/replace #"-" "."))]
;;               (analyze-handler-content nsid content)))
;;           ts-files)))
