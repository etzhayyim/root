# MATURITY — etzhayyim-project-explorer

Scorecard for the apex SPA (ADR-2606201610). Updated by the `/loop` coverage +
maturity pass. Legend: ✅ done · 🟡 partial · ⏳ planned.

## Capability matrix

| Area | Status | Evidence |
|---|---|---|
| **Organism view** (Tree-of-Life, A(t)=⟨M,D,C,P,G⟩ browser-computed, pulse, joucho) | ✅ | `organism/*`; `aliveness_test`, `coverage_test`; visual loop PASS |
| **Explorer view** (kotoba CommitDag verify, EAVT browser, Datalog query) | ✅ | `chain/*`; `datom_test` (byte-compatible CID verify of a real committed log) |
| **Nodes view** (分散状況 mesh from kotoba EAVT query, not JSON) | ✅ | `nodes/*`; `nodes_query_test` (104 cells queried from vitals EAVT) |
| **Actor census** (tiered, queried from a kotoba Datom log) | ✅ | `state` `:census`; unispsc 18342 etc. surfaced |
| **Agent-centric registration** (did:key, signed genesis source-chains) | ✅ | `actor-registry/`; `register_test`, `agent_test` |
| **Validating membrane** (CACAO member vouch + witness quorum + DHT) | ✅ | `membrane_test`; rejects no-vouch / duplicate-handle |
| **Transit wire** (transit+json query/sync, Datomic-client standard) | ✅ | `wire.cljs`, `wire_test`; CID stays canonical-JSON, on-disk stays EDN |
| **Live Datom tail** (kotoba node XRPC sync.subscribe → transit+json SSE) | ✅ | `sync_node.clj`; end-to-end transit decode against the live node |
| **Visual react loop** (computer-use-clj + Ollama gemma vision) | ✅ | `visual-test/`; 3/3 PASS on the real app |
| Browser-side serverless / content-addressed (no backend in the app) | ✅ | all reads CID-verified or static; IPFS-portable |
| IPFS pin of the build | ⏳ | content-addressed by construction; pinning not wired |
| Apex cut-over (binding flip YORO→EXPLORER) | ⏳ | preview-first; deploy-time, see ADR |
| kotoba-wasm raw-block CAR/Prolly decode | ⏳ | R1; `kotoba.datom` tx-log path is live |
| Live DHT gossip + on-chain SBT roster binding | ⏳ | quorum/DHT computed deterministically in the PoC |

## Tests

- **cljs**: 63 tests / 198 assertions, 0 failures (`npm test`).
  Namespaces under test: aliveness, datom, nodes-query, vitals-parse, agent,
  wire, coverage (router, graph, datom edges, aliveness scoring), coverage2
  (bonsai SVG, aliveness liveness + C/P/G read-path, parse-log comment handling),
  coverage3 (re-frame state: resource lifecycle, bounded live-tail buffer,
  chain query + block-inspector state), coverage4 (derived /nodes cells+summary
  classify path, census parse+verify+query, force-layout bounds), coverage5
  (multi-tx commit-DAG prev-linking + tamper localisation, base58 decoder math),
  coverage6 (aliveness band boundaries, compute empty/single-run edges),
  coverage7 (data-base/url + live sync-base under a synthetic globalThis.window),
  coverage8 (ui loading-gate branches + staleness-badges hiccup render),
  coverage9 (full reagent SSR render of all three views via reagent.dom.server),
  coverage10 (data fetch I/O wrappers — fetch-text/json/edn/block-bytes/root-pointer
  + non-ok error path — under a stubbed globalThis.fetch), coverage11 (live SSE
  decode-frame fallback: transit+json → JSON → raw).
- **clj** (`actor-registry/`): 13 tests / 38 assertions — did:key roundtrip,
  self-sign + witness, tamper detection, membrane (Sybil + duplicate rejection),
  base58 round-trip, kotoba-dht XOR neighbourhood, validate warrant reasons,
  sync-node cursor parsing + transit frame round-trip + Datom stream.
- **release build**: 0 warnings.
- **end-to-end**: visual react loop 3/3 PASS; live sync node transit frames
  decoded with keyword fidelity.

## Known gaps / next

1. Wire the sync node as a `bb` task under launchd, fronted by the apex Worker
   proxying the XRPC sync route (production form).
2. kotoba-wasm CAR/Prolly decode for `/kotoba/blocks/<cid>` + full kqe Datalog.
3. IPFS pin of the build; apex binding cut-over after preview verification.
4. **Unit coverage is saturated.** Pure logic, re-frame state, window-coupled
   `data`/`live`, `agent` Web Crypto, `ui`, the `data` fetch I/O wrappers (stubbed
   fetch), and **all three `*/view` namespaces** (full reagent SSR render) are
   covered — even the live SSE frame decode (`decode-frame`). The only paths left
   are the `EventSource`/`fetch` socket lifecycle itself and form-2 interactive
   handlers (hover/click) — exercised **end-to-end** by the visual react loop
   (`visual-test/`, real Chrome + gemma) and the live sync node. **Unit coverage
   is exhausted**; next maturity steps are the deploy-time items (1–3 above), not
   more tests.
