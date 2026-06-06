---
id: adr-2604231811-atproto-extension-service-layers
title: "ADR: AT Protocol 拡張層サービス分類 — PDS/AppView 以外の公式語彙"
status: superseded
doc_type: adr
topic: service-taxonomy
authoritative: true
last_verified: 2026-04-24
authoritative_for:
  - AT Protocol 標準 / W Protocol 拡張のサービス層分類名
  - 新規 Worker 起こす際の layer 選定基準
  - PDS / AppView に収まらない役割の正名
related:
  - adr-2604231800-atproto-permission-spec-integration
  - adr-0022-auth-topology-consolidation
  - adr-0023-auth-shannon-optimal-4-layer
  - adr-0024-auth-accounts-worker-topology
  - adr-0081-worker-direct-hyperdrive-persistence
  - adr-0056-bpmn-as-actor
supersedes: []
superseded_by:
  - adr-2604262145-erc8004-protocol-root-atproto-profile
---

# Supersession

This ADR is superseded by
`adr-2604262145-erc8004-protocol-root-atproto-profile`. The AT Protocol layer
taxonomy remains useful historical vocabulary, but new decisions must treat
ERC725/ERC-8004 as the public protocol root and atproto/XRPC as one protocol
profile under that root.

# Context

AT Protocol の公式サービス分類は PDS / AppView / Relay (BGS) / Feed Generator /
Labeler / Chat / Ozone / Entryway / Client App の 9 種に限定されている。

一方で本 repo の CF Worker 群は明らかにこの 9 分類に収まらない役割を持ちつつも、
CLAUDE.md / deps.toml / ADR ごとに場当たり的な呼称 (〜server, 〜service, 〜fleet,
〜gateway, 〜directory, 〜worker, 〜facade …) を使っている。例:

| Worker | 本質 | 従来の呼び方 (drift 有) |
|---|---|---|
| `signal.etzhayyim.com` | X3DH prekey bundle server | "signal service" / "E2E helper" |
| `vault.etzhayyim.com` | zero-knowledge secret storage | "vault worker" / "1Password 相当" |
| `murakumo.etzhayyim.com` | LLM inference fleet gateway | "murakumo fleet" / "inference gateway" |
| `plc.etzhayyim.com` | did:plc directory (self-hosted) | "plc worker" / "did directory" |
| `authn.etzhayyim.com` / `authz.etzhayyim.com` | OAuth AS / authorization mgmt UI | "auth worker" / "T4 split" |
| `shinshi.etzhayyim.com`, `animeka.etzhayyim.com`, `yabai.etzhayyim.com`, `lawfirm.etzhayyim.com`, ... | server-side actor (no human UI) | "actor worker" / "domain worker" / "MCP capability" / "app worker" |
| `dispatcher.etzhayyim.com` | BPMN process dispatcher (ADR-0056) | "bpmn-dispatcher" |
| `yoro.etzhayyim.com` | Svelte SPA + SEO snapshot | "frontend" / "client" / "ui" |
| `routing-gateway` | did:web sub-actor path resolver (ADR-0023) | "routing-gateway" |
| `atproto.etzhayyim.com` | PDS pipethrough + OAuth AS 兼務 | "atproto worker" / "PDS" |

この drift が起きる理由は単純で、**AT Protocol の公式 9 分類の外側**に必然的に
現れる役割を記述する語彙が定まっていないからである。既に ADR-0056 (BPMN-as-actor),
ADR-0081 (worker-direct Hyperdrive), ADR-0087 (magatama MCP facade), ADR-0092
(every vertex as actor) と続けて「actor 的 Worker」を定義し続けているが、
それらが **同じ層なのか別の層なのか** が言語化されていない。

新規 Worker を設計・命名する度に「これは AppView 扱い? PDS 扱い? actor 扱い?」
で迷い、結果として Worker 名・NSID prefix・CLAUDE.md 記述の 3 箇所が drift する。

# Decision

AT Protocol 標準 9 層の **superset** として、W Protocol / etzhayyim 独自の
**extension layer 6 種** を正名定義する。以下 15 層 (標準 9 + 拡張 6) を
repo 全体で正規語彙とし、`deps.toml [[conventions]]` と Worker 起票 CLAUDE.md
の冒頭で layer 名を明示する。

## 15-Layer Taxonomy

### AT Protocol 標準 (9 層, 触らない)

