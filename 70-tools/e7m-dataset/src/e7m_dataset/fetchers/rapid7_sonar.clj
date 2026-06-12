;; ported from 70-tools/e7m-dataset/src/e7m_dataset/fetchers/rapid7_sonar.py (unit_refactor stage 0)
;; Rapid7 Open Data — Sonar FDNS archive fetcher.
(ns src.e7m-dataset.fetchers.rapid7-sonar
  (:require [clojure.string] [clojure.set] [clojure.edn]))

(declare default-base rapid7-sonar-fetch-opts fetch all)

(def default-base "https://opendata.rapid7.com/sonar.fdns_v2")

;; TODO: port-failed unit Rapid7SonarFetchOpts (assembled-lint error)
;; class Rapid7SonarFetchOpts:
;;     # File name within the upstream archive (e.g. "2026-05-23-fdns_any.json.gz").
;;     archive_file: str = ""
;;     base_url: str = _DEFAULT_BASE
;;     timeout_sec: float = 1800.0  # Sonar files run several GB
;;     client: Optional[httpx.Client] = None
;;     # Source slug used for the acceptance flag lookup. Overridable for
;;     # tests; production callers should leave the default.
;;     acceptance_source: str = "rapid7-open-data"
(defn rapid7-sonar-fetch-opts [& _]
  (throw (ex-info "TODO: port-failed" {:from "Rapid7SonarFetchOpts"})))

;; TODO: port-failed unit fetch (/var/folders/px/b63lssbx5056kq_1t6pvc1f80000gn/T/tmpgpv3sm59/scratch.clj:2:1: er)
;; def fetch(staging_dir: Path, opts: Rapid7SonarFetchOpts) -> FetchResult:
;;     if not opts.archive_file:
;;         raise ValueError(
;;             "Rapid7SonarFetchOpts.archive_file is required "
;;             "(e.g. '2026-05-23-fdns_any.json.gz')."
;;         )
;; 
;;     # G13 acceptance gate — runs BEFORE any HTTP request is issued.
;;     acceptance = require_acceptance(opts.acceptance_source)
;; 
;;     url = f"{opts.base_url}/{opts.archive_file}"
;;     capture_ts = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
;;     dirname = f"rapid7-sonar-{opts.archive_file.replace('/', '_')}-{capture_ts}"
;;     out_dir = staging_dir / dirname
;;     out_dir.mkdir(parents=True, exist_ok=True)
;; 
;;     archive_path = out_dir / opts.archive_file.rsplit("/", 1)[-1]
;; 
;;     owned_client = opts.client is None
;;     client = opts.client or httpx.Client(
;;         timeout=opts.timeout_sec, follow_redirects=True
;;     )
;;     try:
;;         with client.stream("GET", url) as resp:
;;             resp.raise_for_status()
;;             with archive_path.open("wb") as f:
;;                 for chunk in resp.iter_bytes(chunk_size=64 * 1024):
;;                     f.write(chunk)
;;     finally:
;;         if owned_client:
;;             client.close()
;; 
;;     raw_sha = hashlib.sha256(archive_path.read_bytes()).hexdigest()
;;     revision = f"sha256:{raw_sha}"
;; 
;;     size_bytes = sum(
;;         p.stat().st_size for p in out_dir.rglob("*") if p.is_file()
;;     )
;;     file_count = sum(1 for p in out_dir.rglob("*") if p.is_file())
;; 
;;     return FetchResult(
;;         name=f"rapid7-sonar-fdns:{opts.archive_file}",
;;         revision=revision,
;;         staging_path=out_dir,
;;         file_count=file_count,
;;         size_bytes=size_bytes,
;;         source={
;;             "type": "http",
;;             "url": url,
;;             "archiveFile": opts.archive_file,
;;             "capturedAt": capture_ts,
;;             "rawSha256": raw_sha,
;;             "license": "rapid7-research-use",
;;             "tier": "C",
;;             "g13FleetInternalOnly": True,
;;             "piiSensitiveDefault": True,
;;             "acceptance": {
;;                 "source": acceptance.source,
;;                 "acceptedAt": acceptance.accepted_at,
;;                 "acceptedByDid": acceptance.accepted_by_did,
;;                 "upstreamTosUrl": acceptance.upstream_tos_url,
;;             },
;;         },
;;     )
(defn fetch [& _]
  (throw (ex-info "TODO: port-failed" {:from "fetch"})))

(def __all__ ["rapid7-sonarfetch-opts" "fetch"])

