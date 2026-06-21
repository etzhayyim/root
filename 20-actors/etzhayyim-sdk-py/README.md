# etzhayyim-sdk-py — Python SDK for the etzhayyim religious-corp substrate

Python client library for the etzhayyim AT Protocol + IPFS + Base L2 substrate. Used by religious-corp Pregel cells (shinka, joucho, yoro, maps_sentinel) running on the Murakumo distributed fleet.

Per ADR-2605172000 (kotoba substrate), ADR-2605214000 (no commercial K8s), ADR-2605215000 (no commercial GPU rental).

## Modules

| Module | Purpose |
|---|---|
| `mst_projector` | mst-projector XRPC client (query_by_collection / query_by_did / query_by_field / count_by_collection) — server-side indexed view queries |
| `errors` | Error hierarchy (EtzhayyimSdkError base) |

## Quick start

```python
from etzhayyim_sdk import mst_projector

# Query indexed view (server-side filter via mst-projector)
result = await mst_projector.query_by_collection(
    collection="com.etzhayyim.shinka.heartbeat",
    limit=50,
)
for record in result["records"]:
    print(record)

# Count records in a collection
count_result = await mst_projector.count_by_collection(
    collection="com.etzhayyim.shinka.heartbeat",
)
print(f"Total records: {count_result['count']}")

# Query by author DID
records_by_did = await mst_projector.query_by_did(
    did="did:plc:abc123",
    collection="com.etzhayyim.shinka.kyumeiSignal",
    limit=100,
)

# Query by field value
field_results = await mst_projector.query_by_field(
    collection="com.etzhayyim.shinka.heartbeat",
    field_name="nodeName",
    field_value="levi",
)
```

## Environment variables

| Var | Default | Purpose |
|---|---|---|
| `ETZHAYYIM_MST_PROJECTOR_URL` | `http://simeon.local:8765` | mst-projector base URL |

## Install

```bash
uv pip install -e .
# or:
pip install -e .
```

Dependencies in `pyproject.toml`:
- `httpx>=0.24.0` (async HTTP client)
- `websockets>=12.0` (WebSocket support, future use)

## Tests

```bash
cd 20-actors/etzhayyim-sdk-py
uv run pytest tests/ -v
```

All tests use httpx.MockTransport and don't require network access.

## Architecture

The SDK follows a kotoba substrate pattern per ADR-2605172000. All state lives on:
- **AT Protocol MST** — mutable record store via PDS (shinka / joucho / yoro records)
- **IPFS** — immutable content + pinning
- **Base L2** — anchor contracts + land registry

No centralized databases, no commercial Kubernetes, no commercial GPU rental.

## References

- ADR-2605172000 — kotoba substrate
- ADR-2605214000 — Murakumo no-VKE mesh
- ADR-2605215000 — Murakumo-fleet-only inference
- ADR-2605215500 — mst-projector server-side filter
