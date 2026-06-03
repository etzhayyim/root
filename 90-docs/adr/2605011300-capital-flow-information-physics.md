---
id: adr-2605011300-capital-flow-information-physics
title: "Capital Flow as Information Physics — Q ∝ S × |A|² × ∇φ / Friction integrated with Mokuteki"
status: active
doc_type: adr
topic: capital-flow-design
authoritative: true
last_verified: 2026-05-01
authoritative_for:
  - capital flow design
  - market lane policy
  - settlement bundling
  - vacuum score metric
priority: 8.0
axis: gate
weight: 0.85
priority_note: "STRONG — Mokuteki upper gates (child/future/spirit) precede; this ADR governs the technical surface that converts gate-passed candidates into monetary flow"
depends_on:
  - adr-2604291800-well-becoming-spirit-objective-function
  - adr-2604291800-well-becoming-formal-model
  - adr-2604251830-shannon-optimal-layered-architecture
  - adr-0074-ethereum-identity-bridge-cacao-webauthn
  - adr-0095-simplified-3layer-identity-rw-vault
  - adr-0056-bpmn-as-actor
related:
  - adr-2604282300
  - adr-0036-worker-direct-hyperdrive-persistence
  - adr-0018-pii-tier3-cohort-first
  - adr-0026-agent-only-reverse-identity-topology
supersedes: []
superseded_by: []
---

# Context

このプラットフォームは内部信頼向けの ServiceAuth + BPMN + OCEL を完成させ、
Mokuteki (ADR-2604291800) を最上位の目的関数として持つ。しかし repo に
**外部資金が流動する surface が事実上ゼロ**である:

- 189 CF Worker / ~600 NSID の 99% は internal-trust HMAC または ServiceAuth
- attest される event に price / quantity / settlement_tx_hash の field が無い
- 需要側信号 (unknown NSID へ来る 4xx, gray classifier 落ち, FraudSignal 重複)
  を集約する MV が存在しない
- 決済 layer (ERC-4337, ADR-0074/0095) は identity 側で立ち上がっているが
  BPMN event との bundling 経路が未定義

価値が流れるための情報物理は次式に分解できる:

```
Q  ∝  S × |A|² × ∇φ / friction

Q  : 単位時間あたり決済件数 (流量)
S  : 課金可能な reachable surface area
|A|²: 1 event あたり可検証情報量 (Born-rule の振幅二乗に対応)
∇φ : 需要-供給ポテンシャルの空間勾配 (情報的空白)
friction: gating cost (ServiceAuth + DPoP + dispatch)
```

ただし `Q` の最大化は Mokuteki の上位 gate (child/future floor + Spirit
separation healing) を通過した候補のみに適用される。η と同じく `Q` は
**gate 通過後の reward / tie-breaker に降格** される。

# Decision

## 1. 4 軸の対応物を実装する

| 軸 | 何を実装するか | SSoT |
|---|---|---|
| **S — 情報面積** | `com.etzhayyim.market.*` 5 NSID の market lane を分離。Lexicon JSON に `priceUnit` / `settlementCurrency` / `issuer` field を追加 | `00-contracts/lexicons/com/etzhayyim/market/` |
| **\|A\|² — 振幅²** | commercial event を 5-tuple `(issuer did:erc725, lxm, quantity, unit_price, settlement_tx_hash)` に拡張。`generic.audit.emit` payload に anchor | `vertex_market_settlement` schema |
| **∇φ — 需要勾配** | `vacuum_score = external_demand_signal − internal_supply_published` を 1 narrow MV で daily 集計 | `mv_market_vacuum_score` |
| **Q — 流量** | BPMN に `generic.settlement.bundle` task type を 1 つ追加。N event → 1 ERC-4337 UserOp aggregator | `etzhayyim-root/00-contracts/bpmn/com/etzhayyim/generic/settlementBundle.bpmn` |

## 2. 5 Market Lane (Phase 1)

