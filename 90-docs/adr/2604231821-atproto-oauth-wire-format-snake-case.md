---
id: adr-2604231821-atproto-oauth-wire-format-snake-case
title: "ADR: atproto OAuth wire-format snake_case cutover — RFC 6749/7591/8414/9126/9449 準拠"
status: active
doc_type: adr
topic: auth-wire-format
authoritative: true
last_verified: 2026-04-24
authoritative_for:
  - OAuth 2.0 endpoint の request / response key 命名規則
  - `.well-known/oauth-*` metadata の field 命名規則
  - AS / Client metadata の grant_type / response_type / auth method 文字列値
  - `urn:ietf:params:oauth:request_uri:` 発行形式
related:
  - adr-2604231800-atproto-permission-spec-integration
  - adr-0022-auth-topology-consolidation
  - adr-0024-auth-accounts-worker-topology
supersedes: []
superseded_by: []
---

# Context

ADR-2604231800 で AT Protocol permission spec 準拠の 4 axis gap (DPoP signature
verify / resource scope / Service Auth `sub` claim / `.well-known` discovery) を
closure した。しかし同 ADR が監査外に置いた領域 — **endpoint の JSON wire
format** — が repo 全体で camelCase のまま残っており、外部 OAuth client から
見ると spec 非準拠状態にある。

## 規準

OAuth 2.0 の関連 RFC は全て snake_case を MUST で規定する:

| RFC | 対象 | 命名 |
|---|---|---|
| RFC 6749 | OAuth 2.0 core (grant_type, access_token, refresh_token 等) | snake_case |
| RFC 7591 | Dynamic Client Registration (client_id, redirect_uris, grant_types 等) | snake_case |
| RFC 7636 | PKCE (code_challenge, code_challenge_method, code_verifier) | snake_case |
| RFC 8414 | Authorization Server Metadata (authorization_endpoint, token_endpoint, scopes_supported 等) | snake_case |
| RFC 9126 | PAR (request_uri, pushed_authorization_request_endpoint, require_pushed_authorization_requests) | snake_case |
| RFC 9207 | OAuth 2.0 Authorization Server Issuer Identification (iss response parameter) | snake_case |
| RFC 9449 | DPoP (dpop_signing_alg_values_supported, dpop_bound_access_tokens, dpop_jkt, DPoP-Nonce header) | snake_case |
| RFC 9728 | OAuth 2.0 Protected Resource Metadata (resource, authorization_servers, bearer_methods_supported) | snake_case |

AT Protocol OAuth spec (`https://atproto.com/ja/specs/oauth`) はこれらを wrap した
profile で、独自の snake_case 拡張 (`dpop_bound_access_tokens: true`,
`client_id_metadata_document_supported: true`) を追加する以外は RFC そのまま。

## 現状 (2026-04-23 監査)

本 PDS / OAuth AS (`atproto.etzhayyim.com`) は **response / metadata を全面 camelCase**
で出している:

### AS metadata (`50-infra/cloudflare/workers/atproto/src/app.ts:730-745`)

```json
{
  "issuer": "https://atproto.etzhayyim.com",
  "authorizationEndpoint": "https://atproto.etzhayyim.com/oauth/authorize",
  "tokenEndpoint": "https://atproto.etzhayyim.com/oauth/token",
  "tokenEndpointAuthMethodsSupported": ["none", "privateKeyJwt"],
  "grantTypesSupported": ["authorizationCode", "refreshToken"],
  "responseTypesSupported": ["code"],
  "scopesSupported": [...],
  "dpopSigningAlgValuesSupported": ["ES256"],
  "codeChallengeMethodsSupported": ["S256"],
  "pushedAuthorizationRequestEndpoint": "https://atproto.etzhayyim.com/oauth/par",
  "requirePushedAuthorizationRequests": true,
  "clientIdMetadataDocumentSupported": true
}
```

### PR metadata (`app.ts:750-755`)

