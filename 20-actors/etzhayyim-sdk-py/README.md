# etzhayyim-sdk (Python binding)

Python binding for the `@etzhayyim/sdk` RW-free substrate.

Per **ADR-2605172000**, all etzhayyim/root apps MUST use this SDK instead of direct
RisingWave / Postgres / psycopg clients. The substrate is:
- **AT Protocol MST** — primary record store (PDS putRecord / getRecord / listRecords)
- **IPFS** — content-addressed blob pinning (ADR-2605171800 Stage 4)
- **Base L2 anchor** — finality anchor batch (ADR-2605171800 Stage 5)

## ADR references

- ADR-2605172000 — RW-free substrate hard rule
- ADR-2605171800 — LangGraph MST → IPFS → Base L2 anchor pipeline
- ADR-2605215200 — shinka Pregel MST rewrite (shinka cells use this SDK)
- ADR-2605215300 — yoro Python primitives MST rewrite addendum (yoro functions use this SDK)

## Status: M2 skeleton

All modules except `coalesce.py` are NotImplementedError stubs.
`coalesce.py` has a real asyncio implementation (the M2 critical-path unblocker
for yoro translation batch — see ADR-2605215300 §Open risks).

| Module | Status | ADR |
|---|---|---|
| `pds.py` | stub | ADR-2605172000, ADR-2605171800 |
| `mst.py` | stub | ADR-2605171800 |
| `ipfs.py` | stub | ADR-2605171800 Stage 4 |
| `l2.py` | stub | ADR-2605171800 Stage 5, ADR-2605171800 §read-only-address |
| `coalesce.py` | **real impl** | ADR-2605215300 §Open risks |
| `types.py` | real (dataclasses) | ADR-2605215200, ADR-2605215300 |

## Quick start

```python
from etzhayyim_sdk import pds, mst, coalesce

# Coalescer — batches concurrent translation commits
coalescer = coalesce.RequestCoalescer(window_ms=100, max_batch=64)

# PDS dispatch (stub until M3)
# await pds.put_record(collection="app.bsky.feed.post", record={...})

# MST query (stub until M3)
# await mst.query(collection="app.etzhayyim.shinka.kyumeiSignal", did="did:web:...")
```

## License

Apache-2.0 + etzhayyim Charter Compliance Rider v2.0 (see `/CHARTER-RIDER.md`).
