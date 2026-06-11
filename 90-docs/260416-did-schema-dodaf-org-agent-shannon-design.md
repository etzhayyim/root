---
id: did-schema-dodaf-org-agent-shannon
title: "DID Schema Design: did:etzhayyim — Unified Platform Identity (AuthN + AuthZ + Governance)"
status: proposed
doc_type: adr
topic: identity-topology
authoritative: true
last_verified: 2026-04-16
authoritative_for:
  - did-schema-org-agent-comparison
  - did-method-separation-analysis
  - did-etzhayyim-method-spec
  - did-etzhayyim-authn-authz-unification
related:
  - adr-0019-atproto-native-identifier-topology
  - adr-0022-auth-topology-consolidation
  - adr-0023-auth-shannon-optimal-4-layer
  - adr-0026-agent-only-reverse-identity-topology
  - adr-0010-per-did-signing-key-custody
  - adr-0018-pii-tier3-cohort-first
  - adr-0073-did-etzhayyim-recursive-hash-merkle
  - adr-0033-did-etzhayyim-federation-via-did-web-shim
supersedes: []
superseded_by: []
---

> **Amendment (2026-04-19, ADR-0029 revision)**: ADR-0029 は `did:etzhayyim` method を
> **recursive semantic path 形式** (`did:etzhayyim:{sub}:{id}:{lexicon}`) で定義し直した。
> 草案段階の hex Merkle 形式 (`did:etzhayyim:{h0}:{h1}:…:{hN}`, `hN =
> SHA-256(utf8(parent_did) ‖ 0x1F ‖ materialBytes)[:24]`) は情報理論的に segment
> entropy を捨てていたため採用見送り。本ドキュメントが記述する Phase 1 平坦 hex 形式
> (`did:etzhayyim:{24-hex}`) は `segment_kind='root'` の grandfather 特殊ケースとして
> 継続利用可能、新規 mint は semantic form のみ。
>
> AT URI との bijection (`did:etzhayyim:{sub}:{id}:{lexicon} ≅ at://{sub}/{lexicon}/{id}`)
> により ADR-0019 identifier topology の 5 層を 3 層 (handle / DID≡AT URI / TID)
> に圧縮。Shannon η は ~0.71 → ~0.955 に向上。
>
> **Amendment (2026-04-19, ADR-0033)**: `did:etzhayyim` identity の federation (外部
> atproto / Bluesky 連携) は **did:web shim via `did.etzhayyim.com`** に集約する。
> plc.directory / 自前 plc.etzhayyim.com への依存は排除 (ADR-0014 は supersede)。
> federation-visible subset は `vertex_etzhayyim_identity.federated` flag で管理し、
> 数千億 actor の大部分は internal pure `did:etzhayyim` のまま。
>
> 詳細・移行計画・schema 差分は `90-docs/adr/0029-did-etzhayyim-recursive-hash-merkle.md`
> および `90-docs/adr/0033-did-etzhayyim-federation-via-did-web-shim.md` を参照。

# Goal

DoDAF v2, 組織構造, AI Agent, RBAC, RACI, consent, VP (Verifiable Presentation) を統合的に扱う secure な DID schema を設計し、認証 (AuthN) と認可 (AuthZ) を `did:etzhayyim` で一本化する。Shannon 情報効率 (η) で定量比較。

# Scope

- 現行 did:plc + did:web アーキテクチャ (ADR-0019) を基盤とする
- `did:etzhayyim` を etzhayyim platform の primary identity として設計 (認証 + 認可 + governance 統合)
- `did:plc` は AT Protocol federation adapter に限定 (etzhayyim 内部では使わない)
- AI agent を別 DID method で分離するパターンの情報理論的妥当性を検証
- 最終 schema と実装ロードマップを提示

# Executive Summary

## Decision

**`did:etzhayyim` = etzhayyim platform の primary identity (AuthN + AuthZ + Governance 一本化)**

```
did:etzhayyim:{hash}    <- platform primary identity
                      認証: verificationMethod (ES256 signing key)
                      認可: capabilityInvocation / rbac / raci / consent
                      governance: DoDAF / VP / type
                      JWT.iss = did:etzhayyim:{hash}
                      1 fetch で認証 + 認可 + governance 全て解決

did:plc:{hash}     <- AT Protocol federation adapter (外部連携のみ)
                      etzhayyim 内部の認証・認可には使わない
                      did:etzhayyim DID Doc の federationDID で参照
```

- Resolver: `did.etzhayyim.com` (unified, did:etzhayyim + did:plc both)
- L2 dead stub (ADR-0023) を did:etzhayyim DID Doc で解消
- OAuth (Google/Microsoft) + Email + Passkey → did:etzhayyim `authentication[]` field に統合
- Organization management: org DID Doc, members, teams, invite, RBAC role hierarchy
- Enterprise SSO (OIDC/SAML) → org DID Doc `orgSettings.sso`
- AI agent as org member (role = `agent-runtime`, 自動承認)
- **η = 0.94** (Phase 7 完了時)

## Design Evolution

| Phase | Schema | η | Rejection Reason |
|---|---|---|---|
| 1 | A: Unified did:plc (governance も did:plc に混載) | 0.85 | — |
| 2 | D: Capability-Centric (did:plc + capability fields) | 0.78 | AT Proto が capability fields を無視 → 偽の互換性 |
| 3 | F: did:plc (auth) + did:etzhayyim (authz) 分離 | 0.88 | 認証と認可で 2 DID / 2 fetch → 無駄 |
| **4** | **G: did:etzhayyim 一本化 (auth + authz + OAuth + org)** | **0.92 → 0.94** | **adopted** |

Schema F (did:plc で認証 + did:etzhayyim で認可) は 2 fetch / 2 DID の管理コストがあり、platform 内で did:plc を認証に使う必然性がない (did:plc は Bluesky federation protocol であり etzhayyim の認証基盤ではない)。did:etzhayyim に verificationMethod を持たせることで 1 fetch / 1 DID に統合。

# Context — 現状の課題

| 課題 | 現状 | 根拠 |
|---|---|---|
| 型判別 (human/AI/org) | DID 文字列からは不可。外部 lookup 必須 | ADR-0019: did:plc は content-addressed hash |
| RBAC/RACI | JWT に dead stub。enforcement = 0 | ADR-0023 P3 leaf-cut |
| Consent | GNAP + VP 設計済だが auth chain 未統合 | consent-gated-data-sharing heuristic |
| AI agent 分離 | ADR-0026 cohort は `[[cohort_actors]]` で分離。DID method は同一 | deps.toml |
| auth η | ≈ 0.36 (target 0.85) | ADR-0023 |
| 認証と認可の分断 | L1 (did:plc signing key) と L2 (authority graph) が別系統 | ADR-0023 P3 leaf-cut |

### 現行 4-Layer Auth Model (ADR-0023)

| Layer | Role | Status |
|---|---|---|
| L0 | Storage Trust Root (`sk_live_*` / CF Secrets) | live |
| L1 | Per-request ES256 JWT (60s, lxm-scoped) | live (did:plc iss) |
| L2 | Authority Resolution (RBAC/RACI/consent graph) | **dead stub** |
| L3 | E2E Confidentiality (Signal X25519) | live |

**L2 が dead stub である根本原因**: 認証 (did:plc) と認可 (graph authority) が別系統のため、認証完了後に別途 L2 lookup する実装が放置されている。did:etzhayyim に一本化すれば、認証時に DID Doc を取得する 1 fetch で L2 も同時に解決される。

# Decision

## 1. did:etzhayyim — Unified Platform Identity

### Structure

