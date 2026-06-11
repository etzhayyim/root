---
id: ameno-browser-inference-platform
title: Ameno — browser-local LLM inference as murakumo Tier 2 crowd-source
status: active
doc_type: adr
topic: browser-inference
authoritative: true
last_verified: 2026-05-15
authoritative_for:
  - ameno-browser-inference
  - ameno-saveresult-persist-contract
  - ameno-subscribebriefs-firehose-contract
  - ameno-signal-v1-field-encryption
  - ameno-tier2-credit-event-contract
related:
  - adr-2604261936-ipfs-self-hosted-vultr-b2
  - adr-2604291630
  - adr-2605091700-nats-jetstream-as-mycorrhizal-substrate
  - adr-2605092350-baien-1bit-multimodal-edge-browser-cpu-design
  - adr-2605111200-cf-worker-edge-only-no-rw-connection
  - 0018-pii-tier3-cohort-first
  - 0095-simplified-3layer-identity-rw-vault
supersedes: []
superseded_by: []
---

# Context

The platform mapped IPFS (`ipfs.etzhayyim.com`), NATS JetStream firehose
bridging, and a BitNet-tier model strategy in 2026-04 / 05, but had no
**actor** that closes the "browser-edge WASM inference + post +
distributed processing" loop end-to-end. `yoro` runs Gemma E2B for
guest chat (ADR 2604291630), but it never persists, never credits, and
does not subscribe to the firehose. The Baien browser path (ADR
2605092350) was designed but unplumbed.

External question that triggered this work: "atproto.etzhayyim.com は ipfs
にデータ保存している? nats を firehose に使っている? この atproto
record / xrpc であれば browser edge で wasm で推論と post, 分散型処理が
可能?" The answer needed to be **yes**, with code on disk.

# Decision

Promote `ameno.etzhayyim.com` from a stub Svelte scaffold (engine package only)
to a full L3 dispatcher actor that:

- Runs Gemma 4 E2B / E4B (WebGPU) **and** Baien BitNet b1.58 2B
  (WASM ternary) entirely in the browser tab.
- Persists every inference via the standard ADR-2605111200 path
  (`ameno.etzhayyim.com` Worker → `atproto.etzhayyim.com` PDS → `bpmn-dispatcher` →
  `ameno-langserver` pod → `INSERT vertex_ameno_inferenceresult`).
  No `createKyselyDb()` in the Worker; pod-side asyncpg + SQLAlchemy
  Core only.
- Subscribes to the existing NATS firehose (`pds.repo.commit.app_bsky_feed_post`,
  ADR-2605091700) over an SSE stream surfaced as
  `com.etzhayyim.apps.ameno.subscribeBriefs`, then auto-responds per brief
  with local inference → `saveResult`.
- Encrypts private outputs client-side with WebCrypto AES-GCM under the
  `signal:v1:{ciphertext}` field convention; the server never sees the
  plaintext.
- Credits each `saveResult` to the actor's Tier 2 wallet via
  `vertex_credits_af_event` (write) and surfaces the running balance via
  `mv_ameno_credits_balance` + `com.etzhayyim.apps.ameno.listMyCredits` (read).

## Lexicon surface (XRPC, all `com.etzhayyim.apps.ameno.*`)

| NSID | Type | Persist target | Owner |
|---|---|---|---|
| `listModels` | query | none (static catalog) | Worker |
| `cardHome` | query | none (static card) | Worker |
| `saveResult` | procedure | `vertex_ameno_inferenceresult` + `vertex_credits_af_event` | langserver pod |
| `listHistory` | query | `vertex_ameno_inferenceresult` | langserver pod |
| `inferenceResult` | record | (federable AT Record schema) | — |
| `subscribeBriefs` | query (SSE) | NATS → no persist | langserver pod |
| `listActorAdapters` | query | `vertex_lora_adapter` | langserver pod |
| `listMyCredits` | query | `mv_ameno_credits_balance` | langserver pod |

The Worker handles `listModels` and `cardHome` locally (pure compute);
everything else routes via `routing-table.ts` NSID_EXACT_MATCH_TABLE to
`BPMN_URL`. The dispatcher then forks SSE (`_proxy_to_lg_pod_sse`) vs
buffered (`_proxy_to_lg_pod`) per NSID.

## Persistence target

`vertex_ameno_inferenceresult` carries the lexicon's typed columns plus
the ADR-0095 RLS quartet (`actor_did`, `org_did`, `at_did`, `created_at`).
`vertex_credits_af_event` (existing) gets one row per saveResult with
`event_type='ameno_browser_inference'`, `vertex_id=af://credits/{user}/{result}`,
deterministic so the AF log replays cleanly. `mv_ameno_credits_balance`
aggregates `SUM(amount)/COUNT/MAX(ts_ms)` by `user_id` for O(1) reads.

## Browser-side model selection

`MODELS` map in `40-engine/llm/inference/ameno/src/inference.ts` is the
SSoT for engine ids; the worker `MODEL_CATALOG`, the lexicon listModels
output, and `_KNOWN_MODELS` in the server handler all mirror it.
`InferenceDevice = "webgpu" | "wasm"` and `WASM_PREFERRED_MODELS` route
Baien to the WASM execution provider automatically; capability probe
auto-selects Baien when `navigator.gpu` is absent.

## Field encryption (signal:v1)

Phase 5b WebCrypto helper (`svelte/src/lib/private-vault.ts`) generates a
random 256-bit key per origin and stores it in localStorage as base64.
`encryptText(plain) → "signal:v1:<base64(iv12 || ct || tag16)>"` is
idempotent on the prefix; `decryptText` is the inverse. Server treats
the field as opaque varchar; `listHistory` returns ciphertext verbatim
and the client decrypts on display. Loss of localStorage = lost data;
this is the documented MVP failure mode pending a real Vault wrap.

# Consequences

- The original question is answered yes with code on `260512-agent-loop-main`:
  IPFS is a mirror not the primary store; NATS is the internal
  mycorrhizal substrate (public firehose remains AT Protocol SSE);
  browser-edge inference + post + distributed processing all run today.
- ameno becomes the reference implementation for any future
  "browser-local LLM with persist + credit" actor. The pattern is:
  Lexicon × N → Worker (edge proxy, no DB) → routing-table.ts →
  bpmn-dispatcher → `*-langserver` pod (kotodama.worker_api +
  per-actor handlers) → vertex / AF event tables.
- WebGPU LoRA weight merge is **wired but not applied** (selected
  adapter ids are recorded in `saveResult.loraAdapters` but the
  transformers.js internal `Float32Array` weights are not modified).
  Per-actor inference quality currently matches the base model. The
  follow-up phase will integrate with transformers.js's tensor API.
- The Phase 2 `vertex_ameno_inferenceresult` migration originally
  landed under the legacy Kysely directory; Phase 5i added the
  Alembic counterpart and the Kysely file is now a SUPERSEDED lineage
  archive.
- ameno-langserver inherits the `kotodama` image (no per-actor pod
  image), so any kotodama bump touches every Tier 2 actor at once.
  Acceptable tradeoff while the pod count stays small.

# Open follow-ups

- Per-actor LoRA weight merge against transformers.js internals.
- Vault-wrapped device key in place of the localStorage AES key.
- Listen-side mass smoke / load test (the smoke script covers
  correctness, not throughput).
- Generated lexicon bundle (`lexicon-registry.gen.ts` etc.) commit
  cycle — currently deferred to converge with parallel WIP from
  other actors.
- Replicate the ameno pattern to a second actor as a template
  exercise (Phase 6 candidate).
