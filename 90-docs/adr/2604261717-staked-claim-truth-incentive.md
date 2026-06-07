---
id: adr-2604261717-staked-claim-truth-incentive
title: "ADR: Staked Claim Attestation — 正しいと得、嘘で損 (truth-incentive primitive)"
status: active
doc_type: adr
topic: claim-stake-truth-incentive
authoritative: true
last_verified: 2026-04-27
authoritative_for:
  - claim-level-stake-primitive
  - truth-incentive-game-theory
  - com.etzhayyim.claim.stakedAttestation lexicon
  - ClaimStakeEscrow.sol contract
related:
  - adr-0074-ethereum-identity-bridge-cacao-webauthn
  - adr-2604261100-rego-dmn-policy-decision-layers
  - adr-0046
  - adr-0032-gmail-direct-ingest-yabai-classifier
  - adr-2604251220-record-log-not-mst
  - adr-0036-worker-direct-hyperdrive-persistence
  - adr-0019-atproto-native-identifier-topology
  - adr-0029-did-etzhayyim-method-specification
supersedes: []
superseded_by: []
amends:
  - adr-0074-ethereum-identity-bridge-cacao-webauthn
amended_by: []
---

# Status timeline

- **2026-04-26 17:17 JST** — proposed (this ADR drafted)
- **2026-04-26 18:00 JST** — Phase 1 lexicons + contract + Worker module + migration written
- **2026-04-26 18:30 JST** — graph migration `20260426180000_vertex_claim_stake` applied to Kotoba/Datomic; `database.ts` regenerated (1830 tables, 29054 cols, 6 new claim entities)
- **2026-04-26 18:35 JST** — `ClaimStakeEscrow` deployed at `0x7C1d83E42Ac2860eA72Ae2A373e86F67726410A7` on chain 260425; 13/13 immutable + storage sanity reads matched spec
- **2026-04-26 18:45 JST** — Path A end-to-end smoke (postClaim → 60s window → claimUnchallenged → Refunded) passed on live chain; GCC roundtrip 10 → 9 → 10 ✅
- **2026-04-26 18:55 JST** — Path B end-to-end smoke (postClaim → challenge → arbiter-signed settle, claimWins=true → Upheld) passed; ECDSA recovery + 85/10/5 split + state machine 0→1→2→3 verified ✅
- **2026-04-27 09:16 JST** — Phase 2-B live path active: `RegoArbiter` deployed, `claim-consumer` tails `DecisionRecorded`, `worker-authz` exposes HMAC-gated `record-rego-decision` / `auto-settle-claim`, Murakumo judge is bound through Secrets Store, rebuttals persist through service binding, and Kotoba/Datomic stake state/outcome projection was backfilled + verified.
- **2026-04-26** — status promoted to **active**

# Verification (live chain 260425)

