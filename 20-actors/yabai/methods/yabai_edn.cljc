(ns yabai.methods.yabai-edn
  "yabai_edn.py — shared minimal EDN reader + datom classifier (stdlib only).
  1:1 Clojure port of `methods/yabai_edn.py` (ADR-2605301400 §T3).

  Same subset as kabuto/ipaddress readers: vectors [], maps {}, :keyword, \"string\",
  number, bool, nil. Keeps the yabai CTI cells dependency-free.

  House style: Python ':…' keyword strings stay strings (NOT clojure keywords) so the
  whole pipeline stays string-keyed, byte-for-byte the same as the Python port. Pure fns;
  file I/O only at the #?(:clj) load-edn edge."
  (:require [clojure.string :as str]))

;; ── tokens ──────────────────────────────────────────────────────────────────
;; _TOK = re.compile(r'[\s,]+|;[^\n]*|(\[|\]|\{|\}|"(?:\\.|[^"\\])*"|[^\s,\[\]{}]+)')
(def ^:private tok-re
  #"[\s,]+|;[^\n]*|(\[|\]|\{|\}|\"(?:\\.|[^\"\\])*\"|[^\s,\[\]{}]+)")

(defn tokens
  "Lazy seq of significant tokens (group 1 of each tok-re match that captured)."
  [s]
  (let [m (re-matcher tok-re s)]
    ((fn step []
       (lazy-seq
        (when (.find m)
          (let [t (.group m 1)]
            (if (nil? t)
              (step)
              (cons t (step))))))))))

;; alias matching the Python private name (used by kotoba._tokens import).
(def ^:private _tokens tokens)

(defn atom-of
  "Port of _atom: \"…\" → unescaped string; true/false/nil → bool/nil; \":…\" kept as string;
  int → long; else float; else raw string."
  [t]
  (cond
    (str/starts-with? t "\"")
    (-> (subs t 1 (dec (count t)))
        (str/replace "\\\"" "\"")
        (str/replace "\\\\" "\\"))
    (= t "true") true
    (= t "false") false
    (= t "nil") nil
    (str/starts-with? t ":") t
    :else
    (let [as-long (try (Long/parseLong t) (catch #?(:clj Exception :cljs :default) _ ::nan))]
      (if (not= as-long ::nan)
        as-long
        (let [as-dbl (try (Double/parseDouble t) (catch #?(:clj Exception :cljs :default) _ ::nan))]
          (if (not= as-dbl ::nan) as-dbl t))))))

(def ^:private end-marker ::end)

(defn- parse-step
  "Consume one form from the token vector at index i. Returns [value next-i] or
  [end-marker next-i] when a closing ] or } is hit (matching _parse's _END sentinel)."
  [toks i]
  (let [t (nth toks i)
        i (inc i)]
    (cond
      (= t "[")
      (loop [i i, out []]
        (let [[x i] (parse-step toks i)]
          (if (= x end-marker)
            [out i]
            (recur i (conj out x)))))

      (= t "{")
      (loop [i i, out {}]
        (let [[k i] (parse-step toks i)]
          (if (= k end-marker)
            [out i]
            (let [[v i] (parse-step toks i)]
              (recur i (assoc out k v))))))

      (or (= t "]") (= t "}"))
      [end-marker i]

      :else
      [(atom-of t) i])))

(defn parse-tokens
  "Parse the first top-level form from a token seq (matches _parse(_tokens(...)))."
  [toks]
  (first (parse-step (vec toks) 0)))

;; alias matching the Python private name (kotoba._parse import).
(def ^:private _parse parse-tokens)

(defn read-edn
  "Parse the first top-level form from EDN text."
  [text]
  (parse-tokens (tokens text)))

#?(:clj
   (defn load-edn
     "Read + parse an EDN file (file I/O only at this edge)."
     [path]
     (read-edn (slurp (str path)))))

;; ── classify ──────────────────────────────────────────────────────────────────
(def ^:private buckets
  [[":domain/id" "domains"] [":pdns/id" "pdns"] [":iphist/id" "iphist"]
   [":tlscert/id" "certs"] [":indicator/id" "indicators"] [":access/id" "access"]
   [":btobs/id" "btobs"]])

(def ^:private keyed #{"domains"})

;; helper that performs the bucket insert (mirrors Python's per-record `break`).
(defn- bucket-insert [out name key r keyed?]
  (if keyed?
    (assoc-in out [name (get r key)] r)
    (update out name conj r)))

(defn classify
  "Port of classify(rows). Bucket each record by its first matching id key.
  domains is keyed by :domain/id; the rest are appended lists."
  [rows]
  (let [init (reduce (fn [m [_k name]]
                       (assoc m name (if (contains? keyed name) {} [])))
                     {}
                     buckets)]
    (reduce
     (fn [out r]
       (if-not (map? r)
         out
         (loop [bs buckets]
           (if (empty? bs)
             out
             (let [[key name] (first bs)]
               (if (contains? r key)
                 (bucket-insert out name key r (contains? keyed name))
                 (recur (rest bs))))))))
     init
     rows)))

;; ── EDN serialization ──────────────────────────────────────────────────────────
(defn edn-str
  "Port of edn_str: quote a string with \\ and \" escaped."
  [s]
  (str "\"" (-> (str s)
                (str/replace "\\" "\\\\")
                (str/replace "\"" "\\\""))
       "\""))

(defn edn-val
  "Port of edn_val: bool→true/false, number→str, list→[…], string starting with ':'→raw,
  else quoted string."
  [x]
  (cond
    (boolean? x) (if x "true" "false")
    (number? x) (str x)
    (sequential? x) (str "[" (str/join " " (map edn-val x)) "]")
    (string? x) (if (str/starts-with? x ":") x (edn-str x))
    :else (edn-str (str x))))

(defn to-edn
  "Port of to_edn(recs, header_lines)."
  [recs header-lines]
  (let [lines (concat (vec header-lines) ["["]
                      (map (fn [r]
                             (str " {"
                                  (str/join " " (map (fn [[k v]] (str k " " (edn-val v))) r))
                                  "}"))
                           recs)
                      ["]"])]
    (str (str/join "\n" lines) "\n")))
