(ns saisei.methods.edn
  "saisei 再生 — minimal EDN reader (subset: [] {} :kw \"str\" num bool nil).

  Fidelity invariant (root CLAUDE.md convention, shared with tate/methods/edn.cljc):
  keywords are kept as their \":ns/name\" STRINGS, not Clojure keywords, so every
  record is keyed on string keys (\":proc/id\", \":sit/jurisdiction\", …) — the same
  convention the rest of the kotoba-native actor registries use.

  Stdlib only (regex tokenizer); file I/O at the #?(:clj) edge."
  (:require [clojure.string :as str]))

(def ^:private token-re
  #"[\s,]+|;[^\n]*|(\[|\]|\{|\}|\"(?:\\.|[^\"\\])*\"|[^\s,\[\]{}]+)")

(defn- tokens
  [s]
  (let [m (re-matcher token-re s)]
    ((fn step []
       (lazy-seq
        (when (.find m)
          (let [t (.group m 1)]
            (if (nil? t) (step) (cons t (step))))))))))

(defn- unescape-string
  [t]
  (-> (subs t 1 (dec (count t)))
      (str/replace "\\\"" "\"")
      (str/replace "\\\\" "\\")))

(defn- parse-long* [^String t]
  #?(:clj (try (Long/parseLong t) (catch Exception _ nil))
     :cljs (when (re-matches #"[-+]?\d+" t)
             (let [n (js/parseInt t 10)] (when-not (js/isNaN n) n)))))

(defn- parse-double* [^String t]
  #?(:clj (try (Double/parseDouble t) (catch Exception _ nil))
     :cljs (when (re-matches #"[-+]?(\d+\.?\d*|\.\d+)([eE][-+]?\d+)?" t)
             (let [n (js/parseFloat t)] (when-not (js/isNaN n) n)))))

(defn- atom* [t]
  (cond
    (str/starts-with? t "\"") (unescape-string t)
    (= t "true")  true
    (= t "false") false
    (= t "nil")   nil
    (str/starts-with? t ":") t
    :else (or (parse-long* t) (parse-double* t) t)))

(def ^:private END ::end)

(defn- next-tok! [state]
  (let [ts @state]
    (when (empty? ts)
      (throw (ex-info "saisei.methods.edn: unexpected end of input" {})))
    (reset! state (rest ts))
    (first ts)))

(defn- parse-form [state]
  (let [t (next-tok! state)]
    (cond
      (= t "[") (loop [out []]
                  (let [x (parse-form state)]
                    (if (= x END) out (recur (conj out x)))))
      (= t "{") (loop [out {}]
                  (let [k (parse-form state)]
                    (if (= k END)
                      out
                      (let [v (parse-form state)]
                        (recur (assoc out k v))))))
      (or (= t "]") (= t "}")) END
      :else (atom* t))))

(defn read-edn
  [s]
  (parse-form (atom (tokens s))))

#?(:clj
   (defn load-edn
     [path]
     (read-edn (slurp path))))

#?(:clj
   (defn here
     "Directory of this actor's methods/ dir, for default data/ paths."
     []
     (clojure.java.io/file "20-actors" "saisei")))