```text
ClaimStakeEscrow: 0x7C1d83E42Ac2860eA72Ae2A373e86F67726410A7
RegoArbiter:      0x53E29CA12Bd77fD35926627318036c7B2BBE245d
GCCStablecoin:    0x8e9A5162b2800E0D19acC1708A531A3954900E21
sealer/owner/arbiter/treasury/rewardPool: 0xaFed0Cb7633EDBd26aA52658e71528309F562501

Test A (Path A — unchallenged refund, 60-second window):
  postClaim(1 GCC, 60s) → state=Pending(1), escrow=1 GCC, sealer=9 GCC
  block.timestamp ≥ postedAt + 60 → claimUnchallenged() → state=Refunded(5)
  ⇒ escrow=0 GCC, sealer=10 GCC ✅ ERC20 roundtrip clean

Test B (Path B — challenge → arbiter-signed settle, claimWins=true):
  postClaim(1 GCC, 600s) → state=Pending(1)
  challenge(counter=0.5 GCC) → state=Challenged(2)
  arbiter sign keccak256(claimId, true, escrow, chainid) via EIP-191
  settle(claimWins=true, sig) → state=Upheld(3)
  ⇒ ECDSA.recover correctly identifies arbiter, 85/10/5 split executes,
     escrow=0 GCC, sealer=10 GCC ✅ (sealer=arbiter=claimant in this test, so net 0 P&L)

Phase 2-B (Rego decision registry + auto-settler):
  worker-authz:
    /internal/record-rego-decision  (HMAC-gated; signs + submits RegoArbiter.recordDecision)
    /internal/auto-settle-claim     (HMAC-gated; signs + submits ClaimStakeEscrow.settle)
    etzhayyim_REGO_ARBITER_ADDR=0x53E29CA12Bd77fD35926627318036c7B2BBE245d
    CLAIM_SETTLER_HMAC + SEALER_PRIV secrets present
  claim-consumer:
    workers_dev=false; cron + service-binding only
    AUTHZ_RPC=etzhayyim-authz
    SS_MURAKUMO_API_KEY=Secrets Store 1824561668fe47cc9127d493961885af/murakumo_api_key
    MURAKUMO_URL=https://murakumo.etzhayyim.com/api/openai/v1/chat/completions
    MURAKUMO_MODEL=qwen3-30b-a3b
    ops endpoints (/tick,/judge,/settler) HMAC-gated when reachable
  Kotoba/Datomic:
    cursor:claim-consumer:chain-260425:default = 32700 active fail_count=0
    cursor:claim-consumer:rego-arbiter:default = 32700 active fail_count=0
    vertex_claim_stake state backfill:
      0xb55c...0f99 = upheld   tx 0x54b4dffa4db402b167cc244ab2661f16e7d31f65ce57cefeceda1b9ecf945285
      0xb1a2...55f5 = refunded tx 0xad6ffd03ad9caf1fcff1a6be7260c58d455c026755bbccf413444559bdbc08e8
    pending judge rows = 0
```

The Path C (`noShow` after 14-day arbiter timeout) and a multi-EOA Path B
that actually exercises the 85 / 10 / 5 split as separate balance flows
remain to be tested when (i) Phase 2-B introduces a non-sealer arbiter
and (ii) the time budget allows a 14-day wait or a fork-chain test rig.

The XRPC routes `com.etzhayyim.claim.{post,challenge,settle,get}StakedAttestation`
are wired into `worker-authz/src-ts/index.ts`, gated on
`etzhayyim_CLAIM_STAKE_ESCROW_ADDR=0x7C1d…`, and deployed. `challenge` additionally
persists the off-chain rebuttal text to `claim-consumer` through the
`CLAIM_CONSUMER_RPC` service binding so the Murakumo judge can evaluate it;
the chain event itself intentionally carries only claim id / challenger /
counter-bond.

# Context

ADR-0074 で Ethereum bridge (`did:pkh` + SIWE + private chain + 8 contracts) が
LIVE になり、**operator 単位**の経済責任 (`MurakumoRegistry` の stake/slash、
`MurakumoEscrow` の per-job deposit) は実装済み。

しかし「**post / claim / attestation 単位**」で経済責任を載せる primitive は
まだ無い。現状の AT Record (`vertex_repo_record` append-only, ADR-2604251220) は:

- ✅ 署名されている (DID 由来、ADR-0029)
- ✅ 履歴に残る (record-log, hard-delete のみ)
- ❌ **嘘をついても損しない** — 訂正コストはゼロ
- ❌ **正しくても得しない** — 信頼性に対して経済的 reward なし

提案アーキテクチャの core idea は次の式で表せる:

```
V_claim = D · A · (1 - e^(-λ·I))     ;  I = α·S + β·H
                                          ↑
                                          stake (= economic irreversibility)
```

(D) DID, (A) signed record, (H) history, (S) stake。
現状 (S) が claim 単位で 0 なので、(I) → 0、嘘の expected cost = 0。

これを「**P(challenge) × bond**」にすれば、十分な bond で expected EV(lie) < 0 が確定する。
これが「情報を重くする最短ルート」。

# Decision

**`com.etzhayyim.claim.stakedAttestation` lexicon** + **`ClaimStakeEscrow.sol`** +
**challenge period game** で、AT Record と EVM stake を 1 つの IPLD object として
束ねる **claim-level stake primitive** を導入する。

