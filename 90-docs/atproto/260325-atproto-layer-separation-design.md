---
id: atproto-layer-separation
title: "AT Protocol Layer Separation — Layer 0 (AT Faithful) + Layer 1 (W Protocol Extension)"
status: active
doc_type: explanation
topic: at-protocol-layer-separation
authoritative: true
last_verified: 2026-03-25
authoritative_for:
  - AT Protocol vs W Protocol layer boundary
  - W Protocol extension classification
  - AT Protocol conflicting feature isolation
related:
  - w-protocol-at-superset
  - atproto-spec-compliance-analysis
  - w-protocol-federation-design
  - actor-visibility-governance
supersedes: []
superseded_by: []
---

# AT Protocol Layer Separation Design

## Decision

**W Protocol は AT Protocol に忠実に基づき、その上で拡張する。** 2 Layer に明確分離し、Layer 0 (AT Protocol) を壊さないことを設計制約とする。

## Principle

```
Layer 0: AT Protocol (忠実に準拠 — record format, DID, XRPC, firehose, Lexicon)
Layer 1: W Protocol Extension (AT Protocol の上に追加 — Cypher, wRPC, Signal, Governance)
```

**Rule: Layer 1 は Layer 0 を壊さない。** 外部 AT Protocol client が Layer 0 だけで正常に動作すること。

## Layer 0: AT Protocol (Faithful)

AT Protocol spec に忠実に準拠する機能。外部 AT Protocol client はこの layer だけで基本操作が可能。

### [PRODUCTION] Record Format

- AT Lexicon NSID + rkey + SHA-256 CID — 100% 互換
- Evidence: `00-contracts/wit/deps/kotodama-wproto/package.wit` (repo interface)

### [PRODUCTION] DID

- `did:web` method (W3C DID v1.0 準拠)
- Path-based sub-DID (`did:web:com.etzhayyim.com:entity:path`) — W3C DID v1.0 §5.1.2 controller relationship
- Evidence: `50-infra/cloudflare/workers/atproto/src/index.ts` (DID resolution)

### [PRODUCTION] XRPC Sole API

- `/xrpc/{NSID}` が唯一の外部 API surface (AT Protocol native)
- 272/272 endpoints route (100% routing coverage)
- Evidence: `50-infra/cloudflare/workers/atproto/src/index.ts`

### [PRODUCTION] Social = Bluesky Lexicon

- `app.bsky.*` (post/like/repost/follow) — AT Lexicon 準拠
- cross-actor = mention/reply/thread (AT Protocol native)
- Evidence: `00-contracts/wit/deps/kotodama-wproto/package.wit` (repo interface typed API)

### [PRODUCTION] Firehose

- `com.atproto.sync.subscribeRepos` — SSE event stream
- `#commit` event format 準拠 (seq/repo/action/cid/rev/time)
- Evidence: `50-infra/cloudflare/workers/atproto/src/index.ts` (subscribeRepos handler)

### [PRODUCTION] Repo Operations

- `com.atproto.repo.*` — createRecord/getRecord/listRecords/deleteRecord/putRecord/applyWrites/uploadBlob
- Evidence: PDS Worker XRPC handlers

### [PRODUCTION] OAuth + DPoP

- PAR (RFC 9126) + DPoP (RFC 9449) + S256 PKCE
- Evidence: `90-docs/260325-atproto-spec-compliance-analysis.md`

### [PRODUCTION] HandleWCommit = AT Protocol #commit Consumer

- WIT `commit-handler` の `commit` record は AT Protocol `subscribeRepos#commit` field names に忠実
- `seq` / `repo` / `collection` / `rkey` / `action` / `cid` / `rev` / `time` = AT Protocol spec 準拠
- Host が AT Protocol `ops[]` array を 1 operation/call に flatten (convenience, not deviation)
- Evidence: `00-contracts/wit/deps/kotodama-wproto/package.wit` (commit-handler interface)

### [PRODUCTION] Lexicon Namespace Extension

