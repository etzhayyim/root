---
id: 260403-did-namespace-and-lexicon-consolidated
title: DID, Namespace, and Lexicon Mapping (Consolidated)
status: active
doc_type: explanation
topic: did-namespace-lexicon
authoritative: true
last_verified: 2026-04-03
authoritative_for:
  - did path and nsid correspondence baseline
  - performerType and multi-did consolidation baseline
  - namespace and resource-flow lexicon governance
related:
  - 260403-wproto-transport-and-routing-consolidated
supersedes:
  - 260324-did-path-lexicon-correspondence
  - 260324-performertype-did-generation-design
  - 260324-w-protocol-nsid-namespace-design
  - 260323-states-resource-flow-lexicon-design
  - 260323-states-multi-did-consolidation-design
  - 260323-isic-multi-did-consolidation-design
  - 260326-did-follow-deps-governance-design
superseded_by: []
---

# DID, Namespace, and Lexicon Mapping (Consolidated)

## Decision

- DID path と NSID namespace を 1 対応の規則で運用する。
- performerType から DID 生成する規則を正本化する。
- states/isic 系の multi-did consolidation を同一ルールに統合する。
- follow/deps governance を namespace policy に接続する。

## Scope

- did/nsid correspondence
- performerType DID generation
- states/isic consolidation
- follow/deps governance

## Notes

この統合文書が上記 7 文書の正本。
