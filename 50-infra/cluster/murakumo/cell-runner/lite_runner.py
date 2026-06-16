#!/usr/bin/env python3
"""lite_runner — pure-stdlib node cell-runner (Tier-1 supervisor). ADR-2606161645 + 2605192415 §7.1.

THE residency tool, corrected: one supervisor per node (NOT one daemon per actor). It reads the
SAME `cells.edn` registry the canonical `kotoba-kotodama-cell-runner` uses, but needs NO uv / venv /
monorepo / DB migrations — only system `python3` — so it actually deploys on the headless fleet
Macs (whose cells are pure-stdlib). Run it as ONE system LaunchDaemon per node (KeepAlive=true →
crash-restart = stability).

Each tick (60 s) it fires every CRON cell assigned to this node whose minute matches, by importing
`<module>` from `--cells-root` and calling `<entry>()`; it records each fire as a `:cell.run/*` datom
on a local kotoba ops commit-DAG (content-addressed, append-only, verify-able) and serves a healthz
JSON. Layering (honest): tailscale = network · kotoba = state/runtime · murakumo = GPU/MLX inference
· lite_runner = cron supervision. It does NOT duplicate any of them.

Constitutional: it only SUPERVISES cells (which themselves hold the gates); no network I/O of its
own beyond what a cell does; cells stay idempotent/resume-safe; the ops log is the audit trail.

    python3 lite_runner.py --node issachar --registry cells.edn --cells-root ~/.etzhayyim/cells
    python3 lite_runner.py --node issachar ... --once     # fire all due cells once and exit (test/cron)
"""
from __future__ import annotations
import argparse
import hashlib
import http.server
import importlib
import json
import pathlib
import re
import socketserver
import sys
import threading
import time

# ── minimal EDN reader (subset: [] {} :kw "str" num bool nil) — same family as the actors' ──
_TOK = re.compile(r'[\s,]+|;[^\n]*|(\[|\]|\{|\}|"(?:\\.|[^"\\])*"|[^\s,\[\]{}]+)')


def _tokens(s):
    for m in _TOK.finditer(s):
        t = m.group(1)
        if t is not None:
            yield t


def _atom(t):
    if t.startswith('"'):
        return t[1:-1].replace('\\"', '"').replace('\\\\', '\\')
    if t == "true":
        return True
    if t == "false":
        return False
    if t == "nil":
        return None
    if t.startswith(":"):
        return t
    try:
        return int(t)
    except ValueError:
        try:
            return float(t)
        except ValueError:
            return t


_END = object()


def _parse(it):
    t = next(it)
    if t == "[":
        out = []
        while (x := _parse(it)) is not _END:
            out.append(x)
        return out
    if t == "{":
        out = {}
        while (k := _parse(it)) is not _END:
            out[k] = _parse(it)
        return out
    if t in ("]", "}"):
        return _END
    return _atom(t)


def parse_edn(s):
    return _parse(_tokens(s))


def load_cells(registry_path, node):
    """Return the cron-triggered cells assigned to `node` from cells.edn."""
    doc = parse_edn(pathlib.Path(registry_path).read_text(encoding="utf-8"))
    cells = doc.get(":cell", []) if isinstance(doc, dict) else []
    out = []
    for c in cells:
        if not isinstance(c, dict):
            continue
        if c.get(":node") != node:
            continue
        trig = c.get(":trigger", {})
        if isinstance(trig, dict) and trig.get(":kind") == "cron":
            out.append(c)
    return out


def cron_minute(expr):
    """Parse the minute field of a 5-field cron expr → set of minutes (supports N and */N and *)."""
    field = (expr or "").split()[0] if expr else "*"
    if field == "*":
        return set(range(60))
    if field.startswith("*/"):
        step = int(field[2:])
        return set(range(0, 60, step))
    return {int(x) for x in field.split(",") if x.strip().isdigit()}


# ── minimal kotoba ops commit-DAG (content-addressed, append-only) ──────────────
def _canonical(datoms, prev):
    return json.dumps({"prev": prev, "datoms": datoms}, ensure_ascii=False,
                      sort_keys=True, separators=(",", ":")).encode("utf-8")


def _tx_cid(datoms, prev=""):
    return "b" + hashlib.sha256(_canonical(datoms, prev)).hexdigest()


def _read_log(p):
    if not p.exists():
        return []
    return [parse_edn(l) for l in p.read_text(encoding="utf-8").splitlines()
            if l.strip() and not l.strip().startswith(";")]


def _head(p):
    txs = _read_log(p)
    return txs[-1][":tx/cid"] if txs else ""