```json
{
  "resource": "https://atproto.etzhayyim.com",
  "authorizationServers": ["https://atproto.etzhayyim.com"],
  "bearerMethodsSupported": ["header", "DPoP"],
  "scopesSupported": [...]
}
```

### PAR / token endpoint (`handlers/oauth.ts`)

- Request form keys: `clientId`, `redirectUri`, `codeChallenge`, `codeChallengeMethod`, `scope`, `state`, `dpopJkt`
- PAR response: `{ requestUri, expiresIn }`
- `request_uri` value format: `urn:ietf:params:oauth:'requestUri':{uuid}` — **literal single quotes + camelCase token** (RFC 9126 §2.2 は `urn:ietf:params:oauth:request_uri:{id}` を要求)
- Token request: `grantType`, `codeVerifier`, `clientId`, `refreshToken`
- Token request grant values: `"authorizationCode"` / `"refreshToken"` (RFC 6749 §4.1.3 / §6 は `"authorization_code"` / `"refresh_token"`)
- Token response: `{ accessToken, tokenType, expiresIn, refreshToken, scope, sub }`
- Token response missing: `iss` (RFC 9207)、`DPoP-Nonce` header (RFC 9449 §8)

### Client metadata (`handlers/oauth.ts:249-262`)

```json
{
  "clientId": "https://atproto.etzhayyim.com/client-metadata.json",
  "clientName": "etzhayyim PDS",
  "redirectUris": [...],
  "grantTypes": ["authorizationCode", "refreshToken"],
  "responseTypes": ["code"],
  "tokenEndpointAuthMethod": "none",
  "applicationType": "web"
}
```

`dpop_bound_access_tokens: true` が欠落。全 field camelCase。

### 内部の入力側 alias (`60-apps/etzhayyim-project-auth/worker/src-ts/index.ts:617-631`)

authn Worker は form POST を parse する際に snake_case → camelCase の alias map
を持つ (`grant_type → grantType`, `client_id → clientId`, ...)。この結果:

- 外部 client が snake_case で送った **request** は authn Worker では処理できる
- ただし atproto.etzhayyim.com の PAR endpoint (`handlers/oauth.ts:41-51`) は `c.req.raw.formData()` を直接読むだけで alias が無い — snake_case body は受けられない
- response は両 Worker とも camelCase 固定

## 影響

| client | 現状 flow |
|---|---|
| etzhayyim CLI + 内部 Worker | ✅ 動く (camelCase 互換) |
| `@atproto/api` (Bluesky 公式 SDK) | ❌ AS metadata parse で `authorization_endpoint` が見つからず fail |
| Bluesky App / Ivory / Graysky | ❌ 同上。PAR の `request_uri` key 不在、token の `access_token` 不在で失敗 |
| 汎用 OAuth 2.0 library (oauthlib 等) | ❌ metadata discovery 時点で fail |

つまり現状は **federation 面では AT Protocol OAuth spec 非準拠**。ADR-2604231800
が建てた骨格 (DPoP verify / 5-resource scope / permission-set lexicon) は全て
snake_case 層の上でしか発火できないが、その層が無いので外部 client には到達
しない。

# Decision

OAuth 2.0 RFC 群 + AT Protocol OAuth spec に準拠した **snake_case wire format**
を atproto.etzhayyim.com (PDS + OAuth AS) と authn.etzhayyim.com (OAuth AS split) の全 OAuth
endpoint / metadata response で採用する。内部 TypeScript 変数名は camelCase を
維持 (root CLAUDE.md §Identifier: camelCase) し、**serialize / deserialize 境界
でのみ snake_case に変換**する。

## 方針 5 axis

1. **`.well-known` metadata は snake_case MUST** — OAuth 2.0 client は discovery
   時点で metadata を parse するため、ここが snake_case でないと後続全 flow が
   止まる。AS metadata + PR metadata 両方
2. **Request / Response body は snake_case MUST** — PAR / authorize / token /
   client-metadata 全てで OAuth 2.0 RFC が定める key 名を使う