ADR-0074 Phase 3 (CACAO AT Record) を carrier として再利用する (新 IPLD layer は
作らない — Shannon redundancy 違反になる)。

## 1. Game theory (核心)

| シナリオ | claimant payoff | 期待値 |
|---|---|---|
| 正しい claim, 無 challenge | `+bond + reward` (treasury subsidy) | **+ε** (得する) |
| 正しい claim, frivolous challenge → claimant wins | `+bond + counter_bond × (1-fee)` | **+bond** (大きく得) |
| 嘘 claim, 無 challenge | `+bond` (誰も騙されなかった) | **0** |
| 嘘 claim, challenged & loses | `0` (bond 没収) | **−bond** (確実に損) |

**Asymmetry**: 嘘の expected cost = `P(challenge) × bond`。
challenger は勝てば claimant の bond を取れるため自発的に挑む incentive がある
(triple-witness ADR-0046 + yabai classifier ADR-0032 が自動 challenger 候補)。

`P(challenge) > 0` が credible に保たれている限り、十分な `bond` で

```
EV(lie) = (1 − P) · 0 + P · (−bond)  =  −P · bond  <  0
EV(truth) = (1 − P) · (+ε) + P · (+bond)  >  0
```

**「正しいと得、嘘で損」** が数学的に強制される。

## 2. AT Record layer (light)

### Lexicon: `com.etzhayyim.claim.stakedAttestation`

```jsonc
// 00-contracts/lexicons/com/etzhayyim/claim/stakedAttestation.json
{
  "lexicon": 1,
  "id": "com.etzhayyim.claim.stakedAttestation",
  "defs": {
    "main": {
      "type": "record",
      "key": "tid",
      "record": {
        "type": "object",
        "required": ["claim", "claimHash", "bond", "chainId",
                     "escrowAddr", "challengePeriodSec", "createdAt"],
        "properties": {
          "claim":              { "type": "string", "maxLength": 4096 },
          "claimHash":          { "type": "string" },   // sha256 of canonical claim
          "claimType":          { "type": "string" },   // e.g. "factual", "medical", "whistleblower"
          "bond":               { "type": "string" },   // GCC wei (uint256 as string)
          "chainId":            { "type": "integer" },  // 260425 (private) or future L2
          "escrowAddr":         { "type": "string" },   // ClaimStakeEscrow contract
          "claimId":            { "type": "string" },   // bytes32 = keccak256(claimHash + did + nonce)
          "challengePeriodSec": { "type": "integer" },  // typically 7 days = 604800
          "arbiter":            { "type": "string" },   // "dmn:claim_dispute_v1" | "jury:N" | "oracle:0x.."
          "evidence":           { "type": "array", "items": { "type": "string" } },  // CIDs
          "createdAt":          { "type": "string", "format": "datetime" },
          "settled":            { "type": "boolean" },
          "outcome":            { "type": "string" }    // "unchallenged" | "upheld" | "slashed"
        }
      }
    }
  }
}
```

- `claimId` が AT Record と EVM contract を結ぶ join key
- `evidence[]` は CID 配列で `vertex_repo_record` 内の他 record / blob を参照可能
- `arbiter` は **DMN Decision Table (ADR-2604261100)** か **jury** か **single oracle** を
  名前空間で指定。最初は DMN 起点 (deterministic, on-chain verifiable) を default。

### Counter-claim lexicon: `com.etzhayyim.claim.challenge`

```jsonc
{
  "lexicon": 1,
  "id": "com.etzhayyim.claim.challenge",
  "defs": {
    "main": {
      "type": "record",
      "key": "tid",
      "record": {
        "type": "object",
        "required": ["targetClaimId", "counterBond", "rebuttal", "createdAt"],
        "properties": {
          "targetClaimId": { "type": "string" },  // bytes32 from stakedAttestation
          "counterBond":   { "type": "string" },
          "rebuttal":      { "type": "string", "maxLength": 4096 },
          "evidence":      { "type": "array", "items": { "type": "string" } },
          "createdAt":     { "type": "string", "format": "datetime" }
        }
      }
    }
  }
}
```

### Resolution lexicon: `com.etzhayyim.claim.resolution`

