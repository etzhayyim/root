# Wave Bridges (BPMN-as-actor binding-extension)

ADR-0056 BPMN-as-actor wave generators. Each `gen{N}.py` produces:
- `00-contracts/bpmn/com/etzhayyim/<actor>/*.bpmn` (canonical, in-repo)
- `00-contracts/lexicons/com/etzhayyim/apps/<lexApp>/*.json` (canonical, in-repo)
- `bind{N}.sql` (NSID → BPMN process_id binding INSERT for `vertex_bpmn_lexicon_binding`)

Older waves (W1-W98) also created `w{N}_{1..5}.sql` DDL for `vertex_open_*` tables.

## Apply pattern

1. `python3 gen{N}.py` — writes BPMN + lexicon files into `00-contracts/`
2. `for slug in <slugs>; do python3 70-tools/scripts/contract/sync-bpmn-actors.py --apply --only $slug; done` — registers `vertex_bpmn_process_def`
3. `psql $PGURL -f bind{N}.sql` — registers `vertex_bpmn_lexicon_binding`
4. F5 watcher (30s) deploys to Zeebe → `POST /xrpc/{nsid}` live

## Status (W123 landed 2026-04-25)

- 1387 active bindings
- W99-W123 = binding-extension only (no DDL) on existing aggregator tables, post incident_2026_04_25 RW recovery
- W98 IN ministries DDL blocked at RW scale ceiling — strategy: extend existing tables via NSID + bureau/action_kind enum