3. **RFC-defined 値は spec 文字列 MUST** — `grant_type` の値は
   `"authorization_code"` / `"refresh_token"`、`token_endpoint_auth_methods` の
   値は `"private_key_jwt"` / `"none"` 等を literal で使う
4. **`urn:ietf:params:oauth:request_uri:` 形式 MUST** — RFC 9126 §2.2 準拠の
   URN prefix に修正
5. **内部 Worker 間は camelCase を維持** — Hono context / TS 変数 / service
   binding RPC は既存 camelCase のまま。変換は `app.ts` / `handlers/oauth.ts`
   の入出力境界 1 箇所に閉じ込める

## 責務分界

| 層 | 命名 | 権威 |
|---|---|---|
| **外部 wire (HTTP JSON / form)** | **snake_case MUST** | **本 ADR + OAuth 2.0 RFC** |
| Internal TS (Hono c.get, env, service-auth.ts, scope.ts types) | camelCase | root CLAUDE.md §Identifier |
| Permission-set lexicon (consent 画面表示) | camelCase NSID | ADR-2604231800 |
| Graph property / D1 column | snake_case | root CLAUDE.md exception |

禁止: TypeScript 内部で `access_token` 変数を使うこと / `.well-known` response で
camelCase field を出すこと。

# Work Plan

5 つの gap を優先度順に作業する。全て既存 Worker の additive 変更で完結し、
外部 schema 変更なし。Phase 1-3 は並行可、Phase 4-5 は Phase 1-3 land 後。

## Gap 一覧

| # | Gap | 影響範囲 | 優先度 |
|---|---|---|---|
| S1 | AS / PR metadata の snake_case 化 + `dpop_bound_access_tokens` + `jwks_uri` 宣言 | `50-infra/cloudflare/workers/atproto/src/app.ts:720-756` | **CRITICAL** |
| S2 | PAR / authorize / token endpoint の request/response snake_case 化 + `request_uri` URN 修正 + grant_type 値修正 | `50-infra/cloudflare/workers/atproto/src/handlers/oauth.ts` | **CRITICAL** |
| S3 | Client metadata (`/client-metadata.json`) snake_case 化 + `dpop_bound_access_tokens: true` 追加 | `handlers/oauth.ts:249-262` | HIGH |
| S4 | Token response に `iss` (RFC 9207) parameter 追加 + DPoP nonce 発行 (RFC 9449 §8) | `handlers/oauth.ts:203, 240` | HIGH |
| S5 | authn Worker `/oauth/token` の response snake_case 化 (現状 alias は input のみ) | `60-apps/etzhayyim-project-auth/worker/src-ts/index.ts` + `ui.ts` | MEDIUM |

## S1. AS / PR metadata snake_case (CRITICAL)

`app.ts:730-756` を差し替え:

```ts
app.get("/.well-known/oauth-authorization-server", (c) => {
  c.header("Cache-Control", "public, max-age=3600");
  return c.json({
    issuer: "https://atproto.etzhayyim.com",
    authorization_endpoint: "https://atproto.etzhayyim.com/oauth/authorize",
    token_endpoint: "https://atproto.etzhayyim.com/oauth/token",
    jwks_uri: "https://authn.etzhayyim.com/.well-known/jwks.json",
    token_endpoint_auth_methods_supported: ["none", "private_key_jwt"],
    token_endpoint_auth_signing_alg_values_supported: ["ES256"],
    grant_types_supported: ["authorization_code", "refresh_token"],
    response_types_supported: ["code"],
    scopes_supported: buildScopesSupported(),
    code_challenge_methods_supported: ["S256"],
    pushed_authorization_request_endpoint: "https://atproto.etzhayyim.com/oauth/par",
    require_pushed_authorization_requests: true,
    dpop_signing_alg_values_supported: ["ES256"],
    dpop_bound_access_tokens: true,
    client_id_metadata_document_supported: true,
  });
});

app.get("/.well-known/oauth-protected-resource", (c) => {
  c.header("Cache-Control", "public, max-age=3600");
  return c.json({
    resource: "https://atproto.etzhayyim.com",
    authorization_servers: ["https://atproto.etzhayyim.com"],
    bearer_methods_supported: ["header", "DPoP"],
    scopes_supported: buildScopesSupported(),
    dpop_bound_access_tokens_required: true,
  });
});
```