```jsonc
{
  "lexicon": 1,
  "id": "com.etzhayyim.claim.resolution",
  "defs": {
    "main": {
      "type": "record",
      "key": "tid",
      "record": {
        "type": "object",
        "required": ["claimId", "outcome", "txHash", "settledAt"],
        "properties": {
          "claimId":      { "type": "string" },
          "outcome":      { "type": "string" },  // "unchallenged" | "upheld" | "slashed"
          "rationale":    { "type": "string" },  // DMN decision id or oracle sig
          "txHash":       { "type": "string" },  // EVM settlement tx
          "settledAt":    { "type": "string", "format": "datetime" }
        }
      }
    }
  }
}
```

3 record は **append-only**。slash 時に元 stakedAttestation を mutate しない
(ADR-2604251220 record-log invariant 保持)。`resolution` record が
"slashed" を物語る annotation。

## 3. EVM layer (heavy) — `ClaimStakeEscrow.sol`

```
contract ClaimStakeEscrow {
    struct Claim {
        bytes32 claimId;
        bytes32 didHash;            // keccak256(did:etzhayyim:...)
        bytes32 atRecordCid;        // CIDv1 sha256
        uint256 bond;
        uint64  postedAt;
        uint64  challengePeriod;
        uint8   state;              // 0=Pending 1=Challenged 2=Upheld 3=Slashed 4=Refunded
        address claimant;           // payout addr
    }
    struct Challenge {
        bytes32 claimId;
        bytes32 challengerDidHash;
        uint256 counterBond;
        uint64  postedAt;
        address challenger;
    }

    function postClaim(bytes32 claimId, bytes32 didHash, bytes32 cid,
                       uint256 bond, uint64 challengePeriod) external;

    function challenge(bytes32 claimId, bytes32 challengerDidHash,
                       uint256 counterBond) external;

    /// Anyone can call after challengePeriod if no challenge.
    function claimUnchallenged(bytes32 claimId) external;

    /// Arbiter (DMN proxy / oracle / jury aggregator) only.
    function settle(bytes32 claimId, bool claimWins, bytes calldata arbiterSig) external;

    event ClaimPosted(bytes32 indexed claimId, address indexed claimant,
                      bytes32 didHash, bytes32 atRecordCid, uint256 bond);
    event ClaimChallenged(bytes32 indexed claimId, address indexed challenger,
                          uint256 counterBond);
    event ClaimUpheld(bytes32 indexed claimId, uint256 claimantPayout,
                      uint256 challengerLoss);
    event ClaimSlashed(bytes32 indexed claimId, uint256 challengerPayout,
                       uint256 claimantLoss);
    event ClaimRefunded(bytes32 indexed claimId, uint256 amount);
}
```

### Settlement split (initial)

| outcome | claimant gets | challenger gets | treasury | reward pool |
|---|---|---|---|---|
| `unchallenged` (period expired) | `bond` | — | — | `+ε` from pool → claimant |
| `upheld` (claim wins) | `bond + counter_bond × 0.85` | 0 | `counter_bond × 0.10` | `counter_bond × 0.05` |
| `slashed` (claim loses) | 0 | `counter_bond + bond × 0.85` | `bond × 0.10` | `bond × 0.05` |
| `noShow` (frivolous, no arbiter ruling within timeout) | full refund both sides | full refund | 0 | 0 |

**Reward pool** は treasury が事前に subsidize する。最初は数千 GCC で十分
(ADR-0074 §Phase 2-A の treasury が source)。

## 4. Arbiter resolution path

3 種類を **同じ `settle()` API** に統一する:

| arbiter type | resolution source | 用途 |
|---|---|---|
| `dmn:<table_id>` | **ADR-2604261100 DMN Decision Table** が deterministic 判定 | 構造化 claim (e.g. "patent X infringes Y", "company Z is registered") |
| `oracle:<addr>` | sealer / multisig が oracle として ECDSA 署名 (MurakumoEscrow と同型) | 専門知識 claim (medical / legal) |
| `jury:<n>` | n 人の DID から majority vote (Schelling point) | 主観的 claim (whistleblower, defamation) |

Phase 2-B の live 実装は **adapter-first**:

1. `claim-consumer` の Murakumo judge が challenged claim + rebuttal を読む
2. `worker-authz/internal/record-rego-decision` が sealer key で
   `RegoArbiter.recordDecision(claimId, claimWins, evidenceCid, sig)` を送る
3. `claim-consumer` が `DecisionRecorded` event を tail する
4. `worker-authz/internal/auto-settle-claim` が `ClaimStakeEscrow.settle(...)` を送る

現行 `ClaimStakeEscrow` は Phase 1 の ECDSA arbiter signature を保持するため、
`RegoArbiter` は decision registry + audit trail として機能する。将来の escrow v2
では `arbiterSig` の検証を **Rego policy (ADR-2604261100)** に委譲し、contract 側は
`require(IRegoArbiter(authorizedArbiter[arbiterType]).verify(claimId, claimWins, sig))`
だけを行う。これで arbiter logic を on-chain にも off-chain にも置ける。

## 5. Worker pipeline

```
yoro UI: "post staked claim"
   ↓
worker-authz/xrpc/com.etzhayyim.claim.postStakedAttestation
   ↓ (passkey-bearer session 必須、ADR-0023)
   ↓ 1) gcc.approve(escrow, bond)  ← user wallet (did:pkh) signs
   ↓ 2) ClaimStakeEscrow.postClaim(claimId, didHash, cid, bond, period)
   ↓ 3) PDS createRecord com.etzhayyim.claim.stakedAttestation
   ↓ 4) AT Record CID を contract event log に anchor (txHash → record)
   ↓
graph: vertex_claim_stake (label, id=claimId, didHash, bond, state, …)
        edge_claim_evidence (claim → blob)
        edge_claim_challenge (challenge → claim)
   ↓
challenger watcher (yabai / triple-witness):
  POST /xrpc/com.etzhayyim.claim.challenge
   ↓ approve+challenge+createRecord
   ↓
period 経過 OR challenge 発生 → arbiter resolution
   ↓
claim-consumer judgeTick → worker-authz/internal/record-rego-decision
   ↓
RegoArbiter.DecisionRecorded
   ↓
claim-consumer settlerTick → worker-authz/internal/auto-settle-claim
   ↓
ClaimStakeEscrow.settle(...) → ClaimSlashed / ClaimUpheld event
   ↓
PDS createRecord com.etzhayyim.claim.resolution
   ↓
graph: vertex_claim_stake.state = upheld|slashed
```

書き込みは ADR-0036 (Worker-direct Hyperdrive) に従い `vertex_claim_stake` /
`edge_claim_*` を Worker から Kysely で直書き。social broadcast は kotodama.jsonld
の `derive` で `app.bsky.feed.post` を auto-emit (Write-Only Derived, ADR-0004)。

## 6. Why this is the shortest path

「重くする」一番速い方法は **新層を足さず、既存 4 layer を線で結ぶ** こと:

```
DID (ADR-0029) ─────┐
                     ├─ com.etzhayyim.claim.stakedAttestation  ← 新規 lexicon (~200 LoC)
AT Record (0019) ───┤
                     ├─ ClaimStakeEscrow.sol             ← 新規 contract (~250 LoC)
GCC + Escrow pattern ┤
(ADR-0074) ─────────┘
                     ├─ DMN arbiter (ADR-2604261100)     ← 既存、薄い adapter のみ
Rego/DMN policy ─────┘
```

**新規コードは ~450 LoC + 3 lexicon JSON のみ**。新 storage / 新 chain / 新 cluster
は不要。CACAO IPLD wrapper (ADR-0074 Phase 3) も後付けで載るので、claim record を
CAR で federate する path も自動で開く。

# Consequences

## Positive

- **Information weight is now selectable per-record** — default 0 (today の挙動と完全互換)、
  user が `com.etzhayyim.claim.stakedAttestation` を選べば bond ぶん重い
