#!/usr/bin/env python3
"""kotoba_local_server — a stdlib HTTP stand-in for the kotoba XRPC surface (ADR-2606064500 R1).

This is NOT the production kotoba engine. It is a tiny http.server that speaks the EXACT wire
shapes `src/kotoba-spatial.ts` and `methods/ingest.py` use, backed by the kotoba_local
EAVT/AVET reference store — so the maps↔kotoba HTTP loop (ingest gate + Bearer auth + AVET
cell query + response shape) can be exercised END-TO-END offline, before any live endpoint is
wired. It is the local target for the R1 go-live dry-run (methods/README.md).

Endpoints (matching the adapter + ingest.py verbatim):
  POST /xrpc/com.etzhayyim.apps.kotobase.kg.ingest_batch   (Bearer auth required)
       body  {"entities":[{id,type,label_en,claims:[{pred,value}],relations}]}
  POST /xrpc/com.etzhayyim.apps.kotoba.graph.sparql        (AVET cell query)
       body  {"index":"avet","predicate","objects":[...],"filter":{"predicate","in":[...]},"limit"}
       reply {"entities":[{id,claims:[{pred,value}]}]}
  GET  /xrpc/com.etzhayyim.apps.kotobase.kg.entity?id=<id>
       reply {"entity":{id,claims:[{pred,value}]}}

stdlib only. Usage:
    python3 kotoba_local_server.py [--port 8077] [--token <bearer>]
"""
from __future__ import annotations
import json, sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

from kotoba_local import KotobaLocal

STORE = KotobaLocal()
TOKEN = None  # set by main(); when set, ingest requires Authorization: Bearer <TOKEN>


class Handler(BaseHTTPRequestHandler):
    def _send(self, code, obj):
        body = json.dumps(obj).encode("utf-8")
        self.send_response(code)
        self.send_header("content-type", "application/json")
        self.send_header("content-length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_json(self):
        n = int(self.headers.get("content-length", 0))
        return json.loads(self.rfile.read(n) or b"{}")

    def log_message(self, *a):  # quiet
        pass

    def do_GET(self):
        u = urlparse(self.path)
        if u.path.endswith("/kg.entity") or u.path.endswith(".kg.entity"):
            ids = parse_qs(u.query).get("id", [])
            ent = STORE.entity(ids[0]) if ids else None
            if ent is None:
                return self._send(404, {"error": "not found"})
            return self._send(200, {"entity": ent})
        return self._send(404, {"error": "unknown path"})

    def do_POST(self):
        u = urlparse(self.path)
        try:
            body = self._read_json()
        except Exception as e:
            return self._send(400, {"error": f"bad json: {e}"})

        if u.path.endswith("kg.ingest_batch"):
            # no-server-key (§4): a member/operator Bearer is mandatory for writes
            auth = self.headers.get("authorization", "")
            if TOKEN is not None and auth != f"Bearer {TOKEN}":
                return self._send(401, {"error": "missing/invalid Bearer (no-server-key: member-signed)"})
            n = STORE.ingest_batch(body)
            return self._send(200, {"ok": True, "ingested": n})

        if u.path.endswith("graph.sparql"):
            flt = body.get("filter") or {}
            ents = STORE.avet_query(
                predicate=body.get("predicate"),
                objects=body.get("objects", []),
                filter_pred=flt.get("predicate"),
                filter_in=flt.get("in"),
                limit=int(body.get("limit", 500)),
            )
            return self._send(200, {"entities": ents})

        return self._send(404, {"error": "unknown path"})


def serve(port: int, token: str | None):
    global TOKEN
    TOKEN = token
    return ThreadingHTTPServer(("127.0.0.1", port), Handler)


def main(argv):
    port = int(argv[argv.index("--port") + 1]) if "--port" in argv else 8077
    token = argv[argv.index("--token") + 1] if "--token" in argv else None
    httpd = serve(port, token)
    print(f"kotoba_local_server on http://127.0.0.1:{port} (token={'set' if token else 'none'})")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        httpd.shutdown()


if __name__ == "__main__":
    main(sys.argv)
