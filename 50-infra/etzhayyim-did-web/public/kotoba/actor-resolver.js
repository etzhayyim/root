// actor-resolver.js — reusable, zero-dependency browser resolver for the
// `actors-v1` kotoba Datom log.
//
// Resolution is worker-independent and trustless (ADR-2605312345 / 2606015400 /
// 2606015600): it reads the content-addressed root pointer + ProllyTree blocks
// (from the apex static /kotoba route or ANY IPFS gateway), CID-verifies each
// block inside kotoba-wasm (ingestBlock), hydrates the EAVT tree, and answers
// actor + DID queries locally — no CF KV, no XRPC node, no server signature.
// Each DID document is self-verified by recomputing CID(:actor/didDocJson) and
// checking it equals the stored :actor/didDocCid, so the handle→DID binding
// holds with no TLS / no worker.
//
// Consumers (apex /search, yoro AgentProfile, @etzhayyim/ameno) do:
//   import { ActorResolver } from '/kotoba/actor-resolver.js';
//   const r = new ActorResolver();            // defaults to /kotoba on this origin
//   await r.init();
//   const { didDoc, verified } = await r.resolveDid('yadori');
//   const list = r.listActors();
//
// Options (all optional):
//   base        block/root/wasm base URL            (default '/kotoba')
//   graph       graph name                          (default 'actors-v1')
//   fetchImpl   fetch implementation                (default globalThis.fetch)
//   wasmModule  pre-imported kotoba_wasm module     (default: dynamic import)
//   subtle      WebCrypto SubtleCrypto              (default globalThis.crypto.subtle)

export class ActorResolver {
  constructor(opts = {}) {
    this.base = (opts.base ?? '/kotoba').replace(/\/$/, '');
    this.graph = opts.graph ?? 'actors-v1';
    this._fetch = opts.fetchImpl ?? globalThis.fetch?.bind(globalThis);
    this._wasmModule = opts.wasmModule ?? null;
    this._subtle = opts.subtle ?? globalThis.crypto?.subtle;
    this._node = null;
    this._ready = null;
    this.root = null;
    this.manifest = null;
  }

  /** Idempotent: fetch root → fetch+ingest (CID-verify) blocks → hydrate. */
  init() {
    if (!this._ready) this._ready = this._init();
    return this._ready;
  }

  async _init() {
    if (!this._fetch) throw new Error('actor-resolver: no fetch implementation');
    const wasm = this._wasmModule ?? (await import(`${this.base}/kotoba_wasm.js`));
    if (!this._wasmModule) {
      const bin = await (await this._fetch(`${this.base}/kotoba_wasm_bg.wasm`)).arrayBuffer();
      await wasm.default(bin);
    }
    const { KotobaNode } = wasm;
    this._node = new KotobaNode();

    const manifest = await (await this._fetch(`${this.base}/${this.graph}.root.json`)).json();
    this.manifest = manifest;
    this.root = manifest.root;
    for (const cid of manifest.blocks) {
      const bytes = new Uint8Array(
        await (await this._fetch(`${this.base}/blocks/${cid}`)).arrayBuffer(),
      );
      this._node.ingestBlock(cid, bytes); // throws if bytes don't hash to cid
    }
    const applied = this._node.hydrateFromProlly(this.root);
    if (!applied) throw new Error('actor-resolver: hydrate applied 0 datoms');
    return this;
  }

  // ── query helpers ──────────────────────────────────────────────────────────
  _q(queryEdn) {
    const out = JSON.parse(this._node.datomicQ(queryEdn, '[]'));
    return out.rows_edn || out.rows || [];
  }

  // Decode an EDN scalar as produced by datomicQ: strings come back quoted
  // ("\"yadori\""), keywords as ":kw", numbers/bools bare.
  static _unedn(s) {
    if (typeof s !== 'string') return s;
    if (s.startsWith('"')) {
      try {
        return JSON.parse(s);
      } catch {
        return s.slice(1, -1);
      }
    }
    return s;
  }

