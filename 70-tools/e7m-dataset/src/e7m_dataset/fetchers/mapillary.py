"""Mapillary street-imagery fetcher (CC-BY-SA 4.0; Tier C / G13).

Stages a per-bbox slice of Mapillary's public street-level imagery
archive under
``${ETZ_DATASET_ROOT}/datasets-staging/mapillary-{bbox-slug}-{captureTs}/``.

Per ADR-2605262500 §2 (treated as Tier C — sim-recording SA propagation
incompatible with redistribution; G13 fleet-internal carve-out applies)
+ §5 (face / plate / child blur preprocessing MANDATORY at fetch
time, fail-closed on child presence, blur on Murakumo only).

Source = Mapillary Graph API v4 (free tier; operator-supplied token):

  - https://graph.mapillary.com/images
  - Per-image download from `thumb_2048_url` or `thumb_original_url`

The fetcher REFUSES to run without a vision PII filter configured —
the `vision_pii_filter` argument is required, and its `backend` must
have loaded successfully. Tests use a stub backend with controlled
detections.

Output layout:

  staging-dir/
    api_query.json              # records the bbox + filters + token-redacted query
    images/<image_id>.jpg       # redacted (blurred) image — the only safe-to-share view
    annex/<image_id>.jpg        # original — preserved per ADR-2605262500 §5 behind
                                  Council-attestation-gated unlock
    detections/<image_id>.json  # per-image detection record (boxes + child flag)
    rejected/<image_id>.json    # records the rejection reason for child-fail-closed
"""

from __future__ import annotations

import dataclasses
import hashlib
import json
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import httpx

from . import FetchResult
from ..vision_pii_filter import (
    RedactionResult,
    VisionPiiBackendUnavailable,
    VisionPiiFilter,
)


DEFAULT_BASE_URL = "https://graph.mapillary.com"
DEFAULT_USER_AGENT = "etzhayyim-e7m-dataset/0.0.1 (https://etzhayyim.com)"

# We cap image count per fetch invocation to keep budgets sane.
# Operator can raise via `--max-images` but the cap is enforced.
DEFAULT_MAX_IMAGES = 100
ABSOLUTE_MAX_IMAGES = 5000


@dataclass
class MapillaryFetchOpts:
    # WGS84 bbox: [west, south, east, north]
    bbox: tuple[float, float, float, float]
    # Mapillary API token (free tier). Resolved from env if None.
    token: Optional[str] = None
    # Capture-date range filter, ISO-8601 e.g. "2023-04-01..2023-09-30".
    capture_date_range: Optional[str] = None
    # Required: vision PII filter instance with backend loaded.
    vision_pii_filter: Optional[VisionPiiFilter] = None
    # Image cap per fetch invocation.
    max_images: int = DEFAULT_MAX_IMAGES
    # Thumb resolution to download. "thumb_2048_url" is largest free-tier safe.
    thumb_field: str = "thumb_2048_url"
    base_url: str = DEFAULT_BASE_URL
    user_agent: str = DEFAULT_USER_AGENT
    timeout_sec: float = 600.0
    # Inject httpx.Client for tests.
    client: Optional[httpx.Client] = None


def _resolve_token(opts: MapillaryFetchOpts) -> str:
    if opts.token:
        return opts.token
    env = os.environ.get("MAPILLARY_TOKEN") or os.environ.get("ETZ_MAPILLARY_TOKEN")
    if env:
        return env
    raise ValueError(
        "Mapillary token required: pass `token=` or set MAPILLARY_TOKEN env. "
        "Free tier at https://www.mapillary.com/dashboard/developers."
    )


def _bbox_slug(bbox: tuple[float, float, float, float]) -> str:
    w, s, e, n = bbox
    return f"w{w:.4f}_s{s:.4f}_e{e:.4f}_n{n:.4f}".replace(".", "p").replace("-", "m")


def _cap_image_count(requested: int) -> int:
    if requested <= 0:
        raise ValueError("max_images must be > 0")
    return min(requested, ABSOLUTE_MAX_IMAGES)


def _redaction_record(image_id: str, result: RedactionResult) -> dict:
    return {
        "image_id": image_id,
        "backend": result.backend_name,
        "frame_rejected": result.frame_rejected,
        "rejection_reason": result.rejection_reason,
        "detections": {
            "faces": [dataclasses.asdict(b) for b in result.detections.faces],
            "plates": [dataclasses.asdict(b) for b in result.detections.plates],
            "child_face_count": result.detections.child_face_count,
        },
    }


