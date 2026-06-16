;; ported from 20-actors/hakoniwa/methods/world.py — real port replacing the unit_refactor
;; stage-0 "TODO: port-failed" stubs (and the wrong root.hakoniwa.* ns). 20-actors is the bb
;; source root, so hakoniwa.methods.world resolves; the root.* prefix never did.
(ns hakoniwa.methods.world
  "world.py — hakoniwa 箱庭 world-graph loader for the forward-simulation scenario.
  1:1 Clojure port of `methods/world.py` (ADR-2606111500).

  Reads a kotoba-EDN scenario graph (:sim/* nodes + :en/* 縁) into plain string-keyed maps.
  House style mirrors the Python loader EXACTLY: keywords are kept as ':ns/name' STRINGS (not
  Clojure keywords), maps are string-keyed, integers → long, reals → double. The contained
  miniature world holds ONLY FICTIONAL synthetic personas (G1).

  Self-contained EDN reader (subset: [] {} :kw \"string\" num bool nil); no clojure.edn (the
  Python reader's string-keyword semantics must be preserved). Pure; file I/O behind #?(:clj)."
  (:require [clojure.set :as set]
            #?(:clj [clojure.java.io :as io])))

;; fields that would indicate a real-person model — FORBIDDEN by G1 (no PII, ever)
(def forbidden-persona-fields
  #{":person/id" ":person/name" ":individual/id" ":user/id" ":account/id"
    ":email" ":phone" ":address" ":geo/point" ":device/id" ":biometric"
    ":real-name" ":dob" ":ssn" ":handle"})

;; ── minimal EDN tokenizer (mirrors the Python _TOK regex: whitespace/commas + ; comments are
;;    separators; tokens are delimiters, quoted strings, or bare atoms). ──────────────────────
(defn- ws? [c] (or (= c \space) (= c \tab) (= c \newline) (= c \return) (= c \,)))
(defn- delim? [c] (or (= c \[) (= c \]) (= c \{) (= c \})))

(defn tokens
  "Tokenize EDN text → vector of token strings (mirrors world._tokens)."
  [^String s]
  (let [n (count s)]
    (loop [i 0, out (transient [])]
      (if (>= i n)
        (persistent! out)
        (let [c (nth s i)]
          (cond
            (ws? c) (recur (inc i) out)
            (= c \;) (let [j (loop [j i] (if (and (< j n) (not= (nth s j) \newline)) (recur (inc j)) j))]
                       (recur j out))
            (delim? c) (recur (inc i) (conj! out (str c)))
            (= c \") (let [j (loop [j (inc i)]
                               (cond
                                 (>= j n) j
                                 (= (nth s j) \\) (recur (+ j 2))
                                 (= (nth s j) \") (inc j)
                                 :else (recur (inc j))))]
                       (recur j (conj! out (subs s i j))))
            :else (let [j (loop [j i]
                            (if (and (< j n)
                                     (not (ws? (nth s j)))
                                     (not (delim? (nth s j))))
                              (recur (inc j))
                              j))]
                    (recur j (conj! out (subs s i j))))))))))

(defn- parse-long-strict
  "Parse t as a long, else nil."
  [^String t]
  (try (Long/parseLong t) (catch Exception _ nil)))

(defn- parse-double-strict
  [^String t]
  (try (Double/parseDouble t) (catch Exception _ nil)))

(defn atom-val
  "Token string → value, mirroring world._atom. Keeps ':ns/name' keywords AS strings."
  [^String t]
  (cond
    (.startsWith t "\"") (-> (subs t 1 (dec (count t)))
                             (.replace "\\\"" "\"")
                             (.replace "\\\\" "\\"))
    (= t "true") true
    (= t "false") false
    (= t "nil") nil
    (.startsWith t ":") t                       ;; keep keywords as ":ns/name" strings
    :else (or (parse-long-strict t)
              (parse-double-strict t)
              t)))

;; ── recursive-descent parser over a token vector (mirrors world._parse / read_edn) ──────────
(declare parse-one)

(defn- parse-seq
  "Parse forms until the closing delimiter; returns [coll next-idx]. `f` folds a value in."
  [toks i closer init f]
  (loop [i i, acc init]
    (let [[v ni done?] (parse-one toks i)]
      (if (= done? closer) [acc ni]
          (recur ni (f acc v))))))

(defn- parse-one
  "Returns [value next-idx end-marker]. end-marker is the closing token string when a ]/}
  was consumed, else nil."
  [toks i]
  (let [t (nth toks i)]
    (cond
      (= t "[") (let [[v ni] (loop [i (inc i), acc []]
                               (let [[x ni done?] (parse-one toks i)]
                                 (if done? [acc ni] (recur ni (conj acc x)))))]
                  [v ni nil])
      (= t "{") (let [[v ni] (loop [i (inc i), acc {}]
                               (let [[k ni done?] (parse-one toks i)]
                                 (if done?
                                   [acc ni]
                                   (let [[val ni2 _] (parse-one toks ni)]
                                     (recur ni2 (assoc acc k val))))))]
                  [v ni nil])
      (or (= t "]") (= t "}")) [nil (inc i) t]
      :else [(atom-val t) (inc i) nil])))

(defn read-edn
  "Parse the first top-level EDN form in text → Clojure data (string-keyed maps, string keywords)."
  [text]
  (first (parse-one (tokens text) 0)))

(defn assert-synthetic
  "G1: every persona MUST be synthetic and MUST carry no PII-class field. Throws on breach.
  `nodes` is {nid node-map}."
  [nodes]
  (doseq [[nid n] nodes]
    (when (= (get n ":sim/kind") ":persona")
      (when-not (true? (get n ":persona/synthetic"))
        (throw (ex-info (str "G1 violation: persona " nid " is not marked :persona/synthetic true")
                        {:nid nid})))
      (let [leaked (set/intersection (set (keys n)) forbidden-persona-fields)]
        (when (seq leaked)
          (throw (ex-info (str "G1 violation: persona " nid " carries PII-class field(s) " leaked)
                          {:nid nid :leaked leaked})))))))

(defn nodes+edges
  "Fold parsed EDN forms → [nodes-by-id edges]; enforces G1 (synthetic personas)."
  [forms]
  (let [[nodes edges]
        (reduce (fn [[nodes edges] f]
                  (cond
                    (not (map? f)) [nodes edges]
                    (contains? f ":sim/id") [(assoc nodes (get f ":sim/id") f) edges]
                    (and (contains? f ":en/from") (contains? f ":en/to")) [nodes (conj edges f)]
                    :else [nodes edges]))
                [{} []]
                forms)]
    (assert-synthetic nodes)
    [nodes edges]))

#?(:clj
   (defn load
     "Return [nodes-by-id edges] from a scenario EDN graph file; enforces G1. (File I/O edge.)"
     [path]
     (nodes+edges (read-edn (slurp (str path))))))

(defn personas [nodes]
  (into {} (filter (fn [[_ n]] (= (get n ":sim/kind") ":persona")) nodes)))

(defn signals [nodes]
  (into {} (filter (fn [[_ n]] (= (get n ":sim/kind") ":signal")) nodes)))

(defn outcomes [nodes]
  (into {} (filter (fn [[_ n]] (= (get n ":sim/kind") ":outcome")) nodes)))
