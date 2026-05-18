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
  - placement policy for open-scope ADRs
related:
  - 2605170900-etzhayyim-root-adr-canonical-home.md
supersedes: []
superseded_by: []
---

# etzhayyim/root ADRs — Index and Placement Policy

This directory is the **canonical home for ADRs about religious-corp open activities** operated by `etzhayyim`. Policy is established by **ADR-2605170900** (this directory).

## Placement

New open-scope ADRs go here (`etzhayyim/root/90-docs/adr/`). Scope:

- blockchain / baien / bpmn / lexicon / pregel / atproto / ameno / open-data / public governance
- new open project designs, new public infrastructure, new open protocol specs

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
| [2605181100](./2605181100-mst-encrypted-records-signal-keywrap.md) | MST encrypted records + Signal key-wrap (Tahoe-pattern confidentiality on AT Protocol substrate) | proposed | 2026-05-18 |
| [2605181200](./2605181200-mst-encrypted-metadata-leak-reduction.md) | Encrypted-record metadata-leak reduction — ciphertext padding + rkey blinding (Sealed Sender deferred) | proposed | 2026-05-18 |

(Future ADRs added here as they're authored.)

## Conventions

- **ID format**: `YYMMDDhhmm-<topic-slug>.md` (JST timestamp; example `2605170900-...`)
- **ID range**: etzhayyim/root starts at 2605170000 series.
- **Template**: `template.md`
- **Front matter**: see `90-docs/CLAUDE.md` § "Required Metadata"
- **Section order**: Context → Decision → Consequences → Alternatives Considered → References

## See also

- `90-docs/CLAUDE.md` — full docs system rules (this monorepo)
- `CLAUDE.md` (repo root) — operating entity identity, monorepo layout, scaffolding status
