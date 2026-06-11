# Natural Person Latent Entity Backend Design - 2026-04-30

## Purpose

`natural-person` needs a stable split between:

- public/searchable actors
- non-federating PII and hidden cohorts
- all-human latent entities that may eventually fission into individual actors

The current live graph already has the schema for `vertex_latent_entity`, `vertex_cohort_actor`, and `edge_entity_cohort_link`, but the LDA/latent inference tables are empty. This document fixes the path contract and the backend processing shape before enabling high-volume inference.

## Entity Model

| Layer | Meaning | Kotoba/Datomic | Search |
|---|---|---:|---:|---|
| Cohort | Anonymous population bucket or aggregate | yes | only explicit public cohort actors |
| Latent entity | Probable individual or unobservable entity | frontier only | no |
| Individual actor | Fissioned DID/handle/key actor | yes | yes, if public |

All-human latent entity scale can be tens of billions. The logical graph treats each latent entity as a vertex. Materialization into Kotoba/Datomic must be cursor-based, resumable, and rate-limited; it must not run as a single unbounded bulk insert.

## Path Contract

### Cohort Person

Record path:

```text
at://did:web:natural-person.etzhayyim.com/com.etzhayyim.apps.naturalPerson.cohortPerson/{rkey}
```

Current cohort DID patterns:

```text
did:web:natural-person.etzhayyim.com:{cohort_hash}
did:web:natural-person.etzhayyim.com:deceased:{era}:{cause_cluster}
```

Registry path:

```text
at://did:web:natural-person.etzhayyim.com/com.etzhayyim.apps.naturalPerson.cohortActor/{rkey}
```

### Latent Entity

Vertex path:

```text
at://did:web:coverage.etzhayyim.com/com.etzhayyim.apps.coverage.latentEntity/{entity_hash}
```

Natural-person scoped DID-like identifier:

```text
did:web:natural-person.etzhayyim.com:latent:{entity_hash}
```

`entity_hash` must be deterministic and versioned:

```text
blake3("np:latent:v1|{cohort_hash}|{source_family}|{evidence_key_or_ordinal}").slice(0, 32)
```

### Fissioned Individual

For natural-person managed records:

```text
did:web:natural-person.etzhayyim.com:person:{person_hash}
```

For agent-only reverse identity actors:

```text
did:plc:{minted}
handle: agent-{nano}.etzhayyim.com
```

Fission must write lineage back to the cohort:

```text
edge_entity_cohort_link:
  src_vid = vertex_latent_entity.vertex_id
  dst_vid = vertex_cohort_actor.vertex_id or vertex_natural_person_cohort_person.vertex_id
```

## Hash Rules

`cohort_hash` must include every semantic dimension that changes identity. The current deceased cohort seed has a collision risk because the hex prefix is dominated by `era`. Replace with:

```text
blake3("np:cohort:v1|{country}|{era}|{vital_status}|{death_cause_icd10}|{dimension_string}").slice(0, 24)
```

Never use truncated plain hex of a dimension string as the hash source for production cohort identity.

## Visibility Classes

`sensitivity_ord = NULL` is not public. It is `unclassified`.

| Class | Meaning | Suggested `sensitivity_ord` | Federates | Search |
|---|---|---:|---|---|
| `public_searchable` | Public actor/profile/person fact | 0 | yes | yes |
| `internal_aggregate` | Non-PII internal aggregate | 1 | no by default | no |
| `confidential` | Business-sensitive or restricted source | 2 | no | no |
| `restricted_individual` | Live individual/person record | 3 | no | no |
| `non_federating_pii` | PII/cohort identity backend state | >=100 | no | no |
| `unclassified` | Missing classification | NULL | no | no |

Before search counts can be trusted, all `business_person` and `natural_person` rows need explicit classification.

## Backend Topology

### BPMN / Zeebe

BPMN owns orchestration, retries, audit events, and gates:

```text
naturalPerson.reconcileVisibility
  normalize data_classification and sensitivity_ord

naturalPerson.expandCohortUniverse
  census/source stats -> cohort partitions -> latent entity plan

naturalPerson.materializeAllLatentEntities
  cohort estimated counts -> resumable cursor -> individual latent vertices

coverage.inferLdaSignals
  observable graph -> signal vocabulary

coverage.inferLdaTopics
  train/update topic models

coverage.inferLdaEntities
  topic consensus -> latent entity frontier

coverage.inferFission
  posterior + policy + k-anonymity checks -> actor fission

naturalPerson.purgeOrSuppress
  GDPR/APPI delete and suppression propagation
```

### Python Workers

Python workers do the high-volume backend work:

```text
shard planner
  partitions by cohort_hash prefix, country, era, birth_year, source_family

latent entity generator
  deterministic entity_hash generation

inference updater
  evidence_count, existence_probability, viewpoint_consensus, posterior

hot projector
  upsert only frontier/fission-candidate rows to Kotoba/Datomic
```

### LangGraph Service

LangGraph handles long-running state and policy decisions for the active frontier only:

```text
observed
  -> latent
  -> candidate
  -> policy_review
  -> fission_ready
  -> fissioned
  -> suppressed
```

Nodes:

```text
collect_evidence
score_posterior
pii_policy_check
cohort_k_anonymity_check
consent_or_public_figure_check
fission_decision
create_actor
audit_emit
```

LangGraph must not iterate the full all-human universe. It consumes a frontier queue emitted by Python workers and BPMN.

## Storage Plan

Kotoba/Datomic:

```text
vertex_cohort_actor
vertex_natural_person_cohort_person
vertex_natural_person_latent_materialization_cursor
vertex_latent_entity
edge_entity_cohort_link
edge_entity_evidence              -- bounded active evidence
vertex_bpmn_activity_event
vertex_ocel_event
```

Planned latent rows need enough information to replay projection:

```text
entity_hash, cohort_hash, source_family, evidence_key, existence_probability,
status, sensitivity_ord, created_at, model_version
```

## Activation Sequence

1. Run the audit script and save a baseline report.
2. Fix `cohort_hash` generation for new deceased cohorts.
3. Add `naturalPerson.reconcileVisibility` BPMN and worker task.
4. Backfill explicit `sensitivity_ord` for `business_person` and `natural_person`.
5. Enable `naturalPerson.materializeAllLatentEntities` cursor table.
6. Start rate-limited latent vertex materialization into `vertex_latent_entity`.
7. Enable LangGraph fission review with fission disabled.
8. Enable `coverage.inferFission` only for test cohorts with `fission_enabled=true`.

## Operational Guardrails

- No unbounded full all-human latent entity load into Kotoba/Datomic; use resumable cursors and bounded batches.
- No `NULL` classification treated as public.
- No individual actor fission without cohort lineage.
- No fission on LLM-only evidence; require independent graph posterior.
- No live individual data in AT Repo; only hash/cohort assignment may federate.
