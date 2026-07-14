# Status index

> Generated from [`status-registry.edn`](status-registry.edn) by `scripts/regen-status.bb`. One-line index; full verbatim prose per row is in the registry, and each row's ADR holds the detail. Linked from `CLAUDE.md` ## Status.

**Legend**: ✅ shipped · 🟢 landed (substrate, tests green) · 🟡 R0 / proposed scaffold · ⏳ blocked/pending.

### Substrate / infra / dataset / enforcement

| Item | Purpose | Status | ADR | Date |
|---|---|---|---|---|
| maps_sentinel_murakumo | M1 T0 preprocessing pipeline | ✅ | 2605215100 | 05-21 |
| feed-post membrane | first §4 MST membrane + L1 projection (`feed-discover`) | ✅ | 2605231902 | 05-23 |
| kotoba-datomic Tier-D blob | `uploadBlob` TS+Py (superseded by kotoba) | ✅ | 2605232401 | 05-23 |
| UNSPSC organism W1 | actor-as-organism heartbeat-cadence port | ✅ | 2605232345 | 05-23 |
| UNSPSC organism W2 | 18,342 mass-deploy + joucho personality | ✅ | 2605240000 | 05-24 |
| UNSPSC post sink | NDJSON queue + k8s DaemonSet | ✅ | 2605240100 | 05-24 |
| Kaizen self-reflection | `KaizenObserverCell` + 6 rules + PR agent | ✅ | 2605240200 | 05-24 |
| Dataset CID substrate | DataLad + git-annex + IPFS pinner | ✅ | 2605241500 | 05-24 |
| agentURI 5-layer | ERC-8004 + libp2p + AT XRPC peer-resolvable | ✅ | 2605241800 | 05-24 |
| Gov 5-layer taxonomy | L1 namespace … L5 routing-around | ✅ | 2605212100 | 05-25 |
| Charter §0 Preamble | Kingdom of God + Land Trust Wave 2 (ERC-721/5192/7401) … | ✅ | 2605252300 | 05-25 |
| Labor Liberation ladder | Adherent SBT → 7-stage L0..L6 | 🟡 | 2605261000 | 05-26 |
| Basic High Income doctrine | imputed-income (flow) + commons-asset (stock) … | 🟡 | 2605301020 | 05-30 |
| Mission-funding revenue arm | vendor commercial surplus → donation → Public Fund … | 🟡 | 2605301036 | 05-30 |
| Social Security for Humanity | Charter §1.16 人類の社会保障; covenantal-universal, conversion-gated … | 🟡 | 2605302357 | 05-30 |
| Social Security delivery pipeline | §1.16 flow: outreach → vow → compute → openmail → atproto → social … | 🟡 | 2605302358 | 05-30 |
| **kotoba** storage pivot | canonical substrate engine; supersedes kotoba-datomic + RW | 🟡 | 2605262130 | 05-26 |
| Public-data ingestion | organism ecosystem IPFS DataLad subdatasets | 🟢 | 2605262400 | 05-26 |
| Robotics-sim world-data | + kami-usd pipeline (sibling of 2605262400) | 🟢 | 2605262500 | 05-27 |
| Global legal-corpus | statutes/case-law/treaties IPFS ingestion | 🟡 | 2605262800 | 05-26 |
| organism R0+R1 sprint | 26-iter /loop, 8 axes A-H landed | 🟢 | 2605270930 | 05-27 |
| Registry enforcement | 5→8-axis matrix, all PR-gates baseline 0 | 🟢 | 2605271100 / 271200 | 05-28 |
| manimani kotoba-native | personal knowledge router reconciled onto kotoba EAVT + StateGraph + Murakumo + E2E … | 🟡 | 2605291100 | 05-29 |
| kotoba v0.1.0 + brew tap | first tag + GH Release + `etzhayyim/homebrew-kotoba` published … | ✅ | 2605292100 | 05-29 |
| kotoba actor deploy + Murakumo live | WASM + Python-LangGraph (aria) actors run in-WASM on :8077 … | ✅ (see 2605302355) | 2605301625 | 05-30 |
| kotoba LangGraph LLM verified + durable routing | EMPIRICAL re-verify on live :8077 … | ✅ | 2605302356 | 05-30 |
| **Donation-funded operation + compute-node donation** | etzhayyim.com /donate + /.well-known/donation.json … | 🟡 R0 | 2606012100 | 06-01 |
| **moyai 舫い — inference reciprocity reward** | non-monetary, non-transferable, decaying reciprocity credit for commons-inference (入会権) … | 🟢 R0+R1 | 2606062101 | 06-06 |
| **Displacement Dividend + robotics-actor wave** | OSS-robotics frees a worker → Public Fund pays tenure-weighted in-kind income (cash≡0) … | 🟡 R0 | 2606032130 / 2606032100 | 06-03 |
| **Robotics remote-work actor survey** | remote-work lens over the corpus … | 🟡 R0 | 2606073001 | 06-07 |
| Spirit-in-Physics kotoba datafication | 霊性 data of self/humanity/world into datomic kotoba (Jung assay → … | 🟡 R0 | 2606011501 | 06-01 |
| **kotoba hybrid web search** | Google-shaped datom-native search over Common Crawl … | 🟢 | 2606012300 | 06-01 |
| **Actor profile + dynamic did.json** | actor-profile SSoT EDN backs did.json + getProfile … | 🟢 | 2606013800 | 06-01 |
| **One Worker, many WASM actors** | etzhayyim.com = sole CF Worker … | 🟢 | 2606014500 | 06-01 |
| **WASM-actor runtime (gateway + loader + componentize-py)** | apex trustless `/ipfs/<cid>` gateway (CID re-verify) + … | 🟢 | 2606014600 | 06-01 |
| **WASM-actor runtime round 2** | dag-pb CAR verify (multi-block trustless) + e7m-wasm-runner (T2 mesh … | 🟢 | 2606015200 | 06-01 |
| **Mesh-runner serving + IPFS-based DID** | e7m-wasm-runner HTTP serve (`/xrpc/com.etzhayyim.actor.run`, … | 🟢 | 2606015400 | 06-02 |
| **Self-certifying DID attestation** | actor's own ed25519 key (`did:key`) signs the did.json CID → … | 🟢 | 2606015600 | 06-02 |
| **kotoba-os** unikernel OS | content-addressed WASM-first Rust unikernel OS for OT/PLC/k8s (Hermit … | 🟡 R0 | 2606031600 | 06-03 |
| **WASM-actor SBOM attestation** | CycloneDX SBOM generator for deployed wasm (recomputes kotoba program CID) … | 🟢 R0 | 2606036001 | 06-03 |
| **entity-as-actor (society-scale social mirror)** | 1 public/power entity = 1 keyless mirror-actor (gov 7,106 + corp 1,733 … | 🟢 R0 | 2606042330 | 06-04 |
| **kagami 鏡 actor doctrine (八咫鏡)** | renames the "mirror actor" concept → kagami (鏡) actor grounded in the … | ✅ doctrine | 2606211752 | 06-21 |
| **Charter priority-over-specifics reconciliation (3-Tier)** | restructures Charter immutability locked-specifics → 3-Tier (Tier-0 … | ✅ | 2606062100 | 06-06 |
| **多世代採掘リスク評価軸 (extraction risk-gate, NOT blanket mining ban)** | Rider §2(l) reframed: 採掘・採油は一律禁止ではなく 多世代(子・孫)×Wellbecoming リスク評価ゲート … | ✅ | 2606161700 | 06-16 |
| **エヒイェ非二元神論 + yir'ah doctrine** | Tier-1 doctrine 固定: 神の存在の非前提 … | ✅ | 2606112200 | 06-11 |
| **maps kotoba-native substrate migration** | maps.etzhayyim.com refactor off RisingWave/Hyperdrive → kotoba Datom log … | 🟡 R0 | 2606064500 | 06-06 |
| **open-kyber kotoba-Datomic ERP + ISIC packs + productivity suite** | open-kyber → canonical kotoba-Datom-log ERP (no RisingWave/Kysely … | 🟢 R1+R2 | 2606037200 | 06-06 |
| **infra-robotics 3-layer operational substrate** | basic-infra robotics (電気/水道/ガス/通信) from scaffold → runnable … | 🟢 R0+R1 | 2606091800 / 2606101430 | 06-10 |
| **ibuki 息吹 — organism autonomy R2 gap-closure** | closes the 7 gaps blocking the artificial-organism loop … | 🟢 R0+R1+R2+R3+ecosystem+verified+leash | 2606101200 / 2606101800 / 2606102000 / 2606111400 | 06-11 |
| **ibuki 息吹 — co-scientist entropy ReAct loop** | the organism REASONS about its own persistence (clj-native, extends ibuki) … | 🟢 R0 | 2606201200 | 06-20 |
| **actor self-publication seed (gov-mirror constellation)** | uniform charter-clean seed for each government-mirror actor to be … | 🟢 R0 | 2606272355 | 06-27 |
| **toritsugi authority-actor fanout** | Split toritsugi into per-regime (authority) keyless mirror actors on … | 🟢 R0 | 2606292000 | 06-29 |

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
| kami-genesis physics maturation | PlanarChain N-link articulation + clean-room isaacsim.core.api + … | 🟢 | 2605311500 | 05-31 |
| kami-genesis 3-D spatial + contact | full 3-D reduced-coord solver (Featherstone RNEA+CRBA+LDLᵀ) + rigid … | 🟢 | 2605311800 | 05-31 |
| Shibuya street digital-twin (iter 1) | real OSM Shibuya (144 bldg … | 🟢 | 2605311900 | 05-31 |
| Shibuya digital-twin iter 2 (kotoba + 3DGS) | + 501 kotoba EAVT point-assets (poles/lamps/signals) + Mapillary acquisition front … | 🟢 | 2605312200 | 05-31 |
| Shibuya 3DGS (Mapillary SfM + splat-physics) | Mapillary 200 渋谷 images → pycolmap SfM → 2,235-pt 渋谷 .splat → kami … | 🟢 | 2605312600 | 05-31 |
| giemon kabitori (黴取り) mold-removal sim | steerable rotary-brush mold-removal sim (6-DOF URDF + MoldField erosion) on kami-genesis … | 🟢 | 2605312300 | 05-31 |
| giemon part graph (SBOM↔kotoba) | per-part SBOM ledger EDN → CycloneDX → kotoba EAVT … | 🟢 | 2605312330 | 05-31 |
| **giemon factory R0** | the FACTORY that builds the giemon line … | 🟢 | 2606010030 | 05-31 |
| **sarutahiko truck factory R0 (full-robotics + 積込ロボット)** | the FACTORY that builds the 猿田彦 Class-8 truck (giemon-factory 4D-BIM pattern) … | 🟢 | 2606013100 / 2605252500 | 06-01 |
| **kami-genesis maturation (PhysX/Isaac gap)** | WASM clean-room narrowing of NVIDIA gap … | 🟢 | 2606010030 | 05-31 |
| **kami-autodrive GNC autonomy** | autonomy loop (perception→plan→control) over kami-vehicle/sensor-sim/pathfind … | 🟢 | 2606010600 | 05-31 |
| **iwakura/fuigo ternary RTL → sky130 GDSII** | ternary-silicon RTL → verified → synth → P&R GDSII on sky130 open PDK … | 🟢 | 2605242515 / 2606012800 | 06-01 |
| e7m-sim | robotics simulation substrate R0 charter | 🟡 | 2605261600 | 05-26 |
| baien-moemoekyun MoE R0 | 2B BitNet backbone + 128-expert MoE residual | 🟡 | 2605261900 | 05-26 |
| baien-moemoekyun R1 | Phase 0 freeze-train SFT on EVO-X2 ROCm | 🟡 | 2605262100 | 05-26 |
| Charter Rider §2(i)(2) | train-only GPU-rental carve-out (amendment, gated) | 🟡 | 2605262200 | 05-26 |
| baien-moemoekyun R2+ | B200 train architecture (gated on 2605262200) | 🟡 | 2605262300 | 05-26 |
| Energy re-framing | fusion + microbial hydrocarbon conditional permit | 🟡 | 2605263501 | 05-26 |
| **manako 眼 browser-local YOLO26** | first browser-local vision detector (dual-mode YOLO26 postproc, ort-web WASM EP) … | 🟢 R0 | 2606034800 | 06-03 |
| **manako 眼 browser-local YOLO26** | first browser-local vision detector (dual-mode YOLO26 postproc, ort-web WASM EP) … | 🟢 R0 | 2606034800 | 06-03 |
| **Maxwell** default LLM weight | religious-corp default inference weight … | 🟡 R0 | 2606061000 | 06-06 |

### Tier-B actors (each: ADR + manifest + cells + lex)

| Item | Purpose | Status | ADR | Date |
|---|---|---|---|---|
| wadachi 轍 | autonomous-mobility R&D (SAE L4 ceiling) | 🟡 R0 | 2605242000 | 05-23 |
| todoke 届け | last-mile (one-mile) autonomous delivery, curb-to-door ≤25kg SAE-L4 sidewalk … | 🟡 R0+R1 | 2606042300 | 06-04 |
| yakushi 薬師 | pharmaceutical mfg (eye-drop + OTC APIs) | ✅ W1/1b/1c | 2605250500 | 05-25 |
| tokigusuri 時薬 | pharmaceutical patent-cliff … | 🟡 R0 | 2606171300 | 06-17 |
| hirameki 閃き | world PUBLIC-PATENT KG-mirror … | 🟢 R0 | 2606212200 | 06-21 |
| tatekata 建方 | construction (civil + MEP ≤2 story) | 🟡 R0 | 2605250715 | 05-25 |
| watatsumi 綿津見 | civilian submersible (≤6500m) | 🟡 R0 | 2605252200 | 05-25 |
| kanayama 金山 | circular metallurgy (UBC Al recycling) | 🟡 R0 | 2605252400 | 05-25 |
| sarutahiko 猿田彦 | heavy Class-8 truck mfg (wadachi mfg-side sibling) | 🟡 R0 | 2605252500 | 05-25 |
| makura 枕 | foam pillow (PU foam + shred-fill) | 🟡 R0 | 2605261115 | 05-25 |
| mitsuho 瑞穂 | food / agriculture (L2 Sustenance) | 🟡 R0 | 2605261015 | 05-26 |
| hagukumi 育み | care — childcare + eldercare (L4 Care) | 🟡 R0 | 2605261030 | 05-26 |
| manabi 学び | education (open-curriculum + cert_prep sub-cell) | 🟡 R0 | 2605261045 | 05-26 |
| hikari 光 | energy gen/storage/grid-edge (L2 Sustenance) | 🟡 R0 | 2605261100 | 05-26 |
| himawari 向日葵 | solar-grade c-Si PV module manufacturing Tier-B actor … | 🟢 R0.2 | 2606021200 | 06-02 |
| amime 網目 | multi-site energy MESH flow-network … | 🟢 R0 | 2606212020 | 06-21 |
| atsurae 誂え | Product Line Engineering (PLE) feature-model engine … | 🟢 R0 | 2606212010 | 06-21 |
| igata 鋳型 | HPDC megacasting (R0 + R1 benchtop) | 🟡 R0/R1 | 2605261200 | 05-26 |
| hodoki 解き | ELV disassembly + materials recovery | 🟡 R0 | 2605261215 | 05-26 |
| tsutae 伝え | handheld comms device (≤200g, open SoC) | 🟡 R0 | 2605261300 | 05-26 |
| futawa 二輪 | small-displacement motorcycle (≤250cc/≤15kW) | 🟡 R0 | 2605261330 | 05-26 |
| suki 鋤 | farm tractor mfg (mitsuho mfg-side sibling) | 🟡 R0 | 2605261500 | 05-26 |
| chigiri 契 | legal-procedure substrate (UPL prohibited, NOT law firm) … | 🟢 R0 | 2605262700 | 05-26 |
| toritate 執帳 | accounting + audit (100% on-chain) | 🟡 R0 | 2605262900 | 05-26 |
| iyashi 癒 | clinical care provider (L4 Care triad) | 🟡 R0 | 2605263000 | 05-26 |
| mizuho 水穂 | water + sanitation (community-scale; ≠ mitsuho 瑞穂) | 🟡 R0 | 2605263100 | 05-26 |
| kazaori 風折 | civilian disaster response (force-separation sibling) | 🟡 R0 | 2605263200 | 05-26 |
| musubi 結 | covenant ceremony (TIGHT pair w/ chigiri) … | 🟢 R0 | 2605263400 | 05-26 |
| wakai 和会 | mutual aid (NOT insurance) | 🟡 R0 | 2605263500 | 05-26 |
| kataribe 語部 | press + publishing + translation | 🟡 R0 | 2605263600 | 05-26 |
| kokoro 心 | mental health support (NOT clinical psych) | 🟡 R0 | 2605263700 | 05-26 |
| shidemori 死出守 | memorial + cemetery (FINAL gap-closure) | 🟡 R0 | 2605263801 | 05-26 |
| ossekai 御節介 | info-arbitrage + Wellbecoming-nudge (AT Proto) | 🟢 R2 | 2605264000 | 05-26 |
| tsukuroi 繕い | authorized vuln-remediation patch-proposer (akuma sibling … | 🟡 R0 | 2605291500 | 05-29 |
| danjo 弾正 | public-accountability oversight … | 🟡 R0 | 2605301600 | 05-30 |
| tadori 辿 | authorized on-chain tx tracing + actor attribution (kotoba-EAVT-native … | 🟡 R0 | 2605301400 | 05-30 |
| warifu 割符 | open zero-fee card (credit+debit), Stripe-REST/EMV/NFC-compatible … | 🟡 R0 | 2605302000 | 05-30 |
| himotoki 繙き | ACTIVE disclosure-request filer … | 🟡 R0 | 2605302130 | 05-30 |
| kanae 鼎 | global government fiscal-flow VISUALIZATION … | 🟡 R0 | 2605302300 | 05-30 |
| toritsugi 取次 | citizen government-procedure CONCIERGE … | 🟡 R0 | 2605312030 | 05-31 |
| moushibumi 申文 | citizen democratic-participation CONCIERGE … | 🟡 R0 | 2605312400 | 05-31 |
| kurashimori 暮らし守 | citizen consumer-protection CONCIERGE (国民生活センター相当) … | 🟡 R0 | 2605312500 | 05-31 |
| haraedo 祓戸 | global bulky-waste (粗大ゴミ) disposal … | 🟡 R0 | 2606010200 | 05-31 |
| kizashi 兆 | non-invasive multimodal body-scan … | 🟡 R0 | 2605312700 | 05-31 |
| tsumugi 紡ぎ | Engi Knowledge Graph intel weaver … | 🟢 R2 | 2606011800 / 2606061501 / 2606092000 | 06-09 |
| okaimono 御買物 | charter-clean inversion of Amazon … | 🟢 R0+R1+R2+R3 | 2606012101 | 06-01 |
| watatsuna 綿津綱 | world submarine-cable KG … | 🟡 R0+R1+R2 | 2606012600 | 06-01 |
| funadaiku 船大工 | zero-emission autonomous CARGO-SHIP building … | 🟡 R0 | 2606013400 | 06-01 |
| funamori 舫 | 淡水化発電 — marine-renewable salinity-gradient power (PRO/RED) from fresh-meets-sea mixing … | 🟢 R0 | 2605265600 | 06-16 |
| kabuto 兜 | world public-company supply-chain KG … | 🟡 R0 | 2606022000 | 06-02 |
| busshi 物資 | world commodity & raw-materials KG-mirror observatory … | 🟢 R0+R2 | 2606161730 / 2606171000 | 06-17 |
| ugachi 穿ち | the §2(l) extraction RISK-GATE … | 🟢 R0+R1+R2 | 2606161800 / 2606161830 / 2606170900 | 06-17 |
| uchiwake 内訳 | world product bill-of-materials … | 🟡 R0 | 2606081800 | 06-08 |
| kanjō 勘定 | world public-company financial-disclosure (決算) KG … | 🟢 R0+R1-live-leg | 2606032000 / 2606101540 | 06-10 |
| ooyake 公 | world government atlas — structural atlas of public gov units … | 🟡 R0/R1 | 2606021600 | 06-02 |
| sumitsubo 墨壺 | cleanroom CAD interop (Vectorworks/Autodesk/AutoCAD) … | 🟢 R0 | 2606033601 | 06-03 |
| sanae 早苗 | labor-liberation OSS-robotics #1 … | 🟡 R0 | 2606032100 | 06-03 |
| hataori 機織 | labor-liberation OSS-robotics #2 … | 🟡 R0 | 2606032100 | 06-03 |
| kiyome 清め | labor-liberation OSS-robotics #3 … | 🟡 R0 | 2606032100 | 06-03 |
| yadori 宿り | DNS-availability + domain acquisition … | 🟡 R0 | 2606038400 | 06-03 |
| karakuri 絡繰 | web-service-to-CLI — uniform ServiceOp CLI over GUI-only SaaS driving … | 🟡 R0 | 2606039200 | 06-03 |
| nusa 幣 | ritual/industrial hemp heritage + low-THC cultivation datafication … | 🟡 R0 | 2606039800 | 06-03 |
| tazuna 手綱 | clean-room remote-robotics fleet operation + teleoperation + … | 🟡 R0 | 2606042100 | 06-04 |
| watari 渡り | live ship + aircraft real-time position KG … | 🟡 R0 | 2606041827 | 06-04 |
| hotaru 蛍 | III-V/InP substrate open-publication commons (the R4+ re-eval gate of ADR-2605265500) … | 🟡 R0 | 2606051200 | 06-05 |
| noroshi 烽 | 光電融合 photonics-electronics communication chip + ISAC + packaging robotics … | 🟡 R0+R1 | 2606051600 | 06-05 |
| kamado 竈 | closed-loop carbon refining + fossil-refinery decommission/transition + observation … | 🟡 R0 | 2606051500 | 06-05 |
| mitooshi 見通し | probabilistic forecasting observatory + leak-free … | 🟡 R0 | 2606051800 | 06-05 |
| ake 朱 | community-edit membrane — Wikipedia collaborative-correction stance, charter-fitted … | 🟡 R0 | 2606052100 | 06-05 |
| fuchi 扶持 | mission-aligned maintainer sustenance allocator … | 🟢 R2 | 2606052300 | 06-05 |
| tasuke 助 | free cybercrime-victim-support membrane … | 🟡 R0 | 2606060900 | 06-05 |
| kawaraban 瓦版 | news MEDIUM — kotoba-wasm mirror of real news media (面 sections, … | 🟡 R0 | 2606061900 | 06-06 |
| omise 御店 | seller-side storefront commons … | 🟢 R0+R1 | 2606071400 | 06-07 |
| ainori 相乗 | pooled passenger-mobility commons (Uber inversion) … | 🟢 R0+R1 | 2606071500 | 06-07 |
| shukubo 宿坊 | pilgrim-lodging commons (Airbnb/Hotels inversion) … | 🟢 R0+R1 | 2606071600 | 06-07 |
| tsubasa 翼 | flight-route/fare discovery commons (Skyscanner inversion) … | 🟢 R3+ | 2606072802 | 06-21 |
| suji 筋 | musculoskeletal posture-load biomechanics simulator … | 🟡 R0 | 2606061901 | 06-06 |
| keizu 系図 | government power-relations KG … | 🟡 R0 | 2606066001 | 06-06 |
| sukashi 透かし | ad-tech supply-chain + delivery-infra + fraud-network observatory … | 🟡 R0 | 2606071601 | 06-07 |
| shomei 証明 | believer self-sovereign identity binding + proof-of-personhood … | 🟡 R0 | 2606072100 | 06-07 |
| inochi 命 | living-world (生命圏) KG mirror … | 🟡 R0 | 2606073000 | 06-07 |
| kafun 花粉 | 花粉撲滅 remediation actor — the clj-native Tier-B actor-ization of the … | 🟢 R0 | 2606211712 | 06-21 |
| rasen 螺旋 | public-genetics (公開遺伝) KG mirror … | 🟢 R2 | 2606101000 | 06-11 |
| asobi 遊び | freed-time / play & cultural-expression (遊び) KG mirror … | 🟡 R0 | 2606073200 | 06-07 |
| hokorobi 綻び | world systemic finance-risk observatory … | 🟡 R0 | 2606073400 | 06-07 |
| hoshimori 星守 | off-Earth / orbital (軌道) stewardship mirror … | 🟡 R0 | 2606073600 | 06-07 |
| tsugite 継ぎ手 | world peoples-continuity (民の存続) mirror … | 🟡 R0 | 2606073800 | 06-07 |
| kosatsu 高札 | crime/sanctions COMPETING-CLAIM observatory … | 🟡 R0 | 2606072003 | 06-07 |
| kasa 嵩 | worldwide computing-capacity growth observatory … | 🟢 R0 | 2606072002 | 06-07 |
| shionome 潮目 | cross-asset capital-flow observatory … | 🟢 R0+R1-stock+T1-live | 2606072201 / 2606111330 | 06-11 |
| suimin 睡眠 | sleep-disorder treatment-EVIDENCE research + synthesis (sibling of … | 🟡 R0 | 2606072800 | 06-07 |
| meyasu 目安 | 統合 arbitrage actor — a yardstick, NOT a trade … | 🟢 R1 | 2606073201 | 06-07 |
| iryo 医療 | Japan 国内 レセプト計算 + レセ電(レセプト電算)生成 + FHIR claim engine … | 🟢 R0 | 2606074000 | 06-07 |
| niyaku 荷役 | automated port cargo handling … | 🟡 R0 | 2606082000 | 06-08 |
| shiori 栞 | human-Wellbecoming detractor observatory + transparent intervention … | 🟡 R0 | 2606082102 | 06-08 |
| tedai 手代 | member-COMPUTER-operation … | 🟡 R0 | 2606101400 | 06-10 |
| hakoniwa 箱庭 | forward-simulation observatory … | 🟢 R1 | 2606111500 | 06-11 |
| mimamori 見守り | covenant keeping membrane (mishmeret ha-adam 相互保持者会, ADR-2606112200 D6 の実装) … | 🟢 R1 | 2606112300 | 06-11 |
| hinagata 雛形 | legal-document-template commons (法律文書雛形) … | 🟢 R1 | 2606111954 | 06-11 |
| kadode 門出 | labour-resignation concierge + 使者 (退職代行) … | 🟡 R0 | 2606112238 | 06-11 |
| sonae 備え | civilian pre-disaster foresight + preparedness + early-warning substrate … | 🟢 R0 | 2606091200 | 06-09 |
| credits | yoro.etzhayyim.com human-participation credit ledger … | 🟢 R0 | 2604271400 | 07-10 |
| narashi 均 | global inequality observation … | 🟢 R0 | 2607101800 | 07-10 |
| abaki 暴 | anti-monopoly & chokepoint intelligence membrane … | 🟡 R0 | 2606073100 | 06-07 |
| kaiyaku 解約 | 縁切り (tie-severance) executor … | 🟡 R0 | 2606112201 | 06-11 |
| tate 盾 | citizen legal-defense concierge (defensive only) … | 🟢 R2 | 2606112301 / 2606112400 / 2606122000 / 2606122300 | 06-11 |
| tanemaki 種蒔き | Public Fund grant-steward (fund-manager inversion) … | 🟡 R0 | 2606122001 | 06-12 |
| meisai 明細 | member card-statement (利用明細) ingestion … | 🟡 R0 | 2606122400 | 06-12 |
| tatara 鑪 | world manufacturing-plant + logistics GEOGRAPHIC KG … | 🟡 R0 | 2606171800 | 06-17 |
| torifune 鳥船 | zero-net-carbon open launch-vehicle manufacturing + Transparent space access … | 🟡 R0+R1+R2 | 2606162355 | 06-16 |
| subaru 昴 | Transparent connectivity-commons satellite constellation (Starlink/OneWeb inversion) … | 🟡 R0+R1+R2 | 2606162355 | 06-16 |
| jinushi 地主 | world land/building ownership ACQUISITION mirror (clj-native … | 🟢 R1 | 2606162000 | 06-16 |
| kaname 要 | cross-domain system-of-systems leverage-point (律速) synthesizer + おせっかい … | 🟢 R0+R1 deployed | 2606172100 | 06-17 |
| kumi 組 | community/organization-unit dependency-influence-follow-graph + … | 🟡 R0 | 2607101830 | 07-10 |
