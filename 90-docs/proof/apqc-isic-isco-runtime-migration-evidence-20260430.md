# APQC / ISIC / ISCO Runtime Migration Evidence

Date: 2026-04-30

The APQC, open-isic, and open-isco runtime surface has been migrated to the shared pyzeebe + LangGraph + UDF pattern.

| Project | BPMN | pyzeebe tasks | UDF helpers | Legacy runtime |
|---|---:|---:|---:|---|
| APQC | 3/3 | 3/3 | 2/2 | 295/295 retired |
| open-isic | 4/4 | 4/4 | 2/2 | CF Worker archived |
| open-isco | 2/2 | 2/2 | 3/3 | legacy appview archived |

APQC deployment evidence:

| Check | Result |
|---|---:|
| Worker | `kotodama-kyb3proj` |
| Version | `bc9113f2-0322-43db-a9e8-0f67786b17e4` |
| Route | `kyber-projector.etzhayyim.com/*` |
| DID document | `did:web:kyber-projector.etzhayyim.com` |
| APQC L1 actors | 13/13 active |
| APQC sub-processes | 183/183 registered |
| Kyber BPMN catalog tasks | 28 bound |
| Live BPMN E2E | `bpmn-9-trial-balance` -> `ocel-1777525877381-2` |
| APQC 9.0 events today | 1 |

APQC OCEL events are written directly to `vertex_apqc_event` through the deployed Worker Hyperdrive binding and read back through `listActivities`, `getActivity`, and `getApqcCoverage`. APQC actor status still bootstraps idempotently before read so coverage does not depend on graph consumer flush timing.

ISIC / ISCO runtime evidence:

| Check | Result |
|---|---:|
| ISIC classify entity | `2520` -> `f63e0e0a1ed6fcc5c80226b6` |
| ISIC classification edge | 1 row read back |
| ISIC concordance | `NAICS:332992` exactMatch |
| ISCO classify worker | `2512` -> `d83d798409d6171438dfce53` |
| ISCO classification edge | 1 row read back |
| ISCO concordance | `SOC:15-1252` exactMatch |

The ISIC / ISCO pyzeebe handlers write through `kotodama.db_sync` to Kotoba/Datomic. Idempotency is implemented with SELECT-before-INSERT because Kotoba/Datomic rejects `ON CONFLICT` in this path.

Runtime evidence is tracked in `90-docs/proof/apqc-isic-isco-runtime-migration-evidence-20260430.json`.

Verification commands:

```bash
cd 40-engine/kotoba/crates/kotoba-kotodama/py
pytest -q tests/test_open_isic_apqc_primitives.py

cd ../../..
npm run lint:bpmn:manifest
npm run lint:bpmn:coverage
npm run lint:bpmn:worker-tasks
git diff --check
```