- **Asymmetric truth incentive** — 数学的に EV(lie) < 0 < EV(truth) が enforce される
- **Challenger market が立つ** — yabai (ADR-0032) / triple-witness (ADR-0046) が自動 challenger に
- **Arbiter は plug-in** — DMN / oracle / jury を `arbiterType` で差し替え可能
- **既存 layer の Shannon η を維持** — 新層を足さない、既存 4 layer の合成のみ (η ≥ 0.85)
- **Federation-ready** — CACAO blob 化すれば AT Record CAR export で payload まで伝播
- **Treasury に手数料収入** — `bond × 0.10` が継続的に flow、reward pool / multisig 維持費に充当

## Negative

- **UX 複雑化** — yoro post UI に "stake this claim" toggle + bond 入力 + GCC approve 追加
- **GCC 流動性必要** — bond 用に user 側で GCC 保有 (faucet or DEX が要る)
- **arbiter abuse 余地** — DMN table 改ざん / oracle multisig 買収。
  mitigation: arbiter 変更を AT Record `com.etzhayyim.governance.arbiterChange` で公開、
  challenge period に signal が出る
- **Censorship 懸念** — 重要 claim が大量 frivolous challenge で疲弊する可能性。
  mitigation: counter-bond 最小値 = bond × 0.5 で frivolous attack に下限コスト

## Security

- **Reentrancy** — `settle()` は CEI pattern、`Checks-Effects-Interactions` 厳守、ReentrancyGuard
- **Front-running** — `postClaim` を public mempool に流さない (Worker→sealer 直送 path)、
  または commit-reveal を将来 phase で
- **Oracle key compromise** — 単一 oracle 不可、multisig (Phase 2-B 終了後) 必須
- **Arbiter collusion** — DMN table の hash を AT Record で公開、変更履歴は git anchor
- **Replay** — `claimId = keccak256(claimHash + did + nonce)`、nonce は contract 側 mapping で 1 回限り

## Shannon Redundancy Assessment

| primitive | function | overlap | verdict |
|---|---|---|---|
| `com.etzhayyim.claim.stakedAttestation` | claim record + bond pointer | none (新 lexicon) | **add** |
| `ClaimStakeEscrow.sol` | per-claim stake | `MurakumoEscrow` と類似だが scope 違う (job vs claim) | **add** |
| Arbiter dispatch | resolution | ADR-2604261100 DMN を再利用 | **reuse** |
| AT Record CAR carrier | federation | ADR-0074 Phase 3 CACAO を再利用 | **reuse** |
| Graph projection | analytics | ADR-0036 Worker-direct write を再利用 | **reuse** |

新規 layer 0 (3 lexicon + 1 contract、既存 layer 上に薄く乗る)。η ≈ 0.92 維持。

# Alternatives Considered

## Alt 1: 全投稿に強制 stake

- **Pro**: 仕組みがシンプル、信頼性最大
- **Con**: 投稿コストが非ゼロになり拡散が止まる。AT Protocol の "風" が死ぬ
- **Reject**: 提案 §8 "❌ 全投稿にステーク要求" に明記

## Alt 2: AT Record だけで stake (off-chain だけ)

- **Pro**: EVM 不要、UX 軽い
- **Con**: 不可逆性 = AT Record の append-only だけになり、罰の **強制力ゼロ**。
  「損する」の実体がないので EV(lie) ≥ 0
- **Reject**: 提案の核心 (1 - e^(-λ·I)) 項が起動しない

## Alt 3: optimistic rollup style (long fraud-proof window)

- **Pro**: gas cost を後ろ倒し、UX 軽い
- **Con**: settlement が数日〜数週遅延、UX が分かりにくい、private chain 上では over-engineering
- **Defer**: 公開 L2 移行時に検討

## Alt 4: AI / LLM に arbiter させる (single ML oracle)

- **Pro**: 即時 settlement
- **Con**: hallucination + bias + 説明不能性で訴訟リスク。決定のトレースが不可能
- **Reject as primary**, ただし `arbiter:oracle:<llm_addr>` として **opt-in** で許容
  (DMN > oracle > jury の優先順位)

## Alt 5: Filecoin に bond を deposit

- **Pro**: storage incentive と統合
- **Con**: Filecoin tx finality が遅い、GCC 経済圏外、stake/slash semantics が標準化されていない
- **Reject**: ADR-0048 で B2 を選んだ事実上の方針と整合しない

