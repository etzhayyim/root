---
id: adr-2605152100-auth-unified-topology
title: "Auth Unified Topology — auth.etzhayyim.com canonical, 4-layer minimum, x-magatama-verified retirement"
status: active
doc_type: adr
topic: auth-topology
authoritative: true
last_verified: 2026-05-15
authoritative_for:
  - auth canonical domain (auth.etzhayyim.com)
  - worker split (auth = AuthN, authz = AuthZ)
  - oauth-as physical location (PDS)
  - x-magatama-verified cutover date
  - did issuance canonical path (ERC725)
  - nsid namespace ownership
related:
  - 90-docs/adr/0010-per-did-signing-key-custody.md
  - 90-docs/adr/0074-ethereum-identity-bridge-cacao-webauthn.md
  - 90-docs/adr/0095-simplified-3layer-identity-rw-vault.md
  - adr-2604240914-oauth-rs-binding-revocation-introspection
  - adr-2605141700-agent-authentication-api-key-rotation-pattern
supersedes:
  - adr-0022-auth-topology-consolidation
  - adr-0023-auth-shannon-optimal-4-layer
  - adr-0024-auth-accounts-worker-topology
amended_by: []
---

# Context

ADR-0022 / 0023 / 0024 で認証設計を段階的に整理してきたが、3 本の ADR が並立したことで
以下の 4 つの不整合が生じた:

| # | 不整合 | 根拠 |
|---|---|---|
| 1 | `authn.etzhayyim.com` vs `auth.etzhayyim.com` | 0024 実装は authn だが 2605131700 / CLI コードは auth |
| 2 | OAuth AS の物理位置 | `atproto.etzhayyim.com/oauth/authorize` が live、`authn.etzhayyim.com/oauth/authorize` は 404 |
| 3 | DID 発行責務 | authn Worker / plc.etzhayyim.com / ERC725 の 3 経路が並存 |
| 4 | `x-magatama-verified` 退役日未定 | "zero-traffic 1 sprint 後" の条件が消化されず進まない |

本 ADR はこの 4 点を確定し、0022/0023/0024 を supersede する。

---

# Decision

## 1. Domain Canonical

**`auth.etzhayyim.com` を canonical とする。`authn.etzhayyim.com` は 301 redirect。**

```
auth.etzhayyim.com   → etzhayyim-auth Worker     (AuthN: passkey UI, API Key, session)
authz.etzhayyim.com  → etzhayyim-authz Worker    (AuthZ: linked methods, org, actor score)
accounts.etzhayyim.com → authz Worker alias    (hostname alias のまま, redirect 不要)
authn.etzhayyim.com  → 301 → auth.etzhayyim.com/*   (deprecated, 2026-10-01 DNS 廃止)
```

Worker 名・リポジトリパスは変えない (`etzhayyim-auth` / `etzhayyim-authz` を維持)。
wrangler.jsonc の routes を更新するだけ。

## 2. 4-Layer Auth Stack (確定)

```
L0  Human Auth Root
      Browser:  WebAuthn / Passkey (Touch ID / Face ID)
                → auth.etzhayyim.com PKCE → mintBootstrapApiKey → sk_live_*
      Agent/CI: ~/.etzhayyim/auth.json { apiKey: sk_live_* }
      Worker:   CF Secrets { SS_SERVICE_AUTH_PRIVATE_KEY }

L1  Per-request Proof  (60s, 1 form only)
      Authorization: Bearer <ES256 JWT>
      Claims: { iss, aud, lxm, exp, jti }
      iss PRIMARY:  did:erc725:etzhayyim:260425:{identityContract}
      iss COMPAT:   did:web:auth.etzhayyim.com:user:{id}  (→ 2026-10-01)
      iss WORKER:   did:web:{worker}.etzhayyim.com

L2  Authority Resolution  (server-side, 60s cache)
      Primary key:  actor_did = did:erc725:etzhayyim:260425:{contract}
      Enforces:     lxm ∈ scope ∧ (rbac when populated)
      Single live enforcement: tokenScopes via vertex_api_key

L3  E2E Confidentiality  (orthogonal, Signal X25519)
      Field-level: signal:v1:{ciphertext}
      Keyed by: vertex_signal_identity.actor_did (ERC725)
```

## 3. OAuth AS の物理位置

**OAuth AS = `atproto.etzhayyim.com` (PDS) のみ。**

```
/.well-known/oauth-authorization-server → atproto.etzhayyim.com
/oauth/authorize                        → atproto.etzhayyim.com  ← LIVE
/oauth/token                            → atproto.etzhayyim.com  ← LIVE
/oauth/revoke                           → atproto.etzhayyim.com  (ADR-2604240914)
/oauth/introspect                       → atproto.etzhayyim.com  (ADR-2604240914)
```

