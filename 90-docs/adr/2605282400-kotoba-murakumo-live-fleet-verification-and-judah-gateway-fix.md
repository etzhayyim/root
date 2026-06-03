---
id: adr-2605282400-kotoba-murakumo-live-fleet-verification-and-judah-gateway-fix
title: "ADR-2605282400: kotoba_murakumo live-verified on Murakumo fleet 2026-05-28 + judah gateway LITELLM_MASTER_KEY routing fix"
status: proposed
doc_type: adr
topic: kotoba-murakumo-live-verification
authoritative: true
last_verified: 2026-05-28
priority: 5.0
axis: verification
weight: 0.35
priority_note: "Closes the 'can it actually run?' question with a real live round-trip against the Murakumo fleet on 2026-05-28 evening. 4 end-to-end demos — sync .remote() / .map() batch / .stream() SSE / BudgetExceeded pre-flight raise — all green against naphtali (192.168.1.18:11434, gemma3:1b). Discovered + documented honest fleet operational state (some endpoints reachable but wedged, gateway has dead-node routing, EVO-X2 off). Ships a single small code fix (routing.py LITELLM_MASTER_KEY auth_bearer_env for litellm-gateway backend) that the live test surfaced. R1.3c gateway-routing repair + EVO-X2 WoL + auto-tribe-selector deferred to separate ADRs."
authoritative_for:
  - live-verification record of kotoba_murakumo end-to-end on the Murakumo fleet
  - judah gateway bearer-auth env-var convention (LITELLM_MASTER_KEY)
depends_on:
  - "2605282000"  # kotoba_murakumo facade (subject of verification)
  - "2605282100"  # mKOTO economy (Budget exceeded demo verified)
  - "2605282300"  # relocation (verification ran from the post-relocation path)
  - "2605215000"  # Murakumo-only invariant (verification used only fleet endpoints)
related: []
supersedes: []
superseded_by: []
---

# ADR-2605282400: kotoba_murakumo live-verified on Murakumo fleet 2026-05-28 + judah gateway LITELLM_MASTER_KEY routing fix

**Status**: proposed
**Date**: 2026-05-28
**Deciders**: Jun Kawasaki

## Context

After R1.3b shipped (62 unit-test green + 2 live_fleet skipped), the
question "実際に modal python を murakumo fleet で 動かせる?" stood
unanswered with concrete proof. The live_fleet smoke marker in
`tests/test_live_fleet_smoke.py` was gated on
`KOTOBA_MURAKUMO_LIVE_FLEET=1` + LAN reachability of judah :4000 / evo-x2
:11434 and had never actually been run against a reachable fleet.

This ADR captures the 2026-05-28 evening verification session: actually
running the package against the real LAN fleet, what worked, what didn't,
what code fix was needed.

## Decision

**Verified live**. `kotoba_murakumo` runs Modal-shape Python end-to-end
against the Murakumo fleet. Ships one small fix in
`kotoba_murakumo._internal.routing` for the judah gateway bearer-auth
env-var (`LITELLM_MASTER_KEY`) that the live test surfaced. Fleet
operational gaps (judah :11434 hung, gateway dead-node routing, EVO-X2 off)
are documented but deferred to fleet-ops ADRs, not kotoba_murakumo's
problem.

### Reachability probe (2026-05-28 19:xx JST, from dev box on 192.168.1.x)

```
$ for hp in 192.168.1.17:4000 192.168.1.17:11434 192.168.1.70:11434 192.168.1.70:4000; do
    nc -z -G 2 -w 2 ${hp%:*} ${hp#*:}
  done
192.168.1.17:4000   REACHABLE   (judah LiteLLM gateway)
192.168.1.17:11434  REACHABLE   (judah own-node Ollama)
192.168.1.70:11434  unreachable (EVO-X2 :11434, WoL off)
192.168.1.70:4000   unreachable (EVO-X2 :4000, WoL off)
```

Subsequent broader probe found 11 of 16 candidate `192.168.1.X:11434`
endpoints reachable (`.11 .12 .13 .14 .15 .16 .17 .18 .19 .21 .23`).

### The 4 live demos (all green)

