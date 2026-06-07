// kotoba-runtime.mjs
//
// Browser-LOCAL runtime for the clean-room actor corpus (ADR 260607).
//
// This is the JavaScript reference implementation of the contract that each
// actor's content-addressed kotoba-WASM component (`EtzhayyimWasmComponent`,
// ADR-2606014500) compiles to: an in-memory kotoba Datom store + the same
// REST / MCP surface declared in the actor's manifest.json. It lets every
// registered actor's api / mcp surface RUN browser-local TODAY (no server, no
// network) while the compiled WASM is the production drop-in for the same
// contract. Runs unchanged in a browser (`<script type="module">`) and in Node.
//
// Semantics mirror the L4 production main.py: cursor pagination
// (limit/starting_after/has_more), filtering by any field, relationship
// expansion (?expand=<field>), strict-ish validation.

export function pluralize(n) {
  if (/[^aeiou]y$/i.test(n)) return n.slice(0, -1) + "ies";
  if (/(s|x|z|ch|sh)$/i.test(n)) return n + "es";
  return n + "s";
}

export function snake(n) {
  return n.replace(/(?<!^)(?=[A-Z])/g, "_").toLowerCase();
}

const DEFAULT_LIMIT = 20;
const MAX_LIMIT = 100;

export class KotobaActor {
  constructor(manifest) {
    this.manifest = manifest;
    this.handle = manifest.handle;
    this.entities = manifest.entities || [];
    this.store = {};              // entity -> [records]  (the Datom store)
    this._seq = 0;
    this.plural = {};
    this.byPlural = {};
    for (const e of this.entities) {
      const p = pluralize(e).toLowerCase();
      this.plural[e] = p;
      this.byPlural[p] = e;
      this.store[e] = [];
    }
  }

  _now() {
    // monotonic, deterministic-ish ISO stamp (no wall clock dependency)
    return new Date(1_700_000_000_000 + this._seq * 1000).toISOString();
  }
  _id(e) {
    this._seq += 1;
    return e.slice(0, 3).toLowerCase() + "_" + this._seq.toString(16).padStart(8, "0");
  }
  _refEntity(field) {
    // a reference field is either `<entity>Id` (category models) or bare
    // `<entity>` (curated-override models, e.g. stripe's `customer`).
    let base = field.endsWith("Id") ? field.slice(0, -2) : field;
    const cand = base.charAt(0).toUpperCase() + base.slice(1);
    return cand !== "Id" && this.entities.includes(cand) ? cand : null;
  }

  // ── core ops ────────────────────────────────────────────────────────────
  create(entity, body = {}) {
    if (!this.store[entity]) return [404, { error: { message: "unknown entity" } }];
    const ts = this._now();
    const rec = { id: this._id(entity), ...body, createdAt: ts, updatedAt: ts };
    this.store[entity].push(rec);
    return [201, rec];
  }

  list(entity, query = {}) {
    if (!this.store[entity]) return [404, { error: { message: "unknown entity" } }];
    let rows = this.store[entity].slice();
    // filtering: any query key that is a stored field
    for (const [k, v] of Object.entries(query)) {
      if (["limit", "starting_after", "expand"].includes(k)) continue;
      if (v === "" || v == null) continue;
      rows = rows.filter((r) => String(r[k]) === String(v));
    }
    // cursor pagination
    const limit = Math.min(Math.max(parseInt(query.limit) || DEFAULT_LIMIT, 1), MAX_LIMIT);
    if (query.starting_after) {
      const ids = rows.map((r) => r.id);
      const i = ids.indexOf(query.starting_after);
      if (i >= 0) rows = rows.slice(i + 1);
    }
    const page = rows.slice(0, limit);
    return [200, { object: "list", data: page, has_more: rows.length > limit,
                   count: page.length, total: this.store[entity].length }];
  }

  get(entity, id, query = {}) {
    const rec = (this.store[entity] || []).find((r) => r.id === id);
    if (!rec) return [404, { error: { message: "Not found", type: "not_found" } }];
    const out = { ...rec };
    const want = String(query.expand || "").split(",");
    for (const f of Object.keys(out)) {
      const ent = this._refEntity(f);
      if (ent && want.includes(f) && out[f]) {
        out[f + "_obj"] = (this.store[ent] || []).find((r) => r.id === out[f]) || null;
      }
    }
    return [200, out];
  }

  update(entity, id, body = {}) {
    const rec = (this.store[entity] || []).find((r) => r.id === id);
    if (!rec) return [404, { error: { message: "Not found", type: "not_found" } }];
    for (const [k, v] of Object.entries(body)) {
      if (k !== "id" && k !== "createdAt") rec[k] = v;
    }
    rec.updatedAt = this._now();
    return [200, rec];
  }

  remove(entity, id) {
    const arr = this.store[entity] || [];
    const i = arr.findIndex((r) => r.id === id);
    if (i < 0) return [404, { error: { message: "Not found", type: "not_found" } }];
    arr.splice(i, 1);
    return [200, { id, deleted: true }];
  }

  // ── HTTP-style dispatch (the `api` capability) ───────────────────────────
  request(method, path, { query = {}, body = {} } = {}) {
    if (path === "/healthz") return [200, { status: "ok", actor: this.handle }];
    const m = path.match(/^\/v1\/([a-z0-9_]+)(?:\/([^/]+))?$/);
    if (!m) return [404, { error: { message: "no route", path } }];
    const entity = this.byPlural[m[1]];
    if (!entity) return [404, { error: { message: "unknown collection", collection: m[1] } }];
    const id = m[2];
    const mu = method.toUpperCase();
    if (!id) {
      if (mu === "POST") return this.create(entity, body);
      if (mu === "GET") return this.list(entity, query);
    } else {
      if (mu === "GET") return this.get(entity, id, query);
      if (mu === "POST" || mu === "PATCH") return this.update(entity, id, body);
      if (mu === "DELETE") return this.remove(entity, id);
    }
    return [405, { error: { message: "method not allowed", method } }];
  }

  // ── MCP-style dispatch (the `mcp` capability) ────────────────────────────
  listTools() {
    return (this.manifest.capabilities?.mcp?.tools || []).map((t) => t.name);
  }
  callTool(name, args = {}) {
    // tool names: create_<snake> / list_<snakeplural> / get_<snake> /
    //             update_<snake> / delete_<snake>
    const m = name.match(/^(create|list|get|update|delete)_(.+)$/);
    if (!m) return [400, { error: { message: "unknown tool", name } }];
    const [, op, rest] = m;
    const entity = this._entityForSnake(rest, op);
    if (!entity) return [404, { error: { message: "unknown entity for tool", name } }];
    if (op === "create") return this.create(entity, args);
    if (op === "list") return this.list(entity, args);
    if (op === "get") return this.get(entity, args.id, args);
    if (op === "update") { const { id, ...rest2 } = args; return this.update(entity, id, rest2); }
    if (op === "delete") return this.remove(entity, args.id);
    return [400, { error: { message: "bad op", op } }];
  }
  _entityForSnake(rest, op) {
    for (const e of this.entities) {
      if (op === "list") { if (snake(pluralize(e)) === rest) return e; }
      else if (snake(e) === rest) return e;
    }
    return null;
  }
}

export default KotobaActor;