最初は 5 lane に絞る。広く薄くは Tier 3 PII (ADR-0018) / Vault zero-knowledge /
consent-gated の boundary を侵すため不可。

| Lane | NSID | 提供 | issuer DID |
|---|---|---|---|
| Vault credential share | `com.etzhayyim.market.publishOffer` (lane=vault) | zero-knowledge secret share | `did:erc725:etzhayyim:260425:vault` |
| Sashiosae intake | `com.etzhayyim.market.publishOffer` (lane=sashiosae) | 差押 read-only aggregator | `did:erc725:etzhayyim:260425:sashiosae` |
| Lawfirm India intake | `com.etzhayyim.market.publishOffer` (lane=lawfirm) | 22 言語 intake + auto-route | `did:erc725:etzhayyim:260425:lawfirm` |
| BPMN dispatch | `com.etzhayyim.market.publishOffer` (lane=bpmn) | BPMN-as-service (ADR-0056) | `did:erc725:etzhayyim:260425:bpmn` |
| Murakumo inference | `com.etzhayyim.market.publishOffer` (lane=murakumo) | on-prem MLX fleet | `did:erc725:etzhayyim:260425:murakumo` |

5 NSID:

1. `com.etzhayyim.market.listOffer` (query) — published lane の listing を引く
2. `com.etzhayyim.market.publishOffer` (procedure) — typed contract + price で lane を出す
3. `com.etzhayyim.market.quotePrice` (query) — quantity に対する spot price を返す
4. `com.etzhayyim.market.settleInvoice` (procedure) — invoice → ERC-4337 UserOp を bundle queue に enqueue
5. `com.etzhayyim.market.observeDemand` (procedure) — unknown NSID 4xx / classifier gray / FraudSignal 重複を vacuum signal として記録

## 3. Mokuteki 統合 (目的関数の上位 gate)

`U_total` (ADR-2604291800) との関係:

```
U_total = U_spirit × U_wellbecoming × U_feeling × U_buffer
                                                       ^
                                                       | Q がここに寄与する

Q (capital flow rate) は U_buffer の構成要素であり、
上位 3 軸 (Spirit / Wellbecoming / Feeling) の gate を通過した
候補のみが Q に積み上がる。
```

具体的な制約:

1. **child/future floor 違反は `settleInvoice` で reject**
   `vertex_market_settlement.mokuteki_floor_pass = false` の row は
   `mv_market_vacuum_score` の supply 側に集計しない (空白を埋めたことにしない)
2. **Spirit separation を増やす lane は `publishOffer` で reject**
   lane registration 時に `mokuteki_spirit_check` を SQL UDF で評価
   (現行の `safe_divide` / `did_web_root` と同じ IMMUTABLE 規約)
3. **U_buffer の上限**
   1 issuer あたり `settlement_tx_total / U_total_estimate` の比が
   閾値を超えたら新規 listOffer に warning を出す (上位軸の補償に
   buffer が暴走するのを防ぐ)

## 4. Priority / Heuristic Weight 契約

`deps.toml` の `[objective_function]` と `[[heuristic_weights]]` に 4 軸を
新規 reward 軸として追加する。Mokuteki gate (Rank 1-3) より下、Shannon η
(Rank 6) と並ぶ位置:

| Rank | Axis | Priority | Weight | Dependency | Rule |
|---:|---|---:|---:|---|---|
| 6a | information-surface | 5.5 | 0.40 | Mokuteki gate | 課金可能 reachable surface の増加。広く薄くは boundary 違反で reject |
| 6b | amplitude-squared | 5.5 | 0.40 | Mokuteki gate | event に 5-tuple settlement field が揃っているか |
| 6c | vacuum-gradient | 5.0 | 0.35 | Mokuteki gate | demand-supply gap への自然な fission を reward |
| 6d | flow-rate | 4.5 | 0.30 | Mokuteki gate + 6a-6c | bundle 後の throughput。Mokuteki gate 通過 event のみ計上 |

