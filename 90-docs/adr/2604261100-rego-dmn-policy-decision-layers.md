---
id: adr-2604261100-rego-dmn-policy-decision-layers
title: "ADR: Rego (AuthZ) + DMN (Decision) を Lexicon/BPMN と直交する契約レイヤーとして採用"
status: proposed
doc_type: adr
topic: policy-decision-contract-layers
authoritative: true
last_verified: 2026-04-26
authoritative_for:
  - authz-policy-ssot
  - decision-table-ssot
  - lexicon-bpmn-orthogonality
related:
  - adr-0023-auth-shannon-optimal-4-layer
  - adr-0056-bpmn-as-actor
  - adr-0036-worker-direct-hyperdrive-persistence
  - adr-2604261110-wproto-wreactive-wit-retirement
supersedes: []
superseded_by: []
---

# Context

定義レイヤーの DSM 整理 (2026-04-26) で、現 repo は以下を網羅:

- **Schema** = Lexicon (`00-contracts/lexicons/com/etzhayyim/**/*.json`, ~2206 app + 37 host)
- **Behavior** = BPMN (`etzhayyim-root/00-contracts/bpmn/`) + ADR-0056 BPMN-as-actor
- **Topology** = `magatama.jsonld` / `deps.toml` / `wrangler.jsonc`
- **Capability (T3 Container 限定)** = WIT (terminal、ADR-2604261110 で retire)

未カバーの直交軸:

1. **AuthZ policy** — XRPC handler / MCP adapter / `actor.invoke` の許可判断が
   `pds-handlers-*.ts` に TS ハードコード散在。Permission-Set / Follow-based
   coverage / Actor visibility が Lexicon JSON と TS の両方に分裂。
2. **Decision logic** — BPMN gateway 内の if/else が JS リテラル。
   Yabai classifier (ADR-0032) / Authority-Chain 1次2次判定 / lawfirm
   intake auto-route (ADR-0036) などが本来 decision table。

`00-contracts/dmn/ai/` ディレクトリは既に存在するが SSoT 宣言なし。
Rego は repo 未導入。

# Decision

`00-contracts/` 配下に **2 つの一級契約レイヤーを宣言**する:

| Layer | Path | Role | Evaluator |
|---|---|---|---|
| Rego policy | `00-contracts/policies/` | XRPC / MCP / actor.invoke の **AuthZ SSoT** | OPA bundle (CF Worker embedded or sidecar) |
| DMN decision | `00-contracts/dmn/` (既存) | BPMN gateway / classifier / 分類判定の **Decision Table SSoT** | DMN engine (Zeebe DMN or in-Worker JS evaluator) |

## 直交契約

| 契約 | 質問 | 答えるレイヤー |
|---|---|---|
| 何を交換するか (record / param) | shape | **Lexicon** |
| どう動くか (multi-step process) | flow | **BPMN** |
| 誰が呼べるか | gate | **Rego** ← 新設 |
| どう分類するか / 何を選ぶか | decision | **DMN** ← 一級化 |
| 何があるか (binding / actor / route) | topology | `magatama.jsonld` / `deps.toml` |

## Rego — AuthZ SSoT

- **Bundle 構造**: `00-contracts/policies/<package>/{policy.rego, data.json, test.rego}`
- **Package 命名**: NSID を逆ドメイン化 — `com.etzhayyim.apps.<project>.<method>` →
  `package etzhayyim.apps.<project>.<method>`
- **Input contract** (Worker → Rego):
  ```
  input = {
    nsid:        "com.etzhayyim.apps.foo.bar",
    actor:       { did: "did:etzhayyim:...", handles: [...] },
    target:      { did?, collection?, rkey? },
    permission_sets: ["..."],         // Lexicon Permission-Set 由来
    auth:        { method: "service-jwt"|"oauth"|"agent-token", scopes: [...] },
  }
  ```
