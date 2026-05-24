---
id: adr-readme-etzhayyim-root
title: etzhayyim/root ADRs — Index and Placement Policy
status: active
doc_type: reference
topic: adr-readme
authoritative: true
last_verified: 2026-05-24
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
| [2605215000](./2605215000-etzhayyim-inference-murakumo-only-no-runpod.md) | etzhayyim inference is Murakumo-fleet-only — RunPod is constitutionally prohibited (pymagatama RunPod coupling audit + Step 8 cutover sub-list; EVO-X2 LiteLLM gateway as sole GPU inference SSoT; extends ADR-2605191346 / 2605202345 / 2605214000) | proposed | 2026-05-21 |
| [2605215100](./2605215100-etzhayyim-maps-sentinel-mlx-murakumo-fleet.md) | Sentinel-1/2 satellite analysis on Murakumo fleet — tiered MLX/ROCm placement without RunPod (5-tier analysis matrix: T0 CPU preprocessing / T1 Qwen3-VL-8B EVO-X2 / T2 Florence-2 MLX / T3 MPS change-detection / T4 SAR research spike; wire-shape stable; M0-M5 roadmap; concrete REIMPLEMENT successor for ADR-2605215000) | proposed | 2026-05-21 |
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
| [2605242500](./2605242500-baien-ternary-silicon-and-tsukuru-fab-charter.md) | baien ternary silicon + tsukuru fab — religious-corp first-party RTL/装置設計 charter (生命のコア); 2 ASICs (iwakura/fuigo) + 8 fab equipment categories owned by religious-corp under Apache 2.0 + Charter Rider; tsukuru.etzhayyim.com sole orchestration SSoT; §2(a)(c) Council gate; 4-phase roadmap | proposed | 2026-05-24 |
| [2605242515](./2605242515-iwakura-ternary-inference-asic.md) | iwakura (磐座) — baien ternary 専用推論 ASIC architecture (256×256 multiplier-less ternary PE = 65 Tera-ternary-ops/s; radix-3 5-weights-per-byte packing; 16 MB SRAM + 2 GB LPDDR5X-7500; 3-5 W edge / 15 W workstation; Phase 1 = RTL + cocotb sim) | proposed | 2026-05-24 |
| [2605242530](./2605242530-fuigo-hybrid-ternary-bf16-training-asic.md) | fuigo (鞴) — baien hybrid ternary/BF16 training ASIC architecture (1024×1024 ternary forward + 8k BF16 backward dual-SA; STE Glue + Lion hardwire; HBM3e 96 GB / 4.8 TB/s; libp2p NIC on-die for Murakumo no-VKE mesh; closes ADR-2605215000 with training-only-Murakumo) | proposed | 2026-05-24 |
| [2605242545](./2605242545-tsukuru-fab-equipment-pregel-charter.md) | tsukuru fab 8-equipment Pregel charter — litho/depo/etch/implant/CMP/metrology/test/packaging self-design + per-step silicon_* Pregel cell; open-source toolchain only (yosys/Verilator/cocotb/KiCad/FreeCAD/ROS 2); public reference design as transparent religious force; Phase 2 priority sequencing (test → metrology → packaging → litho → 残り 4) | proposed | 2026-05-24 |
| [2605242600](./2605242600-baien-federated-train-via-ameno-webgpu.md) | baien federated training via ameno WebGPU — smartphone-participable LoRA round (R0 scaffold); 5-layer (WebGPU kernel / ameno PWA / lexicon+DID / Murakumo aggregator / MST+L2 anchor); 11 constitutional gates G1..G11 | proposed | 2026-05-24 |
| [2605212100](./2605212100-gftd-to-etzhayyim-migration-batch.md) | gftd→etzhayyim 60-apps migration batch (gov / law / legal scope) — closes the dangling ADR reference in 3 DEPRECATED.md markers + documents 36-file blind-copy restore + substrate-port deferral list | active | 2026-05-21 |
| [2605214000](./2605214000-etzhayyim-murakumo-mesh-no-vke-and-lexicon-port-rules.md) | Murakumo distributed cluster (no-VKE mesh) + lexicon port verdict taxonomy (REDIRECT/VENDOR-ONLY/REIMPLEMENT) + §3 atomic identifier cutover rules — closes 14-citation ghost reference; 220-file atomic-PR invariant; legal-registration master gate | active | 2026-05-21 |
| [2605242330](./2605242330-gov-procedure-pregel-mcp-coverage.md) | Gov-procedure Pregel/MCP coverage 5-layer taxonomy (L1 namespace / L2 COFOG×country / L3 public-services hub / L4 ingest / L5 routing-around) + 195-country scale-out plan + explicit non-roadmap | proposed | 2026-05-24 |
| [2605250100](./2605250100-l5-routing-around-member-registry-cell.md) | L5 routing-around cell ladder + member_registry_cell P1 (住民登録 substitute for SBT-holding adherents) — 1-gate Council activation; existing Adherent SBT / MEMBERS.md / EtzhayyimMembership.sol orchestrated as coherence layer | proposed | 2026-05-25 |
| [2605250200](./2605250200-l5-religious-marriage-cell.md) | L5 P2 religious_marriage_cell (婚姻届 substitute for SBT↔SBT bonds) — 2-gate Council activation; 3 open constitutional questions (gender / polygamy / cross-religion); mutual-consent dissolution only | proposed | 2026-05-25 |
| [2605250300](./2605250300-l5-religious-corp-taxation-cell.md) | L5 P3 religious_corp_taxation_cell (法人税申告 INTERNAL substrate operator; does NOT discharge state-tax obligations) — 3-gate Council activation (+ legal counsel opinion CID); 4 open constitutional questions; Charter Rider §2 violation detection at runtime | proposed | 2026-05-25 |
| [2605250400](./2605250400-gemma-coder-distill-rocm.md) | gemma-coder distill — gemma3:4b drift → gemma4:e4b の LangGraph コーディング適応 (EVO-X2 ROCm + peft+trl, Unsloth Windows-ROCm 不可確定); first non-baien distill route; 6-fix iter-00 E2E + 4 systematic antipattern fixed by hand-authored Apache 2.0 corpus | accepted | 2026-05-25 |
| [2605250500](./2605250500-yakushi-pharmaceutical-rd-charter.md) | yakushi (薬師) pharmaceutical R&D master charter — religious-corp first-party API + sterile fill-finish + supply chain; Wave 1 reference = OTC 抗アレルギー点眼薬 triplet (cromoglicate Na + naphazoline HCl + chlorpheniramine maleate); Charter Rider §2 全条項 clearance + §2(e) anti-gatekeeping pro-clearance; 14 constitutional gates G1..G14 + 10 non-goals N1..N10; 4-phase roadmap R0→R3; Tier-B sibling of kuni-umi / wadachi / tsukuru / iwakura / fuigo | proposed | 2026-05-25 |
| [2605250515](./2605250515-yakushi-otc-ophthalmic-api-synthesis.md) | yakushi Wave 1 sub-ADR — 3 化合物 API 合成・精製・QC (Fisons 1965 DSCG / Ciba 1942 naphazoline / Schering 1949 chlorpheniramine perpetually off-patent routes; CWC + 国内 safety per-raw-material 評価表; recryst + (chlorpheniramine) prep-HPLC ICH M7 PGI removal; HPLC/IR/NMR/KF/ICP-MS/GC/PGI-LCMSMS/endotoxin QC suite) | proposed | 2026-05-25 |
| [2605250530](./2605250530-yakushi-sterile-fill-finish-and-container.md) | yakushi Wave 1 sub-ADR — sterile fill-finish + LDPE BFS 5 mL multi-dose preservative-free 点眼瓶 (§2(h) wellbecoming BAK 不使用); aseptic processing unified across 3 化合物; Annex 1 (2023) 適合; Hitogata class-A sterile sub-config (kuni-umi inheritance); QC bridging attestation chain | proposed | 2026-05-25 |
| [2605250545](./2605250545-yakushi-pharma-supply-chain-and-robotics.md) | yakushi Wave 1 sub-ADR — 8 supply chain categories (raw mat / excipient / WFI / packaging primary+secondary / cold chain / spent material / AE ingestion) + 8 robotics class (既存 6 reuse: Hitogata × 2, Otete × 2, Mimi, Funamori inheritance + 新規 2 placeholder: Kusuko 薬子, Sukoyaka 健やか); GMP attestation chain; cold chain 2-8°C unified; AE reporting design (G5 + G10 + §2(c)); Charter Rider §2 per-category 評価 | proposed | 2026-05-25 |
| [2605250600](./2605250600-yakushi-wave-1b-otc-api-catalog-expansion.md) | yakushi Wave 1b — OTC API catalog expansion (3 → 12 化合物 across 4 therapeutic categories: analgesic+antipyretic acetaminophen/aspirin/ibuprofen + oral H1 antihistamine diphenhydramine/cetirizine/loratadine + H2 antagonist famotidine + topical clotrimazole/diclofenac Na) + 2 new dosage forms (oral tablet + topical cream/gel) + 2 new Pregel cells (pharma_tablet_manufacture on joseph, pharma_topical_formulation on simeon); 14 gates + 10 non-goals 不変 (extension only); 明示的除外 pseudoephedrine/codeine/dextromethorphan/hydrocortisone/sodium-hyaluronate/omeprazole | proposed | 2026-05-25 |
| [2605250615](./2605250615-yakushi-wave-1c-chiral-synthesis-and-deferred-otc-expansion.md) | yakushi Wave 1c — Chiral synthesis (omeprazole PPI via crystalline-resolution-mandelate / prep-hplc-chiral) + deferred OTC expansion (12 → 19 化合物: omeprazole chiral + laxatives polyethylene-glycol-3350/docusate-sodium/senna-extract/bisacodyl + cough-expectorant guaifenesin/benzonatate) + 1 new Pregel cell (pharma_chiral_resolution on levi) + 1 new cell (pharma_liquid_formulation on joseph) + 3 new dosageForm (sachet-powder-for-reconstitution / oral-liquid-syrup / oral-suspension); 14 gates + 10 non-goals 不変 (extension only); **G7 risk = NONE** (omeprazole route omits OPCW Schedule 3); benzonatate PMDA jurisdiction margin (R1 phase pending) | proposed | 2026-05-25 |
| [2605250630](./2605250630-yakushi-wave-1c-r1-chiral-commissioning.md) | yakushi Wave 1c R1 — Chiral synthesis commissioning and benzonatate PMDA jurisdiction; establishes Council Lv6+ ≥3 attestation baseline (silenPharmaReview scope: wave-1c-chiral-resolution-baseline + wave-1c-liquid-formulation-baseline); defines omeprazole S-enantiomer benchtop PoC protocol (≤1g, two parallel routes: crystalline-resolution-mandelate 65-75% yield / prep-HPLC-chiral Chiralcel OD-H 70-95% yield, enantiomeric purity ≥99.5% ICH M7 Class 5); specifies guaifenesin syrup + benzonatate suspension QC baseline (USP <61>/<62> microbial limits); documents benzonatate PMDA jurisdiction margin (monitoring window until 2026-06-30; if approved → R1.5 amendment unlock; if denied → Wave 2 deferral); no amendment to 14 gates + 10 non-goals | proposed | 2026-05-25 |
| [2605250700](./2605250700-oka-mmsheaf-multimodal-integration.md) | Oka × MMSheaf — Sheaf-based diffusion as graph-aware multimodal fusion layer (R0 scaffold); integrates Gonzàlez i Català 2025 (Cambridge / P. Liò) MMSheaf family into Oka as the missing graph-aware modality fusion layer; two-tier deployment (server = MMSheafV4 block-structured + α_ij scalar MLP on EVO-X2 ROCm; edge = MMSheafV3 block-diagonal ternary-quantisable into Baien BitNet 1.58 ≤2GB @ 4k ctx); 9-modality stalk (text / image / audio / video / 3d / geospatial / document / tabular / time-series); d_node = 9 constitutionally fixed; missing modality = zero-row + mask extension beyond paper; training reuses gemma-coder-distill peft+trl bf16 LoRA recipe (no RunPod per CHARTER-RIDER §2(i)); graph source = yatachain-projection (deterministic MST rebuild per ADR-2605231500), first target = feed-discover; lexicon namespace `app.etzhayyim.mmsheaf.diffusionRoundReceipt` reserved; R0 scaffold-declared-no-code (paths reserved in pymagatama.mmsheaf + magatama/cells/mmsheaf_diffusion_aggregator + baien-distill V3 ternary node + mmsheaf-microbench bench); R0→R4 phase plan with each phase gated by its own ADR; reported baseline targets MMSheafV4 86.14% on Ele-Fashion + synthetic +5%–+31% over GCN/GAT | proposed | 2026-05-25 |

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
