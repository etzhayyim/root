---
id: atproto-permission-scope-design
title: AT Protocol Permission Scope — 2-Layer Authorization Design
status: active
doc_type: explanation
topic: atproto-permission-oauth-scope
authoritative: true
last_verified: 2026-04-09
authoritative_for:
  - AT Protocol permission spec integration
  - OAuth scope enforcement architecture
  - Permission set Lexicon JSON schema
related:
  - xrpc-cqrs-service-proxy-design
  - w-protocol-at-superset-architecture
  - consent-gated-data-sharing-design
supersedes: []
superseded_by: []
---

# AT Protocol Permission Scope — 2-Layer Authorization Design

## Goal

AT Protocol permissions spec (https://atproto.com/specs/permission) を W Protocol governance と **Shannon 冗長度 R=0** で統合する。

## Scope

PDS OAuth token issuance + XRPC endpoint enforcement。既存 RBAC/Clearance/Consent は変更しない。

## Executive Summary

AT Protocol permissions (OAuth client scope) と既存 governance (RBAC/Clearance/Consent) は **直交する情報チャネル** — 統合しても Shannon 冗長は発生しない。

## Decision

**2-Layer Authorization**: Layer 1 = AT Protocol Permission Scope (外部境界、OAuth token)、Layer 2 = W Protocol Governance (内部境界、RBAC/Clearance/Consent)。

## Shannon Analysis

```
H(authorization) = H(client_scope) + H(platform_governance)
                 = H(AT Protocol permissions) + H(RBAC + Clearance + Consent)
```

| 軸 | AT Protocol Permissions (Layer 1) | W Protocol Governance (Layer 2) |
|---|---|---|
| 問い | 「この OAuth client は何を操作できるか」 | 「この user/agent は何を操作できるか」 |
| 境界 | 外部 (third-party app → PDS) | 内部 (Worker → PDS → kagami) |
| 粒度 | resource type × action × collection | org × role × sensitivity × consent |
| Enforcement point | Token issuance + XRPC guard | canAccess() + Cypher RLS |

**I(Layer1 ∩ Layer2) ≈ 0** — 相互情報量がゼロに近いため冗長なし。

## AT Protocol Permission Resources

Spec が定義する 5 resource type:

| Resource | Spec 定義 | Permission Set 可否 |
|---|---|---|
| **repo** | Collection NSID × action (create/update/delete) | ✅ 可 |
| **rpc** | Endpoint (lxm) × audience (aud) | ✅ 可 |
| **blob** | MIME type pattern での upload 制御 | ❌ standalone のみ |
| **account** | Email/repo import 等の hosting 管理 | ❌ standalone のみ |
| **identity** | DID document/handle 管理 | ❌ standalone のみ |

## Permission Sets — Lexicon JSON (SSoT)

Permission set は **Lexicon JSON schema** (`type: "permission-set"`) で定義。

**Single Source of Truth**: `00-contracts/lexicons/com/etzhayyim/*/auth*.json`

### 定義済み Permission Sets

| Lexicon NSID | Title | nsAuthority | File |
|---|---|---|---|
| `com.etzhayyim.auth.authFull` | Full W Protocol Access | `com.etzhayyim.` | `auth/authFull.json` |
| `com.etzhayyim.convo.authConversation` | Conversations | `com.etzhayyim.convo.` | `convo/authConversation.json` |
| `com.etzhayyim.projector.authProjectManagement` | Project Management | `com.etzhayyim.projector.` | `projector/authProjectManagement.json` |
| `com.etzhayyim.signal.authEncryption` | Encryption & Signal Protocol | `com.etzhayyim.signal.` | `signal/authEncryption.json` |
| `com.etzhayyim.rtc.authCommunication` | Real-Time Communication | `com.etzhayyim.rtc.` | `rtc/authCommunication.json` |
| `com.etzhayyim.kagami.authGraph` | Graph Database | `com.etzhayyim.kagami.` | `kagami/authGraph.json` |
| `com.etzhayyim.governance.authGovernance` | Governance & Access Control | `com.etzhayyim.governance.` | `governance/authGovernance.json` |
| `com.etzhayyim.actor.authActorManagement` | Actor Management | `com.etzhayyim.actor.` | `actor/authActorManagement.json` |
| `com.etzhayyim.pds.authPlatform` | PDS Platform | `com.etzhayyim.pds.` | `pds/authPlatform.json` |

Bluesky compat (TS-only, Lexicon JSON なし):

| Set ID | Title | nsAuthority |
|---|---|---|
| `app.bsky.authSocial` | Social Features | `app.bsky.` |
| `chat.bsky.authDirectMessage` | Direct Messages | `chat.bsky.` |
| `com.atproto.authAccount` | Account Management | `com.atproto.` |
| `com.atproto.authIdentity` | Identity Management | `com.atproto.` |

### Namespace Authority Rule

Permission set は **自身の NSID namespace 以下のみ** 参照可能。`nsAuthorityCovers()` で enforce。

```
com.etzhayyim.convo.authConversation → com.etzhayyim.convo.* のみ grant 可能
com.etzhayyim.auth.authFull          → com.etzhayyim.* 全体を grant 可能
com.etzhayyim.actor.authActorManagement → com.etzhayyim.actor.* + com.etzhayyim.dmn.* + com.etzhayyim.form.* (共通親 com.etzhayyim.)
```

### Lexicon JSON Format

```json
{
  "lexicon": 1,
  "id": "com.etzhayyim.convo.authConversation",
  "defs": {
    "main": {
      "type": "permission-set",
      "title": "Conversations",
      "title:lang": { "ja": "会話機能" },
      "detail": "Create, send, and manage conversations.",
      "detail:lang": { "ja": "会話の作成・送信・管理" },
      "permissions": [
        { "type": "permission", "resource": "repo", "collection": ["com.etzhayyim.convo.*"], "action": ["create", "update", "delete"] },
        { "type": "permission", "resource": "rpc", "lxm": ["com.etzhayyim.convo.*"] }
      ]
    }
  }
}
```

## Scope String Syntax

AT Protocol scope string format (spec 準拠):

```
atproto                                          — base scope
transition:chat.bsky                             — Bluesky DM
transition:generic                               — transitional
include:com.etzhayyim.convo.authConversation           — permission set
repo:com.atproto.repo.createRecord?collection=app.bsky.feed.post — resource scope
rpc?aud=did:web:test.etzhayyim.com&lxm=com.etzhayyim.pds.getProfile        — rpc scope
blob?accept=image/*                              — blob (standalone only)
account?action=manage                            — account (standalone only)
identity:manage                                  — identity (standalone only)
```

## NSID Scope Derivation

`METHOD_REQUIRED_SCOPE` の per-method 列挙を廃止。NSID prefix でスコープを導出:

| NSID prefix | Required scope |
|---|---|
| `chat.bsky.*` | `transition:chat.bsky` |
| その他すべて | `atproto` |

Override 例外: `com.etzhayyim.projector.sendProjectMessage` → `atproto` (chat.bsky.convo と混在する dispatch のため)

## Codegen Pipeline

```
00-contracts/lexicons/**/*.json (SSoT)
  ↓ gen-lexicon-nsid-types.mjs
  → KnownLexiconPermissionSetNSID (compile-time literal union)
  ↓ gen-permission-scope-client.mjs
  → PermissionSetNSID, ScopeBuilder, PERMISSION_SET_REGISTRY
  ↓ gen-pds-lexicon-registry.mjs
  → XrpcInput<N> / XrpcOutput<N> (server-side typed dispatch)
```

## Implementation

### pds-scope.ts (Layer 1 enforcement)

| Function | 役割 |
|---|---|
| `deriveMethodScope(method)` | NSID prefix → required scope |
| `checkTokenScope(auth, method, body)` | Token scope 検証 (named + resource + include:) |
| `checkPermissionSetCoversMethod(tokenScopes, method)` | include: scope の lxm wildcard check |
| `validateScopes(requested)` | OAuth scope string 検証・展開 |
| `downscopeForRefresh(granted, requested)` | Token refresh 時の scope 縮小 |
| `expandPermissionSets(scopes)` | include: → resource scope 展開 (namespace authority enforce) |
| `buildPermissionSetLexicon(setId)` | Lexicon JSON schema 生成 (resolveLexicon 用) |

### pds-permissions.ts (Layer 2 governance)

| Function | 役割 |
|---|---|
| `canAccess(auth, repo, mode, collection?, sensitivity?)` | RBAC + Clearance + Consent + RACI |
| `canWriteRepo(auth, repo)` | Write gate (delegates to canAccess) |

### pds-handlers-oauth.ts

| 機能 | 実装 |
|---|---|
| PAR | scope 保持 |
| Token exchange | `validateScopes()` で検証・展開 |
| Token refresh | `downscopeForRefresh()` で scope 縮小 |
| Client metadata | `permissionSets` フィールドで全 set 公開 |

### pds-handlers-infra.ts (resolveLexicon)

Permission set Lexicon schema を `com.atproto.lexicon.resolveLexicon` で提供。`buildPermissionSetLexicon()` が `type: "permission-set"` schema を返す。

## Authorization Flow (2-Layer)

```
External Client (OAuth token with scope)
  │
  ├─ Layer 1: AT Protocol Permission Scope (pds-scope.ts)
  │   ├─ deriveMethodScope(nsid) → required scope
  │   ├─ checkTokenScope(auth, nsid, body) → 403 if insufficient
  │   ├─ expandPermissionSets() with namespace authority
  │   └─ checkResourceScope() for repo/rpc/blob/account/identity
  │
  ├─ Layer 2: W Protocol Governance (pds-permissions.ts)
  │   ├─ canAccess() — RBAC/Clearance/Consent/RACI
  │   └─ Graph RLS via authJwt → Kotoba/Datomic
  │
  └─ Execute (PDS → kagami → Kotoba/Datomic)

Internal Worker (service auth)
  │
  ├─ Layer 1: SKIP (internal = trusted)
  ├─ Layer 2: W Protocol Governance (full)
  └─ Execute
```

## Tests

- `pds-scope.test.ts` — 41 tests (namespace derivation, permission set expansion, namespace authority, resource scopes, downscoping, blob exclusion, Lexicon JSON ↔ TS consistency)
- `lexicon-codegen.test.mjs` — 2028 assertions (schema completeness, format compliance, NSID path consistency, codegen integration)
- `lexicon-primary-types.mjs` — lint (validates `type: "permission-set"` + `type: "permission"` sub-type)

## Caching (Spec 準拠)

- Permission set の stale lifetime: 24 時間
- 新規 session での expiration: 90 日
- Access token の scope は発行時に固定 (refresh で downscope のみ)

## Non-Goals

- 既存 RBAC/Clearance/Consent の変更・置換
- AT Protocol permission set の federation 配信 — Lexicon schema として公開すれば十分
- VC/VP (Verifiable Credential/Presentation) PoP binding — P4 planned