**新規 field**:
- `jwks_uri` — `private_key_jwt` client auth 検証時に client の JWKS を取り (client 側の `jwks_uri`)、AS 自身の署名検証用 JWKS は authn Worker の `/.well-known/jwks.json` を指す。**本 ADR では AS の JWKS を authn Worker 側 endpoint に集約**
- `token_endpoint_auth_signing_alg_values_supported: ["ES256"]` — private_key_jwt 使用時の client assertion 署名 alg
- `dpop_bound_access_tokens: true` — AS が DPoP binding を要求することを明示
- PR: `dpop_bound_access_tokens_required: true` — RS が DPoP binding を要求

## S2. PAR / authorize / token snake_case (CRITICAL)

### PAR endpoint (`handlers/oauth.ts:39-63`)

```ts
export async function handleOAuthPar(c: Context<AppType>): Promise<Response> {
  const form = await c.req.raw.formData().catch(() => null);
  const client_id = String(form?.get("client_id") || "");
  const redirect_uri = String(form?.get("redirect_uri") || "");
  const code_challenge = String(form?.get("code_challenge") || "");
  const code_challenge_method = String(form?.get("code_challenge_method") || "S256");
  const scope = String(form?.get("scope") || "atproto");
  const state = String(form?.get("state") || "");
  const dpop_jkt = String(form?.get("dpop_jkt") || "");
  const response_type = String(form?.get("response_type") || "code");
  const login_hint = String(form?.get("login_hint") || "");
  // ... validation (S256 強制等) ...
  const request_uri = `urn:ietf:params:oauth:request_uri:${crypto.randomUUID()}`;
  _oauthCache.set(request_uri, { data: {
    client_id, redirect_uri, code_challenge, code_challenge_method,
    scope, state, dpop_jkt, response_type, login_hint, created_at: Date.now(),
  }, expires_at: Date.now() + 90_000 });
  return c.json({ request_uri, expires_in: 90 }, { headers: { "Cache-Control": "no-store" } });
}
```

変更点:
- form key 全部 snake_case
- PAR TTL は **90 秒** (RFC 9126 §2.2 SHOULD)。現状 300 秒 (5 分) は上限超過
- `request_uri` URN 形式修正: `urn:ietf:params:oauth:request_uri:{uuid}` (literal quotes と camelCase 除去)
- response key: `request_uri`, `expires_in`

### Authorize endpoint (`handlers/oauth.ts:66-124`)

- Query param: `request_uri`, `client_id`, `redirect_uri`, `code_challenge`, `state`, `scope`
- Stored code data: `{ code, client_id, redirect_uri, scope, state, request_uri, code_challenge, sub, created_at }`

### Token endpoint (`handlers/oauth.ts:127-246`)

```ts
const form = await c.req.raw.formData().catch(() => null);
const body = form ? Object.fromEntries(form.entries()) : await c.req.json().catch(() => ({}));
const grant_type = String(body.grant_type || "");
const code = String(body.code || "");
const client_id = String(body.client_id || "");
const code_verifier = String(body.code_verifier || "");
const requested_scope = String(body.scope || "");
const refresh_token_in = String(body.refresh_token || "");
// client_assertion_type / client_assertion (private_key_jwt) も受理

if (grant_type === "authorization_code") { ... }
else if (grant_type === "refresh_token") { ... }
else return c.json({ error: "unsupported_grant_type" }, 400);

// Response (RFC 6749 §5.1 + RFC 9207 iss)
return c.json({
  access_token: session.accessJwt,
  token_type: dpop_jkt ? "DPoP" : "Bearer",
  expires_in: 7200,
  refresh_token: session.refreshJwt,
  scope: granted_scope,
  sub,
  iss: "https://atproto.etzhayyim.com",
}, { headers: { "Cache-Control": "no-store" } });
```

