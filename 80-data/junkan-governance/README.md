# junkan-governance — global citizen↔state asymmetry dataset

DataLad/IPFS-substrate dataset (ADR-2605241500) for the **junkan 循環**
analysis-only societal-systems-dynamics observer (ADR-2605290927), applied to one
question:

> **全世界の政府で、国民と政府を構造的に不均衡にしている具体的な法律・制度・思想・
> 価値観は何か。** Which concrete laws / institutions / doctrines / values worldwide
> widen (or narrow) the structural asymmetry between citizens (国民) and the state
> (政府)?

Each instrument records — as **on-the-record public facts** — the law/institution,
**who established it** (`:enactor`, 誰が定めたか — institutional / public-historical
bodies, never private individuals, per G6), the **circumstances of its
establishment** (`:origin`, 経緯), and the **related parties** (`:stakeholders`,
関係者). junkan then reads off, as **disclosed hypotheses (G5, never proven
causation)**, which feedback loops are spinning 好循環/悪循環 and the Meadows
leverage candidates.

## Source of truth

The canonical substrate lives with the actor (clj-native, kotoba-Datom-native):

- `orgs/etzhayyim/com-etzhayyim-junkan/data/ontology/ontology.junkan-gov.edn` — EAVT schema, enums, the 5
  asymmetry stocks, canonical structural loops, Meadows levels, negative space.
- `orgs/etzhayyim/com-etzhayyim-junkan/data/seed/seed.governance-asymmetry.edn` — the global instrument
  seed (grows each `/loop` iteration).
- `orgs/etzhayyim/com-etzhayyim-junkan/src/junkan/methods/analyze.cljc` — the analysis-only read-off.

## Files here (generated; do not hand-edit)

| file | what |
|---|---|
| `governance-asymmetry.datoms.kotoba.edn` | the findings as append-only EAVT datoms (instruments + derived stock regimes + loop hypotheses) |
| `findings-ledger.kotoba.edn` | a content-addressed single-tx ledger snapshot (commit-DAG; `:tx/cid` is reproducible byte-for-byte from the seed) |
| `report.md` | the rendered sober, non-eschatological read-off (G7) |
| `SCORECARD.md` | generated coverage + integrity + read-off digest (`methods/scorecard.cljc`) |
| `ingest-provenance.json` | regeneration provenance |

Regenerate everything deterministically from the actor substrate:

```bash
bb orgs/etzhayyim/com-etzhayyim-junkan/run_tests.bb            # 33 tests green
bb --classpath orgs/etzhayyim/com-etzhayyim-junkan/src orgs/etzhayyim/com-etzhayyim-junkan/src/junkan/methods/analyze.cljc   # report
# snapshot regeneration: see ingest-provenance.json
```

## Discipline (carried from the actor)

- **Analysis-only (G4)** — junkan has no outward channel; this is a read-only
  findings map. **NEVER a target-list, NEVER a country ranking-to-shame** (G7).
- **Hypothesis-only (G5)** — `:polarity`/`:magnitude`/`:confidence` and every
  regime/loop are junkan's disclosed estimates, not proven causation. The
  `law / year / enactor / origin` are on-the-record public facts.
- **Aggregate-only (G6)** — instruments + institutional enactors; no private
  individual modeling, no PII.
- **Map, not directive (G11)** — leverage points are candidates with uncertainty.

## License

Apache 2.0 + etzhayyim Charter Compliance Rider (see repo root `/CHARTER-RIDER.md`).
