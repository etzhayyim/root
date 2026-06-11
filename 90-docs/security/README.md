---
id: security-readme
title: Security Architecture Documents
status: active
doc_type: reference
topic: security-index
authoritative: true
last_verified: 2026-03-20
authoritative_for:
  - security documentation entrypoint
related:
  - security-architecture
  - security-key-management
  - security-threat-model
  - security-crypto-agility-policy
supersedes: []
superseded_by: []
---

# Security Architecture Documents

This folder defines the repository-wide security design for a zero-knowledge model with did:web + Passkey authentication.

- `docs/security/260403-security-architecture-threat-key-consolidated.md` (authoritative)
- `90-docs/security/2606111200-quantum-singularity-crypto-survivability.md` (quantum/singularity survivability paper → suite pqh-v1, ADR-2606111300)
- `docs/security/crypto-agility-policy.md`
- `docs/security/schemas/zk-v1-envelope.schema.json`
- `docs/security/test-vectors/zk-v1-envelope.example.json`

## Selected Platform Standard

The current standard for this repository is `did:web + Passkey + client-held key management`.

- did:web + Passkey (WebAuthn) handles authentication, sessions, and DPoP token binding.
- Client encryption requires `Account Password + Secret Key`.
- Servers store ciphertext and wrapped keys only.

## Core Principle

Servers must only process ciphertext by default. Identity and access control can be server-side, but decryption keys remain client-controlled.

## Identity Positioning

did:web + Passkey is the identity provider and session authority. The identity layer is not a key management system.

- DID auth manages `who can access encrypted blobs`.
- Clients manage `who can decrypt encrypted blobs`.

## Rollout Order

1. Introduce key hierarchy and envelope format.
2. Switch write paths to client-side encryption.
3. Migrate read paths to client-side decryption.
4. Enforce no-plaintext policy in APIs, logs, and storage.
5. Add continuous verification gates in CI/CD.
