"""Patent pipeline primitives — 4 Zeebe task types.

Pipeline coverage:
  patentBlobConvert.bpmn    → patent.blob.convert
  ingestUsptoWeekly.bpmn    → patent.usptoPatentsview.ingestPatent
                            → patent.usptoPatentsview.ingestCitation
  ingestEpoCitationFill.bpmn → patent.epoOps.fillCitations

ADR-0056 BPMN-as-actor.

Env vars:
  EPO_OPS_CLIENT_KEY     EPO OPS OAuth2 client key (from https://ops.epo.org)
  EPO_OPS_CLIENT_SECRET  EPO OPS OAuth2 client secret
  B2_ACCESS_KEY_ID       Backblaze B2 application key ID
  B2_SECRET_ACCESS_KEY   Backblaze B2 application key
  B2_ENDPOINT            e.g. https://s3.us-west-004.backblazeb2.com

Tools required for patent.blob.convert on the worker pod:
  pdftotext  (poppler-utils)
  cwebp      (webp)
"""

from __future__ import annotations

from datetime import datetime, timezone
from pymagatama.kotoba_datomic import get_kotoba_client

# ──────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────

def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _http_get(url: str, headers: dict[str, str] | None = None, timeout: float = 60.0) -> bytes:
    req = urllib.request.Request(url, headers=headers or {}, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read()
    except urllib.error.HTTPError as e:
        detail = ""
        try:
            detail = e.read().decode("utf-8", errors="replace")[:200]
        except Exception:
            pass
        raise RuntimeError(f"HTTP {e.code} GET {url}: {detail}") from e


def _http_post_form(url: str, data: dict, timeout: float = 30.0) -> dict:
    body = urllib.parse.urlencode(data).encode("utf-8")
    req = urllib.request.Request(url, data=body,
                                  headers={"Content-Type": "application/x-www-form-urlencoded"},
                                  method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        detail = ""
        try:
            detail = e.read().decode("utf-8", errors="replace")[:200]
        except Exception:
            pass
        raise RuntimeError(f"HTTP {e.code} POST {url}: {detail}") from e


def _b2_put(bucket: str, key: str, data: bytes, content_type: str) -> str:
    """Upload bytes to B2 S3-compatible endpoint. Returns public URI."""
    import base64
    import hmac
    import hashlib as _hl

    if not _B2_KEY_ID or not _B2_KEY:
        raise RuntimeError("B2_ACCESS_KEY_ID / B2_SECRET_ACCESS_KEY not set")

    url = f"{_B2_ENDPOINT}/{bucket}/{key}"
    now = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    date = now[:8]

    # AWS Signature V4 (B2 is S3-compatible).
    service = "s3"
    region = "us-west-004"

    # Canonical request
    payload_hash = _hl.sha256(data).hexdigest()
    canonical_headers = (
        f"content-type:{content_type}\n"
        f"host:{_B2_ENDPOINT.replace('https://', '')}\n"
        f"x-amz-content-sha256:{payload_hash}\n"
        f"x-amz-date:{now}\n"
    )
    signed_headers = "content-type;host;x-amz-content-sha256;x-amz-date"
    canonical_req = (
        f"PUT\n/{bucket}/{key}\n\n{canonical_headers}\n{signed_headers}\n{payload_hash}"
    )

    # String to sign
    scope = f"{date}/{region}/{service}/aws4_request"
    string_to_sign = f"AWS4-HMAC-SHA256\n{now}\n{scope}\n{_hl.sha256(canonical_req.encode()).hexdigest()}"

    # Signing key
    def _sign(key: bytes, msg: str) -> bytes:
        return hmac.new(key, msg.encode("utf-8"), _hl.sha256).digest()

    signing_key = _sign(
        _sign(_sign(_sign(f"AWS4{_B2_KEY}".encode(), date), region), service),
        "aws4_request",
    )
    signature = hmac.new(signing_key, string_to_sign.encode("utf-8"), _hl.sha256).hexdigest()

    auth = (
        f"AWS4-HMAC-SHA256 Credential={_B2_KEY_ID}/{scope},"
        f"SignedHeaders={signed_headers},Signature={signature}"
    )

    req = urllib.request.Request(
        url,
        data=data,
        headers={
            "Authorization": auth,
            "Content-Type": content_type,
            "x-amz-content-sha256": payload_hash,
            "x-amz-date": now,
        },
        method="PUT",
    )
    with urllib.request.urlopen(req, timeout=120.0) as resp:
        if resp.status not in (200, 204):
            raise RuntimeError(f"B2 PUT failed: {resp.status}")
    return f"b2://{bucket}/{key}"


# ──────────────────────────────────────────────────────────────────────
# EPO OPS OAuth2 token cache
# ──────────────────────────────────────────────────────────────────────

_epo_token: str = ""
_epo_token_expires: float = 0.0


def _epo_get_token() -> str:
    global _epo_token, _epo_token_expires
    if _epo_token and time.time() < _epo_token_expires - 60:
        return _epo_token
    if not _EPO_OPS_KEY or not _EPO_OPS_SECRET:
        raise RuntimeError("EPO_OPS_CLIENT_KEY / EPO_OPS_CLIENT_SECRET not set")
    import base64
    creds = base64.b64encode(f"{_EPO_OPS_KEY}:{_EPO_OPS_SECRET}".encode()).decode()
    body = urllib.parse.urlencode({"grant_type": "client_credentials"}).encode()
    req = urllib.request.Request(
        _EPO_OPS_AUTH_URL,
        data=body,
        headers={"Authorization": f"Basic {creds}",
                 "Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30.0) as resp:
        data = json.loads(resp.read())
    _epo_token = str(data["access_token"])
    _epo_token_expires = time.time() + int(data.get("expires_in", 3600))
    return _epo_token


# ──────────────────────────────────────────────────────────────────────
# Task 1 (reverse topo leaf): patent.epoOps.fillCitations
# ──────────────────────────────────────────────────────────────────────

async def task_patent_epo_ops_fill_citations(
    rows: list | None = None,
    rateLimitPerMin: int = 100,
    citationEdgeTable: str = "edge_open_patent_citation_pair",
    familyEdgeTable: str = "edge_family_member",
) -> dict:
    """Fetch EPO OPS biblio + citations for a batch of US patents.

    Returns citationEdges, familyEdges, quotaUsedBytes.
    """
    rows = rows or []
    if not rows:
        return {"ok": True, "citationEdges": 0, "familyEdges": 0, "quotaUsedBytes": 0}

    try:
        token = _epo_get_token()
    except RuntimeError as e:
        return {"ok": False, "citationEdges": 0, "familyEdges": 0,
                "quotaUsedBytes": 0, "error": str(e)}

    citation_edges = 0
    family_edges = 0
    quota_bytes = 0
    interval_sec = 60.0 / max(1, rateLimitPerMin)

    for row in rows:
        patent_number = str(row.get("patent_number") or "")
        vertex_id = str(row.get("vertex_id") or "")
        if not patent_number:
            continue

        # EPO OPS publication reference: "US.{number}.A"
        pub_ref = f"US.{patent_number}.A"
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
        }

        # Fetch citations.
        cit_url = f"{_EPO_OPS_BASE}/published-data/publication/docdb/{pub_ref}/citations"
        try:
            raw = _http_get(cit_url, headers=headers, timeout=30.0)
            quota_bytes += len(raw)
            cit_data = json.loads(raw)
        except RuntimeError:
            time.sleep(interval_sec)
            continue
        except json.JSONDecodeError:
            time.sleep(interval_sec)
            continue

        # Parse citations.
        ops_cits = (
            cit_data
            .get("ops:world-patent-data", {})
            .get("exchange-documents", {})
            .get("exchange-document", {})
            .get("citations", {})
            .get("citation", [])
        )
        if isinstance(ops_cits, dict):
            ops_cits = [ops_cits]

        cit_rows = []
        for cit in ops_cits:
            cited_doc = cit.get("patcit", {}).get("document-id", {})
            cited_num = str(cited_doc.get("doc-number", {}).get("$", "") or "")
            cited_cc = str(cited_doc.get("country", {}).get("$", "US") or "US")
            if not cited_num:
                continue
            cited_vertex_id = f"at://{_PATENT_ACTOR}/com.etzhayyim.apps.patent.patent/{cited_cc}-{cited_num}"
            edge_id = f"edge-epo-cit-{patent_number}-{cited_num}-{uuid.uuid4().hex[:6]}"
            cit_rows.append((
                edge_id, vertex_id, cited_vertex_id,
                "epo_ops", _now_iso(),
            ))

        if cit_rows:
            kotoba_cit_rows = []
            for item in cit_rows:
                kotoba_cit_rows.append({
                    "vertex_id": item[0],
                    "citing_patent_id": item[1],
                    "cited_patent_id": item[2],
                    "source": item[3],
                    "created_at": item[4],
                })
            get_kotoba_client().insert_rows(citationEdgeTable, kotoba_cit_rows)
            citation_edges += len(cit_rows)

        # Fetch family members.
        fam_url = f"{_EPO_OPS_BASE}/family/publication/docdb/{pub_ref}"
        try:
            raw_fam = _http_get(fam_url, headers=headers, timeout=30.0)
            quota_bytes += len(raw_fam)
            fam_data = json.loads(raw_fam)
        except (RuntimeError, json.JSONDecodeError):
            time.sleep(interval_sec)
            continue

        members = (
            fam_data.get("ops:world-patent-data", {})
            .get("ops:patent-family", {})
            .get("ops:family-member", [])
        )
        if isinstance(members, dict):
            members = [members]

        fam_rows = []
        for member in members:
            pub_ref_obj = member.get("publication-reference", {}).get("document-id", {})
            if isinstance(pub_ref_obj, list):
                pub_ref_obj = pub_ref_obj[0] if pub_ref_obj else {}
            member_num = str(pub_ref_obj.get("doc-number", {}).get("$", "") or "")
            member_cc = str(pub_ref_obj.get("country", {}).get("$", "") or "")
            if not member_num or not member_cc:
                continue
            member_vid = f"at://{_PATENT_ACTOR}/com.etzhayyim.apps.patent.patent/{member_cc}-{member_num}"
            edge_id = f"edge-fam-{patent_number}-{member_cc}-{member_num}-{uuid.uuid4().hex[:6]}"
            fam_rows.append((edge_id, vertex_id, member_vid, _now_iso()))

        if fam_rows:
            kotoba_fam_rows = []
            for item in fam_rows:
                kotoba_fam_rows.append({
                    "vertex_id": item[0],
                    "patent_id": item[1],
                    "family_member_id": item[2],
                    "created_at": item[3],
                })
            get_kotoba_client().insert_rows(familyEdgeTable, kotoba_fam_rows)
            family_edges += len(fam_rows)

        time.sleep(interval_sec)

    return {
        "ok": True,
        "citationEdges": citation_edges,
        "familyEdges": family_edges,
        "quotaUsedBytes": quota_bytes,
    }


# ──────────────────────────────────────────────────────────────────────
# Task 2 (reverse topo): patent.usptoPatentsview.ingestCitation
# ──────────────────────────────────────────────────────────────────────

async def task_patent_uspto_ingest_citation(
    tsvUrl: str = "",
    batchSize: int = 2000,
    vertexTable: str = "vertex_open_patent_citation",
    edgeTable: str = "edge_open_patent_citation_pair",
) -> dict:
    """Stream-download PatentsView g_us_patent_citation.tsv and bulk-insert.

    TSV columns: uuid, patent_id, citation_patent_id, citation_category,
                 citation_sequence, citation_date
    Returns rows (citation edge count).
    """
    if not tsvUrl:
        return {"ok": False, "rows": 0, "error": "tsvUrl required"}

    rows_inserted = 0
    batch: list[tuple[Any, ...]] = []

    try:
        raw_bytes = _http_get(tsvUrl, timeout=600.0)
    except RuntimeError as e:
        return {"ok": False, "rows": 0, "error": str(e)}

    # Handle gzip or plain TSV.
    if tsvUrl.endswith(".gz") or raw_bytes[:2] == b"\x1f\x8b":
        raw_bytes = gzip.decompress(raw_bytes)

    reader = csv.DictReader(
        io.TextIOWrapper(io.BytesIO(raw_bytes), encoding="utf-8", errors="replace"),
        delimiter="\t",
    )

    for tsv_row in reader:
        pat_id = str(tsv_row.get("patent_id") or "").strip()
        cit_id = str(tsv_row.get("citation_patent_id") or "").strip()
        category = str(tsv_row.get("citation_category") or "").strip()
        seq = tsv_row.get("citation_sequence") or "0"
        cit_date = str(tsv_row.get("citation_date") or "").strip()

        if not pat_id or not cit_id:
            continue

        citing_vid = f"at://{_PATENT_ACTOR}/com.etzhayyim.apps.patent.patent/US-{pat_id}"
        cited_vid = f"at://{_PATENT_ACTOR}/com.etzhayyim.apps.patent.patent/US-{cit_id}"
        edge_id = f"edge-uspto-cit-{pat_id}-{cit_id}"

        batch.append((
            edge_id, citing_vid, cited_vid,
            category, int(seq) if seq.isdigit() else 0,
            cit_date or None, "uspto_patentsview", _now_iso(),
        ))

        if len(batch) >= batchSize:
            kotoba_batch = []
            for item in batch:
                kotoba_batch.append({
                    "vertex_id": item[0],
                    "citing_patent_id": item[1],
                    "cited_patent_id": item[2],
                    "citation_category": item[3],
                    "citation_sequence": item[4],
                    "citation_date": item[5],
                    "source": item[6],
                    "created_at": item[7],
                })
            get_kotoba_client().insert_rows(edgeTable, kotoba_batch)
            rows_inserted += len(batch)
            batch = []

    if batch:
            kotoba_batch = []
            for item in batch:
                kotoba_batch.append({
                    "vertex_id": item[0],
                    "citing_patent_id": item[1],
                    "cited_patent_id": item[2],
                    "citation_category": item[3],
                    "citation_sequence": item[4],
                    "citation_date": item[5],
                    "source": item[6],
                    "created_at": item[7],
                })
            get_kotoba_client().insert_rows(edgeTable, kotoba_batch)
        rows_inserted += len(batch)

    return {"ok": True, "rows": rows_inserted}


# ──────────────────────────────────────────────────────────────────────
# Task 3 (reverse topo): patent.usptoPatentsview.ingestPatent
# ──────────────────────────────────────────────────────────────────────

async def task_patent_uspto_ingest_patent(
    tsvUrl: str = "",
    batchSize: int = 2000,
    table: str = "vertex_open_patent_patent",
    blobThresholdDate: str = "2010-01-01",
    blobTable: str = "vertex_patent_blob",
) -> dict:
    """Stream-download PatentsView g_patent.tsv and bulk-insert.

    TSV columns: patent_id, patent_type, patent_date, patent_title,
                 patent_abstract, num_claims, filename, withdrawn, patent_number
    Returns rows (patent count), blobQueued (blob convert queue count).
    """
    if not tsvUrl:
        return {"ok": False, "rows": 0, "blobQueued": 0, "error": "tsvUrl required"}

    try:
        raw_bytes = _http_get(tsvUrl, timeout=600.0)
    except RuntimeError as e:
        return {"ok": False, "rows": 0, "blobQueued": 0, "error": str(e)}

    if tsvUrl.endswith(".gz") or raw_bytes[:2] == b"\x1f\x8b":
        raw_bytes = gzip.decompress(raw_bytes)

    reader = csv.DictReader(
        io.TextIOWrapper(io.BytesIO(raw_bytes), encoding="utf-8", errors="replace"),
        delimiter="\t",
    )

    rows_inserted = 0
    blob_queued = 0
    batch: list[tuple[Any, ...]] = []
    blob_batch: list[tuple[Any, ...]] = []

    for tsv_row in reader:
        pat_number = str(tsv_row.get("patent_number") or "").strip()
        pat_id = str(tsv_row.get("patent_id") or "").strip()
        pat_type = str(tsv_row.get("patent_type") or "utility").strip()
        pat_date = str(tsv_row.get("patent_date") or "").strip()
        title = str(tsv_row.get("patent_title") or "").strip()[:1000]
        abstract = str(tsv_row.get("patent_abstract") or "").strip()[:4000]
        num_claims = tsv_row.get("num_claims") or "0"
        withdrawn = str(tsv_row.get("withdrawn") or "0").strip()
        filename = str(tsv_row.get("filename") or "").strip()

        if not pat_number:
            continue

        vertex_id = f"at://{_PATENT_ACTOR}/com.etzhayyim.apps.patent.patent/US-{pat_number}"

        batch.append((
            vertex_id, pat_number, "US", pat_type,
            pat_date or None, title, abstract,
            int(num_claims) if str(num_claims).isdigit() else 0,
            withdrawn != "0", filename,
            _PATENT_ACTOR, _PATENT_ACTOR, 1, _now_iso(),
        ))

        # Queue blob convert for patents on or after threshold date.
        if pat_date and pat_date >= blobThresholdDate and filename:
            pdf_url = f"https://bulkdata.uspto.gov/data/patent/grant/redbook/fulltext/{pat_date[:4]}/{filename}"
            blob_vid = f"at://{_PATENT_ACTOR}/com.etzhayyim.apps.patent.blob/US-{pat_number}"
            blob_batch.append((
                blob_vid, pat_number, "US", pdf_url, "pending",
                _PATENT_ACTOR, _PATENT_ACTOR, 1, _now_iso(),
            ))
            blob_queued += 1

        if len(batch) >= batchSize:
            kotoba_batch = []
            for item in batch:
                kotoba_batch.append({
                    "vertex_id": item[0],
                    "patent_number": item[1],
                    "jurisdiction": item[2],
                    "patent_type": item[3],
                    "patent_date": item[4],
                    "title": item[5],
                    "abstract": item[6],
                    "num_claims": item[7],
                    "withdrawn": item[8],
                    "filename": item[9],
                    "actor_did": item[10],
                    "org_did": item[11],
                    "sensitivity_ord": item[12],
                    "created_at": item[13],
                })
            get_kotoba_client().insert_rows(table, kotoba_batch)
            rows_inserted += len(batch)
            batch = []

        if len(blob_batch) >= batchSize:
            kotoba_blob_batch = []
            for item in blob_batch:
                kotoba_blob_batch.append({
                    "vertex_id": item[0],
                    "patent_number": item[1],
                    "jurisdiction": item[2],
                    "pdf_source_url": item[3],
                    "status": item[4],
                    "actor_did": item[5],
                    "org_did": item[6],
                    "sensitivity_ord": item[7],
                    "created_at": item[8],
                })
            get_kotoba_client().insert_rows(blobTable, kotoba_blob_batch)
            blob_batch = []

    if batch:
        kotoba_batch = []
        for item in batch:
            kotoba_batch.append({
                "vertex_id": item[0],
                "patent_number": item[1],
                "jurisdiction": item[2],
                "patent_type": item[3],
                "patent_date": item[4],
                "title": item[5],
                "abstract": item[6],
                "num_claims": item[7],
                "withdrawn": item[8],
                "filename": item[9],
                "actor_did": item[10],
                "org_did": item[11],
                "sensitivity_ord": item[12],
                "created_at": item[13],
            })
        get_kotoba_client().insert_rows(table, kotoba_batch)
        rows_inserted += len(batch)

    if blob_batch:
        kotoba_blob_batch = []
        for item in blob_batch:
            kotoba_blob_batch.append({
                "vertex_id": item[0],
                "patent_number": item[1],
                "jurisdiction": item[2],
                "pdf_source_url": item[3],
                "status": item[4],
                "actor_did": item[5],
                "org_did": item[6],
                "sensitivity_ord": item[7],
                "created_at": item[8],
            })
        get_kotoba_client().insert_rows(blobTable, kotoba_blob_batch)

    return {"ok": True, "rows": rows_inserted, "blobQueued": blob_queued}


# ──────────────────────────────────────────────────────────────────────
# Task 4 (reverse topo root): patent.blob.convert
# ──────────────────────────────────────────────────────────────────────

def _sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _run_cmd(args: list[str], input_data: bytes | None = None, timeout: float = 120.0) -> bytes:
    import subprocess
    result = subprocess.run(
        args,
        input=input_data,
        capture_output=True,
        timeout=timeout,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"{args[0]} failed ({result.returncode}): {result.stderr.decode('utf-8', errors='replace')[:200]}"
        )
    return result.stdout


async def task_patent_blob_convert(
    rows: list | None = None,
    b2Bucket: str = "patent-blobs",
    b2Endpoint: str = "",
    b2PdfPrefix: str = "pdf/",
    b2WebpPrefix: str = "webp/",
    b2TextPrefix: str = "text/",
    webpQuality: int = 80,
) -> dict:
    """Convert PDF blobs to webp + OCR text and upload to B2.

    Requires on the pod: pdftotext (poppler-utils), cwebp (webp), pdftocairo (poppler).
    Each row: { vertex_id, patent_number, jurisdiction, pdf_source_url }
    Updates vertex_patent_blob status to 'ocr_done'.
    """
    rows = rows or []
    if not rows:
        return {"ok": True, "converted": 0, "dedupHit": 0, "failed": 0,
                "bytesPdf": 0, "bytesWebp": 0}

    converted = 0
    dedup_hit = 0
    failed = 0
    bytes_pdf = 0
    bytes_webp = 0

    endpoint = b2Endpoint or _B2_ENDPOINT

    for row in rows:
        vertex_id = str(row.get("vertex_id") or "")
        pdf_url = str(row.get("pdf_source_url") or "")
        if not pdf_url:
            failed += 1
            continue

        # Download PDF.
        try:
            pdf_bytes = _http_get(pdf_url, timeout=120.0)
        except RuntimeError:
            failed += 1
            get_kotoba_client().insert_row(
                "vertex_patent_blob",
                {
                    "vertex_id": vertex_id,
                    "status": "download_failed",
                    "created_at": _now_iso(),
                },
            )
            continue

        pdf_sha = _sha256_hex(pdf_bytes)
        bytes_pdf += len(pdf_bytes)

        # Check dedup: if this sha is already in B2, skip re-upload.
        pdf_key = f"{b2PdfPrefix}{pdf_sha}.pdf"
        try:
            _http_get(f"{endpoint}/{b2Bucket}/{pdf_key}", timeout=10.0)
            dedup_hit += 1
            pdf_uri = f"b2://{b2Bucket}/{pdf_key}"
        except RuntimeError:
            # Not cached — upload.
            try:
                pdf_uri = _b2_put(b2Bucket, pdf_key, pdf_bytes, "application/pdf")
            except RuntimeError:
                failed += 1
                continue

        # Convert first page to WebP via pdftocairo → cwebp (in memory via temp files).
        import tempfile
        webp_uri = ""
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                pdf_path = os.path.join(tmpdir, "input.pdf")
                png_path = os.path.join(tmpdir, "page")
                webp_path = os.path.join(tmpdir, "page.webp")

                with open(pdf_path, "wb") as fh:
                    fh.write(pdf_bytes)

                # pdftocairo: first page only (-l 1) → PNG.
                _run_cmd(["pdftocairo", "-png", "-r", "150", "-l", "1", pdf_path, png_path])

                # cwebp: convert first PNG output (page-1.png).
                png_actual = os.path.join(tmpdir, "page-1.png")
                _run_cmd(["cwebp", "-q", str(webpQuality), png_actual, "-o", webp_path])

                with open(webp_path, "rb") as fh:
                    webp_bytes = fh.read()

            webp_key = f"{b2WebpPrefix}{pdf_sha}.webp"
            webp_uri = _b2_put(b2Bucket, webp_key, webp_bytes, "image/webp")
            bytes_webp += len(webp_bytes)

        except (RuntimeError, FileNotFoundError):
            pass  # webp conversion optional; continue with text extraction

        # Extract text via pdftotext.
        ocr_uri = ""
        ocr_text: str | None = None
        try:
            text_bytes = _run_cmd(["pdftotext", "-", "-"], input_data=pdf_bytes)
            ocr_text = text_bytes.decode("utf-8", errors="replace")
            text_sha = _sha256_hex(text_bytes)
            text_key = f"{b2TextPrefix}{text_sha}.txt"
            ocr_uri = _b2_put(b2Bucket, text_key, text_bytes, "text/plain")
        except (RuntimeError, FileNotFoundError):
            pass

        # Update vertex_patent_blob — store ocr_text directly in RW
        # so v_training_text can UNION ALL without B2 fetches.
        get_kotoba_client().insert_row(
            "vertex_patent_blob",
            {
                "vertex_id": vertex_id,
                "pdf_sha256": pdf_sha,
                "webp_cid": webp_uri,
                "ocr_text_cid": ocr_uri,
                "ocr_text": ocr_text,
                "status": "ocr_done",
                "updated_at": _now_iso(),
            },
        )
        converted += 1

    return {
        "ok": True,
        "converted": converted,
        "dedupHit": dedup_hit,
        "failed": failed,
        "bytesPdf": bytes_pdf,
        "bytesWebp": bytes_webp,
    }


# ──────────────────────────────────────────────────────────────────────
# Registration
# ──────────────────────────────────────────────────────────────────────

def register(worker: Any, *, timeout_ms: int = 300_000) -> None:
    """Wire all patent task types onto the shared LangServer worker."""

    def t(name: str, fn: Any, *, ms: int | None = None) -> None:
        worker.task(task_type=name, single_value=False, timeout_ms=ms or timeout_ms)(fn)

    # Reverse topological order (sinks first).
    t("patent.epoOps.fillCitations",            task_patent_epo_ops_fill_citations,   ms=3_600_000)
    t("patent.usptoPatentsview.ingestCitation",  task_patent_uspto_ingest_citation,    ms=3_600_000)
    t("patent.usptoPatentsview.ingestPatent",    task_patent_uspto_ingest_patent,      ms=3_600_000)
    t("patent.blob.convert",                     task_patent_blob_convert,             ms=3_600_000)


__all__ = [
    "register",
    "task_patent_epo_ops_fill_citations",
    "task_patent_uspto_ingest_citation",
    "task_patent_uspto_ingest_patent",
    "task_patent_blob_convert",
]
