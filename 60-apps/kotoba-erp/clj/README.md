# kotoba-erp — Clojure port (ADR-2606280030)

Faithful clj/cljc port of the four clean-architecture ERP modules under
`60-apps/kotoba-erp/` (FI / MM / SD / CRM). Each Python namespace maps to an
idiomatic `.cljc` namespace (plain fns, records, `ex-info` for errors), per the
repo rule "Operational code = clj/bb over the kotoba Datom log".

## Layout (Clean Architecture preserved)

```
src/kotoba_erp/
  graph.cljc                 ; StateGraph runner — port of the kotoba_langgraph shim
  store.cljc                 ; injectable store seam (KQE assert/get + KSE publish)
  util.cljc                  ; portable helpers (abs*, now-iso)
  fi/  entities | repository | use_cases/{post_journal,process_event} | app
  crm/ entities | repository | use_cases/close_opportunity            | app
  mm/  entities | repository | use_cases/receive_goods                | app
  sd/  entities | repository | use_cases/billing                     | app
test/kotoba_erp/ {graph,fi,crm,mm,sd}_test.cljc
```

| Python | Clojure |
|---|---|
| `kotoba_langgraph` `StateGraph`/`START`/`END`/`compile`/`invoke` | `kotoba-erp.graph` (pure, in-repo shim) |
| `wit_world.kqe` (`assert_quad`/`get_objects`) + `kse.publish` | `kotoba-erp.store` injectable map-of-fns seam |
| `@dataclass` SAP/SFDC models + business-rule methods | `defrecord` + plain validation fns |
| use-case node fns (`state -> dict`) | use-case node fns (`state -> map`, merged) |
| `cbor2` wire encode/decode | handled at the WASM host edge; in-process carries decoded clj data |

## Run

```bash
bb run_tests.clj    # or: bb test   → 15 tests / 54 assertions green
```

## Substrate boundary

The repository adapters speak only to the injected `store` seam. The default
`mem-store` reproduces the python `_KqeMock` read fixtures for dev/test; a live
deploy injects a store whose fns write the canonical **kotoba Datom log** (EAVT
quads, ADR-2605262130). RisingWave/Postgres are forbidden and never appear here.

## Coexistence (do not break the deployed app)

The Python modules are compiled into live PyWasm components (`*/app.wasm`,
~19 MB each) and are **retained** — this port is an additive clj twin, not a
replacement. `py_removed = 0`. No deploy manifest was edited.
