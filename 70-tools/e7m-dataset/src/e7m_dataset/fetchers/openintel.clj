;; ported from 70-tools/e7m-dataset/src/e7m_dataset/fetchers/openintel.py (unit_refactor stage 0)
;; OpenINTEL DNS active-measurement archive fetcher.
(ns src.e7m-dataset.fetchers.openintel
  (:require [clojure.string] [clojure.set] [clojure.edn]))

(declare default-base open-intel-fetch-opts build-url fetch all)

;; TODO: port-failed unit _DEFAULT_BASE (no block)
;; _DEFAULT_BASE = "https://data.openintel.nl"
(def default-base nil) ;; TODO: port-failed const

;; TODO: port-failed unit OpenIntelFetchOpts (assembled-lint error)
;; class OpenIntelFetchOpts:
;;     # Logical zone slug — e.g. "tranco1m", "com", "net", "nl". The
;;     # fetcher builds the URL as "<base>/<zone>/<year>/<month>/<day>/
;;     # <archive_file>" when archive_file does not already contain "/"".
;;     zone: str = "tranco1m"
;;     year: int = 2026
;;     month: int = 5
;;     day: int = 26
;;     archive_file: str = ""  # e.g. "tranco1m-20260526.parquet"
;;     base_url: str = _DEFAULT_BASE
;;     timeout_sec: float = 1800.0
;;     client: Optional[httpx.Client] = None
;;     acceptance_source: str = "openintel"
(defn open-intel-fetch-opts [& _]
  (throw (ex-info "TODO: port-failed" {:from "OpenIntelFetchOpts"})))

;; TODO: port-failed unit _build_url (assembled-lint error)
;; def _build_url(opts: OpenIntelFetchOpts) -> str:
;;     if "/" in opts.archive_file:
;;         # Operator passed a fully-qualified path.
;;         return f"{opts.base_url}/{opts.archive_file}"
;;     yyyy = f"{opts.year:04d}"
;;     mm = f"{opts.month:02d}"
;;     dd = f"{opts.day:02d}"
;;     return (
;;         f"{opts.base_url}/{opts.zone}/{yyyy}/{mm}/{dd}/{opts.archive_file}"
;;     )
(defn build-url [& _]
  (throw (ex-info "TODO: port-failed" {:from "_build_url"})))

;; TODO: port-failed unit fetch (/var/folders/px/b63lssbx5056kq_1t6pvc1f80000gn/T/tmp3q40vy7y/scratch.clj:2:1: er)
;; def fetch(staging_dir: Path, opts: OpenIntelFetchOpts) -> FetchResult:
;;     if not opts.archive_file:
;;         raise ValueError(
;;             "OpenIntelFetchOpts.archive_file is required "
;;             "(e.g. 'tranco1m-20260526.parquet')."
;;         )
;; 
;;     acceptance = require_acceptance(opts.acceptance_source)
;; 
;;     url = _build_url(opts)
;;     capture_ts = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
;;     archive_base = opts.archive_file.replace("/", "_")
;;     dirname = f"openintel-{opts.zone}-{archive_base}-{capture_ts}"
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
;;         name=f"openintel:{opts.zone}:{opts.archive_file}",
;;         revision=revision,
;;         staging_path=out_dir,
;;         file_count=file_count,
;;         size_bytes=size_bytes,
;;         source={
;;             "type": "http",
;;             "url": url,
;;             "zone": opts.zone,
;;             "archiveFile": opts.archive_file,
;;             "snapshotAt": f"{opts.year:04d}-{opts.month:02d}-{opts.day:02d}",
;;             "capturedAt": capture_ts,
;;             "rawSha256": raw_sha,
;;             "license": "CC-BY-NC-4.0",
;;             "tier": "C",
;;             "g13FleetInternalOnly": True,
;;             "piiSensitiveDefault": True,
;;             "attribution": (
;;                 "Source: OpenINTEL — University of Twente / SIDN Labs / "
;;                 "NLnet Labs (https://openintel.nl/)"
;;             ),
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

nil

