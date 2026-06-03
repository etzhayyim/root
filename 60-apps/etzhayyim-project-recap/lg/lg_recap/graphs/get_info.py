"""recap `getInfo` graph — fetch media metadata without downloading.

NSID: com.etzhayyim.apps.recap.getInfo
"""
from __future__ import annotations

import logging
import os
import subprocess
import json as _json
from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph
from langgraph.types import RetryPolicy

_log = logging.getLogger(__name__)

_COOKIES_FILE_SRC = os.environ.get("YTDLP_COOKIES_FILE", "")
if _COOKIES_FILE_SRC:
    import shutil as _shutil
    _COOKIES_FILE = f"/tmp/yt-cookies-{os.getpid()}.txt"
    _shutil.copy2(_COOKIES_FILE_SRC, _COOKIES_FILE)
else:
    _COOKIES_FILE = ""

ALLOWED_PLATFORMS = {
    "youtube", "tiktok", "instagram", "twitter", "x", "niconico",
    "bilibili", "vimeo", "twitch", "facebook", "reddit",
}


class _GetInfoState(TypedDict, total=False):
    url: str
    # output
    platform: str | None
    title: str | None
    uploader: str | None
    duration: int | None
    thumbnail: str | None
    formats: list[dict[str, Any]] | None
    description: str | None
    upload_date: str | None
    license: str | None
    error: str | None


def _detect_platform(url: str) -> str:
    u = url.lower()
    if "youtube.com" in u or "youtu.be" in u:
        return "youtube"
    if "tiktok.com" in u:
        return "tiktok"
    if "instagram.com" in u:
        return "instagram"
    if "twitter.com" in u or "x.com" in u:
        return "x"
    if "nicovideo.jp" in u or "nico.ms" in u:
        return "niconico"
    if "bilibili.com" in u or "b23.tv" in u:
        return "bilibili"
    if "vimeo.com" in u:
        return "vimeo"
    if "twitch.tv" in u:
        return "twitch"
    if "facebook.com" in u or "fb.watch" in u:
        return "facebook"
    if "reddit.com" in u or "redd.it" in u:
        return "reddit"
    return "unknown"


async def _node_validate(state: _GetInfoState) -> dict[str, Any]:
    url = (state.get("url") or "").strip()
    if not url:
        return {"error": "url is required"}
    platform = _detect_platform(url)
    if platform == "unknown":
        return {"error": f"unsupported platform for url: {url[:100]}"}
    return {"platform": platform}


async def _node_get_metadata(state: _GetInfoState) -> dict[str, Any]:
    if state.get("error"):
        return {}
    url = state["url"]
    try:
        _cookies = ["--cookies", _COOKIES_FILE] if _COOKIES_FILE else []
        proc = subprocess.run(
            ["yt-dlp", "--dump-json", "--no-playlist", *_cookies, "--remote-components", "ejs:github", url],
            capture_output=True, text=True, timeout=30,
        )
        if proc.returncode != 0:
            return {"error": f"yt-dlp: {proc.stderr[:200]}"}
        info = _json.loads(proc.stdout)
        formats = [
            {"format_id": f.get("format_id"), "ext": f.get("ext"),
             "note": f.get("format_note"), "height": f.get("height"),
             "filesize": f.get("filesize")}
            for f in info.get("formats", [])[-10:]
        ]
        return {
            "title": info.get("title"),
            "uploader": info.get("uploader") or info.get("channel"),
            "duration": info.get("duration"),
            "thumbnail": info.get("thumbnail"),
            "description": (info.get("description") or "")[:500],
            "upload_date": info.get("upload_date"),
            "license": info.get("license"),
            "formats": formats,
        }
    except subprocess.TimeoutExpired:
        return {"error": "yt-dlp timed out"}
    except Exception as exc:
        _log.exception("get_metadata failed")
        return {"error": str(exc)[:200]}


def _build() -> StateGraph:
    g: StateGraph = StateGraph(_GetInfoState)
    g.add_node("validate", _node_validate)
    g.add_node("get_metadata", _node_get_metadata,
               retry_policy=RetryPolicy(max_attempts=2, backoff_factor=1.5))
    g.add_edge(START, "validate")
    g.add_edge("validate", "get_metadata")
    g.add_edge("get_metadata", END)
    return g


GRAPH = _build().compile(name="get_info")
