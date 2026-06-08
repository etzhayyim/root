# Compact Rust WASM actor — raw single-block (browser-local tier)

Proves the **browser-local** tier of the kotoba-wasm runtime: a clean-room actor
compiled to a tiny (~2 KB) **raw single-block** WebAssembly module whose IPFS
CIDv1 is a valid `bafkrei…` (the worker's `isRawCidV1`), so it loads
browser-local via the ameno wasm-actor loader — no WASI, no host imports.

Contrast `../wasm/` (componentize-py): a full Python guest, ~18 MB, multi-block
→ dag-pb CID → donated-mesh tier. Two tiers, per ADR-2606014600.

## Build

```sh
./build.sh    # uses the rustup stable toolchain (has wasm32-unknown-unknown std)
```

## Verified (this build)

- `cargo build --release --target wasm32-unknown-unknown` → 2 026 bytes.
- `wasm-tools validate` → VALID; exports `alloc`, `actor_create`, `actor_count`,
  `actor_get_len`, `actor_delete`, `actor_healthz`, `memory`.
- raw CIDv1 `bafkreid4jbmgh4yhlbzqqadcearfthjczgke2rwv35shynecizeb4qlqda`
  (matches `isRawCidV1`) → browser-local tier.

The `.wasm` and `target/` are gitignored (build artifacts); `build-record.json`
records the evidence.