# Implementation Plan (phased)

## Phase 1 — Lexicon + Contract skeleton [ACTIVE]

| Surface | Path | Notes |
|---|---|---|
| Lexicons | `00-contracts/lexicons/com/etzhayyim/claim/{stakedAttestation,challenge,resolution}.json` | 新ディレクトリ |
| Contract | `50-infra/vultr/geth-private/contracts/src/ClaimStakeEscrow.sol` | `MurakumoEscrow.sol` を雛形に展開 |
| Foundry script | `50-infra/vultr/geth-private/contracts/script/DeployClaimStake.s.sol` | sealer key で deploy |
| Address record | `50-infra/vultr/geth-private/contracts/ADDRESSES.md` | `ClaimStakeEscrow` 追記 |
| AuthZ XRPC | `60-apps/etzhayyim-project-auth/worker-authz/src-ts/claim-stake.ts` | `postStakedAttestation` / `challenge` / `settle` 3 endpoint |
| AuthZ XRPC handlers | `com.etzhayyim.claim.{post,challenge,settle}StakedAttestation` | passkey-required, ADR-0023 |
| Graph migration | `30-graph/graph-schema/migrations/202604xxxxxx_claim_stake.ts` | `vertex_claim_stake` + `edge_claim_*` |
| MV | `mv_claim_stake_outcomes` | label, count by outcome, treasury balance |

## Phase 2 — Rego/Murakumo arbiter binding [ACTIVE]

- `RegoArbiter` adapter contract deployed at `0x53E29CA12Bd77fD35926627318036c7B2BBE245d`
- `claim-consumer` tails `DecisionRecorded` with independent cursor
  `cursor:claim-consumer:rego-arbiter:default`
- `worker-authz` owns sealer-funded internal routes:
  `/internal/record-rego-decision` and `/internal/auto-settle-claim`
- Murakumo judge v0 is active behind `SS_MURAKUMO_API_KEY`; deterministic
  DMN/Rego bundle remains the Phase 3 hardening target

## Phase 3 — yoro UI integration [PARTIAL]

- post composer に `Stake this claim` toggle + bond input + GCC approve flow
- `lib/superapp/SettingsPanelImpl.svelte` に `Claim history` panel (own + watched)
- challenge UI: "Challenge this claim" button on staked posts (24h 以内に rebuttal 提出)
- challenge rebuttal persistence is active via `CLAIM_CONSUMER_RPC`; historical
  rows without rebuttal remain human-review-only.

## Phase 4 — Auto-challenger pipeline [PROPOSED]

- `yabai` classifier (ADR-0032) の T3 LLM rule に "高 risk + claim type=factual" → auto-challenge proposal
- `triple-witness` (ADR-0046) の autonomy monitor に "stake claim mismatched with witness" alarm
- BPMN (ADR-0056): `claim_auto_challenge.bpmn` timer-driven `R/PT1H` で resolved-status を sweep

## Phase 5 — Federation via CACAO [PROPOSED, depends on ADR-0074 Phase 3]

- `com.etzhayyim.claim.stakedAttestation` を CACAO v2 DAG-CBOR で wrap
- AT Record CAR export 時に bond/escrow pointer 同梱、外部 PDS にも payload で federate
- Ceramic Network との互換確認

# References

- ADR-0074 — Ethereum Identity Bridge via WebAuthn + SIWE/CACAO over AT Protocol IPLD
- ADR-2604261100 — Rego/DMN policy decision layers
- ADR-0046 — yoro triple-witness autonomy monitoring (challenger candidate)
- ADR-0032 — Gmail direct ingest + yabai classifier (auto-challenger feed)
- ADR-2604251220 — Record-log semantics, not MST (append-only invariant)
- ADR-0036 — Worker-direct Hyperdrive persistence (claim graph projection)
- ADR-0019 — atproto-native identifier topology
- ADR-0029 — did:etzhayyim method specification
- `MurakumoEscrow.sol` / `MurakumoRegistry.sol` — escrow + stake/slash 雛形
- EIP-712 typed data signing — arbiterSig payload format
- Schelling point coordination games — jury arbiter rationale