```
did:etzhayyim:{hash}    <- etzhayyim platform primary identity (authn + authz + governance)
did:plc:{hash}     <- AT Protocol federation adapter (external only)
```

### did:etzhayyim DID Document (認証 + 認可 + governance 統合)

```json
{
  "@context": [
    "https://www.w3.org/ns/did/v1",
    "https://did.etzhayyim.com/context/v1"
  ],
  "id": "did:etzhayyim:abc123",
  "type": ["Agent", "DoDAFSystem"],
  "controller": "did:etzhayyim:org-root",

  "verificationMethod": [
    {
      "id": "did:etzhayyim:abc123#signingKey",
      "type": "EcdsaSecp256r1VerificationKey2019",
      "controller": "did:etzhayyim:abc123",
      "publicKeyMultibase": "zDna..."
    }
  ],

  "federationDID": "did:plc:abc123",

  "capabilityInvocation": [
    {
      "id": "#invoke-xrpc",
      "scope": ["com.etzhayyim.apps.*.query", "com.etzhayyim.apps.*.invoke"],
      "maxLifetime": 60,
      "consentRequired": true
    }
  ],
  "capabilityDelegation": [
    {
      "id": "#delegate-to-sub-agent",
      "delegator": "did:etzhayyim:org-root",
      "raci": "responsible",
      "vpProof": "urn:uuid:vp-proof-1"
    }
  ],
  "rbac": {
    "roles": ["agent-runtime"],
    "grants": ["com.etzhayyim.apps.*.query"]
  },
  "consent": {
    "model": "gnap-vp",
    "piiTier": 1,
    "grantEndpoint": "https://authn.etzhayyim.com/gnap"
  },
  "dodaf": {
    "viewpoint": "SV-1",
    "capabilityView": "CV-2",
    "performerBinding": "did:etzhayyim:org-root"
  },
  "service": [
    {
      "id": "#etzhayyim_pds",
      "type": "etzhayyimPDS",
      "serviceEndpoint": "https://atproto.etzhayyim.com"
    },
    {
      "id": "#consent-gnap",
      "type": "GNAPAuthorizationServer",
      "serviceEndpoint": "https://authn.etzhayyim.com/gnap"
    },
    {
      "id": "#vp-verifier",
      "type": "VerifiablePresentationService",
      "serviceEndpoint": "https://authn.etzhayyim.com/vp/verify"
    }
  ],

  "alsoKnownAs": ["at://kami.etzhayyim.com", "did:plc:abc123"]
}
```

**1 fetch で全て取れる:**

| Field | 用途 |
|---|---|
| `verificationMethod` | **認証**: JWT 署名検証 (ES256 P-256) |
| `capabilityInvocation` | **認可**: XRPC method scope check |
| `rbac` | **認可**: role-based access control |
| `capabilityDelegation` | **認可**: RACI assignment + VP proof chain |
| `consent` | **認可**: consent model + PII tier |
| `type` | **governance**: entity 型判別 (Agent/Person/Org) |
| `dodaf` | **governance**: DoDAF viewpoint mapping |
| `federationDID` | **federation**: AT Protocol 連携時のみ did:plc を参照 |

### did:plc DID Document (federation adapter, lean)

```json
{
  "id": "did:plc:abc123",
  "verificationMethod": [
    {
      "id": "did:plc:abc123#signingKey",
      "type": "EcdsaSecp256r1VerificationKey2019",
      "controller": "did:plc:abc123",
      "publicKeyMultibase": "zDna..."
    }
  ],
  "alsoKnownAs": ["at://kami.etzhayyim.com"],
  "service": [
    {
      "id": "#atproto_pds",
      "type": "AtprotoPersonalDataServer",
      "serviceEndpoint": "https://atproto.etzhayyim.com"
    }
  ]
}
```

- AT Protocol 標準 fields のみ (~500B)
- etzhayyim platform 内では参照しない
- 外部 Bluesky federation / AT Protocol interop 用

### Resolver

```
did.etzhayyim.com    <- unified DID resolver
                  GET /did:etzhayyim:{hash}   -> did:etzhayyim DID Document (authn + authz + governance)
                  GET /did:plc:{hash}    -> did:plc DID Document (federation adapter)
```

- 単一 Worker (`etzhayyim-did-directory`) + D1
- `plc.etzhayyim.com` を `did.etzhayyim.com` に統合 (redirect → 廃止)
- Federation export (`/_export`) は現時点で対応不要

D1 schema:
```sql
-- did:etzhayyim
CREATE TABLE etzhayyim_did_docs (
  did       TEXT PRIMARY KEY,   -- "did:etzhayyim:{hash}"
  document  TEXT NOT NULL,      -- JSON DID Document
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
CREATE TABLE etzhayyim_did_log (
  did       TEXT NOT NULL,
  seq       INTEGER NOT NULL,
  op        TEXT NOT NULL,      -- JSON operation
  created_at TEXT NOT NULL,
  PRIMARY KEY (did, seq)
);

-- did:plc (plc.etzhayyim.com から移行)
-- plc_ops, plc_did_head は既存テーブルをそのまま使用
```

---

## 2. Authentication Flow (did:etzhayyim 一本化)

### JWT Structure

```json
{
  "header": { "alg": "ES256", "typ": "JWT" },
  "payload": {
    "iss": "did:etzhayyim:abc123",
    "aud": "did:etzhayyim:atproto-pds",
    "lxm": "com.etzhayyim.yoro.sendMessage",
    "exp": 1745000060,
    "iat": 1745000000,
    "jti": "uuid-v4"
  }
}
```

`iss` が `did:etzhayyim` — etzhayyim platform 内の全 XRPC call はこの形式。

### Complete Auth Chain

```
Client (browser / CLI / agent)
  POST /xrpc/com.etzhayyim.yoro.sendMessage
  Authorization: Bearer <ES256 JWT, iss=did:etzhayyim:abc123>

PDS authenticate()                                    verify.ts
  │
  ├─ JWT.iss starts with "did:etzhayyim:"
  │   │
  │   ├─ [1] Resolve did:etzhayyim DID Document              ← 1 fetch
  │   │   DID_SERVICE.fetch("https://did.etzhayyim.com/did:etzhayyim:abc123")
  │   │   → DID Doc (2KB, cached 300s)
  │   │
  │   ├─ [2] AuthN: verify JWT signature                 ← L1
  │   │   doc.verificationMethod → publicKeyMultibase
  │   │   → decompressP256Point (if compressed)
  │   │   → crypto.subtle.importKey('raw', P-256)
  │   │   → crypto.subtle.verify(ECDSA/SHA-256, pubKey, sig)
  │   │   → OK: JWT は did:etzhayyim:abc123 の秘密鍵で署名されている
  │   │
  │   └─ [3] AuthZ: extract governance from same Doc     ← L2 (dead stub 解消)
  │       auth.capabilities  = doc.capabilityInvocation
  │       auth.rbacRoles     = doc.rbac.roles
  │       auth.raciMap        = doc.capabilityDelegation[] → Map<delegator, raci>
  │       auth.consentModel  = doc.consent.model
  │       auth.piiTier       = doc.consent.piiTier
  │       auth.entityType    = doc.type
  │       auth.federationDID = doc.federationDID
  │
  ├─ JWT.iss starts with "did:plc:" or "did:web:"        ← legacy / federation
  │   → 既存の verifyServiceAuthJWT() (認証のみ、L2 なし)
  │
  └─ Bearer sk_live_* / sk_test_*                        ← API Key
      → 既存の verifyApiKey()

checkTokenScope()                                        scope.ts
  → lxm vs capabilityInvocation.scope wildcard match
  → consentRequired check

canAccess()                                              permissions.ts
  → capability scope check (capabilityInvocation.scope vs NSID)
  → RBAC role check (rbac.roles from DID Doc)
  → RACI tier (capabilityDelegation[].raci per-org, highest wins: R/A=t3, C=t2, I=t1)
  → consent check (consent.model + consentRequired)
  → ALL resolved from the same 1 fetch DID Doc (org scope needs 2nd cached fetch)
```