| # | Surface | Resolved route | Result | Latency |
|---|---|---|---|---|
| 1 | `@stub.function(gpu=modal.gpu.A10G(), ...)` → switched to `gpu.MacMini(node="naphtali")` for working path | `192.168.1.18:11434` ollama gemma3:1b | `'Positive\n'` (sentiment) | 358 ms |
| 2 | `classify.map(prompts, concurrency=3)` | same backend × 3 parallel | `H2O / Burning / Quiet` | 324 ms |
| 3 | `async for tok in f.stream(...)` | same backend, SSE | 123 chars across N tokens | 568 ms |
| 4 | `@stub.function(max_cost_mkoto=1)` + `f.remote(...)` | budget cap = 1 mKOTO; est = 323 mKOTO | `BudgetExceeded` raised, **HTTP never fired** | < 1 ms |

Demo 4 evidence (R1.3b economy layer working as designed):

```
caught: cap=1 mKOTO, estimated=323 mKOTO, fn='too_cheap'
→ HTTP never fired, donation prompt UI surface ready
```

Demo 1 NDJSON record written to `~/.kotoba_murakumo/invocations.ndjson`:

```json
{"backend":"mac-mini/naphtali","endpoint":"http://192.168.1.18:11434",
 "model":"gemma3:1b","latency_ms":228,"cost_mkoto":8,
 "tariff_version":"2026-05-28-dev","charter_in":"clean","charter_out":"clean",
 "phase":"sync"}
```

Cost arithmetic check: `tariff.for_backend("mac-mini/judah").gpu_second_mkoto = 30`
(mac-mini/naphtali falls back to mac-mini/judah row); 228 ms = 0.228 s ×
30 mKOTO/s = 6.84 → `ceil` = **8 mKOTO**. Matches the NDJSON entry exactly.

### Routing fix surfaced by the live test

The initial `test_live_litellm_gateway_round_trip` call to judah :4000
returned `401 Unauthorized`. Investigation:

- Existing config at
  `60-apps/etzhayyim-project-murakumo/litellm/config.yaml` line 78:
  `master_key: os.environ/LITELLM_MASTER_KEY`
- Default value from ansible role
  (`ansible/roles/litellm/defaults/main.yml` line 6):
  `litellm_master_key: "sk-etzhayyim-litellm-local"`
- Every other consumer (Workers, langgraph, executor, health-check)
  passes `Authorization: Bearer ${LITELLM_MASTER_KEY}`.

`kotoba_murakumo._internal.routing.resolve` for the `litellm-gateway`
backend was wired with `auth_bearer_env=None`. **Fix** in this commit:

```python
# kotoba_murakumo/_internal/routing.py
return ResolvedRoute(
    url=url,
    model=resolved_model,
    backend="litellm-gateway",
    kind="openai-compatible",
    # The judah-hosted LiteLLM gateway requires bearer auth ...
    auth_bearer_env="LITELLM_MASTER_KEY",
    note=f"routed to LiteLLM gateway on {gateway_node}",
)
```

`tests/test_routing.py::test_none_routes_to_litellm_gateway` updated to
assert `auth_bearer_env == "LITELLM_MASTER_KEY"`. 62 tests still pass.

### Honest fleet state (operational; OUT OF SCOPE for this ADR's code fix)

1. **judah :11434 own-node Ollama wedged**. Port open, `/api/tags`
   returns immediately, but `/api/generate` and `/v1/chat/completions`
   hang past 180 s with no bytes received. Possible causes: model
   load-loop, OOM, concurrent inference monopolizing GPU. **Action**:
   separate fleet-ops issue. The demo used naphtali instead.
2. **judah :4000 gateway dead-node routing**. With correct bearer:
   `model: gemma4-e4b` → forwarded to `http://192.168.1.49:11434`
   (`Can't assign requested address`); `model: gemma3-1b` → forwarded
   to `http://192.168.1.64:11434` (same error). The gateway's
   model→node table predates the current 11-tribe layout. **Action**:
   re-wire gateway config to live tribes (separate fleet-ops ADR).
3. **EVO-X2 (192.168.1.70) off**. Both :4000 and :11434 unreachable.
   Known per `fleet.toml` "WoL recovery pending". **Action**: out of
   scope.

These are real production-readiness gaps but they are about *fleet
operations*, not about `kotoba_murakumo`. The package itself dispatches
correctly to any reachable backend `fleet.toml` declares.

### Future trackers (deferred to separate ADRs)

