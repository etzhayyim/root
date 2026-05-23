---
id: adr-readme-etzhayyim-root
title: etzhayyim/root ADRs — Index and Placement Policy
status: active
doc_type: reference
topic: adr-readme
authoritative: true
last_verified: 2026-05-21
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
| [2605201400](./2605201400-etzhayyim-kuni-umi-planetary-infra-fleet.md) | etzhayyim kuni-umi (国生み) — planetary-scale infrastructure robotics fleet actor (Survey → Plan → Construct → Commission Pregel; open-* utility lexicons × open-robo × open-ot × UNSPSC fleet seam; 4-domain extended sovereignty) | proposed | 2026-05-20 |
| [2605201500](./2605201500-etzhayyim-kuni-umi-s1-solo-survey.md) | kuni-umi S1 — solo survey (1 Giemon Otete + 1 Mimi stationary witness base-station; 山中湖 LandRegistry plot; SiteSurveyCell cell.py reference; 8 acceptance criteria) | proposed | 2026-05-20 |
| [2605201600](./2605201600-etzhayyim-kuni-umi-s2-community-microgrid.md) | kuni-umi S2 — community microgrid (1 MW class single-utility electric prototype; kuni-umi Phase 2–4 × open-ot 7 loops end-to-end; university campus site; 6 Otete + 8 Mimi + 2 Hitogata fleet; USDC 2.3–3.1M; governance vote + Public Fund grant triggered) | proposed | 2026-05-20 |
| [2605201700](./2605201700-etzhayyim-kuni-umi-s3-multi-utility.md) | kuni-umi S3 — multi-utility integrated (electric + water + network on S2 site; BoM consolidation algorithm with MIP solver + 15% savings target; cross-utility witness coordination 12-cluster; multi-target commissioning; 12 Otete + 12 Mimi + 4 Hitogata; +USDC 1.5–2.1M incremental) | proposed | 2026-05-20 |
| [2605201800](./2605201800-etzhayyim-kuni-umi-s4-multi-site-fleet.md) | kuni-umi S4 — multi-site fleet (≥5 archetype concurrent sites: university / rural / religious community / workers' coop / disaster recovery; FleetRebalanceCell Hungarian-method algorithm; cross-site BoM batching 20% savings target; Pregel-native edge orchestration + NATS over CF tunnel; Quad introduction; Council Lv6+ supermajority on fleet portfolio composition new gate; +USDC 6.3–8.8M incremental) | proposed | 2026-05-20 |
| [2605201900](./2605201900-etzhayyim-kuni-umi-s5-extended-sovereignty.md) | kuni-umi S5 — extended sovereignty (S5a river + S5b ocean + S5c atmosphere HAPS + S5d orbit LEO microsat; stewardship-only operational invariant; 4 new robot classes Suii/Tairyou/Sora/Hoshi; international law dual-recognition pattern per ADR-2605192330; +USDC 12.7–28.4M incremental; final roadmap phase) | proposed | 2026-05-20 |
| [2605202000](./2605202000-etzhayyim-energy-substrate.md) | etzhayyim Energy Substrate — solar + storage + microgrid first; SMR deferred; open-hardware mandatory; 3-phase scale (§1.3 mission implementation) | proposed | 2026-05-20 |
| [2605202015](./2605202015-etzhayyim-robotics-first-industry-agriculture.md) | etzhayyim Robotics First-Industry — Agriculture selected over logistics/construction/care/manufacturing (§1.4 mission, FarmBot fork, Land trust integration) | proposed | 2026-05-20 |
| [2605202030](./2605202030-etzhayyim-tithe-router-v1-create2.md) | TitheRouter v1 — CREATE2 sequencing で Constitution.getMutable 経由 publicFund 読み出しを実現 (post-mainnet migration) | proposed | 2026-05-20 |
| [2605202100](./2605202100-etzhayyim-magatama-cell-runner-launchd.md) | magatama-cell-runner launchd LaunchAgent (operationalising Tier 1 常駐稼働 on Murakumo fleet; pyproject `[project.scripts]` entry + plist template + idempotent installer + per-node `--health` smoke; closes spec → OS-level boot path gap) | proposed | 2026-05-20 |
| [2605202115](./2605202115-baien-graft-3d-augmented-dataset.md) | Baien graft 3D-augmented dataset — TripoSR + Hunyuan3D-2 image→3D, moderngl 4-view render, Florence-2 multi-view caption; baien Move 1 supervision を 3D-aware text で強化 (input 2D 据置) | proposed | 2026-05-20 |
| [2605211241](./2605211241-etzhayyim-surplus-router-warehouse-bridge.md) | etzhayyim Surplus Router — global surplus / dead-stock / overstock redistribution bridge across warehouse × toshiKozan × ftzZones × freeportRegistry × payment.tithe (donation-only, 10% in-kind tithe coupling, Wellbecoming routing priority enforcement, 7 Lexicons under `ai.gftd.apps.surplusRouter.*`) | proposed | 2026-05-21 |
| [2605215200](./2605215200-etzhayyim-shinka-pregel-mst-rewrite.md) | etzhayyim shinka Pregel/MST rewrite — 4 core cells + mst-projector + charter compliance gate | proposed | 2026-05-21 |
| [2605215300](./2605215300-etzhayyim-yoro-python-primitives-mst-rewrite-addendum.md) | etzhayyim yoro Python primitives MST rewrite addendum — migration waves M2–M7 (40 functions) | proposed | 2026-05-21 |
| [2605215400](./2605215400-etzhayyim-shinka-evolution-witness-min.md) | etzhayyim shinka EVOLUTION_WITNESS_MIN — 7-level witness thresholds + Council gate + 30-day appeal | proposed | 2026-05-21 |
| [2605212150](./2605212150-etzhayyim-langserver-substrate.md) | etzhayyim-langserver — Fleet-resident LSP substrate on Murakumo Mac mini fleet (9-layer reverse-topo build) | proposed | 2026-05-21 |
| [2605231230](./2605231230-etzhayyim-esign-actor-did-bound-mst-anchored.md) | etzhayyim-esign actor — DID-bound, MST-recorded, L2-anchored document signing (religious-corp native replacement for DocuSign / Adobe Sign / RazorpaySign; gftd lawfirm passthrough retained only for fiat / India counsel intake) | proposed | 2026-05-23 |
| [2605231451](./2605231451-level-system-unification.md) | Level System Unification — society6 Kyu/Dan を canonical scale とし、信者 7段 (MEMBERS.md) / dojo 帯 / joucho S-D を正規化 (joucho は object-axis として非変換、Elder ↔ Dan 10 を信者経由に限定)。Kyu 1 → Dan 1 に **自他非分離体験ゲート D6** (瞑想 / breathwork / 断食 / sensory deprivation / sacramental plant medicine, §D6.5 法域責任を明示) を一度きり課す | proposed | 2026-05-23 |
| [2605231500](./2605231500-etzhayyim-agent-driven-unspsc-supply-flows.md) | agent-driven UNSPSC supply flows — business-model wiring for 18,346-actor commodity automation (AgentAuthorityToken soulbound contract + 2 new lexicon namespaces + esign envelope extensions + charter-compliance-gate library; companion to ADR-2605231230 for AAT-bound agent signing) | proposed | 2026-05-23 |
| [2605242100](./2605242100-baien-server-xl-carve-out.md) | baien-server / baien-XL carve-out from edge invariant — 4-tier ladder (edge / bonsai / server / XL) with shared Charter Rider + Murakumo-only invariants across tiers | accepted | 2026-05-24 |
| [2605242110](./2605242110-baien-mx-move5-video-graft.md) | baien Move 5 — video graft (VideoMAE-base + 1.58-bit projector + 4 modal configs A/B/C/D; edge tier on-demand modality loading to respect ADR-2605241900 cumulative encoder ceiling) | accepted | 2026-05-24 |
| [2605242120](./2605242120-baien-mx-move6-robotics-graft.md) | baien Move 6 — robotics graft (edge = scene description only / server = OpenVLA-style action head post-Council; safety-driven tier split per Charter Rider §2(h) + §2(a)) | accepted | 2026-05-24 |
| [2605242400](./2605242400-baien-smoke-is-destructive-finding.md) | baien smoke runs are destructive, not informative — Move 1 Phase A + distill iter-00 honest signal; formalises Phase B as minimum-informative tier + operator gate against publishing smoke-tier adapters to distilled-models.jsonl | accepted | 2026-05-24 |

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
