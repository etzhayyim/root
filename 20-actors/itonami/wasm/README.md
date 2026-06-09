# itonami 営み — kotoba pywasm actor (componentize-py)

Design for running itonami's operations analyzer as a **kotoba pywasm actor** under the
"one Worker, many WASM actors" model (ADR-2606014500 / 2606014600), identical in shape to
asobi / inochi. The only first-party Cloudflare Worker is `etzhayyim.com`; the actor is a
**content-addressed WASM component** fetched from IPFS and run **locally** (browser via
ameno, or the donated mesh via e7m-wasm-runner) — **no per-actor server** (no-server-key).

## Why pywasm fits itonami

itonami's methods are **pure-stdlib Python (no numpy)** — the OEE/energy/quality maths is a
plain aggregation over scan-cycle ticks — so they compile to a WASM Component via
**componentize-py**. The same code runs as a CLI cell on a mesh node and in-WASM in the
browser with zero server trust (the reader recomputes the component CID and compares it to
the DID-doc CID before executing). This matters for **G1**: a read-only WASM component
*cannot* actuate the OT bus — the no-actuation invariant is enforced by construction.

## Component ABI (WIT sketch)

```wit
package etzhayyim:itonami@0.1.0;

world itonami-actor {
  /// one-screen brain view: line OEE + bottleneck + top alert + drift + attend-first line (JSON)
  export summary: func() -> string;
  /// per-station + line OEE/energy/quality + routed findings (JSON)
  export analyze: func() -> string;
  /// fused daily digest + Murakumo narration (G7) (JSON)
  export digest: func() -> string;
  /// graded threshold alerts — advisory only, never actuates (G1) (JSON)
  export alert: func() -> string;
  /// multi-line plant rollup + attention ranking (JSON)
  export fleet: func() -> string;
  /// canonical EAVT Datom log (durable ground state) as EDN text
  export datoms: func(tx: u32) -> string;
}
```

`methods/actor.py` is the single entrypoint that wires the nine cells into these export
bodies; the embedded seeds are bundled read-only (no filesystem, no network, no OT bus at
runtime). `python3 methods/actor.py <summary|analyze|digest|alert|fleet|datoms>` exercises the
same surface from the CLI.

## Build & verify (target)

```bash
componentize-py -w itonami-actor componentize methods -o dist/itonami.wasm
ipfs add --cid-version=1 --raw-leaves dist/itonami.wasm > dist/itonami.cid
node ../../tsumugi/wasm/loader/verify.mjs dist/itonami.wasm   # reuse headless CID-verify path
```

## Trust model

- **No server key.** Read-only component; never signs, never actuates.
- **Integrity before execution.** ameno / e7m refuse on CID mismatch.
- **G1/G2 hold in WASM too.** The component contains no write-back path and no worker
  dimension; it cannot surface or do what it does not contain.

## Status

R0 design-only. Methods are pywasm-ready (pure stdlib, 10 tests green); the componentize-py
build + CID advertisement land with the actor's first WASM deploy wave (gated like asobi).
Live scan-cycle ingest from a kotoba-os `plc-host-runner` Datom stream is G6/Council-gated.
