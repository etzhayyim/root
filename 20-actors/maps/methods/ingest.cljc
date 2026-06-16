(ns maps.methods.ingest
  "ingest.py — legacy vertex_spatial → kotoba :feature/* normalizer + ingest (R0).
  1:1 Clojure port of `methods/ingest.py` (ADR-2606064500).

  Reads a legacy RisingWave `vertex_spatial` export and normalizes each row into a kotoba-EDN
  `:feature/*` entity, stamps the H3-cell spatial index when an `h3` package is present (never,
  on this host — h3 is unavailable, mirroring the Python no-h3 path), and converts to a
  `kg.ingest_batch` body for the kotoba Datom log.

  Pure normalization (normalize-row / normalize / to-kg-batch / render-features-edn) is portable.
  File/env/network I/O (push-batch / main) is host-only behind #?(:clj ...). JSON encode/parse is
  inlined (self-contained, danjo/methods/budget_ledger.cljc style). The __main__ demo's stdout
  printing is omitted; `main` keeps the gate/file behavior the tests exercise.

  NOTE on H3: like the Python module on a host without `h3`, _h3-cell raises and _stamp-cells
  returns {} — so every lat/lon feature awaits TS-adapter stamping (the 'unstamped' path)."
  (:require [clojure.string :as str]
            [maps.methods.search :as search]
            [maps.methods.analyze :as analyze]))

