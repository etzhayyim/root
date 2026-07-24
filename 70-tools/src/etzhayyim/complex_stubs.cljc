;; etzhayyim.complex-stubs — CLI stub helpers (cljc port, wave-4b).
;;
;; Pure-logic port of selected helpers from
;; 70-tools/etzhayyim-py/src/etzhayyim/complex_stubs.py
;;
;; The CLI commands in complex_stubs.py delegate to the Go binary, subprocess,
;; or httpx (PDS, Common Crawl, performance tests, plugin download).  Those are
;; ALL IO-only wrappers and are SKIPPED.
;;
;; The 5 pure helpers extracted here have no IO dependency and are worth porting:
;;   (parse-duration  dur-str)     → seconds int (capped at 300)
;;   (date?           s)           → boolean — "YYYY-MM-DD" check
;;   (parse-front-matter text)     → {:result map :error string-or-nil}
;;   (strip-jsonc-comments src)    → src string without // line-comments
;;   (parse-toml-array s)          → list of strings from "[\"a\", \"b\"]"
;;
;; bb usage (classpath 70-tools/src):
;;   (require '[etzhayyim.complex-stubs :as cs])
;;   (cs/parse-duration "2m")   ;; => 120
;;   (cs/date? "2026-06-21")    ;; => true

(ns etzhayyim.complex-stubs
  (:require [clojure.string :as str]))

;; ── parse-duration ────────────────────────────────────────────────────────────

(defn parse-duration
  "Parse a duration string like '30s', '2m', '1h' into seconds (max 300).
   Mirrors _parse_duration in complex_stubs.py."
  [dur]
  (let [s     (str/lower-case (str/trim (str dur)))
        secs  (cond
                (str/ends-with? s "h") (* (Long/parseLong (subs s 0 (dec (count s)))) 3600)
                (str/ends-with? s "m") (* (Long/parseLong (subs s 0 (dec (count s)))) 60)
                (str/ends-with? s "s") (Long/parseLong (subs s 0 (dec (count s))))
                :else                  (Long/parseLong s))]
    (min secs 300)))

;; ── date? ─────────────────────────────────────────────────────────────────────

(defn date?
  "Return true iff s is exactly a 'YYYY-MM-DD' string.
   Mirrors _is_date in complex_stubs.py."
  [s]
  (let [s (str s)]
    (and (= (count s) 10)
         (= \- (.charAt s 4))
         (= \- (.charAt s 7))
         (every? #(Character/isDigit %) (subs s 0 4))
         (every? #(Character/isDigit %) (subs s 5 7))
         (every? #(Character/isDigit %) (subs s 8 10)))))

;; ── strip-jsonc-comments ──────────────────────────────────────────────────────

(defn strip-jsonc-comments
  "Remove // line-comments from JSONC source (respects string literals).
   Mirrors _strip_jsonc_comments in complex_stubs.py."
  [src]
  (let [src (str src)
        n   (count src)]
    (loop [i         0
           in-string false
           sb        (StringBuilder.)]
      (if (>= i n)
        (str sb)
        (let [c (.charAt src i)]
          (cond
            in-string
            (if (and (= c \\) (< (inc i) n))
              (do (.append sb c)
                  (.append sb (.charAt src (inc i)))
                  (recur (+ i 2) true sb))
              (do (.append sb c)
                  (recur (inc i) (not= c \") sb)))

            (= c \")
            (do (.append sb c)
                (recur (inc i) true sb))

            (and (= c \/) (< (inc i) n) (= (.charAt src (inc i)) \/))
            ;; skip to end of line
            (let [j (loop [j i]
                      (if (or (>= j n) (= (.charAt src j) \newline))
                        j
                        (recur (inc j))))]
              (recur j false sb))

            :else
            (do (.append sb c)
                (recur (inc i) false sb))))))))

;; ── parse-toml-array ─────────────────────────────────────────────────────────

(defn parse-toml-array
  "Parse a simple TOML array like [\"a\", \"b\", \"c\"] to a list of strings.
   Mirrors _parse_toml_array in complex_stubs.py."
  [s]
  (let [s (str/trim (str s))]
    (if (not (str/includes? s "]"))
      []
      (let [inner (-> s
                      (str/replace #"^\[" "")
                      (str/replace #"\]$" "")
                      str/trim)]
        (if (str/blank? inner)
          []
          (into []
                (keep (fn [item]
                        (let [v (-> item str/trim
                                    (str/replace #",$" "")
                                    (str/replace #"^[\"']" "")
                                    (str/replace #"[\"']$" "")
                                    str/trim)]
                          (when-not (str/blank? v) v)))
                      (str/split inner #","))))))))

;; ── parse-front-matter ────────────────────────────────────────────────────────

(defn parse-front-matter
  "Parse a Markdown file's YAML front matter (subset: scalar + list values only).
   `text` – full file content as string
   Returns {:result {key val ...} :error string-or-nil}.
   Mirrors _parse_front_matter in complex_stubs.py."
  [text]
  (let [lines (str/split-lines (str text))]
    (if (or (empty? lines) (not= (str/trim (first lines)) "---"))
      {:result {} :error "missing YAML front matter opening delimiter"}
      ;; find closing ---
      (let [end (loop [i 1]
                  (cond
                    (>= i (count lines)) -1
                    (= (str/trim (nth lines i)) "---") i
                    :else (recur (inc i))))]
        (if (= end -1)
          {:result {} :error "missing YAML front matter closing delimiter"}
          (let [result
                (loop [i 1 acc {}]
                  (if (>= i end)
                    acc
                    (let [line    (nth lines i)
                          stripped (str/trim line)]
                      (cond
                        (str/blank? stripped)
                        (recur (inc i) acc)

                        (not (str/includes? stripped ":"))
                        (recur (inc i) acc)

                        :else
                        (let [colon (str/index-of line ":")
                              k     (str/trim (subs line 0 colon))
                              raw   (str/trim (subs line (inc colon)))]
                          (if (str/blank? raw)
                            ;; list value: collect subsequent "- item" lines
                            (let [[lst next-i]
                                  (loop [j (inc i) lst []]
                                    (if (>= j end)
                                      [lst j]
                                      (let [child (str/trim (nth lines j))]
                                        (cond
                                          (str/blank? child)
                                          (recur (inc j) lst)
                                          (str/starts-with? child "- ")
                                          (recur (inc j) (conj lst (str/trim (subs child 2))))
                                          :else [lst j]))))]
                              (recur next-i (assoc acc k lst)))
                            ;; scalar value
                            (let [v (cond
                                      (#{"true" "True"} raw) true
                                      (#{"false" "False"} raw) false
                                      (and (str/starts-with? raw "\"") (str/ends-with? raw "\""))
                                      (subs raw 1 (dec (count raw)))
                                      (and (str/starts-with? raw "'") (str/ends-with? raw "'"))
                                      (subs raw 1 (dec (count raw)))
                                      :else raw)]
                              (recur (inc i) (assoc acc k v)))))))))]
            {:result result :error nil}))))))
