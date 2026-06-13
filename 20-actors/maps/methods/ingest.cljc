(ns maps.methods.ingest
  "maps — legacy vertex_spatial → kotoba :feature/* normalizer + ingest (R0).
  1:1 Clojure port of `methods/ingest.py` (ADR-2606064500).

  Pure normalization logic (label mapping, H3 cell stamping stub, batch
  building). The --push path (HTTP kg.ingest_batch) is `#?(:clj ...)` only.

  CONSTITUTIONAL (ADR-2606064500 gates):
    G3 — every normalized feature carries :feature/sourcing :representative.
    G4 no-server-key — live push uses member/operator-DID bearer, no platform key.
    G7 outward-gated — push requires MAPS_OPERATOR_GATE=1 + --push flag.
    G9 — a feature is a PLACED THING, never a person.

  Portable .cljc."
  (:require [clojure.string :as str]
            [maps.methods.search :as search-ns]))

;; H3 resolutions the client queries (zoom→LOD ladder, mirrors ontology §2).
(def cell-resolutions [2 4 6 8 10 12])

(def label-map
  {"Place"          ":place"   "Road"          ":road"      "Railway"     ":railway"
   "Building"       ":building" "River"        ":river"     "Lake"        ":lake"
   "Coastline"      ":coastline" "AdminArea"   ":admin-area" "Mountain"  ":mountain"
   "Port"           ":port"    "Airport"       ":airport"   "Station"     ":station"
   "BusStop"        ":bus-stop" "BusRoute"     ":bus-route" "SeaRoute"   ":sea-route"
   "AirRoute"       ":air-route" "LegalEntity" ":legal-entity" "LandRegistry" ":registry"
   "SatelliteScene" ":satellite-scene" "Spot"  ":place"})

(defn normalize-label [s]
  (or (get label-map (str s))
      (str ":" (-> (str s) str/trim str/lower-case (str/replace " " "-")))))

(defn normalize-row
  "One legacy vertex_spatial row → a kotoba :feature/* map (+ H3 cell stubs).
  Returns nil when the row lacks an id."
  [row]
  (let [fid (or (get row "vertex_id") (get row "id"))]
    (when fid
      (let [lat (get row "lat")
            lon (or (get row "lng") (get row "lon"))
            props (let [p (get row "props")]
                    (cond
                      (map? p) p
                      (string? p)
                      (try #?(:clj ((requiring-resolve 'cheshire.core/parse-string) p)
                              :cljs (js->clj (js/JSON.parse p)))
                           (catch #?(:clj Exception :cljs :default) _ {}))
                      :else {}))
            feat (cond-> {":feature/id"       (str fid)
                          ":feature/label"    (normalize-label (get row "label"))
                          ":feature/sourcing" ":representative"}
                   (get row "name")         (assoc ":feature/name" (get row "name"))
                   (get row "display_name") (assoc ":feature/display-name" (get row "display_name"))
                   (get row "category")     (assoc ":feature/category" (get row "category"))
                   (get row "source_did")   (assoc ":feature/source-did" (get row "source_did"))
                   (number? lat)            (assoc ":feature/lat" lat)
                   (number? lon)            (assoc ":feature/lon" lon))
            h-m (or (get props "heightM") (get props "height_m"))
            lvl (or (get props "levels") (get props "floors"))
            geom (get props "geometry")
            rest-props (dissoc props "geometry" "heightM" "height_m" "levels" "floors")
            feat (cond-> feat
                   (number? h-m)  (assoc ":feature/height-m" (double h-m))
                   (number? lvl)  (assoc ":feature/levels" (long lvl))
                   (some? geom)   (assoc ":feature/geometry"
                                         #?(:clj ((requiring-resolve 'cheshire.core/generate-string) geom)
                                            :cljs (.stringify js/JSON (clj->js geom))))
                   (seq rest-props) (assoc ":feature/props"
                                           #?(:clj ((requiring-resolve 'cheshire.core/generate-string) rest-props)
                                              :cljs (.stringify js/JSON (clj->js rest-props)))))]
        feat))))

(defn normalize
  "export = {\"rows\" [...]} or a bare vector.
  Returns [feats-by-id stamped-count unstamped-count]."
  [export]
  (let [rows (if (map? export) (get export "rows" export) export)
        feats (volatile! {}) stamped (volatile! 0) unstamped (volatile! 0)]
    (doseq [r rows]
      (when-let [f (normalize-row r)]
        (let [fid (get f ":feature/id")]
          (vswap! feats assoc fid f)
          (if (some #(str/starts-with? (str %) ":feature.cell/") (keys f))
            (vswap! stamped inc)
            (when (contains? f ":feature/lat")
              (vswap! unstamped inc))))))
    [@feats @stamped @unstamped]))

(defn to-kg-batch
  "feature dicts → kg.ingest_batch body {\"entities\" [...]}."
  [feats]
  (let [entities
        (mapv (fn [[fid f]]
                (let [name-toks (if (fn? search-ns/name-tokens)
                                  (reduce (fn [s k]
                                            (if-let [v (get f k)]
                                              (into s (search-ns/name-tokens (str v)))
                                              s))
                                          #{}
                                          [":feature/name" ":feature/display-name"])
                                  #{})
                      claims (into (mapv (fn [[k v]]
                                           {"pred" (subs (str k) 1) "value" (str v)})
                                         (dissoc f ":feature/id"))
                                   (map (fn [t] {"pred" "feature/name-token" "value" t})
                                        (sort name-toks)))]
                  {"id"       fid
                   "type"     "maps-feature"
                   "label_en" (or (get f ":feature/name")
                                  (get f ":feature/display-name") fid)
                   "claims"   claims
                   "relations" []}))
              feats)]
    {"entities" entities}))

#?(:clj
   (defn push-batch
     "POST kg.ingest_batch JSON to the kotoba endpoint. Returns [status body]."
     [batch auth endpoint]
     (let [nsid   "com.etzhayyim.apps.kotobase.kg.ingest_batch"
           url    (str (str/replace endpoint #"/$" "") "/xrpc/" nsid)
           body   (.getBytes ((requiring-resolve 'cheshire.core/generate-string) batch) "UTF-8")
           conn   (doto (.openConnection (java.net.URL. url))
                    (.setRequestMethod "POST")
                    (.setDoOutput true)
                    (.setConnectTimeout 30000)
                    (.setReadTimeout 30000)
                    (.setRequestProperty "content-type" "application/json")
                    (.setRequestProperty "authorization" (str "Bearer " auth)))]
       (.connect conn)
       (with-open [os (.getOutputStream conn)]
         (.write os body))
       [(.getResponseCode conn)
        (slurp (.getInputStream conn))])))
