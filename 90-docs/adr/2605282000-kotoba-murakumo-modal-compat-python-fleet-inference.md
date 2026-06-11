---
id: adr-2605282000-kotoba-murakumo-modal-compat-python-fleet-inference
title: "ADR-2605282000: kotoba_murakumo — Modal-compatible Python facade for Murakumo Mac mini fleet GPU inference (R0 scaffold)"
status: proposed
doc_type: adr
topic: kotoba-murakumo-python-facade
authoritative: true
last_verified: 2026-05-28
priority: 6.0
axis: architecture
weight: 0.55
priority_note: "Closes the developer-ergonomics gap between Modal's well-known decorator API and the religious-corp Murakumo-only inference invariant (ADR-2605215000). Without this, every internal app writing inference code must hand-wire LiteLLM/Ollama HTTP calls, which (a) discourages migration from existing Modal code and (b) creates per-app drift that bypasses Charter Rider §2 scanning. This ADR defines the R0 scaffold that lands the package skeleton, Modal-compat surface, and 3-backend routing (LiteLLM gateway / EVO-X2 ollama / per-node Ollama gemma3:4b). R1+ wires WASM Component dispatch, ComfyUI, kotoba-vm Invoke records, and DID-bound auth."
authoritative_for:
  - kotoba_murakumo Python facade for Murakumo fleet inference
  - Modal-API-compatibility contract for religious-corp internal apps
  - Inference routing policy from Python to the fleet's 3 backend tiers
depends_on:
  - "2605215000"  # Murakumo-only inference invariant (NO RunPod / commercial GPU rental)
  - "2605262130"  # kotoba canonical storage substrate
  - "2605192200"  # Charter Rider v2.0 (§2(a)-(h) scan on inputs and outputs)
  - "2605202345"  # EVO-X2 Windows ROCm inference backend
  - "2605231525"  # server-side signing-capability (DID-bound auth; no platform-held keys)
  - "2605232100"  # k3s on Lima fleet (cells as DaemonSet)
  - "2605240001"  # kotoba cleanroom architecture (SSoT)
  - "2605250005"  # WebGPU inference + unified weight predicate scheme
  - "2605262200"  # CHARTER-RIDER §2(i)(2) train-only carve-out (inference path unchanged; this ADR enforces that)
related: []
supersedes: []
superseded_by: []
---

# ADR-2605282000: kotoba_murakumo — Modal-compatible Python facade for Murakumo Mac mini fleet GPU inference (R0 scaffold)

**Status**: proposed
**Date**: 2026-05-28
**Deciders**: Jun Kawasaki

## Context

Modal (modal.com) is the de-facto Python decorator-API for "submit a function, get GPU inference back." Internal religious-corp app authors (yoro, watashi, baien-distill orchestrator, KaizenObserver downstream, future PWAs) already know that API. Today they have two unergonomic choices:

1. Call LiteLLM gateway by hand-rolled `httpx.post("http://192.168.1.17:4000/v1/chat/completions", ...)`. Every app re-invents env-var wiring, Charter Rider §2 scanning, error handling, streaming, fallback-on-unreachable.
2. Drop into `kotodama` cell-runner. That is the production path for cells but is heavy for one-shot inference from a notebook or PWA backend.

**The constitutional constraint (CRITICAL)** — ADR-2605215000 §2(i)(1) makes the Murakumo fleet (LiteLLM gateway on judah :4000 + EVO-X2 LAN 192.168.1.70 + per-node Ollama gemma3:4b fallback) the **sole inference SSoT** for religious-corp paths. RunPod, Bedrock direct, Vertex direct, Anthropic-direct-from-vendor-key, and any commercial GPU rental are **prohibited at the inference path** (ADR-2605262200 §2(i)(2) carves out training rental only and explicitly preserves the inference invariant unchanged). A drop-in `modal`-shaped facade that secretly calls Modal Labs would violate this — so the facade must route **only** to Murakumo endpoints declared in `50-infra/murakumo/fleet.toml`.

