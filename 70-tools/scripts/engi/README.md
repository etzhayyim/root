# engi — Engi-Organism Ontology tooling

Reference implementation + machine guard for the **Engi-Organism Ontology**
(ADR-2606011000): every entity is an `:organism`, every relation is a first-class
`:en` (縁) edge, ownership is recorded only as `:en/custodies` + `:en/grasping-load`
(取), never `:owns`.

## Files

| File | Purpose |
|---|---|
| `engi_ingest.py` | atproto follow/deps → `:organism`/`:en`/`:grasp` kotoba EDN, with the §4(2) floor enforced in code (fail-closed). Includes `from_atproto_records()` — the MST feed-membrane / firehose adapter (ADR-2605231902) |
| `grasp_render.py` | 取-concentration **aggregate render-spec** for kanae (ADR-2605302300): treemap of "who grasps", named-members-only + single anonymous latent node + k-anonymity collapse; surfaces top concentration for release |
| `retrofit_danjo_tadori.py` | reference transform: danjo `discrepancyObservation` + tadori `attributionFinding` → `:en` edges (design-first, gated; see `RETROFIT-danjo-tadori.md`) |
| `firehose_dryrun.py` | members-only **dry run** over the real `FirehoseEvent` shape from `50-infra/mst-projector` (ADR-2605231902): events → hydrate `subject` via injected `recordFetcher` (real run = `com.atproto.repo.getRecord`) → ingest → fail-closed floor check |
| `test_engi_ingest.py` | 10 floor-invariant tests (`python3 test_engi_ingest.py`) |
| `test_engi_pipeline.py` | 12 tests for the (c) adapter, (a) render, (d) retrofit, dry-run (`python3 test_engi_pipeline.py`) |

Total: **22 tests green**. All are proposed scaffold — nothing runs against production data.

## Pipeline (end to end)

```
mst-projector FirehoseEvent{did,collection,rkey,op,recordCid}   (ADR-2605231902)
  └─ firehose_dryrun.events_to_records  (filter graph collections, skip delete,
  │                                       hydrate subject via recordFetcher)
  └─ engi_ingest.from_atproto_records   → Follow edges
  └─ engi_ingest.ingest(member floor)   → :organism / :en(縁) / :grasp(取)  [F1–F4]
  └─ engi_ingest.validate_floor         → fail-closed if dirty (§4(2))
  └─ grasp_render.render_spec           → kanae 取-集中 treemap (aggregate-first)
        + retrofit_danjo_tadori         → danjo/tadori findings join the same :en graph
```

To go live: swap the injected `recordFetcher` for a real `getRecord` call and pass the
real member-DID set. The floor enforces members-only emission regardless of input.

## The floor (ADR-2606011000 §D9 + ADR-2605310100 §4(2))

Enforced by `validate_floor()`, fail-closed:

- **F1** `:owns`/`:owner` never appears in output — ownership is 取, recorded as custody.
- **F2** no non-member DID/handle in output — latent, non-ingressed organisms contribute
  to **anonymous aggregates only**. The text is scanned for `did:*` tokens, not just the
  result object.
- **F3** every `:en` edge has **both** endpoints claimed (members' own follow-graph is
  covenant-visible, ADR-2605310100 §1–§2).
- **F4** every `:en` edge carries `:en/grasping-load` + `:en/source :atproto-*`.

The graph thus grows **claimed-first** (members + their declared 縁) and **aggregate-first**
for the latent remainder — by construction, not by a privacy carve-out.

## `:owns`-crosswalk (existing attributes → engi vocabulary)

The repo today carries a few ownership-ish attributes. Under the ontology they become
`:en` edges (with 取-load) or stay as plain descriptive facts — but none reify `:owns`:

| Today | engi rewrite | grasping? |
|---|---|---|
| `:asset/company` (shibuya street asset installer/holder, ADR-2605312200) | `:en/kind :custodies` from the company-organism `:en/to` the asset-organism | yes — `:en/grasping-load` (infrastructure custody) |
| `:part/manufacturer` (giemon SBOM, ADR-2605312330) | `:en/kind :tends` from manufacturer-organism to part-organism | low — making, not grasping; load ≈ 0 |
| `:proc/title` / `:bom/title` (procurement/BOM document titles) | stays a descriptive string attribute (a label, not a relation) | n/a |
| land "owner" (any future) | `:en/kind :custodies` + `:en/tree-of-life-custody? true` (ADR-2605192245) | custody under Trust, **never title** |

Retrofitting these is **gated** (ADR-2606011000 §D9: §D1–§D4 need Council Lv7+); this
crosswalk is the design of record, not an executed migration.

## Status

Proposed scaffold. Does not run against production data; binds nothing until ratification.
Inference, when wired, is Murakumo-only (ADR-2605215000). Substrate is the kotoba Datom
log (ADR-2605312345).