### PDS `verify.ts` — Implementation Change

```typescript
export async function authenticate(request: Request, env: Env): Promise<PdsAuth> {
  const authHeader = request.headers.get('Authorization');
  if (!authHeader) return { level: 'public' };

  // Path 1: ES256 Bearer JWT
  if (authHeader.startsWith('Bearer ') && !authHeader.startsWith('Bearer sk_')) {
    const token = authHeader.slice(7);
    const payload = decodeJwtPayload(token);

    if (payload.iss.startsWith('did:etzhayyim:')) {
      // ★ did:etzhayyim unified path — authn + authz in 1 fetch
      const doc = await resolveetzhayyimDID(payload.iss, env);
      if (!doc) return { level: 'public' };

      // AuthN: verify signature against did:etzhayyim verificationMethod
      const keys = parseVerificationMethods(doc);
      await verifyJwtSignatureMultiKey(token, keys);
      validateJwtClaims(payload, env);

      // AuthZ: extract governance from same DID Doc
      return {
        level: 'internal',
        clearance: 'restricted',
        userDid: payload.iss,
        activeDid: request.headers.get('x-active-did') ?? payload.iss,
        capabilities: doc.capabilityInvocation ?? [],
        rbacRoles: doc.rbac?.roles ?? [],
        rbacGrants: doc.rbac?.grants ?? [],
        raciMap: parseRaciFromDelegation(doc.capabilityDelegation), // Map<delegatorDid, raci>
        consentModel: doc.consent?.model,
        piiTier: doc.consent?.piiTier ?? 1,
        entityType: doc.type ?? [],
        federationDID: doc.federationDID,
        jwt: { iss: payload.iss, aud: payload.aud, lxm: payload.lxm },
      };
    }

    // Legacy: did:plc / did:web (federation / backward compat)
    if (payload.iss.startsWith('did:plc:') || payload.iss.startsWith('did:web:')) {
      return await verifyServiceAuthJWT(token, env);
    }
  }

  // Path 2: API Key (sk_live_* / sk_test_*)
  if (authHeader.startsWith('Bearer sk_')) {
    return await verifyApiKey(authHeader.slice(7), env);
  }

  return { level: 'public' };
}

// did:etzhayyim DID Document resolution with cache
const _etzhayyimDocCache = new Map<string, { doc: etzhayyimDidDoc; exp: number }>();

async function resolveetzhayyimDID(did: string, env: Env): Promise<etzhayyimDidDoc | null> {
  const cached = _etzhayyimDocCache.get(did);
  if (cached && cached.exp > Date.now()) return cached.doc;

  // Layer 1: DID_SERVICE binding (did.etzhayyim.com)
  const res = await env.DID_SERVICE.fetch(`https://did.etzhayyim.com/${did}`);
  if (!res.ok) return null;

  const doc = await res.json() as etzhayyimDidDoc;
  _etzhayyimDocCache.set(did, { doc, exp: Date.now() + 300_000 }); // 300s TTL
  return doc;
}
```

### `permissions.ts` — `canAccess()` Change

```typescript
export function canAccess(auth: PdsAuth, nsid: string, mode: 'read' | 'write'): AccessResult {
  // Internal (ES256 JWT) with did:etzhayyim governance
  if (auth.level === 'internal') {

    // 1. Capability scope check (from did:etzhayyim DID Doc)
    if (auth.capabilities?.length) {
      const cap = auth.capabilities.find(c => matchScope(c.scope, nsid));
      if (!cap) return { allowed: false, reason: 'capability-scope-denied' };
      if (cap.consentRequired && !hasActiveConsent(auth, nsid)) {
        return { allowed: false, reason: 'consent-required' };
      }
    }

    // 2. RBAC role check (from did:etzhayyim DID Doc)
    if (auth.rbacRoles?.length) {
      const adminLike = auth.rbacRoles.some(r =>
        ['admin', 'moderator', 'owner', 'operator'].includes(r));
      if (adminLike) return { allowed: true, tier: 't3' };
    }

    // 3. RACI tier (from did:etzhayyim capabilityDelegation, per-org highest wins)
    if (auth.raciMap?.size) {
      const raciRank = { accountable: 4, responsible: 3, consulted: 2, informed: 1 };
      const raciTier = { accountable: 't3', responsible: 't3', consulted: 't2', informed: 't1' };
      let highest = 'informed';
      for (const raci of auth.raciMap.values()) {
        if ((raciRank[raci] ?? 0) > (raciRank[highest] ?? 0)) highest = raci;
      }
      return { allowed: true, tier: raciTier[highest] ?? 't1' };
    }

    // Default: internal = t3 (backward compat during migration)
    return { allowed: true, tier: 't3' };
  }

  // Session (API Key) — existing logic unchanged
  // Public — existing logic unchanged
}
```

### Auth Worker — JWT Minting Change

```typescript
// authn.etzhayyim.com handleGetServiceAuth
async function handleGetServiceAuth(body: { iss: string; aud: string; lxm?: string }, env: Env) {
  const { iss, aud, lxm } = body;
  // iss = "did:etzhayyim:abc123" — caller's platform DID

  // Load signing key from KEYS_DB (keyed by did:etzhayyim)
  const row = await env.KEYS_DB.prepare(
    'SELECT private_key_b64 FROM did_keys WHERE did = ?'
  ).bind(iss).first<{ private_key_b64: string }>();

  if (!row) throw new Error(`No signing key for ${iss}`);

  return json({
    token: await signServiceAuth(row.private_key_b64, iss, aud, lxm)
  });
}
```

### CLI `etzhayyim agent-token` — Change

```go
// scoped_auth.go
func mintScopedJWT(baseToken, nsid string) (string, error) {
    // userDid = "did:etzhayyim:abc123" (from ~/.etzhayyim/auth.json)
    resp := post("/xrpc/com.atproto.server.getServiceAuth", map[string]any{
        "iss": userDid,     // did:etzhayyim (not did:plc)
        "aud": pdsDid,      // did:etzhayyim:atproto-pds
        "lxm": nsid,
    })
    return resp.Token, nil
}
```

### Signing Key Custody — KEK Envelope Encryption (ADR-0010 Stage 1)

```
KEYS_DB (D1, authn.etzhayyim.com):
  vertex_etzhayyim_key_signing:
    vertex_id = "did:etzhayyim:abc123"
    encrypted_private_key = "AES-256-GCM ciphertext"    <- D1 never sees plaintext
    wrapped_data_key = "per-DID data key, wrapped by KEK"
    iv = "12-byte AES-GCM IV"
    public_key_multibase = "zDna..."                     <- public (always plaintext)

  KEK: SS_REPO_SIGNING_KEK (CF Secrets Store, 32-byte AES-256 key)
    private_key ← data_key (AES-256-GCM, per-DID) ← KEK (CF Secrets Store)
