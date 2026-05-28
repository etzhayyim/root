# kotoba

**Content-Addressed Distributed Datalog Database**

```
KOTOBA ≝ Datom[CID/T] × EAVT[KSE Topic] × Pregel[BSP] × Datalog[Δ]
          × CACAO × AT Protocol × LLM/Weight × WASM/WIT
```

Kotoba is a distributed, content-addressed knowledge graph database designed for decentralized AI agent systems. It combines Datomic-style immutable datoms, Pregel BSP graph computation, Signal Protocol end-to-end encryption, and WASM Component Model execution.

## Crates

| Crate | Role |
|---|---|
| `kotoba-core` | CIDv1 blake3, KAIS 8-bit frame, Prolly Tree |
| `kotoba-kse` | Journal, Topic, Shelf, Vault (Knowledge Store Engine) |
| `kotoba-kqe` | Datalog engine, Arrangement (EAVT/AEVT/AVET/VAET), Delta, MV |
| `kotoba-dht` | Source Chain, Warrant, Neighborhood (DHT) |
| `kotoba-net` | libp2p QUIC/Noise/GossipSub |
| `kotoba-auth` | CACAO chain verification, DID Document |
| `kotoba-graph` | Quad API, SPARQL→Datalog, Commit DAG |
| `kotoba-vm` | Invoke/Result ChainEntry, CALL_FOREIGN bridge |
| `kotoba-llm` | Weight blob (FP8), LoRA Delta, KV-cache, inference, WebGPU training |
| `kotoba-runtime` | WASM Component Model host: WasmExecutor + UdfExecutor + WIT bindings |
| `kotoba-store` | BlockStore: Memory, Sled, S3; BudgetedBlockStore LRU; TieredBlockStore hot/cold |
| `kotoba-store-web` | Browser IndexedDB block store (wasm32) |
| `kotoba-crypto` | AEAD (AES-256-GCM), HKDF, key wrap |
| `kotoba-signal` | Signal Protocol (X3DH + Double Ratchet + MLS) |
| `kotoba-ingest` | Gmail OAuth2 poll + E2E encrypt → QuadStore |
| `kotoba-server` | XRPC / MCP endpoints |
| `kotoba-guest` | WASM guest SDK (WIT bindings for kotoba nodes) |

## Key Properties

- **Content-addressed**: Every value identified by CIDv1 (blake3)
- **Immutable datoms**: Datomic-style EAVT with Delta (assert/retract)
- **4-index arrangement**: EAVT / AEVT / AVET / VAET for O(1)–O(log n) access patterns
- **Prolly Tree storage**: Deterministic, hash-consistent B-tree over content-addressed blocks
- **Distributed Pregel**: BSP graph computation across nodes via libp2p
- **AT Protocol native**: Quad store backed by AT Protocol commit DAG and JetStream
- **WASM runtime**: Execute arbitrary graph logic as WASM Component Model guests
- **E2E encryption**: Signal Protocol + CACAO auth for consent-gated data

## Performance (aarch64, 2026-05-25)

| Operation | Throughput |
|---|---|
| EAVT point lookup | ~180 ns |
| 2-hop graph traversal | ~748 ns |
| QuadStore batch insert | 252K–390K quad/s |
| 1M quad loadtest | 290K q/s, 840 MB RSS |

## Python siblings (`py/`)

Pure-Python packages that ride on top of the Rust workspace:

| Package | Path | Role |
|---|---|---|
| `kotoba-langgraph` | `py/kotoba_langgraph/` | LangGraph-compatible graph engine compiled to WASM Components via `componentize-py` (stdlib-only) |
| `kotoba-murakumo` | `py/kotoba_murakumo/` | Modal-compatible facade for the etzhayyim Murakumo Mac mini fleet — Python decorators dispatch to LiteLLM gateway / EVO-X2 / own-node Ollama per `50-infra/murakumo/fleet.toml`; never to commercial GPU rental. R1.3 adds the mKOTO economy + Modal-billing-parity (spend caps, pre-flight estimate, post-call billing records). See `py/README.md` + ADR-2605282000 (facade) + ADR-2605282100 (economy). |

Each Python package keeps its own `pyproject.toml`; there is no Python
workspace umbrella at the kotoba level. `py/README.md` is the index.

## Build

```bash
cargo build --workspace
cargo test --workspace
cargo bench -p kotoba-kqe --bench arrangement
cargo bench -p kotoba-graph --bench quad_store

# Python siblings (independent; see py/README.md)
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest py/kotoba_murakumo/tests/
```

## License

Apache-2.0 — see [LICENSE](LICENSE)
