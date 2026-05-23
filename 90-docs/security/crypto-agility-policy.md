---
id: security-crypto-agility-policy
title: Crypto Agility Policy
status: active
doc_type: reference
topic: crypto-agility
authoritative: true
last_verified: 2026-03-20
authoritative_for:
  - crypto suite upgrade and compatibility policy
related:
  - security-readme
  - security-key-management
supersedes: []
superseded_by: []
---

# Crypto Agility Policy

## Purpose

Enable algorithm upgrades without data loss or forced big-bang migrations.

## Policy

- All encrypted objects must include:
  - `envelope.version`
  - algorithm identifiers (`kdf`, `aead`, `wrap`, `sig`)
- New writes use the current default suite.
- Reads must support at least:
  - current suite
  - previous suite

## Versioning

- `zk-v1`: initial production suite.
- `zk-v2+`: introduced only after:
  - published test vectors
  - interop validation across supported clients
  - staged rollout plan and rollback plan

## Deprecation Workflow

1. Mark suite as deprecated.
2. Stop using it for new writes.
3. Re-encrypt active objects in background with user/device authorization.
4. Remove read compatibility after completion threshold and grace period.

## Required Controls

- Compatibility tests in CI for all supported envelope versions.
- Known-answer tests for all crypto primitives in use.
- Runtime metrics:
  - object count by envelope version
  - decryption failure rates by version

## DID Auth Compatibility Notes

- DID claims are authorization input only.
- Crypto suite upgrades must not require DID schema changes.
- Recovery and device enrollment remain independent from Passkey reset flows.
- Secret-key-gated decryption (`Account Password + Secret Key`) remains mandatory across crypto versions.

## Incident Response Hooks

- If primitive weakness is announced:
  - disable vulnerable suite for writes immediately
  - prioritize key and data re-wrap jobs
  - notify users/org admins of required client upgrade windows
