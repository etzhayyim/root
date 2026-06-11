---
id: adr-2604240914-oauth-rs-binding-revocation-introspection
title: "ADR: OAuth server lifecycle — RS DPoP nonce + RFC 7009 revocation + RFC 7662 introspection"
status: active
doc_type: adr
topic: auth-lifecycle
authoritative: true
last_verified: 2026-04-24
authoritative_for:
  - /xrpc/* Resource Server 側の DPoP proof + nonce 検証方針
  - OAuth 2.0 token revocation endpoint の採用方針 (RFC 7009)
  - OAuth 2.0 token introspection endpoint の採用方針 (RFC 7662)
  - access_token 短寿命 + 明示 revocation の責務分界
related:
  - adr-2604231821-atproto-oauth-wire-format-snake-case
  - adr-2604231800-atproto-permission-spec-integration
  - adr-2604231811-atproto-extension-service-layers
  - adr-0022-auth-topology-consolidation
supersedes: []
superseded_by: []
---

# Context

ADR-2604231821 Phase 1-3 で OAuth AS (`atproto.etzhayyim.com` + `authn.etzhayyim.com`) の
wire format と token endpoint の DPoP nonce 強制 (RFC 9449 §8) を完了した。
同 ADR が "Phase 5 follow-up" として out-of-scope 化した 3 項目を本 ADR で扱う。

## 現状 (2026-04-24 監査)

| 層 | 実装 | RFC |
|---|---|---|
| AS metadata snake_case | ✅ | RFC 8414 |
| PAR | ✅ `POST /oauth/par`、`request_uri` TTL 90s | RFC 9126 |
| PKCE S256 | ✅ | RFC 7636 |
| token endpoint の DPoP signature verify | ✅ | RFC 9449 §4 |
| **token endpoint の DPoP nonce** | ✅ ADR-2604231821 S4 | RFC 9449 §8 |
| token response `iss` | ✅ | RFC 9207 |
| DPoP proof on `/xrpc/*` (Resource Server) | ⚠️ DPoP header 受理のみ、**proof 検証 / nonce 強制なし** | RFC 9449 §5-8 |
| access_token 失効 | ❌ **revocation endpoint 不在**。900s TTL だけが唯一の失効経路 | RFC 7009 |
| token introspection | ❌ `/oauth/introspect` 不在 | RFC 7662 |

## 問題

### X1. RS 側で DPoP proof-of-possession が担保されていない

`50-infra/cloudflare/workers/atproto/src/auth.ts` の `/xrpc/*` 受付 path は
`Authorization: DPoP <token>` header を受け入れるが、ペアの `DPoP:` header
に入る proof JWT を **署名検証していない**。access_token の `cnf.jkt` に
bound された public key thumbprint と、proof JWT の署名鍵 thumbprint が
一致することを検証しないと、proof-of-possession の保証は名目のみ。

現状は **access_token が漏洩すれば即 compromise** で bearer と変わらない。
token endpoint 側では DPoP binding を正しく issue しているのに、RS 側で
verify していないため DPoP の防御効果がゼロ。

### X2. access_token 失効手段が TTL のみ

ADR-2604231821 S2 で access_token TTL を 900s (15 min) に短縮したが、
漏洩発覚時に即時無効化する経路がない:

- user が sign-out しても access_token は 15 分間有効
- PDS 側の session delete XRPC (`com.atproto.server.deleteSession`) が ある
  が、内部 session JWT の blacklist に追加するだけで、**OAuth access_token は
  触らない**
- 3rd-party client (Bluesky App 等) が access_token を破棄する標準 endpoint が
  ない → RFC 7009 (`/oauth/revoke`) を実装すべき

### X3. 他 Worker から token 状態を確認できない

内部 Worker (yoro Client App / AppView / etzhayyim CLI 経由の Agent tool) が
"この access_token は有効か / どの DID の / どの scope / expired か" を
問い合わせる標準手段がない。現状は JWT を自力 decode して `exp` を見ている
が、revocation status は取れない。

RFC 7662 (`/oauth/introspect`) は confidential client 専用 endpoint で、
access/refresh token の metadata (active / scope / sub / exp / jkt / iss) を
返す。内部 Worker-to-Worker trust で呼び出す形に落とし込めば、revocation
反映 + 分散 session validation が成立する。

# Decision

次の 3 項目を OAuth server lifecycle の完成として同時採用する:

## Y1. RS 側 DPoP proof verification + nonce enforcement

1. `/xrpc/*` 入口 middleware で、`Authorization: DPoP <token>` が付いた request
   について:
   - `DPoP:` header の proof JWT を ES256 署名検証 (既存 `auth/dpop.ts:verifyDpopProof`)
   - access_token の `cnf.jkt` と proof JWK thumbprint の **一致検証 (MUST)**
   - proof JWT の `htm` = request method、`htu` = request URL path 一致検証
   - proof JWT の `jti` 重複検出 (既存 `_checkDpopJti`)
   - **nonce 強制**: `nonce` claim が AS 発行の nonce と一致することを検証
2. nonce 不在 / 不一致時は `401` + `DPoP-Nonce: <fresh>` header + `WWW-Authenticate:
   DPoP error="use_dpop_nonce"` で応答
3. RS は AS と同じ nonce cache (`auth/scope.ts:_dpopNonceCache`) を共有。
   atproto Worker 内なので in-memory Map で足りる。将来 AS/RS 分離時は
   Cloudflare KV or Durable Object に移す
4. Bearer (DPoP なし) は既存挙動維持 — session JWT / API key は引き続き動く。
   DPoP path のみ spec compliant に昇格

## Y2. `/oauth/revoke` endpoint (RFC 7009)

1. atproto.etzhayyim.com に `POST /oauth/revoke` を追加
2. form body: `token` (必須), `token_type_hint` (`access_token` / `refresh_token`, optional)
3. authn Worker に委譲 — access_jwt / refresh_jwt を jti ベースの blacklist
   (`vertex_etzhayyim_key_revoked_session` D1 table, 既存) に追加
4. revoked token の再利用: RS 側 verify で blacklist lookup → `401 invalid_token`
5. spec 要件を満たす応答:
   - 成功: `200` (body なし)
   - 不正 token / unknown: **依然として 200** (RFC 7009 §2.2 — information leak 防止)
   - 不正 request (token 欠落等): `400 invalid_request`
6. DPoP binding された access_token の revocation 時は、対応 refresh_token も
   **同時に revoke** (RFC 7009 §2.1 SHOULD)

## Y3. `/oauth/introspect` endpoint (RFC 7662)

1. atproto.etzhayyim.com に `POST /oauth/introspect` を追加
2. confidential client 専用: `Authorization: Bearer <sk_live_*>` で `etzhayyim`
   internal API key 認証 (ADR-0022 L0)。public client は 403 で reject
3. form body: `token` (必須), `token_type_hint` (optional)
4. response (RFC 7662 §2.2):
   ```json
   {
     "active": true,
     "scope": "atproto transition:generic",
     "client_id": "https://atproto.etzhayyim.com/client-metadata.json",
     "sub": "did:web:alice.etzhayyim.com",
     "exp": 1745702400,
     "iat": 1745701500,
     "iss": "https://atproto.etzhayyim.com",
     "token_type": "DPoP",
     "cnf": { "jkt": "<thumbprint>" }
   }
   ```
5. inactive / expired / revoked / unknown token: `{"active": false}` のみ返す
   (他 field leak 禁止)
6. token revocation (Y2) と同じ blacklist lookup を経由
7. rate limit 必須 — token scanning 防止のため per-client 100/min

## 責務分界

| 層 | 所在 | 呼出元 |
|---|---|---|
| DPoP verify (RS) | atproto Worker middleware (`src/auth.ts`) | 全 `/xrpc/*` |
| revocation blacklist | authn Worker D1 (`vertex_etzhayyim_key_revoked_session`) | atproto `/oauth/revoke`, atproto RS verify |
| introspection | atproto Worker `/oauth/introspect` → authn service binding で token metadata 取得 | 内部 Worker, confidential 3rd party |
| nonce cache | `50-infra/cloudflare/workers/atproto/src/auth/scope.ts:_dpopNonceCache` | atproto AS + RS 共通 |

**禁止**:
- public client (bearer のみ) に introspection を開放する (token scanning)
- revocation endpoint で invalid token に 400 / 404 を返す (active/inactive 漏洩)
- nonce cache を外部に流す

# Work Plan

3 phase。Y1 → Y2 → Y3 の順で、それぞれ grace window 付き。

## Phase A (Y1, 2026-04-26): RS DPoP enforcement

### A1. `/xrpc/*` middleware で DPoP proof verify を追加

- `50-infra/cloudflare/workers/atproto/src/auth.ts` の auth middleware に
  dpop path を追加:
  ```ts
  if (authHeader.startsWith("DPoP ")) {
    const accessToken = authHeader.slice(5);
    const claims = await verifyAtprotoJwt(accessToken, secret, "com.atproto.access");
    const jktFromToken = claims?.cnf?.jkt;
    if (!jktFromToken) return unauthorized("missing cnf.jkt");
    const proof = request.headers.get("DPoP") || "";
    try {
      const { jkt, claims: dpopClaims } = await verifyDpopProof(
        proof, request.method, new URL(request.url).pathname, _checkDpopJti
      );
      if (jkt !== jktFromToken) return unauthorized("dpop jkt mismatch");
      if (!dpopClaims.nonce || !verifyDpopNonce(dpopClaims.nonce)) {
        return useNonce(); // 401 + DPoP-Nonce header
      }
    } catch (e) {
      return invalidDpop(e);
    }
  }
  ```

### A2. `cnf.jkt` claim の issue path

- atproto worker の access_token issue 時 (`authn` via AUTH_SERVICE.createSession)
  の JWT payload に `cnf.jkt` を含める
- authn Worker `session.ts` に `cnf` optional field を追加、token endpoint
  経由の session issue 時に DPoP proof の jkt を forward

### A3. grace window

- 14 日間: `cnf.jkt` 不在 token は warn log のみで通過 (Phase A grace)
- 14 日明け: reject に切替

## Phase B (Y2, 2026-04-29): `/oauth/revoke`

### B1. revocation endpoint

- `POST /oauth/revoke` を atproto Worker に追加
  (`50-infra/cloudflare/workers/atproto/src/handlers/oauth.ts`)
- authn Worker に service binding で委譲:
  - authn に `POST /rpc/revoke-token` を追加 → D1 `vertex_etzhayyim_key_revoked_session`
    に `(jti, revoked_at, token_type, subject_did)` を INSERT
- auth spec 要件: 成功 + unknown token は同じ `200` レスポンス

### B2. RS verify で blacklist lookup

- `50-infra/cloudflare/workers/atproto/src/auth/verify.ts` の access_token
  verify に blacklist check を追加:
  - cached in 60s TTL in-memory Map (atproto Worker 毎に独立)
  - miss 時 authn service binding で D1 query
  - hit 時 `401 invalid_token`

### B3. revocation cascade

- access_token revoke 時は対応 refresh_token も自動 revoke (RFC 7009 §2.1 SHOULD)
- refresh_token revoke 時は全 descendant access_token の blacklist 登録

## Phase C (Y3, 2026-05-02): `/oauth/introspect`

### C1. introspection endpoint

- `POST /oauth/introspect` を atproto Worker に追加
- `Authorization: Bearer sk_live_*` 認証 必須 (ADR-0022 L0 api_key)
  - authn service binding で api_key → confidential flag 判定
  - 非 confidential 時は `403 unauthorized_client`
- JWT decode (既存 `verifyAtprotoJwt`) + blacklist lookup + exp check

### C2. rate limit

- CF Rate Limiting binding or in-memory counter で per-api_key 100/min
- 超過時 `429 Too Many Requests`

### C3. introspection metadata の sanitize

- inactive token: `{"active": false}` のみ
- active token: RFC 7662 §2.2 の最小 field set (`active`, `scope`, `client_id`,
  `sub`, `exp`, `iat`, `iss`, `token_type`, `cnf.jkt`)
- 拡張 field (`aud`, `jti`, `nbf`) は scope 次第で opt-in

## Phase D (2026-05-09): AS metadata 反映

`.well-known/oauth-authorization-server` に:

```json
{
  ...,
  "revocation_endpoint": "https://atproto.etzhayyim.com/oauth/revoke",
  "revocation_endpoint_auth_methods_supported": ["none"],
  "introspection_endpoint": "https://atproto.etzhayyim.com/oauth/introspect",
  "introspection_endpoint_auth_methods_supported": ["private_key_jwt"]
}
```

RFC 8414 §2 準拠。ADR-2604231821 の AS metadata に加えて 4 field 追加。

# Consequences

## Positive

- **DPoP の防御効果が実体化**: access_token 漏洩しても proof-of-possession
  key も盗まないと悪用不能。現状の名目 DPoP は実害 0、本 ADR で spec 準拠
- **15 分未満での失効経路確立**: revocation endpoint により明示失効が可能に。
  sign-out UX / sec incident 対応 / 3rd-party app unlink が機能する
- **分散 session 検証**: introspection で yoro Client App / AppView / 内部
  agent が統一的に token status を問える。JWT 自力 decode + `exp` 観測の
  暫定実装を撤去できる
- **OAuth 2.0 suite の完成**: PAR + PKCE + DPoP + token + revoke + introspect
  の full stack。`@atproto/api` 含む spec-compliant client が全機能を使える

## Negative

- **RS DPoP verify のコスト**: per `/xrpc/*` request に ECDSA verify 1 回
  (~1ms CF Worker)。`cnf.jkt` 比較 + `jti` cache lookup で更に ~0.1ms。
  Bearer flow は不変
- **D1 revocation blacklist の書込負荷**: revoke 呼出頻度は低いが、RS verify の
  lookup 頻度は高い。60s in-memory cache で吸収
- **introspection の security surface 追加**: confidential client しか呼べない
  設計だが、api_key 漏洩時の token scanning リスク。rate limit で緩和
- **`cnf.jkt` claim 追加で JWT size 微増**: ~60 byte 増 (thumbprint + key names)

## Neutral

- ADR-2604231821 で採用した snake_case wire format はそのまま適用。revoke /
  introspect endpoint も全 request/response snake_case
- DPoP nonce cache (`auth/scope.ts:_dpopNonceCache`) は AS token endpoint と RS の
  両方から共有。移行 (KV / Durable Object 化) は別 ADR に送る
- 内部 Worker (authn / yoro / AppView) は Service Auth JWT (ES256) を独自 L1
  layer で使い続ける (ADR-0022 / ADR-0023)。OAuth access_token + RS DPoP は
  **外部 OAuth client 向け面のみ** — 内部面は無改変

# Alternatives Considered

## Z1. Bearer-only に戻し DPoP 廃止

- pros: RS verify 実装不要
- cons: 外部 `@atproto/api` 互換性崩壊、AT Protocol spec 違反、token 漏洩で
  即 compromise。**却下**

## Z2. revocation を実装せず access_token TTL を 60 秒まで短縮

- pros: 失効は TTL で吸収
- cons: 1 分毎に refresh 必須 → refresh_token endpoint 負荷 60x、
  3rd-party app の UX 劣化。PDS が refresh の中継点で常時 hot。**却下**

## Z3. introspection を廃止し JWT 自力 decode を標準化

- pros: 実装不要
- cons: revocation 反映不能、confidential client の "active?" 問い合わせが
  できない、分散 session model が壊れる。**却下**

## Z4. 3 項目を別 ADR に分割

- pros: 小粒度で land
- cons: Y1 + Y2 + Y3 が "OAuth server lifecycle" として同じ root decision を
  共有 (外部 client 向け full stack)。3 別 ADR は relation graph 肥大 + Phase
  dependency の再掲が冗長。ADR Rule "1 decision" を "full lifecycle" 単位で
  解釈した方が実態に近い。**却下** (仮に scope が膨張したら分割は follow-up)

## Z5. token binding を DPoP ではなく mTLS (RFC 8705) で

- pros: Cloudflare Worker ネイティブの Client Certificate 機能利用可
- cons: AT Protocol spec が DPoP 前提、`@atproto/api` は DPoP 実装済み
  mTLS は browser client で扱いづらい。**却下**

# Non-Goals

- 内部 Worker-to-Worker auth (Service Auth JWT L1) の変更 — 対象外
- AT Protocol federation ingress auth (did:plc 外部 PDS からの読み) の RS 側
  改変 — 対象外 (`/xrpc/com.atproto.sync.*` は本 ADR 外)
- Session JWT (HS256) の廃止 — `etzhayyim authn signin` flow は独立
- DPoP nonce の persistence (KV / DO) — in-memory で十分、将来 scale out 時に follow-up
- `authorization_details` (RFC 9396 Rich Authorization Requests) の採用
- FAPI 2.0 profile 全面対応 — 選択的に DPoP binding + PKCE S256 + PAR のみ採用済

# References

## 公式仕様

- [RFC 7009](https://datatracker.ietf.org/doc/html/rfc7009) — OAuth 2.0 Token Revocation
- [RFC 7662](https://datatracker.ietf.org/doc/html/rfc7662) — OAuth 2.0 Token Introspection
- [RFC 9449](https://datatracker.ietf.org/doc/html/rfc9449) — DPoP (§5-8 RS binding)
- [RFC 8414](https://datatracker.ietf.org/doc/html/rfc8414) — AS Metadata (`revocation_endpoint` / `introspection_endpoint`)
- [AT Protocol OAuth spec](https://atproto.com/specs/oauth)

## 関連 ADR

- `90-docs/adr/2604231821-atproto-oauth-wire-format-snake-case.md` — snake_case wire format + AS-side DPoP nonce (本 ADR の前段)
- `90-docs/adr/2604231800-atproto-permission-spec-integration.md` — permission spec 準拠
- `90-docs/adr/2604231811-atproto-extension-service-layers.md` — 15-layer taxonomy
- `90-docs/adr/0022-auth-topology-consolidation.md` — 2-token model (api_key / session JWT)
- `90-docs/adr/0023-auth-shannon-optimal-4-layer.md` — L0 API key / L1 ES256 JWT / L2 authority / L3 signal

## 実装 citations

- `50-infra/cloudflare/workers/atproto/src/auth.ts` — RS 入口 auth middleware (Y1 作業対象)
- `50-infra/cloudflare/workers/atproto/src/auth/verify.ts` — access_token verify (Y2 blacklist lookup 対象)
- `50-infra/cloudflare/workers/atproto/src/auth/dpop.ts` — DPoP verify (既存)
- `50-infra/cloudflare/workers/atproto/src/auth/scope.ts` — `_dpopNonceCache` (AS/RS 共用)
- `50-infra/cloudflare/workers/atproto/src/handlers/oauth.ts` — Y2 / Y3 endpoint 追加対象
- `60-apps/etzhayyim-project-auth/worker/src-ts/session.ts` — `cnf` claim issue (Y1 A2)
- `60-apps/etzhayyim-project-auth/worker/src-ts/index.ts` — `/rpc/revoke-token` 追加 (Y2 B1)
