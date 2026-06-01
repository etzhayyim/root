# Finding: kotoba:kais/evm invoke-error — blocked by kotoba-submodule inconsistency

**Date**: 2026-06-01 · **Context**: ADR-2605312100, Wave 1/2 ledger (11 invoke-error cells, all evm)

## Symptom
The 11 runnable chain/finance cells (yoro-supply {delivery_verify, manufacture_track,
order_placement, shipment, supplier_selection}, gov-municipality/permit_submission, …) build
clean but fail invoke on :8077:
`InstantiateFailed(component imports kotoba:kais/evm@0.1.0 ... export eth-chain-id has the
wrong type ... function implementation is missing)`.

## Investigation
- WIT `crates/kotoba-runtime/wit/world.wit`: `interface evm { eth-chain-id: func(rpc-url: string) -> result<string, string>; ... }` and the `kotoba-node` world `import evm;` (line 209).
- Host `crates/kotoba-runtime/src/host.rs:863`: registers `eth-chain-id` as `(String,) -> Result<(Result<String,String>,)>` — MATCHES the WIT. Source is self-consistent.
- The evm read surface was added in kotoba commit `cbad341` (2026-05-30, "EVM read + verify surface").
- So the deployed :8077 binary's evm interface SKEWED vs the WIT the wasm components were built against.

## The real blocker (discovered 2026-06-01)
Rebuilding binary+wasm from the CURRENT submodule HEAD (918e8a7) does NOT work:
1. The binary built from 918e8a7 does NOT start — :8077 returned no health; rolled back to the prior working binary (`~/.local/bin/kotoba.bak-pre-evm`).
2. 918e8a7's `world.wit` adds `import wasi:http/outgoing-handler@0.2.0` (line 210) which `componentize-py` (build-pywasm.sh) cannot satisfy — wasm builds fail.

=> The submodule advanced (concurrent work) into a state where neither the binary nor the
componentize-py wasm build is usable for migration. evm invoke-verification cannot be unblocked
by a naive rebuild.

## Required fix (coordination, not a one-shot rebuild)
Align the kotoba submodule to a single commit where ALL hold simultaneously:
- host evm impl signature == world.wit evm interface (so guests link), AND
- `kotoba serve` binary starts cleanly (health ok), AND
- `componentize-py` can build against world.wit (no unsatisfiable `wasi:http` import, or the
  toolchain/WIT is updated to handle it).
Then rebuild :8077 + rebuild the 11 cells' wasm from that same commit and re-run invoke_equiv.

## State left
- :8077 ROLLED BACK to the working binary (kotoba.bak-pre-evm); health ok.
- The 11 cells remain `invoke-error` in the ledger (build-verified, runtime-blocked on evm skew).
- Non-evm cells unaffected (Wave 1: 6/6 strict).
