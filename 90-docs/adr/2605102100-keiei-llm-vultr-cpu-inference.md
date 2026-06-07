---
id: adr-2605102100-keiei-llm-vultr-cpu-inference
title: "keiei LSP LLM resolution on Vultr CPU pod (gemma-4-E2B-it)"
status: superseded
doc_type: adr
topic: keiei-llm-vultr-cpu
authoritative: true
last_verified: 2026-05-14
superseded_by:
  - adr-2605211000
authoritative: false
authoritative_for:
  - keiei (経営) C-suite LSP daemon LLM endpoint
  - google/gemma-4-E2B-it CPU inference deployment shape
  - bearer secret + Keychain mirror flow for the keiei daemon
related:
  - adr-2605101200-ai-cxo-roles-lsp-resident
  - adr-2604231828-appview-domain-separation-bsky-etzhayyim-ai
  - adr-2605010000
  - adr-0036-worker-direct-hyperdrive-persistence
  - adr-2605141500-shinshi-review-generation-quality-loop
---

# ADR 2605102100 — keiei LSP LLM resolution on Vultr CPU pod (gemma-4-E2B-it)

Status: **Proposed** (2026-05-10, iter129).
Operating Entity: etzhayyim (sole principal).
Vendor: etzhayyim Japan株式会社 (engineering capacity).
Author: etzhayyim Claude Agent on behalf of CEO 河崎.

## 1. Decision

The keiei (経営) resident LSP daemon (ADR 2605101200) resolves its LLM
calls through a **dedicated Vultr VKE CPU inference pod** running
`google/gemma-4-E2B-it` (Q4_K_M GGUF, ~1.5 GiB) under
**llama.cpp's OpenAI-compatible HTTP server**. Public surface is
`https://gemma-e2b.etzhayyim.com` via Cloudflare Tunnel; in-cluster surface is
the ClusterIP `keiei-llm.keiei-llm.svc.cluster.local:8080`.

The macOS launchd daemon (`com.etzhayyim.keiei`) is wired through a small
shell wrapper that loads the bearer from macOS Keychain
(`etzhayyim.keiei / LLM_BEARER`) at process start; the secret never lives in
the world-readable `~/Library/LaunchAgents/com.etzhayyim.keiei.plist`.

## 2. Why CPU, not GPU

| Property | Vultr CPU (this ADR) | RunPod GPU (ADR-2605010000) |
|---|---|---|
| Hardware | shares `vhf-16c-58gb × 2` (existing) | RTX 6000 Ada, 48 GB |
| Marginal cost | ~$1/mo (10 GiB PVC) | $554 pod + $17.50 volume = $571.50/mo |
| Idle cost | $0 (warm in-memory weights) | $0.77/hr metered |
| Cold start | ~30 s (mmap GGUF) | ~2-3 min (vLLM warm) |
| Latency, ctx=8192 | ~1-2 s/request | ~0.2-0.5 s/request |
| Throughput cap | ~1 req/s sustained | 10-20+ req/s |
| Failure surface | Vultr pod restart | RunPod pod recycle / region drift |

The keiei daemon's call rate is **a few requests per minute** (one per
CXO decision, plus light review traffic), latency budget
`KEIEI_LLM_TIMEOUT_SEC=20`. CPU comfortably fits inside that envelope at
~30× lower marginal cost than reusing the GPU path.

GPU returns when (a) sustained load exceeds 1 req/s, or (b) the daemon
graduates to multimodal CXO review (vision over screenshots / PDFs).
Until then, CPU is the right tier.

## 3. Why a dedicated pod

`60-apps/etzhayyim-project-murakumo/litellm/` (mac mini fleet at
`https://llm.etzhayyim.com`) is the platform's general-purpose LLM gateway.
Reasons it's not used here:

- **Auth boundary** — the keiei daemon is the *only* caller for the AI
  CXO graph; sharing the murakumo gateway would force murakumo to
  understand the keiei bearer flow. A dedicated pod keeps each gateway
  responsible for one principal class.
- **Failure isolation** — murakumo serves dozens of consumers
  (heartbeat / shinka / general / extraction). A noisy neighbor stalling
  the gateway should not hold up CXO decisions; conversely, a runaway
  CXO loop should not stall heartbeat traffic.
- **Auditability** — the keiei layer's institutional discipline
  (`[rationale={source}]` audit marker on every ledger row) requires
  knowing which physical endpoint answered. A dedicated pod is one
  unambiguous endpoint.

The Vultr-pool / cloudflared / Keychain pattern mirrors the existing
`embedder-tunnel.yaml` deployment exactly, so this ADR introduces no
new operational shape — only a new instance of an established pattern.

## 4. Component layout