変更点:
- form key 全 snake_case
- grant_type 値: `"authorization_code"` / `"refresh_token"` (キャメル廃止)
- error code: `"invalid_request"`, `"invalid_grant"`, `"invalid_dpop_proof"`, `"unsupported_grant_type"`, `"server_error"` (RFC 6749 §5.2 + RFC 9449 §7.1)
- response key: `access_token`, `token_type`, `expires_in`, `refresh_token`, `iss`
- `Set-Cookie: etzhayyim_session=...` は **削除** (OAuth 2.0 token endpoint は cookie を返さない。既存の内部 UI session は /sign-in 経由で別に確立)
- `access_token` TTL: **900 秒 (15 分)** に短縮 (spec §access-token-lifetime "≤ 15 min if non-revocable")。現状 7200 (2h) は revocation なしでは違反

## S3. Client metadata snake_case (HIGH)

`handlers/oauth.ts:249-262`:

```ts
export function handleClientMetadata(c: Context<AppType>): Response {
  c.header("Cache-Control", "public, max-age=3600");
  return c.json({
    client_id: "https://atproto.etzhayyim.com/client-metadata.json",
    client_name: "etzhayyim PDS",
    client_uri: "https://atproto.etzhayyim.com",
    redirect_uris: [
      "https://atproto.etzhayyim.com/oauth/callback",
      "https://yoro.etzhayyim.com/oauth/callback",
    ],
    grant_types: ["authorization_code", "refresh_token"],
    response_types: ["code"],
    scope: "atproto transition:generic transition:chat.bsky",
    token_endpoint_auth_method: "none",
    application_type: "web",
    dpop_bound_access_tokens: true,
  });
}
```

## S4. `iss` parameter + DPoP nonce (HIGH)

### RFC 9207 `iss` in token response

S2 のレスポンスに含める。authorize redirect にも `iss` query param を付ける
(RFC 9207 §2)。

### RFC 9449 §8 DPoP-Nonce

spec は "Server-provided DPoP nonces are mandatory" と規定。実装:

- `/oauth/token` への DPoP 付き request に対し、初回 request 時に 400
  `use_dpop_nonce` error + `DPoP-Nonce: <random>` header を返す
- client は request を nonce 入り proof で再送
- nonce は KV or in-memory cache で 300 秒 TTL (`_dpopNonceCache`)
- 全 RS request (`/xrpc/*`) でも同じ pattern を適用 (別 ADR で RS side を扱う)

本 ADR では **token endpoint のみ** で nonce を enforce。RS side (XRPC) の
nonce enforcement は follow-up ADR とする。

## S5. authn Worker `/oauth/token` response (MEDIUM)

`worker/src-ts/index.ts` の既存 alias は **input 側のみ** で response は
camelCase で返している。OAuth flow 上は atproto.etzhayyim.com が AS の front を張り
authn は internal binding なので、authn の response が camelCase でも外部
client には直接見えない。しかし `/xrpc/com.atproto.server.getServiceAuth` や
`com.etzhayyim.auth.*` が snake_case/camelCase 混在すると後続 ADR で困る。

**作業**: authn Worker の `/oauth/token` / `/oauth/issue-code` / `/oauth/authorize`
endpoint の response も snake_case 化。`passkey.ts` の snake_case compat レイヤ
(既に存在) と整合。

# Migration

## Phase 0 (本 ADR land)

registry entry 追加。既存 ADR-2604231800 の `related` に本 ADR を加える。

## Phase 1 (S1 + S2 implementation, 2026-04-24)

`app.ts:730-756` (AS / PR metadata) + `handlers/oauth.ts` 全体を snake_case に
差し替え。**dual-read 期間** (2 週間) を設ける:

