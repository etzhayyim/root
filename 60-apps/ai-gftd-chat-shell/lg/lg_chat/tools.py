"""6 tool implementations for lg-chat agent_chat graph.

Each tool is a plain sync function returning a dict.  The graph node
`_node_execute_tools` calls them synchronously inside a thread executor.

Ported from _archive/migrated-to-etzhayyim-2026-05-21/20-actors/magatama/
py/src/pymagatama/primitives/chat.py (2026-05-23).
"""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import os
import subprocess
import tempfile
import time
from typing import Any

_log = logging.getLogger(__name__)

# ── env ────────────────────────────────────────────────────────────────

_COMFYUI_URL = os.environ.get("COMFYUI_URL", "").rstrip("/")
_RW_URL = os.environ.get("RW_URL", "")
_WEB_SEARCH_PROVIDER = os.environ.get("WEB_SEARCH_PROVIDER", "brave")
_WEB_SEARCH_KEY = os.environ.get("WEB_SEARCH_KEY", "")
_B2_S3_ENDPOINT = os.environ.get("B2_S3_ENDPOINT", "https://s3.us-west-004.backblazeb2.com")
_B2_ACCESS_KEY = os.environ.get("B2_ACCESS_KEY_ID") or os.environ.get("B2_APPLICATION_KEY_ID", "")
_B2_SECRET_KEY = os.environ.get("B2_SECRET_ACCESS_KEY") or os.environ.get("B2_APPLICATION_KEY", "")
_B2_BUCKET = os.environ.get("CHAT_B2_BUCKET", "gftd-chat-artifacts")
_B2_PREFIX = os.environ.get("CHAT_B2_PREFIX", "chat")
_DISPATCHER_URL = os.environ.get("BPMN_DISPATCHER_INTERNAL_URL", "").rstrip("/")
_INTERNAL_SECRET = os.environ.get("CHAT_INTERNAL_SECRET", "")

