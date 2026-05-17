# etzhayyim/root — CLAUDE Index

This monorepo is the **principal-owned half** of the source-control boundary established by ADR-2605152100 (vendor monorepo) and is the **canonical home for new religious-corp open ADRs** per ADR-2605170900 (this monorepo, `90-docs/adr/`).

## Identity (CRITICAL)

- **Operating entity** (this repo's owner): `etzhayyim` (canonical)
  - Aliases: `amanomibashira` / `天御柱` / `עץ חיים` (Tree of Life) / `etz hayim` / `etzhayim` / `etz chaim` / `エツ・ハイム`
  - Form: 宗教法人 (任意団体 / unincorporated religious voluntary association)
  - Registry: On-chain (blockchain-registered constitution and member roster); NOT registered under 日本国 宗教法人法
  - DID: `did:web:etzhayyim.com` (LIVE — CF Worker at `50-infra/etzhayyim-did-web/`, resolvable via curl + Universal Resolver since 2026-05-17T03:25Z)
  - Domain: https://etzhayyim.com (Cloudflare Registrar, 2026-05-15)
  - License default: Apache 2.0
- **Vendor**: Gftd Japan株式会社 (corporate number 9007-2846, `did:web:gftd.co.jp`)
- **Boundary rule (CRITICAL)**: Payoff帰属・意思決定権 = etzhayyim only. Vendor risk = SOW / SLA / termination / IP-ownership internalized.

## Status

**Seeded + ADR-canonical** (2026-05-17). Migration plan from ADR-2605152100 progress:

| Step | Status |
|---|---|
| 1. etzhayyim.com 取得 (CF Registrar) | ✅ 2026-05-15T12:08Z |
| 2. github.com/etzhayyim org 作成 | ✅ 2026-05-10T14:23Z |
| 3. github.com/etzhayyim/root 作成 | ✅ 2026-05-15T12:20Z |
| 4. ADR-2605152100 active 化 | ✅ |
| 5. Scaffold (LICENSE/README/CLAUDE.md/deps.toml/.gitignore/lefthook.yml) | ✅ |
| 6. Content seed (Tranches A-E + Wave 2) | ✅ |
| 7. 既存 gftdcojp open repos archive + [MOVED] prefix | ✅ 26 repos archived |
| 8. gftdcojp 側 open scope cleanup | ⏳ pending |
| 9. CI / wrangler / package.json `repository` field sed | ✅ etzhayyim/root 側 done (11 pkg.json + 2 wrangler.jsonc) |
| 10. did:web publish (DNS + wrangler deploy) | ✅ 2026-05-17T03:25Z (verified via curl + dev.uniresolver.io) |
| 11. 220-file `amanomibashira` → `etzhayyim` cutover | ⏳ 登記変更後 |

## Repo Layout (Shannon-Optimal 8-Layer, ADR-2604251830)

```
etzhayyim/root/
├── 00-contracts/        # lexicons / bpmn / dmn / Rego policies / resources (JSON-LD)
├── 10-protocol/         # atproto, xrpc, lexicons-bundle, signal, did-etzhayyim,
│                        # wproto, at-client, signal-client
├── 20-actors/           # magatama (Pregel framework + host SDK +
│                        # unispsc_agents/ 18,345 LangGraph agents per ADR-2605171300),
│                        # magatama-go, kami-engine-sdk, effect-cypher,
│                        # etzhayyim-bpmn-sdk, etzhayyim-sdk (RW-free substrate per ADR-2605172000+2605172100)
├── 30-graph/            # graph-schema, kagami, risingwave-udf, vectorization
├── 50-infra/            # SEEDED: geth-private, holochain, ipfs, blockscout,
│                        #   k8s/atproto-pds, lancedb-wasm, yata, tonbo,
│                        #   nats-tiered-storage, nats-jetstream-{objectstore-s3, kv-resp},
│                        #   sveltejs-adapter-wasm, spin-tinygo-flight
│                        # SUBSTRATE (ADR-2605171800 + 2605172100):
│                        #   etzhayyim-did-web/ (CF Worker, LIVE 2026-05-17T03:25Z)
│                        #   mst-projector/   (Stage 3, scaffold)
│                        #   ipfs-pinner/     (Stage 4, scaffold)
│                        #   l2-anchor-contract/ (Stage 5a, Foundry Solidity)
│                        #   anchor-cron/     (Stage 5b, K8s CronJob)
│                        #   etzhayyim-paymaster/ (ERC-4337, Foundry Solidity)
├── 60-apps/             # ai-gftd-project-{open-*, public-*, atproto, ameno, yoro}, watashi
│                        # FIRST RW-FREE REFERENCE IMPL: ai-gftd-project-open-isco/rw-free/
├── 70-tools/            # etzhayyim-cli (renamed from gftd-cli), cdn
├── 90-docs/             # CLAUDE.md (docs rules), adr/, baien/
├── CLAUDE.md            # this file
├── deps.toml            # SSoT for [platform.operating_entity] + monorepo state
├── LICENSE              # Apache 2.0
├── README.md            # public-facing
├── lefthook.yml         # pre-commit (trailing-ws + EOF; full hooks pending)
└── .gitignore
```

## ADR Authority (per ADR-2605170900)

**This repo is canonical for new open religious-corp ADRs.** Vendor monorepo is canonical for boundary / vendor-business / foundational ADRs that predate the org split.

- New ADR placement matrix → `90-docs/adr/README.md`
- ADR ID convention → `90-docs/CLAUDE.md` § "ADR ID Convention"
- Template → `90-docs/adr/template.md`
- ID range partition: vendor ≤2605152xxx, etzhayyim/root ≥2605170xxx

For shared foundational ADRs (Shannon-Optimal 8-Layer, MCP-as-Cell-Membrane, Bonsai Cultivar series, LangGraph patterns, Pydantic/SQLAlchemy contracts), reference by full URL from `gftdcojp/ai-gftd-apps-gftdcojp`. No duplication.

## Do Not

- Do not copy private business documents (CEO packets, SOW templates, lawfirm legal pages, vault contents, family-office registration). Those belong in the vendor monorepo only.
- Do not introduce `gftd-` prefixed identifiers in newly authored code. Use `etzhayyim-` or no prefix. Existing seeded `gftd-` files will be renamed in a follow-up cutover.
- Do not weaken the Apache 2.0 license default. Religious-corp public-interest activity requires permissive license.
- Do not dual-author ADRs across repos. Pick one home per the placement matrix.
- Do not commit secrets. Private DID key lives in macOS Keychain (`service=gftd.etzhayyim, account=DID_PRIVATE_KEY_ED25519`) + pending 1Password mirror.

## Future Work

- **lefthook hooks** mirrored from vendor monorepo (adr-validate, docs-registry, lint-dangerous-query, llm-model-ssot)
- **GitHub Actions CI**: lint / type-check / build / test per layer
- **Dependabot** for npm + cargo + uv ecosystems
- **`90-docs/_registry/docs.json`** generator + validator (parity with vendor)
- **1Password mirror** of `gftd.etzhayyim` / `DID_PRIVATE_KEY_ED25519` (Keychain primary; mirror to `Gftd Japan株式会社` vault, item `etzhayyim/did-web/key-0`)
- **did:gftd → did:etzhayyim method spec** (optional future migration; existing did:gftd:xxx identifiers preserved meanwhile)
- **vendor cleanup (ADR-2605152100 Step 8)**: remove open scope from vendor monorepo + update directory_index pointers

## Substrate boundary (CRITICAL — ADRs 2605172000 + 2605172100)

This repo is **blockchain-self-contained**. Hard rules enforced by ADRs and (future) CI hooks:

| Concern | Allowed | Prohibited |
|---|---|---|
| State | AT Protocol MST + IPFS + Base L2 anchor | RisingWave / Postgres / Kysely / centralized DB |
| Payment | USDC on Base L2 + ERC-4337 Smart Account | Stripe / PayPal / Square / fiat processors |
| Identity | did:web:etzhayyim.com + did:plc + WebAuthn passkey | server-issued JWTs without DID binding |
| Substrate client imports | Only via `@etzhayyim/sdk` | Direct `@atproto/api` / `viem` / IPFS client from app code |

When an open app needs fiat / paid features, it calls vendor backend via XRPC consent-capability (progressive enhancement). Open app remains operational without it.

## SSoT pointers

- `deps.toml` — operating entity, vendor relationship, substrate rules, L2 contracts, DNS records, ADR registry, module registry
- `90-docs/CLAUDE.md` — docs system rules + ADR placement policy
- `90-docs/adr/README.md` — ADR index (7 ADRs as of 2026-05-17)
- `20-actors/etzhayyim-sdk/README.md` — SDK API surface + hard rules

## Cross-repo references

- Vendor (proprietary) monorepo: https://github.com/gftdcojp/ai-gftd-apps-gftdcojp
- This repo (public): https://github.com/etzhayyim/root
- Domain landing (pending): https://etzhayyim.com
- DID resolver: https://etzhayyim.com/.well-known/did.json (LIVE; CF Worker at zone `etzhayyim.com`, DNS AAAA `@` `100::` proxied, deployed 2026-05-17T03:25Z)