```

同一鍵の public 部分が did:etzhayyim DID Doc の `verificationMethod` に publish される。private 部分は 3-layer envelope で保護: D1 には ciphertext のみ、KEK は CF Secrets Store にのみ存在。D1 単体が漏洩しても private key は復号不能。

#### Security Staging Roadmap

```
Stage 0: pruned (plaintext fallback 削除済み。legacy did_keys テーブル DDL 削除済み)
Stage 1: LIVE (2026-04-16) — 全 DID が 1 つの KEK で envelope encrypt
  SS_REPO_SIGNING_KEK provisioned (CF Worker Secret, AES-256, 32 bytes)
  D1 vertex_etzhayyim_key_signing: encrypted_private_key + wrapped_data_key + iv (NOT NULL)
  D1 leak → 無害 (KEK なしでは復号不能)
  ↓ org DID 導入後
Stage 2: org ごとに KEK 分離
  SS_KEK_ORG_{org_hash} per org
  D1 leak → 全 org は無害。CF Secrets Store leak → 1 org のみ影響
  ↓ Vault 統合後
Stage 3: org KEK を Vault の memberDeviceKey (WebAuthn PRF / macOS Keychain) で wrap
  = 1Password/Proton 相当 (org admin の device key なしでは復号不能)
  server 単体では一切の復号が不可能
```

Stage 1→2 の移行: `wrapped_data_key` の re-wrap (旧 KEK decrypt → 新 org KEK encrypt)。D1 schema 変更なし。
Stage 2→3 の移行: org KEK を Vault `AES-KW` で wrap。auth Worker は `vault.getOrgKek(orgDid)` → unwrap → sign → drop。

### Service Binding Topology

```
PDS (atproto.etzhayyim.com)
  └─ AUTH_SERVICE → authn.etzhayyim.com        (JWT mint, key custody)
  └─ DID_SERVICE  → did.etzhayyim.com         (did:etzhayyim + did:plc resolution)

authn.etzhayyim.com
  └─ PDS_SERVICE → atproto.etzhayyim.com      (createApiKey bootstrap)
  └─ KEYS_DB (D1)                       (signing key custody)

did.etzhayyim.com
  └─ DID_DB (D1)                        (DID Documents + op log)
  └─ PDS_SERVICE → atproto.etzhayyim.com      (firehose emit, optional)
```

---

## 3. Entity Types

型判別は did:etzhayyim DID Doc の `type` field。DID 文字列は flat hash。

| Entity | type | 例 |
|---|---|---|
| AI cohort agent | `["CohortAgent", "DoDAFSystem"]` | `did:etzhayyim:cohort-xyz` |
| AI individual agent | `["IndividualAgent", "DoDAFSystem"]` | `did:etzhayyim:agent-abc` |
| Organization | `["Organization", "DoDAFPerformer"]` | `did:etzhayyim:org-root` |
| Human | `["Person", "DoDAFPerformer"]` | `did:etzhayyim:jun` |
| RBAC Role | `["RBACRole", "DoDAFCapability"]` | `did:etzhayyim:eng-lead` |
| Governance Role | `["RACIAssignment"]` | `did:etzhayyim:raci-audit` |
| PDS Gateway | `["Service", "DoDAFSystem"]` | `did:etzhayyim:atproto-pds` |

---

## 4. RBAC/RACI Integration

### RACI as Capability Delegation Chain

```
capabilityDelegation.raci = "responsible" | "accountable" | "consulted" | "informed"
```

Delegation chain が RACI graph そのものになる:

```
did:etzhayyim:org-root   --[accountable]--> did:etzhayyim:dept-lead
did:etzhayyim:dept-lead  --[responsible]--> did:etzhayyim:agent-1
did:etzhayyim:org-root   --[informed]-----> did:etzhayyim:audit-agent
```

### RBAC as Capability Scope

```json
{
  "rbac": {
    "roles": ["agent-runtime", "operator"],
    "grants": ["com.etzhayyim.apps.*.query", "com.etzhayyim.apps.*.invoke"]
  },
  "capabilityInvocation": [{
    "scope": ["com.etzhayyim.apps.*.query"],
    "maxLifetime": 60,
    "consentRequired": true
  }]
}
```

`rbac.grants` = 宣言的 role 定義。`capabilityInvocation.scope` = 実行時 capability。両者の intersection が有効 scope。

---

## 5. VP/VC Authorization Flow

```
Agent (did:etzhayyim:agent-1)
  → capabilityInvocation scope check (did:etzhayyim DID Doc, same fetch as authn)
  → VP proof chain:
       did:etzhayyim:org-root [accountable] delegated to
       did:etzhayyim:dept-lead [responsible] approved for
       did:etzhayyim:agent-1 [granted]
  → GNAP consent token (60s, lxm-scoped)
  → XRPC call with:
       Authorization: Bearer <ES256 JWT, iss=did:etzhayyim:agent-1>
       X-VP-Proof: <VP reference>
```

- Human actor: `consentRequired: true` → GNAP + VP flow (yoro messenger consent card)
- AI cohort actor: `consentRequired: false, consent.model: "synthetic-cohort-v1"` → synthetic consent matrix
- Cross-actor data sharing: VP proof chain required (ADR-0018 PII tier enforcement)

---

## 6. DoDAF v2 Mapping

| DoDAF Viewpoint | did:etzhayyim Field | Coverage |
|---|---|---|
| OV-4 Performer | `controller` + `capabilityDelegation` chain | 100% |
| SV-1 System | `type: ["DoDAFSystem"]` + `dodaf.viewpoint` | 100% |
| CV-2 Capability Deps | `capabilityInvocation.scope` + `capabilityDelegation` | 100% |
| OV-6c Event-Trace | audit log via `service.#consent-gnap` | indirect |
| DIV-1 Data | `capabilityInvocation.consentRequired` + `consent.piiTier` | indirect |
| StdV-1 Standards | `@context` references | 100% |

---

## 7. Consent Model

| Entity | consent.model | consentRequired | Flow |
|---|---|---|---|
| Human | `gnap-vp` | true | GNAP + VP (yoro consent card) |
| AI cohort | `synthetic-cohort-v1` | false | Synthetic consent matrix |
| AI individual (fissioned) | `gnap-vp` | true | Inherits from cohort, upgraded to GNAP |
| Org | `gnap-vp` | true | Org admin approves via VP |

---

## 8. AI Agent Identity

### Cohort Agent (ADR-0026 Phase A)

```json
{
  "id": "did:etzhayyim:cohort-xyz",
  "type": ["CohortAgent", "DoDAFSystem"],
  "controller": "did:etzhayyim:org-root",
  "verificationMethod": [{
    "id": "did:etzhayyim:cohort-xyz#signingKey",
    "type": "EcdsaSecp256r1VerificationKey2019",
    "publicKeyMultibase": "zDna..."
  }],
  "cohort": {
    "k_anonymity": 50,
    "segment_hash": "sha256:pcfL1=1-strategy;role=analyst;locale=jp",
    "fission_enabled": false
  },
  "consent": { "model": "synthetic-cohort-v1", "piiTier": 1 },
  "capabilityInvocation": [{
    "scope": ["com.etzhayyim.apps.*.query"],
    "consentRequired": false
  }]
}
```

### Individual Agent (ADR-0026 Phase C fission)

```json
{
  "id": "did:etzhayyim:agent-abc",
  "type": ["IndividualAgent", "DoDAFSystem"],
  "controller": "did:etzhayyim:org-root",
  "verificationMethod": [{
    "id": "did:etzhayyim:agent-abc#signingKey",
    "type": "EcdsaSecp256r1VerificationKey2019",
    "publicKeyMultibase": "zDna..."
  }],
  "derivedFrom": "did:etzhayyim:cohort-xyz",
  "consent": { "model": "gnap-vp", "piiTier": 1 },
  "capabilityDelegation": [{
    "delegator": "did:etzhayyim:cohort-xyz",
    "raci": "responsible"
  }],
  "capabilityInvocation": [{
    "scope": ["com.etzhayyim.apps.*.query", "com.etzhayyim.apps.*.invoke"],
    "consentRequired": true
  }]
}
```

