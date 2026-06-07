---
id: adr-2604300135-hume-distillation-artifact-persistence
title: Hume Distillation Artifact Persistence to IPFS and Kotoba/Datomic
status: active
doc_type: adr
topic: hume-distillation
authoritative: true
last_verified: 2026-04-30
authoritative_for:
  - hume-distillation-artifact-persistence
  - hume-student-training-artifact-indexing
  - hume-teacher-label-durable-storage
related:
  - adr-2604261936-ipfs-self-hosted-vultr-b2
  - adr-2604261900-kotoba-ddl-backfill-path-topology
  - adr-2604262359-kotoba-multimodal-vector-search-topology
supersedes: []
superseded_by: []
---

# Context

Hume Expression Measurement is being used as the teacher for etzhayyim's
multimodal expression student models while the Hume API remains available. The
distillation runs produce several durable artifacts:

- teacher-labeled JSONL;
- SFT JSONL for LLM-style supervised tuning;
- media/text run manifests;
- bootstrap student model JSON;
- training report JSON;
- per-example normalized expression labels.

Keeping those files only in a repo or worker `/tmp` is not sufficient. The
training corpus must survive pod rotation, be content-addressable, and be
queryable by future trainers and audit tools. At the same time, the artifacts
can be larger than normal graph rows and should not be stored as raw payloads
inside Kotoba/Datomic.

# Decision

Persist Hume distillation artifacts using a two-store layout:

1. **IPFS body store**: artifact bytes are pinned to `ipfs.etzhayyim.com` via the
   self-hosted Kubo service. The returned CID is the authoritative artifact body
   address.
2. **Kotoba/Datomic index store**: searchable metadata is written to the existing
   `vertex_ingest_artifact` table. This avoids hot-path DDL and follows
   ADR-2604261900.

The current persistence implementation is:

- `60-apps/etzhayyim-project-hume/scripts/persist_hume_artifacts.py`
- `20-actors/magatama/py/src/pymagatama/primitives/ipfs_ingest.py`
- `20-actors/magatama/py/src/pymagatama/ingest/core.py`

For the first media run, the persistence manifest is:

- `60-apps/etzhayyim-project-hume/data/distillation/hume-media-audio-small-persistence-20260430.json`

The Kotoba/Datomic `run_id` is the Hume distillation run id:

- `hume-distill-media-20260430T012113Z`

Artifact kinds written to `vertex_ingest_artifact`:

| Kind | Count | Meaning |
|---|---:|---|
| `hume.distillation.teacher_labels_jsonl` | 1 | Teacher-labeled dataset JSONL |
| `hume.distillation.sft_jsonl` | 1 | LLM SFT JSONL derived from labels |
| `hume.distillation.manifest` | 1 | Distillation run manifest |
| `hume.student.model` | 1 | Bootstrap student model JSON |
| `hume.student.training_report` | 1 | Training evaluation report |
| `hume.distillation.example` | 6 | One content-addressed JSON object per teacher-labeled example |

The `props` column stores lightweight audit metadata such as dataset name,
filename, gateway URL, CID, modality, split, primary emotion, primary score,
and Hume teacher job id. Artifact payloads remain in IPFS.

# Consequences

- Hume distillation data is recoverable from `ipfs://` CIDs even if local repo
  artifacts or worker `/tmp` are deleted.
- Trainers can discover available artifacts through Kotoba/Datomic without loading
  large JSONL/model bodies into the database.
- The first implementation uses the existing ingest spine, so no Kotoba/Datomic DDL
  was required on the hot path.
- Duplicate rows are possible if an artifact is reclassified under a new
  `artifact_kind`; cleanup must be explicit and audited.
- Future dedicated Hume tables may be added through the DDL queue if query
  requirements outgrow `vertex_ingest_artifact`.

# Alternatives Considered

- Store full JSONL/model bodies in Kotoba/Datomic. Rejected because it mixes large
  artifact storage with query indexes and increases write-path pressure.
- Store only in IPFS. Rejected because trainers need searchable run/dataset
  metadata, row counts, modalities, and primary labels.
- Add dedicated `vertex_hume_*` tables immediately. Deferred because the
  existing ingest artifact table already provides the required durable index
  without new DDL.

# References

- `60-apps/etzhayyim-project-hume/scripts/persist_hume_artifacts.py`
- `60-apps/etzhayyim-project-hume/training/student-training-manifest.json`
- `50-infra/vultr/ipfs/CLAUDE.md`
- `90-docs/adr/2604261936-ipfs-self-hosted-vultr-b2.md`
- `90-docs/adr/2604261900-kotoba-ddl-backfill-path-topology.md`
