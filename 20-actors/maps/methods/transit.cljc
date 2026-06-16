(ns maps.methods.transit
  "transit.py — kotoba-native transit reads (ADR-2606064500 R2 aux).
  1:1 Clojure port of `methods/transit.py`.

  The READ complement to the GTFS aux write path. next-departures-at-stop / trips-on-route each
  become a single AVET probe over the Datom log, sorted client-side. GTFS departure_time may
  exceed 24:00:00; it stays textual and sorts correctly as text within a service day.

  The wire read (_avet HTTP I/O) is host-only behind #?(:clj ...). JSON inlined. Fail-soft → []."
  (:require [clojure.string :as str]))

(def query-nsid "com.etzhayyim.apps.kotoba.graph.sparql")
(def ^:private timeout-ms 5000)

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
  "One AVET predicate+object probe → entity maps. Fail-soft → []."
  ([endpoint predicate objects] (avet endpoint predicate objects 2000))
  ([endpoint predicate objects limit]
   #?(:clj
      (let [body {"index" "avet" "predicate" predicate "objects" (vec objects) "limit" limit}]
        (try
          (get (http-post-json (str (str/replace endpoint #"/+$" "") "/xrpc/" query-nsid) body) "entities" [])
          (catch Exception _ [])))
      :default [])))

(defn- claims [entity]
  (reduce (fn [m c] (if (get c "pred") (assoc m (get c "pred") (get c "value")) m))
          {}
          (get entity "claims" [])))

(defn next-departures-at-stop
  "Next scheduled departures at a stop, sorted by departure time (earliest first, ≥ `after`).
  Returns [{stopTime, trip, departure, arrival, headsign, sequence}]."
  ([endpoint stop-id] (next-departures-at-stop endpoint stop-id "00:00:00" 10))
  ([endpoint stop-id after] (next-departures-at-stop endpoint stop-id after 10))
  ([endpoint stop-id after limit]
   (let [rows (reduce
               (fn [rows e]
                 (let [c (claims e)
                       dep (get c "transit.stop-time/departure-time")]
                   (if (or (not dep) (< (compare dep after) 0))
                     rows
                     (conj rows {"stopTime" (get e "id")
                                 "trip" (get c "transit.stop-time/trip")
                                 "departure" dep
                                 "arrival" (get c "transit.stop-time/arrival-time")
                                 "headsign" (get c "transit.stop-time/headsign")
                                 "sequence" (get c "transit.stop-time/sequence")}))))
               []
               (avet endpoint "transit.stop-time/stop" [stop-id]))]
     (->> rows (sort-by #(get % "departure")) (take limit) vec))))

(defn trips-on-route
  "All trips on a route (idx_maps_trip_route successor)."
  ([endpoint route-id] (trips-on-route endpoint route-id 2000))
  ([endpoint route-id limit]
   (vec
    (for [e (avet endpoint "transit.trip/route" [route-id] limit)]
      (let [c (claims e)]
        {"trip" (get e "id")
         "headsign" (get c "transit.trip/headsign")
         "service" (get c "transit.trip/service")
         "direction" (get c "transit.trip/direction")})))))
