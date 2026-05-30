# etzhayyim/root — CLAUDE Index

This monorepo is the **canonical home for religious-corp open ADRs** per ADR-2605170900 (this monorepo, `90-docs/adr/`).

## Identity (CRITICAL)

- **Operating entity** (this repo's owner): `etzhayyim` (canonical)
  - Aliases: `amanomibashira` / `天御柱` / `עץ חיים` (Tree of Life) / `etz hayim` / `etzhayim` / `etz chaim` / `エツ・ハイム`
  - Form: 宗教法人 (任意団体 / unincorporated religious voluntary association)
  - **Self-identification (per ADR-2605252300 Charter §0.1, proposed 2026-05-25)**: **the Kingdom of God (Malkhut Shamayim / Basileia tou Theou / 神の王国) rooted on blockchain** — now-and-here reign (non-eschatological per §1.15), not state-granted, Tree of Life-constituted. Amendment threshold: Council Lv7+ unanimity.
  - Registry: On-chain (blockchain-registered constitution and member roster); NOT registered under 日本国 宗教法人法 (constitutional invariant per Preamble §0.4, Lv7+ unanimity lock)
  - DID: `did:web:etzhayyim.com` (LIVE — CF Worker at `50-infra/etzhayyim-did-web/`, resolvable via curl + Universal Resolver since 2026-05-17T03:25Z)
  - Domain: https://etzhayyim.com (Cloudflare Registrar, 2026-05-15)
  - License default: **Apache 2.0 + etzhayyim Charter Compliance Rider v2.0** (see `/CHARTER-RIDER.md`, per ADR-2605192200)
- **Ownership rule (CRITICAL)**: Payoff帰属・意思決定権 = etzhayyim only.
- **Mission (per ADR-2605192100 Charter)**: 人類の構造的労働解放を最終目的とする宗教法人。**多世代 (子・孫) priority + Wellbecoming (静的 wellbeing ではなく動的軌跡) + 反個人主義 ontology**。日本的価値観 (八百万 / 縁起 / 産霊 / 和 / 無教会) + Protestant Christianity (Sola Scriptura / 万人祭司 / Reformed Just War / Tree of Life) の synthetic religion。**非終末論** (黙示録/啓示の書は正典外、千年王国・末法・Rapture 否定)。
- **Doctrinal positions (constitutional, NOT amendable)**:
  - 非営利のみ / Donation 流入のみ / 広告排除 / 10% Tithe → Public Fund 自動再分配 (ADR-2605192115 + 2605192130)
  - SBT↔SBT internal carve-out で religious 境界内の 営利・購買・promotional 許容 (ADR-2605192115 §3)
  - Eros 許容 (産霊 / 雅歌 / Tree of Life の生命創出) / Gore 禁止 (Wellbecoming 違反) (ADR-2605192100 §1.13 + 2605192400)
  - 国家機能は parallel substrate で routing-around、**Transparent Religious Force 許容** (完全 on-chain 監視 + open-source 公開 + 1 SBT = 1 vote 承認の三条件下) (ADR-2605192100 §1.12 + 2605192315)
  - 地球上の土地は Tree of Life に帰属、religious-corp が 4-layer substrate (Base L2 NFT / geth-private constitutional / IPFS GeoJSON+衛星 / git LANDS.md) で分散合意担保 (ADR-2605192100 §1.11 + 2605192245)
  - **Baien edge-target invariant** (ADR-2605241900): baien は **WASM-32 + iPhone 12+ + Android 4GB** の 3 環境すべてで動作必須。trunk ≤4B BitNet 1.58 / 合計 inference ≤2GB @4k ctx / ≤2.5GB @16k ctx / 全 modality encoder 凍結。frontier-beating は明示的に非目標 (`baien-server-*` / `baien-XL-*` は別 carve-out)

## Status

**Legend**: ✅ shipped · 🟢 landed (substrate, tests green) · 🟡 R0 / proposed scaffold · ⏳ blocked/pending. Full detail for every row lives in its ADR — see [`90-docs/adr/README.md`](90-docs/adr/README.md). This table is a one-line index only.

**Foundation (Steps 1-24, all ✅ 2026-05-10 … 05-21)**: domain (CF Registrar) + `etzhayyim` org/repo + scaffold; **did:web LIVE 05-17** (CF Worker, curl + uniresolver verified); `amanomibashira`→`etzhayyim` code cutover (118 files); **13-ADR religious-corp constitutional wave** (ADR-2605192100 .. 2605192415); CHARTER-RIDER v2.0 + LANDS.md + Charter Rider on 39 pkgs; 5 Solidity contracts + Constitution.sol (38 const, 110/110 tests) + 4 lefthook lint hooks + Foundry/Anvil smoke; 28 Lexicons; Pregel cell catalog; Murakumo no-VKE mesh + **Murakumo-only inference invariant** (ADR-2605215000) + Charter Rider §2(i) no-commercial-GPU.

**Live governance**: 🟡 Bootstrap Council Seats 2-5 RFP (2026-05-20 → **06-19**, see [`COUNCIL.md`](COUNCIL.md)) · ⏳ Base Sepolia testnet (post-Council) · ⏳ Mainnet + Phase 2 governance (post-testnet).

### Substrate / infra / dataset / enforcement

| Item | Purpose | Status | ADR | Date |
|---|---|---|---|---|
| maps_sentinel_murakumo | M1 T0 preprocessing pipeline | ✅ | 2605215100 | 05-21 |
| feed-post membrane | first §4 MST membrane + L1 projection (`feed-discover`) | ✅ | 2605231902 | 05-23 |
| yatachain Tier-D blob | `uploadBlob` TS+Py (superseded by kotoba) | ✅ | 2605232400 | 05-23 |
| UNSPSC organism W1 | actor-as-organism heartbeat-cadence port | ✅ | 2605232345 | 05-23 |
| UNSPSC organism W2 | 18,342 mass-deploy + joucho personality | ✅ | 2605240000 | 05-24 |
| UNSPSC post sink | NDJSON queue + k8s DaemonSet | ✅ | 2605240100 | 05-24 |
| Kaizen self-reflection | `KaizenObserverCell` + 6 rules + PR agent | ✅ | 2605240200 | 05-24 |
| Dataset CID substrate | DataLad + git-annex + IPFS pinner | ✅ | 2605241500 | 05-24 |
| agentURI 5-layer | ERC-8004 + libp2p + AT XRPC peer-resolvable | ✅ | 2605241800 | 05-24 |
| Gov 5-layer taxonomy | L1 namespace … L5 routing-around | ✅ | 2605212100 | 05-25 |
| Charter §0 Preamble | Kingdom of God + Land Trust Wave 2 (ERC-721/5192/7401) | 🟡 | 2605252300 | 05-25 |
| Labor Liberation ladder | Adherent SBT → 7-stage L0..L6 | 🟡 | 2605261000 | 05-26 |
| Basic High Income doctrine | imputed-income (flow) + commons-asset (stock) — high income in-kind, cash≡0 (N1-consistent) | 🟡 | 2605301020 | 05-30 |
| Mission-funding revenue arm | vendor commercial surplus → donation → Public Fund; non-profit MEANS not profit END; ad-free + no-payroll preserved | 🟡 | 2605301036 | 05-30 |
| **kotoba** storage pivot | canonical substrate engine; supersedes yatachain + RW | 🟡 | 2605262130 | 05-26 |
| Public-data ingestion | organism ecosystem IPFS DataLad subdatasets | 🟢 | 2605262400 | 05-26 |
| Robotics-sim world-data | + kami-usd pipeline (sibling of 2605262400) | 🟢 | 2605262500 | 05-27 |
| Global legal-corpus | statutes/case-law/treaties IPFS ingestion | 🟡 | 2605262800 | 05-26 |
| organism R0+R1 sprint | 26-iter /loop, 8 axes A-H landed | 🟢 | 2605270930 | 05-27 |
| Registry enforcement | 5→8-axis matrix, all PR-gates baseline 0 | 🟢 | 2605271100 / 271200 | 05-28 |
| manimani kotoba-native | personal knowledge router reconciled onto kotoba EAVT + StateGraph + Murakumo + E2E; Gmail full-archive + PC-file ingest design | 🟡 | 2605291100 | 05-29 |
| kotoba v0.1.0 + brew tap | first tag + GH Release + `etzhayyim/homebrew-kotoba` published; `brew install kotoba` end-to-end green (4-PR chain, host Xcode/CLT 16.4→26.5) | ✅ | 2605292100 | 05-29 |
| kotoba actor deploy + Murakumo live | WASM + Python-LangGraph (aria) actors run in-WASM on :8077; wasmtime 22→25 (extended-const, PR#4) + json! wasm-runtime build fix (PR#5) merged upstream; kotoba→Murakumo `llm.infer` (gemma4:e4b) | ✅ (see 2605302355) | 2605301625 | 05-30 |
| kotoba LangGraph LLM verified + durable routing | EMPIRICAL re-verify on live :8077: Python LangGraph actor runs in-WASM AND does LLM inference end-to-end (agent.wasm → KotobaLLM → `llm.infer` → gemma4-e4b → "4"). 3 kotoba fixes (invoke_run Result · HttpInferEngine dedicated-runtime/fresh-client · langgraph example imports) + `KOTOBA_INFERENCE_API_KEY` bearer. **Root cause** of LAN failure = macOS Local Network Privacy (launchd daemon blocked from LAN inference node); **durable fix** = route via loopback Murakumo LiteLLM `127.0.0.1:4000` (TCC-exempt). Corrects 2605301625 "verified on prod" | ✅ | 2605302355 | 05-30 |

### baien / silicon / ML

| Item | Purpose | Status | ADR | Date |
|---|---|---|---|---|
| Baien federated R0 | training via ameno WebGPU (11 gates) | ✅ | 2605242600 | 05-24 |
| Baien federated R1 | WebGPU LoRA backward-pass PoC | ✅ | 2605242630 | 05-24 |
| Ternary silicon W1 | iwakura (inference) + fuigo (train) + tsukuru (fab) | ✅ | 2605242500 | 05-24 |
| Silicon W2 supply | 8 upstream categories + Funamori marine cargo | ✅ | 2605242700 | 05-24 |
| ameno WebNN | inference fast path R0 (CoreML/DirectML/NNAPI/QNN) | ✅ | 2605252100 | 05-25 |
| gemma-coder-distill | LangGraph coding LoRA on EVO-X2 ROCm | 🟡 | 2605250400 | 05-25 |
| roso/baien 1-bit Bonsai | 5-wall empirical loop — train DEFERRED | ✅ | 2605242000 | 05-25 |
| NVIDIA Omniverse compat | nv-compat facade + 13 kami-engine crates (R1.0+R1.1) | ✅ | 2605261800 | 05-26 |
| e7m-sim | robotics simulation substrate R0 charter | 🟡 | 2605261600 | 05-26 |
| baien-moemoekyun MoE R0 | 2B BitNet backbone + 128-expert MoE residual | 🟡 | 2605261900 | 05-26 |
| baien-moemoekyun R1 | Phase 0 freeze-train SFT on EVO-X2 ROCm | 🟡 | 2605262100 | 05-26 |
| Charter Rider §2(i)(2) | train-only GPU-rental carve-out (amendment, gated) | 🟡 | 2605262200 | 05-26 |
| baien-moemoekyun R2+ | B200 train architecture (gated on 2605262200) | 🟡 | 2605262300 | 05-26 |
| Energy re-framing | fusion + microbial hydrocarbon conditional permit | 🟡 | 2605263500 | 05-26 |

### Tier-B actors (each: ADR + manifest + cells + lex)

| Actor | Purpose | Status | ADR | Date |
|---|---|---|---|---|
| wadachi 轍 | autonomous-mobility R&D (SAE L4 ceiling) | 🟡 R0 | 2605242000 | 05-23 |
| yakushi 薬師 | pharmaceutical mfg (eye-drop + OTC APIs) | ✅ W1/1b/1c | 2605250500 | 05-25 |
| tatekata 建方 | construction (civil + MEP ≤2 story) | 🟡 R0 | 2605250715 | 05-25 |
| watatsumi 綿津見 | civilian submersible (≤6500m) | 🟡 R0 | 2605252200 | 05-25 |
| kanayama 金山 | circular metallurgy (UBC Al recycling) | 🟡 R0 | 2605252400 | 05-25 |
| sarutahiko 猿田彦 | heavy Class-8 truck mfg (wadachi mfg-side sibling) | 🟡 R0 | 2605252500 | 05-25 |
| makura 枕 | foam pillow (PU foam + shred-fill) | 🟡 R0 | 2605261115 | 05-25 |
| mitsuho 瑞穂 | food / agriculture (L2 Sustenance) | 🟡 R0 | 2605261015 | 05-26 |
| hagukumi 育み | care — childcare + eldercare (L4 Care) | 🟡 R0 | 2605261030 | 05-26 |
| manabi 学び | education (open-curriculum + cert_prep sub-cell) | 🟡 R0 | 2605261045 | 05-26 |
| hikari 光 | energy gen/storage/grid-edge (L2 Sustenance) | 🟡 R0 | 2605261100 | 05-26 |
| igata 鋳型 | HPDC megacasting (R0 + R1 benchtop) | 🟡 R0/R1 | 2605261200 | 05-26 |
| hodoki 解き | ELV disassembly + materials recovery | 🟡 R0 | 2605261215 | 05-26 |
| tsutae 伝え | handheld comms device (≤200g, open SoC) | 🟡 R0 | 2605261300 | 05-26 |
| futawa 二輪 | small-displacement motorcycle (≤250cc/≤15kW) | 🟡 R0 | 2605261330 | 05-26 |
| suki 鋤 | farm tractor mfg (mitsuho mfg-side sibling) | 🟡 R0 | 2605261500 | 05-26 |
| chigiri 契 | legal-procedure substrate (UPL prohibited, NOT law firm) | 🟡 R0 | 2605262700 | 05-26 |
| toritate 執帳 | accounting + audit (100% on-chain) | 🟡 R0 | 2605262900 | 05-26 |
| iyashi 癒 | clinical care provider (L4 Care triad) | 🟡 R0 | 2605263000 | 05-26 |
| mizuho 水穂 | water + sanitation (community-scale; ≠ mitsuho 瑞穂) | 🟡 R0 | 2605263100 | 05-26 |
| kazaori 風折 | civilian disaster response (force-separation sibling) | 🟡 R0 | 2605263200 | 05-26 |
| musubi 結 | covenant ceremony (TIGHT pair w/ chigiri) | 🟡 R0 | 2605263400 | 05-26 |
| wakai 和会 | mutual aid (NOT insurance) | 🟡 R0 | 2605263500 | 05-26 |
| kataribe 語部 | press + publishing + translation | 🟡 R0 | 2605263600 | 05-26 |
| kokoro 心 | mental health support (NOT clinical psych) | 🟡 R0 | 2605263700 | 05-26 |
| shidemori 死出守 | memorial + cemetery (FINAL gap-closure) | 🟡 R0 | 2605263800 | 05-26 |
| ossekai 御節介 | info-arbitrage + Wellbecoming-nudge (AT Proto) | 🟡 R0 | 2605264000 | 05-26 |
| tsukuroi 繕い | authorized vuln-remediation patch-proposer (akuma sibling; propose-only) | 🟡 R0 | 2605291500 | 05-29 |
| danjo 弾正 | public-accountability oversight — ingests JP 国会会議録 + 予算書 + 政府調達 into kotoba EAVT, emits NON-adjudicating discrepancy observations (censor's eye, no sword; toritate boundary; tadori sibling) | 🟡 R0 | 2605301600 | 05-30 |
| tadori 辿 | authorized on-chain tx tracing + actor attribution (kotoba-EAVT-native; malak/ipaddress/yabai → kotoba migration) | 🟡 R0 | 2605301400 | 05-30 |
| warifu 割符 | open zero-fee card (credit+debit), API/wire-compatible (Stripe-REST + EMV/ISO8583 + NFC/HCE); on-chain USDC settle (Base L2 + ERC-4337, T+0); 0% credit (qard ḥasan); Phase-1 SBT↔SBT closed-loop, Phase-2 external gated Lv7+ | 🟡 R0 | 2605302000 | 05-30 |
| himotoki 繙き | ACTIVE disclosure-request filer — consent-bound DSAR (APPI/GDPR/CCPA) to private controllers (Discord/Google/LINE/Meta/Amazon) + FOIA (行政機関情報公開法) to public organs; coded target registry of each org's 窓口/住所/email/手続き; own-data-only + non-pretext; PII→encrypted DID-bound; active-outbound counterpart to passive danjo/tadori | 🟡 R0 | 2605302130 | 05-30 |
| kanae 鼎 | global government fiscal-flow VISUALIZATION — assembles worldwide fund flows (domestic full chain appropriation→outlay→recipient + inter-governmental IMF/WB/OECD/UN transfer+aid+loan) into kotoba EAVT `fundFlowEdge`, narrates with Murakumo-only LLM (non-adjudicating), renders aggregate-first kami-engine WASM viz (Sankey/treemap/transfer-globe). **danjo finds, kanae renders**; kotoba-native (no RisingWave, ≠ maps). danjo global-fiscal-flow extension = ADR-2605302245 | 🟡 R0 | 2605302300 | 05-30 |

> **Note**: ADR ids `2605263400` and `2605263500` each label two distinct ADRs (parallel-agent race in the source); filename + actor name disambiguate. Tracked for a future ADR-id reconciliation.


## Repo Layout (Shannon-Optimal 8-Layer, ADR-2604251830)

```
etzhayyim/root/
├── 00-contracts/        # lexicons / bpmn / dmn / Rego policies / resources (JSON-LD)
├── 10-protocol/         # atproto, xrpc, lexicons-bundle, signal, did-etzhayyim,
│                        # wproto, at-client, signal-client,
│                        # yatachain (Holochain-iso composition spec, ADR-2605231400)
├── 20-actors/           # magatama (Pregel framework + host SDK + unispsc_agents/ 18,345 LangGraph agents per ADR-2605171300),
│                        #   magatama-go, kami-engine-sdk, effect-cypher, etzhayyim-bpmn-sdk,
│                        #   etzhayyim-sdk (RW-free substrate, ADR-2605172000+2605172100)
│                        #   kuni-umi      planetary-infra producer    (ADR-2605201400)
│                        # Tier-B religious-corp actors (27): each has ADR + manifest + cells + lex.
│                        #   See Status § "Tier-B actors" for the full roster (name · purpose · ADR).
│                        #   Per-actor gates/prohibitions live in each actor's ADR + 20-actors/<name>/CLAUDE.md.
├── 30-graph/            # graph-schema, kagami, risingwave-udf, vectorization
├── 40-engine/           # Rust workspaces: kami-engine, llm,
│                        #   kotoba (storage substrate engine — git subrepo of
│                        #   github.com/etzhayyim/kotoba; 17 crates Apache-2.0;
│                        #   subsumes ipfs-pinner / nats-jetstream-* / mst-projector
│                        #   / lancedb-wasm / tonbo / etzhayyim-xrpc-proxy /
│                        #   libsignal wrappers; kotoba-llm local-inference
│                        #   constitutionally disabled per ADR-2605215000 +
│                        #   Charter Rider §2(i); ADR-2605262130 Phase 0)
├── 50-infra/            # SEEDED: geth-private, holochain, ipfs, blockscout,
│                        #   k8s/atproto-pds, k8s/murakumo-kubelet (migrated 2026-05-17),
│                        #   lancedb-wasm, yata, tonbo,
│                        #   nats-tiered-storage, nats-jetstream-{objectstore-s3, kv-resp},
│                        #   sveltejs-adapter-wasm, spin-tinygo-flight
│                        # SUBSTRATE (ADR-2605171800 + 2605172100 + 2605172200):
│                        #   etzhayyim-did-web/ (CF Worker, LIVE 2026-05-17T03:25Z)
│                        #   mst-projector/   (Stage 3, scaffold)
│                        #   ipfs-pinner/     (Stage 4, scaffold)
│                        #   l2-anchor-contract/ (Stage 5a, Foundry Solidity)
│                        #   anchor-cron/     (Stage 5b, K8s CronJob)
│                        #   etzhayyim-paymaster/ (ERC-4337, Foundry Solidity)
│                        #   openmail-postage/ (Postage.sol, Foundry, Phase 1 scaffold)
│                        # RELIGIOUS-CORP CONSTITUTIONAL (ADR-2605192100 wave, 2026-05-19):
│                        #   etzhayyim-charters-compliance/ (Council attestation single SoT)
│                        #   etzhayyim-tithe-router/        (10% donation → Public Fund atomic split)
│                        #   etzhayyim-public-fund/         (5-of-7 Safe + 1 SBT = 1 vote)
│                        #   etzhayyim-land-registry/       (geth-private + Base L2 ERC-721 mirror)
│                        #   etzhayyim-force-authorization/ (Transparent Force, 1 SBT = 1 vote)
│                        #   murakumo/fleet.toml            (10-node cell placement)
├── 60-apps/             # open-*, public-*, atproto, ameno, yoro, comfyui, watashi
│                        # FIRST RW-FREE REFERENCE IMPL: open-isco/rw-free/
│                        # MAC MINI FLEET: comfyui/ (migrated 2026-05-17)
│                        # RELIGIOUS-CORP:
│                        #   etzhayyim-transparent-force-rd/ (open-source R&D registry per ADR-2605192315)
├── 70-tools/            # etzhayyim-cli, cdn
│                        #   charter-rider-applicator/      (retro-active Rider applier, ADR-2605192200)
├── 90-docs/             # CLAUDE.md (docs rules), adr/, baien/
├── CHARTER-RIDER.md     # Apache 2.0 + Charter Compliance Rider v2.0 (per ADR-2605192200)
├── COUNCIL.md           # 5-seat Bootstrap Council roster (per ADR-2605192300)
├── COUNCIL-BOOTSTRAP-RFP.md  # 30-day public RFP for Seats 2-5 (2026-05-20 → 2026-06-19)
├── LANDS.md             # 4-layer permanent land record roster (per ADR-2605192245)
├── CLAUDE.md            # this file
├── deps.toml            # SSoT for [platform.operating_entity] + monorepo state
├── LICENSE              # Apache 2.0 (NOTICE/CHARTER-RIDER.md adds Rider conditions)
├── MEMBERS.md           # 信者 dual-permanent record (per ADR-2605172600)
├── README.md            # public-facing
├── lefthook.yml         # pre-commit (trailing-ws + EOF; full hooks pending)
└── .gitignore
```

## ADR Authority (per ADR-2605170900)

**This repo is canonical for religious-corp open ADRs.**

- ADR placement matrix → `90-docs/adr/README.md`
- ADR ID convention → `90-docs/CLAUDE.md` § "ADR ID Convention"
- Template → `90-docs/adr/template.md`

## Do Not

- Do not introduce legacy organisation-specific prefixes in newly authored code. Use `etzhayyim-` or no prefix. Existing seeded files with legacy prefixes will be renamed in a follow-up cutover.
- Do not weaken the Apache 2.0 license default. Religious-corp public-interest activity requires permissive license.
- Do not weaken the Charter Compliance Rider v2.0. The 8 prohibited categories (§2(a)-(h)) and 三層 enforcement (L1 license / L2 便益 / L3 評価) are constitutional invariants per ADR-2605192200 v2.0.
- Do not add Charter Rider to 3rd-party vendored code (`lib/`, `vendor/`, `*-fork/`). Apache 2.0 §4 requires preserving original NOTICE of 3rd-party works. `charter-rider-applicator` already skips these patterns.
- Do not introduce `transfer()` / `burn()` / `setOwner()` to `LandRegistry.sol`. Donated land is constitutionally inalienable (waqf-equivalent, ADR-2605192245).
- Do not propose proprietary 兵器設計 or covert force operations. ADR-2605192100 §1.12.B constitutional invariant requires open-source + on-chain 監視 + 1 SBT = 1 vote.
- Do not include the Book of Revelation (黙示録/啓示の書) or eschatological content as religious doctrine. Per ADR-2605192100 §1.15, etzhayyim is non-eschatological.
- Do not commit secrets. Private DID key lives in macOS Keychain (`service=etzhayyim, account=DID_PRIVATE_KEY_ED25519`) + 1Password mirror.
- Do not introduce RunPod / Vertex AI direct / OpenAI direct (without Murakumo proxy) / Anthropic-direct from vendor key / Linode GPU / AWS Bedrock direct / any commercial GPU rental into religious-corp inference paths. ADR-2605215000 makes Murakumo fleet (LiteLLM 127.0.0.1:4000 + EVO-X2 LAN 192.168.1.70 + per-node Ollama gemma3:4b) the sole inference SSoT. Vendor (`etzhayyim.com`) keeps its commercial GPU pool for paid SaaS workloads; religious-corp callers must not invoke vendor RunPod paths (consent capability boundary).
- Do not rename `gftd-*` identifiers in `50-infra/cluster/murakumo/` or `20-actors/magatama/py/` outside the Step 8 cutover wave. Per ADR-2605214000 §3 + ADR-2605215000 §4, the renames are itemised in `MIGRATION-NOTES.md` files and must execute as one atomic PR after legal registration (repo-root CLAUDE.md §Status row 8). Partial rename breaks runtime (env vars + config dir + DNS suffix are interdependent).

## Baien tooling index (2026-05-23 wave)

| Tool / dir | Purpose | Key ADR |
|---|---|---|
| `e7m bench micro` | 15-prompt verifiable smoke for baien (`70-tools/scripts/bench/baien-microbench/`) | ADR-2605092350 |
| `e7m bench core4` | lm-eval-harness Core 4 (IFEval / GPQA / MMLU-Redux / Global PIQA) via `lm_eval_wrapper.py` (inductor probe suppressed) | — |
| `e7m bench distill` | LangGraph ReAct loop: analyze → fetch_dataset (HF, default) **or** select_teacher (fallback) → SFT (peft+trl LoRA on bf16 master) → microbench eval. `commit_node` appends `90-docs/baien/distilled-models.jsonl` → codegen → `llm-model-registry-distilled.ts` | ADR-2605231300 |
| `e7m bench rope-extend` | Stage 1 of context extension — runs `microbench_long.py` under 3 RoPE configs (baseline / linear×4 / NTK×4) and emits side-by-side pass matrix | ADR-2605231600 |
| `bgp-submit --generator hunyuan3d|pixal3d` | baien-graft 3D dataset pipeline; two generators (Hunyuan3D-2 default / TencentARC Pixal3D-T cascade@512) | ADR-2605202115 |
| `etzhayyim_organism.sensors.charter_rider.scan()` | Canonical §2(a)..(h) content scanner; used by `baien-distill.validate` and recommended for any pipeline that ingests / generates text into first-party artifacts | ADR-2605192200 |
| `70-tools/scripts/llm-registry/gen-distilled-entries.mjs` | distilled-models.jsonl → `llm-model-registry-distilled.ts` codegen (2-phase ship: manifest + reviewer-gated TS) | — |

Snapshot artifacts (run results) live under `90-docs/baien/`:
- `frontier-bench-snapshot-260523.md` — frontier-LLM §A reference + baien microbench results
- `context-extend-snapshot-260523.md` — rope-extend Stage 1 results stub (awaits run)
- `distilled-models.jsonl` — committed adapter manifest (codegen source)

## Future Work

- **lefthook hooks** full set (adr-validate, docs-registry, lint-dangerous-query, llm-model-ssot)
- **GitHub Actions CI**: lint / type-check / build / test per layer
- **Dependabot** for npm + cargo + uv ecosystems
- **`90-docs/_registry/docs.json`** generator + validator
- **baien-distill Stage 2/3** (YaRN + LoRA, LongRoPE continual) per ADR-2605231600
- **Core 3 bench strategy revision** — switch from `_generative` (~28h/task) to `_completions` (loglikelihood, ~30 min) for next baien snapshot

## Substrate boundary (CRITICAL — ADRs 2605172000 + 2605172100 + religious-corp wave)

This repo is **blockchain-self-contained**. Hard rules enforced by ADRs and (future) CI hooks:

| Concern | Allowed | Prohibited |
|---|---|---|
| State | AT Protocol MST + IPFS + Base L2 anchor | RisingWave / Postgres / Kysely / centralized DB |
| Payment | USDC on Base L2 + ERC-4337 Smart Account + TitheRouter (10% auto-split) | Stripe / PayPal / Square / fiat processors |
| Payment purpose | `donation` / `kisha` / `grant` / `tithe` / `escrow-refund` + (SBT↔SBT internal carve-out) `internal-purchase` / `internal-subscription` / `internal-promo` | `subscription` / `purchase` / `tip` for external; commercial sale for SaaS tier |
| Advertising | etzhayyim 自身の religious 活動 案内 (internal-promo) のみ | 第三者広告 / AdSense / Meta Pixel / アフィリエイト / GA4 広告連携 |
| Identity | did:web:etzhayyim.com + did:plc + WebAuthn passkey + Adherent SBT | server-issued JWTs without DID binding |
| License | Apache 2.0 + Charter Compliance Rider v2.0 (`/CHARTER-RIDER.md`) | Apache 2.0 alone (Rider required) / proprietary / no-NOTICE |
| Charter compliance (3-tier) | ChartersComplianceRegistry attestation flow + Council Lv6+ ≥3 multisig | bypass of three-tier enforcement (L1 license / L2 便益拒否 / L3 評価=0) |
| Land trust | etzhayyim Land Registry 4-layer (Base L2 NFT + geth-private + IPFS + LANDS.md) | transfer / burn / sale / private ownership of donated land |
| Religious force | Transparent (on-chain log + open-source + 1 SBT = 1 vote) | Proprietary / covert / independent military arm / state military alliance |
| Content (Eros) | 合意ある成人性表現 (産霊 / 雅歌 整合) | 児童性的表現 / 非合意 / Wellbecoming 違反 addictive design |
| Content (Gore) | 教育 / 歴史 / 宗教 / 人権告発 文脈の暴力 imagery のみ | 無目的暴力 entertainment / desensitization 設計 |
| Confidentiality (ADR-2605181100) | `app.etzhayyim.encrypted.*` (XChaCha20-Poly1305 envelope + Signal-wrapped per-recipient keys, DID-bound) | Plaintext private records on MST / app-side libsignal / noble-ciphers imports |
| Substrate client imports | Only via `@etzhayyim/sdk` | Direct `@atproto/api` / `viem` / IPFS client / `@noble/ciphers` / `@signalapp/libsignal-client` from app code |
| Substrate engine | `kotoba` (`40-engine/kotoba/`, ADR-2605262130) — content-addressed Datalog + Pregel + Signal + WASM Component Model in one Rust workspace; 17 crates; canonical impl of every substrate primitive (supersedes yatachain composition spec ADR-2605231400) | inventing a parallel substrate engine name without ADR; importing yatachain / RW / Lance / Iroh as projection backends |
| Read path (hot-path queries) | `kotoba-kqe` arrangements (EAVT / AEVT / AVET / VAET) directly over content-addressed blocks; no separate projection layer (ADR-2605262130 D7 + N8 supersedes ADR-2605231500 yatachain-projection rules). First L1-projection app `feed-discover` (50-infra/mst-projector/projection/, ADR-2605231902) preserved unchanged; read backend migrates to kotoba-kqe at Phase 2.5 | RisingWave / Postgres / Lance / DuckDB / SQLite as projection or cache; "yatachain-projection" marker comments — both deprecated by ADR-2605262130 |
| Server-side signing capability (ADR-2605231525, Council ratify pending) | Member wallet sign (USDC), member passkey-derived ES256 (session), community-operator DID (bulk-ingest), Council 5-of-7 Safe (governance), read-only RPC / firehose subscribe / IPFS pin / static asset serve | Any platform-held private key, master credential, or signing token in etzhayyim-operated Workers / pods / CronJobs / CI / hosted bots. Exemption: `// no-server-key: read-only` marker on documented Stage handover rollback windows. Enforced by `e7m verify` (9th invariant) |
| GPU / inference | LiteLLM gateway (127.0.0.1:4000) + EVO-X2 LAN (192.168.1.70) + per-node Mac mini Ollama gemma3:4b (per ADR-2605215000) | RunPod / OpenAI direct / Vertex AI direct / Anthropic-direct from vendor key / Linode GPU / AWS Bedrock direct / any commercial GPU rental |

Apps that need fiat / paid features call an external backend via XRPC consent-capability (progressive enhancement, **non-profit領収書 用途のみ** per ADR-2605192115 §4). Open app remains operational without it.

## SSoT pointers

- `deps.toml` — operating entity, substrate rules, L2 contracts, DNS records, ADR registry, module registry
- `90-docs/CLAUDE.md` — docs system rules + ADR placement policy
- `90-docs/adr/README.md` — ADR index
- `90-docs/adr/2605192100-etzhayyim-mission-charter.md` — religious-corp 上位憲章 (mission + constitutional constants)
- `90-docs/adr/2605192200-etzhayyim-ip-free-release-charter-rider.md` — License + Rider 正本 spec (v2.0)
- `90-docs/adr/2605192245-etzhayyim-global-land-sovereignty.md` — Land Trust 4-layer architecture
- `90-docs/adr/2605192415-etzhayyim-religious-corp-daemon-architecture.md` — Pregel cell catalog + Murakumo deployment
- `/CHARTER-RIDER.md` — license addendum canonical text
- `/LANDS.md` — Land Trust roster
- `/MEMBERS.md` — 信者 roster
- `50-infra/murakumo/fleet.toml` — religious-corp cell placement (10 nodes × 15 cells)
- `20-actors/etzhayyim-sdk/README.md` — SDK API surface + hard rules
- `20-actors/magatama/cells/README.md` — religious-corp Pregel cell catalog
- `90-docs/adr/2605262130-kotoba-storage-substrate-unification.md` — canonical storage substrate engine (kotoba); supersedes yatachain composition + projection layers; no RisingWave
- `40-engine/kotoba/README.md` — kotoba upstream README (17 crates)
- `10-protocol/yatachain/SPEC.md` — (superseded by ADR-2605262130; deprecation banner Phase 0.5; retained one R-cycle then archived)
- `90-docs/adr/2605231400-yatachain-holochain-iso-substrate.md` — (superseded by ADR-2605262130)
- `90-docs/adr/2605231500-yatachain-projection.md` — (superseded by ADR-2605262130; no projection layer under kotoba)
- `90-docs/adr/2605231902-feed-post-membrane-and-feed-discover-projection.md` — first end-to-end MST §4 membrane + L1-projection app (app.bsky.feed.post); **preserved unchanged**; Phase 2.5 read-path migration to kotoba-kqe per ADR-2605262130
- `90-docs/adr/2605214000-etzhayyim-murakumo-mesh-no-vke-and-lexicon-port-rules.md` — Murakumo distributed cluster (no-VKE mesh) + lexicon port verdict taxonomy
- `90-docs/adr/2605215000-etzhayyim-inference-murakumo-only-no-runpod.md` — etzhayyim inference Murakumo-fleet-only (no RunPod)

## References

- This repo (public): https://github.com/etzhayyim/root
- Domain landing: https://etzhayyim.com
- DID resolver: https://etzhayyim.com/.well-known/did.json (LIVE; CF Worker at zone `etzhayyim.com`, DNS AAAA `@` `100::` proxied, deployed 2026-05-17T03:25Z)
