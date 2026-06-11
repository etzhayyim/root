# chigiri-legal-aid-guest

Free legal-aid intake gate as a **kotoba WASM Component** — runs INSIDE the
kotoba node (`wasm32-wasip2`, WasmExecutor), not as a Cloudflare Worker.

Realises ADR-2605302200 / 2605302330 / 2605302345 server-side: the constitutional
gates are enforced in WASM, and on a valid intake the guest asserts a
`legalAidMatter` quad into the kotoba EAVT graph via the KQE host ABI.

## Gates (enforced in `evaluate_intake`)

- **G14** — the guest produces no advice; it only routes + asserts.
- **G15** — `zero_compensation` must be true; any consideration rejects.
- **G16** — an in-jurisdiction (`license == matter`) supervising counsel is
  required, and the jurisdiction must be `enabled` (AT / US-state are
  `verify-required` and rejected).

## Build

```sh
# Python guests are blocked on the current kotoba (wasmtime 22 / extended-const);
# the Rust guest path is live-verified (deps.toml). cargo-component required.
XDG_CONFIG_HOME=/tmp/xdg-empty cargo component build --release   # local-WIT, no registry
# → target/wasm32-wasip1/release/chigiri_legal_aid_guest.wasm  (~150 KB)
cargo test --release    # native gate-logic unit tests (5)
```

## Deploy / invoke

`scripts/deploy.py` base64-encodes the wasm + a CBOR InvokeContext and POSTs to
`com.etzhayyim.apps.kotoba.invoke.run` (program_type `wasm-node`) with an operator JWT
(`sub == operator_did`).

Live-verified on the local node (2026-05-30):

| intake | result |
|---|---|
| valid (jpn + jpn counsel + zero-comp) | `status=ok assert_count=1` → matter quad asserted (`counsel-assigned`) |
| G15 (zero_compensation=false) | `rejected assert_count=0` |
| G16 (Austria, verify-required) | `rejected assert_count=0` |
| G16 (no counsel) | `rejected assert_count=0` |

## Host ABI used

`kqe.assert-quad` (persist the matter), `kse.publish` (emit a
`chigiri/<graph>/legalAid/counsel-assigned` event), `auth.current-did`.
WIT world `kotoba-node` (`wit/world.wit`, copied from kotoba-guest).
