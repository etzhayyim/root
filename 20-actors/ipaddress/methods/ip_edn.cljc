(ns ipaddress.methods.ip-edn
  "ip_edn.py — ipaddress shared minimal EDN reader + datom classifier.
  1:1 Clojure port of `methods/ip_edn.py` (stdlib only).

  Ported from kabuto/watatsuna readers (same subset: vectors [], maps {}, :keyword,
  \"string\", number, bool, nil). Keeps the ipaddress cells dependency-free. ADR-2605301400 §T2.

  House style: ':…' keyword strings stay strings (NOT clojure keywords) so the whole
  pipeline stays string-keyed, byte-for-byte the same as the Python port. Pure fns;
  file I/O only at the load-edn #?(:clj) edge."
  (:require [clojure.string :as str]))

;; ── minimal EDN reader (subset) ──────────────────────────────────────────────
;; _TOK = re.compile(r'[\s,]+|;[^\n]*|(\[|\]|\{|\}|"(?:\\.|[^"\\])*"|[^\s,\[\]{}]+)')
(def ^:private tok-re
  #"[\s,]+|;[^\n]*|(\[|\]|\{|\}|\"(?:\\.|[^\"\\])*\"|[^\s,\[\]{}]+)")

(defn tokens
  "Lazy seq of significant tokens (group 1 of each tok-re match that captured).
  Mirrors _tokens()."
  [s]
  (let [m (re-matcher tok-re s)]
    ((fn step []
       (lazy-seq
        (when (.find m)
          (let [t (.group m 1)]
            (if (nil? t)
              (step)
              (cons t (step))))))))))

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

(defn parse-step
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
      ;; preserve map key INSERTION order (Python dict order) via ::order metadata so
      ;; downstream datom fan-out (graph-datoms / rows-to-datoms) matches Python exactly.
      (loop [i i, out ^{::order []} {}]
        (let [[k i] (parse-step toks i)]
          (if (= k end-marker)
            [out i]
            (let [[v i] (parse-step toks i)]
              (recur i (with-meta (assoc out k v) (update (meta out) ::order conj k)))))))

      (or (= t "]") (= t "}"))
      [end-marker i]

      :else
      [(atom-of t) i])))

(defn parse
  "Parse the first top-level form from a token seq (matches _parse(_tokens(text)))."
  [toks]
  (first (parse-step (vec toks) 0)))

#?(:clj
   (defn load-edn
     "Read + parse an EDN file → Clojure data. File I/O at this edge."
     [path]
     (parse (tokens (slurp (str path))))))

;; ── classify the flat datom vector into entity buckets ───────────────────────
(def ^:private buckets
  [[":rir/id" "rirs"] [":asn/id" "asns"] [":iprange/id" "ranges"]
   [":ip/id" "ips"] [":net.announce/id" "announces"] [":net.member/id" "members"]
   [":geo/id" "geos"] [":rdns/id" "rdns"] [":whois/id" "whois"]])

(def ^:private keyed #{"rirs" "asns" "ranges" "ips"})

(defn ordered-items
  "Items of a map in first-touch insertion order when the map carries ::order metadata
  (mirrors Python dict iteration order); otherwise plain (seq m). Shared by analyze/kotoba."
  [m]
  (if-let [order (::order (meta m))]
    (map (fn [k] [k (get m k)]) order)
    (seq m)))

(defn- oassoc
  "assoc into a map while recording the key's first-touch position in ::order metadata."
  [m k v]
  (if (contains? m k)
    (with-meta (assoc m k v) (meta m))
    (with-meta (assoc m k v) (update (meta m) ::order (fnil conj []) k))))

(defn classify
  "Return map bucket-name → (map keyed by id for entities, vector for edges).
  Keyed buckets preserve Python dict insertion order via ::order metadata (any size)."
  [rows]
  (let [;; init: keyed buckets → ordered map (^{::order []}), edge buckets → vector
        init (reduce (fn [m [_k name]]
                       (assoc m name (if (contains? keyed name) ^{::order []} {} [])))
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
                 (if (contains? keyed name)
                   (update out name oassoc (get r key) r)
                   (update out name conj r))
                 (recur (rest bs))))))))
     init
     rows)))

(defn edn-str
  "EDN-escape a string into a quoted EDN string literal."
  [s]
  (str "\"" (-> (str s) (str/replace "\\" "\\\\") (str/replace "\"" "\\\"")) "\""))

(defn edn-val
  "Render a value as EDN (keyword strings pass through unquoted)."
  [x]
  (cond
    (boolean? x) (if x "true" "false")
    (integer? x) (str x)
    (number? x)  (str x)
    (sequential? x) (str "[" (str/join " " (map edn-val x)) "]")
    (string? x)  (if (str/starts-with? x ":") x (edn-str x))
    :else        (edn-str (str x))))

(defn to-edn
  "Render a list of entity maps as an EDN datom vector with header lines."
  [recs header-lines]
  (let [lines (-> (vec header-lines)
                  (conj "[")
                  (into (map (fn [r]
                               (str " {" (str/join " " (map (fn [[k v]] (str k " " (edn-val v))) (ordered-items r))) "}"))
                             recs))
                  (conj "]"))]
    (str (str/join "\n" lines) "\n")))
