# medical-coverage-ingester

Kubernetes CronJob for draining healthcare coverage gaps through RisingWave.

The ingester writes canonical records into `vertex_repo_record`; coverage is
read from `mv_world_collection_coverage_live`. It keeps cursors as normal
`com.etzhayyim.apps.iryo.coverageCursor` records in `vertex_repo_record`, so repeated
runs continue until each target coverage row reaches `coverage_rate >= 1.0`.
Before the first write, the CronJob runs an RW health gate equivalent to
`70-tools/scripts/ingest/rw-health-gate.sh`: `rw_recovery_info`, two compute
pods warm for at least 60 seconds, and recent object-store/recovery logs must be healthy. If the
gate is red, the job exits 0 without writing and waits for the next schedule.
Writes keep `RW_IMPLICIT_FLUSH=false` by default. Hot-path flushes can block
when compute pods are recovering or object storage is throttled, so cursor and
coverage reads are allowed to converge on the next scheduled run. PubMed drains
at a conservative `PUBMED_RETMAX=20`, `BATCH_SIZE=20` until RisingWave DML
latency is consistently healthy; MCP-triggered runs can use `maxRecords` for
smaller probes.

This is a plain Kubernetes Python batch worker. It is not a Zeebe worker and it
does not run inside RisingWave as a Python external UDF. Zeebe can be added
later as the durable orchestrator, and RisingWave UDFs should stay focused on
deterministic scoring/enrichment near the data.

Default targets:

- `pubmed`: PubMed E-utilities -> `com.etzhayyim.apps.iryo.pubmedPaper`
- `clinical_trials`: ClinicalTrials.gov v2 -> `com.etzhayyim.apps.iryo.rinshou`
- `dsm`: public category-level DSM taxonomy metadata only -> `com.etzhayyim.apps.iryo.dsmCategory`
- `facilities_csv`: hardcoded CMS Provider of Services sources first, optional
  `FACILITY_CSV_URL` override for CSV/JSONL -> `com.etzhayyim.apps.iryo.shisetsu`

Deploy:

```sh
kubectl apply -k .
```

Run once:

```sh
kubectl -n risingwave create job medical-coverage-ingest-now \
  --from=cronjob/medical-coverage-ingester
```

Required secret:

```sh
kubectl -n risingwave create secret generic medical-coverage-ingester-secrets \
  --from-literal=RW_DSN='host=risingwave.risingwave.svc.cluster.local port=4566 dbname=dev user=root'
```

Optional keys:

- `NCBI_API_KEY`

Facility coverage does not require URL secret configuration by default. The
ingester pages these public CMS Data API sources in order, writes each raw page
to B2 as gzipped JSONL, then writes canonical facility records into
`vertex_repo_record`:

- CMS Provider of Services - Clinical Laboratories
- CMS Provider of Services - Internet Quality Improvement and Evaluation System
- CMS Provider of Services - Quality Improvement and Evaluation System

Default B2 location:

- bucket: `etzhayyim-nats`
- prefix: `medical-sources/iryo-shisetsu/{source}/{YYYY}/{MM}/{DD}/...jsonl.gz`
- raw-only cursor: `medical-sources/iryo-shisetsu/_cursors/facilities_csv.json`

`medical-facility-raw-archiver` is the B2-first CronJob. It runs with
`FACILITY_RAW_ONLY=true`, does not connect to RisingWave, and can continue while
RisingWave DDL/DML is paused. `medical-coverage-ingester` remains the canonical
RisingWave writer and should only be resumed after RW health gates and the
Kysely datasource schema are green.
The raw archiver uses 5,000-row pages so the 676k-row CMS Clinical Laboratories
source drains to B2 in roughly 11-12 hours at the default 5-minute cadence.

`medical-facility-b2-replayer` is the B2 -> RisingWave canonical writer. It
runs with `FACILITY_REPLAY_FROM_B2=true`, reads the raw JSONL.gz archive, writes
`com.etzhayyim.apps.iryo.shisetsu` records, and tracks replay progress in:

- `medical-sources/iryo-shisetsu/_cursors/facilities_replay.json`

It is intentionally slower than the raw archiver: 100-row replay batches keep
RisingWave DML pressure bounded while the B2 backlog continues to grow.

Lineage/progress schema is defined in
`30-graph/graph-schema/migrations/20260425190000_medical_data_source_ingest_spine.ts`:

- `vertex_medical_data_source`
- `vertex_medical_source_asset`
- `vertex_medical_ingest_cursor`
- `vertex_medical_ingest_run`
- `edge_medical_source_targets_collection`

For GitOps, copy `secrets-template.yaml` to a SOPS/SealedSecret/ExternalSecret
managed file outside the plain-text path, then sync this directory with
Argo CD or Flux.
