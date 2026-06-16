(ns maps.methods.reverse
  "reverse.py — kotoba-native reverse geocoding (ADR-2606064500 R2).
  1:1 Clojure port of `methods/reverse.py`.

  The kotoba-native successor to `cmdPlaceReverseGeocode`. The query point's owning H3 cell +
  its grid_disk ring bound the candidate set, then haversine ranks them.

  haversine-m is pure (always testable). _ring-cells needs h3 (absent on this host → nil, exactly
  like the Python except-branch), so reverse-geocode degrades to [] without it. The wire read
  (_avet HTTP I/O) is host-only behind #?(:clj ...). JSON inlined. Fail-soft: any error → []."
  (:require [clojure.string :as str]))

(def query-nsid "com.etzhayyim.apps.kotoba.graph.sparql")
(def ^:private timeout-ms 5000)
(def ^:private earth-r 6371000.0)

(defn haversine-m
  "Great-circle distance between two WGS84 points, in metres."
  [lat1 lon1 lat2 lon2]
  (let [p1 (Math/toRadians lat1)
        p2 (Math/toRadians lat2)
        dp (Math/toRadians (- lat2 lat1))
        dl (Math/toRadians (- lon2 lon1))
        a (+ (Math/pow (Math/sin (/ dp 2)) 2)
             (* (Math/cos p1) (Math/cos p2) (Math/pow (Math/sin (/ dl 2)) 2)))]
    (* 2 earth-r (Math/asin (min 1.0 (Math/sqrt a))))))

(defn- ring-cells
  "The point's owning H3 cell + `ring` rings, or nil if h3 is unavailable (this host → nil)."
  [_lat _lon _res _ring]
  nil)

;; ── inlined JSON + HTTP ─────────────────────────────────────────────────────────
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
           (finally (.close sock)))))))

(defn- avet
  ([endpoint predicate objects] (avet endpoint predicate objects 4000))
  ([endpoint predicate objects limit]
   #?(:clj
      (let [body {"index" "avet" "predicate" predicate "objects" (vec objects) "limit" limit}]
        (try
          (get (http-post-json (str (str/replace endpoint #"/+$" "") "/xrpc/" query-nsid) body) "entities" [])
          (catch Exception _ [])))
      :default [])))

(defn- round1 [x]
  (/ (Math/round (* (double x) 10.0)) 10.0))

(defn reverse-geocode
  "Nearest features to (lat, lon), nearest first. Returns
  [{id, name, label, lat, lon, distanceM}]. Empty if h3 absent or nothing in range."
  ([endpoint lat lon] (reverse-geocode endpoint lat lon {}))
  ([endpoint lat lon {:keys [res ring labels limit] :or {res 10 ring 2 limit 5}}]
   (let [cells (ring-cells lat lon res ring)]
     (if-not (seq cells)
       []
       (let [want (when (seq labels)
                    (set (map (fn [l] (if (str/starts-with? (str l) ":") (str l) (str ":" l))) labels)))
             out (reduce
                  (fn [out e]
                    (let [{:keys [flat flon name label]}
                          (reduce (fn [acc c]
                                    (let [p (get c "pred") v (get c "value")]
                                      (cond
                                        (= p "feature/lat") (assoc acc :flat (try (double (Double/parseDouble (str v))) (catch Exception _ (:flat acc))))
                                        (= p "feature/lon") (assoc acc :flon (try (double (Double/parseDouble (str v))) (catch Exception _ (:flon acc))))
                                        (= p "feature/name") (assoc acc :name v)
                                        (= p "feature/label") (assoc acc :label v)
                                        :else acc)))
                                  {:flat nil :flon nil :name nil :label nil}
                                  (get e "claims" []))]
                      (cond
                        (or (nil? flat) (nil? flon)) out
                        (and want (not (contains? want label))) out
                        :else (conj out {"id" (get e "id") "name" name "label" label
                                         "lat" flat "lon" flon
                                         "distanceM" (round1 (haversine-m lat lon flat flon))}))))
                  []
                  (avet endpoint (str "feature.cell/r" res) cells))]
         (->> out (sort-by #(get % "distanceM")) (take limit) vec))))))