`auth.etzhayyim.com` は **OAuth AS ではない**。担当は:
- `POST /xrpc/com.etzhayyim.auth.createApiKey` — passkey セッション → sk_live_* 発行
- `GET  /.well-known/did.json` — Worker 自身の did:web document
- `GET  /sign-in` / `/sign-up` — passkey UI (HTML)
- `POST /xrpc/com.etzhayyim.auth.passkeyRegister` / `passkeyAuthenticate`

CLI の `etzhayyim authn signin` は現状 2 つの問題がある (ADR-2605141700):
1. URL が stale: `authn.etzhayyim.com/oauth/authorize` → `atproto.etzhayyim.com/oauth/authorize` に修正必要
2. DPoP 未対応: AT Protocol OAuth AS は `dpop_bound_access_tokens=true` を要求するが CLI は PKCE のみ

**このため `etzhayyim authn signin` は別 ADR で DPoP 実装が完了するまで broken のまま。**
canonical な CLI 認証フローは以下:
1. ブラウザで `https://auth.etzhayyim.com/sign-in` を開き passkey 認証
2. 発行された `sk_live_*` を `~/.etzhayyim/auth.json` に手動コピー、または `etzhayyim authn set-key <key>`
3. 以降の全 XRPC 呼び出しは API Key → scoped ES256 JWT で自動認証

`etzhayyim authn signin` の DPoP 対応は `deps.toml [[migrations]] cli-dpop-etzhayyim-authn-signin` に
pending として記録する (本 ADR の scope 外)。

## 4. DID 発行 (新規)

| 対象 | 発行 DID | 担当 |
|---|---|---|
| 新規ユーザ signup | `did:erc725:etzhayyim:260425:{contract}` | ERC725 provisioning (authz Worker) |
| Worker サービス | `did:web:{worker}.etzhayyim.com` | per-Worker `.well-known/did.json` |
| AT federation actor | `did:plc:{...}` | `plc.etzhayyim.com` (ADR-0014, unchanged) |
| **廃止 (新規発行禁止)** | `did:web:auth.etzhayyim.com:user:*` | — (既存は 2026-10-01 まで read-only) |

`did:web:authn.etzhayyim.com:user:*` の resolution:
- **外部 HTTPS 呼出**: `authn.etzhayyim.com` → 301 → `auth.etzhayyim.com` でブラウザ/curl は透過的にフォロー
- **PDS 内部 service binding**: CF Worker-to-Worker は 301 を follow しない。PDS の
  `resolveDIDSigningKey` は `did:web:authn.etzhayyim.com:user:*` を検出したら `env.AUTH_SERVICE.fetch()`
  (service binding) 経由で `authn.etzhayyim.com` を直接呼ぶ既存パスを維持し、**auth Worker 側は
  両ホスト名 (`auth.etzhayyim.com` / `authn.etzhayyim.com`) に対して同一の `/users/:id/did.json`
  レスポンスを返す**。301 redirect ではなく同一 Worker が両 route を持つことで解決。
- 既存 DB レコードの書き換えは不要。`/users/:id/did.json` ハンドラを auth Worker に追加するだけ。

## 5. `x-magatama-verified` Retirement

**カットオーバー日: 2026-07-01 (固定)**

| ステップ | 期限 | 内容 |
|---|---|---|
| 残 ~10 Worker の ES256 移行 | 2026-06-15 | per-Worker checklist (ADR-0023 P4) |
| `[auth][deprecated]` ゼロ確認 | 2026-06-22 | CF tail log 1 week zero |
| PDS `verify.ts` x-magatama-verified branch 削除 | 2026-07-01 | deploy + smoke test |
| murakumo / comfyui / browser-host inbound 削除 | 2026-07-01 | 同 PR |

HMAC gate (ADR-0022 Amendment A2) は 2026-07-01 まで security 担保として維持し、
その後 branch ごと削除する。

## 6. NSID Ownership

| Worker | DNS | NSID prefix |
|---|---|---|
| etzhayyim-auth | `auth.etzhayyim.com` | `com.etzhayyim.auth.*` |
| etzhayyim-authz | `authz.etzhayyim.com` (+ accounts alias) | `com.etzhayyim.authz.*` |
| etzhayyim-pds (atproto) | `atproto.etzhayyim.com` | `com.atproto.*` |