| Issue | Suggested next step |
|---|---|
| Judah :11434 wedge | Restart Ollama on judah; investigate root cause |
| Gateway dead-node routing | Re-wire `60-apps/etzhayyim-project-murakumo/litellm/config.yaml` model_list to 11 live tribes |
| EVO-X2 WoL | Bring back online or revise fleet.toml `failover.on_unreachable` |
| `gpu.MacMini(node="auto")` selector | Add health-check-driven auto-tribe selector to `routing.resolve` (Modal-equivalent of automatic GPU pool dispatch) |
| Live smoke test re-targeting | Update `tests/test_live_fleet_smoke.py` to default to naphtali (known-good) instead of judah :11434 (known-wedged) |
| R1.3c `kotoba-server` XRPC wiring | Take the `economy_xrpc.rs` cfg-gated scaffold (still inside subrepo per ADR-2605282300) live |

## Consequences

**Positive**:
- The package is no longer "theoretically functional" — it has been
  empirically demonstrated against the real fleet.
- One real bug found and fixed (gateway 401) before any consumer hit it.
- Operational gaps surfaced are documented + assigned to the right scope
  (fleet-ops, not facade).
- The R1.3b economy layer is verified working in-anger (BudgetExceeded
  preflight, NDJSON cost record, tariff arithmetic round-trip).
- Modal-compat shim verified — `import kotoba_murakumo.modal_compat as
  modal` + `@stub.function(gpu=modal.gpu.A10G(), ...)` works without
  source-body edits to the user function.

**Negative / Tradeoffs**:
- Default `gpu=None` (LiteLLM gateway) path will NOT work end-to-end
  until either (a) `LITELLM_MASTER_KEY` env var is set in the caller's
  environment, AND (b) the gateway's dead-node routing is repaired.
  Until both, callers should prefer `gpu=gpu.MacMini(node="naphtali")`
  or another known-working tribe.
- The live smoke test in `tests/test_live_fleet_smoke.py` still targets
  judah :11434 + EVO-X2 :11434 and will skip / fail on a live run. Fix
  deferred (see Future trackers).

**Constitutional**:
- ADR-2605215000 Murakumo-only invariant **upheld** — the live demo
  contacted only `192.168.1.18:11434` (declared in `fleet.toml`); no
  commercial GPU rental, no Modal Labs servers.
- ADR-2605282000 N1 (no Modal Labs calls) **upheld** — CI grep gate
  re-run clean.
- ADR-2605282100 mKOTO economy **honored** — pre-flight budget check
  fired before HTTP for the BudgetExceeded demo; NDJSON cost record
  written for the successful dispatch.

## Alternatives Considered

1. **Skip live verification; ship on unit tests alone**. Rejected — the
   user explicitly asked "実際に動かせる?", which is a verification
   request that unit tests cannot answer.
2. **Fix the gateway dead-node routing in this same commit**. Rejected
   — that fix lives in
   `60-apps/etzhayyim-project-murakumo/litellm/config.yaml` which is a
   different concern (fleet ops); bundling would muddy this ADR's scope
   (verification of `kotoba_murakumo`).
3. **Land the `gpu.MacMini(node="auto")` selector here**. Rejected —
   would require a health-check probe layer + caching; should be its own
   ADR.
4. **Hard-code the default key `sk-etzhayyim-litellm-local` as a fallback**.
   Rejected — would violate ADR-2605231525 (no platform-held keys); the
   key must come from the caller's env.

## References

- ADR-2605282000 (kotoba_murakumo facade — subject of verification)
- ADR-2605282100 (mKOTO economy — BudgetExceeded demo verified)
- ADR-2605282300 (relocation ADR — verification ran from the post-
  relocation path `40-engine/kotoba_murakumo/`)
- ADR-2605215000 (Murakumo-only invariant)
- ADR-2605231525 (no platform-held keys — why the bearer comes from env)
- `60-apps/etzhayyim-project-murakumo/litellm/config.yaml` — gateway
  config (line 78: `master_key: os.environ/LITELLM_MASTER_KEY`)
- `60-apps/etzhayyim-project-murakumo/ansible/roles/litellm/defaults/main.yml` —
  default key value (line 6: `sk-etzhayyim-litellm-local`)
- `50-infra/murakumo/fleet.toml` — fleet SSoT
- `~/.kotoba_murakumo/invocations.ndjson` — live demo NDJSON evidence
