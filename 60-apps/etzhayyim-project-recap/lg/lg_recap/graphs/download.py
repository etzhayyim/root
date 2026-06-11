"""recap `download` graph -- validate, download, upload, and record media.

NSID: com.etzhayyim.apps.recap.download
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph
from langgraph.types import RetryPolicy

from .get_info import _detect_platform

_log = logging.getLogger(__name__)

_COOKIES_FILE_SRC = os.environ.get("YTDLP_COOKIES_FILE", "")
if _COOKIES_FILE_SRC:
    import shutil as _shutil
    _COOKIES_FILE = f"/tmp/yt-cookies-{os.getpid()}.txt"
    _shutil.copy2(_COOKIES_FILE_SRC, _COOKIES_FILE)
else:
    _COOKIES_FILE = ""
_RW_URL = os.environ.get("RW_URL") or os.environ.get("LG_CHECKPOINTER_URL", "")
_REPO = os.environ.get("RECAP_REPO_DID", "did:web:recap.etzhayyim.com")
_OWNER = os.environ.get("RECAP_OWNER_DID", "did:web:recap.etzhayyim.com")
_DEFAULT_ORG_DID = os.environ.get("RECAP_ORG_DID", "anon")
_B2_BUCKET = os.environ.get("RECAP_B2_BUCKET", "etzhayyim-cache")
_ALLOWED_SCOPES = {"research", "authorized"}


class _DownloadState(TypedDict, total=False):
    url: str
    scope: str
    format_id: str | None
    actor_did: str | None
    org_did: str | None
    platform: str | None
    title: str | None
    uploader: str | None
    duration_sec: int | None
    thumbnail_url: str | None
    upload_date: str | None
    blob_key: str | None
    blob_size_bytes: int | None
    download_uri: str | None
    license: str | None
    status: str
    error: str | None


async def _node_validate(state: _DownloadState) -> dict[str, Any]:
    url = (state.get("url") or "").strip()
    if not url:
        return {"status": "error", "error": "url is required"}
    scope = (state.get("scope") or "research").strip()
    if scope not in _ALLOWED_SCOPES:
        return {"status": "error", "error": "scope must be research or authorized"}
    platform = _detect_platform(url)
    if platform == "unknown":
        return {"status": "error", "error": f"unsupported platform for url: {url[:100]}"}
    return {"platform": platform, "scope": scope, "status": "downloading"}


async def _node_download_upload(state: _DownloadState) -> dict[str, Any]:
    if state.get("error"):
        return {}
    url = state["url"]
    fmt = state.get("format_id") or "bestvideo+bestaudio/best"
    try:
        with tempfile.TemporaryDirectory(prefix="recap-") as td:
            out_tmpl = str(Path(td) / "%(id)s.%(ext)s")
            _cookies = ["--cookies", _COOKIES_FILE] if _COOKIES_FILE else []
            meta_proc = subprocess.run(
                ["yt-dlp", "--dump-json", "--no-playlist", *_cookies, "--remote-components", "ejs:github", url],
                capture_output=True,
                text=True,
                timeout=45,
            )
            if meta_proc.returncode != 0:
                return {"status": "error", "error": f"yt-dlp metadata: {meta_proc.stderr[:200]}"}
            info = json.loads(meta_proc.stdout)

            dl_proc = subprocess.run(
                ["yt-dlp", "-f", fmt, "--no-playlist", *_cookies, "--remote-components", "ejs:github", "-o", out_tmpl, url],
                capture_output=True,
                text=True,
                timeout=900,
            )
            if dl_proc.returncode != 0:
                return {"status": "error", "error": f"yt-dlp download: {dl_proc.stderr[:300]}"}
            files = [p for p in Path(td).iterdir() if p.is_file()]
            if not files:
                return {"status": "error", "error": "yt-dlp produced no file"}
            media = max(files, key=lambda p: p.stat().st_size)
            data = media.read_bytes()
            digest = hashlib.sha256(data).hexdigest()
            ext = media.suffix.lstrip(".") or "bin"
            blob_key = f"recap/{digest}.{ext}"

            uploaded = False
            key_id = os.environ.get("B2_KEY_ID") or os.environ.get("AWS_ACCESS_KEY_ID")
            app_key = os.environ.get("B2_APPLICATION_KEY") or os.environ.get("AWS_SECRET_ACCESS_KEY")
            if key_id and app_key:
                import boto3

                s3 = boto3.client(
                    "s3",
                    aws_access_key_id=key_id,
                    aws_secret_access_key=app_key,
                    endpoint_url=os.environ.get("B2_ENDPOINT_URL") or os.environ.get("AWS_ENDPOINT_URL"),
                )
                bucket = os.environ.get("B2_BUCKET_MEDIA") or _B2_BUCKET
                s3.put_object(Bucket=bucket, Key=blob_key, Body=data)
                uploaded = True

        return {
            "title": info.get("title"),
            "uploader": info.get("uploader") or info.get("channel"),
            "duration_sec": info.get("duration"),
            "thumbnail_url": info.get("thumbnail"),
            "upload_date": info.get("upload_date"),
            "license": info.get("license"),
            "format_id": fmt,
            "blob_key": blob_key,
            "blob_size_bytes": len(data),
            "status": "done" if uploaded else "downloaded",
        }
    except subprocess.TimeoutExpired:
        return {"status": "error", "error": "yt-dlp timed out"}
    except Exception as exc:
        _log.exception("download failed")
        return {"status": "error", "error": str(exc)[:300]}


async def _node_write_record(state: _DownloadState) -> dict[str, Any]:
    if not _RW_URL or not state.get("blob_key"):
        return {}
    try:
        import secrets
        from datetime import datetime, timezone

        import psycopg

        rkey = f"dl-{secrets.token_hex(4)}"
        vertex_id = f"at://{_REPO}/com.etzhayyim.apps.recap.download/{rkey}"
        actor_did = state.get("actor_did") or _OWNER
        org_did = state.get("org_did") or _DEFAULT_ORG_DID
        conn = await psycopg.AsyncConnection.connect(_RW_URL, autocommit=True)
        try:
            await conn.execute(
                """
                INSERT INTO vertex_recap_download
                    (vertex_id, rkey, owner_did, actor_did, org_did, at_did,
                     source_url, platform, title, duration_sec, format_id,
                     blob_key, blob_size_bytes, thumbnail_url, uploader,
                     upload_date, license, status, error_msg, scope, created_at)
                VALUES
                    (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """,
                [
                    vertex_id, rkey, _OWNER, actor_did, org_did, actor_did,
                    state.get("url"), state.get("platform"), state.get("title"),
                    state.get("duration_sec"), state.get("format_id"),
                    state.get("blob_key"), state.get("blob_size_bytes"),
                    state.get("thumbnail_url"), state.get("uploader"),
                    state.get("upload_date"), state.get("license"),
                    state.get("status"), state.get("error"), state.get("scope"),
                    datetime.now(tz=timezone.utc).isoformat(),
                ],
            )
        finally:
            await conn.close()
        return {"download_uri": vertex_id}
    except Exception as exc:
        _log.exception("write recap record failed")
        return {"error": f"record: {exc!s}"[:300]}


def _build() -> StateGraph:
    g: StateGraph = StateGraph(_DownloadState)
    g.add_node("validate", _node_validate)
    g.add_node("download_upload", _node_download_upload,
               retry_policy=RetryPolicy(max_attempts=2, backoff_factor=2.0))
    g.add_node("write_record", _node_write_record,
               retry_policy=RetryPolicy(max_attempts=2, backoff_factor=2.0))
    g.add_edge(START, "validate")
    g.add_edge("validate", "download_upload")
    g.add_edge("download_upload", "write_record")
    g.add_edge("write_record", END)
    return g


GRAPH = _build().compile(name="download")