- metadata response は **snake_case のみ** 出す (camelCase は即時廃止)
- request body は snake_case 優先、camelCase 存在時は warn log 出しつつ受け入れる alias を `handlers/oauth.ts` 頭に追加
- `oauth-security.test.ts` / `well-known-oauth.test.ts` / `scope.test.ts` を
  snake_case assertion に書き換え

## Phase 2 (S3 + S4, 2026-04-25)

- Client metadata snake_case 化 (S3)
- `iss` parameter 追加 (S4 RFC 9207)
- DPoP nonce 発行 + `use_dpop_nonce` error response (S4 RFC 9449 §8)

## Phase 3 (S5, 2026-04-28)

authn Worker の response も snake_case 化。既存の camelCase response に依存して
いる可能性のある yoro frontend / etzhayyim CLI / passkey.ts を確認、snake_case 対応
を逆側にも追加。

## Phase 4 (grace close, 2026-05-08 = +2 weeks)

`handlers/oauth.ts` 頭の camelCase input alias を削除。warn log 頻度を確認して
ゼロであれば cutover 完了。

## Phase 5 (follow-up ADR, 2026-05-15)

RS side (XRPC `/xrpc/*` への DPoP nonce enforcement, token revocation endpoint
RFC 7009, introspection endpoint RFC 7662) を別 ADR で扱う。本 ADR の scope 外。

# Consequences

## Positive

- **federation 完全復活**: `@atproto/api` / Bluesky App / Ivory / Graysky /
  汎用 OAuth 2.0 library が atproto.etzhayyim.com を AS として使える
- **spec compliance claim 可**: AT Protocol OAuth spec の全 MUST を満たす
  (DPoP verify は ADR-2604231800 で、wire format は本 ADR で)
- **RFC 9207 `iss` で mix-up attack 防御**: 複数 AS 相手の client が正しい AS
  から token を受け取ったことを検証可能に
- **access_token TTL 短縮**: 7200 → 900 秒で漏洩時 window 最小化
- **DPoP nonce で replay 防御強化**: 現状 300s window 内 replay は jti cache のみで止めていたが、server-controlled nonce で時刻ずれ攻撃も遮断

## Negative

- **内部 Worker の既存 test 書き換え**: `oauth-security.test.ts` 等で
  `requestUri` / `accessToken` 等を assert しているもの全面修正
- **yoro / etzhayyim CLI の response parse 修正**: 内部から叩いている箇所で
  `response.accessToken` を読んでいれば `response.access_token` に変更必要
- **DPoP nonce 実装コスト**: 全 `/oauth/token` request が 2 RTT (初回 400 →
  nonce 入り再送) になる。keep-warm cache を入れれば 2 回目以降は 1 RTT

## Neutral

- ADR-2604231800 の W1–W4 は不変。本 ADR は同 ADR の wire format 層の補完で
  あって、permission-set / DPoP signature verify / resource scope の設計判断
  には touch しない
- 内部 TS 変数名の camelCase は維持。境界でのみ snake_case 変換

# Alternatives Considered

## A1. camelCase のまま維持し、外部 client は etzhayyim-specific SDK に寄せる

- pros: 実装コストゼロ
- cons: AT Protocol federation 不能。Bluesky 互換性を捨てることになり、本
  platform のコア価値 (W Protocol = AT Protocol superset) に反する。**却下**

## A2. metadata だけ snake_case にして request/response は camelCase 維持

- pros: 作業量半減
- cons: client が metadata から `token_endpoint` を発見した後、実際の token
  request で camelCase を強制されると spec 違反。step 2 で止まる client が
  発生。**却下**

## A3. 両命名を response に併記 (`{"access_token": x, "accessToken": x}`)

- pros: backward compat 保障
- cons: RFC 8414 は strict JSON schema を要求。未知 field は無視されるべきだが
  `access_token` と `accessToken` が両方あると保守上混乱。response size も
  倍近く。**却下**

