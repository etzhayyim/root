---
id: adr-2604231800-atproto-permission-spec-integration
title: "ADR: AT Protocol Permission Spec を canonical authorization surface として活用 — 4-axis gap closure"
status: active
doc_type: adr
topic: auth-permission
authoritative: true
last_verified: 2026-04-23
authoritative_for:
  - AT Protocol permission spec (https://atproto.com/ja/specs/permission) への準拠方針
  - permission-set / resource scope / DPoP / Service Auth JWT の欠落要素特定
  - 公式 permission scope と W Protocol governance (ADR-0023) の責務分界
related:
  - adr-0022-auth-topology-consolidation
  - adr-0023-auth-shannon-optimal-4-layer
  - adr-0029-did-etzhayyim-method-specification
supersedes: []
superseded_by: []
---

# Context

AT Protocol は 2025 に permission 仕様を
[`https://atproto.com/ja/specs/permission`](https://atproto.com/ja/specs/permission)
として確定した。これは **OAuth 2.0 scope の宣言的 superset** で、次の資源型を持つ。

| resource | 用途 | positional / 主要 param |
|---|---|---|
| `repo` | AT Repo record の write | `collection`, `action` |
| `rpc` | XRPC method 呼び出し | `lxm`, `aud` (少なくとも一方必須) |
| `blob` | blob upload | `accept` (MIME) |
| `account` | PDS hosting 管理 | `attr` (email/repo) |
| `identity` | DID doc / handle 管理 | `attr` (handle) |
| `include` | permission-set 参照 | NSID + optional `aud` |

各 permission-set は **NSID で lexicon に宣言された宣言的まとまり** で、auth server が
authorize flow 時に dynamic resolve し、UI で human-readable な consent 画面を
生成する。namespace authority (parent/sibling 参照禁止) と include の `inheritAud`
で安全に合成できる。

一方、本 repo の現状 (2026-04-23 監査):

| 層 | 状況 | 権威ソース |
|---|---|---|
| Permission-Set lexicon | 9 etzhayyim + 3 Bluesky 公式 = 22 セット宣言済 | `00-contracts/lexicons/com/etzhayyim/*/auth*.json` / `deps.toml [[conventions]] "Permission Set"` |
| OAuth 2.0 PAR + authorize + token + PKCE (S256) | 実装済 | `50-infra/cloudflare/workers/atproto/src/handlers/oauth.ts:37-255` |
| Scope parse / validate (`atproto`, `transition:`, `include:`, `repo:`, `rpc:`) | 実装済 | `50-infra/cloudflare/workers/atproto/src/auth/scope.ts:140-179` (`checkTokenScope`) |
| Service Auth JWT (ES256, `lxm` claim, 60s TTL) | 実装済 | `60-apps/etzhayyim-project-auth/worker/src-ts/service-auth.ts` / `10-protocol/xrpc/src/auth.ts:14-71` / `70-tools/etzhayyim/etzhayyim/scoped_auth.go` |
| DPoP proof parse (`jkt` thumbprint 抽出) | 実装済 | `oauth.ts:143-163` |
| **DPoP ES256 signature 検証** | **未実装** (header parse のみ) | 同上 |
| **resource scope `blob` / `account` / `identity`** | **未実装** (`repo` + `rpc` のみ) | `scope.ts:140-179` |
| **Service Auth JWT `sub` claim** | **未設定** (`iss`/`aud`/`lxm`/`exp` のみ) | `service-auth.ts` |
| **`.well-known/oauth-authorization-server`** | **未実装** | — |
| **`.well-known/oauth-protected-resource`** | **未実装** | — |

ADR-0022 (auth topology consolidation) と ADR-0023 (Shannon-optimal 4-layer) は
内部の auth boundary を L0 API Key / L1 ES256 JWT / L2 graph authority / L3 Signal X25519
の 4 層に分離しているが、**外向き federation 互換面** — すなわち外部 OAuth client
(Bluesky App, 3rd party agent, `@atproto/api`) が permission を要求する面 — は
公式 permission spec に寄せる必要がある。現在は spec の骨格 (PAR/PKCE/include:)
は入っているが、**cryptographic binding の担保** と **resource scope の網羅**
で穴があり、"spec 準拠" とは名乗れない。

# Decision

AT Protocol permission spec を **外部 authorization surface の唯一の正** として
採用し、以下 4 軸で gap closure を実施する。内部 governance (ADR-0023 の RBAC /
consent / crypto layer 分離) は直交レイヤとして維持し、permission-set と二重に
同じ判断を書かない。

## 方針 4 axis

1. **Permission-Set = 外部 consent の SSoT** — user-facing consent 画面で表示する
   scope は必ず lexicon-declared permission-set NSID を経由する。散在する
   `transition:generic` や custom scope string は permission-set に集約する
2. **DPoP proof は cryptographic に検証する** — header の `jkt` 抽出だけでは
   proof-of-possession の保証ゼロ。ES256 signature verify を必須化する
3. **resource scope を 5 種全部サポートする** — `repo` / `rpc` に加え `blob` /
   `account` / `identity` を scope parser と enforcer の両方に追加する。Bluesky
   互換 client が blob upload scope を request したとき reject しない
4. **`.well-known` discovery を serve する** — 外部 OAuth client が endpoint を
   自力発見できるようにし、手動設定を不要化する

## 責務分界

| 層 | 権威 | 用途 |
|---|---|---|
| **外部 scope (OAuth client → PDS)** | **本 ADR + atproto permission spec** | consent 取得、scope 検証、token 発行 |
| 内部 auth boundary (L0-L3) | ADR-0023 | Worker-to-Worker trust、crypto 分離、API key custody |
| identity 構造 (did:etzhayyim) | ADR-0029 | DID method 仕様、key rotation |
| token topology (API Key / ES256 JWT) | ADR-0022 | 2-token model、60s `lxm` scoped JWT |

**禁止**: permission-set lexicon の意味論を ADR-0023 に書くこと / ADR-0023 の
4-layer 境界を permission-set lexicon に書くこと — 一方だけに置き、他方は参照
のみとする。

# Work Plan

4 つの gap を優先度順に作業する。全て既存 Worker (`50-infra/cloudflare/workers/atproto`,
`60-apps/etzhayyim-project-auth/worker`) 内の additive 変更で完結し、外部 schema 変更なし。

## Implementation Status (2026-04-23, status = active)

| # | Gap | 実装 status | commit 対象 |
|---|---|---|---|
| W1 | DPoP ES256 signature verify | ✅ **DONE** | `auth/dpop.ts` (new), `handlers/oauth.ts:143-153` |
| W2 | blob/account/identity resource scope | ✅ **ALREADY DONE** (audit 誤認) | `auth/scope.ts:229-329` で実装済、`scope.test.ts` でカバー済 (39/41 pass) |
| W3 | Service Auth JWT `sub` claim | ✅ **DONE** (grace warn) | `service-auth.ts`, `index.ts`, `agent_token.go`, `auth/verify.ts` |
| W4 | `.well-known` discovery | ✅ **DONE** (endpoint は既存、scope list 強化) | `app.ts:720-746` で permission-set NSID + standalone resource scope を enumerate |

## W1. DPoP ES256 signature verify (CRITICAL) — DONE

現状 `oauth.ts:143-163` は `jkt` thumbprint を抽出するだけで、proof JWT の
署名検証が無かった → RFC 9449 の cryptographic binding 要件を満たさず。

実装: `50-infra/cloudflare/workers/atproto/src/auth/dpop.ts` (new) に
`verifyDpopProof` を port (reference: `60-apps/etzhayyim-project-auth/worker/src-ts/dpop.ts`)。
`typ=dpop+jwt` / `alg=ES256` / `htm` / `htu` / `iat` (30s future skew, 300s max age) /
`jti` / ES256 signature を全て検証。`oauth.ts:143-153` で `verifyDpopProof` を呼び出し、
失敗時は `400 invalidDpopProof` を返す。

## W2. Resource scope `blob` / `account` / `identity` (CRITICAL) — ALREADY IMPLEMENTED

本 ADR の初版 audit は scope.ts を古い状態で読んでいた。再監査で以下が確認できた:

- `scope.ts:229` — `AtpPermission` interface は 6 resource 型 (`repo|rpc|blob|account|identity|include`) 全て対応
- `scope.ts:238-263` — `parsePermissionScope()` が 5 resource 型の positional + param を parse
- `scope.ts:265-332` — `checkResourceScope()` が以下を enforce:
  - `repo` (line 269-287): createRecord/putRecord/deleteRecord × collection + action
  - blob (line 301-314): `uploadBlob` × `accept` MIME pattern
  - `account` (line 316-323): `updateEmail` / `requestAccountDelete` / `deactivateAccount`
  - `identity` (line 325-329): `updateHandle` / `signPlcOperation` / `submitPlcOperation`
- Permission-set lexicon には repo/rpc のみ含まれる (spec §namespace-authority 準拠、
  blob/account/identity は standalone scope 限定、`scope.ts:10` コメント明記)
- `scope.test.ts:9` が resource 5 型 parse を covers。39/41 test pass (残 2 は
  lexicon JSON file 存在テストで本 ADR 無関係)

## W3. Service Auth JWT `sub` claim (HIGH) — DONE (grace warn)

- `60-apps/etzhayyim-project-auth/worker/src-ts/service-auth.ts:109-133` —
  `signServiceAuth(..., sub?)` に optional 第 5 引数追加、payload に `sub: sub || iss` を注入
- `60-apps/etzhayyim-project-auth/worker/src-ts/index.ts:921-926` / `966-971` —
  bootstrap + proxyApiKeyManagement が `sub = accountDid` を渡して delegation 識別
- `60-apps/etzhayyim-project-auth/worker/src-ts/index.ts:1668-1689` —
  `handleGetServiceAuth` が request body の `sub` を受け取り、未指定時は `iss` にフォールバック
- `70-tools/etzhayyim/etzhayyim/agent_token.go` — `--sub <did>` flag が JWT payload に sub を追加
- `50-infra/cloudflare/workers/atproto/src/auth/verify.ts:150-213` —
  `verifyServiceAuthJWT` が `sub` を抽出。欠落時 **warn only (grace period)**、
  非-DID 形式は reject。grace 明けは `return null` に切替 (Phase 4)

## W4. `.well-known` discovery (MEDIUM) — DONE

- `50-infra/cloudflare/workers/atproto/src/app.ts:720-746` の両 endpoint は既に存在
- `buildScopesSupported()` helper を追加し `scopesSupported` が:
  - base: `atproto` / `transition:generic` / `transition:chat.bsky`
  - standalone resource: `blob` / `account` / `identity`
  - permission-set: `include:<NSID>` × `getPermissionSetIds()`
- `bearerMethodsSupported: ["header", "DPoP"]` に拡張 (従前 `["header"]`)
- `dpopSigningAlgValuesSupported` を `["ES256"]` に制限 (`dpop.ts` 実装と整合、
  ES384 は実装しないため advertise しない)

# Consequences

## Positive

- **外部 client 互換性**: `@atproto/api`, Bluesky 公式 App, 3rd party agent が
  scope parameter に `blob:` や `account:?attr=email` を含めても reject されない
- **cryptographic binding**: DPoP proof の署名検証で access token の
  proof-of-possession が実際に担保される (現状は名目のみ)
- **SSoT 単一化**: 外部 scope の意味論を permission-set lexicon に集約。
  scope string を手書きする箇所が scope.ts 内 1 箇所に限定
- **discovery 自動化**: `.well-known` 経由で client が endpoint を自動取得、
  手動設定ドキュメントが不要に

## Negative

- **lexicon 更新コスト**: 既存 9 permission-set に blob/account/identity 要素を
  足すと consent UI 表示文字列が変わる → i18n 再生成が必要
- **追加 verify コスト**: DPoP proof 1 件あたり ECDSA verify 1 回追加
  (~1ms CF Worker)。全 `/oauth/token` 呼び出しに効く
- **既存 client 影響**: 古い内部 CLI が `sub` claim 無しの JWT を送っている場合、
  sub required enforcement で reject される → grace period (2 weeks) で warn ログ
  のみ → 切替

## Neutral

- ADR-0022 / ADR-0023 は不変。本 ADR は「外部面を公式 spec に寄せる」だけで、
  内部 4-layer boundary は touch しない
- `did:etzhayyim` (ADR-0029) は resolver 側で permission 文脈と無関係に動作

# Alternatives Considered

## A1. atproto permission spec を無視して ADR-0023 の 4-layer を外部にも押し出す

- pros: 実装ゼロ、現状維持
- cons: 外部 OAuth client 互換性崩壊。`@atproto/api` が blob upload scope を要求
  したとき reject → federation 不能。**却下**

## A2. permission-set lexicon 廃止、全て bare scope string で管理

- pros: lexicon resolve のラウンドトリップ不要
- cons: consent UI が string 解釈依存になり i18n 不可、dynamic evolvability 喪失
  (permission-set 追加に re-authenticate 要求)。spec の核である **declarative user
  consent vs fine-grained technical grants の分離** を破壊。**却下**

## A3. DPoP を廃止し bearer-only に戻す

- pros: verify コスト削減
- cons: access token 漏洩時の完全な compromise。RFC 9449 は AT Protocol spec で
  RECOMMENDED。**却下**

## A4. 本 ADR を一括ではなく resource ごとに別 ADR に分割

- pros: 小粒度で review 可能
- cons: 5 個の tiny ADR になり relation graph が膨らむ。4 gap は同じ root context
  (公式 spec 準拠) を共有 = 1 decision に集約するのが ADR rule (90-docs/CLAUDE.md
  §ADR Rule "1 ADR = 1 decision") の "decision" 単位として適切。**却下**

# Migration

- **Phase 0** ✅ (本 ADR land 時): registry entry 追加。既存 `260324-atproto-permission-scope-design.md`
  の `related` に本 ADR を加える
- **Phase 1** ✅ (W1 + W3, 2026-04-23): DPoP signature verify + `sub` claim 実装。
  `sub` 未設定 token は warn log のみ (grace window 開始)
- **Phase 2** ✅ (W2, 2026-04-23): 再監査で実装済みを確認。scope.ts の blob/account/identity
  enforcement は既にあり、lexicon 定義も spec 準拠 (blob は permission-set から除外)
- **Phase 3** ✅ (W4, 2026-04-23): `.well-known/oauth-*` に permission-set NSID 列挙 +
  DPoP bearer method 追加
- **Phase 4** ⏳ (grace 明け, 2026-05-07 予定 = +2 weeks): `verify.ts:200-210` の
  `sub` 欠落 warn を reject に切替 (`return null`)。CLI clients は `etzhayyim agent-token --sub`
  で明示指定 or default `iss` を使用することで事前対応可

Phase 4 cutover 前に確認する項目:
- `[verifyServiceAuthJWT] missing sub claim` warn ログの頻度 (Logpush `atproto-worker` → B2)
- etzhayyim CLI の全 release が `sub` claim 送信に対応 (>= 2026-04-23 build)
- 外部 agent (CI, Claude Code session) が最新 CLI に更新済み

全 phase は existing Worker の additive deploy。DNS / route / schema 変更なし。

# References

## 公式仕様

- [`https://atproto.com/ja/specs/permission`](https://atproto.com/ja/specs/permission) — AT Protocol permission spec (本 ADR の正)
- [RFC 9449](https://datatracker.ietf.org/doc/html/rfc9449) — DPoP
- [RFC 9126](https://datatracker.ietf.org/doc/html/rfc9126) — PAR
- [RFC 7636](https://datatracker.ietf.org/doc/html/rfc7636) — PKCE
- [RFC 8414](https://datatracker.ietf.org/doc/html/rfc8414) — OAuth 2.0 Authorization Server Metadata

## 関連 ADR / Design

- `90-docs/adr/0022-auth-topology-consolidation.md` — 2-token model
- `90-docs/adr/0023-auth-shannon-optimal-4-layer.md` — L0-L3 internal boundary (直交)
- `90-docs/adr/0029-did-etzhayyim-method-specification.md` — did:etzhayyim method spec
- `90-docs/atproto/260324-atproto-permission-scope-design.md` — 本 repo 既存の
  permission scope 設計メモ (本 ADR が外部面を確定する canonical に昇格)

## 実装 citations

- `50-infra/cloudflare/workers/atproto/src/handlers/oauth.ts:37-255` — PAR / authorize / token
- `50-infra/cloudflare/workers/atproto/src/handlers/oauth.ts:143-163` — DPoP parse (W1 作業対象)
- `50-infra/cloudflare/workers/atproto/src/auth/scope.ts:140-179` — permission-set table + `checkTokenScope` (W2 作業対象)
- `60-apps/etzhayyim-project-auth/worker/src-ts/service-auth.ts` — ES256 signer (W3 作業対象)
- `60-apps/etzhayyim-project-auth/worker/src-ts/dpop.ts` — DPoP verify 既存実装 (W1 で再利用)
- `10-protocol/xrpc/src/auth.ts:14-71` — `ServiceAuth` class
- `70-tools/etzhayyim/etzhayyim/scoped_auth.go` — `etzhayyim agent-token --lxm <nsid>` (W3 作業対象)
- `00-contracts/lexicons/com/etzhayyim/*/auth*.json` — 9 permission-set lexicon (W2 で拡張)
