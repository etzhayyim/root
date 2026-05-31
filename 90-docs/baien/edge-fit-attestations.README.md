# `edge-fit-attestations.jsonl` — schema + protocol

Per ADR-2605241900 §"Enforcement Phase 2". This sidecar JSONL is the
ground truth for whether a model tagged `useCases: ["edge", "browser",
"cpu"]` in any `llm-model-registry*.ts` actually fits the edge ceiling.

The lefthook hook `70-tools/scripts/lint/baien-edge-fit-attestation.mjs`
fails any pre-commit that adds / modifies an edge-tagged registry
entry without a matching in-budget attestation row here.

## Schema

One JSON object per line. Order doesn't matter; the linter keeps the
**latest by `ts`** per `model_id`.

```jsonc
{
  "ts": "2026-05-24T01:00:00+00:00",                  // ISO-8601 UTC
  "model_id": "baien-bitnet-1.58bit-base",            // matches registry key
  "weights_packed_bytes": 838860800,                   // ≤ 1.6 GB (ADR-2605241900)
  "peak_ram_4k_bytes": 1968525312,                     // ≤ 2.0 GB
  "peak_ram_16k_bytes": 2147483648,                    // ≤ 2.5 GB
  "first_token_latency_ms_iphone14": 2800,             // ≤ 3000 ms
  "attesting_council_seat_did": "did:plc:founder-seat-1",
  "attesting_runtime": "bitnet.cpp 1.0 (cpu)",
  "attesting_session_chronicle": "https://github.com/etzhayyim/root/pull/268",
  "notes": "Measured on EVO-X2 + Mac mini fleet smoke harness; full method documented in chronicle."
}
```

## How to add a row

1. Run the deployment artifact (post-merge + post-quantization) on a
   real device (or representative emulator) and measure:
   - on-disk packed bytes (`du -b` of the artifact)
   - peak resident memory at 4 k and 16 k context inference
   - first-token latency on a recent iPhone (iPhone 14/A16 = baseline)
2. Append a row with all fields populated.
3. Commit; the lefthook hook will verify all ceilings pass.

## Ceilings (verbatim from ADR-2605241900 §Decision)

| field | ceiling |
|---|---|
| `weights_packed_bytes` | 1.6 GB |
| `peak_ram_4k_bytes` | 2.0 GB |
| `peak_ram_16k_bytes` | 2.5 GB |
| `first_token_latency_ms_iphone14` | 3 000 ms |

A row over any ceiling fails the hook. Fix by either:
- Re-quantizing / pruning the artifact to fit, OR
- Re-tagging it as `baien-server-*` / `baien-XL-*` (different
  `useCases`, no longer subject to this invariant).

## Bootstrap: today's baien (no attestation yet)

The current `baien-bitnet-1.58bit-base` entry in
`llm-model-registry.ts` was created **before** this enforcement
landed. Until the first real on-device attestation runs, the hook
treats the entry as a known-pending bootstrap (see hook source — TODO
add a `bootstrap_exempt` shortlist). After the first attestation lands,
the exemption is removed.
