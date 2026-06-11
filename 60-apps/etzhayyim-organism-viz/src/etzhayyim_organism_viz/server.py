"""Realtime FastAPI server — SSE event stream + chat + state snapshot.

Endpoints:
  GET  /                 → index.html (interactive bonsai + chat)
  GET  /static/*         → static assets
  GET  /api/state        → full EcosystemSnapshot
  GET  /api/events       → SSE stream of file-system + git activity
  POST /api/chat         → {entity_id, message} → entity's voice

Substrate-boundary note (§1.6): this server only reads /repo. It does NOT
hold credentials, does NOT push to remote, does NOT mutate _observations/.
The organism CNS pod writes; this pod just listens and speaks.
"""

from __future__ import annotations

import asyncio
import json
import os
import time
from pathlib import Path
from typing import Any, AsyncIterator

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .ecosystem import snapshot
from .chat import chat


# ── pub/sub bus ───────────────────────────────────────────────────────────
# Every SSE client subscribes; chat broadcasts to all subscribers so
# multiple operators / agents see each other's conversations with the
# organism in real time. 縁起 made literal.
_subscribers: set[asyncio.Queue] = set()


async def _broadcast(payload: dict[str, Any]) -> None:
    dead: list[asyncio.Queue] = []
    for q in _subscribers:
        try:
            q.put_nowait(payload)
        except asyncio.QueueFull:
            dead.append(q)
    for q in dead:
        _subscribers.discard(q)


REPO = Path(os.environ.get("ETZ_REPO", "/repo")).resolve()
# Prefer Svelte build output (web/dist) — falls back to the legacy vanilla
# frontend/ in the same package if dist/ wasn't produced.
PKG_DIR = Path(__file__).resolve().parent
DIST_DIR = PKG_DIR / "dist"
LEGACY_DIR = PKG_DIR / "frontend"
FRONTEND_DIR = DIST_DIR if DIST_DIR.is_dir() else LEGACY_DIR

app = FastAPI(title="etzhayyim-organism-viz", version="0.4.0")


# ── static + index ────────────────────────────────────────────────────────

if FRONTEND_DIR.is_dir():
    # Svelte build emits an `assets/` subtree; serve the whole dist verbatim.
    assets = FRONTEND_DIR / "assets"
    if assets.is_dir():
        app.mount("/assets", StaticFiles(directory=str(assets)), name="assets")
    # also serve the legacy /static prefix so the old vanilla frontend still works
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")


@app.get("/")
async def index():
    idx = FRONTEND_DIR / "index.html"
    if idx.exists():
        return FileResponse(str(idx))
    return JSONResponse({"error": "frontend not built"}, status_code=500)


# ── state snapshot ────────────────────────────────────────────────────────

@app.get("/api/state")
async def state():
    snap = snapshot(REPO)
    return JSONResponse(snap.to_json())


@app.get("/api/healthz")
async def healthz():
    return {"ok": True, "repo": str(REPO), "ts": int(time.time())}


# ── chat ──────────────────────────────────────────────────────────────────

class ChatIn(BaseModel):
    entity_id: str
    message: str


@app.post("/api/chat")
async def api_chat(body: ChatIn):
    snap = snapshot(REPO)
    result = chat(snap, body.entity_id, body.message)
    # Broadcast the exchange so other connected viewers see the conversation
    # in their activity stream. Operator (you) lines and entity replies both
    # go out; receivers can choose to display them differently.
    if result.get("ok"):
        await _broadcast({
            "type": "chat",
            "ts": result.get("ts", int(time.time())),
            "entity": body.entity_id,
            "summary": f"chat → {body.entity_id}",
            "message": body.message,
            "voice": result["voice"],
            "intent": result.get("intent"),
        })
    return result


@app.get("/api/pruning")
async def api_pruning():
    from .pruning import scan_all, to_markdown
    cands = scan_all(REPO)
    return {
        "candidates": [c.__dict__ for c in cands],
        "markdown":   to_markdown(REPO, cands),
    }


# ── SSE event stream ──────────────────────────────────────────────────────

_WATCH_PATHS = [
    "_observations",
    "90-docs/adr",
    "40-engine/kotoba/crates/kotoba-kotodama/cells",
    ".git/refs/heads/main",
    ".git/HEAD",
    "LANDS.md",
    "MEMBERS.md",
    "SISTER-CORPS.md",
    "COUNCIL.md",
]


def _mtime_snapshot(repo: Path) -> dict[str, float]:
    snap: dict[str, float] = {}
    for rel in _WATCH_PATHS:
        p = repo / rel
        if p.is_file():
            try:
                snap[rel] = p.stat().st_mtime
            except OSError:
                pass
        elif p.is_dir():
            try:
                snap[rel] = max(
                    (c.stat().st_mtime for c in p.rglob("*") if c.is_file()),
                    default=p.stat().st_mtime,
                )
            except OSError:
                pass
    return snap


async def _event_generator(request: Request) -> AsyncIterator[str]:
    prev = _mtime_snapshot(REPO)
    # initial "hello" event with full state
    snap0 = snapshot(REPO)
    yield _sse({"type": "hello", "ts": int(time.time()),
                "summary": "ecosystem online",
                "state": snap0.to_json()})
    last_full = time.time()

    # subscribe to the chat broadcast bus
    q: asyncio.Queue = asyncio.Queue(maxsize=64)
    _subscribers.add(q)
    try:
        while True:
            if await request.is_disconnected():
                return
            # Drain any broadcast events first (chat conversations from others)
            drained = 0
            while not q.empty() and drained < 16:
                try:
                    yield _sse(q.get_nowait())
                    drained += 1
                except asyncio.QueueEmpty:
                    break

            # Wait up to 2s OR until a broadcast lands
            try:
                ev = await asyncio.wait_for(q.get(), timeout=2.0)
                yield _sse(ev)
            except asyncio.TimeoutError:
                pass

            # File-system change detection
            cur = _mtime_snapshot(REPO)
            for k, v in cur.items():
                if prev.get(k) != v:
                    yield _sse({
                        "type": "change",
                        "path": k,
                        "ts": int(v),
                        "summary": f"changed: {k}",
                    })
            prev = cur
            # Periodic full state (every 30s) for reconnecting clients
            if time.time() - last_full > 30:
                snap = snapshot(REPO)
                yield _sse({"type": "tick", "ts": int(time.time()),
                            "summary": "periodic snapshot",
                            "state": snap.to_json()})
                last_full = time.time()
            else:
                yield _sse({"type": "heartbeat", "ts": int(time.time())})
    finally:
        _subscribers.discard(q)


def _sse(payload: dict[str, Any]) -> str:
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"


@app.get("/api/events")
async def events(request: Request):
    return StreamingResponse(
        _event_generator(request),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
