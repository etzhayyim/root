---
id: 260403-inference-runtime-and-artifacts-consolidated
title: Inference Runtime and Artifacts (Consolidated)
status: active
doc_type: explanation
topic: inference-runtime-artifacts
authoritative: true
last_verified: 2026-04-03
authoritative_for:
  - inference runtime baseline across rust and wasm paths
  - hayate artifact schema and runtime compatibility baseline
related:
supersedes:
  - 260325-claude-native-lifecycle-management
  - ingredient-safety-scoring
  - 260330-hayate-wasm-kotodama-design
  - 260330-hayate-artifact-schema-design
superseded_by: []
---

# Inference Runtime and Artifacts (Consolidated)

## Decision

- inference runtime は rust/ts/wasm の経路を単一運用基準に統合する。
- artifact schema は hayate runtime 互換の正本として維持する。
- historical fallback は運用上の既定経路から除外する。

## Scope

- runtime architecture
- wit contract/runtime boundary
- hayate wasm execution
- artifact schema

## Notes

この統合文書が上記 4 文書の正本。