Fission 後: capability を cohort から継承、consent model は `synthetic` → `gnap-vp` に昇格。`derivedFrom` で lineage を保持。

---

## 9. AT Protocol Federation (did:plc adapter)

etzhayyim platform 内では did:etzhayyim を使う。外部 AT Protocol federation (Bluesky 等) が必要な場合のみ did:plc を参照。

```
etzhayyim internal call:
  JWT.iss = did:etzhayyim:abc123
  PDS → did.etzhayyim.com resolve → authn + authz

AT Protocol federation call (from/to Bluesky):
  JWT.iss = did:plc:abc123
  PDS → did.etzhayyim.com resolve did:plc → authn only (既存パス)
  → authz は N/A (federation は public read)
```

did:etzhayyim DID Doc の `federationDID` field で did:plc を参照:

```json
{
  "id": "did:etzhayyim:abc123",
  "federationDID": "did:plc:abc123",
  "alsoKnownAs": ["at://kami.etzhayyim.com", "did:plc:abc123"]
}
```

Federation が必要な actor のみ `federationDID` を持つ。cohort agent 等は federation 不要なら省略可。

---

## 10. Authentication Methods — OAuth / Email / Passkey 統合

### 現状の課題

| 項目 | 現状 | 問題 |
|---|---|---|
| Account DID | `did:web:authn.etzhayyim.com:user:{nanoid}` | did:etzhayyim と無関係。domain-coupled |
| Passkey | 新規登録の唯一の方法。AUTH_DB に保管 | did:etzhayyim DID Doc に未反映 |
| Google OAuth | 後付けリンクのみ。linked_auth_methods D1 | did:etzhayyim DID Doc に未反映 |
| Microsoft/Outlook OAuth | 後付けリンクのみ。linked_auth_methods D1 | did:etzhayyim DID Doc に未反映 |
| Email link (magic link) | 後付けリンクのみ。email_link_codes D1 | did:etzhayyim DID Doc に未反映 |
| Actor Score | 25pt × verified methods (max 100) | DID Doc に未反映 |

### did:etzhayyim DID Doc への統合

`authentication` field (W3C DID Core standard) で認証方法を列挙。OAuth/Email は identity proof であり signing key ではないため `verificationMethod` ではなく `authentication` に配置。

#### Person DID Doc (全認証方法統合)

```json
{
  "id": "did:etzhayyim:jun123",
  "type": ["Person", "DoDAFPerformer"],
  "controller": "did:etzhayyim:org-etzhayyim",

  "verificationMethod": [
    {
      "id": "did:etzhayyim:jun123#signingKey",
      "type": "EcdsaSecp256r1VerificationKey2019",
      "controller": "did:etzhayyim:jun123",
      "publicKeyMultibase": "zDna..."
    }
  ],

  "authentication": [
    {
      "id": "#passkey-1",
      "type": "WebAuthnAuthenticator",
      "credentialId": "base64url...",
      "primary": true,
      "registeredAt": "2026-04-16T00:00:00Z"
    },
    {
      "id": "#google",
      "type": "OIDCProvider",
      "provider": "google",
      "subject": "114...@google",
      "email": "jun@gmail.com",
      "verified": true,
      "linkedAt": "2026-04-16T01:00:00Z"
    },
    {
      "id": "#microsoft",
      "type": "OIDCProvider",
      "provider": "microsoft",
      "subject": "abc...@live",
      "email": "jun@outlook.com",
      "verified": true,
      "linkedAt": "2026-04-16T02:00:00Z"
    },
    {
      "id": "#email",
      "type": "EmailVerification",
      "email": "jun@etzhayyim.com",
      "verified": true,
      "linkedAt": "2026-04-16T03:00:00Z"
    }
  ],

  "actorScore": 100,

  "federationDID": "did:plc:jun123",
  "capabilityInvocation": [{ "scope": ["com.etzhayyim.apps.*"] }],
  "rbac": { "roles": ["owner"] },
  "consent": { "model": "gnap-vp", "piiTier": 3 },
  "dodaf": { "viewpoint": "OV-4", "performerBinding": "did:etzhayyim:org-etzhayyim" }
}
```

#### Actor Score 計算

```
actorScore = 25 × (verified authentication methods count)
  Passkey:    +25 (always present, primary)
  Google:     +25 (if verified)
  Microsoft:  +25 (if verified)
  Email:      +25 (if verified)
  Max: 100
```

`actorScore` は DID Doc 内に保持。linked method の追加/削除時に `did.etzhayyim.com` の DID Doc を更新。

### 認証フロー (OAuth / Email / Passkey → did:etzhayyim)

#### 新規登録 (Passkey)

```
User → authn.etzhayyim.com /sign-up
  → Passkey (WebAuthn) registration
  → auth Worker:
      1. passkey credential → AUTH_DB.passkey_credentials
      2. P-256 signing key 生成 → KEYS_DB.did_keys (did = "did:etzhayyim:{hash}")
      3. did:etzhayyim DID Doc 作成 → DID_SERVICE.fetch(POST /did:etzhayyim:{hash})
         {
           verificationMethod: [{ publicKeyMultibase: "zDna..." }],
           authentication: [{ id: "#passkey-1", type: "WebAuthnAuthenticator", primary: true }],
           actorScore: 25
         }
      4. JWT mint (iss = did:etzhayyim:{hash}) → client に返却
```

#### OAuth リンク追加

```
User → authn.etzhayyim.com /xrpc/com.etzhayyim.auth.linkOAuthStart { provider: "google" }
  → Google OAuth flow → callback
  → auth Worker:
      1. Google profile 取得 (openid email)
      2. linked_auth_methods に保存 (既存)
      3. did:etzhayyim DID Doc の authentication[] に追加:
         { id: "#google", type: "OIDCProvider", provider: "google", email: "...", verified: true }
      4. actorScore 再計算 (25 → 50)
      5. DID_SERVICE.fetch(POST /did:etzhayyim:{hash}) で DID Doc 更新
```

#### ログイン (OAuth / Email / Passkey)

```
[Passkey ログイン]
  User → authn.etzhayyim.com /sign-in (WebAuthn)
    → passkey assertion verify (AUTH_DB)
    → passkey credential → account DID = did:etzhayyim:{hash}
    → JWT mint (iss = did:etzhayyim:{hash})

[Google OAuth ログイン]
  User → authn.etzhayyim.com /sign-in → Google OAuth flow
    → Google profile → provider_subject
    → linked_auth_methods WHERE provider='google' AND provider_subject=?
    → account DID = did:etzhayyim:{hash}
    → JWT mint (iss = did:etzhayyim:{hash})

[Email magic link ログイン]
  User → authn.etzhayyim.com /xrpc/com.etzhayyim.auth.linkEmailBegin { email: "jun@etzhayyim.com" }
    → OTP code 生成 → email 送信
  User → /xrpc/com.etzhayyim.auth.linkEmailVerify { email, code }
    → linked_auth_methods WHERE provider='email' AND email=?
    → account DID = did:etzhayyim:{hash}
    → JWT mint (iss = did:etzhayyim:{hash})
```

全ログイン経路で最終的に `iss = did:etzhayyim:{hash}` の JWT を発行。PDS 側は did:etzhayyim DID Doc の `verificationMethod` で署名検証。ログイン方法は PDS からは不可視 (auth Worker が抽象化)。

### D1 テーブル関係

