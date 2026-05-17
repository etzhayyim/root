---
id: adr-readme-etzhayyim-root
title: etzhayyim/root ADRs — Index and Placement Policy
status: active
doc_type: reference
topic: adr-readme
authoritative: true
last_verified: 2026-05-17
authoritative_for:
  - ADR index for etzhayyim/root
  - placement policy (which ADRs live here vs in vendor monorepo)
related:
  - 2605170900-etzhayyim-root-adr-canonical-home.md
supersedes: []
superseded_by: []
---

# etzhayyim/root ADRs — Index and Placement Policy

This directory is the **canonical home for ADRs about religious-corp open activities** operated by `etzhayyim`. Policy is established by **ADR-2605170900** (this directory) and **ADR-2605152100** (vendor monorepo).

## Placement matrix

| Scope | Canonical home | Examples |
|---|---|---|
| Open religious-corp activities (blockchain / baien / bpmn / lexicon / pregel / atproto / ameno / open-data / public governance) | **`etzhayyim/root/90-docs/adr/`** ← here | new open project designs, new public infrastructure, new open protocol specs |
| Source-control boundary | `gftdcojp/ai-gftd-apps-gftdcojp` (vendor historical) | ADR-2605152100, ADR-2605102200 |
| Vendor business (lawfirm / malak / akuma / finance / HR / lawfirm / kaisya / microsoft) | `gftdcojp/ai-gftd-apps-gftdcojp` (vendor) | ADR-2605151400, ADR-2605152000, ADR-2605151500 |
| Shared foundational | `gftdcojp/ai-gftd-apps-gftdcojp` (vendor historical), URL-linked from here | ADR-2604251830 Shannon-Optimal, ADR-2605091400 MCP-as-Cell-Membrane |

When in doubt: **new open-scope ADRs go here.** Don't dual-author across repos.

## ADRs in this directory

### Active

| ID | Title | Status | Date |
|---|---|---|---|
| [2605170900](./2605170900-etzhayyim-root-adr-canonical-home.md) | etzhayyim/root as canonical home for religious-corp open ADRs | active | 2026-05-17 |
| [2605171800](./2605171800-langgraph-mst-ipfs-l2-anchor-pipeline.md) | Artificial Organism Ecosystem — LangGraph Pregel → PostgresSaver → atproto MST → IPFS → Base L2 anchor pipeline | proposed | 2026-05-17 |

