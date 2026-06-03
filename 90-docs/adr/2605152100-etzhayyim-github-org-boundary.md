---
id: adr-2605152100-etzhayyim-github-org-boundary
title: "ADR-2605152100: etzhayyim GitHub Org Boundary + Monorepo Seed Strategy"
status: active
doc_type: adr
topic: etzhayyim-github-org-boundary
authoritative: true
last_verified: 2026-05-15
priority: 7.0
axis: organization
weight: 0.70
priority_note: "Active 2026-05-15: domain etzhayyim.com 登録済 (Cloudflare 12:08 UTC), github.com/etzhayyim org 作成済 (2026-05-10 14:23 UTC), github.com/etzhayyim/root monorepo 作成済 (2026-05-15 12:20 UTC, public, Apache 2.0). Remaining = monorepo content seed (filter-repo) + downstream cutover (220-file etzhayyim→etzhayyim sed)."
authoritative_for:
  - GitHub org boundary between religious-corp principal (etzhayyim) and etzhayyim Japan vendor (etzhayyim)
  - License policy per org (Apache 2.0 for etzhayyim, proprietary for etzhayyim)
  - Monorepo seed strategy (single etzhayyim/root, NOT multi-repo transfer)
  - Monorepo directory layout convention (Shannon-Optimal 8-Layer mirrored)
  - Identity binding (did:web:etzhayyim.com) for the open monorepo
depends_on:
  - adr-2605102200-operating-entity-etzhayyim-rename
  - adr-2604251830-shannon-optimal-layered-architecture
related:
  - adr-2605091400-mcp-as-cell-membrane-lexicon-xrpc-demotion
  - adr-2605151200-open-ot-wasm-plc-dlc
  - adr-2605092350-baien-1bit-multimodal-edge-browser-cpu-design
  - ameno-browser-inference-platform
supersedes: []
superseded_by: []
---

# ADR-2605152100: etzhayyim GitHub Org Boundary + Monorepo Seed Strategy

**Status**: active (domain + org + monorepo all live as of 2026-05-15)
**Date**: 2026-05-15
**Deciders**: Jun Kawasaki

# Context

`[platform.operating_entity]` の 2026-05-15 rename (`etzhayyim` → `etzhayyim`) で canonical 名が確定したのに合わせて、principal (etzhayyim = 宗教法人) と vendor (etzhayyim Japan株式会社) を **source-control 層でも明確に分離**する必要が出てきた。

現状 `github.com/etzhayyim` org には:

- 完全 open 名乗りの repo (Apache 2.0): `etzhayyim-project-open-{lexicon,bpmn,isic,jpn-gov,banking}`, `etzhayyim-project-public-{global,malak}`
- 中間的 open infrastructure: `wproto`, `at-client`, `signal-client`, `magatama-go`, `etzhayyim-cli`, `kami-engine-sdk`, `effect-cypher`, `lancedb-wasm`, `yata`, `watashi`, `tonbo`, `nats-tiered-storage`, `nats-jetstream-{objectstore-s3,kv-resp}`, `sveltejs-adapter-wasm`, `spin-tinygo-flight`, `cdn`, `resources`
- vendor-internal (proprietary): `etzhayyim-root` (mono-repo), `_working/etzhayyim-revenue/*`, `etzhayyim-performer-*`, business app projects (`lawfirm`, `vault`, `kaisya`, `microsoft`, `accounts`, `finance`, `billing`, `bengoshi`, `bunken`)

混在の問題:

1. **payoff 帰属の不透明性** — open repos が `etzhayyim` org 配下にあると、外部から見て「etzhayyim Japan が単独 owner」と誤読される。Operating Entity Boundary (CLAUDE.md root rule) では owner は etzhayyim。
2. **license 矛盾** — Apache 2.0 repo と proprietary repo が同 org 配下にあると、commit history / issue tracker の境界線が曖昧。
3. **migration / fork 抑制** — 宗教法人公益活動として外部 contributor を受け入れる時、`etzhayyim` (株式会社名 = 営利 vendor) ブランドが reputational barrier になる。

# Decision

