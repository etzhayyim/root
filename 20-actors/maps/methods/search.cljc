(ns maps.methods.search
  "search.py — kotoba-native place name search (ADR-2606064500 R2).
  1:1 Clojure port of `methods/search.py`.

  The kotoba-native successor to the legacy `cmdSearchPlaces` (`WHERE name LIKE prefix`). Name
  search is a TOKEN INDEX: at ingest a feature's name is tokenized to a set of search tokens
  stored as `:feature/name-token` claims; at query the query is tokenized the same way and each
  token is an AVET probe; candidates are ranked by how many query tokens they match.

  The tokenizers (name-tokens / query-tokens / runs / bigrams) are pure and portable. The wire
  read (_avet / search-places HTTP I/O) is host-only, behind #?(:clj ...). JSON encode/parse is
  inlined (self-contained, copied danjo/methods/budget_ledger.cljc style). The __main__ demo is
  intentionally omitted."
  (:require [clojure.string :as str]
            [clojure.set :as set]))

(def query-nsid "com.etzhayyim.apps.kotoba.graph.sparql")
(def ^:private timeout-ms 5000)
(def ^:private max-prefix 12)

;; ── tokenizer (ONE set of fns, used by BOTH write [ingest to-kg-batch] and read) ──
(defn- is-cjk? [ch]
  (let [o (int ch)]
    (or (<= 0x3040 o 0x30FF)
        (<= 0x3400 o 0x9FFF)
        (<= 0xF900 o 0xFAFF)
        (<= 0xFF66 o 0xFF9D))))

(defn- alnum? [ch]
  ;; mirror Python str.isalnum() for the ASCII/Latin range relevant to the seed:
  (or (Character/isLetterOrDigit ch)))

(defn- runs
  "Split a name into [kind text] runs: [\"ascii\" word] | [\"cjk\" run].
  Separators (non-alnum, non-CJK) break runs and are dropped."
  [name]
  (let [s (str/lower-case (or name ""))]
    (loop [chars (seq s), buf [], kind nil, out []]
      (if (empty? chars)
        (if (and (seq buf) (some? kind)) (conj out [kind (apply str buf)]) out)
        (let [ch (first chars)
              k (cond (is-cjk? ch) "cjk"
                      (alnum? ch) "ascii"
                      :else nil)]
          (if (not= k kind)
            (let [out (if (seq buf) (conj out [kind (apply str buf)]) out)]
              (recur (rest chars) (if (some? k) [ch] []) k out))
            (recur (rest chars) (if (some? k) (conj buf ch) buf) kind out)))))))