## A4. atproto.etzhayyim.com は snake_case、authn.etzhayyim.com は camelCase のまま

- pros: Phase 5 (authn 側書き換え) 不要
- cons: internal consistency が崩れ、今後 T4 split 再構成時に drift 再発。
  少なくとも `/oauth/token` は両 Worker で同じ wire format にする必要がある。
  **部分採用** — authn の **internal XRPC (`/xrpc/com.etzhayyim.auth.*`)** は
  camelCase 維持 (内部 alias のため)、**OAuth endpoint (`/oauth/*`)** のみ
  snake_case 化

# Non-Goals

本 ADR は **scope 外**:

- RS (XRPC `/xrpc/*`) 側の DPoP nonce enforcement — Phase 5 follow-up
- Token revocation endpoint (RFC 7009) 実装 — Phase 5 follow-up
- Token introspection endpoint (RFC 7662) 実装 — Phase 5 follow-up
- `authorization_details` (RFC 9396 Rich Authorization Requests) 対応
- FAPI 2.0 対応 (high-assurance profile)
- 内部 TS 変数名の snake_case 化 (root CLAUDE.md §Identifier に反するため不変)

# References

## 公式仕様

- [RFC 6749](https://datatracker.ietf.org/doc/html/rfc6749) — OAuth 2.0 core
- [RFC 7591](https://datatracker.ietf.org/doc/html/rfc7591) — Dynamic Client Registration
- [RFC 7636](https://datatracker.ietf.org/doc/html/rfc7636) — PKCE
- [RFC 8414](https://datatracker.ietf.org/doc/html/rfc8414) — Authorization Server Metadata
- [RFC 9126](https://datatracker.ietf.org/doc/html/rfc9126) — PAR
- [RFC 9207](https://datatracker.ietf.org/doc/html/rfc9207) — AS Issuer Identification
- [RFC 9449](https://datatracker.ietf.org/doc/html/rfc9449) — DPoP
- [RFC 9728](https://datatracker.ietf.org/doc/html/rfc9728) — Protected Resource Metadata
- [AT Protocol OAuth spec](https://atproto.com/specs/oauth)
- [AT Protocol Permission spec](https://atproto.com/ja/specs/permission)

## 関連 ADR

- `90-docs/adr/2604231800-atproto-permission-spec-integration.md` — permission spec 準拠 (本 ADR の前段)
- `90-docs/adr/2604231811-atproto-extension-service-layers.md` — 15-layer taxonomy (Entryway 層の責務)
- `90-docs/adr/0022-auth-topology-consolidation.md` — 2-token model
- `90-docs/adr/0023-auth-shannon-optimal-4-layer.md` — L0-L3 internal boundary
- `90-docs/adr/0024-auth-accounts-worker-topology.md` — authn/authz T4 split

## 実装 citations

- `50-infra/cloudflare/workers/atproto/src/app.ts:720-756` — AS / PR metadata (S1 作業対象)
- `50-infra/cloudflare/workers/atproto/src/handlers/oauth.ts:38-263` — PAR / authorize / token / client-metadata (S2, S3, S4 作業対象)
- `50-infra/cloudflare/workers/atproto/src/auth/dpop.ts` — DPoP ES256 verify (S4 nonce 追加対象)
- `50-infra/cloudflare/workers/atproto/src/auth/scope.ts:229-329` — 5-resource scope parser (不変)
- `60-apps/etzhayyim-project-auth/worker/src-ts/index.ts:617-631` — snake_case→camelCase alias (S5 でOAuth endpoint response を snake_case 化)
- `60-apps/etzhayyim-project-auth/worker/src-ts/ui.ts:163-171` — 既存 snake_case compat (parity 維持)
- `50-infra/cloudflare/workers/atproto/src/oauth-security.test.ts` — Phase 1 test 書き換え対象
- `50-infra/cloudflare/workers/atproto/src/auth/well-known-oauth.test.ts` — Phase 1 test 書き換え対象
