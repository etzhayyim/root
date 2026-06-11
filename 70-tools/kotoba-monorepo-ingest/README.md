---
id: doc-kotoba-monorepo-ingest-readme
title: "kotoba-monorepo-ingest — ADR corpus → kotoba quad NDJSON tool"
status: active
doc_type: reference
topic: kotoba-monorepo-projection
authoritative: true
last_verified: 2026-05-28
authoritative_for:
  - kotoba-monorepo-ingest usage + invariants
related:
  - adr-2605281700-kotoba-content-addressed-monorepo-projection
  - adr-2605281800-kotoba-monorepo-projection-r1-adr-corpus-ingest
supersedes: []
superseded_by: []
---

# kotoba-monorepo-ingest

R1 deliverable of ADR-2605281700 (kotoba content-addressed monorepo projection). Walks `90-docs/adr/*.md`, parses YAML front matter, computes IPFS CIDs via local Kubo, emits a kotoba-shaped NDJSON quad stream conforming to the R0 schema.

## Quick start

```bash
# Requires: PyYAML, local Kubo daemon on 127.0.0.1:5001
pip install pyyaml
python3 70-tools/kotoba-monorepo-ingest/ingest_adr.py
# → wrote 90-docs/_registry/kotoba-quads.ndjson

# Schema-only smoke (no IPFS daemon needed)
python3 70-tools/kotoba-monorepo-ingest/ingest_adr.py --dry-run
```

## Output

NDJSON, 1 row per quad:

```json
{"graph": "kotoba:graph:etzhayyim-root", "subject": "adr:2605281700", "predicate": "hasCid", "object": "bafkrei..."}
{"graph": "kotoba:graph:etzhayyim-root", "subject": "adr:2605281700", "predicate": "status", "object": "proposed"}
{"graph": "kotoba:graph:etzhayyim-root", "subject": "adr:2605281700", "predicate": "dependsOn", "object": "adr:2605262130"}
```

## Constraints (per ADR-2605281800)

- IPFS endpoint locked to `127.0.0.1:5001` (local Kubo); no commercial PSA (ADR-2605215000)
- Subject IRI scheme: `adr:<10-digit-id>` only (ADR-2605281700 §5.2)
- No kotoba server write (R1.5+ scope); NDJSON is the deliverable

## Not in scope here

- Lexicon / deps.toml / Roster / CLAUDE.md Status ingest (R2-R4, separate ADRs)
- `quad.create` XRPC POST + CACAO signing (R1.5)
- Markdown body section extraction (R5+)
