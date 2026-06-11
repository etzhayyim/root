# Finding: kotoba:kais/evm invoke-error — root cause is two kotoba-submodule bugs

**Date**: 2026-06-01 · **Context**: ADR-2605312100, Wave 1/2 ledger (11 invoke-error cells, all evm)

## Symptom
11 runnable chain/finance cells (yoro-supply {delivery_verify, manufacture_track, order_placement,
shipment, supplier_selection}, gov-municipality/permit_submission, …) build clean but fail invoke
on :8077: `InstantiateFailed(component imports kotoba:kais/evm@0.1.0 ... export eth-chain-id has
the wrong type ... function implementation is missing)`.

## Full root-cause chain (empirically established 2026-06-01)

1. **The WIT is NOT the problem.** `interface evm` (incl. `eth-chain-id: func(rpc-url: string) ->
   result<string,string>`) is BYTE-IDENTICAL between cbad341 (where evm read-surface landed) and the
   current submodule HEAD 918e8a7. Rebuilding an evm cell's wasm against cbad341's WIT (no
   wasi:http) and invoking it against the live :8077 STILL fails with the same "eth-chain-id wrong
   type". So neither the WIT version nor the later `wasi:http` world import is the cause.

2. **The deployed :8077 binary's host registration of `eth-chain-id` is the wrong type vs the WIT.**
   "wrong type" (not "missing") = the host provides an eth-chain-id whose wasmtime component
   signature does not match the WIT the guest is built against. The CURRENT source host.rs:863
   registers it correctly `(String,) -> Result<(Result<String,String>,)>`, so a binary rebuilt from
   current source WOULD fix it —

3. **— but the current-source binary does NOT start.** Built from 918e8a7 it blocks during
   `kotoba_kse::sovereign_key::load_block_durable`, retrying forever to fetch a wrapped-key block
   (`bafyrei…`) from Kubo IPFS (localhost:5001) instead of falling through to `genesis()`. :8077
   never binds. (The prior good binary `~/.local/bin/kotoba.bak-pre-evm` has the older
   fall-through-to-genesis behavior and starts fine.)

## Conclusion
Both blockers live in the **kotoba submodule**, not the migration:
- (a) host `eth-chain-id` registration must match the WIT (so guests link), AND
- (b) `SovereignCrypto::load_or_genesis` must fall through to genesis on a missing/unreachable
  durable block (so `kotoba serve` starts when IPFS lacks the key block).
The migration cannot unblock evm invoke-verification from its side. Needs a kotoba commit where the
binary BOTH starts AND registers the evm host funcs matching the WIT; then rebuild :8077 + the 11
cells' wasm from that commit and re-run invoke_equiv.

## State left (safe)
- :8077 rolled back to the working binary (`kotoba.bak-pre-evm`); health ok.
- kotoba submodule untouched (verification used temp WIT copies, never checked out).
- The 11 cells remain `invoke-error` (build-verified, runtime-blocked on the two kotoba bugs).
- Non-evm cells unaffected (Wave 1: 6/6 strict).
