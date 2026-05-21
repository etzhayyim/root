---
id: 260403-security-architecture-threat-key-consolidated
title: Security Architecture, Threat Model, and Key Management (Consolidated)
status: active
doc_type: reference
topic: security-architecture-threat-key
authoritative: true
last_verified: 2026-04-03
authoritative_for:
  - repository wide security architecture and identity model
  - zero knowledge plus did:web passkey threat model
  - client held decryption key management standard
related:
  - security-readme
  - security-crypto-agility-policy
supersedes:
  - security-architecture
  - security-threat-model
  - security-key-management
superseded_by: []
---

# Security Architecture, Threat Model, and Key Management (Consolidated)

## Goal

Security の正本を 1 つに統合し、設計・脅威・鍵管理の重複記述をなくす。

## Identity and Trust Baseline

- Identity: `did:web` + Passkey (WebAuthn)
- Session: short-lived token + DPoP binding
- Trust: backend は plaintext data / long-term decryption key を信頼境界外として扱う

## Security Invariants

1. server は長期 plaintext 復号鍵を保持しない
2. DID 認証のみで自動復号しない
3. key 操作は versioned + auditable
4. revocation completion に明示 SLO を持つ

## Threat Model Summary

主要脅威:

- backend plaintext 参照
- token replay / session theft
- tenant boundary 越えアクセス
- compromised workload / dependency exfiltration
- recovery flow abuse

主要対策:

- ciphertext-only API/storage
- DPoP + strict `(org_id, user_id, did)` binding
- signed envelope metadata + immutable audit trail
- dependency pinning / SBOM / runtime egress control

## Key Management Baseline

- Password KDF: Argon2id
- AEAD: XChaCha20-Poly1305 (or AES-256-GCM)
- Key agreement: X25519
- Signature: Ed25519
- Expansion: HKDF-SHA256

運用ルール:

- 永続化は wrapped keys + ciphertext のみ
- passphrase / derived master key は永続化しない
- device revoke 時は key path を再ラップ

## Cross-App and Governance

- cross-app call は caller DID + org context を必須
- host 側 governance gate で dispatch 前認可
- audit は暗号的検証可能な履歴として保存

## Repository Contract

- authn/authz は server-side で実施可能
- decryption authority は client-side key possession に限定
- encryption/decryption の実体は client を正本とする

## Superseded Docs

以下は本書に統合済み。

- `docs/security/architecture.md`
- `docs/security/threat-model.md`
- `docs/security/key-management.md`
