;; ported from 70-tools/e7m-dataset/src/e7m_dataset/fetchers/openintel.py — real port
;; replacing the unit_refactor stage-0 "TODO: port-failed" stubs. NS fixed
;; (src.e7m-dataset.* -> e7m-dataset.fetchers.openintel, matching the Python package
;; e7m_dataset.fetchers.openintel under source root src/) and the file is now .cljc.
;; Self-contained: own sha-256 + opts constructor; host file/network I/O behind #?(:clj ...).
(ns e7m-dataset.fetchers.openintel
  "OpenINTEL DNS active-measurement archive fetcher.

  1:1 Clojure port of `fetchers/openintel.py`. OpenINTEL
  (https://openintel.nl/) publishes large-scale daily DNS measurement
  archives in Parquet, scoped per zone (Tranco 1M by default). Data is
  CC-BY-NC 4.0 — Tier C, internal-only under the G13 fleet-internal carve-out.

  source maps stay string-keyed, byte-for-byte the shapes Python produced;
  Python ':kw' enum values are kept as strings. Pure except the fetch edge,
  which is behind #?(:clj ...) (host httpx-equivalent network I/O)."
  (:require [clojure.string :as str]))

(def default-base "https://data.openintel.nl")

;; ── sha-256 (self-contained, copied from danjo budget_ledger.cljc idiom) ──────
(defn- sha256-hex
  "Bytes → lowercase hex sha-256 digest."
  ^String [^bytes b]
  #?(:clj (let [d (.digest (java.security.MessageDigest/getInstance "SHA-256") b)]
            (apply str (map #(format "%02x" (bit-and % 0xff)) d)))
     :default (throw (ex-info "bind a sha-256 impl on this host" {}))))

;; ── opts (port of @dataclass OpenIntelFetchOpts) ──────────────────────────────
(defn open-intel-fetch-opts
  "Construct an OpenIntelFetchOpts map with the dataclass defaults.

  zone: logical zone slug — e.g. \"tranco1m\", \"com\", \"net\", \"nl\". The
  fetcher builds the URL as \"<base>/<zone>/<year>/<month>/<day>/<archive-file>\"
  when archive-file does not already contain \"/\"."
  [& {:keys [zone year month day archive-file base-url timeout-sec client acceptance-source]
      :or   {zone "tranco1m" year 2026 month 5 day 26 archive-file ""
             base-url default-base timeout-sec 1800.0 client nil
             acceptance-source "openintel"}}]
  {"zone" zone "year" year "month" month "day" day
   "archiveFile" archive-file "baseUrl" base-url "timeoutSec" timeout-sec
   "client" client "acceptanceSource" acceptance-source})

(defn build-url
  "Port of _build_url. Build the archive URL from opts."
  [opts]
  (let [archive-file (get opts "archiveFile")
        base-url     (get opts "baseUrl")]
    (if (str/includes? archive-file "/")
      ;; Operator passed a fully-qualified path.
      (str base-url "/" archive-file)
      (let [yyyy (format "%04d" (get opts "year"))
            mm   (format "%02d" (get opts "month"))
            dd   (format "%02d" (get opts "day"))]
        (str base-url "/" (get opts "zone") "/" yyyy "/" mm "/" dd "/" archive-file)))))

#?(:clj
   (defn- gmt-capture-ts
     "time.strftime(\"%Y%m%dT%H%M%SZ\", time.gmtime())."
     ^String []
     (.format (doto (java.text.SimpleDateFormat. "yyyyMMdd'T'HHmmss'Z'")
                (.setTimeZone (java.util.TimeZone/getTimeZone "UTC")))
              (java.util.Date.))))

#?(:clj
   (defn fetch
     "Port of fetch. Streams the named archive shard into a staged dir and
     returns a FetchResult map.

     `require-acceptance` is injected as a fn (source-slug -> acceptance map with
     keys \"source\"/\"acceptedAt\"/\"acceptedByDid\"/\"upstreamTosUrl\"); the
     Python module imported it from `._acceptance`. `download!` is injected as a
     fn (url, dest-file) -> nil performing the streamed GET (httpx equivalent)."
     [staging-dir opts require-acceptance download!]
     (let [archive-file (get opts "archiveFile")]
       (when (str/blank? archive-file)
         (throw (ex-info "OpenIntelFetchOpts.archiveFile is required (e.g. 'tranco1m-20260526.parquet')."
                         {:opts opts})))
       (let [acceptance (require-acceptance (get opts "acceptanceSource"))
             url        (build-url opts)
             capture-ts (gmt-capture-ts)
             archive-base (str/replace archive-file "/" "_")
             dirname    (str "openintel-" (get opts "zone") "-" archive-base "-" capture-ts)
             out-dir    (java.io.File. (str staging-dir) dirname)
             _          (.mkdirs out-dir)
             leaf       (last (str/split archive-file #"/"))
             archive-path (java.io.File. out-dir leaf)]
         (download! url archive-path)
         (let [raw-sha   (sha256-hex (java.nio.file.Files/readAllBytes (.toPath archive-path)))
               revision  (str "sha256:" raw-sha)
               files     (filter #(.isFile %) (file-seq out-dir))
               size-bytes (reduce + 0 (map #(.length %) files))
               file-count (count files)]
           {"name"        (str "openintel:" (get opts "zone") ":" archive-file)
            "revision"    revision
            "stagingPath" (.getPath out-dir)
            "fileCount"   file-count
            "sizeBytes"   size-bytes
            "source"      {"type" "http"
                           "url"  url
                           "zone" (get opts "zone")
                           "archiveFile" archive-file
                           "snapshotAt" (format "%04d-%02d-%02d"
                                                 (get opts "year") (get opts "month") (get opts "day"))
                           "capturedAt" capture-ts
                           "rawSha256"  raw-sha
                           "license"    "CC-BY-NC-4.0"
                           "tier"       "C"
                           "g13FleetInternalOnly" true
                           "piiSensitiveDefault"  true
                           "attribution" (str "Source: OpenINTEL — University of Twente / SIDN Labs / "
                                              "NLnet Labs (https://openintel.nl/)")
                           "acceptance" {"source"         (get acceptance "source")
                                         "acceptedAt"     (get acceptance "acceptedAt")
                                         "acceptedByDid"  (get acceptance "acceptedByDid")
                                         "upstreamTosUrl" (get acceptance "upstreamTosUrl")}}})))))

;; Python __all__ = ["OpenIntelFetchOpts", "fetch"]; __main__ demo: none.