**The substrate fit** — kotoba (ADR-2605262130) is the canonical storage substrate engine, and its Rust workspace already exposes everything we need on the back end:

- `kotoba-llm::http_infer::HttpInferEngine` — OpenAI-compatible HTTP client driven by `KOTOBA_INFERENCE_URL` / `KOTOBA_INFERENCE_MODEL` / `KOTOBA_INFERENCE_API_KEY` env vars. Already supports Ollama / LiteLLM / vLLM wire format.
- `kotoba-vm::executor` + `kotoba-runtime::WasmExecutor` — WASM Component Model host for arbitrary GPU/CPU compute (R2 scope: lets `@app.function(image=Image.wasm_component(...))` dispatch real compute, not just LLM calls).
- `kotoba-kse::Vault` — content-addressed blob store for `Image` payloads and `Volume` contents (Modal's `Image.debian_slim().pip_install(...)` and `Volume.from_name("models")` both reduce to "this CID is the contents of /something").
- `kotoba-graph::QuadStore` — invocation records (Datom: `{invocation_cid, "result", result_cid}`) become first-class Datalog facts queryable from KaizenObserver.
- `kotoba-auth::CACAO` — DID-bound auth chains so every `.remote()` call carries a verifiable caller identity (closes the ADR-2605231525 no-platform-keys invariant for the inference path).
- `kotoba-net::libp2p` — cross-node dispatch in R2+ when WASM Component routing is wired.

Python-side, `40-engine/kotoba/py/kotoba_langgraph/` already exists as a pure-Python sibling that uses kotoba via componentize-py-built WASM Components. `kotoba_murakumo` sits next to it as a second public Python surface — pure stdlib R0, optional `httpx` / `anyio` in R1, optional `cbor2` in R2.

**User decision 2026-05-28**: "modal と互換性を保持" — Modal compatibility is a hard goal. That means the surface should be `from kotoba_murakumo.modal_compat import *` → user can `import modal` → swap import path → their existing decorator code runs against the fleet without rewriting bodies. Gaps (e.g. Modal-only features like `Image.from_registry`, `web_endpoint`, `Queue`, `Dict`, `Sandbox`, GPU types we cannot satisfy) raise a clear `MurakumoCompatNotImplemented` exception with the deviation reason, not silent fallback.

**Naming collision honesty** — Modal is a registered trademark of Modal Labs Inc. `kotoba_murakumo` does NOT distribute Modal Labs code, link to their servers, or claim Modal certification. The `modal_compat` subpackage is an API-compat shim only (analogous to `nv_compat` in ADR-2605261800 §D10 — the Google v. Oracle 2021 API fair-use precedent applies). CHARTER-RIDER §6 trademark notice will be amended in R1 to add Modal® attribution.

## Decision

Land `40-engine/kotoba/py/kotoba_murakumo/` as a new Python package (sibling of `kotoba_langgraph/`), Apache 2.0 + Charter Rider v2.0, R0 scope = scaffold + Modal-compat surface + 3-backend routing. R1+ ships WASM dispatch, Volume CID resolve, DID-bound auth, and live-smoke against judah :4000.

### Package layout (R0)

```
40-engine/kotoba/py/kotoba_murakumo/
├── pyproject.toml
├── README.md
├── kotoba_murakumo/
│   ├── __init__.py          # re-exports public API
│   ├── app.py               # App (Modal's Stub equivalent)
│   ├── function.py          # Function wrapper: .remote / .spawn / .map / .stream / .local
│   ├── cls.py               # Cls + @enter/@exit/@method decorators
│   ├── image.py             # Image builder (R0: identity + .from_litellm + .wasm_component stub)
│   ├── volume.py            # Volume (R0: name registry; R1: kotoba-kse Vault CID binding)
│   ├── secret.py            # Secret (R0: env-only; R1: encrypted Vault entry)
│   ├── gpu.py               # GPU type classes + selector → fleet endpoint mapping
│   ├── fleet.py             # fleet.toml loader + backend registry
│   ├── exceptions.py        # MurakumoCompatNotImplemented, FleetUnreachable, CharterViolation
│   ├── charter.py           # Charter Rider §2(a)-(h) scan hook (input + output)
│   ├── modal_compat.py      # `import modal` → drop-in shim
│   ├── _internal/
│   │   ├── __init__.py
│   │   ├── routing.py       # selector → endpoint (resolve gpu= + model= → URL)
│   │   ├── ndjson.py        # invocation log emit (R0: local file; R1: PDS attest)
│   │   └── toml_loader.py   # stdlib tomllib wrapper for fleet.toml
│   └── client/
│       ├── __init__.py
│       ├── litellm.py       # OpenAI chat-completions sync + async + stream
│       ├── ollama.py        # Ollama-direct fallback (own-node gemma3:4b path)
│       └── comfyui.py       # ComfyUI prompt POST (image gen, R1+ wiring)
└── tests/
    ├── __init__.py
    ├── test_fleet_load.py
    ├── test_routing.py
    └── test_modal_compat.py
```

### Modal-compatibility contract (R0 → R3 ladder)

| Modal API surface | R0 (this ADR) | R1 | R2 | R3 |
|---|---|---|---|---|
| `App(name=)` / `Stub` alias | ✓ | DID-bound | — | — |
| `@app.function(...)` | ✓ (signature only) | LLM `.remote()` live | WASM Component dispatch | sharded `.map()` |
| `@app.cls()` + `@enter` / `@exit` / `@method` | ✓ (signature only) | per-instance KV-cache stub | live KV-cache in `kotoba-llm` Arrangement | distributed Cls (Pregel BSP) |
| `.remote()` sync | ✓ stub | LLM live | WASM live | — |
| `.local()` | ✓ identity passthrough | — | — | — |
| `.spawn()` async | — | ✓ (ChainEntry CID return) | — | — |
| `.map()` / `.starmap()` | — | ✓ thread pool | ✓ fleet-distributed | — |
| `.stream()` SSE | — | ✓ LiteLLM SSE | — | — |
| `Image.debian_slim()` / `.pip_install()` | ✓ no-op (records intent) | ✓ records Charter scan input | ✓ produces WASM Component CID | — |
| `Image.from_registry()` | ✗ → `MurakumoCompatNotImplemented` ("commercial registry forbidden per Charter Rider §2(c)+(e)") | — | — | — |
| `Volume.from_name()` | ✓ stub registry | ✓ kotoba-kse Vault CID lookup | ✓ pin/unpin via Kubo | — |
| `Secret.from_name()` | ✓ env-var lookup | ✓ encrypted Vault | — | — |
| `Secret.from_dict()` | ✓ in-memory | — | — | — |
| `Queue` / `Dict` | — | — | ✓ `kotoba-graph` QuadStore backed | — |
| `web_endpoint` / `asgi_app` | ✗ → `MurakumoCompatNotImplemented` ("use yoro / kotoba-server XRPC") | — | — | — |
| `Sandbox` / `Function.from_dockerhub` | ✗ → `MurakumoCompatNotImplemented` ("no container runtime in fleet; use WASM Component") | — | — | — |
| `gpu.T4` / `gpu.L4` / `gpu.A10G` | ✓ → EVO-X2 selector | — | — | — |
| `gpu.A100` / `gpu.A100_80GB` / `gpu.H100` / `gpu.H200` | ✓ → EVO-X2 high-VRAM + warning logged ("requested NVIDIA-class GPU; routed to EVO-X2 ROCm gfx1151; expect throughput delta") | — | — | — |
| `gpu="any"` / `None` | ✓ → LiteLLM gateway (model-routed) | — | — | — |

Any Modal surface not in this table is implicitly `MurakumoCompatNotImplemented` — fail loud, never silently substitute Modal Labs.

### Fleet routing policy (R0 deterministic)

`fleet.toml` is the SSoT. Resolution rules (R0):

1. **Explicit `gpu=gpu.MacMini(node="judah")`** → `http://{node.ip_lan}:11434` (own-node Ollama gemma3:4b). Fails fast if `node` not in fleet.
2. **`gpu=gpu.EvoX2()`** → `inference_backends.evo-x2.endpoints.litellm.url` (default), or `.ollama.url` if `prefer="ollama"`. Auth via `EVO_X2_LITELLM_KEY` env (per `master_key_env`).
3. **`gpu=gpu.WebGPU()`** → R2 (WASM Component dispatch); R0 raises `MurakumoCompatNotImplemented("WebGPU dispatch lands R2")`.
4. **`gpu=None` / `gpu="any"` / Modal-string GPU** → LiteLLM gateway at `http://192.168.1.17:4000` (judah; the gateway routes by model name across backends).
5. **`on_unreachable`** → per `fleet.toml` `failover.on_unreachable` ("cells fall back to own-node local Ollama gemma3:4b"). R0 surfaces the unreachable event as `FleetUnreachable` with the attempted endpoint chain.

No magic. No silent Modal Labs fallback. If `fleet.toml` is absent, every `.remote()` raises `FleetUnreachable("fleet.toml not found; refusing to route to anywhere else per ADR-2605215000")`.

### Charter Rider §2 scan hook (R0 advisory, R1 enforce)

`charter.py` exports `scan(text: str, *, side: Literal["input","output"]) -> CharterScanResult`. R0 implementation is a stub that returns `clean` for everything but records the call (so we can verify hook coverage in tests). R1 binds to the existing scanner pattern used by `baien-distill.validate` (CLAUDE.md "Baien tooling index" row references `etzhayyim_organism.sensors.charter_rider.scan()` as canonical). Both `.remote()` input args and the returned text are scanned; a finding of severity ≥ `major` raises `CharterViolation` and the call is aborted **before** results are returned to the caller.

R0 hook surface (so R1 can flip the switch without API churn):

```python
# every .remote() wraps user prompt + result like:
from kotoba_murakumo.charter import scan, CharterViolation
scan_in = scan(prompt, side="input")     # R0: stub returns clean
result = _dispatch(...)
scan_out = scan(result, side="output")   # R0: stub returns clean
# R1: if scan_in.severity >= "major" or scan_out.severity >= "major": raise CharterViolation
```

### Invocation record (R0 local NDJSON, R1 PDS attest)

Every `.remote()` emits one line to `~/.kotoba_murakumo/invocations.ndjson`:

```json
{"ts":"2026-05-28T20:00:00Z","app":"my-inference","fn":"summarize","caller_did":"did:web:...","endpoint":"http://192.168.1.17:4000","model":"gemma3:4b","prompt_chars":42,"result_chars":138,"latency_ms":312,"charter_in":"clean","charter_out":"clean"}
```

R1 promotes this to a real `com.etzhayyim.murakumo.invocation` Lexicon record posted to the caller's PDS (consistent with the existing organism observation pattern in ADR-2605240200). R0 lands the NDJSON path so KaizenObserver downstream tail-readers can ingest immediately without waiting for the Lexicon.

### Hard non-goals (R0 → R3)

- **N1**: NEVER call Modal Labs servers (modal.com / api.modal.com) from any code path. CI grep gate added in R1.
- **N2**: NEVER allow `Image.from_registry` to resolve a Docker Hub / GHCR / ECR / GCR image. Closed enum at R0.
- **N3**: NEVER hold a platform-side API key for inference routing other than `EVO_X2_LITELLM_KEY` (fleet-internal master key, rotated per `fleet.toml` security policy). Per-caller auth uses CACAO chain in R1.
- **N4**: NEVER hide a `FleetUnreachable` by silently substituting another vendor. R0+ surface failures with the attempted endpoint chain.
- **N5**: NO `gpu.A100()` / `gpu.H100()` silently delivers NVIDIA — they all route to ROCm EVO-X2 with a logged warning. This is honesty, not bait-and-switch.
- **N6**: NEVER bypass Charter Rider §2 scan once R1 flips it from advisory to enforce. The scan is a constitutional invariant per Charter Rider §2 and ADR-2605192200.
- **N7**: NEVER make `kotoba_murakumo` depend on `kotodama` (and vice versa). Both are siblings consuming the same fleet.toml.
- **N8**: NEVER write to `kotoba-kse` Vault from R0 client paths. Vault binding lands R1 after `kotoba-store` Python bindings stabilize.

### Pyproject + dependencies

```toml
[project]
name = "kotoba-murakumo"
version = "0.0.1"            # R0 scaffold
requires-python = ">=3.11"
license = { text = "Apache-2.0" }
dependencies = []            # stdlib only at R0 (tomllib in 3.11+)

[project.optional-dependencies]
http = ["httpx>=0.27", "anyio>=4"]    # R1: live LiteLLM/Ollama dispatch
test = ["pytest>=8", "pytest-asyncio>=0.23"]
```

Stdlib-only R0 keeps the package componentize-py-portable (same constraint that drove `kotoba_langgraph` to stdlib-only) so it can be embedded in WASM Components if needed.

## Subrepo placement (final framing, amended 2026-05-28 evening)

**Decision** (per ADR-2605282200 relocation rationale): `kotoba_murakumo`
lives at **`40-engine/kotoba_murakumo/`** as a sibling of the kotoba
subrepo, NOT inside it. This is the structurally correct placement and
permanent.

Why the relocation: the original R0/R1.1/R1.2 commits (`81fe1db2c` +
`b8549d937`) placed `kotoba_murakumo` inside the kotoba subrepo working
tree at `40-engine/kotoba/py/kotoba_murakumo/`. The first attempt to
`git subrepo push` revealed that the upstream `github.com/etzhayyim/kotoba`
had force-pushed away the merge-base commit (`17e30d9db5...`) recorded in
`.gitrepo`, making subrepo sync impossible without manual surgery.
ADR-2605282300 §"Root cause" treats this as a structural signal: a
religious-corp downstream consumer should not live inside an upstream
mirror.

| Integration axis | State |
|---|---|
| Path location | ✓ `40-engine/kotoba_murakumo/` (sibling of `40-engine/kotoba/`) |
| git-subrepo coupling | ✓ **none** — package is monorepo-only |
| External clone visibility (`git clone github.com/etzhayyim/kotoba`) | ✗ by design — package is religious-corp internal, not part of kotoba's external surface |
| `kotoba_langgraph` precedent | n/a — `kotoba_langgraph` lives inside the subrepo because it IS canonical kotoba (compiled to WASM Components for `kotoba-runtime`); `kotoba_murakumo` is downstream |
| Cargo workspace member | n/a (Python only) |
| Rust crate dependency | ✗ none at R1.1; the `economy_xrpc.rs` scaffold that lands in kotoba-server is independent (cfg-gated; R1.3d-wiring) |
| CI / test runner | ✓ `70-tools/scripts/test-kotoba-murakumo.sh` (monorepo path; runs from project root) |

**Consumer relationship (preserved)**: `kotoba_murakumo` consumes the
kotoba substrate engine via HTTP at R1.1 (LiteLLM gateway + Ollama
endpoints declared in `50-infra/murakumo/fleet.toml`), and will consume
it via kotoba-vm XRPC at R2 (`kotoba_murakumo.client.kotoba_vm` →
`POST /xrpc/com.etzhayyim.kotoba.vm.invoke` against a kotoba-server
instance on the fleet). The consumer relationship does not require
filesystem-collocation.

## Consequences

**Positive**:

- Internal app authors can write `import kotoba_murakumo as modal` and use the familiar decorator API while staying on the Murakumo fleet — zero code-body changes for the common LLM-call case.
- The 3-tier routing policy is in code, not in `httpx.post` boilerplate scattered across apps. Charter scan, fleet unreachable handling, invocation logging all happen exactly once.
- KaizenObserver and the future `com.etzhayyim.murakumo.invocation` Lexicon gain a uniform observability surface across every Python caller.
- The package is a natural home for the R2 WASM Component dispatch path (kotoba-vm Invoke), so adding non-LLM GPU compute later does not require a new public surface.
- Closes a year of drift risk where each app would otherwise hand-roll its own LiteLLM call pattern with its own (likely missing) Charter scan.

**Negative / Tradeoffs**:

- Maintaining Modal-compat surface means tracking Modal's API evolution. R1 will pin a Modal-API snapshot date and document it in the package README; new Modal surfaces ship as `MurakumoCompatNotImplemented` until reviewed.
- `gpu.A100() → EVO-X2 ROCm gfx1151` is technically a downshift. The warning log is honest, but some Modal-port apps may have throughput expectations that ROCm cannot meet. Documented in the GPU mapping table.
- Modal trademark adjacency requires the CHARTER-RIDER §6 attribution amendment in R1. Until then, the README carries an inline disclaimer.

**Constitutional**:

- ADR-2605215000 Murakumo-only invariant is **strengthened**, not weakened: this ADR makes the invariant easier to honor (the path of least resistance routes to fleet) rather than easier to bypass.
- ADR-2605262200 §2(i)(2) train carve-out is **preserved unchanged**: this ADR is inference-only; it does not provide any path to commercial GPU rental.
- ADR-2605192200 Charter Rider §2 scan is **operationalized at the inference boundary** in R1, closing a gap where free-form prompts could carry §2(a)-(h) violations into the fleet.

## Alternatives Considered

1. **No facade; require apps to call LiteLLM via raw HTTP**. Status quo. Rejected: high drift, missing Charter scan, no observability uniformity.
2. **Extend `kotodama` cell-runner to host a Modal-compat surface**. Rejected: cells are k3s DaemonSets per ADR-2605232100, not per-call dispatchers. The two surfaces solve different problems.
3. **Build a non-Modal-shaped Python SDK**. Considered. Rejected because the user explicitly chose "Modal-compat" and because forcing a new mental model on internal authors who already know Modal raises adoption cost for no constitutional benefit.
4. **Wrap a hosted Modal Labs deployment behind a proxy**. Categorically rejected per ADR-2605215000 (Murakumo-only invariant) and ADR-2605262200 §2(i)(2) (carve-out is train-only). Would require Council Lv7+ unanimity to amend, which is not requested.
5. **Skip Charter scan at R0**. Rejected: even an advisory stub locks the API shape in, so R1 is a one-line flip from `advisory` to `enforce`. Adding the hook later is a breaking change.
6. **Live LLM dispatch in R0**. Rejected: scaffold-first lets us land the API and tests today, then iterate routing with a stable contract. Same ladder pattern used by ADR-2605262500 W0 (paths reserved, no code) and ADR-2605261800 R0/R1.0/R1.1 (charter → first runnable code → end-to-end).

## References

- ADR-2605215000 (etzhayyim inference Murakumo-only — NO RunPod / commercial GPU rental)
- ADR-2605262130 (kotoba canonical storage substrate)
- ADR-2605192200 (Apache 2.0 + Charter Compliance Rider v2.0)
- ADR-2605202345 (EVO-X2 Windows ROCm inference backend)
- ADR-2605231525 (server-side signing-capability invariant)
- ADR-2605232100 (k3s on Lima fleet — cells as DaemonSet)
- ADR-2605262200 (Charter Rider §2(i)(2) train-only commercial-GPU-rental carve-out — inference path unchanged)
- ADR-2605261800 (NVIDIA Omniverse stack API-compat — `nv_compat` precedent for trademark-adjacent compat namespace)
- ADR-2605240200 (KaizenObserver — downstream consumer for invocation NDJSON)
- ADR-2605240001 (kotoba cleanroom architecture)
- `50-infra/murakumo/fleet.toml` — fleet endpoint SSoT
- `40-engine/kotoba/crates/kotoba-llm/src/http_infer.rs` — Rust-side equivalent (env-var-driven OpenAI-compat client)
- `40-engine/kotoba/py/kotoba_langgraph/` — sibling pure-Python kotoba package (precedent for stdlib-only)
- `/CHARTER-RIDER.md` — license addendum (R1 §6 amendment will add Modal® attribution)