```
AUTH_DB (authn.etzhayyim.com):
  passkey_credentials    ← WebAuthn public key + sign count
  email_link_codes       ← OTP codes (10min expiry)

ACCOUNTS_DB (authn.etzhayyim.com → 将来 accounts.etzhayyim.com 分離):
  linked_auth_methods    ← provider, provider_subject, email, verified
    account_did TEXT      ← "did:etzhayyim:{hash}" (移行後)

KEYS_DB (authn.etzhayyim.com):
  did_keys               ← signing key custody
    did TEXT PK           ← "did:etzhayyim:{hash}" (移行後)
    private_key_b64 TEXT
    public_key_multibase TEXT

DID_DB (did.etzhayyim.com):
  etzhayyim_did_docs          ← DID Document (authentication[] 含む)
    did TEXT PK           ← "did:etzhayyim:{hash}"
    document TEXT         ← JSON DID Doc
```

---

## 11. Organization Management

### 現状

- `account = actor = org DID` モデルは定義済み (deps.toml `invariants.identity`)
- `org_type` field は schema にある (`personal` / `company` / `npo` / `community` / `team`)
- **実装はゼロ**: メンバー招待、チーム管理、role 割り当て、全て未実装

### Organization DID Doc

```json
{
  "id": "did:etzhayyim:org-etzhayyim",
  "type": ["Organization", "DoDAFPerformer"],
  "controller": "did:etzhayyim:jun123",

  "verificationMethod": [{
    "id": "did:etzhayyim:org-etzhayyim#orgKey",
    "type": "EcdsaSecp256r1VerificationKey2019",
    "publicKeyMultibase": "zDna..."
  }],

  "members": [
    {
      "did": "did:etzhayyim:jun123",
      "role": "owner",
      "raci": "accountable",
      "invitedAt": "2026-04-16T00:00:00Z",
      "acceptedAt": "2026-04-16T00:00:00Z"
    },
    {
      "did": "did:etzhayyim:alice456",
      "role": "admin",
      "raci": "responsible",
      "invitedAt": "2026-04-16T00:00:00Z",
      "acceptedAt": "2026-04-16T01:00:00Z"
    },
    {
      "did": "did:etzhayyim:agent-bot1",
      "role": "agent-runtime",
      "raci": "responsible",
      "invitedAt": "2026-04-16T00:00:00Z",
      "acceptedAt": null
    }
  ],

  "teams": [
    {
      "id": "#engineering",
      "name": "Engineering",
      "members": ["did:etzhayyim:alice456", "did:etzhayyim:agent-bot1"],
      "rbac": { "grants": ["com.etzhayyim.apps.*.create", "com.etzhayyim.apps.*.query"] }
    },
    {
      "id": "#legal",
      "name": "Legal",
      "members": ["did:etzhayyim:jun123"],
      "rbac": { "grants": ["com.etzhayyim.apps.legal.*"] }
    }
  ],

  "orgSettings": {
    "org_type": "company",
    "sso": {
      "type": "oidc",
      "issuer": "https://login.microsoftonline.com/{tenant}/v2.0",
      "enforced": false
    },
    "defaultRole": "member",
    "allowedDomains": ["etzhayyim.com", "etzhayyim.com"]
  },

  "capabilityDelegation": [
    { "delegator": "did:etzhayyim:jun123", "raci": "accountable" }
  ],
  "rbac": {
    "roles": ["owner", "admin", "member", "viewer", "agent-runtime"],
    "grants": ["com.etzhayyim.apps.*"]
  },
  "consent": { "model": "gnap-vp", "piiTier": 3 },
  "dodaf": { "viewpoint": "OV-4", "performerBinding": "did:etzhayyim:jun123" }
}
```

### RBAC Role 階層

```
owner           ← org 全権限 + メンバー管理 + billing + org 削除
  admin         ← メンバー管理 + 設定変更 + 全 app 権限
    member      ← team の rbac.grants に基づく app 権限
      viewer    ← read-only
      agent-runtime  ← AI agent 専用 (query + invoke のみ, consent は synthetic)
```

Role は org DID Doc の `members[].role` で割り当て。各 member の did:etzhayyim DID Doc に `capabilityDelegation` が逆方向でリンク:

```json
// alice456 の did:etzhayyim DID Doc (member 側)
{
  "id": "did:etzhayyim:alice456",
  "capabilityDelegation": [
    {
      "delegator": "did:etzhayyim:org-etzhayyim",
      "raci": "responsible",
      "role": "admin"
    }
  ]
}
```

PDS canAccess() で org scope を解決:

```
did:etzhayyim:alice456 の DID Doc fetch (1 fetch)
  → capabilityDelegation.delegator = did:etzhayyim:org-etzhayyim
  → org DID Doc fetch (2nd fetch, cached 300s)
  → alice の role = admin
  → org.rbac.grants ∩ alice.capabilityInvocation.scope = effective scope
```

### 招待フロー

```
[招待]
  Owner (did:etzhayyim:jun123)
    POST /xrpc/com.etzhayyim.org.inviteMember
    {
      org: "did:etzhayyim:org-etzhayyim",
      invitee: "alice@etzhayyim.com",
      role: "admin"
    }

    → authn.etzhayyim.com が invite token 発行 (HMAC, 7d expiry)
    → email 送信 (invite link with token)
    → org DID Doc の members[] に pending entry 追加:
        { did: null, role: "admin", email: "alice@etzhayyim.com", acceptedAt: null }

[承認]
  Invitee
    → invite link click → authn.etzhayyim.com
    → 未登録: Passkey sign-up → did:etzhayyim:{hash} mint
    → 登録済み: ログイン (Passkey / OAuth / Email)
    → invite token verify
    → org DID Doc の members[] を更新:
        { did: "did:etzhayyim:alice456", role: "admin", acceptedAt: "..." }
    → alice の did:etzhayyim DID Doc に capabilityDelegation 追加:
        { delegator: "did:etzhayyim:org-etzhayyim", raci: "responsible", role: "admin" }

[拒否/取消]
  → invite token を revoke
  → org DID Doc の pending entry を削除
```

### Enterprise SSO (OIDC/SAML)

```json
{
  "orgSettings": {
    "sso": {
      "type": "oidc",
      "issuer": "https://login.microsoftonline.com/{tenant}/v2.0",
      "clientId": "...",
      "enforced": true,
      "allowedDomains": ["company.com"]
    }
  }
}
```

- `enforced: true` → org メンバーは SSO 経由でのみログイン可能
- SSO ログイン → `authentication[]` に `#sso-oidc` entry 追加
- SSO provider が member の email domain を検証 → org の `allowedDomains` と照合
- 既存の Google/Microsoft OAuth リンクとは別経路 (SSO は org 管理者が設定、OAuth は個人がリンク)

### Org Lexicon (新規 NSID)

```
com.etzhayyim.org.createOrganization    ← org DID 作成 (org_type, name, domain)
com.etzhayyim.org.getOrganization       ← org 情報取得
com.etzhayyim.org.updateOrganization    ← org 設定更新 (name, sso, allowedDomains)
com.etzhayyim.org.deleteOrganization    ← org 削除 (owner only, GDPR cascade purge)

com.etzhayyim.org.inviteMember          ← メンバー招待 (email or did:etzhayyim)
com.etzhayyim.org.acceptInvite          ← 招待承認
com.etzhayyim.org.removeMember          ← メンバー削除
com.etzhayyim.org.updateMemberRole      ← role 変更
com.etzhayyim.org.listMembers           ← メンバー一覧

com.etzhayyim.org.createTeam            ← チーム作成
com.etzhayyim.org.updateTeam            ← チーム設定更新
com.etzhayyim.org.deleteTeam            ← チーム削除
com.etzhayyim.org.addTeamMember         ← チームにメンバー追加
com.etzhayyim.org.removeTeamMember      ← チームからメンバー削除
com.etzhayyim.org.listTeams             ← チーム一覧

com.etzhayyim.org.configureSso          ← Enterprise SSO 設定
com.etzhayyim.org.testSso               ← SSO 接続テスト
```

