"""recap `summarize` graph — extract transcript and generate LLM summary.

NSID: com.etzhayyim.apps.recap.summarize

Flow:
  validate → extract_transcript → summarize_llm → write_record → END
"""
from __future__ import annotations

import json
import logging
import os
import re
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Any, TypedDict

import httpx
from langgraph.graph import END, START, StateGraph
from langgraph.types import RetryPolicy

from .get_info import _detect_platform

_log = logging.getLogger(__name__)

_VLLM_URL = os.environ.get("VLLM_URL", "https://vyp99t9px7h4dl-4000.proxy.runpod.net/v1").rstrip("/")
_VLLM_MODEL = os.environ.get("VLLM_MODEL", "tier0-general")
_VLLM_TIMEOUT = float(os.environ.get("VLLM_TIMEOUT_SEC", "120"))
_RW_URL = os.environ.get("RW_URL") or os.environ.get("LG_CHECKPOINTER_URL", "")
_REPO = os.environ.get("RECAP_REPO_DID", "did:web:recap.etzhayyim.com")
_OWNER = os.environ.get("RECAP_OWNER_DID", "did:web:recap.etzhayyim.com")
_DEFAULT_ORG_DID = os.environ.get("RECAP_ORG_DID", "anon")
_COOKIES_FILE_SRC = os.environ.get("YTDLP_COOKIES_FILE", "")
if _COOKIES_FILE_SRC:
    import shutil as _shutil
    _COOKIES_FILE = f"/tmp/yt-cookies-{os.getpid()}.txt"
    _shutil.copy2(_COOKIES_FILE_SRC, _COOKIES_FILE)
else:
    _COOKIES_FILE = ""

_TRANSCRIPT_CHUNK_CHARS = 6000
_SUMMARY_MAX_TOKENS = 800


class _SummarizeState(TypedDict, total=False):
    url: str
    lang: str
    actor_did: str | None
    org_did: str | None
    # metadata
    platform: str | None
    title: str | None
    uploader: str | None
    duration_sec: int | None
    license: str | None
    upload_date: str | None
    # transcript
    transcript: str | None
    transcript_lang: str | None
    # output
    summary: str | None
    summary_uri: str | None
    error: str | None


def _vtt_to_text(vtt_content: str) -> str:
    lines = vtt_content.splitlines()
    texts: list[str] = []
    for line in lines:
        line = line.strip()
        if not line or line.startswith("WEBVTT") or re.match(r"^\d{2}:\d{2}", line) or "-->" in line:
            continue
        # Strip HTML tags
        clean = re.sub(r"<[^>]+>", "", line)
        clean = re.sub(r"&amp;", "&", clean)
        clean = re.sub(r"&lt;", "<", clean)
        clean = re.sub(r"&gt;", ">", clean)
        if clean:
            texts.append(clean)
    # Deduplicate adjacent identical lines (YouTube duplicates captions)
    deduped: list[str] = []
    for t in texts:
        if not deduped or deduped[-1] != t:
            deduped.append(t)
    return " ".join(deduped)


async def _node_validate(state: _SummarizeState) -> dict[str, Any]:
    url = (state.get("url") or "").strip()
    if not url:
        return {"error": "url is required"}
    platform = _detect_platform(url)
    if platform == "unknown":
        return {"error": f"unsupported platform for url: {url[:100]}"}
    lang = (state.get("lang") or "ja").strip()
    return {"platform": platform, "lang": lang}


async def _node_extract_transcript(state: _SummarizeState) -> dict[str, Any]:
    if state.get("error"):
        return {}
    url = state["url"]
    lang = state.get("lang", "ja")
    # Try requested lang first, then English fallback
    sub_langs = f"{lang},en" if lang != "en" else "en"
    try:
        with tempfile.TemporaryDirectory(prefix="recap-sub-") as td:
            _cookies = ["--cookies", _COOKIES_FILE] if _COOKIES_FILE else []
            # First: get metadata
            meta_proc = subprocess.run(
                ["yt-dlp", "--dump-json", "--no-playlist", *_cookies, "--remote-components", "ejs:github", url],
                capture_output=True, text=True, timeout=30,
            )
            meta: dict[str, Any] = {}
            if meta_proc.returncode == 0:
                meta = json.loads(meta_proc.stdout)

            # Second: download subtitles only
            sub_proc = subprocess.run(
                [
                    "yt-dlp",
                    "--write-auto-subs",
                    "--write-subs",
                    "--sub-langs", sub_langs,
                    "--sub-format", "vtt",
                    "--skip-download",
                    "--no-playlist",
                    *_cookies,
                    "--remote-components", "ejs:github",
                    "-o", str(Path(td) / "%(id)s.%(ext)s"),
                    url,
                ],
                capture_output=True, text=True, timeout=60,
            )
            vtt_files = list(Path(td).glob("*.vtt"))
            if not vtt_files:
                return {
                    "title": meta.get("title"),
                    "uploader": meta.get("uploader") or meta.get("channel"),
                    "duration_sec": meta.get("duration"),
                    "license": meta.get("license"),
                    "upload_date": meta.get("upload_date"),
                    "error": "no subtitles available for this video",
                }

            # Prefer requested lang; fallback to any
            target = None
            for f in vtt_files:
                if f".{lang}." in f.name or f"-{lang}." in f.name:
                    target = f
                    break
            if target is None:
                target = vtt_files[0]

            transcript_lang = target.stem.rsplit(".", 1)[-1] if "." in target.stem else lang
            raw = target.read_text(encoding="utf-8", errors="replace")
            text = _vtt_to_text(raw)
            if len(text) > _TRANSCRIPT_CHUNK_CHARS:
                text = text[:_TRANSCRIPT_CHUNK_CHARS] + " …[truncated]"

            return {
                "title": meta.get("title"),
                "uploader": meta.get("uploader") or meta.get("channel"),
                "duration_sec": meta.get("duration"),
                "license": meta.get("license"),
                "upload_date": meta.get("upload_date"),
                "transcript": text,
                "transcript_lang": transcript_lang,
            }
    except subprocess.TimeoutExpired:
        return {"error": "yt-dlp timed out"}
    except Exception as exc:
        _log.exception("extract_transcript failed")
        return {"error": str(exc)[:200]}