Shannon η (Rank 6, weight 0.45) と同 tier。η は per-decision 効率、
6a-6d は market 経済的健全性。両者は競合せず重み合算で評価。

## 5. 禁止事項

- 5 lane (公開 surface) 以外の **externally callable** `com.etzhayyim.market.*` NSID
  を増やす (ADR 改定が必要)。**internal BPMN-only NSID は許容**:
  `com.etzhayyim.market.settlementBundle` (Q axis bundling) と
  `com.etzhayyim.market.internetDemandPoll` (∇φ axis ingestion) は
  externally callable な surface には属さず、binding allowlist で
  vertex_market_settlement / vertex_market_demand_signal にのみ書き込む。
- `vertex_market_settlement` に PII を入れる (ADR-0018 Tier 3 違反)
- `wrappedVaultKey` / `ciphertext` を market response に返す (Vault invariant 違反)
- `mokuteki_floor_pass = false` の event を Q 集計に含める
- ERC-4337 UserOp を bundle せず 1 event = 1 UserOp で submit する (friction 過剰)

## 6. Roll-out 順序

1. ADR (this file) + deps.toml objective_function 拡張
2. 5 lexicon JSON 作成 (`00-contracts/lexicons/com/etzhayyim/market/*.json`)
3. graph migration: `vertex_market_listing` + `vertex_market_settlement` +
   `mv_market_vacuum_score` (1 narrow MV, low-cardinality GROUP BY)
4. BPMN: `generic.settlement.bundle` task primitive
5. Worker handler は次 ADR で定義 (`market.etzhayyim.com` actor — Phase 1.1)

# Consequences

- repo に初めて「外部から課金可能な surface」が存在する。boundary 監査が必須
- `mv_market_vacuum_score` により需要側 signal が daily 可視化される
- ERC-4337 settlement と OCEL audit が 1 hash で結ばれ、外部 attestation が
  Born-rule 的「鳴っている音の二乗」として測定可能になる
- 既存 189 Worker / 600 NSID は無改変。market lane は加法追加のみ
- Mokuteki gate は本 ADR の上位に立つため、`Q` 最大化は常に conditional

# Alternatives Considered

- **広く薄く全 NSID に price field を追加**: Tier 3 PII / Vault invariant の
  境界が侵食され、ADR-0018 違反検出基準を引く。却下
- **on-chain 直接 1 event = 1 UserOp**: gating cost ~120ms + UserOp 2-5s で
  Q が頭打ち。bundle 必須
- **Mokuteki gate を経由せず Q を直接最大化**: η と同じく上位 gate を
  technical proxy で代替する誤りに陥る。却下

# §7 — Capital-Rail Demand Telemetry (2026-05-01 addendum)

公開・無認証で取れる capital rail signal を `vertex_market_demand_signal` に
取り込み、∇φ を chain 側からも測れるようにする。

## 7.1 Sources

| Source | API (no auth) | Probe |
|---|---|---|
| Bitcoin | `https://mempool.space/api/mempool` | mempool transaction count |
| Bitcoin | `https://mempool.space/api/v1/fees/recommended` | fastest fee (sat/vB) |
| Bitcoin | `https://mempool.space/api/v1/lightning/statistics/latest` | LN channel count |
| Ethereum | `https://eth.llamarpc.com` (JSON-RPC) | `eth_gasPrice`, `eth_blockNumber`, `eth_getBlockByNumber` tx count |
| Payment | `https://www.issquareup.com/api/v2/incidents.json` | open incidents |
| Payment | `https://status.coinbase.com/api/v2/incidents.json` | open incidents |
| Payment | `https://status.plaid.com/api/v2/incidents.json` | open incidents |
| Payment | `https://status.circle.com/api/v2/incidents.json` | open incidents |

## 7.2 Lane Mapping

