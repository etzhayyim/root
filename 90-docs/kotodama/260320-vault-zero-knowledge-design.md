---
id: 260320-vault-zero-knowledge-design
title: "Vault Zero-Knowledge Design — 1Password-Style Key Hierarchy for All Principal Types"
status: active
doc_type: explanation
topic: vault-zero-knowledge-crypto
authoritative: true
authoritative_for:
  - vault.etzhayyim.com zero knowledge key hierarchy and encryption design
  - vault principal types and key exchange patterns
  - vault WIT interface design (kotodama:secrets/vault)
last_verified: "2026-03-20"
related:
  - yoro-superapp-oembed-design
  - 260317-yata-secure-cas-design
  - 260315-atprotocol-signal-design
  - 260319-kotodama-wit-dodaf-nist-coverage
supersedes: []
superseded_by: []
---

# Vault Zero-Knowledge Design — 1Password-Style Key Hierarchy for All Principal Types

## Goal

vault.etzhayyim.com を **zero-knowledge** アーキテクチャで再設計する。server は暗号文のみ保持し、平文に一切触れない。Human / Agent / Org の全 principal type に対応し、6 通りの鍵共有パターン (U2U, U2A, U2O, cross-actor, A2U, A2O) + org 間 (O2O, O2U, O2A) を統一的に扱う。

## Scope

- `kotodama:secrets/vault` WIT interface の設計 (既存 `kotodama:secrets/secrets` とは独立)
- Key hierarchy (3 層: Identity → Vault → Item)
- 全 9 参加者パターンの鍵交換プロトコル
- `kotodama:consent` との統合 (delegation flow)
- Cloudflare native storage mapping (D1 / B2 / Secrets Store / DO)
- kaiyaku.etzhayyim.com 連携の具体フロー

## Non-Scope

- Signal Protocol (forward secrecy — vault とは相反する要件)
- HSM / external KMS 連携 (将来拡張)
- Secret Key の物理バックアップ UI (AppShell 実装は別 doc)

## Why Not Signal Protocol

| 観点 | Signal Protocol | Vault Crypto |
|---|---|---|
| 目的 | メッセージ E2E (forward secrecy) | データ at-rest (durability) |
| 鍵ライフサイクル | Ratchet で常に回転 | 長期安定 (account key は年単位) |
| Forward secrecy | 必須 | 不要 (過去データに再アクセスが必要) |
| 復号回数 | 受信時 1 回 (consume) | 何度でも (retrieve) |
| 鍵紛失 | 新 session で回復 | Secret Key + password で全データ回復 |

Forward secrecy と data durability は相反する。Vault には 1Password モデルが適切。

## Existing `kotodama:secrets` との関係

| Interface | 役割 | Server trust |
|---|---|---|
| `kotodama:secrets/secrets` | Flat KV secrets (host-encrypted AES-256-GCM) | **server-trusted** — host が平文を見る |
| `kotodama:secrets/vault` (新規) | 1Password-style zero-knowledge vault | **zero-knowledge** — server は暗号文のみ |

両者は共存する。`secrets` は runtime config / API key 等の operational secrets 用。`vault` は user credentials / sensitive data 用。

## Principal Model

### 3 Principal Types

| Principal | Identity | Key Material | Key Derivation Location |
|---|---|---|---|
| **Human** | did:web user DID | `password + Secret Key → Account Key` | Client-side (AppShell JS, SubtleCrypto) |
| **Agent** | App DID | `agent_seed → Account Key` | Host-side (TS host runtime) |
| **Org** | did:web org DID | `threshold(admin Identity Keys) → Org Master Key` | Ceremony (N-of-M admin) |

### Human

- Account Key は `HKDF-SHA256(password || secret_key, salt, "vault-v1")` で導出
- password は user の頭にのみ存在。server に送信しない
- Secret Key は初回登録時に client-side で生成。QR / PDF で user が保管
- SRP (Secure Remote Password) で認証。server は SRP verifier のみ保持

### Agent

- `agent_seed` は Cloudflare Secrets Store に格納 (per-app)
- Account Key は `HKDF-SHA256(agent_seed || app_did, salt, "vault-v1")` で導出
- TS host runtime 内で完結。guest WASM には復号済み plaintext を渡す
- Agent の「password」= Secrets Store 内の seed。Human と同等の security guarantee

### Org