  static _esc(h) {
    return String(h).replace(/\\/g, '\\\\').replace(/"/g, '\\"');
  }

  /** All handles present in the log. */
  listHandles() {
    return this._q('{:find [?h] :where [[?e :actor/handle ?h]]}')
      .map((row) => ActorResolver._unedn(row[0]))
      .sort();
  }

  /** Full actor record (attribute map) for a handle, or null. */
  resolveRecord(handle) {
    const h = ActorResolver._esc(handle);
    const rows = this._q(
      `{:find [?a ?v] :where [[?e :actor/handle "${h}"] [?e ?a ?v]]}`,
    );
    if (!rows.length) return null;
    const rec = {};
    for (const [a, v] of rows) {
      const attr = ActorResolver._unedn(a).replace(/^:actor\//, '');
      let val = ActorResolver._unedn(v);
      if (attr.endsWith('Json')) {
        try {
          val = JSON.parse(val);
        } catch {
          /* keep raw */
        }
        rec[attr.replace(/Json$/, '')] = val;
      } else {
        rec[attr] = val;
      }
    }
    return rec;
  }

  /**
   * Resolve + SELF-VERIFY an actor's canonical DID document.
   * Returns { did, didDoc, cid, verified } — verified === true iff
   * CID(didDocJson bytes) === the stored :actor/didDocCid (content-addressed,
   * no TLS / no server).
   */
  async resolveDid(handle) {
    const rec = this.resolveRecord(handle);
    if (!rec || rec.didDocCid == null) return null;
    const canonical = rec.didDocJson; // already JSON.parsed → re-serialize? No:
    // resolveRecord JSON.parsed :actor/didDocJson into an object. For the CID we
    // need the EXACT canonical bytes, so re-read them raw from the datom instead.
    const rawRows = this._q(
      `{:find [?v] :where [[?e :actor/handle "${ActorResolver._esc(handle)}"] [?e :actor/didDocJson ?v]]}`,
    );
    const canonicalStr = ActorResolver._unedn(rawRows[0]?.[0]);
    const cid = await ActorResolver.cidV1Raw(canonicalStr, this._subtle);
    return {
      did: rec.did,
      didDoc: typeof canonical === 'object' ? canonical : JSON.parse(canonicalStr),
      cid: rec.didDocCid,
      verified: cid === rec.didDocCid,
    };
  }

  /** Lightweight list for /search & registry views. */
  listActors() {
    return this.listHandles()
      .map((h) => {
        const r = this.resolveRecord(h) || {};
        return {
          handle: r.handle,
          did: r.did,
          glyph: r.glyph,
          kind: r.kind,
          status: r.status,
          displayName: r.displayNameEn || r.displayNameJa || r.handle,
          description: r.description,
        };
      })
      .filter((a) => a.handle);
  }

  /** Substring search over handle / displayName / description (case-insensitive). */
  searchActors(query) {
    const q = String(query || '').toLowerCase();
    if (!q) return this.listActors();
    return this.listActors().filter((a) =>
      [a.handle, a.displayName, a.description].some((s) =>
        String(s || '').toLowerCase().includes(q),
      ),
    );
  }

  // CIDv1 (raw 0x55, sha2-256) of a UTF-8 string — matches cid.ts / publisher /
  // gen-kotoba-actor-blocks.mjs, so the recomputed CID equals the published one.
  static async cidV1Raw(str, subtle = globalThis.crypto?.subtle) {
    const bytes = new TextEncoder().encode(str);
    const digest = new Uint8Array(await subtle.digest('SHA-256', bytes));
    const prefixed = new Uint8Array(4 + digest.length);
    prefixed.set([0x01, 0x55, 0x12, 0x20], 0);
    prefixed.set(digest, 4);
    return 'b' + ActorResolver._base32(prefixed);
  }

  static _base32(bytes) {
    const A = 'abcdefghijklmnopqrstuvwxyz234567';
    let bits = 0,
      val = 0,
      out = '';
    for (const b of bytes) {
      val = (val << 8) | b;
      bits += 8;
      while (bits >= 5) {
        out += A[(val >>> (bits - 5)) & 31];
        bits -= 5;
      }
    }
    if (bits > 0) out += A[(val << (5 - bits)) & 31];
    return out;
  }
}

export default ActorResolver;