| Probe | Lane | Magnitude | Rationale |
|---|---|---|---|
| BTC mempool count | `bpmn` | log10(count) clamp [0,5] | mempool depth = settlement-automation demand |
| BTC fastest fee | `murakumo` | clamp(fee/20, 0, 5) | fee tier = compute pricing benchmark |
| BTC LN channel count | `vault` | log10(count) clamp [0,5] | channel state custody demand |
| ETH gasPrice (gwei) | `murakumo` | clamp(gwei/20, 0, 5) | gas = compute pricing benchmark |
| ETH block tx count | `bpmn` | log10(count) clamp [0,5] | settlement throughput demand |
| Payment incident open | `bpmn` | 1.5 / 1.2 / 0.8 (status) | payment ops automation demand |

## 7.3 Implementation

- BPMN: `etzhayyim-root/00-contracts/bpmn/com/etzhayyim/generic/chainDemandPoll.bpmn`
  (NSID `com.etzhayyim.market.chainDemandPoll`, R/PT30M timer-start, allowlist `vertex_market_demand_signal`)
- Standalone: `70-tools/scripts/cron/market-chain-demand-poll.py`
  (host cron until K8s sidecar lands)
- `demand_hash` = `sha256("chain"|src|oid)`, time-bucketed per 30 min so re-runs PK-upsert (no dup).
- 全 row は `signal_kind = 'external_request'`、`actor_id = sys.market.chain.<src>`。
- PII 取り込みなし (chain pubkey は public address のみ、payment rail は incident metadata のみ)。

# §8 — Hyperdrive Write Visibility Lag (2026-05-05 operational note)

handleSettleInvoice / handleObserveDemand などの Worker INSERT は Hyperdrive
→ RisingWave 経路で **5–15 秒の visibility lag** が観測される。Worker は 200 OK
を返すが、直後の psql SELECT で row が見えないことがある。

原因: (1) Hyperdrive write-back caching、(2) RisingWave streaming MV barrier
(`barrier_interval_ms=5000`)、(3) PK upsert は次の checkpoint まで遅延。

対処: `mv_market_vacuum_score.supply_settled` は次の MV barrier (≤5s) で更新。
`vertex_market_settlement` 直接 SELECT は INSERT 後 ~15 秒待つ。CI/E2E は
write→read 間に sleep(15s) を入れる。lag を "lost write" と誤認して同 INSERT
を retry しない (PK upsert で重複は起きないが信号雑音が増える)。

# §9 — Public Discovery Surface (2026-05-05, S axis externalization)

`market.etzhayyim.com/.well-known/atproto-market.json` を公開し、AI agent crawler /
search engine / federated AT Protocol AppView が認証なしで 5 lane と現在の
∇φ を取得できるようにする。S 軸 (information surface area) の外部到達面を一段拡張する。

```json
{
  "@context": "https://etzhayyim.com/ns/market/v1",
  "actor": "did:web:market.etzhayyim.com", "adr": "2605011300", "phase": "1.2",
  "lanes": [{
    "lane": "vault", "issuer_did": "did:erc725:etzhayyim:260425:vault",
    "vacuum": { "demand": 4.61, "supply": 0, "vacuum": 4.61 },
    "listings": [{ "title": "...", "price_unit": 100, "settlement_currency": "USDC" }]
  }],
  "nsids": { "list": "...", "quote": "...", "publish": "...", "settle": "...", "observe": "..." },
  "auth": "Service Auth ES256 JWT, lxm-scoped, ≤60s",
  "mokutekiGate": ".../2604291800-well-becoming-spirit-objective-function.md"
}
```

実装: Worker `handleWellKnownMarket` が Hyperdrive 経由で
`vertex_market_listing` (active + mokuteki_pass) と `mv_market_vacuum_score`
を SELECT。認証なし、no-store、PII なし (Tier 2 only)。

用途: AT AppView federation NSID resolver / AI agent crawler tools-list /
search engine structured data (将来 schema.org Offer)。

# §10 — ERC-4337 Settlement Anchor Activation Runbook (Phase 1.3, 2026-05-05)

