(ns keizu.methods.registry
  "registry.cljc — 系図 (keizu) public-source registry access. ADR-2606066000.
  1:1 Clojure port of `methods/registry.py`.

  Loads registry/sources.seed.json and exposes the source catalog to the ingest/bridge paths:
    - get-source / source-ids
    - sourcing-for(source-id) — G11 honesty DRIVEN BY the registry: a record from a VERIFIED source
      may be :authoritative; from an unverified-seed source it stays :representative.
    - assert-source-allowed — the Charter Rider §2(e)/N5 commercial-gov-intel deny-list as a
      reusable RUNTIME guard (the same SOURCE-DENY weave.validate-* enforces on derived datoms).

  House style: the registry is JSON; no cheshire/data.json dependency, so a minimal self-contained
  JSON reader (copy of the danjo budget_ledger.cljc pattern) reads it. SOURCE-DENY / source-denied
  are reused from the already-ported keizu.methods.weave sibling. Omits the Python __main__ demo.

  Stdlib only; file I/O at the #?(:clj) edge."
  (:require [clojure.string :as str]
            [keizu.methods.weave :as w]))

;; ── minimal JSON reader (subset sufficient for the sources.seed.json catalog) ───
;; maps string-keyed, integers → long, doubles → double, literals → true/false/nil.
(declare json-value)

(defn- skip-ws [^String s i]
  (loop [i i]
    (if (and (< i (count s)) (contains? #{\space \tab \newline \return} (nth s i)))
      (recur (inc i)) i)))

(defn- json-string [^String s i]
  (loop [i (inc i), sb (StringBuilder.)]
    (let [c (nth s i)]
      (cond
        (= c \") [(.toString sb) (inc i)]
        (= c \\)
        (let [e (nth s (inc i))]
          (case e
            \" (do (.append sb \") (recur (+ i 2) sb))
            \\ (do (.append sb \\) (recur (+ i 2) sb))
            \/ (do (.append sb \/) (recur (+ i 2) sb))
            \b (do (.append sb \backspace) (recur (+ i 2) sb))
            \f (do (.append sb \formfeed) (recur (+ i 2) sb))
            \n (do (.append sb \newline) (recur (+ i 2) sb))
            \r (do (.append sb \return) (recur (+ i 2) sb))
            \t (do (.append sb \tab) (recur (+ i 2) sb))
            \u (let [cp (Integer/parseInt (subs s (+ i 2) (+ i 6)) 16)]
                 (.append sb (char cp)) (recur (+ i 6) sb))
            (do (.append sb e) (recur (+ i 2) sb))))
        :else (do (.append sb c) (recur (inc i) sb))))))

(defn- json-number [^String s i]
  (let [end (loop [j i]
              (if (and (< j (count s))
                       (contains? #{\0 \1 \2 \3 \4 \5 \6 \7 \8 \9 \+ \- \. \e \E} (nth s j)))
                (recur (inc j)) j))
        tok (subs s i end)]
    [(if (some #{\. \e \E} tok) (Double/parseDouble tok) (Long/parseLong tok)) end]))

(defn- json-array [^String s i]
  (loop [i (skip-ws s (inc i)), out []]
    (if (= (nth s i) \])
      [out (inc i)]
      (let [[v i] (json-value s i)
            i (skip-ws s i)]
        (if (= (nth s i) \,)
          (recur (skip-ws s (inc i)) (conj out v))
          [(conj out v) (inc i)])))))

(defn- json-object [^String s i]
  (loop [i (skip-ws s (inc i)), out {}]
    (if (= (nth s i) \})
      [out (inc i)]
      (let [[k i] (json-string s i)
            i (skip-ws s i)
            [v i] (json-value s (skip-ws s (inc i)))
            out (assoc out k v)
            i (skip-ws s i)]
        (if (= (nth s i) \,)
          (recur (skip-ws s (inc i)) out)
          [out (inc i)])))))

(defn- json-value [^String s i]
  (let [i (skip-ws s i), c (nth s i)]
    (cond
      (= c \{) (json-object s i)
      (= c \[) (json-array s i)
      (= c \") (json-string s i)
      (= c \t) [true (+ i 4)]
      (= c \f) [false (+ i 5)]
      (= c \n) [nil (+ i 4)]
      :else (json-number s i))))

(defn parse-json
  "Parse the first JSON value in text → Clojure data (maps string-keyed)."
  [text]
  (first (json-value text 0)))

;; ── registry path (…/keizu/methods/registry.cljc → up 2 = keizu → registry/sources.seed.json)
#?(:clj
   (def ^:private reg-path
     (-> (java.io.File. ^String *file*) .getParentFile .getParentFile
         (java.io.File. "registry") (java.io.File. "sources.seed.json"))))

(defn load-registry
  ([] #?(:clj (load-registry reg-path)
         :default (throw (ex-info "bind a registry path on this host" {}))))
  ([path] (parse-json (slurp (str path)))))

(defn source-ids
  "All sourceIds in the registry, in file order."
  []
  (mapv #(get % "sourceId") (get (load-registry) "sources")))

(defn get-source
  "The source map for `source-id`; raises (KeyError analogue) when absent."
  [source-id]
  (or (some (fn [s] (when (= (get s "sourceId") source-id) s))
            (get (load-registry) "sources"))
      (throw (ex-info (str "no such source " (pr-str source-id)) {:source-id source-id}))))

(defn sourcing-for
  "G11 — :authoritative only when the registry marks the source verified; else :representative.
  An unknown source id is treated conservatively as :representative (never auto-authoritative)."
  [source-id]
  (let [status (try (get (get-source source-id) "verificationStatus" "")
                    (catch #?(:clj Exception :cljs :default) _ ::unknown))]
    (cond
      (= status ::unknown) ":representative"
      (= status "verified") ":authoritative"
      :else ":representative")))

(defn assert-source-allowed
  "Charter Rider §2(e)/N5 — raise if any text cites a commercial gov-intel terminal. Reusable
  runtime guard (mirror of the SOURCE-DENY check baked into weave.validate-rel/validate-money)."
  [& texts]
  (let [d (w/source-denied (vec texts))]
    (when (seq d)
      (throw (ex-info (str "Rider §2(e)/N5: " (pr-str d)
                           " is a prohibited commercial gov-intel terminal") {:term d})))))

;; SOURCE-DENY re-exported for the test suites (single source of truth in weave).
(def SOURCE-DENY w/SOURCE-DENY)
