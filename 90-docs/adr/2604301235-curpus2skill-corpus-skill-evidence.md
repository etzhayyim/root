---
id: adr-2604301235-curpus2skill-corpus-skill-evidence
doc_type: adr
title: curpus2skill — corpus to skill evidence extraction
status: accepted
date: 2026-04-30
topic: talent
---

# ADR-2604301235 — curpus2skill corpus → skill evidence extraction

## Context

Repo-wide skill data already exists as ESCO-backed `vertex_skill`,
`edge_occupation_skill`, and `edge_skill_skill`. Corpus data also exists in
multiple actors (`legal-corpus`, `houbun`, domain knowledge chunks), but there
was no common path to connect corpus text to canonical skills.

The risk is creating duplicate or low-quality skills directly from corpus text.
The first repo-wide integration therefore records evidence edges only. Human or
model-reviewed promotion of novel candidates remains a separate workflow.

## Decision

Introduce `curpus2skill` as a conservative extraction pass:

- Canonical skill nodes remain `vertex_skill` (ESCO-first).
- Extractor output is `edge_corpus_skill_evidence`.
- Each run is recorded in `vertex_corpus_skill_extraction_run`.
- Input corpus sources must be public/plaintext and must skip `signal:v1:*`.
- Initial matching is deterministic lexical scoring over skill labels and
  alt-labels. Embedding/LLM matching may be added after baseline precision is
  measured.

## Schema

Migration:

- `30-graph/graph-schema/migrations/20260430400000_corpus_skill_extraction.ts`

Tables:

- `vertex_corpus_skill_extraction_run`
- `edge_corpus_skill_evidence`

The evidence edge stores:

- `corpus_table`, `corpus_vertex_id`
- `skill_id`
- `score`, `match_kind`
- short `evidence_text` span
- `source_actor_did`, `source_license`
- `extraction_run_id`

## Tooling

Operator script:

```bash
node 70-tools/scripts/curpus2skill.mjs --list-sources
node 70-tools/scripts/curpus2skill.mjs --source legal-corpus --limit 100 --dry-run
node 70-tools/scripts/curpus2skill.mjs --source houbun-article --min-score 0.82
```

Initial sources:

- `legal-corpus` → `vertex_legal_corpus_document`
- `houbun-article` → `vertex_houbun_article`
- `domain-knowledge` → `vertex_domain_knowledge_chunk`

## Guardrails

- No private/PII corpus extraction in this phase.
- No auto-creation of `vertex_skill`.
- No writes to AT Repo; graph evidence only.
- Evidence rows are idempotent by stable edge id:
  `(corpus_table, corpus_vertex_id, skill_id, match_kind)`.
- Default threshold is intentionally high (`0.78`) and should be tuned with
  sampled precision before enabling large backfills.

## Follow-up

1. Add BPMN wrapper only after the operator script has sampled precision.
2. Add candidate skill staging table if evidence shows high-value non-ESCO
   terms.
3. Add embedding rerank (`bge-m3` or existing vector project tables) after the
   lexical baseline is measured.