- Org Master Key は admin N-of-M threshold で復元
- 各 admin が自身の Account Key で Org Master Key share を wrap して保存
- Org ceremony: N 人の admin が各自の share を提出 → combine → Org Master Key
- Org vault の item 追加/削除は任意の member が行える (Org Master Key なしで vault key で操作)
- Org Master Key が必要なのは vault key rotation / admin 変更時のみ

## Key Hierarchy (3 Layer)

```
Layer 0: Identity Key (principal-specific)
  ├─ Human:  HKDF(password || secret_key, salt)
  ├─ Agent:  HKDF(agent_seed || app_did, salt)
  └─ Org:    threshold_combine(admin_identity_keys[N/M])
  Output: X25519 keypair (identity_sk, identity_pk)

Layer 1: Vault Key (per-vault)
  = random AES-256 key (generated at vault creation)
  → wrapped_vault_key = AES-256-GCM(identity_key, vault_key)
  → server stores wrapped_vault_key per member
  → shared vault: vault_key wrapped by each member's identity_pk

Layer 2: Item Key (per-item)
  = random AES-256 key (generated at item creation)
  → wrapped_item_key = AES-256-GCM(vault_key, item_key)
  → encrypted_item   = AES-256-GCM(item_key, plaintext_json)
  → server stores (wrapped_item_key, nonce, ciphertext)
```

### Why Per-Item Key

- Item 単位の revocation (vault key rotation なしで単一 item を無効化)
- Delegation 時に vault key ではなく item key を re-wrap (最小権限)
- Item 削除時に item key を破棄するだけで暗号学的消去

## 9 Key Exchange Patterns

### Notation

- `pk(X)` = X の identity public key (X25519)
- `wrap(K, data)` = AES-256-GCM(K, data)
- `x25519(sk_A, pk_B)` = X25519 shared secret

### User-to-User (U2U)

```
Alice → Bob:
  shared = x25519(alice_sk, pk(bob))
  wrapped_vault_key_for_bob = wrap(shared, vault_key)
  → server stores (bob_did, wrapped_vault_key_for_bob)
Bob:
  shared = x25519(bob_sk, pk(alice))
  vault_key = unwrap(shared, wrapped_vault_key_for_bob)
```

### User-to-Agent (U2A)

```
User → kaiyaku:
  1. kotodama:consent request (GNAP) → User 承認
  2. shared = x25519(user_sk, pk(kaiyaku))
  3. wrapped_item_key_for_kaiyaku = wrap(shared, item_key)
  4. delegate-item(wrapped_key, consent_grant_id, ttl)
kaiyaku host:
  shared = x25519(kaiyaku_sk, pk(user))
  item_key = unwrap(shared, wrapped_item_key_for_kaiyaku)
  plaintext = decrypt(item_key, ciphertext)
```

### User-to-Org (U2O)

```
User → Org vault:
  wrapped_vault_key_for_user = wrap(org_vault_key_shared_secret, vault_key)
  → User が org vault の member として追加される
  → 全 org member が vault_key にアクセス可能
```

### agent conversation

```
Agent-A → Agent-B:
  shared = x25519(agent_a_sk, pk(agent_b))
  wrapped = wrap(shared, item_key)
  delegate-item(wrapped, consent_grant_id, ttl)
Agent-B host:
  shared = x25519(agent_b_sk, pk(agent_a))
  item_key = unwrap(shared, wrapped)
  → host-to-host, 両方 runtime 内完結
```

### Agent-to-User (A2U)

```
Agent → User:
  shared = x25519(agent_sk, pk(user))
  wrapped = wrap(shared, item_key)
  delegate-item(wrapped, consent_grant_id, ttl)
User client-side:
  shared = x25519(user_sk, pk(agent))
  item_key = unwrap(shared, wrapped)
  plaintext = decrypt(item_key, ciphertext)
```

### Agent-to-Org (A2O)

```
Agent → Org:
  shared = x25519(agent_sk, pk(org))
  wrapped = wrap(shared, vault_key)
  → Org members が vault_key → item access
```

### Org-to-User (O2U) / Org-to-Agent (O2A) / Org-to-Org (O2O)

```
Org → target:
  shared = x25519(org_sk, pk(target))
  wrapped = wrap(shared, item_key_or_vault_key)
  → target が unwrap
O2O: 両 org の pk で相互 wrap
```

## Consent Integration