| # | Layer | 責務 | 本 repo の実体 |
|---|---|---|---|
| 1 | **PDS** (Personal Data Server) | repo commit + blob + identity | `atproto.etzhayyim.com` の PDS 部 (pipethrough 先の `etzhayyim-pds`) |
| 2 | **AppView** | indexed view for an app lexicon | yoro AppView (`app.bsky.*` indexed view、graph Worker + Kotoba/Datomic) |
| 3 | **Relay** (BGS) | firehose 集約 | (未運用、Bluesky 公式依存) |
| 4 | **Entryway** (Authorization Server) | OAuth / DPoP / PAR / PKCE | `atproto.etzhayyim.com` の OAuth handler 部 (ADR-2604231800) |
| 5 | **Feed Generator** | `app.bsky.feed.getFeedSkeleton` | 未運用 |
| 6 | **Labeler** | label emit | 未運用 |
| 7 | **Chat Service** | `chat.bsky.convo.*` / `wproto.convo.*` | PDS pipethrough 内の convo handler |
| 8 | **Ozone** | moderation dashboard | 未運用 |
| 9 | **Client App** | end-user UI consumer | `yoro.etzhayyim.com` (Svelte 5 SPA + SEO) |

### W Protocol 拡張 (6 層, 本 ADR が正名)

| # | Layer (正名) | 簡名 | 責務 | 登録要件 |
|---|---|---|---|---|
| 10 | **Actor Worker** (Agent-as-Service) | `actor-worker` | ヒューマン UI を持たない server-side actor。path-DID 保持 + `sdk.pds.createRecord` or Worker-direct Hyperdrive (ADR-0081) で書き込み。MCP capability を公開してよい (ADR-0087) | `com.etzhayyim.apps.<actor>.*` NSID 保持、`magatama.jsonld` 必須、domain collection のみ |
| 11 | **Key Directory** (E2E Keystore) | `key-directory` | Signal/X3DH/MLS 系の prekey bundle + identity key publish + fetch | `com.etzhayyim.signal.*` 系 NSID、plaintext 鍵を server に持たない (published pubkey + wrapped のみ) |
| 12 | **Secret Vault** (Zero-Knowledge Secret Manager) | `secret-vault` | encrypted secret storage。server は ciphertext + wrapped key のみ、plaintext は client/device key 経由でのみ復号 | `com.etzhayyim.vault.*` 系 NSID、Zero-Knowledge Invariant (CLAUDE.md root) 遵守 |
| 13 | **Inference Fleet** | `inference-fleet` | LLM / vision / embedding inference の gateway + backing compute pool | `com.etzhayyim.apps.murakumo.*` / `com.etzhayyim.apps.ameno.*` 等、model id は `llm-model-registry.ts` SSoT |
| 14 | **DID Directory** | `did-directory` | did method を自ホストで serve (did:plc / did:etzhayyim / did:web sub-actor 等) | `com.etzhayyim.plc.*` / `com.etzhayyim.identity.*`、W3C DID Resolution v0.3 準拠 |
| 15 | **Process Orchestrator** | `process-orchestrator` | BPMN 2.0 / OCEL / cron / event 駆動の multi-step workflow dispatcher | Zeebe + BPMN definitions (ADR-0056)、`vertex_bpmn_process_def` 経由で宣言 |

### AuthN / AuthZ の扱い

ADR-0024 で split した `authn.etzhayyim.com` / `authz.etzhayyim.com` は **Layer 4 (Entryway)
の 2 subcomponents** として扱う:

- `authn.etzhayyim.com` = Entryway AS の front (sign-in / passkey / OAuth / DID doc serve)
- `authz.etzhayyim.com` = Entryway AS の back (linked method mgmt / `/manage` UI / api-key CRUD)

独立レイヤにはしない。AT Protocol OAuth spec 的にはどちらも "Authorization Server"
の面。

### Routing Gateway の扱い

`routing-gateway` Worker (ADR-0023) は **infra glue** であってサービス層ではない。
did:web sub-actor path の `HOST:a:b:c → HOST/a/b/c/did.json` 解決のみ行う
L7 reverse proxy 的な存在。Layer 分類には載せない (= Layer 14 DID Directory
の補助、PDS から見ると binding 1 本で O(1) 解決する glue)。

## Layer 選定基準 (新規 Worker 起票時)

新規 Worker を立てる時の決定木:

```
Q1: end-user に UI を見せるか?
  Yes → Layer 9 Client App
  No  → Q2

Q2: 他 Worker / user agent に XRPC を serve するか?
  No  → Worker 不要 (script or cron で良い)
  Yes → Q3

Q3: 自分で repo record を持つか (path-DID or collection)?
  Yes → Layer 10 Actor Worker
  No  → Q4

Q4: 暗号鍵の publish/fetch か?
  Yes → Layer 11 Key Directory
  No  → Q5

Q5: 暗号化された secret の保管か?
  Yes → Layer 12 Secret Vault
  No  → Q6

Q6: LLM / inference compute の gateway か?
  Yes → Layer 13 Inference Fleet
  No  → Q7

Q7: DID 解決 / DID document の発行か?
  Yes → Layer 14 DID Directory
  No  → Q8

Q8: BPMN / workflow dispatch か?
  Yes → Layer 15 Process Orchestrator
  No  → 該当なし — ADR を書いて新レイヤを提案する
```

## 宣言方法

各 Worker の CLAUDE.md 冒頭に次のテーブルを必須化 (段階適用、新規 + 意味論変更時):