;; H3 resolutions the client queries (the app's zoom→LOD ladder).
(def cell-resolutions [2 4 6 8 10 12])

;; legacy vertex_spatial.label (PascalCase) → kotoba :feature/label keyword
(def ^:private label-map
  {"Place" ":place" "Road" ":road" "Railway" ":railway" "Building" ":building"
   "River" ":river" "Lake" ":lake" "Coastline" ":coastline" "AdminArea" ":admin-area"
   "Mountain" ":mountain" "Port" ":port" "Airport" ":airport" "Station" ":station"
   "BusStop" ":bus-stop" "BusRoute" ":bus-route" "SeaRoute" ":sea-route"
   "AirRoute" ":air-route" "LegalEntity" ":legal-entity" "LandRegistry" ":registry"
   "SatelliteScene" ":satellite-scene" "Spot" ":place"})

(defn label* [legacy]
  (get label-map legacy (str ":" (str/replace (str/lower-case (str/trim (str legacy))) " " "-"))))

(defn- number? [v] (and (clojure.core/number? v) (not (boolean? v))))

(defn- stamp-cells
  "Owning H3 cell at each queryable resolution, or [{} false] when h3 is absent (this host)."
  [_lat _lon]
  ;; h3 is unavailable on this host: mirror the Python `except Exception: return {}, False`.
  [{} false])

;; ── inlined JSON (encode + parse subset) ──────────────────────────────────────
(defn- json-escape ^String [^String s]
  (str/escape s {\" "\\\"" \\ "\\\\"
                 \backspace "\\b" \tab "\\t" \newline "\\n" \formfeed "\\f" \return "\\r"}))

(defn json-encode ^String [v]
  (cond
    (nil? v)        "null"
    (string? v)     (str "\"" (json-escape v) "\"")
    (boolean? v)    (if v "true" "false")
    (integer? v)    (str v)
    (number? v)     (str v)
    (map? v)        (str "{" (str/join ", " (map (fn [[k val]] (str "\"" (json-escape (str k)) "\": " (json-encode val))) v)) "}")
    (sequential? v) (str "[" (str/join ", " (map json-encode v)) "]")
    :else           (str "\"" (json-escape (str v)) "\"")))

(defn- json-encode-compact ^String [v]
  (cond
    (nil? v)        "null"
    (string? v)     (str "\"" (json-escape v) "\"")
    (boolean? v)    (if v "true" "false")
    (integer? v)    (str v)
    (number? v)     (str v)
    (map? v)        (str "{" (str/join ", " (map (fn [[k val]] (str "\"" (json-escape (str k)) "\": " (json-encode-compact val))) v)) "}")
    (sequential? v) (str "[" (str/join ", " (map json-encode-compact v)) "]")
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
     (defn parse-json [text] (first (json-value text 0)))))

(defn normalize-row
  "One legacy vertex_spatial row → a kotoba :feature/* map (+ H3 cells if available).
  Returns an ordered map mirroring Python dict insertion order."
  [row]
  (let [fid (or (get row "vertex_id") (get row "id"))]
    (when fid
      (let [lat (get row "lat")
            lon (get row "lng" (get row "lon"))
            props0 (get row "props")
            props (cond
                    (string? props0) (or #?(:clj (try (parse-json props0) (catch Exception _ {})) :default {}) {})
                    (nil? props0) {}
                    :else props0)
            base (array-map ":feature/id" (str fid)
                            ":feature/label" (label* (get row "label"))
                            ":feature/sourcing" ":representative")
            feat (reduce
                  (fn [feat [key attr]]
                    (let [v (get row key)]
                      (if (and (not (nil? v)) (not= v "")) (assoc feat attr v) feat)))
                  base
                  [["name" ":feature/name"] ["display_name" ":feature/display-name"]
                   ["category" ":feature/category"] ["source_did" ":feature/source-did"]])
            feat (if (number? lat) (assoc feat ":feature/lat" lat) feat)
            feat (if (number? lon) (assoc feat ":feature/lon" lon) feat)
            h (get props "heightM" (get props "height_m"))
            feat (if (number? h) (assoc feat ":feature/height-m" (double h)) feat)
            lv (get props "levels" (get props "floors"))
            feat (if (number? lv) (assoc feat ":feature/levels" (long lv)) feat)
            geom (get props "geometry")
            feat (if (some? geom) (assoc feat ":feature/geometry" (json-encode geom)) feat)
            rest-props (reduce dissoc props ["geometry" "heightM" "height_m" "levels" "floors"])
            feat (if (seq rest-props) (assoc feat ":feature/props" (json-encode rest-props)) feat)
            [cells _] (stamp-cells lat lon)]
        (merge feat cells)))))

(defn normalize
  "export = {\"rows\": [<vertex_spatial row>, ...]} (or a bare list)."
  [export]
  (let [rows (cond
               (and (map? export) (contains? export "rows")) (get export "rows")
               (map? export) export
               :else export)]
    (reduce
     (fn [[feats stamped unstamped] r]
       (let [f (normalize-row r)]
         (if-not f
           [feats stamped unstamped]
           (let [feats (assoc feats (get f ":feature/id") f)]
             (cond
               (some #(str/starts-with? % ":feature.cell/") (keys f)) [feats (inc stamped) unstamped]
               (contains? f ":feature/lat") [feats stamped (inc unstamped)]
               :else [feats stamped unstamped])))))
     [(array-map) 0 0]
     rows)))

(defn to-kg-batch
  ":feature/* maps → kg.ingest_batch body (kamado/watari shape).
  Also stamps :feature/name-token search-index claims."
  [feats]
  {"entities"
   (vec
    (for [[fid f] feats]
      (let [claims (vec (for [[k v] f
                              :when (and (not= k ":feature/id") (not (nil? v)) (not= v ""))]
                          {"pred" (subs k 1) "value" (str v)}))
            toks (reduce (fn [toks nk]
                           (if (get f nk) (into toks (search/name-tokens (str (get f nk)))) toks))
                         #{}
                         [":feature/name" ":feature/display-name"])
            claims (into claims (for [t (sort toks)] {"pred" "feature/name-token" "value" t}))]
        {"id" fid
         "type" "maps-feature"
         "label_en" (or (get f ":feature/name") (get f ":feature/display-name") fid)
         "claims" claims
         "relations" []})))})

(defn- edn-val
  "Serialize a value as EDN (keywords kept verbatim, strings quoted)."
  [v]
  (cond
    (boolean? v) (if v "true" "false")
    (number? v) (str v)
    (string? v) (if (str/starts-with? v ":")
                  v
                  (str "\"" (-> v (str/replace "\\" "\\\\") (str/replace "\"" "\\\"")) "\""))
    :else (str "\"" v "\"")))

(defn render-features-edn
  ":feature/* maps → a kotoba-EDN vector (the backfill artifact, R1)."
  [feats]
  (let [header [";; maps — backfilled :feature/* graph (ADR-2606064500 R1)."
                ";; legacy vertex_spatial export normalized to kotoba EAVT, deduped vs seed."
                "["]
        body (for [fid (sort (keys feats))]
               (let [f (get feats fid)
                     pairs (str/join " " (for [[k v] f :when (and (not (nil? v)) (not= v ""))]
                                           (str k " " (edn-val v))))]
                 (str " {" pairs "}")))]
    (str (str/join "\n" (concat header body ["]"])) "\n")))

#?(:clj
   (defn dedup-vs-seed
     "Drop features whose :feature/id already exists in the seed (seed identity wins)."
     [feats seed-path]
     (let [seed-feats (try (first (analyze/classify (analyze/load-edn seed-path)))
                           (catch Exception _ {}))
           kept (into (array-map) (filter (fn [[fid _]] (not (contains? seed-feats fid))) feats))]
       [kept (- (count feats) (count kept))])))

#?(:clj
   (do
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
     (defn- read-status+headers [^java.io.InputStream in]
       (let [status (read-line-crlf in)
             code (try (Integer/parseInt (second (str/split status #" "))) (catch Exception _ 0))]
         (loop [cl 0]
           (let [l (read-line-crlf in)]
             (if (or (nil? l) (= l "")) [code cl]
                 (recur (if (str/starts-with? (str/lower-case l) "content-length:")
                          (Integer/parseInt (str/trim (subs l (inc (str/index-of l ":"))))) cl)))))))
     (defn push-batch
       "POST a kg.ingest_batch body with a member/operator Bearer. Returns [status body-string]."
       ([batch auth endpoint] (push-batch batch auth endpoint "com.etzhayyim.apps.kotobase.kg.ingest_batch"))
       ([batch auth endpoint nsid]
        (let [url (str (str/replace endpoint #"/+$" "") "/xrpc/" nsid)
              u (java.net.URI. url)
              host (.getHost u)
              port (let [p (.getPort u)] (if (pos? p) p 80))
              path (.getRawPath u)
              body (json-encode-compact batch)
              bb (.getBytes body "UTF-8")
              sock (java.net.Socket.)]
          (try
            (.connect sock (java.net.InetSocketAddress. host port) 30000)
            (.setSoTimeout sock 30000)
            (let [out (.getOutputStream sock) in (.getInputStream sock)]
              (.write out (.getBytes (str "POST " path " HTTP/1.1\r\nHost: " host "\r\n"
                                          "authorization: Bearer " auth "\r\n"
                                          "content-type: application/json\r\n"
                                          "Connection: close\r\n"
                                          "Content-Length: " (count bb) "\r\n\r\n") "UTF-8"))
              (.write out bb) (.flush out)
              (let [[code cl] (read-status+headers in)]
                [code (read-n in cl)]))
            (finally (.close sock))))))))

;; Env access behind an indirection so the gate paths are testable on a host that cannot
;; mutate its own process env (the JVM); defaults to the real process env.
#?(:clj (def ^:dynamic *getenv* (fn [k] (System/getenv k))))

#?(:clj
   (defn main
     "Faithful port of the Python `main(argv)`. Throws ex-info to mirror sys.exit on the
     gate-refusal paths (the tests assert these). `argv` includes argv[0] like Python."
     [argv]
     (let [argv (vec argv)
           idx (fn [flag] (.indexOf argv flag))]
       (when-not (some #{"--export"} argv)
         (throw (ex-info "usage: ingest.py --export <file>" {:exit 1})))
       (let [export-path (nth argv (inc (idx "--export")))
             export (parse-json (slurp export-path))
             [feats _stamped _unstamped] (normalize export)
             batch (to-kg-batch feats)
             actor-root (-> (java.io.File. (str *file*)) .getAbsoluteFile .getParentFile .getParentFile)
             outdir (if (some #{"--out"} argv)
                      (java.io.File. (str (nth argv (inc (idx "--out")))))
                      (java.io.File. actor-root "out"))]
         (cond
           (some #{"--emit-edn"} argv)
           (let [seed-path (str (java.io.File. (java.io.File. actor-root "data") "seed-spatial-graph.kotoba.edn"))
                 [kept _dropped] (dedup-vs-seed feats seed-path)]
             (.mkdirs outdir)
             (spit (java.io.File. outdir "spatial-graph.backfilled.kotoba.edn") (render-features-edn kept))
             :emitted)

           (some #{"--push"} argv)
           (do
             (when (not= (*getenv* "MAPS_OPERATOR_GATE") "1")
               (throw (ex-info (str "maps G7: live kg.ingest_batch push is Council+operator gated. "
                                    "Set MAPS_OPERATOR_GATE=1 with attestation to enable. "
                                    "Default offline mode writes the batch locally.")
                               {:exit 1})))
             (let [auth (*getenv* "KOTOBA_AUTH")
                   endpoint (*getenv* "KOTOBA_ENDPOINT")]
               (when-not (and auth endpoint (seq auth) (seq endpoint))
                 (throw (ex-info (str "maps G4/G7: --push needs KOTOBA_AUTH (member/operator DID bearer) + "
                                      "KOTOBA_ENDPOINT. The maps Worker holds no server key (no-server-key).")
                                 {:exit 1})))
               (push-batch batch auth endpoint)
               :pushed))

           :else
           (do
             (.mkdirs outdir)
             (spit (java.io.File. outdir "features.kg-batch.json") (json-encode batch))
             :wrote))))))