def _edn_val(v):
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (int, float)):
        return repr(v)
    if isinstance(v, str):
        return v if v.startswith(":") else json.dumps(v, ensure_ascii=False)
    return json.dumps(str(v), ensure_ascii=False)


def append_run(log_path, *, node, cell, status, detail, as_of):
    """Append one :cell.run/* tx to the ops commit-DAG."""
    e = f"cell.run.{node}.{cell}.{as_of}"
    datoms = [[":db/add", e, ":cell.run/node", ":" + node],
              [":db/add", e, ":cell.run/cell", cell],
              [":db/add", e, ":cell.run/status", status],
              [":db/add", e, ":cell.run/as-of", as_of],
              [":db/add", e, ":cell.run/detail", detail[:200]]]
    prev = _head(log_path)
    cid = _tx_cid(datoms, prev)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    if not log_path.exists():
        log_path.write_text(";; lite_runner ops commit-DAG — append-only. ADR-2606161645.\n",
                            encoding="utf-8")
    body = " ".join("[" + " ".join(_edn_val(x) for x in d) + "]" for d in datoms)
    with log_path.open("a", encoding="utf-8") as fh:
        fh.write(f'{{:tx/id {len(_read_log(log_path)) + 1} :tx/as-of {as_of} '
                 f':tx/prev {json.dumps(prev)} :tx/cid {json.dumps(cid)} :tx/datoms [{body}]}}\n')
    return cid


def fire_cell(cell, cells_root):
    """Import <module> from cells_root and call <entry>(). Returns (status, detail)."""
    root = str(pathlib.Path(cells_root).expanduser())
    if root not in sys.path:
        sys.path.insert(0, root)
    try:
        mod = importlib.import_module(cell[":module"])
        fn = getattr(mod, cell.get(":entry", "fire"))
        res = fn()
        cid = (res or {}).get("cid") or (res or {}).get("head") if isinstance(res, dict) else None
        return ":ok", (str(cid)[:16] if cid else "ok")
    except Exception as e:  # noqa: BLE001 — a failing cell must not kill the supervisor
        return ":error", f"{type(e).__name__}: {e}"


# ── healthz ─────────────────────────────────────────────────────────────────────
_STATE = {"node": "?", "cells": [], "last": {}}


def _serve_healthz(port):
    state = _STATE

    class H(http.server.BaseHTTPRequestHandler):
        def do_GET(self):  # noqa: N802
            body = json.dumps({"ok": True, **state}).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *a):  # silence
            pass

    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("127.0.0.1", port), H) as srv:
        srv.serve_forever()


def run(node, registry, cells_root, ops_log, *, healthz_port=None, once=False, tick=60.0,
        now_fn=None, clock=None):
    cells = load_cells(registry, node)
    _STATE["node"] = node
    _STATE["cells"] = [c[":name"] for c in cells]
    if healthz_port:
        threading.Thread(target=_serve_healthz, args=(healthz_port,), daemon=True).start()
    fired_this_minute = {}
    while True:
        t = (clock() if clock else time.localtime())
        minute, stamp = t.tm_min, time.strftime("%Y%m%d%H%M", t)
        for c in cells:
            if minute in cron_minute(c.get(":trigger", {}).get(":expr")):
                key = (c[":name"], stamp)
                if key in fired_this_minute:
                    continue
                fired_this_minute[key] = True
                as_of = int(stamp)
                status, detail = fire_cell(c, cells_root)
                append_run(ops_log, node=node, cell=c[":name"], status=status, detail=detail,
                           as_of=as_of)
                _STATE["last"][c[":name"]] = {"status": status, "detail": detail, "at": stamp}
                print(f"lite_runner[{node}] {c[':name']} {status} {detail}", flush=True)
        if once:
            return _STATE
        # keep the dedup map small
        if len(fired_this_minute) > 256:
            fired_this_minute = {}
        time.sleep(tick)


def main(argv):
    ap = argparse.ArgumentParser(description="pure-stdlib node cell-runner (Tier-1 supervisor)")
    import os
    ap.add_argument("--node", default=os.environ.get("ETZHAYYIM_NODE_NAME", ""))
    ap.add_argument("--registry", required=True)
    ap.add_argument("--cells-root", required=True)
    ap.add_argument("--ops-log", default="~/.etzhayyim/cells/cell-ops.kotoba.edn")
    ap.add_argument("--healthz-port", type=int, default=0)
    ap.add_argument("--once", action="store_true")
    a = ap.parse_args(argv[1:])
    if not a.node:
        print("ERROR: --node (or ETZHAYYIM_NODE_NAME) required", file=sys.stderr)
        return 2
    run(a.node, a.registry, a.cells_root, pathlib.Path(a.ops_log).expanduser(),
        healthz_port=(a.healthz_port or None), once=a.once)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
