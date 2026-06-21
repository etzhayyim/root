---
id: adr-2605181200-mst-encrypted-metadata-leak-reduction
title: "ADR-2605181200: Encrypted-record metadata-leak reduction — ciphertext padding + rkey blinding (Sealed Sender deferred)"
status: proposed
doc_type: adr
topic: mst-encrypted-metadata-leak-reduction
authoritative: true
last_verified: 2026-05-18
priority: 6.5
axis: architecture
weight: 0.65
priority_note: "Closes the two cheapest metadata leaks in ADR-2605181100 (ciphertext size, rkey path). Sealed Sender and timing/fan-out mitigations are larger and tracked separately."
authoritative_for:
  - "hard rule: encrypted record ciphertexts MUST be padded to a fixed bucket size when stored on PDS"
  - "bucket schedule: 1 KiB / 4 KiB / 16 KiB / 64 KiB → blob fallback at 256 KiB"
  - "hard rule: rkey blinding uses base32(BLAKE2b-128(symKey || seq))"
  - "SDK API: `pad` option on crypto.encrypt(), `blindRkey: true` on encryptedWriteStandalone"
depends_on:
  - adr-2605181100-mst-encrypted-records-signal-keywrap
related:
  - adr-2605172000-etzhayyim-kotoba-substrate
supersedes: []
superseded_by: []
---

# ADR-2605181200: Encrypted-record metadata-leak reduction — ciphertext padding + rkey blinding (Sealed Sender deferred)

**Status**: proposed
**Date**: 2026-05-18
**Deciders**: Jun Kawasaki

# Context

ADR-2605181100 introduced encrypted records on the AT Protocol substrate with explicit "metadata that this design does not solve":

1. **`collection/rkey` paths in plaintext.** MST keys are visible to anyone with PDS read access, leaking write order and any naming pattern the SDK chooses (e.g., timestamp-based TIDs reveal write timing precisely).
2. **Ciphertext size.** A 200-byte vote envelope and a 50 KB clinical-attachment proposal envelope are trivially distinguishable. Even within a single innerType the size distribution carries entropy.
3. **Sender DID on `keyWrap`.** Every keyWrap names its `sender`, exposing the social graph of who deliberates with whom.
4. **Write timestamps + fan-out shape.** PDS commit log reveals timing; the count of keyWraps per record reveals group size.

This ADR addresses (1) and (2) — the two leaks the SDK can fix unilaterally without infrastructure changes or libsignal-specific API depth.

(3) requires libsignal Sealed Sender (`UnidentifiedSenderMessageContent`), which is a non-trivial integration with its own trust model (server-side sender-cert authority). Deferred to a follow-up ADR after the council-flow reference impl matures.

(4) requires PDS-side changes (batch flush, decoy keyWraps) and/or Tor-routed PDS access. Out of scope for the SDK; tracked as infra ADR candidates.

# Decision

## Padding (ciphertext size leak)

All `com.etzhayyim.encrypted.record` ciphertexts MUST be padded before AEAD encryption such that the resulting ciphertext length lands in one of the bucket sizes:

| Bucket | Inline cap (ciphertext bytes) |
|---|---|
| 1 KiB  | 1024  |
| 4 KiB  | 4096  |
| 16 KiB | 16384 |
| 64 KiB | 65536 |
| blob   | (>64 KiB → out-of-line as `ciphertextBlob`, pinned to IPFS) |

Padding scheme: ISO/IEC 7816-4 (`0x80` followed by `0x00`s) applied to the plaintext CBOR before AEAD. The bucket is chosen as the smallest one accommodating `plaintext + 1 byte (delimiter) + AEAD-tag`. Decoding strips trailing `0x00`s and the `0x80` delimiter.

Properties:
- An adversary who can observe PDS storage learns only the bucket, not the exact body size.
- Bucket boundaries are constants so envelopes from different senders/innerTypes are size-indistinguishable within a bucket.
- The IPFS-pinned `ciphertextBlob` path inherits the same property at IPFS chunk granularity (256 KiB chunks).

Plaintext recovery is unambiguous: AEAD authenticates the padded plaintext, and the padding scheme is uniquely decodable. The envelope schema (lexicon) does not change — only the `ciphertext` field contents change shape.

## rkey blinding (write-order / naming leak)

rkeys for encrypted records and keyWraps MUST be derived as:

```
rkey = base32-lowercase( BLAKE2b-128( symKey || seq_u32_be ) )[0..13]
```

where:
- `symKey` is the 32-byte AEAD key for the envelope,
- `seq` is a per-key monotonically increasing 32-bit counter (starts at 0; +1 per envelope+keyWrap written under the same key),
- output is truncated to 13 base32-lowercase characters to match TID length so AT Proto's lexicon `key: "tid"` validator accepts it.

Properties:
- rkey carries no timestamp information (TID-based rkeys leak write time at sub-second resolution; blinded rkeys do not).
- Adversary without the symKey cannot link rkeys across envelopes from the same author.
- Adversary with the symKey (legitimate read-cap holder) can enumerate the sequence and detect missing rkeys (anti-tampering side-effect).

Trade-off: rkey is no longer time-sortable. Pagination falls back to PDS commit log ordering, which the substrate already exposes. Apps that need application-level ordering put a sequence number inside the encrypted plaintext.

## SDK surface

