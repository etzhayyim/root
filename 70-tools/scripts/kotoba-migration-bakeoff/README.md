# kotoba py-WASM migration BAKE-OFF

Migrates 5 representative actor cells **1-by-1, agentically** (build-error feedback
loop, not single-shot codegen) with each of 3 candidate models, then compares
**generation quality and cost**. This is the maturity-first alternative to bulk
template regeneration (see `90-docs/kotoba-wasm-migration-plan.edn`, Wave 4 note).

## Models under test (all routed via Murakumo LiteLLM :4000, per ADR-2605215000)

| logical name           | backend                      | cost basis           |
|------------------------|------------------------------|----------------------|
| `bakeoff-claude-haiku` | `anthropic/claude-haiku-4-5` | $/token (commercial) |
| `bakeoff-gemini-flash` | `gemini/gemini-3.1-flash`    | $/token (commercial) |
| `bakeoff-gemma-26b`    | `gemma-4-26b-a4b-it` (local) | compute-seconds, $0  |

## Corpus (active Python cells) — `corpus.edn` (SoT) / `corpus.json` (harness mirror)

| cell | tier | LOC | nodes | rel-imp | ref-strategy |
|---|---|---|---|---|---|
| service-request   | simple         | 27 | 2 | 0 | gold-wasm |
| final-sign-off    | simple-plus    | 38 | 4 | 0 | gold-wasm |
| safety-monitoring | medium         | 67 | 5 | 1 | host-python |
| wafer-processing  | medium-complex | 73 | 6 | 1 | host-python |
| elv-body-shred    | complex        | 78 | 7 | 1 | host-python |

## Scored metrics

**Quality**: `build_pass`, `iters_to_build` (agentic iterations; lower = more mature),
`deploy_pass` (:8077), `invoke_equiv` (byte-equal to gold reference), `judge_score`
(1-5 by `BAKEOFF_JUDGE_MODEL`).
**Cost**: `tokens_in`/`tokens_out` (summed across iterations), `usd`, `wall_s`.

## Run prerequisites  (harness preflights and fails fast if unmet)

1. **kotoba `:8077` up** — `curl localhost:8077/health` → `wasm_executor: ready`. ✅ currently live.
2. **`componentize-py>=0.23`** — `build-pywasm.sh` auto-installs via pip; or `pip install componentize-py cbor2 langgraph langchain-core`.  ⛔ currently NOT installed.
3. **LiteLLM `:4000` up with the 3 `bakeoff-*` routes** — append `litellm-routes.bakeoff.yaml`
   to `50-infra/cluster/murakumo/litellm/config.yaml`, then start the gateway.  ⛔ currently down.
4. **Keys in env** (never committed; harness references via gateway only):
   - `ANTHROPIC_API_KEY`           ⛔ unset
   - `GEMINI_API_KEY`              ⛔ unset
   - `GEMMA26B_OPENAI_BASE`        ⛔ unset (EVO-X2 :11434 also unreachable from this host
     — loopback-route per ADR-2605302355 to dodge macOS Local Network Privacy)

> Set keys yourself (`! export ANTHROPIC_API_KEY=…` or macOS Keychain → env at gateway
> launch). They are NOT handed to the agent; the harness only ever calls `:4000`.

## Run

```bash
cd 70-tools/scripts/kotoba-migration-bakeoff
# (after prereqs) regenerate corpus.json from corpus.edn if you edited the EDN
python3 bakeoff.py
```

Outputs:
- `ports/<cell>/<model>.py` + `.wasm` — every generated port (inspectable)
- `results/results.edn` + `results.json` — per-(model,cell) rows + per-model rollup

## Notes / known follow-ups

- `:gold-wasm` equivalence is marked `nil` by the harness and compared offline
  against the committed `kotoba-langgraph-*` example components (the two simple cells
  already have hand-ported gold .wasm). `:host-python` cells compute ground truth live.
- The `:8077` invoke envelope here sends `input_json`; production uses a CBOR ctx.
  Align `deploy_and_invoke()` with the prod CBOR envelope before trusting `invoke_equiv`
  as a release gate.
- Charter Rider scan + structural-conformance are available cheaply (AST pre-check is
  already wired) but were out of scope for this round's chosen metrics.