async def _node_summarize_llm(state: _SummarizeState) -> dict[str, Any]:
    if state.get("error"):
        return {}
    transcript = state.get("transcript") or ""
    if not transcript:
        return {"error": "no transcript to summarize"}

    title = state.get("title") or ""
    uploader = state.get("uploader") or ""
    lang = state.get("lang", "ja")
    duration = state.get("duration_sec")
    duration_str = f"{duration // 60}分{duration % 60}秒" if duration else "不明"

    lang_instruction = "日本語" if lang == "ja" else f"language: {lang}"

    system = (
        f"You are a research assistant. Summarize the video transcript in {lang_instruction}. "
        "Structure: ① one-sentence overview, ② 3-5 key points as bullets, "
        "③ one-sentence conclusion. Be concise and factual. "
        "If the transcript is incomplete or unclear, note that."
    )
    user = (
        f"Title: {title}\nCreator: {uploader}\nDuration: {duration_str}\n\n"
        f"Transcript:\n{transcript}"
    )

    started = time.monotonic()
    try:
        async with httpx.AsyncClient(timeout=_VLLM_TIMEOUT) as client:
            r = await client.post(
                f"{_VLLM_URL}/chat/completions",
                json={
                    "model": _VLLM_MODEL,
                    "messages": [
                        {"role": "system", "content": system},
                        {"role": "user", "content": user},
                    ],
                    "max_tokens": _SUMMARY_MAX_TOKENS,
                    "temperature": 0.3,
                },
                headers={"Content-Type": "application/json"},
            )
        elapsed = int((time.monotonic() - started) * 1000)
        if r.status_code >= 400:
            return {"error": f"vllm {r.status_code}: {r.text[:200]}"}
        resp = r.json()
        _log.info("summarize_llm done title=%s ms=%d", title[:40], elapsed)
    except httpx.TimeoutException:
        return {"error": "LLM request timed out"}
    except Exception as exc:
        _log.exception("summarize_llm failed")
        return {"error": str(exc)[:200]}

    summary = (
        ((resp.get("choices") or [{}])[0].get("message") or {}).get("content") or ""
    ).strip()
    if not summary:
        return {"error": "LLM returned empty summary"}
    return {"summary": summary}


async def _node_write_record(state: _SummarizeState) -> dict[str, Any]:
    if not _RW_URL or not state.get("summary"):
        return {}
    try:
        import secrets
        from datetime import datetime, timezone

        import psycopg

        rkey = f"sum-{secrets.token_hex(4)}"
        vertex_id = f"at://{_REPO}/com.etzhayyim.apps.recap.summarize/{rkey}"
        actor_did = state.get("actor_did") or _OWNER
        org_did = state.get("org_did") or _DEFAULT_ORG_DID
        conn = await psycopg.AsyncConnection.connect(_RW_URL, autocommit=True)
        try:
            await conn.execute(
                """
                INSERT INTO vertex_recap_summary
                    (vertex_id, rkey, owner_did, actor_did, org_did, at_did,
                     source_url, platform, title, uploader, duration_sec,
                     upload_date, license, transcript_lang, transcript,
                     summary, summary_lang, status, created_at)
                VALUES
                    (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """,
                [
                    vertex_id, rkey, _OWNER, actor_did, org_did, actor_did,
                    state.get("url"), state.get("platform"), state.get("title"),
                    state.get("uploader"), state.get("duration_sec"),
                    state.get("upload_date"), state.get("license"),
                    state.get("transcript_lang"),
                    (state.get("transcript") or "")[:4000],
                    state.get("summary"), state.get("lang"),
                    "done",
                    datetime.now(tz=timezone.utc).isoformat(),
                ],
            )
        finally:
            await conn.close()
        return {"summary_uri": vertex_id}
    except Exception as exc:
        _log.exception("write recap summary failed")
        return {"error": f"record: {exc!s}"[:300]}


def _build() -> StateGraph:
    g: StateGraph = StateGraph(_SummarizeState)
    g.add_node("validate", _node_validate)
    g.add_node("extract_transcript", _node_extract_transcript,
               retry_policy=RetryPolicy(max_attempts=2, backoff_factor=1.5))
    g.add_node("summarize_llm", _node_summarize_llm,
               retry_policy=RetryPolicy(max_attempts=2, backoff_factor=2.0))
    g.add_node("write_record", _node_write_record,
               retry_policy=RetryPolicy(max_attempts=2, backoff_factor=2.0))
    g.add_edge(START, "validate")
    g.add_edge("validate", "extract_transcript")
    g.add_edge("extract_transcript", "summarize_llm")
    g.add_edge("summarize_llm", "write_record")
    g.add_edge("write_record", END)
    return g


GRAPH = _build().compile(name="summarize")