(Future ADRs added here as they're authored.)

## Foundational ADRs in vendor monorepo (URL-linked from here)

These ADRs originated in the vendor monorepo. They are **referenced** from etzhayyim/root ADRs but their canonical home remains in the vendor monorepo because they predate the org boundary.

### Architecture core

- [ADR-2604251830 Shannon-Optimal 8-Layer Architecture](https://github.com/gftdcojp/ai-gftd-apps-gftdcojp/blob/main/90-docs/adr/2604251830-shannon-optimal-layered-architecture.md) (CRITICAL — monorepo layout convention)
- [ADR-2605091400 MCP-as-Cell-Membrane / Lexicon Dual-Wire SSoT](https://github.com/gftdcojp/ai-gftd-apps-gftdcojp/blob/main/90-docs/adr/2605091400-mcp-as-cell-membrane-lexicon-xrpc-demotion.md)
- [ADR-2605080000 Distributed Cognitive Actor System 6-Layer](https://github.com/gftdcojp/ai-gftd-apps-gftdcojp/blob/main/90-docs/adr/2605080000-distributed-cognitive-actor-system.md)
- [ADR-2605080600 LangGraph Server + Granian L3 Runtime](https://github.com/gftdcojp/ai-gftd-apps-gftdcojp/blob/main/90-docs/adr/2605080600-langgraph-server-granian-l3-runtime.md)
- [ADR-2605082000 LangGraph Graph Definition as Data](https://github.com/gftdcojp/ai-gftd-apps-gftdcojp/blob/main/90-docs/adr/2605082000-langgraph-graph-definition-as-data.md)

### Bonsai cultivar metaphor

- [ADR-2605091300 Bonsai Cultivar Layer Above Myco-Yeast Substrate](https://github.com/gftdcojp/ai-gftd-apps-gftdcojp/blob/main/90-docs/adr/2605091300-bonsai-cultivar-layer-above-myco-yeast.md)
- [ADR-2605092000 Ecosystem-as-Model — Unified Multimodal FP8 Vector Substrate](https://github.com/gftdcojp/ai-gftd-apps-gftdcojp/blob/main/90-docs/adr/2605092000-ecosystem-as-model-unified-multimodal-fp8-vector-substrate.md)
- [ADR-2605092100 LoRA-per-Cell as MoE Expert with Cohort Fission](https://github.com/gftdcojp/ai-gftd-apps-gftdcojp/blob/main/90-docs/adr/2605092100-lora-per-cell-moe-expert-cohort-fission.md)
- [ADR-2605092200 Continuous Metabolic Training](https://github.com/gftdcojp/ai-gftd-apps-gftdcojp/blob/main/90-docs/adr/2605092200-continuous-metabolic-training.md)

### Open ML / inference

- [ADR-2605092350 baien — 1-bit Multimodal Edge / Browser / CPU Design](https://github.com/gftdcojp/ai-gftd-apps-gftdcojp/blob/main/90-docs/adr/2605092350-baien-1bit-multimodal-edge-browser-cpu-design.md)
- [ADR-2605101000 baien MX Multimodal Expansion from RW](https://github.com/gftdcojp/ai-gftd-apps-gftdcojp/blob/main/90-docs/adr/2605101000-baien-mx-multimodal-expansion-from-rw.md)
- [ADR-2605150600 Ameno Browser Inference Platform](https://github.com/gftdcojp/ai-gftd-apps-gftdcojp/blob/main/90-docs/adr/2605150600-ameno-browser-inference-platform.md)
- [ADR-2605151200 Open-OT WASM PLC and Distributed Logic Controller](https://github.com/gftdcojp/ai-gftd-apps-gftdcojp/blob/main/90-docs/adr/2605151200-open-ot-wasm-plc-dlc.md)

### Identity / Operating Entity (boundary)

- [ADR-2605102200 Operating Entity Rename (etz hayim → amanomibashira)](https://github.com/gftdcojp/ai-gftd-apps-gftdcojp/blob/main/90-docs/adr/2605102200-operating-entity-amanomibashira-rename.md) (later partially reverted; see ADR-2605152100)
- [ADR-2605152100 etzhayyim GitHub Org Boundary + Monorepo Seed Strategy](https://github.com/gftdcojp/ai-gftd-apps-gftdcojp/blob/main/90-docs/adr/2605152100-etzhayyim-github-org-boundary.md)

### Python / DB contracts

- [ADR-2605080200 Pydantic v2 L6 Validation Contract](https://github.com/gftdcojp/ai-gftd-apps-gftdcojp/blob/main/90-docs/adr/2605080200-pydantic-l6-validation-contract.md)
- [ADR-2605080300 SQLAlchemy Core Usage Contract](https://github.com/gftdcojp/ai-gftd-apps-gftdcojp/blob/main/90-docs/adr/2605080300-sqlalchemy-core-usage-contract.md)
- [ADR-2605080400 Alembic Scope Contract](https://github.com/gftdcojp/ai-gftd-apps-gftdcojp/blob/main/90-docs/adr/2605080400-alembic-scope-contract.md)
- [ADR-2605080500 SQLMesh MV Management](https://github.com/gftdcojp/ai-gftd-apps-gftdcojp/blob/main/90-docs/adr/2605080500-sqlmesh-mv-management.md)

### Persistence / Graph

- [ADR-2605111200 CF Worker Edge-Only — RW Connection K8s-Pod Only](https://github.com/gftdcojp/ai-gftd-apps-gftdcojp/blob/main/90-docs/adr/2605111200-cf-worker-edge-only-no-rw-connection.md)
- [ADR-2605111300 PDS-to-Pod Bun Container](https://github.com/gftdcojp/ai-gftd-apps-gftdcojp/blob/main/90-docs/adr/2605111300-pds-to-pod-bun-container.md)
- [ADR-0044 RisingWave UDF Language Strategy](https://github.com/gftdcojp/ai-gftd-apps-gftdcojp/blob/main/90-docs/adr/0044-risingwave-udf-language-strategy.md)

## Conventions

- **ID format**: `YYMMDDhhmm-<topic-slug>.md` (JST timestamp; example `2605170900-...`)
- **Vendor collision avoidance**: vendor monorepo uses up to ~2605152000 series. etzhayyim/root starts at 2605170000 series.
- **Template**: `template.md` (mirror vendor's structure)
- **Front matter**: see `90-docs/CLAUDE.md` § "Required Metadata"
- **Section order**: Context → Decision → Consequences → Alternatives Considered → References

## See also

- `90-docs/CLAUDE.md` — full docs system rules (this monorepo)
- `CLAUDE.md` (repo root) — operating entity identity, monorepo layout, scaffolding status
- vendor monorepo `90-docs/CLAUDE.md` — original docs system rules (etzhayyim/root mirrors with adaptations)