**廃止 legacy alias (authz Worker から削除)**:
- `GET  /xrpc/com.etzhayyim.auth.getSession` on authz → `com.etzhayyim.authz.getSession` に rename
- `POST /xrpc/com.etzhayyim.auth.linkEmailBegin` / `linkEmailVerify` / `linkOAuthStart` on authz → `com.etzhayyim.authz.*` に rename

---

# Migration Checklist

```
# Domain (即時)
[x] wrangler.jsonc (etzhayyim-auth): routes に "auth.etzhayyim.com/*" 追加、"authn.etzhayyim.com/*" は 301 handler に変更
[x] auth Worker fetch handler: Host=authn.etzhayyim.com への受信を 301 → auth.etzhayyim.com にする
[x] auth Worker: /users/:id/did.json ハンドラ追加 (両ホスト名で同一レスポンス)
[x] PDS resolveDIDSigningKey: did:web:authn.etzhayyim.com 検出時に env.AUTH_SERVICE.fetch() 経路を維持 (変更不要を確認)

# NSID rename (Lexicon JSON 同時更新必須)
[ ] authz Worker: com.etzhayyim.auth.getSession → com.etzhayyim.authz.getSession (Lexicon JSON + handler)
[ ] authz Worker: com.etzhayyim.auth.linkEmail* / linkOAuth* → com.etzhayyim.authz.* (Lexicon JSON + handler)

# Phase 3 callsite migration (2026-05-15 完了)
[x] auth Worker getServiceAuth: _SVC_AUTH_ISS_ALLOWLIST (6 entries) + Option B HMAC gate (magatama のみ)
[x] auth Worker: /svc/browser-host/did.json — did:web:authn.etzhayyim.com:svc:browser-host DID document
[x] etzhayyim-email-relay: AUTH_RPC binding + getServiceAuthJwt + dual-header (pdsXrpc/pdsXrpcAs/pdsSqlQuery)
[x] etzhayyim-plc-directory: AUTH_RPC binding + getServiceAuthJwt + dual-header in emitFirehose
[x] etzhayyim-browser-host: AUTH_RPC binding + getServiceAuthJwt + dual-header + wrangler main → worker.ts

# x-magatama-verified 退役 (2026-06-15 / 2026-07-01)
[ ] 残 ~5 Worker (shinshi/news/mangaka/public-malak/llm): x-magatama-verified → ES256 JWT (期限 2026-06-15)
[ ] CF tail log 確認: [auth][deprecated] channel=x-magatama-verified が 1 week zero (2026-06-22)
[ ] PDS verify.ts + murakumo + comfyui: x-magatama-verified branch 削除 (2026-07-01)

# CLI (別 ADR 待ち — DPoP 実装完了後)
[x] deps.toml [[migrations]] に "cli-dpop-etzhayyim-authn-signin" を pending で記録 (本 ADR の scope 外)

# DNS 廃止
[ ] DNS: authn.etzhayyim.com CF zone record 削除 (2026-10-01)
```

---

# Consequences

**Positive**
- `auth.etzhayyim.com` 1 ドメインで "認証" を想起できる。内外のドキュメント・CLI 出力が一致
- OAuth AS = PDS の現実と設計書が一致 → "authn.etzhayyim.com/oauth/authorize が 404" バグが設計レベルで解消
- ADR 3 本 → 1 本 (本 ADR) に集約。残 ADR は直交テーマのみ
- `x-magatama-verified` の終端日確定 → security entropy が 0.34 → 0.90+ に収束

**Negative / Migration cost**
- wrangler.jsonc の routes 変更 (1 file, ~10 lines)
- CLI の URL 1 箇所修正
- authz Worker の NSID rename は Lexicon JSON も同時更新が必要 (CLAUDE.md LLM Guardrails)
- `authn.etzhayyim.com` の DNS を 2026-10-01 まで維持するコスト (CF zone record 1 件)

# References

- `60-apps/etzhayyim-project-auth/worker/wrangler.jsonc` — auth Worker routes
- `60-apps/etzhayyim-project-auth/worker-authz/src-ts/index.ts:2671-2674` — legacy NSID alias
- `50-infra/cloudflare/workers/atproto/src/auth/verify.ts` — x-magatama-verified branch
- `70-tools/etzhayyim/etzhayyim/auth.go` — CLI OAuth URL (stale)
- ADR-0010 — DID rotation key custody (L0 Worker trust root)
- ADR-0074 / ADR-0095 — ERC725 root identity (L1 canonical DID)
- ADR-2604240914 — OAuth revocation + introspection (OAuth AS lifecycle)
- ADR-2605141700 — Agent auth / API key rotation pattern
