(ns maps.methods.chunk
  "chunk.py — kotoba-native chunk read (ADR-2606064500 §2).
  1:1 Clojure port of `methods/chunk.py`.

  The HTTP reference for `cmdGetChunk` — the maps-3d / 2D-overlay hot-path. Same AVET cell probe,
  same grouped-GeoJSON output shape as the legacy getChunk.

  fold-label / _feature shaping is pure; the wire read (_avet HTTP I/O) is host-only behind
  #?(:clj ...). JSON encode/parse is inlined (self-contained). Fail-soft: any error → empty chunks."
  (:require [clojure.string :as str]))

(def query-nsid "com.etzhayyim.apps.kotoba.graph.sparql")
(def ^:private timeout-ms 5000)

(def ^:private label-map
  {"Place" ":place" "Road" ":road" "Railway" ":railway" "Building" ":building"
   "River" ":river" "Lake" ":lake" "Coastline" ":coastline" "AdminArea" ":admin-area"
   "Mountain" ":mountain" "Port" ":port" "Airport" ":airport" "Station" ":station"
   "BusStop" ":bus-stop" "BusRoute" ":bus-route" "SeaRoute" ":sea-route"
   "AirRoute" ":air-route" "LegalEntity" ":legal-entity" "LandRegistry" ":registry"})

(defn fold-label [label]
  (if (str/starts-with? label ":")
    label
    (get label-map label (str ":" (str/replace (str/lower-case (str/trim label)) " " "-")))))

;; ── inlined JSON ──────────────────────────────────────────────────────────────
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
     (defn- http-post-json [^String url body-map]
       (let [u (java.net.URI. url)
             host (.getHost u)
             port (let [p (.getPort u)] (if (pos? p) p 80))
             path (.getRawPath u)
             body (json-encode body-map)
             bb (.getBytes body "UTF-8")
             sock (java.net.Socket.)]
         (try
           (.connect sock (java.net.InetSocketAddress. host port) timeout-ms)
           (.setSoTimeout sock timeout-ms)
           (let [out (.getOutputStream sock) in (.getInputStream sock)]
             (.write out (.getBytes (str "POST " path " HTTP/1.1\r\nHost: " host "\r\n"
                                         "content-type: application/json\r\n"
                                         "Connection: close\r\n"
                                         "Content-Length: " (count bb) "\r\n\r\n") "UTF-8"))
             (.write out bb) (.flush out)
             (read-line-crlf in)
             (let [cl (read-headers in)]
               (parse-json (read-n in cl))))
           (finally (.close sock)))))
     (defn- parse-json* [text] (parse-json text))))

(defn- avet
  ([endpoint predicate objects] (avet endpoint predicate objects 8000))
  ([endpoint predicate objects limit]
   #?(:clj
      (let [body {"index" "avet" "predicate" predicate "objects" (vec objects) "limit" limit}]
        (try
          (get (http-post-json (str (str/replace endpoint #"/+$" "") "/xrpc/" query-nsid) body) "entities" [])
          (catch Exception _ [])))
      :default [])))

(defn- feature*
  "A matching entity → [owning-cell label GeoJSON-Feature]."
  [entity lod]
  (let [c (reduce (fn [c cl]
                    (let [p (get cl "pred") v (get cl "value")]
                      (if (and p (not (contains? c p))) (assoc c p v) c)))
                  {}
                  (get entity "claims" []))
        owner (get c (str "feature.cell/r" lod))
        label (get c "feature/label")
        geom (cond
               (get c "feature/geometry")
               #?(:clj (try (parse-json* (get c "feature/geometry")) (catch Exception _ nil)) :default nil)
               :else nil)
        geom (if (and (nil? geom) (get c "feature/lat") (get c "feature/lon"))
               (try {"type" "Point"
                     "coordinates" [(double (#?(:clj Double/parseDouble :default js/parseFloat) (get c "feature/lon")))
                                    (double (#?(:clj Double/parseDouble :default js/parseFloat) (get c "feature/lat")))]}
                    (catch #?(:clj Exception :cljs js/Error) _ nil))
               geom)
        feat {"type" "Feature"
              "geometry" geom
              "properties" {"id" (get entity "id")
                            "name" (get c "feature/name")
                            "label" label
                            "category" (get c "feature/category")
                            "heightM" (get c "feature/height-m")
                            "levels" (get c "feature/levels")}}]
    [owner label feat]))

(defn get-chunk
  "getChunk-equivalent: per requested cell, the features owning it, grouped by label."
  ([endpoint h3-cells lod] (get-chunk endpoint h3-cells lod nil 500))
  ([endpoint h3-cells lod labels] (get-chunk endpoint h3-cells lod labels 500))
  ([endpoint h3-cells lod labels limit]
   (let [cells (vec (distinct (map str h3-cells)))
         want (when (seq labels) (set (map (fn [l] (fold-label (str l))) labels)))
         lod (long lod)
         cellset (set cells)
         init-chunks (into (array-map) (map (fn [c] [c {}]) cells))]
     (loop [es (avet endpoint (str "feature.cell/r" lod) cells)
            chunks init-chunks
            total 0]
       (if (empty? es)
         {"chunks" chunks "lod" lod "total" total}
         (let [[owner label feat] (feature* (first es) lod)]
           (cond
             (or (not (contains? cellset owner)) (not label))
             (recur (rest es) chunks total)
             (and want (not (contains? want label)))
             (recur (rest es) chunks total)
             :else
             (let [bucket (get-in chunks [owner label] [])]
               (if (>= (count bucket) limit)
                 (recur (rest es) chunks total)
                 (recur (rest es) (assoc-in chunks [owner label] (conj bucket feat)) (inc total)))))))))))