```
| 項目 | 値 |
|---|---|
| layer | <layer 簡名> (e.g. actor-worker / key-directory / ...) |
| at_standard | true / false |
| nsid_prefix | com.etzhayyim.apps.<actor> / com.etzhayyim.signal / ... |
| did | did:web:<host> または did:plc:... |
```

`deps.toml [[conventions]]` に新 rule `AT Protocol 15-Layer Taxonomy` を追加し、
本 ADR を `adr` フィールドで pin する。

## 既存 Worker の layer 割当 (2026-04-23 監査)

| Worker host | Layer |
|---|---|
| `atproto.etzhayyim.com` | **1 PDS + 4 Entryway** (両面、分離は将来課題) |
| `authn.etzhayyim.com` | 4 Entryway (AS front) |
| `authz.etzhayyim.com`, `accounts.etzhayyim.com` | 4 Entryway (AS back) |
| `yoro.etzhayyim.com` | 9 Client App |
| `shinshi.etzhayyim.com` | 10 Actor Worker |
| `animeka.etzhayyim.com` | 10 Actor Worker |
| `mangaka.etzhayyim.com` | 10 Actor Worker |
| `news.etzhayyim.com` | 10 Actor Worker |
| `yabai.etzhayyim.com` | 10 Actor Worker |
| `lawfirm.etzhayyim.com` | 10 Actor Worker |
| `dns.etzhayyim.com` | 10 Actor Worker |
| `kaikei.etzhayyim.com` | 10 Actor Worker |
| `microsoft.etzhayyim.com` | 10 Actor Worker |
| `lawyer.etzhayyim.com` | 10 Actor Worker |
| `sashiosae.etzhayyim.com`, `jpn.state.etzhayyim.com` (path DIDs) | 10 Actor Worker |
| `kyber-projector.etzhayyim.com` | 10 Actor Worker (path-DID L1 × 13) |
| `signal.etzhayyim.com` | 11 Key Directory |
| `vault.etzhayyim.com` | 12 Secret Vault |
| `murakumo.etzhayyim.com` | 13 Inference Fleet |
| `ameno.*` (browser-side) | 13 Inference Fleet (client compute variant) |
| `plc.etzhayyim.com` | 14 DID Directory |
| `did.etzhayyim.com` | 14 DID Directory (did:etzhayyim, ADR-0029) |
| `dispatcher.etzhayyim.com` | 15 Process Orchestrator |
| `routing-gateway` | (glue, not a layer) |

# Consequences

**Pros:**

- 新規 Worker の命名と責務が 15 択の決定木で一意に決まる
- `deps.toml [[projects]]` に `layer` フィールドを追加できる (将来作業)
- CLAUDE.md の drift (「これは AppView? PDS?」誤分類) を検出しやすくなる
- ADR-0056 / 0081 / 0087 / 0092 が Layer 10 Actor Worker 上の variant として
  整理でき、actor 関連 ADR 間の境界が明確になる

**Cons / 注意点:**

- `atproto.etzhayyim.com` が Layer 1 + Layer 4 両面で動いている事実は変わらない。
  将来分離するか、両面 Worker を許容するかは別 ADR で扱う
- 新レイヤの追加提案 (例: Relay 自ホスト、Ozone 自ホスト) は本 ADR の改訂ではなく
  **続編 ADR** で行う (1 ADR = 1 decision 原則)

**Non-breaking:** 既存 Worker コードは 1 文字も変えない。CLAUDE.md の記述も
段階適用でよい。ADR 採択 = 語彙の凍結のみ。

# Alternatives Considered

1. **AT Protocol 9 層に押し込む** — 却下。Key Directory / Secret Vault /
   Inference Fleet は明らかに PDS でも AppView でもなく、無理に PDS 扱い
   すると Faithful Public/Private rule (CLAUDE.md root) に違反する
2. **全部を "actor" と呼ぶ** — 却下。ADR-0092 の "every vertex as actor"
   は data model の話で、service layer の話とは直交する。混同すると
   「Murakumo は actor か?」のような無益な議論を呼ぶ
3. **Layer 番号に振らず名前だけ** — 却下。15 層の順序 (標準 9 → 拡張 6)
   が明示できると決定木が書ける。番号は recall 用で、将来 14.5 等の
   挿入は避ける

# References

- AT Protocol service reference: https://atproto.com/guides/overview
- ADR-2604231800 permission spec integration (Layer 4 Entryway の深掘り)
- ADR-0022 auth topology consolidation
- ADR-0023 auth Shannon-optimal 4-layer
- ADR-0024 authn/authz T4 split
- ADR-0056 BPMN-as-actor (Layer 15 Process Orchestrator の源流)
- ADR-0081 worker-direct Hyperdrive persistence (Layer 10 の書込 path)
- ADR-0087 magatama MCP tool facade (Layer 10 の MCP 面)
- ADR-0092 every vertex as actor (Layer 10 の data-model 側)
