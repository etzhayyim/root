---
id: adr-2606037000
title: "ADR-2606037000: Session close — kotoba coverage + security-hardening sweep (passkey/CACAO/Signal secrecy verified)"
status: active
doc_type: adr
topic: session-close-kotoba-coverage-security-hardening-sweep
authoritative: false
last_verified: 2026-06-03
priority: 4.0
axis: process
weight: 0.40
priority_note: "session-close record; verifies + hardens the secrecy design of ADR-2606014000/4500/5000"
authoritative_for: []
related:
  - adr-2606014000-kotoba-passkey-cacao-signal-secrecy
  - adr-2606014500-etzhayyim-auth-zero-access-proton-alignment
  - adr-2606015000-pds-refactor-onto-kotoba-server
  - adr-2605181100-mst-encrypted-records-signal-keywrap
  - adr-2605231525-no-server-key-invariant
  - adr-2605262130-kotoba-storage-substrate-unification
supersedes: []
superseded_by: []
depends_on:
  - ADR-2606014000 (passkey→ARK→CACAO/Signal secrecy design — this session verifies + hardens its substrate)
---

# ADR-2606037000: Session close — kotoba coverage + security-hardening sweep (passkey/CACAO/Signal secrecy verified)

**Date**: 2026-06-03
**Status**: ACTIVE (documentation-only session closure)
**Deciders**: Jun Kawasaki

## Context

The session opened with the `/goal` *"webauth, passkey を中心に kotoba server での暗号、秘匿化を設計. user 同士のメッセージでは signal. また kotoba は cacao, key なども踏まえて美しく設計に"* — answered by the passkey→ARK→HKDF key tree + CACAO delegation + DID↔Signal binding design (**ADR-2606014000**), the auth-worker zero-access alignment (**ADR-2606014500**), and the PDS-on-kotoba-server refactor (**ADR-2606015000**), all built pre-compaction.

The operator then drove a long `/loop coverage と成熟度を高めて` (≈65 iterations). The mandate was raising test coverage **and** maturity across the `40-engine/kotoba` substrate that those ADRs depend on. This ADR records the outcome and the residual design calls.

Submodule commit: `40-engine/kotoba @ be43e63` (branch `fix/datomic-startup-cache-warm`). Workspace state at close: **24 crates / 2443 lib tests / 0 failed.**

## Decision (what shipped)

### A. Security/correctness fixes (21)

**Parser/decoder DoS hardening** — every untrusted-input deserializer (network / IPFS / cloned-repo) was swept for three bug classes (alloc-from-untrusted-length, unbounded recursion/decompression, byte-slice-on-multibyte):

- `kotoba-core/frame`: varint payload-length overflow wrapped `end` → out-of-range slice **panic** → checked arithmetic.
- `kotoba-store/car_bundle`: `extract_block` offset overflow + `parse_index` mul/add overflow + `with_capacity(block_count)` OOM → checked + bounded.
- `kotoba-git/pack`: delta `dst_size` OOM cap (16 MiB) + **unbounded delta-chain recursion** stack-overflow (self-ref / cycle / long chain) → depth cap 64 + zlib **decompression-bomb** cap (1 GiB, pack + loose).
- `kotoba-kse/vault`: `reassemble` `total_size` OOM → 64 MiB pre-alloc cap.
- `kotoba-edn/parser`: deep-nesting recursive-descent stack-overflow → `MAX_DEPTH=1024` + `ParseError::TooDeep`.
- `kotoba-kqe/cypher` (hand-rolled parser — richest seam, 4 bugs): multibyte diagnostic-truncation panic; **`WHERE a.x != "y"` silently parsed as `= "y"` (filter inversion)**; `split_and` byte-cursor multibyte panic + AND-split-inside-quotes; `split_clause_after` `to_uppercase()` byte-offset desync (ligatures).
- `kotoba-ingest/ingest` Message-ID + `kotoba-vm/agent` observation/session-cid: multibyte byte-slice panics.

**Other correctness/security:**

- `kotoba-kse/sovereign_key`: a present-but-**corrupt** wrapped vault-key block silently re-genesised a new key → **orphaning all prior-encrypted data**. Now re-genesis fires **only** on a confirmed-missing block (`Ok(None)`); corruption/tampering/wrong-identity fail loud.
- `kotoba-dht/source_chain`: entry CID was a non-injective `Debug`-string concat that **omitted `agent` + `policy`** and could collide `(seq,ts)` → now canonical CBOR over all fields.
- `kotoba-auth`: CACAO `verify_skip_sig` max-age parity with `verify_inner`; `validate_did` rejects DID-URL delimiters `/ ? #` (storage-key namespace injection).
- `kotoba-crypto/key_tree`: Shamir `combine` rejects zero/duplicate share indices (was a silent wrong secret).
- `kotoba-server/pds_session`: opt-in PoP **audience binding** (`verify_session_pop_with_audience`) — closes cross-service replay; backward-compatible.

### B. Coverage (≈55 defining/safety-property tests)

Pinned the *characteristic* property of each component, not just happy paths: CACAO temporal + depth-2 attenuation + resolver fail-closed; EVM read surface (EIP-55 canonical addresses, all ERC-20/721/1155 selectors, ABI hostile-length decode, EIP-1271 exact-magic); Signal X3DH anti-MITM (incl. valid-sig-wrong-key) + binding tamper + ratchet skip-boundary; hybrid search (BM25 TF-saturation/length-norm, IVF == brute-force, PageRank authority-transitivity, RRF agreement-beats-strength); Datomic as-of/since timeline partition + cardinality-one accretion history-retention; CAR pack/extract arithmetic; budgeted-eviction + sync-window pin lifecycle; journal fallback payload fidelity; shelf bucket isolation; pre-key re-enrollment; WASM gas charge/floor; FP8 negative saturation; EDN escaping/malformed roundtrips.

## Consequences

- The secrecy substrate of ADR-2606014000/4500/5000 is now **verified end-to-end and hardened** against the deserialization-DoS surface a passkey-rooted, IPFS-backed, peer-federated system exposes.
- No public-API breaks; no constitutional invariants touched (no-server-key, Murakumo-only inference, Apache+Rider all intact). The `.solve()`/Council gates and R0 ceilings are untouched.

## Flagged for a future design decision (NOT changed — both migration-affecting)

1. **One-time-prekey consume-on-fetch** (`signal_xrpc::get_prekey_bundle` returns the bundle verbatim → OPK reuse weakens X3DH forward secrecy). Needs an OPK-pool + atomic-pop data model.
2. **`did_slug` width** (`agent_identity::did_slug` = `blake3(did)[..4]` = 32 bits is the sole namespace for per-agent vault keys; birthday collision ≈70% at 10K agents → vault-key namespace collision → data loss). Widening changes every storage key (migration).

## Verification

- `cargo test --workspace --lib` → 24 crates / 2443 / 0 failed.
- Per-fix regression tests would fail pre-fix (panic/OOM/wrong-result) and pass post-fix.