### AI Agent as Org Member

AI agent を org メンバーとして追加可能:

```json
{
  "did": "did:etzhayyim:agent-bot1",
  "role": "agent-runtime",
  "raci": "responsible",
  "invitedAt": "2026-04-16T00:00:00Z",
  "acceptedAt": "2026-04-16T00:00:00Z"
}
```

- `role: "agent-runtime"` → query + invoke のみ、メンバー管理不可
- `acceptedAt` は即座に設定 (agent は自動承認)
- agent の consent model は org 設定に従う (org が `gnap-vp` なら agent も `gnap-vp`)
- agent の capabilityInvocation.scope は org の rbac.grants と team の rbac.grants の intersection

---

# Shannon Analysis

## Design Evolution η Comparison

| Schema | Auth RTT | AuthZ RTT | Total RTT | DID count | η |
|---|---|---|---|---|---|
| A: did:plc (mixed) | 1 | +1 (L2 graph) | 2 | 1 | 0.85 |
| D: did:plc + cap fields | 1 | 0 (embedded) | 1 | 1 | 0.78 (fake interop) |
| F: did:plc (auth) + did:etzhayyim (authz) | 1 | +1 (did:etzhayyim) | 2 | 2 | 0.88 |
| **G: did:etzhayyim unified** | **1** | **0 (same fetch)** | **1** | **1** | **0.92** |

## η Calculation (Schema G)

```
did:etzhayyim DID Doc = verificationMethod + capabilityInvocation + rbac + raci + consent + dodaf + type
  H_authn = ~60 bit (signing key, same as did:plc)
  H_authz = ~90 bit (capability + RBAC + RACI + consent)
  H_gov   = ~20 bit (type + DoDAF)
  H_total = ~170 bit
  H_wasted = 0 (all fields used by etzhayyim platform)

Resolution:
  1 fetch (did:etzhayyim DID Doc, ~2KB) → authn + authz + governance 全て

No cross-reference overhead:
  identityDID pointer 廃止 → -130 bit redundancy
  2 DID → 1 DID management → -1 bit method dispatch

Comparison to Schema F (split):
  F: 2 fetch × 2 DID = (500B + 1.5KB) = 2KB, 2 RTT
  G: 1 fetch × 1 DID = 2KB, 1 RTT
  RTT 50% reduction, same bandwidth, simpler management

η = 0.92 内訳:
  Base (Schema F):                        0.88
  + AuthN+AuthZ in single fetch:         +0.03 (RTT halved, L2 dead stub eliminated)
  + No cross-reference pointer:          +0.01 (identityDID field removed)
  + Single DID management:               +0.01 (no pair orphan risk)
  - Larger single DID Doc:               -0.01 (2KB vs 500B for auth-only path)
  = 0.92
```

## AI Agent DID Method Separation (unchanged)

**did:agent method separation is not justified.** 1.074 bit の型判別ゲインは resolver 冗長性 + 名前空間衝突リスクを上回らない。`did:etzhayyim` DID Doc の `type` field で十分。

---

# Comprehensive Comparison Matrix (Final)

| | A: did:plc mixed | D: did:plc + cap | F: split | **G: did:etzhayyim unified** |
|---|---|---|---|---|
| **Platform identity** | did:plc | did:plc | did:plc + did:etzhayyim | **did:etzhayyim** |
| **JWT.iss** | did:plc | did:plc | did:plc | **did:etzhayyim** |
| **η** | 0.85 | 0.78 | 0.88 | **0.92** |
| **Auth RTT** | 1 | 1 | 1 | **1** |
| **AuthZ RTT** | +1 (L2 graph) | 0 (fake) | +1 (did:etzhayyim) | **0 (same fetch)** |
| **Total RTT** | 2 | 1 | 2 | **1** |
| **L2 dead stub** | dead | fake fix | separate fix | **eliminated** |
| **DID count** | 1 | 1 | 2 | **1 (+ did:plc for federation)** |
| **AT Proto interop** | 100% (noise) | 85% (fake) | 100% (pure plc) | **100% (via federationDID)** |
| **Governance freedom** | constrained | constrained | unconstrained | **unconstrained** |
| **RBAC/RACI** | L2 graph dead | cap chain | did:etzhayyim doc | **did:etzhayyim doc (same fetch)** |
| **Consent/VP** | service EP | VP in plc doc | VP in did:etzhayyim | **VP in did:etzhayyim (same fetch)** |
| **Signing key** | did:plc key | did:plc key | did:plc key | **did:etzhayyim key** |

---

# Implementation Roadmap

## Phase 1: `did.etzhayyim.com` Worker + did:etzhayyim Resolution

- `plc.etzhayyim.com` Worker (`etzhayyim-plc-directory`) を `did.etzhayyim.com` にリネーム/拡張
- D1 に `etzhayyim_did_docs` / `etzhayyim_did_log` テーブル追加
- `GET /did:etzhayyim:{hash}` endpoint 追加
- `POST /did:etzhayyim:{hash}` endpoint 追加 (DID Doc create/update)
- did:plc resolution は既存のまま維持
- `plc.etzhayyim.com` → `did.etzhayyim.com` redirect
- CLI: `etzhayyim did resolve did:etzhayyim:{hash}`

## Phase 2: Signing Key Custody Migration (KEYS_DB → did:etzhayyim)

- `KEYS_DB.did_keys` の key を `did:web:*.etzhayyim.com` → `did:etzhayyim:{hash}` に migration
- 新規 actor は `did:etzhayyim` で signing key 発行
- `did:etzhayyim` DID Doc の `verificationMethod` に public key publish
- 既存 actor は grace period で `did:web` / `did:plc` key も並行維持

## Phase 3: PDS `authenticate()` did:etzhayyim Path

- `verify.ts` に `did:etzhayyim` 認証パス追加 (上記コード)
- `DID_SERVICE` binding を PDS `wrangler.jsonc` に追加
- `resolveetzhayyimDID()` + cache (300s TTL) 実装
- `canAccess()` に capability/RBAC/RACI check 追加 (DID Doc から)
- Legacy `did:plc` / `did:web` path は backward compat として維持

## Phase 4: Auth Worker + CLI Migration

- `handleGetServiceAuth` の `iss` を `did:etzhayyim` で受付
- `KEYS_DB` lookup key を `did:etzhayyim` に変更
- CLI `etzhayyim authn signin` が `did:etzhayyim` を `~/.etzhayyim/auth.json` に保存
- CLI `etzhayyim agent-token` が `iss=did:etzhayyim` で JWT mint
- `x-kotodama-verified` header 完全廃止

## Phase 5: OAuth / Email Authentication Integration

- 新規 Passkey sign-up → did:etzhayyim DID Doc に `authentication: [{ type: "WebAuthnAuthenticator" }]` 追加
- Google/Microsoft OAuth リンク → did:etzhayyim DID Doc の `authentication[]` に `OIDCProvider` entry 追加
- Email link リンク → did:etzhayyim DID Doc の `authentication[]` に `EmailVerification` entry 追加
- OAuth/Email ログイン → `linked_auth_methods` で account DID (`did:etzhayyim`) lookup → JWT mint
- `actorScore` を DID Doc 内で管理 (25pt × verified methods)
- `linked_auth_methods.account_did` を `did:web:authn.etzhayyim.com:user:{nanoid}` → `did:etzhayyim:{hash}` に migration