- **Output contract**: `{ allow: boolean, reason: string, deny_obligations: [...] }`
- **評価点**: XRPC dispatch (`@etzhayyim/xrpc` の入口), MCP adapter
  (`pds/src/mcp-adapter.ts`), `actor.invoke` 直前。**全評価点が単一 bundle**
  を参照する (Shannon η=1)。
- **Distribution**: ビルド時に bundle (`*.tar.gz`) を生成し R2 配置 →
  Worker 起動時に fetch + cache (TTL 60s)。OPA-WASM コンパイル選択肢を
  検証 ADR fast-follow で評価。
- **Test**: `*_test.rego` を CI で `opa test ./00-contracts/policies/...`。
- **Lexicon との接続**: Lexicon JSON の `x-permissionSet` 拡張で
  required policy package を宣言 (実装は subtractive ADR で詳細化)。

## DMN — Decision Table SSoT

- **既存 `00-contracts/dmn/ai/` を一級化**: 全 BPMN gateway / TS 内 if/else
  classifier を DMN 1.5 XML に書き出す方針。
- **Decision 命名**: `com/etzhayyim/<project>/<decision>.dmn` (Lexicon と同階層)。
- **Evaluator**: Zeebe deploy 時は Zeebe DMN engine、CF Worker in-process は
  軽量 JS evaluator (候補: `dmn-eval-js`) を `magatama-host-sdk` に追加。
- **BPMN 連携**: BPMN `businessRuleTask` の `decisionRef` が DMN id と
  1:1 対応。
- **対象 (initial)**: yabai classifier、Authority-Chain 1次/2次判定、
  lawfirm intake routing、abuse takedown severity。

## 重複禁止 (Shannon η=1 系)

- **Rego ↔ Lexicon Permission-Set**: Permission-Set は **declaration**
  (Lexicon が宣言)、Rego は **enforcement** (誰が満たすか判定)。両者が
  別の事実を所有。同じ事実を両側に書かない。
- **DMN ↔ BPMN gateway**: gateway は flow merge/split のみ、判定式は DMN
  に出す。BPMN XML 内 `<conditionExpression>` で複雑式を書くのを禁止。
- **Rego ↔ DMN**: Rego = boolean access、DMN = N-of-M classification。
  両者は別質問に答える。

# Consequences

- TS handler 内に散らばった AuthZ / classifier ロジックを契約に出すことで
  ADR-0023 (Auth Shannon-Optimal 4-Layer) の境界が明確化。
- BPMN-as-actor (ADR-0056) と DMN が `decisionRef` 経由で接続され、actor
  追加コストは「BPMN row + DMN file」のみ。
- OPA bundle distribution に R2 + TTL 設計が必要 (build-time bundle、
  runtime fetch)。実装 ADR を fast-follow で別途。
- Lexicon の `x-permissionSet` 仕様拡張が必要。

# Alternatives Considered

- **Cedar (AWS)**: DID/AT graph との親和性で Rego を選択。Cedar の type
  system は魅力だが entity 表現が AT URI に直接マップしない。
- **XACML**: XML 重量級、運用コストが Rego の 5–10x。却下。
- **Lexicon 拡張のみで AuthZ**: Permission-Set declaration を実行可能
  policy にすると Lexicon が肥大化し schema/policy の分離が崩れる。却下。
- **OpenAPI 採用**: Lexicon と完全重複、ADR-0019 と矛盾。却下。
- **AsyncAPI/CloudEvents 採用**: 検討中、本 ADR には含めず別 ADR で扱う。

# References

- 90-docs/adr/0023-auth-shannon-optimal-4-layer.md
- 90-docs/adr/0056-bpmn-as-actor.md
- 90-docs/adr/2604261110-wproto-wreactive-wit-retirement.md (subtractive companion)
- 00-contracts/dmn/ai/ (既存)
- 00-contracts/lexicons/com/etzhayyim/host/ (Permission-Set 宣言基盤)