Delegation (cross-principal item sharing) は `kotodama:consent` が gate:

```
1. Requester: ConsentRequestConsent(resource=vault://..., scope=record)
   → W Protocol DM (kind="consent.request") to grantor
2. Grantor: approve → ConsentGrant VC 発行
3. Requester: get-public-key(grantor) → pk
4. Grantor: client/host-side re-wrap:
   shared = x25519(grantor_sk, pk(requester))
   wrapped_item_key_for_requester = wrap(shared, item_key)
   delegate-item(wrapped_key, consent_grant_id, ttl)
5. Requester: fetch-delegated(delegation_id) → unwrap → plaintext
6. TTL expiry or explicit revoke → delegation invalidated
```

### Agent Consent の特殊性

Agent は自律的に consent を承認できる。UMA pre-policy として:
- Org admin が「kaiyaku は vault://org/credentials/* に TTL=1h でアクセス可」を事前定義
- Agent が consent request → UMA policy match → auto-approve (human interaction 不要)
- Audit trail は `kotodama:consent` graph に記録

## WIT Interface: `kotodama:secrets/vault`

```wit
// kotodama:secrets@1.0.0 package に追加

interface vault {
    enum principal-kind { human, agent, org }

    record principal-ref {
        kind: principal-kind,
        did: string,
    }

    /// Register identity. Human: SRP verifier. Agent: empty (host derives).
    /// Returns identity public key (X25519).
    register-identity: func(
        principal: principal-ref,
        verifier-or-empty: list<u8>,
    ) -> result<list<u8>, string>;

    /// Authenticate and unlock. Human: SRP proof. Agent/Org: empty.
    unlock: func(
        principal: principal-ref,
        auth-proof: list<u8>,
    ) -> result<_, string>;

    /// Get a principal's identity public key.
    get-public-key: func(principal: principal-ref) -> result<list<u8>, string>;

    // ── Vault lifecycle ──

    record vault-def {
        vault-id: string,
        name: string,
        owner: principal-ref,
        wrapped-vault-key: list<u8>,
    }

    create-vault: func(def: vault-def) -> result<string, string>;

    add-member: func(
        vault-id: string,
        member: principal-ref,
        wrapped-key-for-member: list<u8>,
    ) -> result<_, string>;

    remove-member: func(vault-id: string, member: principal-ref) -> result<_, string>;

    list-vaults: func(principal: principal-ref) -> result<list<vault-def>, string>;

    // ── Item CRUD (all ciphertext) ──

    record vault-item {
        item-id: string,
        vault-id: string,
        wrapped-item-key: list<u8>,
        ciphertext: list<u8>,
        nonce: list<u8>,
        metadata-json: string,
    }

    put-item: func(item: vault-item) -> result<_, string>;
    get-item: func(vault-id: string, item-id: string) -> result<vault-item, string>;
    delete-item: func(vault-id: string, item-id: string) -> result<_, string>;
    list-items: func(vault-id: string, offset: u32, limit: u32) -> result<list<vault-item>, string>;

    // ── Delegation (consent-gated) ──

    delegate-item: func(
        vault-id: string,
        item-id: string,
        delegate: principal-ref,
        wrapped-item-key-for-delegate: list<u8>,
        consent-grant-id: string,
        ttl-secs: u32,
    ) -> result<string, string>;

    fetch-delegated: func(delegation-id: string) -> result<vault-item, string>;
    revoke-delegation: func(delegation-id: string) -> result<_, string>;
}
```

## Storage Mapping (Cloudflare Native)

| Data | Storage | Schema |
|---|---|---|
| Identity public key + SRP verifier | D1 `vault_identities` | `(did TEXT PK, kind TEXT, pubkey BLOB, srp_verifier BLOB, created_at TEXT)` |
| Vault definition | D1 `vault_vaults` | `(vault_id TEXT PK, name TEXT, owner_did TEXT, org_id TEXT, created_at TEXT)` |
| Vault membership (wrapped keys) | D1 `vault_memberships` | `(vault_id TEXT, member_did TEXT, wrapped_vault_key BLOB, PK(vault_id, member_did))` |
| Item metadata | D1 `vault_items` | `(item_id TEXT PK, vault_id TEXT, metadata_json TEXT, cid TEXT, org_id TEXT, created_at TEXT)` |
| Item ciphertext | B2 | key = `vault/{vault_id}/{item_id}`, value = `wrapped_item_key || nonce || ciphertext` |
| Delegations | D1 `vault_delegations` | `(delegation_id TEXT PK, vault_id TEXT, item_id TEXT, delegate_did TEXT, wrapped_key BLOB, consent_id TEXT, expires_at TEXT)` |
| Agent seed | Secrets Store | `agent_seed_{nanoid}` (Cloudflare managed, never exported) |