(defn- bigrams [s]
  (let [bs (mapv #(subs s % (+ % 2)) (range (dec (count s))))]
    (if (seq bs) bs [s])))

(defn name-tokens
  "INDEX tokens for a feature name (stored as :feature/name-token at ingest). Returns a set."
  [name]
  (reduce
   (fn [toks [kind text]]
     (cond
       (and (= kind "ascii") (>= (count text) 2))
       (into toks (for [n (range 2 (inc (min (count text) max-prefix)))] (subs text 0 n)))
       (= kind "cjk")
       (let [toks (into toks (bigrams text))]
         (if (= (count text) 1) (conj toks text) toks))
       :else toks))
   #{}
   (runs name)))

(defn query-tokens
  "PROBE tokens for a search query. Returns a set."
  [q]
  (reduce
   (fn [toks [kind text]]
     (cond
       (and (= kind "ascii") (>= (count text) 2))
       (conj toks (subs text 0 (min (count text) max-prefix)))
       (= kind "cjk")
       (let [toks (into toks (bigrams text))]
         (if (= (count text) 1) (conj toks text) toks))
       :else toks))
   #{}
   (runs q)))

;; ── inlined JSON (encode + parse subset) ──────────────────────────────────────
(defn- json-escape ^String [^String s]
  (str/escape s {\" "\\\"" \\ "\\\\"
                 \backspace "\\b" \tab "\\t" \newline "\\n" \formfeed "\\f" \return "\\r"}))

(defn- json-encode ^String [v]
  (cond
    (nil? v)        "null"
    (string? v)     (str "\"" (json-escape v) "\"")
    (boolean? v)    (if v "true" "false")
    (integer? v)    (str v)
    (number? v)     (str v)
    (map? v)        (str "{" (str/join "," (map (fn [[k val]] (str "\"" (json-escape (str k)) "\":" (json-encode val))) v)) "}")
    (sequential? v) (str "[" (str/join "," (map json-encode v)) "]")
    :else           (str "\"" (json-escape (str v)) "\"")))

#?(:clj
   (do
     (declare json-value)
     (defn- skip-ws [^String s i]
       (loop [i i]
         (if (and (< i (count s)) (contains? #{\space \tab \newline \return} (nth s i)))
           (recur (inc i)) i)))
     (defn- json-string* [^String s i]
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
     (defn- json-number* [^String s i]
       (let [end (loop [j i]
                   (if (and (< j (count s))
                            (contains? #{\0 \1 \2 \3 \4 \5 \6 \7 \8 \9 \+ \- \. \e \E} (nth s j)))
                     (recur (inc j)) j))
             tok (subs s i end)]
         [(if (some #{\. \e \E} tok) (Double/parseDouble tok) (Long/parseLong tok)) end]))
     (defn- json-array* [^String s i]
       (loop [i (skip-ws s (inc i)), out []]
         (if (= (nth s i) \])
           [out (inc i)]
           (let [[v i] (json-value s i) i (skip-ws s i)]
             (if (= (nth s i) \,)
               (recur (skip-ws s (inc i)) (conj out v))
               [(conj out v) (inc i)])))))
     (defn- json-object* [^String s i]
       (loop [i (skip-ws s (inc i)), out {}]
         (if (= (nth s i) \})
           [out (inc i)]
           (let [[k i] (json-string* s i) i (skip-ws s i)
                 [v i] (json-value s (skip-ws s (inc i))) out (assoc out k v) i (skip-ws s i)]
             (if (= (nth s i) \,)
               (recur (skip-ws s (inc i)) out)
               [out (inc i)])))))
     (defn- json-value [^String s i]
       (let [i (skip-ws s i) c (nth s i)]
         (cond
           (= c \{) (json-object* s i)
           (= c \[) (json-array* s i)
           (= c \") (json-string* s i)
           (= c \t) [true (+ i 4)]
           (= c \f) [false (+ i 5)]
           (= c \n) [nil (+ i 4)]
           :else (json-number* s i))))
     (defn- parse-json [text] (first (json-value text 0)))

     ;; ── raw-socket HTTP POST (self-contained; no external deps) ──
     (defn- read-line-crlf [^java.io.InputStream in]
       (let [sb (StringBuilder.)]
         (loop []
           (let [c (.read in)]
             (cond
               (= c -1) (if (pos? (.length sb)) (.toString sb) nil)
               (= c 13) (do (.read in) (.toString sb))
               :else (do (.append sb (char c)) (recur)))))))
     (defn- read-n [^java.io.InputStream in n]
       (let [buf (byte-array n)]
         (loop [off 0]
           (if (>= off n) (String. buf "UTF-8")
               (let [r (.read in buf off (- n off))]
                 (if (neg? r) (String. buf 0 off "UTF-8") (recur (+ off r))))))))
     (defn- read-headers [^java.io.InputStream in]
       (loop [cl 0]
         (let [l (read-line-crlf in)]
           (if (or (nil? l) (= l "")) cl
               (recur (if (str/starts-with? (str/lower-case l) "content-length:")
                        (Integer/parseInt (str/trim (subs l (inc (str/index-of l ":"))))) cl))))))
     (defn http-post-json
       "POST a JSON body to a full URL, return the parsed JSON response (or throw)."
       [^String url body-map]
       (let [u (java.net.URI. url)
             host (.getHost u)
             port (let [p (.getPort u)] (if (pos? p) p 80))
             path (str (.getRawPath u) (when (.getRawQuery u) (str "?" (.getRawQuery u))))
             body (json-encode body-map)
             bb (.getBytes body "UTF-8")
             sock (java.net.Socket.)]
         (try
           (.connect sock (java.net.InetSocketAddress. host port) timeout-ms)
           (.setSoTimeout sock timeout-ms)
           (let [out (.getOutputStream sock) in (.getInputStream sock)]
             (.write out (.getBytes (str "POST " path " HTTP/1.1\r\nHost: " host "\r\n"
                                         "Content-Type: application/json\r\n"
                                         "Connection: close\r\n"
                                         "Content-Length: " (count bb) "\r\n\r\n") "UTF-8"))
             (.write out bb) (.flush out)
             (read-line-crlf in)
             (let [cl (read-headers in)]
               (parse-json (read-n in cl))))
           (finally (.close sock)))))))

(defn- avet
  "One AVET predicate+object probe → entity maps {id, claims:[{pred,value}]}. Fail-soft → []."
  ([endpoint predicate objects] (avet endpoint predicate objects 2000))
  ([endpoint predicate objects limit]
   #?(:clj
      (let [body {"index" "avet" "predicate" predicate "objects" (vec objects) "limit" limit}]
        (try
          (get (http-post-json (str (str/replace endpoint #"/+$" "") "/xrpc/" query-nsid) body) "entities" [])
          (catch Exception _ [])))
      :default [])))

(defn search-places
  "Name search ranked by query-token overlap. Optional label filter (kebab keywords).
  Returns [{id, name, label, score}], best first."
  ([endpoint query] (search-places endpoint query nil 20))
  ([endpoint query labels] (search-places endpoint query labels 20))
  ([endpoint query labels limit]
   (let [qt (query-tokens query)]
     (if (empty? qt)
       []
       (let [want (when (seq labels)
                    (set (map (fn [l] (if (str/starts-with? (str l) ":") (str l) (str ":" l))) labels)))
             out (reduce
                  (fn [out e]
                    (let [{:strs [stored name label]}
                          (reduce (fn [acc c]
                                    (let [p (get c "pred") v (get c "value")]
                                      (cond
                                        (= p "feature/name-token") (update acc "stored" conj v)
                                        (= p "feature/name") (assoc acc "name" v)
                                        (= p "feature/label") (assoc acc "label" v)
                                        :else acc)))
                                  {"stored" #{} "name" nil "label" nil}
                                  (get e "claims" []))]
                      (if (and want (not (contains? want label)))
                        out
                        (let [score (count (set/intersection stored qt))]
                          (if (pos? score)
                            (conj out {"id" (get e "id") "name" name "label" label "score" score})
                            out)))))
                  []
                  (avet endpoint "feature/name-token" qt))]
         (->> out
              (sort-by (fn [r] [(- (get r "score")) (or (get r "name") (get r "id") "")]))
              (take limit)
              vec))))))
