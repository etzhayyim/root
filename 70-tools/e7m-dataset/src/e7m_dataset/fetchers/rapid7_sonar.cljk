;; ported from 70-tools/e7m-dataset/src/e7m_dataset/fetchers/rapid7_sonar.py — real port
;; replacing the unit_refactor stage-0 "TODO: port-failed" stubs. NS fixed
;; (src.e7m-dataset.* -> e7m-dataset.fetchers.rapid7-sonar, matching the Python package
;; e7m_dataset.fetchers.rapid7_sonar under source root src/) and the file is now .cljc.
;; Self-contained; host file/network I/O behind #?(:clj ...).
(ns e7m-dataset.fetchers.rapid7-sonar
  "Rapid7 Open Data — Sonar FDNS archive fetcher.

  1:1 Clojure port of `fetchers/rapid7_sonar.py`. Rapid7's Project Sonar
  publishes globally collected forward-DNS scan archives (FDNS) under
  research-use terms. TIER C — acceptance-flag-gated ingest under the G13
  fleet-internal carve-out; pulls a single named file per invocation.

  License/TOS: research-use. NOT Apache/CC0/CC-BY publishable — Tier C,
  internal-only. source maps stay string-keyed."
  (:require [clojure.string :as str]))

(def default-base "https://opendata.rapid7.com/sonar.fdns_v2")

;; ── sha-256 (self-contained) ──────────────────────────────────────────────────
(defn- sha256-hex
  "Bytes → lowercase hex sha-256 digest."
  ^String [^bytes b]
  #?(:clj (let [d (.digest (java.security.MessageDigest/getInstance "SHA-256") b)]
            (apply str (map #(format "%02x" (bit-and % 0xff)) d)))
     :default (throw (ex-info "bind a sha-256 impl on this host" {}))))

;; ── opts (port of @dataclass Rapid7SonarFetchOpts) ────────────────────────────
(defn rapid7-sonar-fetch-opts
  "Construct a Rapid7SonarFetchOpts map with the dataclass defaults.

  archive-file: file name within the upstream archive
  (e.g. \"2026-05-23-fdns_any.json.gz\"). timeout-sec default 1800.0 — Sonar
  files run several GB."
  [& {:keys [archive-file base-url timeout-sec client acceptance-source]
      :or   {archive-file "" base-url default-base timeout-sec 1800.0 client nil
             acceptance-source "rapid7-open-data"}}]
  {"archiveFile" archive-file "baseUrl" base-url "timeoutSec" timeout-sec
   "client" client "acceptanceSource" acceptance-source})

#?(:clj
   (defn- gmt-capture-ts
     "time.strftime(\"%Y%m%dT%H%M%SZ\", time.gmtime())."
     ^String []
     (.format (doto (java.text.SimpleDateFormat. "yyyyMMdd'T'HHmmss'Z'")
                (.setTimeZone (java.util.TimeZone/getTimeZone "UTC")))
              (java.util.Date.))))

#?(:clj
   (defn fetch
     "Port of fetch. Streams the named Sonar archive shard into a staged dir and
     returns a FetchResult map.

     `require-acceptance` is injected as a fn (source-slug -> acceptance map) — the
     G13 acceptance gate runs BEFORE any HTTP request. `download!` is injected as a
     fn (url, dest-file) -> nil performing the streamed GET (httpx equivalent)."
     [staging-dir opts require-acceptance download!]
     (let [archive-file (get opts "archiveFile")]
       (when (str/blank? archive-file)
         (throw (ex-info "Rapid7SonarFetchOpts.archiveFile is required (e.g. '2026-05-23-fdns_any.json.gz')."
                         {:opts opts})))
       ;; G13 acceptance gate — runs BEFORE any HTTP request is issued.
       (let [acceptance (require-acceptance (get opts "acceptanceSource"))
             url        (str (get opts "baseUrl") "/" archive-file)
             capture-ts (gmt-capture-ts)
             dirname    (str "rapid7-sonar-" (str/replace archive-file "/" "_") "-" capture-ts)
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
           {"name"        (str "rapid7-sonar-fdns:" archive-file)
            "revision"    revision
            "stagingPath" (.getPath out-dir)
            "fileCount"   file-count
            "sizeBytes"   size-bytes
            "source"      {"type" "http"
                           "url"  url
                           "archiveFile" archive-file
                           "capturedAt" capture-ts
                           "rawSha256"  raw-sha
                           "license"    "rapid7-research-use"
                           "tier"       "C"
                           "g13FleetInternalOnly" true
                           "piiSensitiveDefault"  true
                           "acceptance" {"source"         (get acceptance "source")
                                         "acceptedAt"     (get acceptance "acceptedAt")
                                         "acceptedByDid"  (get acceptance "acceptedByDid")
                                         "upstreamTosUrl" (get acceptance "upstreamTosUrl")}}})))))

;; Python __all__ = ["Rapid7SonarFetchOpts", "fetch"]; __main__ demo: none.