Both behaviors are **off by default in v0.1.x** and **on by default in v0.2.0**, with the staging window letting the council-flow reference impl exercise the unpadded path first and validate the rollout incrementally.

```typescript
// Padding
import { encrypt } from "@etzhayyim/sdk/crypto";
encrypt({key, sender, plaintext, pad: "bucket"});  // auto-bucket
encrypt({key, sender, plaintext, pad: "none"});    // explicit opt-out
encrypt({key, sender, plaintext, pad: {bucket: 4096}}); // explicit bucket

// rkey blinding (via the orchestration layer)
await encryptedWriteStandalone(deps, {
  innerType: "...",
  record: {...},
  recipients: [...],
  blindRkey: true,         // off in v0.1.x default, on in v0.2.0
});
```

Hard-rule (extends ADR-2605181100): in v0.2.0+, `pad: "none"` is permitted only with an explicit ESLint disable on a labeled test fixture. Production app code MUST NOT set `pad: "none"`.

# Consequences

## 正の効果

- **Size leak closed at PDS layer.** A passive PDS-storage observer sees five bucket sizes regardless of message content. The remaining leak is bucket-level (vote vs. small proposal vs. long proposal), which is acceptable for the council-flow threat model.
- **rkey time leak closed.** Write timing is still inferable from PDS commit log (separate concern), but the rkey itself no longer encodes a clock.
- **No new dependency.** BLAKE2b is already in `@noble/hashes`; ISO/IEC 7816-4 padding is a few lines.
- **Backward compatible.** Existing v0.1.0-alpha envelopes (no padding, TID rkeys) remain decryptable since the AEAD tag verifies the padded-or-not plaintext as authored.

## 負の効果 / コスト

- **Storage overhead.** Worst case for the 1 KiB bucket is ~1 KiB per record where the plaintext is ~1 byte. For chatty vote records (~100 bytes) the inflation is ~10×. At etzhayyim council scale this is negligible; for OpenMail it would matter (tracked there separately).
- **Loss of time-sortable rkeys.** Apps that previously relied on lexicographic TID order for pagination must add an explicit sequence field inside the plaintext.
- **Bucket migration risk.** If we add a new bucket size later (e.g., 256 bytes for vote-class records), pre-existing records still decode but new ones diverge in bucket distribution from old ones. Mitigation: pad to nearest *existing* bucket forever; new buckets are additive at the small end.
- **Sequence counter coordination.** rkey blinding requires the sender to know its current `seq` for the symKey. The simplest implementation is per-symKey ephemeral state in memory; the sender re-derives `seq` by enumerating PDS records under that symKey on startup. For one-symKey-per-envelope (current SDK), `seq` is always 0; the value only varies if a single symKey serves multiple envelopes (channel-rekey future work in P4).

## Rollout

1. **This commit** — ADR + crypto.ts `pad` option + encrypted.ts `blindRkey` option + unit tests + integration test variant exercising both.
2. **Council-flow soak (v0.1.x)** — opt-in via flags on the reference impl. Validate decode round-trip and look for size-cardinality regressions.
3. **v0.2.0 default-on** — flip the defaults, add the lint hard-rule for `pad: "none"`.
4. **Sealed Sender follow-up ADR** — when (3) lands.
5. **PDS-infra mitigations follow-up ADR** — batch flush + decoy keyWraps + onion access.

# Alternatives Considered

## A. CTBR (Constant-Time-Bandwidth-Ratio) padding

Pad to constant bytes per second over the session. Hides write timing too, not just size. Rejected because it requires a persistent sender process and a chunked-record model; not aligned with one-shot envelope writes on PDS.

## B. PURB (Padded Uniform Random Blob) — Nikitin et al.

Cryptographically uniform padding that masks even the algorithm identifier. Stronger than buckets. Rejected for v1 because the existing envelope schema commits `alg` in cleartext; switching to PURB requires breaking the envelope shape and losing the verify-cap clarity ADR-2605181100 explicitly relies on. Re-evaluate when an envelope v2 lands.

## C. Always-blob (every ciphertext goes out-of-line to IPFS)

Eliminates inline-size leak entirely; PDS sees only fixed-shape AT Records with a blob CID. Rejected because IPFS pinning latency + the operational burden of pinning all council deliberation is high; buckets give 90% of the property at 10% of the cost.

## D. Hashed rkey without symKey (e.g., `hash(sender, createdAt)`)

Hides the writes-from-the-same-key linkage but allows an adversary to test rkey candidates (creation-time guessing). The symKey-based blinding makes the rkey unforgeable without the read-cap. Rejected as weaker.

## E. Random rkey (`randomBytes(13)`)

Simplest possible blinding. Rejected because legitimate read-cap holders cannot enumerate / verify rkey sequence; missing rkey detection is lost.

# References

- ADR-2605181100 [MST encrypted records + Signal key-wrap](./2605181100-mst-encrypted-records-signal-keywrap.md) — design this ADR refines
- ADR-2605172000 [etzhayyim/root kotoba substrate](./2605172000-etzhayyim-kotoba-substrate.md)
- ISO/IEC 7816-4 padding — used in CMS / TLS 1.3 records
- BLAKE2b — RFC 7693
- Sealed Sender (Signal) — https://signal.org/blog/sealed-sender/ (deferred follow-up)
- PURB — Nikitin et al., "Reducing Metadata Leakage from Encrypted Files and Communication with PURBs" https://arxiv.org/abs/1806.03160