TOOL_SCHEMAS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "code_exec",
            "description": (
                "Execute Python 3 code in an isolated subprocess. "
                "Returns stdout, stderr, and exit code. "
                "No network access; timeout 30 s."
            ),
            "parameters": {
                "type": "object",
                "required": ["code"],
                "properties": {
                    "code": {"type": "string"},
                    "timeoutSec": {"type": "integer", "default": 15, "maximum": 30},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "image_gen",
            "description": (
                "Generate an image with ComfyUI (SDXL). "
                "Returns a CDN URL when successful. "
                "Disabled when no ComfyUI endpoint is configured."
            ),
            "parameters": {
                "type": "object",
                "required": ["prompt"],
                "properties": {
                    "prompt": {"type": "string", "maxLength": 2000},
                    "negativePrompt": {"type": "string"},
                    "width": {"type": "integer", "default": 1024},
                    "height": {"type": "integer", "default": 1024},
                    "steps": {"type": "integer", "default": 4},
                    "seed": {"type": "integer"},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "file_save",
            "description": (
                "Save text or binary content to B2 storage. "
                "Returns a download URL. "
                "Disabled when B2 credentials are absent."
            ),
            "parameters": {
                "type": "object",
                "required": ["filename", "content"],
                "properties": {
                    "filename": {"type": "string", "maxLength": 256},
                    "content": {"type": "string"},
                    "encoding": {"type": "string", "enum": ["utf-8", "base64"], "default": "utf-8"},
                    "mimeType": {"type": "string", "default": "text/plain"},
                    "title": {"type": "string"},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "rag_search",
            "description": (
                "Search previous conversation history stored in RisingWave. "
                "Returns matching message snippets. "
                "Falls back gracefully if RW is unavailable."
            ),
            "parameters": {
                "type": "object",
                "required": ["query"],
                "properties": {
                    "query": {"type": "string", "maxLength": 500},
                    "topK": {"type": "integer", "default": 6, "maximum": 20},
                    "convId": {"type": "string"},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": (
                "Search the public web via Brave Search. "
                "Returns {title, url, snippet} hits. "
                "Falls back to RisingWave vector search when no API key is set."
            ),
            "parameters": {
                "type": "object",
                "required": ["query"],
                "properties": {
                    "query": {"type": "string", "maxLength": 500},
                    "topK": {"type": "integer", "default": 6, "maximum": 20},
                    "lang": {"type": "string", "default": "ja"},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "schedule_report",
            "description": (
                "Schedule a deep-research report. "
                "Returns immediately with a runId; the result will be posted back "
                "to this conversation when the report is ready. "
                "Requires BPMN dispatcher to be configured."
            ),
            "parameters": {
                "type": "object",
                "required": ["title", "prompt"],
                "properties": {
                    "title": {"type": "string", "maxLength": 256},
                    "prompt": {"type": "string", "maxLength": 4000},
                    "deliverChannel": {
                        "type": "string",
                        "enum": ["chat", "email", "pds-record"],
                        "default": "chat",
                    },
                    "deliverAt": {"type": "string", "format": "datetime"},
                },
            },
        },
    },
]


# ── tool: code_exec ────────────────────────────────────────────────────


def tool_code_exec(args: dict[str, Any]) -> dict[str, Any]:
    code = str(args.get("code") or "")
    timeout_sec = min(int(args.get("timeoutSec") or 15), 30)
    if not code.strip():
        return {"ok": False, "error": "code is required"}
    started = time.time()
    with tempfile.TemporaryDirectory(prefix="lg-chat-exec-") as td:
        script = os.path.join(td, "exec.py")
        with open(script, "w", encoding="utf-8") as f:
            f.write(code)
        try:
            proc = subprocess.run(
                ["python3", "-I", script],
                capture_output=True, text=True, timeout=timeout_sec, cwd=td,
                env={"PATH": "/usr/local/bin:/usr/bin:/bin", "HOME": td, "TMPDIR": td},
            )
        except subprocess.TimeoutExpired:
            return {"ok": False, "error": f"timeout after {timeout_sec}s"}
    return {
        "ok": proc.returncode == 0,
        "stdout": (proc.stdout or "")[:8000],
        "stderr": (proc.stderr or "")[:2000],
        "exitCode": proc.returncode,
        "durationMs": int((time.time() - started) * 1000),
    }


# ── tool: image_gen ────────────────────────────────────────────────────


def tool_image_gen(args: dict[str, Any], *, conv_id: str = "", owner_did: str = "") -> dict[str, Any]:
    if not _COMFYUI_URL:
        return {
            "ok": False,
            "error": "image_gen is not available — no ComfyUI endpoint configured (COMFYUI_URL)",
        }
    import urllib.parse
    import urllib.request

    prompt = str(args.get("prompt") or "").strip()
    if not prompt:
        return {"ok": False, "error": "prompt is required"}
    width = max(256, min(int(args.get("width") or 1024), 1536))
    height = max(256, min(int(args.get("height") or 1024), 1536))
    steps = max(2, min(int(args.get("steps") or 4), 30))
    seed = int(args.get("seed") or (int(time.time() * 1000) & 0x7FFFFFFF))
    neg = str(args.get("negativePrompt") or "nsfw, lowres, blurry")

    workflow: dict[str, Any] = {
        "ckpt": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": "v1-5-pruned-emaonly.safetensors"}},
        "latent": {"class_type": "EmptyLatentImage", "inputs": {"width": width, "height": height, "batch_size": 1}},
        "pos": {"class_type": "CLIPTextEncode", "inputs": {"text": prompt, "clip": ["ckpt", 1]}},
        "neg": {"class_type": "CLIPTextEncode", "inputs": {"text": neg, "clip": ["ckpt", 1]}},
        "ks": {"class_type": "KSampler", "inputs": {
            "seed": seed, "steps": steps, "cfg": 7.0,
            "sampler_name": "euler_ancestral", "scheduler": "normal", "denoise": 1.0,
            "model": ["ckpt", 0], "positive": ["pos", 0], "negative": ["neg", 0],
            "latent_image": ["latent", 0],
        }},
        "vae": {"class_type": "VAEDecode", "inputs": {"samples": ["ks", 0], "vae": ["ckpt", 2]}},
        "save": {"class_type": "SaveImage", "inputs": {"filename_prefix": "gftd_chat", "images": ["vae", 0]}},
    }
    _ua = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/129.0.0.0"
    headers = {"User-Agent": _ua, "Accept": "application/json", "Content-Type": "application/json"}

    started = time.time()
    try:
        body = json.dumps({"prompt": workflow}).encode()
        req = urllib.request.Request(f"{_COMFYUI_URL}/prompt", data=body, method="POST",
                                     headers=headers)
        with urllib.request.urlopen(req, timeout=15.0) as r:
            resp = json.loads(r.read())
        prompt_id = resp.get("prompt_id")
        if not prompt_id:
            return {"ok": False, "error": f"comfy no prompt_id: {resp}"}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": f"comfy /prompt: {exc!s}"[:200]}

    # Poll for completion
    deadline = time.time() + 120
    delay = 1.5
    entry = None
    while time.time() < deadline:
        try:
            req2 = urllib.request.Request(f"{_COMFYUI_URL}/history/{prompt_id}", headers=headers)
            with urllib.request.urlopen(req2, timeout=10.0) as r2:
                hist = json.loads(r2.read())
            rec = hist.get(prompt_id)
            if rec and rec.get("status", {}).get("completed"):
                entry = rec
                break
        except Exception:
            pass
        time.sleep(delay)
        delay = min(delay * 1.4, 4.0)

    if not entry:
        return {"ok": False, "error": f"comfy timeout after 120s", "promptId": prompt_id}

    images: list[dict[str, Any]] = []
    for node_out in (entry.get("outputs") or {}).values():
        if isinstance(node_out, dict) and "images" in node_out:
            images.extend(node_out["images"] or [])
    if not images:
        return {"ok": False, "error": "comfy returned no images", "promptId": prompt_id}

    img = images[0]
    qs = f"filename={urllib.parse.quote(img.get('filename',''))}&subfolder={urllib.parse.quote(img.get('subfolder',''))}&type={urllib.parse.quote(img.get('type','output'))}"
    img_url = f"{_COMFYUI_URL}/view?{qs}"
    return {
        "ok": True,
        "imageUrl": img_url,
        "width": width, "height": height, "seed": seed,
        "promptId": prompt_id,
        "durationMs": int((time.time() - started) * 1000),
    }


# ── tool: file_save ────────────────────────────────────────────────────


def tool_file_save(args: dict[str, Any], *, conv_id: str = "", owner_did: str = "") -> dict[str, Any]:
    if not _B2_ACCESS_KEY or not _B2_SECRET_KEY:
        return {"ok": False, "error": "file_save is not available — B2 credentials not configured"}
    import base64 as b64
    import boto3  # type: ignore[import-untyped]

    filename = str(args.get("filename") or "").strip()
    content = str(args.get("content") or "")
    if not filename or not content:
        return {"ok": False, "error": "filename and content are required"}
    encoding = str(args.get("encoding") or "utf-8").lower()
    mime = str(args.get("mimeType") or "text/plain")
    if encoding == "base64":
        try:
            blob = b64.b64decode(content)
        except Exception as exc:
            return {"ok": False, "error": f"invalid base64: {exc}"}
    else:
        blob = content.encode("utf-8")

    sha = hashlib.sha256(blob).hexdigest()[:12]
    safe = filename.replace("/", "_").replace("..", "_")[:128]
    key = f"{_B2_PREFIX}/{owner_did.replace(':', '_') or 'anon'}/{conv_id or 'nocid'}/{sha}-{safe}"
    try:
        s3 = boto3.client("s3", endpoint_url=_B2_S3_ENDPOINT,
                          aws_access_key_id=_B2_ACCESS_KEY,
                          aws_secret_access_key=_B2_SECRET_KEY,
                          region_name="us-west-004")
        s3.put_object(Bucket=_B2_BUCKET, Key=key, Body=blob, ContentType=mime)
    except Exception as exc:
        return {"ok": False, "error": f"B2 PUT failed: {exc!s}"[:200]}
    cdn_url = f"https://cdn.gftd.ai/{key}"
    return {"ok": True, "filename": filename, "mimeType": mime, "byteSize": len(blob),
            "b2Key": key, "cdnUrl": cdn_url}


# ── tool: rag_search ───────────────────────────────────────────────────


def tool_rag_search(args: dict[str, Any], *, owner_did: str = "") -> dict[str, Any]:
    query = str(args.get("query") or "")
    top_k = min(int(args.get("topK") or 6), 20)
    conv_id_filter = str(args.get("convId") or "").strip() or None
    if not query.strip():
        return {"ok": False, "error": "query is required"}
    if not _RW_URL:
        return {"ok": False, "error": "rag_search unavailable — RW_URL not configured", "hits": []}
    try:
        import psycopg

        pat = f"%{query[:200]}%"
        with psycopg.connect(_RW_URL, autocommit=True) as conn:
            if conv_id_filter:
                rows = conn.execute(  # type: ignore[arg-type]
                    "SELECT conv_id, msg_id, role, substring(content, 1, 400), ts_ms "
                    "FROM vertex_chat_message "
                    "WHERE owner_did = %s AND conv_id = %s AND status = 'active' "
                    "  AND content ILIKE %s "
                    f"ORDER BY ts_ms DESC LIMIT {top_k}",
                    (owner_did or "anon", conv_id_filter, pat),
                ).fetchall()
            else:
                rows = conn.execute(  # type: ignore[arg-type]
                    "SELECT conv_id, msg_id, role, substring(content, 1, 400), ts_ms "
                    "FROM vertex_chat_message "
                    "WHERE owner_did = %s AND status = 'active' "
                    "  AND content ILIKE %s "
                    f"ORDER BY ts_ms DESC LIMIT {top_k}",
                    (owner_did or "anon", pat),
                ).fetchall()
        hits = [{"convId": r[0], "msgId": r[1], "role": r[2], "snippet": r[3], "tsMs": r[4]}
                for r in rows]
        return {"ok": True, "query": query, "hits": hits}
    except Exception as exc:  # noqa: BLE001
        _log.warning("rag_search failed: %s", exc)
        return {"ok": False, "error": f"rag_search: {type(exc).__name__}", "hits": []}


# ── tool: web_search ───────────────────────────────────────────────────


def tool_web_search(args: dict[str, Any]) -> dict[str, Any]:
    query = str(args.get("query") or "")
    top_k = min(int(args.get("topK") or 6), 20)
    if not query.strip():
        return {"ok": False, "error": "query is required"}

    if _WEB_SEARCH_KEY and _WEB_SEARCH_PROVIDER == "brave":
        import urllib.error
        import urllib.parse
        import urllib.request

        url = f"https://api.search.brave.com/res/v1/web/search?q={urllib.parse.quote(query)}&count={top_k}"
        req = urllib.request.Request(url, headers={
            "Accept": "application/json",
            "Accept-Encoding": "gzip",
            "X-Subscription-Token": _WEB_SEARCH_KEY,
        })
        try:
            with urllib.request.urlopen(req, timeout=15.0) as r:
                import gzip
                raw = r.read()
                if r.headers.get("Content-Encoding") == "gzip":
                    raw = gzip.decompress(raw)
                data = json.loads(raw)
            results = data.get("web", {}).get("results") or []
            hits = [{"title": h.get("title", ""), "url": h.get("url", ""),
                     "snippet": h.get("description", "")[:500]}
                    for h in results[:top_k]]
            return {"ok": True, "query": query, "hits": hits, "provider": "brave"}
        except urllib.error.HTTPError as exc:
            _log.warning("brave search HTTP %s: %s", exc.code, exc)
        except Exception as exc:
            _log.warning("brave search failed: %s", exc)

    # Fallback: RisingWave ILIKE on any indexed bluesky posts
    if _RW_URL:
        try:
            import psycopg

            pat = f"%{query[:200]}%"
            with psycopg.connect(_RW_URL, autocommit=True) as conn:
                rows = conn.execute(  # type: ignore[arg-type]
                    "SELECT uri, substring(text, 1, 400) "
                    "FROM vertex_bluesky_post "
                    "WHERE text ILIKE %s "
                    f"ORDER BY created_at DESC LIMIT {top_k}",
                    (pat,),
                ).fetchall()
            hits = [{"title": r[0], "url": r[0], "snippet": r[1]} for r in rows]
            return {"ok": bool(hits), "query": query, "hits": hits, "provider": "risingwave-ilike"}
        except Exception as exc:
            _log.warning("web_search RW fallback failed: %s", exc)

    return {"ok": False, "error": "web_search: no provider available", "hits": []}


# ── tool: schedule_report ─────────────────────────────────────────────


def tool_schedule_report(args: dict[str, Any], *, conv_id: str = "", msg_id: str = "",
                         owner_did: str = "") -> dict[str, Any]:
    if not _DISPATCHER_URL:
        return {"ok": False, "error": "schedule_report unavailable — BPMN_DISPATCHER_INTERNAL_URL not configured"}
    title = str(args.get("title") or "").strip()
    prompt = str(args.get("prompt") or "").strip()
    if not title or not prompt:
        return {"ok": False, "error": "title and prompt are required"}

    import urllib.request

    body = {
        "convId": conv_id,
        "msgId": msg_id,
        "ownerDid": owner_did,
        "title": title,
        "prompt": prompt,
        "deliverAt": str(args.get("deliverAt") or ""),
        "deliverChannel": str(args.get("deliverChannel") or "chat"),
    }
    headers: dict[str, str] = {"Content-Type": "application/json"}
    if _INTERNAL_SECRET:
        sig = hmac.new(_INTERNAL_SECRET.encode(), json.dumps(body).encode(), hashlib.sha256).hexdigest()
        headers["x-internal-trust"] = sig
    url = f"{_DISPATCHER_URL}/xrpc/ai.gftd.apps.chat.scheduleReport"
    try:
        req = urllib.request.Request(url, data=json.dumps(body).encode(), method="POST", headers=headers)
        with urllib.request.urlopen(req, timeout=30.0) as r:
            resp = json.loads(r.read())
        return {"ok": bool(resp.get("ok")), "runId": resp.get("runId", ""),
                "scheduledAt": resp.get("scheduledAt", "")}
    except Exception as exc:
        return {"ok": False, "error": f"schedule_report dispatcher: {exc!s}"[:200]}


# ── dispatcher ────────────────────────────────────────────────────────


def dispatch_tool(name: str, args: dict[str, Any], *,
                  conv_id: str = "", msg_id: str = "", owner_did: str = "") -> dict[str, Any]:
    if name == "code_exec":
        return tool_code_exec(args)
    if name == "image_gen":
        return tool_image_gen(args, conv_id=conv_id, owner_did=owner_did)
    if name == "file_save":
        return tool_file_save(args, conv_id=conv_id, owner_did=owner_did)
    if name == "rag_search":
        return tool_rag_search(args, owner_did=owner_did)
    if name == "web_search":
        return tool_web_search(args)
    if name == "schedule_report":
        return tool_schedule_report(args, conv_id=conv_id, msg_id=msg_id, owner_did=owner_did)
    return {"ok": False, "error": f"unknown tool: {name!r}"}