- `com.etzhayyim.apps.*` (per-app domain data) — AT Lexicon の正規拡張方法
- `com.etzhayyim.{convo|signal|rtc|files}.*` — W Protocol 4 namespace
- AT Protocol は namespace を無限に拡張可能 — 仕様に矛盾しない

## Layer 1: W Protocol Extension

AT Protocol に存在しない capability を追加する。Layer 0 を壊さず、AT Protocol client から見えない internal path で動作。

### Category A: AT Protocol の仕組みで実現可能な拡張

AT Protocol の Lexicon / service proxy / DID で表現できる機能。

| 機能 | 実装方法 | AT Protocol 準拠性 |
|---|---|---|
| **Follow-based reactive input** | `app.bsky.graph.follow` + firehose filter | AT Lexicon native |
| **DID-addressed Invoke** | XRPC service proxy (`atproto-proxy` header) | AT Protocol spec §service-proxying |
| **Path-based Sub-DID** | `did:web` path segments | W3C DID v1.0 §5.1.2 |
| **Actor Sensitivity** | Lexicon record property | AT Record extension |
| **RBAC/RACI governance** | Lexicon metadata records | AT Record extension |
| **Trust Score** | Application-level logic, AT Record output | AT Record extension |
| **Content Labeling** | `app.bsky.labeler.service` | AT Lexicon standard |
| **Richtext L1 Facets** | `facet-feature` variant `@field 10–39` (bold/italic/heading/list/etc.) — AT client は未知 field を無視しプレーンテキスト表示 | AT Lexicon forward-compatible (unknown facet feature = skip) |
| **Multi-DID per App** | DID controller chain | W3C DID v1.0 §5.1.2 |

### Category B: AT Protocol にない capability（矛盾なし）

AT Protocol に存在しないが、AT Protocol の動作を壊さない拡張。Internal path でのみ動作。

| 機能 | 性質 | Layer 0 への影響 |
|---|---|---|
| **Cypher Graph Query (47 methods)** | AT `listRecords` の superset read | なし — AT standard query も正常動作 |
| **Workers RPC (internal transport)** | 実装詳細 | なし — external は XRPC (AT native) |
| **wRPC Stream (backpressure)** | AT に stream 機構なし | なし — external firehose は SSE 維持 |
| **Signal Protocol E2E** | Application-level encryption | なし — AT Record 形式は維持 |
| **Pipeline durable write** | Internal durability layer | なし — external から不可視 |
| **MDAG commit chain** | Internal storage format | なし — CAR export は AT standard |
| **GovernanceGate** | Internal access control | なし — public XRPC は AT standard auth |
| **Consent (VC/VP + GNAP)** | Application-level metadata | なし — AT Record として永続化 |
| **WIT → Lexicon codegen** | Tooling | なし — 出力は AT Lexicon 準拠 |

### Category C: AT Protocol 設計思想と衝突する機能（隔離必須）

AT Protocol の前提（public federation, individual actor autonomy, DID signing）と衝突する機能。**Layer 0 に漏洩させない。**

#### C1. Default Sensitivity Floor

| 衝突 | AT Protocol は全 record public 前提 (federation model) |
|---|---|
| **隔離方法** | public record は AT firehose に流す。restricted record は Layer 1 internal path でのみアクセス可能。AT firehose consumer は public record のみ受信 |
| **AT Protocol view** | 全 public record が `subscribeRepos` で見える standard PDS |
| **W Protocol view** | sensitivity tier (T0-T3) で record 可視性を制御 |
| **Code location** | `50-infra/cloudflare/workers/atproto/src/index.ts` — ActorVisibilityGate middleware |

#### C2. Per-Method Authorization (Invoke/Serve)

| 衝突 | AT Protocol に「method」概念なし。全 DID が全 XRPC endpoint にアクセス可能 |
|---|---|
| **隔離方法** | XRPC endpoint = public (AT Protocol auth のみ)。Private method は internal-only (Invoke/Serve via Workers RPC) |
| **AT Protocol view** | Standard XRPC endpoints、DID signing で認証 |
| **W Protocol view** | DID-addressed method + GovernanceGate (RBAC/trust/consent) |
| **Code location** | `00-contracts/wit/deps/kotodama-wproto/package.wit` — invoke/serve interfaces |