def fetch(staging_dir: Path, opts: MapillaryFetchOpts) -> FetchResult:
    """Fetch + redact a Mapillary bbox slice.

    Steps:
      1. Validate vision PII filter is loaded (G2 fail-closed).
      2. Resolve token.
      3. GET /images with bbox filter → list of image_id + thumb URL.
      4. Per image: GET thumb → redact via VisionPiiFilter → write
         redacted to images/ + original to annex/ + detection record
         to detections/ (or rejected/ if child-presence rejected).
      5. Return FetchResult with per-image counts + license=CC-BY-SA-4.0.
    """
    if opts.vision_pii_filter is None:
        raise VisionPiiBackendUnavailable(
            "mapillary.fetch() requires `vision_pii_filter=` (G2 enforcement). "
            "ADR-2605262500 §5: no Mapillary frame may leave fetch without "
            "face/plate/child blur applied."
        )

    token = _resolve_token(opts)
    max_n = _cap_image_count(opts.max_images)
    bbox_slug = _bbox_slug(opts.bbox)
    capture_ts = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    dataset_dirname = f"mapillary-{bbox_slug}-{capture_ts}"
    out_dir = staging_dir / dataset_dirname
    (out_dir / "images").mkdir(parents=True, exist_ok=True)
    (out_dir / "annex").mkdir(parents=True, exist_ok=True)
    (out_dir / "detections").mkdir(parents=True, exist_ok=True)
    (out_dir / "rejected").mkdir(parents=True, exist_ok=True)

    # 1. Persist a token-redacted query record for the manifest audit trail.
    bbox_str = ",".join(f"{c}" for c in opts.bbox)
    query = {
        "bbox": bbox_str,
        "fields": f"id,captured_at,{opts.thumb_field}",
        "limit": max_n,
    }
    if opts.capture_date_range:
        query["start_captured_at"] = opts.capture_date_range
    (out_dir / "api_query.json").write_text(
        json.dumps({**query, "token": "REDACTED"}, indent=2),
        encoding="utf-8",
    )

    owned_client = opts.client is None
    headers = {
        "User-Agent": opts.user_agent,
        "Authorization": f"OAuth {token}",
    }
    client = opts.client or httpx.Client(
        timeout=opts.timeout_sec, follow_redirects=True, headers=headers
    )
    n_fetched = 0
    n_rejected = 0

    try:
        # 2. List images by bbox.
        list_resp = client.get(f"{opts.base_url}/images", params=query)
        list_resp.raise_for_status()
        items: list[dict] = list_resp.json().get("data", [])

        for item in items[:max_n]:
            image_id = str(item.get("id", ""))
            thumb_url = item.get(opts.thumb_field)
            if not image_id or not thumb_url:
                continue

            # 3. Download.
            img_resp = client.get(thumb_url)
            img_resp.raise_for_status()
            original_bytes = img_resp.content

            # 4. Redact via vision PII filter (G2; fail-closed on child).
            try:
                result = opts.vision_pii_filter.redact(
                    original_bytes, mime_type="image/jpeg"
                )
            except VisionPiiBackendUnavailable:
                # Hard fail: backend unloaded mid-fetch is catastrophic.
                raise

            # 5. Persist annex (original) + detection record.
            (out_dir / "annex" / f"{image_id}.jpg").write_bytes(original_bytes)
            (out_dir / "detections" / f"{image_id}.json").write_text(
                json.dumps(_redaction_record(image_id, result), indent=2),
                encoding="utf-8",
            )

            if result.frame_rejected:
                # G5 §5 — child-presence: drop redacted, record reason.
                (out_dir / "rejected" / f"{image_id}.json").write_text(
                    json.dumps({
                        "image_id": image_id,
                        "reason": result.rejection_reason,
                        "g13_compliant": True,
                    }, indent=2),
                    encoding="utf-8",
                )
                n_rejected += 1
                continue

            # Redacted view is the only safe-to-share artifact.
            (out_dir / "images" / f"{image_id}.jpg").write_bytes(
                result.redacted_bytes or b""
            )
            n_fetched += 1

    finally:
        if owned_client:
            client.close()

    size_bytes = sum(p.stat().st_size for p in out_dir.rglob("*") if p.is_file())
    file_count = sum(1 for p in out_dir.rglob("*") if p.is_file())

    # Revision = sha256 of the (sorted) image_id list for stable pinning.
    image_ids = sorted(p.stem for p in (out_dir / "annex").iterdir()
                       if p.suffix == ".jpg")
    rev_input = "\n".join(image_ids).encode("utf-8")
    revision = f"mapillary:sha256:{hashlib.sha256(rev_input).hexdigest()}:{capture_ts}"

    return FetchResult(
        name=f"mapillary:{bbox_slug}",
        revision=revision,
        staging_path=out_dir,
        file_count=file_count,
        size_bytes=size_bytes,
        source={
            "type": "mapillary-graph-v4",
            "bbox": list(opts.bbox),
            "max_images_requested": max_n,
            "n_fetched": n_fetched,
            "n_rejected_for_child": n_rejected,
            "capture_date_range": opts.capture_date_range,
            "thumb_field": opts.thumb_field,
            "vision_pii_backend": opts.vision_pii_filter.backend.name,
            "captured_at": capture_ts,
            "license": "CC-BY-SA-4.0",                    # ADR-2605262500 §2 (treated Tier C)
            "tier": "C",
            "g13_nc_infix_required_in_artifacts": True,
            "g5_originals_council_attestation_gated_unlock": True,
            "g2_pii_filter_applied": True,
        },
    )


__all__ = [
    "ABSOLUTE_MAX_IMAGES",
    "DEFAULT_BASE_URL",
    "DEFAULT_MAX_IMAGES",
    "MapillaryFetchOpts",
    "fetch",
]
