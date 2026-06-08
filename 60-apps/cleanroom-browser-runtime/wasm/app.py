"""
Clean-room actor WASM guest (componentize-py) — ADR 260607.

A self-contained implementation of the `etzhayyim:cleanroom/actor` WIT world:
an in-memory kotoba Datom store + the actor's REST `api` (CRUD + cursor
pagination + filtering + ?expand=) + MCP (`list-tools` / `call-tool`), with NO
host imports — no network, no clock, no fs. This is the production WASM drop-in
for the same contract the JS runtime (kotoba-runtime.mjs) implements.

Entities are embedded (this build targets `stripe-compat`); the generator that
emits one guest per actor reuses deepen_actors.PLATFORM_OVERRIDES / models.
"""
import json

HANDLE = "stripe-compat"
ENTITIES = ["Customer", "PaymentIntent", "Charge", "Refund",
            "Invoice", "Subscription", "Product", "Price"]
DEFAULT_LIMIT = 20
MAX_LIMIT = 100


def _pluralize(n):
    if len(n) > 1 and n[-1] == "y" and n[-2].lower() not in "aeiou":
        return n[:-1] + "ies"
    if n.endswith(("s", "x", "z", "ch", "sh")):
        return n + "es"
    return n + "s"


def _snake(n):
    out = []
    for i, c in enumerate(n):
        if c.isupper() and i:
            out.append("_")
        out.append(c.lower())
    return "".join(out)


class _Store:
    def __init__(self):
        self.data = {e: [] for e in ENTITIES}
        self.seq = 0
        self.plural = {e: _pluralize(e).lower() for e in ENTITIES}
        self.by_plural = {v: k for k, v in self.plural.items()}

    def _now(self):
        return "1970-01-01T00:00:%02dZ" % (self.seq % 60)

    def _id(self, e):
        self.seq += 1
        return e[:3].lower() + "_" + format(self.seq, "08x")

    def _ref(self, field):
        base = field[:-2] if field.endswith("Id") else field
        cand = base[:1].upper() + base[1:]
        return cand if (cand != "Id" and cand in self.data) else None

    def create(self, e, body):
        ts = self._now()
        rec = {"id": self._id(e)}
        rec.update(body)
        rec["createdAt"] = ts
        rec["updatedAt"] = ts
        self.data[e].append(rec)
        return 201, rec

    def list(self, e, q):
        rows = list(self.data[e])
        for k, v in q.items():
            if k in ("limit", "starting_after", "expand") or v in ("", None):
                continue
            rows = [r for r in rows if str(r.get(k)) == str(v)]
        try:
            limit = int(q.get("limit") or DEFAULT_LIMIT)
        except (TypeError, ValueError):
            limit = DEFAULT_LIMIT
        limit = max(1, min(limit, MAX_LIMIT))
        start = q.get("starting_after")
        if start:
            ids = [r["id"] for r in rows]
            if start in ids:
                rows = rows[ids.index(start) + 1:]
        page = rows[:limit]
        return 200, {"object": "list", "data": page, "has_more": len(rows) > limit,
                     "count": len(page), "total": len(self.data[e])}

    def get(self, e, eid, q):
        rec = next((r for r in self.data[e] if r["id"] == eid), None)
        if not rec:
            return 404, {"error": {"message": "Not found", "type": "not_found"}}
        out = dict(rec)
        want = (q.get("expand") or "").split(",")
        for f in list(out):
            ent = self._ref(f)
            if ent and f in want and out[f]:
                out[f + "_obj"] = next((r for r in self.data[ent] if r["id"] == out[f]), None)
        return 200, out

    def update(self, e, eid, body):
        rec = next((r for r in self.data[e] if r["id"] == eid), None)
        if not rec:
            return 404, {"error": {"message": "Not found", "type": "not_found"}}
        for k, v in body.items():
            if k not in ("id", "createdAt"):
                rec[k] = v
        rec["updatedAt"] = self._now()
        return 200, rec

    def remove(self, e, eid):
        arr = self.data[e]
        for i, r in enumerate(arr):
            if r["id"] == eid:
                del arr[i]
                return 200, {"id": eid, "deleted": True}
        return 404, {"error": {"message": "Not found", "type": "not_found"}}


_STORE = _Store()


def _route(method, path, query, body):
    if path == "/healthz":
        return 200, {"status": "ok", "actor": HANDLE}
    parts = path.strip("/").split("/")
    if len(parts) >= 2 and parts[0] == "v1":
        ent = _STORE.by_plural.get(parts[1])
        if not ent:
            return 404, {"error": {"message": "unknown collection"}}
        eid = parts[2] if len(parts) > 2 else None
        m = method.upper()
        if eid is None:
            if m == "POST":
                return _STORE.create(ent, body)
            if m == "GET":
                return _STORE.list(ent, query)
        else:
            if m == "GET":
                return _STORE.get(ent, eid, query)
            if m in ("POST", "PATCH"):
                return _STORE.update(ent, eid, body)
            if m == "DELETE":
                return _STORE.remove(ent, eid)
    return 404, {"error": {"message": "no route", "path": path}}


class WitWorld:
    """Implements the `etzhayyim:cleanroom/actor` world."""

    def handle_request(self, method, path, query, body):
        q = json.loads(query) if query else {}
        b = json.loads(body) if body else {}
        status, resp = _route(method, path, q, b)
        return json.dumps({"status": status, "body": resp})

    def list_tools(self):
        tools = []
        for e in ENTITIES:
            tools += [f"create_{_snake(e)}", f"list_{_snake(_pluralize(e))}",
                      f"get_{_snake(e)}", f"update_{_snake(e)}", f"delete_{_snake(e)}"]
        return json.dumps(tools)

    def call_tool(self, name, args):
        a = json.loads(args) if args else {}
        for op in ("create", "list", "get", "update", "delete"):
            if name.startswith(op + "_"):
                rest = name[len(op) + 1:]
                ent = next((e for e in ENTITIES
                            if (_snake(_pluralize(e)) if op == "list" else _snake(e)) == rest), None)
                if not ent:
                    break
                if op == "create":
                    s, r = _STORE.create(ent, a)
                elif op == "list":
                    s, r = _STORE.list(ent, a)
                elif op == "get":
                    s, r = _STORE.get(ent, a.get("id"), a)
                elif op == "update":
                    eid = a.pop("id", None)
                    s, r = _STORE.update(ent, eid, a)
                else:
                    s, r = _STORE.remove(ent, a.get("id"))
                return json.dumps({"status": s, "body": r})
        return json.dumps({"status": 400, "body": {"error": {"message": "unknown tool", "name": name}}})

    def healthz(self):
        return json.dumps({"status": "ok", "actor": HANDLE, "entities": ENTITIES})
