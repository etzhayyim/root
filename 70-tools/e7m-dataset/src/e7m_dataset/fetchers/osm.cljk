;; ported from 70-tools/e7m-dataset/src/e7m_dataset/fetchers/osm.py — real port
;; replacing the unit_refactor stage-0 "TODO: port-failed" stubs. NS fixed
;; (src.e7m-dataset.* -> e7m-dataset.fetchers.osm, matching the Python package
;; e7m_dataset.fetchers.osm under source root src/) and the file is now .cljc.
;; Self-contained; host file/network I/O behind #?(:clj ...).
(ns e7m-dataset.fetchers.osm
  "OSM PBF extract fetcher (Geofabrik mirror).

  1:1 Clojure port of `fetchers/osm.py`. Stages a regional .osm.pbf under
  ${ETZ_DATASET_ROOT}/datasets-staging/osm-{region-slug}-{captureTs}/.
  Region is the Geofabrik path slug (no leading slash, no extension), e.g.:
    japan                      -> asia/japan-latest.osm.pbf
    asia/japan                 -> asia/japan-latest.osm.pbf (explicit)
    europe/germany/berlin      -> europe/germany/berlin-latest.osm.pbf

  source maps stay string-keyed, byte-for-byte the shapes Python produced."
  (:require [clojure.string :as str]))

(def default-base-url "https://download.geofabrik.de")

;; Top-level Geofabrik regions — used to expand a bare region slug like
;; "japan" -> "asia/japan" automatically. Operator can always pass the full slug.
(def geofabrik-top-level
  #{"africa" "antarctica" "asia" "australia-oceania" "central-america"
    "europe" "north-america" "russia" "south-america"})

;; Common shortcuts for popular regions (single-word slugs that resolve
;; to a known continent/country).
(def region-aliases
  {"japan" "asia/japan"
   "germany" "europe/germany"
   "france" "europe/france"
   "spain" "europe/spain"
   "italy" "europe/italy"
   "united-kingdom" "europe/united-kingdom"
   "great-britain" "europe/great-britain"
   "us" "north-america/us"
   "usa" "north-america/us"
   "canada" "north-america/canada"
   "mexico" "north-america/mexico"
   "brazil" "south-america/brazil"
   "india" "asia/india"
   "china" "asia/china"
   "korea" "asia/south-korea"
   "south-korea" "asia/south-korea"})

;; ── sha-256 (self-contained) ──────────────────────────────────────────────────
(defn- sha256-hex
  "Bytes → lowercase hex sha-256 digest."
  ^String [^bytes b]
  #?(:clj (let [d (.digest (java.security.MessageDigest/getInstance "SHA-256") b)]
            (apply str (map #(format "%02x" (bit-and % 0xff)) d)))
     :default (throw (ex-info "bind a sha-256 impl on this host" {}))))

;; ── opts (port of @dataclass OsmFetchOpts) ────────────────────────────────────
(defn osm-fetch-opts
  "Construct an OsmFetchOpts map. `region` is required (no default)."
  [region & {:keys [base-url timeout-sec fetch-md5 client]
             :or   {base-url default-base-url timeout-sec 1800.0 fetch-md5 true client nil}}]
  {"region" region "baseUrl" base-url "timeoutSec" timeout-sec
   "fetchMd5" fetch-md5 "client" client})

(defn resolve-region
  "Port of _resolve_region. Normalize the region slug to a Geofabrik path."
  [region]
  (cond
    (str/includes? region "/") region
    (contains? region-aliases region) (get region-aliases region)
    ;; User asked for an entire continent dump — Geofabrik provides these at
    ;; the top level: e.g. 'europe-latest.osm.pbf'.
    (contains? geofabrik-top-level region) region
    :else (throw (ex-info (str "unknown OSM region slug '" region "'. Pass a full Geofabrik path "
                               "(e.g. 'asia/japan', 'europe/germany/berlin') or one of the "
                               "known aliases: " (pr-str (sort (keys region-aliases))))
                          {:region region}))))

#?(:clj
   (defn- gmt-capture-ts
     "time.strftime(\"%Y%m%dT%H%M%SZ\", time.gmtime())."
     ^String []
     (.format (doto (java.text.SimpleDateFormat. "yyyyMMdd'T'HHmmss'Z'")
                (.setTimeZone (java.util.TimeZone/getTimeZone "UTC")))
              (java.util.Date.))))

#?(:clj
   (defn fetch
     "Port of fetch. Streams the regional PBF (+ optional MD5 sidecar) into a
     staged dir and returns a FetchResult map.

     `download!` is injected as a fn (url, dest-file) -> nil performing the
     streamed GET. `get-md5` is injected as a fn (url) -> md5-text-string or nil
     (nil = sidecar absent / non-200; non-fatal, mirroring the Python branch)."
     [staging-dir opts download! get-md5]
     (let [region-path (resolve-region (get opts "region"))
           base-url    (get opts "baseUrl")
           pbf-url     (str base-url "/" region-path "-latest.osm.pbf")
           md5-url     (str pbf-url ".md5")
           capture-ts  (gmt-capture-ts)
           region-slug (str/replace region-path "/" "-")
           dataset-dirname (str "osm-" region-slug "-" capture-ts)
           out-dir     (java.io.File. (str staging-dir) dataset-dirname)
           _           (.mkdirs out-dir)
           pbf-path    (java.io.File. out-dir (str region-slug "-latest.osm.pbf"))]
       (download! pbf-url pbf-path)
       (let [md5-text (when (get opts "fetchMd5")
                        (let [t (get-md5 md5-url)]
                          (when t
                            (spit (java.io.File. out-dir (str region-slug "-latest.osm.pbf.md5")) t)
                            t)))
             ;; Revision = Geofabrik-published MD5 when available; falls back to
             ;; the local sha256 of the downloaded PBF.
             revision (if md5-text
                        (str "md5:" (str/trim (first (str/split md5-text #"\s+"))))
                        (str "sha256:" (sha256-hex (java.nio.file.Files/readAllBytes (.toPath pbf-path)))))
             files     (filter #(.isFile %) (.listFiles out-dir))
             size-bytes (reduce + 0 (map #(.length %) files))
             file-count (count files)]
         {"name"        (str "osm:" region-path)
          "revision"    revision
          "stagingPath" (.getPath out-dir)
          "fileCount"   file-count
          "sizeBytes"   size-bytes
          "source"      {"type" "http"
                         "url"  pbf-url
                         "region" region-path
                         "captured_at" capture-ts
                         "md5_url" (when (get opts "fetchMd5") md5-url)}}))))

;; Python __all__ = ["DEFAULT_BASE_URL","GEOFABRIK_TOP_LEVEL","OsmFetchOpts","REGION_ALIASES","fetch"].
;; __main__ demo: none.