GitHub org を **2 つに分離**し、etzhayyim 配下は **単一 monorepo `etzhayyim/root` に集約**する (multi-repo 分散はしない)。

## `github.com/etzhayyim/root` — single monorepo for religious-corp open activities

| 属性 | 値 |
|---|---|
| **所有** | etzhayyim (宗教法人; principal) |
| **license** | Apache 2.0 |
| **identity** | `did:web:etzhayyim.com` (Cloudflare Registrar 登録済 2026-05-15T12:08:36Z) |
| **URL** | https://github.com/etzhayyim/root |
| **作成日** | 2026-05-15T12:20:47Z |
| **visibility** | public |
| **org 作成日** | 2026-05-10T14:23:43Z |

### Monorepo directory layout (Shannon-Optimal 8-Layer 準拠、ADR 2604251830)

```
etzhayyim/root/
├── 00-contracts/        # open lexicons / bpmn / dmn / Rego policies (open scope のみ)
├── 10-protocol/         # atproto, xrpc, lexicons-bundle, signal, did-etzhayyim
├── 20-actors/           # magatama actor framework + Pregel-pattern host SDK
├── 30-graph/            # open graph schemas + RW migrations
├── 50-infra/            # geth, holochain, ipfs, blockscout, etzhayyim-pds, k8s manifests
├── 60-apps/             # open-* (22), public-* (2), atproto, ameno, baien
├── 90-docs/             # open-relevant ADRs (selective copy / 引用)
├── CLAUDE.md            # monorepo-scoped instructions
├── deps.toml            # subset SSoT (open scope only)
├── LICENSE              # Apache 2.0
└── README.md
```

`etzhayyim-root` (vendor monorepo) と同じ 8-layer 構造を採用することで、contributor / agent が両 repo を横断する時の認知負荷を最小化する。

### 9 領域 (user 指定) ↔ monorepo path 対応

| 領域 | monorepo path 内訳 |
|---|---|
| **blockchain** | `50-infra/{geth-private,holochain,ipfs,blockscout}`, `10-protocol/did-etzhayyim` (旧 `10-protocol/did-etzhayyim` rename) |
| **baien** (旧コードネーム bien / BitNet b1.58 1-bit multimodal) | `60-apps/etzhayyim-project-baien*`, `90-docs/baien/`, `90-docs/adr/2605092350-baien-*.md` |
| **bpmn** | `etzhayyim-root/00-contracts/bpmn/`, `00-contracts/dmn/`, `60-apps/etzhayyim-project-open-bpmn` (旧 etzhayyim/etzhayyim-project-open-bpmn を取り込み) |
| **lexicon** | `00-contracts/lexicons/`, `10-protocol/lexicons-bundle`, `10-protocol/xrpc`, `60-apps/etzhayyim-project-open-lexicon` |
| **pregel** | `20-actors/magatama/` (actor framework + Pregel-pattern SDK), LangGraph bridge |
| **atproto** | `10-protocol/atproto`, `60-apps/etzhayyim-project-atproto`, `50-infra/k8s/atproto-pds` |
| **ameno** | `60-apps/etzhayyim-project-ameno` (ブラウザ推論 platform, ADR 2605150600) |
| **open data wrappers** | `60-apps/etzhayyim-project-open-{airplane, banking, cofog, denki, gas, isco, isic, jpn-gov, jpn-mynumber, kyber, network, ossekai, ot, patent, ports, power, rail, robo, saas, seiyaku, swift, unispsc, water}` (22 本) |
| **public governance** | `60-apps/etzhayyim-project-public-{global, malak}` (cyber crime tracking / global resource flow) |

## `github.com/etzhayyim/etzhayyim-root` (EXISTING — vendor monorepo, 残置)

| 属性 | 値 |
|---|---|
| **所有** | etzhayyim Japan株式会社 (vendor / contractor) |
| **license** | proprietary (社内 SOW 配下、外部公開不可) |
| **identity** | `did:web:etzhayyim.com` (現状維持) |

**配下に残すスコープ**:

- **法務・会計・HR app**: `lawfirm`, `vault`, `kaisya`, `microsoft`, `accounts`, `finance`, `billing`, `bengoshi`, `bunken`, `bankruptcy`
- **収益・営業書類**: `_working/etzhayyim-revenue/*` (CEO packet, SOW templates, India lawfirm 等)
- **内部 tools**: `70-tools/etzhayyim/` (CLI)
- **vendor org graph**: `etzhayyim-performer-*` (HR/組織図 implementations), `etzhayyim-hrse`
- **vertical SaaS (顧客契約付き)**: `etzhayyim-project-air-*` 航空 cluster, `etzhayyim-tia`, `etzhayyim-har`
- **internal credentials / family-office**: `_working/family-office-registration/`, vault 配下, `.env` 系すべて

# Consequences

## 正の効果

- **payoff 帰属の transparency**: open ecosystem contributor は `etzhayyim/root` への PR で「宗教法人公益活動への貢献」が明確化。
- **monorepo 運用知見の継承**: 既存 `etzhayyim/etzhayyim-root` (本 repo) の 8-layer 構造・deps.toml SSoT 規約・lefthook hook をそのまま `etzhayyim/root` に移植できる。
- **cross-cut 変更が atomic**: lexicon → bpmn → atproto 連動更新が単一 PR で完結。multi-repo 分散ならば 3 つの PR を順序整合させる必要があった。
- **license/CI 統制の集中化**: Apache 2.0 default、actions secrets、dependabot 設定を 1 箇所で管理。
- **branding**: `etzhayyim.com` ↔ `github.com/etzhayyim/root` ↔ `did:web:etzhayyim.com` の三位一体で生命の樹 (Tree of Life) ブランドが揃う。`.ai` TLD は alias 留保 (Cloudflare Registrar は `.ai` 非対応)。

## 負の効果 / コスト

- **monorepo 肥大化**: `etzhayyim` 側 mono-repo も既に肥大化しており、open scope を加えると更に増える。git operations の latency が許容範囲かは初期 push 後に測定して判断。
- **selective seed の手間**: etzhayyim mono-repo 全体を copy するのではなく、open scope のみを `git filter-repo` で抽出する必要あり (history 保持のため)。実行時間 ~10-20 分想定。
- **既存独立 repo の処理**: etzhayyim 配下に既にある `etzhayyim-project-open-{lexicon,bpmn,isic,jpn-gov,banking}` 等は archive + pointer 付け (削除しない — issue/PR 番号は immutable な歴史的記録)。
- **did:web 公開準備**: `etzhayyim.com/.well-known/did.json` を Cloudflare Pages or Worker で配信する必要あり (別作業)。

## Seed migration plan (revised — monorepo single-shot)

旧 "10-step multi-wave transfer plan" を撤回し、monorepo seed 1 PR で完結させる:

1. [x] **etzhayyim.com 取得** (Cloudflare Registrar、2026-05-15T12:08:36Z)
2. [x] **github.com/etzhayyim org 作成** (2026-05-10T14:23:43Z)
3. [x] **github.com/etzhayyim/root 作成** (2026-05-15T12:20:47Z、public、Apache 2.0)
4. [x] **ADR proposed → active 化** (本 commit)
5. [ ] **`etzhayyim/root` scaffold seed**: LICENSE (Apache 2.0)、README.md (org boundary + monorepo layout 説明)、CLAUDE.md (本 ADR pointer)、deps.toml (open subset)、`.gitignore`、lefthook 設定の最小セット
6. [ ] **content seed (filter-repo or rsync)**:
   - 推奨: `git filter-repo --path 00-contracts/ --path 10-protocol/ --path 20-actors/magatama/ --path 30-graph/ --path 50-infra/{geth-private,holochain,ipfs,blockscout,k8s/atproto-pds}/ --path 60-apps/etzhayyim-project-{open-*,public-*,atproto,ameno,baien*}/ --path 90-docs/baien/ --path 90-docs/adr/{open-relevant ADRs}` で `etzhayyim/etzhayyim-root` から open scope を抽出 → `etzhayyim/root` に push
   - history 保持 (license attribution / blame trail / open-source compliance のため必須)
