---
id: adr-2604251200-vault-zero-knowledge-invariant
title: "ADR: Vault zero-knowledge invariant — server holds only ciphertext, wrapped keys, metadata"
status: active
doc_type: adr
topic: vault-zero-knowledge
authoritative: true
last_verified: 2026-04-25
authoritative_for:
  - vault.etzhayyim.com server-side data classification
  - vaultKey / memberDeviceKey custody boundary
  - MCP response redaction contract
related:
  - adr-0010-stage-1-kek-envelope
  - adr-2604231811-atproto-extension-service-layers
supersedes: []
superseded_by: []
---

# Context

`vault.etzhayyim.com` は Layer 12 Secret Vault (ADR-2604231811) として、メンバー間で
共有する API key / credential を保持する。AT Protocol federable repo に PII /
credential を書く規約違反 (ADR-0018 / Root-Only "AT Protocol Faithful") を
避けつつ、CF Worker / Browser / `etzhayyim` CLI から透過的に key 取得を可能にする
ため、**zero-knowledge** が前提条件となる。Server (Worker + D1) は plaintext
を一度も観測してはならない。本 ADR は CLAUDE.md の Root-Only "Vault Zero-
Knowledge Invariant" を ADR 化し、不変条件と禁止事項を確定する。

# Decision

## D1. Server-side data classification

`vault.etzhayyim.com` server (CF Worker + D1) が保持できるのは以下のみ:
- `vault_items.ciphertext` (BLOB, AES-GCM, ≤ 900 KB per item)
- wrapped vaultKey (AES-KW, member 単位で多重 wrap)
- wrapped item key (ECIES X25519 + HKDF + AES-KW share)
- metadata (item id, owner did, recipient did[], created_at, audit log)

**Forbidden on server**: plaintext value, raw vaultKey, raw memberDeviceKey,
unwrapped item key。これらが Worker memory に存在するのは唯一 §D2 の例外のみ。

## D2. ephemeralVaultKey exception (`com.etzhayyim.vault.injectWorkerSecret`)

CF Workers Secret 注入のために 1 回だけ caller が unwrap 済み vaultKey
(`ephemeralVaultKey`) を server に渡す。Server は `wrangler secret put` 完了
直後に memory から drop し、log / persist / cache しない。

## D3. memberDeviceKey custody

memberDeviceKey は **WebAuthn PRF** (browser) または **macOS Keychain** (CLI)
のみに存在する (ADR-2604251205)。Plaintext 取得は必ず caller の local device
key を使う `etzhayyim` CLI または browser を経由する。Server / MCP / API endpoint
からは取り出せない。

## D4. MCP response redaction contract

`/mcp` 経由の tool response は metadata only。`redactVaultResponse` が以下
field を強制除去する:
- `ciphertext`
- `wrappedVaultKey`
- `wrappedItemKey`
- `iv`
- `mac`
- `ephemeralVaultKey`

許可されている MCP tool: `etzhayyim.vault.list` / `listItems` / `audit` (metadata)。
`get` / `decrypt` 系は MCP 非公開、CLI/browser 専用。

## D5. Public AT Record gate

`com.atproto.repo.createRecord` で wrapped key / ciphertext を含む record を
public collection に書く操作は禁止。`com.etzhayyim.vault.*` collection は federable
gate (ADR-0085) で firehose から除外する。

# Consequences

- Server breach = ciphertext + wrapped keys のみ流出。Plaintext 復号には別途
  各 member の WebAuthn authenticator / macOS Keychain を要する。
- Server-side search / index 不可 — metadata (tag, name) は plaintext 保存だが
  value/secret 列の検索は不可能。
- MCP tool で plaintext 取得はできない。Agent 経由で secret を読むには `etzhayyim
  vault run` を CLI で実行する必要がある。

# Alternatives Considered

- **Server-side decrypt cache**: 性能向上するが breach 時の影響が plaintext
  全件流出になり zero-knowledge 不成立。却下。
- **HSM for memberDeviceKey**: 個人 HSM 保有を全 member に要求するのは運用
  不能。WebAuthn PRF + macOS Keychain で同等の TPM-backed 強度を確保。

# References

- `60-apps/etzhayyim-project-vault/CLAUDE.md`
- `redactVaultResponse` 実装: `60-apps/etzhayyim-project-vault/worker/src/mcp.ts`
- ADR-2604251205 (Local Secret Storage = macOS Keychain)
- ADR-2604251210 (Credential Sharing via etzhayyim Vault + Bitwarden)