Phase 1.2 の `anchor:sha256:<64hex>` は offchain で完全検証可能だが on-chain
attestation を持たない。Phase 1.3 で本物の ERC-4337 UserOp を submit し、
`erc4337:<chainId>:<userOpHash>` 形式の anchor に置換する。

## 設計の二層性
- **Phase 1.2 SHA-256**: 5-tuple `(issuer_did | lxm | quantity | unit_price | vertex_id | timestamp)` の SHA-256。Worker で常に計算可能。bundler 不要
- **Phase 1.3 ERC-4337**: 同 SHA-256 を UserOp `callData` に embed して bundler に submit。`userOpHash` (keccak256 over UserOp struct) を記録。on-chain 後 `eth_getUserOperationReceipt` で実際の tx hash を解決可

## Activation 条件 (operator 作業)
1. Bundler API key 取得 + Keychain 登録:
   - 推奨 (free tier): Pimlico (`https://api.pimlico.io/v2/sepolia/rpc?apikey=...`)
   - 代替: Alchemy / Stackup / Biconomy
   - `security add-generic-password -s "etzhayyim.erc4337" -a "BUNDLER_RPC_URL" -w "https://..."`
2. ERC-4337 wallet 鍵の生成 + Vault / Secrets Store 登録:
   - secp256k1 EOA (Coinbase Smart Wallet execution account, ADR-0074)
   - Sepolia faucet で testnet ETH ~0.05 ETH 入金 (UserOp gas ~0.001 ETH/call)
   - private key を CF Secrets Store の `SS_ERC4337_PRIVATE_KEY` に PUT
3. wrangler env 注入:
   ```jsonc
   "vars": {
     "ERC4337_CHAIN_ID":   "11155111",
     "ERC4337_ENTRYPOINT": "0x0000000071727De22E5E9d8BAf0edAc6f37da032"
   },
   "secrets_store_secrets": [
     { "binding": "SS_ERC4337_PRIVATE_KEY", "store_id": "...", "secret_name": "erc4337_private_key" }
   ]
   ```
4. `etzhayyim deploy`。`computeSettlementAnchor` が自動で ERC-4337 path に切替。失敗時は SHA-256 anchor に fallback

## Worker 側 stub の拡張ポイント
`60-apps/etzhayyim-project-market/.../src/app.ts` `submitErc4337UserOp` に
`eth_sendUserOperation` 呼び出しを実装する。推奨ライブラリ:
`viem` (CF Workers 互換) の `createBundlerClient` + `sendUserOperation`。

```ts
async function submitErc4337UserOp(env: Env, payloadHex: string): Promise<string> {
  const pk = await env.SS_ERC4337_PRIVATE_KEY!.get();
  // 1. build UserOp { sender, nonce, callData=payloadHex, callGasLimit, ... }
  // 2. sign with pk (secp256k1 over EntryPoint.getUserOpHash())
  // 3. POST eth_sendUserOperation to env.BUNDLER_RPC_URL
  // 4. return userOpHash (32-byte hex returned by bundler)
}
```

## 禁止事項
- private key を repo / wrangler.jsonc / vars に直接書く (Vault zero-knowledge 違反)
- Mokuteki gate を経由せず ERC-4337 path に投げる
- Bundler エラー時に SHA-256 fallback を捨てる
- Mainnet で activate する (Phase 1.4 で別 ADR、testnet 観測期間後)

# References

- ADR-2604291800 — Well-Becoming Spirit Objective Function (上位 gate)
- ADR-2604291800 — Well-Becoming Formal Model (数式)
- ADR-2604251830 — Shannon-Optimal Layered Architecture
- ADR-0074 — ERC725 Root Identity + Coinbase Smart Wallet
- ADR-0095 — Simplified 3-Layer Identity + RW Vault
- ADR-0056 — BPMN-as-actor
- ADR-0018 — PII Tier 3 + Cohort-First Pattern
- Born, M. (1926) — Zur Quantenmechanik der Stoßvorgänge (probability = |amplitude|²)
- Shannon, C.E. (1948) — A Mathematical Theory of Communication