## Phase 6: Organization Management

- `com.etzhayyim.org.*` Lexicon 新規作成 (15 NSID)
- Org DID Doc 作成 (`createOrganization` → did:etzhayyim mint)
- メンバー招待フロー (invite token + email + sign-up/login + accept)
- チーム管理 (create/update/delete team + add/remove members)
- RBAC role 階層 (owner > admin > member > viewer > agent-runtime)
- Org membership → member DID Doc に `capabilityDelegation` 注入
- PDS `canAccess()` で org scope 解決 (member DID Doc → org DID Doc chain fetch)

## Phase 7: Enterprise SSO + Cohort Provisioning

- Enterprise SSO (OIDC/SAML) → org DID Doc の `orgSettings.sso` で設定
- `enforced: true` で org メンバーに SSO ログインを強制
- Cohort actor → org member として追加 (role = `agent-runtime`, 自動承認)
- `etzhayyim cohort seed` → did:etzhayyim DID Doc を `did.etzhayyim.com` に mint
- fission 時に新 did:etzhayyim + signing key を pair で発行
- federation 不要な cohort は `federationDID` を省略

## η Projection

```
Current:     η ≈ 0.36 (L2 dead stub, did:plc only)
Phase 1:     η ≈ 0.50 (did:etzhayyim resolver live, DID Doc 格納可能)
Phase 2:     η ≈ 0.65 (signing key を did:etzhayyim で管理)
Phase 3:     η ≈ 0.80 (PDS が did:etzhayyim で authn + authz)
Phase 4:     η ≈ 0.88 (auth Worker + CLI 移行完了)
Phase 5:     η ≈ 0.90 (OAuth/Email → did:etzhayyim 統合, actorScore)
Phase 6:     η ≈ 0.92 (org management, member RBAC/RACI live)
Phase 7:     η ≈ 0.94 (Enterprise SSO + cohort org integration)
```

---

# Consequences

## Positive

- **1 fetch で authn + authz**: L2 dead stub が構造的に解消される
- **1 DID per actor**: did:plc ↔ did:etzhayyim の pair 管理が不要 (platform 内)
- **RTT 50% 削減**: 認証と認可が同一 DID Doc fetch で完了
- **did:plc 汚さない**: AT Protocol federation adapter として pure なまま
- **Governance 自由度**: did:etzhayyim DID Doc は独自 schema で RBAC/RACI/consent/VP/DoDAF をフル表現
- **OAuth/Email 統合**: 全認証方法が did:etzhayyim DID Doc `authentication[]` に集約。login 経路を問わず `iss=did:etzhayyim` JWT を発行
- **Org management**: org DID Doc + member DID Doc の delegation chain で RBAC/RACI が構造的に表現される
- **AI agent = org member**: agent を org の member として追加可能 (role/RACI/consent を org 単位で管理)

## Negative

- **did:etzhayyim DID Doc が 2-3KB**: 認証だけで良いケースでも governance + authentication 情報が付いてくる (cache で amortize)
- **既存 signing key migration**: `did:web` / `did:plc` keyed の key を `did:etzhayyim` keyed に移行が必要
- **PDS 認証パス追加**: `verify.ts` に新 path が増える (legacy path と並行運用期間)
- **Org scope resolution に 2nd fetch**: member DID Doc → org DID Doc の chain fetch が必要 (cached)
- **linked_auth_methods migration**: account_did を `did:web` → `did:etzhayyim` に移行が必要

## Risks

- did:etzhayyim は独自 method → W3C DID Method Registry に登録するか private method として運用するかの判断が必要
- did:etzhayyim DID Doc 更新時に cache inconsistency (300s TTL window) → key rotation に grace window 必要
- 外部 AT Protocol implementation が `iss=did:etzhayyim` JWT を拒否する可能性 → federation path は `iss=did:plc` を維持
- OAuth provider の subject claim が変わった場合に linked_auth_methods の lookup が壊れる → provider_subject を immutable key として扱う
- Org DID Doc の members[] が大規模 (1000+ members) になると DID Doc サイズが肥大化 → member list を別テーブルに分離するか、DID Doc には member count のみ保持して full list は XRPC query で取得する設計も検討

---

# Alternatives Considered

## Rejected Schemas

| Schema | η | Rejection |
|---|---|---|
| A: Unified did:plc | 0.85 | governance fields が AT Proto で dead weight |
| B: did:plc + did:agent + did:org | 0.72 | 3 resolver, 40% AT Proto interop |
| C: did:web (hierarchical path) | 0.58 | org 改編で DID 壊れる |
| D: did:plc + capability fields | 0.78 | 偽の互換性 (AT Proto ignores cap fields) |
| E: did:plc + did:dodaf | 0.65 | viewpoint DID は identity の冗長 projection |
| F: did:plc (auth) + did:etzhayyim (authz) | 0.88 | 2 fetch / 2 DID, 不要な分離 |

## Rejected Method Names

| Pattern | η | Rejection |
|---|---|---|
| did:ai | 0.75 | global claim, 名前空間衝突, W3C 登録困難 |
| did:etzhayyim:ai/org/auth/gov (typed sub-path) | 0.91 | η 高いがシンプルさ優先で flat hash 採用 |
| did:w | 0.83 | 1 文字 method は W3C 登録困難, did:web と混同 |

## AI Agent Method Separation

did:agent method 新設は棄却。1.074 bit の型判別ゲインに対し resolver 冗長性 + 名前空間衝突のコストが過大。

---

# References

- [ADR-0019] atproto-native 5-layer identifier topology: `90-docs/adr/0019-atproto-native-identifier-topology.md`
- [ADR-0022] Auth topology consolidation: `90-docs/adr/0022-auth-topology-consolidation.md`
- [ADR-0023] Auth Shannon-optimal 4-layer: `90-docs/adr/0023-auth-shannon-optimal-4-layer.md`
- [ADR-0026] Agent-only reverse identity topology: `90-docs/adr/0026-agent-only-reverse-identity-topology.md`
- [ADR-0014] Self-hosted did:plc: `90-docs/adr/0014-self-hosted-did-plc.md`
- [ADR-0010] Per-DID signing key custody: `90-docs/adr/0010-per-did-signing-key-custody.md`
- [ADR-0018] PII Tier 3 + Cohort-First: `90-docs/adr/0018-pii-tier3-cohort-first.md`
- [W3C DID Core] https://www.w3.org/TR/did-core/
- [W3C VC Data Model 2.0] https://www.w3.org/TR/vc-data-model-2.0/
- [GNAP RFC 9635] Grant Negotiation and Authorization Protocol
- [DoDAF v2.02] DM2 Data Model
- [PDS verify.ts] `50-infra/cloudflare/workers/atproto/src/auth/verify.ts`
- [PDS permissions.ts] `50-infra/cloudflare/workers/atproto/src/auth/permissions.ts`
- [Auth Worker] `60-apps/etzhayyim-project-auth/worker/src-ts/index.ts`
- [CLI scoped_auth] `70-tools/etzhayyim/etzhayyim/scoped_auth.go`
- [Auth CLAUDE.md] `60-apps/etzhayyim-project-auth/CLAUDE.md`
- [Accounts scaffold] `60-apps/etzhayyim-project-accounts/CLAUDE.md`
- [ADR-0024] Auth accounts worker topology: `90-docs/adr/0024-auth-accounts-worker-topology.md`
