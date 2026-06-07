#!/usr/bin/env python3
"""healthz-sidecar — minimal HTTP liveness responder for an LSP daemon.

Spawned in the background by ``run-langserver.sh``. Each LSP gets one sidecar
on ``<lsp_port> + 100`` (the 15600-15699 range, mirroring the kotodama cell
healthz allocation convention).

Probes performed on each ``GET /healthz``:
  1. TCP-connect to ``127.0.0.1:<lsp_port>``  (catches socat dead, port unbound)
  2. If --deep: send an LSP ``initialize`` JSON-RPC request and read the
     ``initialized`` response (catches LSP child deadlocked)

Response:
  200 + {"ok": true, "lang": "<id>", "lsp_port": <p>, "uptime_seconds": <n>}
  503 + {"ok": false, "lang": "<id>", "error": "<reason>"}

Constraints (per CLAUDE.md):
  - stdlib only — no third-party deps
  - no MST / IPFS / L2 writes (computation only)
  - Apache 2.0 + Charter Rider applies (this file is etzhayyim first-party)
"""

from __future__ import annotations

import argparse
import http.server
import json
import os
import socket
import socketserver
import sys
import threading
import time
from typing import Any


START_TS = time.monotonic()


class Stats:
    """Thread-safe counter store for /metrics Prometheus rendering (L7)."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self.up: int = 0
        self.last_probe_latency_seconds: float = 0.0
        self.last_deep_probe_latency_seconds: float = 0.0
        self.probe_failures_total: int = 0
        self.probe_total: int = 0

    def record(self, ok: bool, latency: float, deep: bool) -> None:
        with self._lock:
            self.up = 1 if ok else 0
            if deep:
                self.last_deep_probe_latency_seconds = latency
            else:
                self.last_probe_latency_seconds = latency
            self.probe_total += 1
            if not ok:
                self.probe_failures_total += 1

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            return {
                "up": self.up,
                "last_probe_latency_seconds": self.last_probe_latency_seconds,
                "last_deep_probe_latency_seconds": self.last_deep_probe_latency_seconds,
                "probe_failures_total": self.probe_failures_total,
                "probe_total": self.probe_total,
            }


STATS = Stats()


def tcp_probe(host: str, port: int, timeout: float = 0.5) -> tuple[bool, str]:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True, ""
    except (socket.timeout, ConnectionRefusedError, OSError) as exc:
        return False, f"tcp_probe({host}:{port}): {exc!r}"


def lsp_handshake_probe(host: str, port: int, timeout: float = 2.0) -> tuple[bool, str]:
    """Send LSP `initialize` and read the response. Catches LSP-level deadlock.

    LSP framing: Content-Length: N\r\n\r\n<JSON>
    """
    req: dict[str, Any] = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "processId": None,
            "rootUri": None,
            "capabilities": {},
        },
    }
    payload = json.dumps(req).encode("utf-8")
    framed = b"Content-Length: " + str(len(payload)).encode() + b"\r\n\r\n" + payload

    try:
        with socket.create_connection((host, port), timeout=timeout) as s:
            s.sendall(framed)
            s.settimeout(timeout)
            # Read at least the response header
            buf = b""
            while b"\r\n\r\n" not in buf and len(buf) < 4096:
                chunk = s.recv(1024)
                if not chunk:
                    break
                buf += chunk
            if b"Content-Length:" not in buf:
                return False, f"lsp_initialize: no Content-Length in response (got {buf[:120]!r})"
            return True, ""
    except (socket.timeout, ConnectionRefusedError, OSError) as exc:
        return False, f"lsp_handshake({host}:{port}): {exc!r}"


def render_prometheus(lang: str, host: str, lsp_port: int) -> bytes:
    s = STATS.snapshot()
    uptime = int(time.monotonic() - START_TS)
    labels = f'lang="{lang}",host="{host}"'
    lines = [
        "# HELP etzhayyim_langserver_up 1 if the LSP is reachable on its TCP port, 0 otherwise.",
        "# TYPE etzhayyim_langserver_up gauge",
        f'etzhayyim_langserver_up{{{labels}}} {s["up"]}',
        "# HELP etzhayyim_langserver_uptime_seconds Uptime of the healthz sidecar in seconds.",
        "# TYPE etzhayyim_langserver_uptime_seconds counter",
        f'etzhayyim_langserver_uptime_seconds{{{labels}}} {uptime}',
        "# HELP etzhayyim_langserver_probe_latency_seconds Last probe round-trip in seconds.",
        "# TYPE etzhayyim_langserver_probe_latency_seconds gauge",
        f'etzhayyim_langserver_probe_latency_seconds{{{labels},probe="tcp"}} {s["last_probe_latency_seconds"]:.6f}',
        f'etzhayyim_langserver_probe_latency_seconds{{{labels},probe="deep"}} {s["last_deep_probe_latency_seconds"]:.6f}',
        "# HELP etzhayyim_langserver_probe_failures_total Total probe failures since sidecar start.",
        "# TYPE etzhayyim_langserver_probe_failures_total counter",
        f'etzhayyim_langserver_probe_failures_total{{{labels}}} {s["probe_failures_total"]}',
        "# HELP etzhayyim_langserver_probe_total Total probes since sidecar start.",
        "# TYPE etzhayyim_langserver_probe_total counter",
        f'etzhayyim_langserver_probe_total{{{labels}}} {s["probe_total"]}',
        "",
    ]
    return "\n".join(lines).encode("utf-8")


def make_handler(
    lang: str, host: str, lsp_port: int, deep: bool
) -> type[http.server.BaseHTTPRequestHandler]:
    class HealthzHandler(http.server.BaseHTTPRequestHandler):
        def log_message(self, fmt: str, *args: Any) -> None:  # noqa: D401
            # Forward to stderr so launchd captures it via StandardErrorPath
            sys.stderr.write(f"[healthz/{lang}] {fmt % args}\n")

        def do_GET(self) -> None:  # noqa: N802 (http.server contract)
            if self.path in ("/healthz", "/healthz/", "/"):
                self._handle_healthz()
            elif self.path in ("/metrics", "/metrics/"):
                self._handle_metrics()
            else:
                self.send_response(404)
                self.end_headers()

        def _handle_healthz(self) -> None:
            t0 = time.monotonic()
            ok, err = tcp_probe("127.0.0.1", lsp_port)
            tcp_latency = time.monotonic() - t0
            STATS.record(ok, tcp_latency, deep=False)

            if ok and deep:
                t1 = time.monotonic()
                ok, err = lsp_handshake_probe("127.0.0.1", lsp_port)
                STATS.record(ok, time.monotonic() - t1, deep=True)

            body: dict[str, Any] = {
                "ok": ok,
                "lang": lang,
                "host": host,
                "lsp_port": lsp_port,
                "uptime_seconds": int(time.monotonic() - START_TS),
                "deep_probe": deep,
            }
            if not ok:
                body["error"] = err
            payload = json.dumps(body).encode()
            self.send_response(200 if ok else 503)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

        def _handle_metrics(self) -> None:
            payload = render_prometheus(lang, host, lsp_port)
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; version=0.0.4; charset=utf-8")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

    return HealthzHandler


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--lang", required=True, help="Language identifier (rust/python/...)")
    ap.add_argument("--lsp-port", type=int, required=True, help="The LSP's own TCP port")
    ap.add_argument(
        "--healthz-port",
        type=int,
        required=True,
        help="Port to bind this healthz responder on (default convention: lsp-port + 100)",
    )
    ap.add_argument("--bind", default="127.0.0.1", help="Bind address (default 127.0.0.1; mesh-IP for fleet-wide reach)")
    ap.add_argument("--host", default=os.environ.get("ETZHAYYIM_NODE_NAME", "unknown"), help="Tribe/host name for metric labels (default: $ETZHAYYIM_NODE_NAME or 'unknown')")
    ap.add_argument("--deep", action="store_true", help="Also send LSP `initialize` handshake probe")
    args = ap.parse_args()

    handler = make_handler(args.lang, args.host, args.lsp_port, args.deep)

    class ReusableServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
        allow_reuse_address = True
        daemon_threads = True

    with ReusableServer((args.bind, args.healthz_port), handler) as srv:
        sys.stderr.write(
            f"[healthz/{args.lang}] listening on http://{args.bind}:{args.healthz_port}/healthz "
            f"probing LSP at 127.0.0.1:{args.lsp_port} deep={args.deep}\n"
        )
        try:
            srv.serve_forever()
        except KeyboardInterrupt:
            return 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
