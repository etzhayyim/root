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
| [2605182312](./2605182312-local-bring-up-murakumo-gemma4.md) | Local Bring-up of Artificial Organism on Murakumo Fleet | active | 2026-05-18 |
| [2605192100](./2605192100-etzhayyim-mission-charter.md) | etzhayyim Mission Charter — 人類の労働解放を最終目的とする宗教法人の上位憲章 (多世代 / 反個人主義 / Wellbecoming 三柱を含む) | proposed | 2026-05-19 |
| [2605192115](./2605192115-etzhayyim-non-profit-donation-only-no-ads.md) | etzhayyim Non-profit / Donation-only / No-ads — 営利・広告・購買モデルの構造的排除 | proposed | 2026-05-19 |
| [2605192130](./2605192130-etzhayyim-tithe-redistribution.md) | etzhayyim 10% Tithe — donation / kisha 受領時の Public Fund 自動再分配 (constitutional constant) | proposed | 2026-05-19 |
| [2605192145](./2605192145-etzhayyim-public-fund-architecture.md) | etzhayyim Public Fund Architecture — 10% tithe の受け皿としての grant 評議・配布機構 | proposed | 2026-05-19 |
| [2605192200](./2605192200-etzhayyim-ip-free-release-charter-rider.md) | etzhayyim IP-Free-Release with Charter Compliance Rider v2.0 — Apache 2.0 + 多世代 + 反個人主義 + Wellbecoming license addendum (von Neumann minimax 解) | proposed | 2026-05-19 |
| [2605192230](./2605192230-etzhayyim-three-tier-enforcement-implementation.md) | etzhayyim Three-Tier Enforcement Implementation — Phenotype / KishaStream / PublicFund / TitheRouter への Charter Compliance Gate 実装 + Council attestation flow + Rehabilitation (Teshuvah) | proposed | 2026-05-19 |
| [2605192245](./2605192245-etzhayyim-global-land-sovereignty.md) | etzhayyim Global Land Sovereignty — 地球上の土地を国家ではなく religious-corp chain が分散合意で担保する (dual-recognition with state cadastre + Lv5 護 Steward + 4-layer substrate) | proposed | 2026-05-19 |
| [2605192300](./2605192300-etzhayyim-bootstrap-council-five.md) | etzhayyim Bootstrap Council 5名 — initial Lv6+ ロスター + 5軸 expertise + 30日 public objection + Phase 2 移行 | proposed | 2026-05-19 |
| [2605192315](./2605192315-etzhayyim-transparent-force-rd.md) | etzhayyim Transparent Religious Force — open-source R&D registry + 1 SBT = 1 vote 承認 + on-chain force log Lexicon | proposed | 2026-05-19 |
| [2605192330](./2605192330-etzhayyim-extended-land-sovereignty-ocean-river-air-orbit.md) | etzhayyim Extended Land Sovereignty — 海洋 / 河川 / 大気 / 軌道への寄付受付拡張 | proposed | 2026-05-19 |
| [2605192345](./2605192345-etzhayyim-steward-succession.md) | etzhayyim Steward Succession — donor 死亡時の steward 継承手続き + 多世代 stewardship continuity | proposed | 2026-05-19 |
| [2605192400](./2605192400-etzhayyim-eros-gore-council-judging.md) | etzhayyim Eros / Gore Boundary — Council Lv6+ judging framework + LLM-assisted classification + precedent registry | proposed | 2026-05-19 |
| [2605192415](./2605192415-etzhayyim-religious-corp-daemon-architecture.md) | etzhayyim Religious-Corp Daemon Architecture — Pregel cell catalog (15 cells) + 3階層 actor hierarchy + Murakumo 常駐化 + LangGraph 実行 roadmap (S0-S11) | proposed | 2026-05-19 |

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
