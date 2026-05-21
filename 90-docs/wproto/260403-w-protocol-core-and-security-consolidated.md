---
id: 260403-w-protocol-core-and-security-consolidated
title: W Protocol Core and Security (Consolidated)
status: active
doc_type: explanation
topic: w-protocol-core-security
authoritative: true
last_verified: 2026-04-03
authoritative_for:
  - w protocol core architecture baseline
  - federation and trust boundary baseline
  - confidential container position in w protocol security model
related:
  - 260403-wproto-transport-and-routing-consolidated
supersedes:
  - 260317-w-protocol-design
  - 260318-confidential-container-design
  - 260318-w-protocol-federation-design
  - 260318-w-protocol-sender-trust-design
superseded_by: []
---

# W Protocol Core and Security (Consolidated)

## Decision

- W Protocol を AT Protocol 互換を保つ基盤層として運用する。
- federation は DID ベースで外部公開し、内部 transport は統合 transport 設計に従う。
- trust boundary は network-assumed ではなく cryptographic verification 前提で定義する。
- confidential container は高機密ワークロードの実行境界として採用可能とする。

## Scope

- protocol core model
- federation boundary
- sender trust / E2E 前提
- confidential container role

## Notes

この統合文書が上記 4 文書の正本。