### Why D1 + B2 (not Cypher graph)

- D1: operational CRUD (index, membership, delegation lookup) — SQL の JOIN / WHERE が自然
- B2: large encrypted blobs (item ciphertext は可変長)
- Cypher graph: consent grant / audit trail は graph-native (既に `kotodama:consent` が使用)

## kaiyaku.etzhayyim.com 連携フロー (具体例)

```
User: "Netflix を解約して"

1. kaiyaku: ConsentCheck(user_did → kaiyaku_did, vault://org/credentials/netflix)
   → grant なし

2. kaiyaku: ConsentRequestConsent({
     grantee: kaiyaku_did,
     scope: record,
     resources: ["vault://org/credentials/netflix"],
     disclosed_claims: ["username", "password"],
     purpose: "Web service cancellation",
     sensitivity: confidential,
     participant_type: agent,
   })
   → consent_id returned, W Protocol DM sent to user

3. User (AppShell chat): consent.request card 表示
   → "kaiyaku が Netflix の認証情報に 1 時間アクセスを要求しています"
   → User taps "承認"

4. User client-side (AppShell JS):
   a. ConsentResolve(consent_id, approve=true) → ConsentGrant VC 発行
   b. vault_key = unwrap(account_key, wrapped_vault_key)
   c. item_key = unwrap(vault_key, wrapped_item_key)
   d. kaiyaku_pk = vault.get-public-key({agent, kaiyaku_did})
   e. shared = x25519(user_sk, kaiyaku_pk)
   f. wrapped_for_kaiyaku = wrap(shared, item_key)
   g. vault.delegate-item(vault_id, item_id, kaiyaku, wrapped_for_kaiyaku, consent_id, ttl=3600)

5. kaiyaku host:
   a. delegation_id を受信 (W Protocol notification)
   b. vault.fetch-delegated(delegation_id)
   c. shared = x25519(kaiyaku_sk, user_pk)
   d. item_key = unwrap(shared, wrapped_for_kaiyaku)
   e. {username, password} = decrypt(item_key, ciphertext)
   f. browser automation で Netflix 解約実行

6. 完了後:
   a. kaiyaku: vault.revoke-delegation(delegation_id)
   b. item_key, plaintext を memory から消去
   c. TTL (1h) 経過で自動 revoke (バックアップ)
```

## Security Properties

| Property | Guarantee |
|---|---|
| **Zero-knowledge** | Server は wrapped keys + ciphertext のみ保持。平文・identity key に触れない |
| **Compromise resilience** | Server 侵害 = 暗号文のみ流出。password + Secret Key なしで復号不能 |
| **Forward secrecy** | なし (意図的 — data durability が要件) |
| **Per-item isolation** | Item key 漏洩は当該 item のみ影響。vault key / account key は安全 |
| **Delegation scoping** | Consent grant + TTL + per-item re-wrap。vault 全体は共有しない |
| **Agent seed protection** | Secrets Store (Cloudflare managed) — export 不可、runtime memory のみ |
| **Org threshold** | N-of-M admin ceremony。単一 admin の侵害では Org Master Key 復元不能 |
| **Audit trail** | Consent graph (MDAG) + vault delegation log (D1) |

## Implementation Phases

| Phase | 内容 | 依存 |
|---|---|---|
| **P0** | WIT interface (`kotodama:secrets/vault`) + D1 schema + B2 storage | — |
| **P1** | Agent crypto (host-side HKDF + AES-GCM + X25519) | P0 |
| **P2** | Human crypto (AppShell JS SubtleCrypto + SRP) | P0 |
| **P3** | Consent-gated delegation (U2A, cross-actor) | P1 + `kotodama:consent` |
| **P4** | Org threshold (N-of-M Shamir's Secret Sharing) | P2 |
| **P5** | kaiyaku integration (end-to-end flow) | P3 |
| **P6** | Secret Key backup UX (QR, PDF, recovery kit) | P2 |