#### C3. wRPC Stream Backpressure

| 衝突 | AT Protocol `subscribeRepos` は push-only SSE、flow control なし |
|---|---|
| **隔離方法** | External firehose は AT standard SSE (backpressure なし) を維持。Internal stream のみ wRPC credit-based backpressure |
| **AT Protocol view** | `subscribeRepos` SSE push stream (AT spec 準拠) |
| **W Protocol view** | wRPC LEB128 frame + credit-based flow control |

#### C4. Per-Entity MDAG Signing

| 衝突 | AT Protocol Repo は 1 DID 1 signature。W Protocol MDAG は per-entity signatures |
|---|---|
| **隔離方法** | XRPC export (CAR, getRepo) 時に primary DID で re-sign。Internal MDAG は per-entity signature chain を保持 |
| **AT Protocol view** | Standard Repo (1 DID signature) |
| **W Protocol view** | MDAG commit chain (N DID controllers) |

#### C5. Org-level Clearance Gating

| 衝突 | AT Protocol は個人 actor 自律前提。Org が member DID を制約する概念なし |
|---|---|
| **隔離方法** | Org 制約は internal governance のみ。AT federation view では個人 DID として見える |
| **AT Protocol view** | Independent actor DID |
| **W Protocol view** | Org sensitivity floor + trust + RBAC |

#### C6. Service-binding Authorization (Internal)

| 衝突 | AT Protocol は全操作に DID signing 必須 |
|---|---|
| **隔離方法** | Internal Workers RPC は service binding (DID signing 不要)。External XRPC は DID signing 必須 (AT Protocol 準拠) |
| **AT Protocol view** | DID signing required for all XRPC calls |
| **W Protocol view** | Service binding (0-hop, no crypto overhead) for internal path |

## Rules

| Rule | Description |
|---|---|
| **Layer 0 = AT Protocol faithful (CRITICAL)** | Record format, DID, XRPC, firehose, Lexicon は AT Protocol spec に忠実。独自 deviation 禁止 |
| **Layer 1 = internal-only extension (CRITICAL)** | Cypher, wRPC, Signal, GovernanceGate は internal path でのみ動作。XRPC facade に漏洩禁止 |
| **Category C 隔離 (CRITICAL)** | AT Protocol 設計思想と衝突する機能は Layer 1 に隔離。AT Protocol client が Layer 0 だけで正常動作すること |
| **AT Protocol field names (CRITICAL)** | Event format (`#commit`), record format, API response の field names は AT Protocol spec に忠実。W Protocol 独自 field name 禁止 |
| **External = AT Protocol native (CRITICAL)** | 外部クライアントから見える全 interface は AT Protocol 準拠。W Protocol Extension は internal path の追加 capability |
| **新規機能の Layer 判定 (CRITICAL)** | 新規機能追加時に Category A/B/C を判定。Category C なら隔離方法を明示してからコード実装 |

## Verification

AT Protocol compliance は `90-docs/260325-atproto-spec-compliance-analysis.md` で 7 specs × normative requirements を追跡。97% compliance (186/192 requirements)。

Layer 分離の検証:
1. External AT client が XRPC だけで record CRUD + firehose consume できること
2. Category C 機能が XRPC response に field として漏洩していないこと
3. HandleWCommit の commit record field names が AT Protocol `#commit` に忠実であること

## References

- `90-docs/260324-w-protocol-at-superset-architecture.md` — 2-Layer transport architecture
- `90-docs/260325-atproto-spec-compliance-analysis.md` — AT Protocol spec compliance (7 specs, 97%)
- `90-docs/260323-actor-visibility-governance-design.md` — Category C1/C5 隔離 (sensitivity/org clearance)
- `90-docs/260329-richtext-facet-l1-extension-design.md` — Richtext facet L1 extension (Category A)
- AT Protocol spec: https://atproto.com/specs/event-stream — `subscribeRepos#commit` format
- AT Protocol spec: https://atproto.com/specs/xrpc — XRPC + service proxying
