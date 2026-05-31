# haraedo 祓戸 — langgraph actor (kotoba WASM cell)

Two graphs over one kotoba EAVT graph (ADR-2606010200):

- **intake** (`handle_intake`): citizen application — classify (G3 hazardous split)
  → quote → match-facility (G14/G15) → schedule → sticker (G1 consent-gated).
- **dispatch** (`handle_dispatch`): operator logistics — gather → cluster →
  assign-vehicle (G15 capacity) → assign-crew (G5) → optimize-route (NN + 2-opt)
  → select-facility (G14/G15) → emit-plan (state `:planned`; G11 design-only).

LLM access is Murakumo-only via the kotoba `llm` host binding (127.0.0.1:4000,
gemma3:4b). State is read/written via the kotoba `datalog` host binding.

## Local dev

```bash
python agent.py   # runs both graphs with the kotoba bindings stubbed to None
```

## Build + deploy (WASM)

```bash
../kotoba/deploy.sh   # transacts schema+seed, componentize-py build, actor/deploy
```
