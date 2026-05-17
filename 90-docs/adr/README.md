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
| [2605171300](./2605171300-open-unispsc-generative-agent-fleet.md) | Open-UNSPSC Generative Agent Fleet using OpenRouter and Local Fallback (18,345 agents) | accepted | 2026-05-17 |
| [2605171800](./2605171800-langgraph-mst-ipfs-l2-anchor-pipeline.md) | Artificial Organism Ecosystem — LangGraph Pregel → PostgresSaver → atproto MST → IPFS → Base L2 anchor pipeline | proposed | 2026-05-17 |
| [2605171900](./2605171900-yoro-migration-to-etzhayyim.md) | yoro AppView migration — code + DNS + deployment to yoro.etzhayyim.com | proposed | 2026-05-17 |
| [2605172000](./2605172000-etzhayyim-rw-free-substrate.md) | etzhayyim/root open apps MUST be RW-free — AT MST + IPFS + Base L2 substrate | proposed | 2026-05-17 |
| [2605172100](./2605172100-etzhayyim-payments-on-chain-only.md) | etzhayyim payments — Base L2 + USDC + ERC-4337 Smart Account (on-chain only, no fiat processor) | proposed | 2026-05-17 |
| [2605172200](./2605172200-openmail-atproto-mst-smtp-bridge.md) | Open Email — atproto MST-native mail with bidirectional SMTP bridge and on-chain postage | proposed | 2026-05-17 |
| [2605172300](./2605172300-etzhayyim-bi-asset-substrate.md) | etzhayyim Kisha-Stream / Goji-Treasury — two-chain (geth-private + Base L2) basic-income and asset substrate for an on-chain religious voluntary association | proposed | 2026-05-17 |
| [2605172600](./2605172600-etzhayyim-membership-ritual.md) | etzhayyim Membership Ritual — dual-permanent record (Base L2 + Github) + signed oath | proposed | 2026-05-17 |
| [2605172700](./2605172700-membership-layering-shinto-adherent.md) | Membership layering — 信者 (172600) and Adherent (172300 S0) as complementary tiers | proposed | 2026-05-17 |
| [2605172800](./2605172800-gftd-cli-migration-strategy.md) | 70-tools/gftd CLI migration strategy — git-subrepo unwind + open-scope fork | proposed | 2026-05-17 |
| [2605172900](./2605172900-gftd-followup-cutover-policy.md) | gftd-→-etzhayyim follow-up cutover policy — what is rewritten, what is preserved as historical | active | 2026-05-17 |
| [2605173000](./2605173000-pds-did-web-resolution-worker.md) | did:web:pds.etzhayyim.com resolution via path-specific Cloudflare Worker | active | 2026-05-17 |
| [2605173100](./2605173100-gitguardian-incident-response.md) | GitGuardian RisingWave credential-leak incident response — full remediation 2026-05-17 | active | 2026-05-17 |

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