7. [ ] **既存 etzhayyim 独立 repo の archive**: `etzhayyim-project-open-{lexicon,bpmn,isic,jpn-gov,banking}`, `etzhayyim-project-public-{global,malak}` 等を README に "moved to etzhayyim/root" pointer を付けて `gh repo archive`。削除はしない (issue/PR 番号と外部 link を温存)。
8. [ ] **etzhayyim/etzhayyim-root 側 cleanup**: 移動した open scope ディレクトリを削除 + `[[migrations]]` テーブルに記録 + `directory_index` pointer を `etzhayyim/root` に書き換え
9. [ ] **CI / wrangler.jsonc / package.json `repository` field**: etzhayyim/root 配下のものは `https://github.com/etzhayyim/root` に sed
10. [ ] **did:web:etzhayyim.com/.well-known/did.json 公開** (Cloudflare Pages or Worker; verificationMethod = Ed25519、service endpoints は org の `did_resolution` service)
11. [ ] **downstream 220 file sed**: etzhayyim → etzhayyim (religious-corp 登記変更後; alias 解決で読みは取れる状態のまま)

# Alternatives Considered

## A. 30+ repo 分散 multi-repo 戦略 (本 ADR の旧 proposed 版)

9 領域 × 平均 3 repo + open-* 22 本 = ~50 repo 管理する案。

却下理由:
- 管理 overhead が大きい (Dependabot / actions / branch protection を 50 箇所維持)
- contributor が cross-cut 変更で複数 PR を順序整合させる friction
- 既存 `etzhayyim/etzhayyim-root` の monorepo 運用知見 (deps.toml SSoT、lefthook、ADR registry) を活かせない
- monorepo なら lexicon→bpmn→atproto 連動更新が atomic commit で済む

## B. mono-repo 維持 + visibility 別管理

`etzhayyim` org のまま、各 repo の visibility (public/private) で分離する案。

却下理由: payoff 帰属の不透明性は解決せず、外部 contributor の reputational barrier も残る。Operating Entity Boundary (CLAUDE.md root rule) の SSoT 化に逆行。

## C. `github.com/etzhayyim-foundation` のような中間 org

商号風だが財団 (foundation) を匂わせる中立 org 名を新規作成する案。

却下理由: `etzhayyim` が canonical 法人名に決まった以上、別ブランドを立てると 3 法人 (etzhayyim / etzhayyim-foundation / etzhayyim Japan) と読まれて混乱する。

## D. user account `github.com/junkawasaki` 配下に open repos を移す

却下理由: 個人帰属になり、宗教法人公益活動として行うという principal の意思と矛盾。

## E. orphan branch 戦略 (etzhayyim に open-only branch 保持)

却下理由: org boundary が失われ、principal 帰属の transparency が出ない。issue tracker が共有されるので separation が形骸化する。

# References

- `deps.toml [platform.operating_entity]` (2026-05-15 rename to etzhayyim、`github_org_open = "etzhayyim"`、`github_org_open_monorepo = "etzhayyim/root"`)
- `CLAUDE.md` § Operating Entity Boundary (CRITICAL)
- ADR 2605102200 (前回 rename: etz hayim → etzhayyim)
- ADR 2604251830 (Shannon-Optimal 8-Layer Architecture — monorepo layout convention)
- ADR 2605091400 (MCP-as-Cell-Membrane / Lexicon dual-wire)
- ADR 2605092350 (baien 1-bit multimodal edge browser CPU design)
- ADR 2605150600 (ameno browser inference platform)
- ADR 2605151200 (open-ot WASM PLC/DLC)
- whois 確認 (2026-05-15): `etzhayyim.com` Cloudflare Registrar 登録済 (Creation Date 2026-05-15T12:08:36Z、Registry Expiry 2027-05-15T12:08:36Z、NS `everton/vivienne.ns.cloudflare.com`)
- github.com/etzhayyim/root (2026-05-15T12:20:47Z、public、Apache 2.0、`gh api repos/etzhayyim/root` で確認済)