```
macOS launchd com.etzhayyim.keiei  (PID alive, KeepAlive=true)
  └─ /bin/zsh -c keiei-launchd-wrapper.sh
       ├─ security find-generic-password -s etzhayyim.keiei -a LLM_BEARER → etzhayyim_LLM_API_KEY
       ├─ export etzhayyim_LLM_URL=https://gemma-e2b.etzhayyim.com/v1/chat/completions
       ├─ export KEIEI_LLM_MODEL=gemma-4-E2B-it
       └─ exec python3 -m pymagatama.keiei --socket ~/Library/Caches/keiei.sock
            ↓
        pymagatama.keiei.graph._llm.call_llm()    (lazy import, only when gate allows)
            ↓ HTTPS POST (Authorization: Bearer)
        gemma-e2b.etzhayyim.com
            ↓ QUIC tunnel (cloudflared-keiei-llm × 2 replicas)
        keiei-llm Service :8080  (ClusterIP)
            ↓
        llama-server pod
          --model /model/gemma-4-E2B-it-Q4_K_M.gguf
          --ctx-size 8192 --parallel 2 --threads 6 --threads-batch 8
          --api-key-file /etc/keiei-llm/auth/bearer
          ↓ mmap
        /model PVC (10 GiB ReadWriteOnce, populated by initContainer)
```

## 5. Hard rules

1. **Bearer never in plist.** The plist only references the wrapper
   script; the wrapper reads from Keychain and exports into the child
   environment. Re-keying = `security add-generic-password -s etzhayyim.keiei
   -a LLM_BEARER -w <new>` + `launchctl unload && load`. The kubectl
   Secret `keiei-llm-auth` and the Keychain entry MUST stay in sync.
2. **HF token never in plist.** The model fetch initContainer reads
   `HF_TOKEN` from the kubectl Secret `keiei-llm-hf-token`, which is
   seeded once from macOS Keychain (`etzhayyim.huggingface / HF_TOKEN`). If
   HF rotates the token, rotate Keychain → recreate the Secret →
   restart the pod (or wait for a new pod cycle).
3. **PVC retention.** The 10 GiB `keiei-llm-model` PVC persists across
   pod restarts. The initContainer is idempotent — it skips the
   download when `${TARGET}` is already non-empty. To force a refresh
   (new quant, new model version), `kubectl delete pvc keiei-llm-model`
   and let the next pod re-create.
4. **Recreate strategy, not rolling.** Rolling would briefly run two
   `llama-server` pods, each holding ~1.6 GiB resident memory, doubling
   the memory footprint on the node. Recreate accepts ~30 s of downtime
   in exchange for a stable memory profile.
5. **Daemon graceful degradation is non-optional.** When the pod or
   tunnel is unreachable, `_llm.py` returns
   `("…", "fallback-error:URLError")` so the daemon stays useful and
   the ledger row gets `[rationale=fallback-error:URLError]`. **Do not**
   add a hard-fail path that kills the daemon on LLM error — institutional
   discipline (every Class A still escalates, every Class B/C still
   logs) outweighs prompt quality.
6. **Audit marker is non-optional.** `lsp_server._decide` MUST append
   `[rationale={source}]` to the ledger row's `artefact` column when
   `rationaleSource != "llm"`. Auditors must be able to distinguish
   real LLM rationales from deterministic stubs without re-reading
   every JSON-RPC payload.

## 6. Migration path

| Phase | Scope | Status |
|---|---|---|
| 0 | ADR + Helm chart + tunnel manifest + daemon rewire | **done** (iter129) |
| 1 | Operator runs `cloudflared tunnel create` + `helm upgrade --install` + 2 secrets + `tunnel route dns` + Keychain seed + `launchctl unload && load` | **pending** (~10 min, RUNBOOK §1) |
| 2 | Verify `rationaleSource=llm` on next CTO decision; backfill or stop the trailing `[rationale=fallback-no-key]` ledger rows | depends on Phase 1 |
| 3 | HPA + multi-replica when sustained load >1 req/s, or graduation to a quant tier (Q5_K_M ~2 GiB) for quality | future |
| 4 | Multimodal CXO review (vision over PDFs / screenshots) — would justify GPU pod return | future |

## 7. Cost & sizing

- llama-server resources: requests 2c/4Gi, limits 4c/8Gi. Q4_K_M
  weights ≈ 1.5 GiB; KV cache at ctx=8192 ≈ 1.6 GiB; OS + buffers ≈
  0.4 GiB; total ≈ 3.5 GiB resident — comfortably inside the 4 GiB
  request, well under the 8 GiB limit.
- PVC: 10 GiB at the cluster's default storage class. Holds the GGUF
  plus headroom for one rollback quant + tokenizer artefacts.
- Cloudflare Tunnel: free tier; 2 cloudflared replicas at 50m CPU /
  64Mi RAM each.
- **Marginal monthly cost: ~$1** (PVC). Pod fits in the existing
  `vhf-16c-58gb × 2` nodepool headroom (Kotoba/Datomic compute uses
  ~24 GiB/pod; ~10 GiB/node remains free).

## 8. Anti-goals (explicit)

- **Not a replacement** for murakumo / litellm. Those gateways serve
  general application traffic (heartbeat, shinka, ingest); this pod
  serves only the keiei layer.
