# wasm-sbom — SBOM for kotoba-deployed WASM actors

Attaches a **CycloneDX 1.5 SBOM** to a WASM actor deployed to a kotoba node,
**bound to the wasm's kotoba program CID**. Per
[ADR-2606036000](../../../90-docs/adr/2606036000-wasm-actor-sbom-attestation-on-kotoba-deploy.md).

## Why

A WASM actor on a kotoba node is content-addressed by its **program CID** =
`KotobaCid::from_bytes(wasm)` → `to_multibase()` (CIDv1 dag-cbor sha2-256,
[`cid.rs`](../../../40-engine/kotoba/crates/kotoba-core/src/cid.rs)). The
`invoke.run` / `block.put` path records **what** the binary is (CID), **who**
deployed it (`agent_did`), and — with a did.json attestation — that it is
**authentic**. None of that says **what it is made of**. This tool closes that
gap so the wasm supply chain is first-class, queryable, and CVE-matchable in the
EAVT log — the same treatment the giemon *hardware* SBOMs already get
([ADR-2605312330](../../../90-docs/adr/2605312330-giemon-part-graph-sbom-kotoba-fleet-cve-svelte.md)).

## What it emits

```
<stem>.wasm.cdx.json          portable CycloneDX 1.5 (ships next to the binary /
                              pinnable to IPFS); metadata.component = the wasm,
                              keyed by the program CID; components = deps
<stem>.wasm.sbom.ingest.json  kotoba kg.ingest_batch body:
                                WasmActorImage  (id = program CID)
                                SbomComponent×N (id = purl) --wasm/componentOf--> image
```

The generator recomputes the **exact** kotoba program CID from the built wasm
(verified against an independent RFC4648 base32 encoder in the tests), so the
SBOM is keyed by the same identity the server stores.

## Usage

Python / componentize-py actors (sumitsubo, okaimono, …):

```sh
python3 wasm_sbom_gen.py --wasm py/agent.wasm --actor sumitsubo \
  --world kotoba-actor --requirements py/requirements.txt \
  [--freeze py/requirements.lock] [--built-by componentize-py@0.23.0]
```

Rust actors built with `cargo cyclonedx` (tsumugi, kanae, …) — re-key the
cargo SBOM by the program CID:

```sh
cargo cyclonedx --format json          # → <crate>.cdx.json
python3 wasm_sbom_gen.py --wasm target/wasm32-wasi/release/tsumugi.wasm \
  --actor tsumugi --from-cdx tsumugi.cdx.json
```

Ingest (operator-gated — no-server-key posture, the body is written by the
operator session, never a platform key):

```sh
curl -fsS -XPOST "$KOTOBA_URL/xrpc/com.etzhayyim.apps.kotobase.kg.ingest_batch" \
  -H "Authorization: Bearer $KOTOBA_TOKEN" -H 'Content-Type: application/json' \
  --data @py/agent.wasm.sbom.ingest.json
```

`orgs/etzhayyim/com-etzhayyim-sumitsubo/kotoba/deploy.edn` records the
operator-gated deployment and SBOM requirement; an operator implementation runs the above after
the `componentize-py` build (ingest only when `KOTOBA_TOKEN` is set).

## Honesty (version provenance)

Each pypi component records `wasm:versionSource`:

| value | meaning |
|---|---|
| `lock` | resolved from `--freeze` (a real lock) — pair with `--sourcing authoritative` |
| `pin` | `==x.y.z` in requirements |
| `constraint` | `>=x.y` — the purl uses the **lower bound**, NOT a resolved version |
| `unspecified` | no version given |

For a fully authoritative SBOM, generate `--freeze` from the build venv
(`pip freeze`) so every dep is `lock`-sourced.

## Vuln-match (no new tooling)

Component entities carry `cdx/purl`, the join key the existing matcher scans, so:

```sh
python3 ../sbom/purl_vuln_match.py <jwt> "$KOTOBA_URL"
```

matches a deployed wasm's dependencies against ingested CVEs and materializes
`VulnMatch` entities — identical to the giemon flow.

## Tests

```sh
python3 test_wasm_sbom_gen.py   # 7/7: CID parity (independent base32), shape, binding, rust path
```

Vocabulary SSoT: [`00-contracts/schemas/wasm-sbom.kotoba.edn`](../../../00-contracts/schemas/wasm-sbom.kotoba.edn).
stdlib-only (runs on the edge); Murakumo-only / no-server-key compatible.
