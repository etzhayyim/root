# etzhayyim/root — CLAUDE Index

This monorepo is the **canonical home for religious-corp open ADRs** per ADR-2605170900 (this monorepo, `90-docs/adr/`).

## Identity (CRITICAL)

- **Operating entity** (this repo's owner): `etzhayyim` (canonical)
  - Aliases: `amanomibashira` / `天御柱` / `עץ חיים` (Tree of Life) / `etz hayim` / `etzhayim` / `etz chaim` / `エツ・ハイム`
  - Form: 宗教法人 (任意団体 / unincorporated religious voluntary association)
  - Registry: On-chain (blockchain-registered constitution and member roster); NOT registered under 日本国 宗教法人法
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

**Religious-corp constitutional wave complete** (2026-05-19/20). Foundation milestones:

| Step | Status |
|---|---|
| 1. etzhayyim.com 取得 (CF Registrar) | ✅ 2026-05-15T12:08Z |
| 2. github.com/etzhayyim org 作成 | ✅ 2026-05-10T14:23Z |
| 3. github.com/etzhayyim/root 作成 | ✅ 2026-05-15T12:20Z |
| 4. Scaffold (LICENSE/README/CLAUDE.md/deps.toml/.gitignore/lefthook.yml) | ✅ |
| 5. Content seed (Tranches A-E + Wave 2) | ✅ |
| 6. CI / wrangler / package.json `repository` field sed | ✅ done (11 pkg.json + 2 wrangler.jsonc) |
| 7. did:web publish (DNS + wrangler deploy) | ✅ 2026-05-17T03:25Z (verified via curl + dev.uniresolver.io) |
| 8. `amanomibashira` → `etzhayyim` cutover (code identifiers) | ✅ 2026-05-21 (118 files; alias docs preserved in CLAUDE.md/README.md/CHARTER-RIDER.md, 登記変更は別) |
| 9. Religious-corp constitutional ADR wave (13 ADRs, ADR-2605192100 .. 2605192415) | ✅ 2026-05-19/20 |
| 10. CHARTER-RIDER.md v2.0 + LANDS.md repo root | ✅ 2026-05-19 |
| 11. Charter Rider applied to 39 first-party Apache-2.0 packages | ✅ 2026-05-20 (78 NOTICE + symlink entries) |
| 12. Solidity contracts scaffold (charters-compliance / tithe-router / land-registry / public-fund / force-authorization) | ✅ 2026-05-19 (3 working .sol skeletons + 5 specs) |
| 13. Pregel cell catalog (15 cells) + cell-runner CLI + Murakumo fleet.toml | ✅ 2026-05-19 |
| 14. Lexicon registration (charter-* / land-* / force-* / eros-gore-* / steward-* / public-fund + tithe + payment narrow) | ✅ 2026-05-20 (28 Lexicons + 1 modified) |
| 15. Constitution.sol religious-corp constants wiring (38 const + 16 mutable) + ConstitutionKeys library | ✅ 2026-05-20 (110/110 tests) |
| 16. lefthook lint hooks (no-advertising / no-purchase-purpose / paywall-warn / charter-rider-notice) | ✅ 2026-05-20 (4 hooks) |
| 17. Religious-corp wave Foundry consolidation + DeployReligiousCorp.s.sol + Anvil smoke ✓ | ✅ 2026-05-20 (chainId 31337 verified) |
| 18. Bootstrap Council Seat 2-5 (30-day public objection period 2026-05-20 → 2026-06-19) | 🟡 RFP OPEN — see [`COUNCIL.md`](COUNCIL.md) + [`COUNCIL-BOOTSTRAP-RFP.md`](COUNCIL-BOOTSTRAP-RFP.md) |
| 19. Base Sepolia testnet deploy (funded private key + RPC required) | ⏳ post-Council |
| 20. Mainnet deploy + Phase 2 governance reference wiring | ⏳ post-testnet |
| 21. Murakumo no-VKE mesh placement contract + vendor→religious-corp lexicon port rules (ADR-2605214000) | ✅ 2026-05-21 |
| 22. etzhayyim inference Murakumo-fleet-only invariant + pymagatama RunPod-free audit (ADR-2605215000) | ✅ 2026-05-21 |
| 23. CHARTER-RIDER.md §2(i) — no commercial GPU rental constitutional invariant (Council Lv6+ supermajority to amend) | ✅ 2026-05-21 |
| 24. 20-actors substrate-fit audit (kuni-umi clean / shinka 16 findings / yoro 42 findings incl. 8 active Stripe REJECT) | ✅ 2026-05-21 — see [`20-actors/AUDIT-RUNPOD-RW-2026-05-21.md`](20-actors/AUDIT-RUNPOD-RW-2026-05-21.md) |
| 25. maps_sentinel_murakumo M1 T0 preprocessing pipeline (986 LoC, 34/51 tests pass + 17 skip-on-rasterio) | ✅ 2026-05-21 (ADR-2605215100 §4 M1) |
| 26. UNSPSC actor-as-organism Wave 1 (joucho heartbeat-cadence Python port + c10101500 reference) | ✅ 2026-05-23 (ADR-2605232345; `pymagatama.organism`) |
| 27. UNSPSC actor-as-organism Wave 2 (18,342 mass-deploy via `UnispscOrganismFleetCell` shard-0/1/2 + per-code joucho personality + follower stub) | ✅ 2026-05-24 (ADRs 2605240000 / 2605240015 / 2605240030; manifests-ready, apply pending) |
| 28. UNSPSC organism post sink (NDJSON queue + TS drainer interface) + k8s DaemonSet manifests | ✅ 2026-05-24 (ADR-2605240100; `50-infra/k8s/unispsc-organism-fleet/`; drainer sidecar Wave 3) |
| 29. Ecosystem self-reflection: `KaizenObserverCell` + 6 rules + KaizenProposal NDJSON + PR agent contract | ✅ 2026-05-24 (ADR-2605240200; `pymagatama.organism.kaizen`; PR agent Wave 4) |
| 30. Dataset CID substrate (DataLad + git-annex `directory` remote + sidecar IPFS pinner; HF `add` E2E + 4 fetchers `pull hf\|geonames\|osm\|wikidata` + PDS `datasetPin` emit) | ✅ 2026-05-24 (ADR-2605241500; `70-tools/e7m-dataset/` + `app.etzhayyim.substrate.datasetPin`; smoke map CID `bafkrei…f5z2q`; HF add map CID `bafybeigeput…fr7a` on `hf-internal-testing/fixtures_image_utils@8665b8ad` 9 files / 1.5 MiB; Kubo on `/Volumes/260317`; 28/28 pytest; PDS emit defaults to dry-run, real wiring via `ETZ_E7M_PDS_{SESSION,AUTH,DID}`; Charter Rider scanner warn-only until pymagatama installed) |
| 31. yatachain Tier D blob primitive (`Etzhayyim.uploadBlob` TS + `Etzhayyim.upload_blob` Python; bit-identical `{cid,sizeBytes,mediaType}` receipt) + gsplat trainer B2 → IPFS swap (`USE_PYMAGATAMA_SUBSTRATE_BLOB=1`) + yoro `@atproto/api` → `@etzhayyim/sdk/atproto` facade closure (6 callsites) | ✅ 2026-05-23 (ADR-2605232400; `20-actors/etzhayyim-sdk` + `20-actors/magatama/py/src/pymagatama/substrate/`; 13 new tests — 7 vitest + 6 pytest; gsplat `_blob_upload`/`_blob_download` dispatch on `ipfs://` scheme; SDK 111 → 118, pymagatama.substrate 18 → 24; Tier A + B + D end-to-end SDK-mediated, Tier C still ADR-2605222330 carve-out) |
| 32. Peer-resolvable agentURI substrate — 5-layer model (ERC-8004 L5 settled + libp2p L2 transport + AT Protocol XRPC L1) + Phase A actor registry collapse + Phase B dataset-pinner libp2p Multiaddr dual-publish + GftdAgentRegistry.sol (ERC-8004-shape) + iroh sibling PoC | ✅ 2026-05-24 (ADR-2605241800; `10-protocol/etzhayyim-libp2p/` + `50-infra/etzhayyim-did-web/src/registry/infra-actors.ts` (8 actors) + `50-infra/etzhayyim-chain-contracts/src/GftdAgentRegistry.sol` (15/15 forge tests pass); 2-peer Kubo loopback PoC bytes-identical (host `12D3KooW…AiEc` / consumer `12D3KooW…1bdX`); iroh 0.28.1 2-node PoC bytes-identical (host `35hn75v…rx6q` / consumer `lafzhys…okia`); per-actor DID Worker count 8 → 1 root via `etzhayyim.com/actor/<slug>/did.json`; Phase C (HTTPS retirement) + Phase D (yatachain witness quorum) post-Council) |
| 33. wadachi (轍) autonomous-mobility R&D actor — kuni-umi-S4 ADR-2605201800 自律走行 carve-out fulfillment; R0 scaffold only (no vehicles, no code, no lexicons); 12 constitutional gates (G1-G12) + 8 non-goals (N1-N8) declared **before** capability lands. SAE J3016 Level ceiling = 4 (Level 5 = constitutional non-goal). 4-phase roadmap (R0 scaffold → R1 intra-site ≤1 m/s → R2 inter-site Level-3 driver-in-seat → R3 adherent Level-4 ODD + survey-altitude aerial). Each subsequent R-phase requires its own ADR. | ✅ 2026-05-23 (ADR-2605242000; `20-actors/wadachi/` scaffold — README + CLAUDE.md + manifest.jsonld + empty `cells/`; lexicon namespace `app.etzhayyim.wadachi.*` reserved-deferred; DID `did:web:etzhayyim.com:wadachi`; sibling of `kuni-umi`) |
| 34. **First end-to-end yatachain §4 membrane + L1 projection** for `app.bsky.feed.post` — closes the original symptom ("yatachain ベースで投稿を表示するには"). `70-tools/seed-post/` operator CLI + L2 Rego (`00-contracts/policies/app/bsky/feed/`, 8/8 `opa test`) + L3 Pregel cell (`20-actors/magatama/cells/feed_post/`, 18/18 pytest) + sidecar verdict lexicon + `FeedPostCell` on `levi` + `feed-discover` projection (mst-projector extension, lexicon `app.etzhayyim.projection.feedDiscover`, manifest + REBUILD.md, **L1-projection conformance** via CI golden replay) + membrane→projection wire (`applyVerdictEvent` drops `reject` from Discover, annotates `approve`/`escalate`). yoro-xrpc-adapter PDS_URL cutover to atproto.etzhayyim.com deployed. Seed-post end-to-end verification blocked on operator Keychain provisioning. | ✅ 2026-05-23 (ADR-2605231902; 31/31 mst-projector node:test + 25/25 yoro-rw-free vitest + 18/18 feed_post pytest + 8/8 Rego opa test all pass; live edge serves header `x-etzhayyim-substrate: mst-ipfs-l2`) |
| 35. **Gov coverage 5-layer taxonomy + 3-app L3 edge substrate-port + L5 routing-around ladder (3/3 cells scaffolded)** — closes "この世の全ての政府機関、行政手続きの pregel, mcp の実装カバレッジ?" question with a 5-layer model (L1 namespace / L2 COFOG×country / L3 public-services hub / L4 ingest / L5 routing-around). Migration recovery (36 files across gov / lawfirm-admin / legal-entity) + 5 Lexicons (`app.etzhayyim.gov.{agency,official,consult,municipality,procedure}`) + L1 fill-out 140→196 (100% ISO-3, +448 BPMN files) + 3 L4 ingest scripts emitting 421 demonstrator records + 3 L3 thin-edge substrate-ports (Kysely→MST for gov-mcp-component, DID/NSID/dispatcher renames for lawfirm-admin + legal-entity, all 6 .ts files runtime gftd.ai-free) + L5 ladder (member_registry / religious_marriage / religious_corp_taxation, all 3 Council-attestation-gated scaffolds with import-time RuntimeError until activation) + 2 ghost ADRs back-authored (2605212100 migration batch + 2605214000 Murakumo no-VKE mesh + atomic identifier cutover rules) | ✅ 2026-05-25 (ADRs 2605212100 / 2605214000 / 2605242330 / 2605250100 / 2605250200 / 2605250300; L1 100% / L2 1229 files + 202 ingest records / L3 3 apps ported / L4 9 scripts / L5 0→3 cells; commit pending) |
| 36. **Baien federated training via ameno WebGPU — R0 scaffold (smartphone-participable LoRA round)** — 5-layer design (L1 WebGPU LoRA-only autograd / L2 ameno PWA loop / L3 lexicon + DID / L4 Murakumo aggregator / L5 MST + L2 anchor settlement) honouring all constitutional invariants (G1 trunk+encoders frozen / G2 LoRA rank-16 on q/k/v/o_proj only / G3 IPFS+MST upload route / G4 member passkey ES256 / G5 Murakumo-only aggregation / G6 on-device Charter Rider scan / G7 Adherent SBT gate / G8 Wellbecoming gate / G9 Byzantine median/Krum + DP-Gaussian / G10 round-frozen baseModelCid / G11 no per-delta payout). 6 R0 artifacts: ADR-2605242600 + lexicon (`app.etzhayyim.baien.distributedTrainDelta`) + `ameno/src/train.ts` throw-on-use scaffold + `baien-distill/nodes/federated_aggregate.py` dry-run-only planner + `magatama/cells/baien_federated_aggregator/` import-time `RuntimeError` (L5-routing-around pattern from row 35). R1..R4 phased activation, each subsequent phase requires its own ADR (matches wadachi R0 pattern from row 33). | ✅ 2026-05-24 (ADR-2605242600; baien-distill graph unchanged in R0; aggregator cell gated on Council attestation per R2 activation rule; commit pending) |
| 37. **Baien ternary silicon Wave 1 — iwakura inference ASIC + fuigo training ASIC + tsukuru fab 8-equipment Pregel charter ("半導体は生命のコア")** — first-party RTL/CAD/mechanical/robotics for ternary ASICs and 8 fab equipment categories (litho/depo/etch/implant/CMP/metrology/test/packaging), all Apache 2.0 + Charter Rider, manufactured via tsukuru.etzhayyim.com (NOT tukuru.gftd.ai — religious-corp side, already serves ISIC C26 + EUV lane per ADR-0061). iwakura = 256×256 multiplier-less ternary PE @ 65 Tera-ternary-ops/s + radix-3 5-weights/byte packing + LPDDR5X-7500 120 GB/s + 3-5 W edge target. fuigo = 1024×1024 ternary forward + 8k BF16 backward dual-SA + Lion hardwire + HBM3e 96 GB / 4.8 TB/s + libp2p NIC on-die (Murakumo no-VKE mesh native). Phase 1 = RTL + cocotb sim only (Verilator open-source toolchain; ~620-gate PE vs ~5,200 for INT8 mult = 8.4× density; 75-case exhaustive cocotb test). 4 ADRs + 50-infra/silicon/ scaffold (16 files) + 8 silicon_litho..packaging Pregel cells + 4 Lexicons (chipManufacturingAttestation / silenForceReview / fabEquipmentTelemetry / waferLotAttestation). All cells scaffold-only until Council fleet.toml node (judah/dan/naphtali/simeon/levi) + EUV/implant silen-force baseline review. Silicon = land-trust-analogue inalienable (no sale, lease to SBT holders only). | ✅ 2026-05-24 (ADRs 2605242500 / 2605242515 / 2605242530 / 2605242545; commit `b6e2cac1e` 54 files; deps.toml + adr/README registry parity restored) |
| 38. **Silicon Wave 2 upstream supply chain — 原材料調達 + 輸送の全 robotics 化** — extends Wave 1 from chip + fab to upstream. 8 categories (wafer-source / gas / photoresist / metals / consumables / mask / amhs / logistics) all robotics-orchestrated. NO new robot class except **Funamori (船守)** = kuni-umi 8th class for external-ocean bulk cargo (IMO MASS Degree 3 cap; 12 constitutional gates incl. §2(a) no naval weapons + §2(g) LNG/NH3/methanol fuel only + MARPOL Annex I-VI + BWMC). Other 7 reused: kuni-umi Otete/Quad (mining via task-program extension), Hitogata (clean-room class 1), Mimi (metrology), Sora (drone), Hoshi (orbit), wadachi (ground). 17-step end-to-end Pregel chain: miningLot → 6 rawMaterialAttestation → 8 waferLotAttestation → chipManufacturingAttestation. Phase 2a priority = silicon_mask + silicon_photoresist (EUV chokepoint of chokepoint — Hoya+AGC mask blank duopoly + JSR/TOK/Shin-Etsu/Sumitomo EUV resist oligopoly). 10 ADRs + 8 supply-chain subdirs + 8 silicon_wafer_source..logistics Pregel cells + 4 Lexicons under `app.etzhayyim.silicon.supply`. Charter Rider §2 risk: HIGH metals (§2(g) rare-earth env + §2(a) W ammo) + mask (§2(a) Mo/Si laser-weapon optics); MEDIUM gas (CWC Sch 3 + SF6 GHG ≥95% recovery) + photoresist (VOC); LOW wafer-source/consumables/amhs/logistics. | ✅ 2026-05-24 (ADRs 2605242700 / 2605242715 / 2605242730 / 2605242745 / 2605242800 / 2605242815 / 2605242830 / 2605242845 / 2605242900 / 2605242915; commit `341b6824b` 51 files; deps.toml + adr/README registry parity restored; 14 silicon ADRs + 16 silicon_* cells + 8 silicon Lexicons cumulative) |
| 39. **Baien federated R1 ADR + R1a framework (WebGPU LoRA backward-pass PoC scaffolding)** — extends row 36 (R0 scaffold). R1 ADR (ADR-2605242630) fixes the device matrix (iPhone 12 / Adreno-650+ Android / M-series desktop), three numerics fallback paths (A fp16 / B fp32-grad-accum DEFAULT for mobile / C full fp32), OPFS Adam-state on-disk format, 16-example microbench shard, success criteria (three consecutive `lossAfter < lossBefore × 0.98`). R1a framework lands every piece **except** the WebGPU autograd dispatch itself (R1b): `train.ts` rewritten as orchestration barrel (shard load + CID verify → Charter Rider scan → pre-eval → numerics-path warm-up → throw with R1b marker → post-eval scaffold); `train/opfs.ts` (computeRoundId + openRoundDir + commit/abort sentinels); `train/device.ts` (detectDeviceClass UA+adapter probe + selectNumericsPath sweep A→B→C with [0.99, 1.01] ratio gate, mobile-skip A); `train/shard.ts` (loadShard CID-verify + 16-row fixed-size enforce + 3 graders exact-match/regex/token-set); `train/charter-rider.ts` (5 categories 2a/2b/2c/advertising/eschatology + JA prohibited regex; ≤5% rejection threshold); `train/kernels.ts` (3 WGSL sources — LoRA forward, LoRA backward dA+dB, Adam step with `exp2(t*log2(beta))` mobile-fp16-stable bias correction; dispatch wrappers throw with R1b markers); microbench shard committed at `90-docs/baien/r1-microbench-shard.jsonl` + `.cid` sidecar `sha256-b3582a53486b8438da88d86d16d95c9c0565628e9794d958b3a7506c97745bf7`. R1b = transformers.js layer-replacement OR tfjs-webgpu autograd bridge. `signDeltaManifest` + `publishDeltaRecord` remain throws (R2). | ✅ 2026-05-24 (ADR-2605242630 + R1a framework; `tsc --noEmit` clean; 85 lexicons validated; PR #274 R1 ADR pending merge; R1b dispatch wiring + per-device run-log capture remain) |
| 40. **gemma-coder-distill — Murakumo fleet gemma4:e4b の LangGraph コーディング適応 (EVO-X2 ROCm + peft+trl)** — fleet で実 serve 中の `gemma4:e4b` (8B Gemma 4 Effective 4B; CLAUDE.md/fleet.toml の `gemma3:4b` 表記はドリフト、judah Ollama 192.168.1.17:11434 で実機確認) を LangGraph specific に distill する初の non-baien 経路 (BitNet 専用 `baien-distill` とは別 model class)。`70-tools/gemma-coder-distill/` scaffold (LangGraph ReAct: analyze → fetch → validate → train → evaluate → commit、6 node、peft+trl bf16 LoRA r=16 on EVO-X2 ROCm 7.2.1 + Gemma4ClippableLinear inner `.linear` auto-resolve) + `70-tools/scripts/bench/langgraph-coding/` (exec-graded bench、8 prompts × 4 categories: stategraph / reducer / conditional×3 / interrupt×3、shared `_lib.py` extractor with unclosed-fence handling)。**Unsloth は不採用** (gate-1 probe 2026-05-25 で Windows ROCm 7.2.1 + Python 3.12 上の pip dep resolution が CUDA-stack 前提依存で RecursionError 確定、evidence `90-docs/baien/probe_unsloth_rocm.json`)。**Claude Opus は HF Apache 2.0 indirect 経路のみ** (`lordx64/reasoning-distill-opus-4-7-max-sft` qwen-text format parser; 直叩きは ADR-2605215000 §1.2 で禁止)。**Baseline 2/8 (25%) on gemma4:e4b** で 4 antipattern が systematic に検出 (wrong `MemorySaver`/`Command` import paths / `compile(config=...)` hallucination / `set_entry_point(START)`); 20-row hand-authored antipattern-corrective SFT corpus が `data/antipattern-corrective.jsonl` に commit。**iter-00 quick E2E 完走** (6 hot-fix を越えて: parents[5] install-root / Gemma4ClippableLinear LoRA / trl Windows cp1252 via PYTHONUTF8 / safetensors numpy ctypes int32 overflow >2GB tensor → `torch.save` bypass / bench runner path via `GEMMA_CODER_BENCH_RUNNER` env / dry-run synthetic padding); 5 steps × 20 ex × 1 epoch / loss=2.363 / merged adapter 完成 / post-distill bench 2/8 (20 ex × 1 epoch では補正定着せず、HF Opus fetch が silent 0 yield — fix landed: qwen-text parser format-aware streaming)。**iter-01 full** (5020 ex × 2 epoch、~100 min wall) を detached PowerShell Start-Process で background 実行中、done marker poll で完了通知待ち。 | 🟡 2026-05-25 (ADR-2605250400 accepted; commits `3523c0ed8` / `51e0e29a6` / `9c2b40ad9` / `efc841358` / `0383cc6d2`; iter-01 in-flight) |
| 41. **yakushi (薬師) — religious-corp first-party 製薬 R&D Wave 1 + Wave 1b (OTC 12 化合物 × 3 dosage forms)** — kuni-umi-S6 化学物質生産 carve-out には収まらない独立 Tier-B actor として「医薬品」を初めて religious-corp が自前で覆う wave (silicon Wave 1+2 と同 scope class)。actor `yakushi` (薬師: Heian 朝廷の典薬寮系譜 + Yakushi Nyorai medicine-as-religious-practice echo) で **Wave 1** = OTC 抗アレルギー点眼薬 triplet (クロモグリク酸 Na 1965 Fisons / ナファゾリン HCl 1942 Ciba / クロルフェニラミン maleate 1949 Schering) を constitutional 最低リスク template に固定、**Wave 1b** = +9 化合物に拡張 (analgesic: acetaminophen 1893 / aspirin 1897 Bayer / ibuprofen 1969 Boots / oral H1: diphenhydramine 1946 / cetirizine 1987 UCB / loratadine 1988 Schering / H2: famotidine 1986 Yamanouchi / topical: clotrimazole 1969 Bayer / diclofenac Na 1973 Geigy)。**全 12 化合物 G1 全 clearance** (PMDA/FDA/EMA all-3 OTC switched + ≥ 18 年 off-patent in all jurisdictions)、全 G6 clearance (Rx-only / controlled substance / biologic / NME 該当ゼロ)。**Charter Rider §2 全条項 clearance** — §2(e) anti-gatekeeping は constitutional 推進力 (yakushi の存在意義そのものが §2(e)(i)(ii) medical knowledge artificial restriction の counter-action)。**Wave 1b 明示的除外**: pseudoephedrine (CMEA precursor) / codeine (Rx) / hydrocortisone (steroid bioprocess Wave 2 候補) / sodium hyaluronate (発酵 bioprocess Wave 2) / omeprazole (chiral Wave 1c 候補) ― 全て別 ADR + Council Lv6+ supermajority 経由。**14 constitutional gates G1..G14 + 10 non-goals N1..N10 不変** — Wave 1b は API + dosage form extension のみで gate / non-goal の修正なし。**5 ADRs** (master 2605250500 + sub 2605250515/530/545 Wave 1 + 2605250600 Wave 1b) + **actor scaffold** (`20-actors/yakushi/` README + CLAUDE.md + manifest.jsonld with 3 Wave 1 + 9 Wave 1b reference APIs) + **12 Pregel cells** (10 Wave 1: pharma_{raw_material, api_synthesis, purification, qc, sterile_fill_finish, container, packaging, cold_chain, adverse_event, post_market_surveillance} + 2 Wave 1b: pharma_{tablet_manufacture, topical_formulation}、全 import-time RuntimeError multi-gate) + **8 lexicons** (`app.etzhayyim.pharma.{rawMaterialAttestation, apiSynthesisAttestation, purificationAttestation, qcAttestation, fillFinishAttestation, lotAttestation, silenPharmaReview, adverseEventReport}` ― Wave 1b で apiInn knownValues 3→12 + dosageForm field 10 knownValues 新設 + qcAttestation に dissolution/disintegration/friability/content-uniformity/viscosity/pH 追加 + silenPharmaReview scope に wave-1b-* triggers 追加 ― 新 lexicon 増加なし)。**Robotics class** = 既存 6 reuse (kuni-umi Hitogata class-A sterile + class-C clean、Otete chem-resist + cold-chain、Mimi pharma-analytical、silicon Wave 2 Funamori marine inheritance for 海外 R3+) + 新規 2 placeholder (Kusuko 薬子 single-use sterile autoloader R2+ / Sukoyaka 健やか patient-side cold-chain last-mile R3+)。**Murakumo fleet placement** (design-only at R0): naphtali (raw mat + cold chain)、zebulun (synthesis + purification)、levi (QC + AE + post-market)、joseph (sterile fill-finish + tablet)、simeon (container + topical)、dan (packaging) — 既存 6 ノード全再利用、silicon Wave 1 の `judah` 新ノード追加と対照的に新ノード追加なし。**4-phase roadmap R0→R3** (R0 scaffold this wave / R1 benchtop ≤1g + QP-equivalent on Council / R2 pilot ≤100g + Annex 1 facility + 3-batch media fill (sterile dosage forms only) + tablet-press / topical-mixer equipment qualification (Wave 1b) / R3 community-scale + 60-day public review + jurisdiction 薬事手続)。 | ✅ 2026-05-25 (ADRs 2605250500/515/530/545 Wave 1 + 2605250600 Wave 1b proposed; deps.toml ADR + module registry; adr/README.md index; 12 cells + 8 lexicons + 4 actor files; ~50 files committed) |
| 42. **yakushi Wave 1c — Chiral synthesis (omeprazole) + deferred OTC expansion (19 化合物 × 4 dosage forms)** — Wave 1b の 明示的除外 omeprazole (chiral resolution 複雑) + laxatives (zero synthesis route) + cough-expectorant を Wave 1c で実装。**API catalog 12 → 19 化合物** (omeprazole + PEG-3350 / docusate-Na / senna-extract / bisacodyl + guaifenesin / benzonatate)。**Chiral synthesis cell** (`pharma_chiral_resolution`, levi node): omeprazole S-enantiomer separation via crystalline-resolution-mandelate (L-mandelic acid salt, ~70% yield) or prep-HPLC-chiral (Chiralcel OD-H); enantiomeric purity ≥ 99.5% (ICH M7 Class 5)。**Liquid formulation cell** (`pharma_liquid_formulation`, joseph node): cough-expectorant syrups (guaifenesin 100 mg/5 mL, benzonatate 100-150 mg/5 mL) + laxative solutions (docusate Na liquid, post-reconstitution PEG 3350); non-sterile fill into amber bottles with dosing cups; microbial limit USP <61>/<62>, viscosity, pH QC。**Dosage forms 3 → 4** (eye-drop sterile + tablet + topical + NEW sachet-powder-for-reconstitution + oral-liquid-syrup + oral-suspension)。**Lexicon extensions only** (新 lexicon なし): apiInn knownValues 12→19 / purificationAttestation scheme に crystalline-resolution-mandelate / prep-hplc-chiral / SFC-supercritical 追加 / fillFinishAttestation dosageForm 10→13 / silenPharmaReview scope に wave-1c-chiral-resolution-baseline / wave-1c-laxative-formulation-baseline / wave-1c-cough-syrup-formulation-baseline / wave-1c-benzonatate-jp-marginal 追加。**G7 risk = NONE** — omeprazole route は OPCW Schedule 3 precursor 不要 (acetic anhydride 使用なし)、Wave 1b analgesics (acetaminophen/aspirin/ibuprofen) との大きな contrast。**Benzonatate PMDA jurisdiction margin** — Japan で Rx form 並行存在、USA/EMA では OTC cleared；PMDA OTC 申請中 (2023 年提出、2024-2025 年決定予定)、R1 phase で判断。**14 gates + 10 non-goals 不変** — Wave 1c も scope extension のみ。**6 ADRs cumulative** (master + Wave 1 4 sub + Wave 1b 1 + Wave 1c 1) + **14 Pregel cells cumulative** (10 Wave 1 + 2 Wave 1b + 2 Wave 1c) + **8 lexicons** (拡張のみ) + **manifest.jsonld** に `wave1cReferenceApis` section 追加 (7 APIs) + **deps.toml** に ADR 2605250615 + 2 module entries (pharma_chiral_resolution / pharma_liquid_formulation) + **adr/README.md** index 追加。 | ✅ 2026-05-25 (ADR 2605250615 proposed; 2 cells created + lexicons extended + deps.toml + adr/README.md + manifest.jsonld updated; ~15 new files + 5 lexicon updates + 3 deps.toml entries) |

## Repo Layout (Shannon-Optimal 8-Layer, ADR-2604251830)

```
etzhayyim/root/
├── 00-contracts/        # lexicons / bpmn / dmn / Rego policies / resources (JSON-LD)
├── 10-protocol/         # atproto, xrpc, lexicons-bundle, signal, did-etzhayyim,
│                        # wproto, at-client, signal-client,
│                        # yatachain (Holochain-iso composition spec, ADR-2605231400)
├── 20-actors/           # magatama (Pregel framework + host SDK +
│                        # unispsc_agents/ 18,345 LangGraph agents per ADR-2605171300),
│                        # magatama-go, kami-engine-sdk, effect-cypher,
│                        # etzhayyim-bpmn-sdk, etzhayyim-sdk (RW-free substrate per ADR-2605172000+2605172100),
│                        # kuni-umi (Tier-B planetary-infra producer per ADR-2605201400),
│                        # wadachi (Tier-B autonomous-mobility R&D, R0 scaffold per ADR-2605242000),
│                        # yakushi (Tier-B pharmaceutical R&D, R0 scaffold per ADR-2605250500;
│                        #   Wave 1 ref = OTC 抗アレルギー点眼薬 triplet: cromoglicate Na +
│                        #   naphazoline HCl + chlorpheniramine maleate)
├── 30-graph/            # graph-schema, kagami, risingwave-udf, vectorization
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
- Do not introduce RunPod / Vertex AI direct / OpenAI direct (without Murakumo proxy) / Anthropic-direct from vendor key / Linode GPU / AWS Bedrock direct / any commercial GPU rental into religious-corp inference paths. ADR-2605215000 makes Murakumo fleet (LiteLLM 127.0.0.1:4000 + EVO-X2 LAN 192.168.1.70 + per-node Ollama gemma3:4b) the sole inference SSoT. Vendor (`gftd.co.jp`) keeps its commercial GPU pool for paid SaaS workloads; religious-corp callers must not invoke vendor RunPod paths (consent capability boundary).
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
| Architecture reference (Holochain-iso) | `yatachain` (`10-protocol/yatachain/`, ADR-2605231400) — names the composition of the substrate primitives above | inventing a parallel composition name without ADR |
| Derived read path (hot-path queries) | `yatachain-projection` (ADR-2605231500) — RW / Lance / Iroh / index used for range/spatial/aggregate reads, IFF (a) deterministically rebuildable from MST+IPFS, (b) never the sole write home, (c) marked with `// yatachain-projection` line comment or `yatachain-projection.toml` manifest. First L1-projection: `feed-discover` (50-infra/mst-projector/projection/, ADR-2605231902) | using RW/Postgres as a primary write store; un-marked carve-outs; "projection of projection" without documented chain back to MST |
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
- `10-protocol/yatachain/SPEC.md` — Holochain-isomorphic substrate composition spec (ADR-2605231400)
- `90-docs/adr/2605231400-yatachain-holochain-iso-substrate.md` — yatachain naming + 7-layer mapping + witness quorum decision
- `90-docs/adr/2605231500-yatachain-projection.md` — regenerable cache rules; the hot-path escape hatch for ADR-2605172000
- `90-docs/adr/2605231902-feed-post-membrane-and-feed-discover-projection.md` — first end-to-end yatachain §4 membrane + L1-projection (app.bsky.feed.post)
- `90-docs/adr/2605214000-etzhayyim-murakumo-mesh-no-vke-and-lexicon-port-rules.md` — Murakumo distributed cluster (no-VKE mesh) + lexicon port verdict taxonomy
- `90-docs/adr/2605215000-etzhayyim-inference-murakumo-only-no-runpod.md` — etzhayyim inference Murakumo-fleet-only (no RunPod)

## References

- This repo (public): https://github.com/etzhayyim/root
- Domain landing: https://etzhayyim.com
- DID resolver: https://etzhayyim.com/.well-known/did.json (LIVE; CF Worker at zone `etzhayyim.com`, DNS AAAA `@` `100::` proxied, deployed 2026-05-17T03:25Z)