- **Not a public LLM API.** `gemma-e2b.etzhayyim.com` is bearer-gated; the
  bearer rotates at operator discretion. Do not document the endpoint
  externally; do not create an ingress without a bearer requirement.
- **Not a quality replacement** for larger models. gemma-4-E2B is
  small. CXO rationales will be terser and occasionally weaker than
  what `qwen3-30b` would emit. The trade-off (cost, latency, isolation)
  is intentional; quality returns when the daemon graduates to GPU.
- **Not a place to add unrelated workloads.** The pool is named
  `keiei-llm-pool` and lives in the `keiei-llm` namespace specifically
  to discourage other teams from co-locating. New LLM workloads go in
  their own pool.

## 9. Failure modes (operational)

See `50-infra/vultr/keiei-llm-pool/RUNBOOK.md §5` for the full table.
Highlights:

- `fetch-model` 401 → HF token rotated; re-seed `keiei-llm-hf-token`
- `fallback-no-key` in ledger → Keychain bearer drift or wrapper not
  loading it; `security find-generic-password -s etzhayyim.keiei -a
  LLM_BEARER -w` should print the bearer
- `fallback-error:URLError` in ledger → tunnel/DNS not ready, or pod
  not yet reachable
- 401 from `/v1/chat/completions` via tunnel → bearer drift between
  Secret and Keychain; rotate both, restart daemon
- latency > 20 s → CPU contention on the node; scale node pool or
  graduate to GPU per Phase 4

## 10. Cross-references

- `90-docs/adr/2605101200-ai-cxo-roles-lsp-resident.md` — keiei layer
- `50-infra/vultr/keiei-llm-pool/RUNBOOK.md` — operator runbook
- `50-infra/vultr/cloudflared/embedder-tunnel.yaml` — peer pattern
- `60-apps/etzhayyim-project-murakumo/litellm/` — alternate gateway
- `90-docs/adr/2605010000-runpod-6000ada-unified-pod.md` — when GPU
  returns
- `deps.toml [[migrations]] keiei-llm-vultr-cpu-cutover-2026-05-10` —
  pending operator steps

## Addendum (2026-05-10, iter130) — fleet + LiteLLM proxy

The chart is now fleet-shaped. `.Values.models` is a list; default
contains both `gemma-4-E2B-it` and `gemma-4-E4B-it`. Each entry
renders its own PVC / Deployment / Service named `keiei-llm-{name}`.
A LiteLLM proxy (`keiei-litellm`, ClusterIP :4000) sits in front and
exposes the OpenAI-compatible `/v1/chat/completions` with a
`model_list` covering both backends, so the daemon picks model by
name. Public surface is `gemma.etzhayyim.com` (LiteLLM); `gemma-{e2b,e4b}.etzhayyim.com`
remain as direct routes for benchmark/diagnostic use.

The bearer Secret (`keiei-llm-auth`) does triple duty: backend
`--api-key-file` for both llama-server pods, LiteLLM `master_key`
that the daemon presents, and `UPSTREAM_BEARER` that LiteLLM forwards
to backends. Single secret = single rotation path.

A benchmark script `scripts/bench.py` drives both models through
LiteLLM (default) or directly (`--direct`) with the daemon's bearer
shape and emits a markdown summary table (mean / p50 / p95 latency
+ tok/s). Run after Phase 1 cutover; pin `KEIEI_LLM_MODEL` to whichever
variant best fits the daemon's 20 s timeout vs rationale-quality budget.

Anti-goal addendum: do **not** add per-conversation routing logic to
LiteLLM (e.g. "use E4B for CTO Class B, E2B for everything else").
That belongs in the daemon-side hook (`keiei.graph.cto._hook`), not in
LiteLLM. LiteLLM's job here is one-hop name → ClusterIP routing.

## Addendum (2026-05-14) — Gemma 4 E4B vision serving

Gemma 4 E4B is now used by Shinshi review generation as a multimodal
vision reviewer. The active route is the k8s-local direct llama-server
endpoint:

```text
http://keiei-llm-e4b.keiei-llm.svc.cluster.local:8080/v1/chat/completions
```

For `llama.cpp`, the GGUF model alone is not enough for image input. The E4B
Deployment must fetch and pass the matching mmproj file:

```text
--model /model/gemma-4-E4B-it-Q4_K_M.gguf
--mmproj /model/mmproj-gemma-4-E4B-it-F16.gguf
--image-max-tokens 280
```

Without `--mmproj`, text calls still work but image requests fail with an
"image input is not supported" error. `50-infra/vultr/keiei-llm-pool` now
treats the E4B service as the small CPU vision tier for low-QPS internal
review traffic. The current E4B sizing is 3500m CPU / 6 GiB requested and
6 CPU / 12 GiB limited; this is intentionally scoped for bounded review calls,
not high-throughput image understanding.

The public `gemma-e4b.etzhayyim.com` route remains diagnostic. Product traffic from
Shinshi uses the cluster-local service through `lg-shinshi`, preserving the
edge-only rule: Cloudflare/SvelteKit does not hold model credentials, DB
connections, or Hyperdrive state.
