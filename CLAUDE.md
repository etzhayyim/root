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
| 21. UNSPSC actor-as-organism Wave 1 (joucho heartbeat-cadence Python port + c10101500 reference) | ✅ 2026-05-23 (ADR-2605232345; `pymagatama.organism`) |
| 22. UNSPSC actor-as-organism Wave 2 (18,342 mass-deploy via `UnispscOrganismFleetCell` shard-0/1/2 + per-code joucho personality + follower stub) | ✅ 2026-05-24 (ADRs 2605240000 / 2605240015 / 2605240030; manifests-ready, apply pending) |
| 23. UNSPSC organism post sink (NDJSON queue + TS drainer interface) + k8s DaemonSet manifests | ✅ 2026-05-24 (ADR-2605240100; `50-infra/k8s/unispsc-organism-fleet/`; drainer sidecar Wave 3) |
| 24. Ecosystem self-reflection: `KaizenObserverCell` + 6 rules + KaizenProposal NDJSON + PR agent contract | ✅ 2026-05-24 (ADR-2605240200; `pymagatama.organism.kaizen`; PR agent Wave 4) |
| 25. Dataset CID substrate (DataLad + git-annex `directory` remote + sidecar IPFS pinner; HF `add` E2E + 4 fetchers `pull hf\|geonames\|osm\|wikidata` + PDS `datasetPin` emit) | ✅ 2026-05-24 (ADR-2605241500; `70-tools/e7m-dataset/` + `app.etzhayyim.substrate.datasetPin`; smoke map CID `bafkrei…f5z2q`; HF add map CID `bafybeigeput…fr7a` on `hf-internal-testing/fixtures_image_utils@8665b8ad` 9 files / 1.5 MiB; Kubo on `/Volumes/260317`; 28/28 pytest; PDS emit defaults to dry-run, real wiring via `ETZ_E7M_PDS_{SESSION,AUTH,DID}`; Charter Rider scanner warn-only until pymagatama installed) |

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
│                        # etzhayyim-bpmn-sdk, etzhayyim-sdk (RW-free substrate per ADR-2605172000+2605172100)
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
| Derived read path (hot-path queries) | `yatachain-projection` (ADR-2605231500) — RW / Lance / Iroh / index used for range/spatial/aggregate reads, IFF (a) deterministically rebuildable from MST+IPFS, (b) never the sole write home, (c) marked with `// yatachain-projection` line comment or `yatachain-projection.toml` manifest | using RW/Postgres as a primary write store; un-marked carve-outs; "projection of projection" without documented chain back to MST |
| Server-side signing capability (ADR-2605231525, Council ratify pending) | Member wallet sign (USDC), member passkey-derived ES256 (session), community-operator DID (bulk-ingest), Council 5-of-7 Safe (governance), read-only RPC / firehose subscribe / IPFS pin / static asset serve | Any platform-held private key, master credential, or signing token in etzhayyim-operated Workers / pods / CronJobs / CI / hosted bots. Exemption: `// no-server-key: read-only` marker on documented Stage handover rollback windows. Enforced by `e7m verify` (9th invariant) |

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

## References

- This repo (public): https://github.com/etzhayyim/root
- Domain landing: https://etzhayyim.com
- DID resolver: https://etzhayyim.com/.well-known/did.json (LIVE; CF Worker at zone `etzhayyim.com`, DNS AAAA `@` `100::` proxied, deployed 2026-05-17T03:25Z)
