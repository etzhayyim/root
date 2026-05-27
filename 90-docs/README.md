---
id: docs-readme
title: Docs System
status: active
doc_type: reference
topic: docs-system-index
authoritative: true
last_verified: 2026-03-20
authoritative_for:
  - docs system entrypoint
related:
  - docs-claude
  - adr-readme
supersedes: []
superseded_by: []
---

# Docs System

`90-docs/` の本文は Markdown を canonical source とする。LLM / tooling 向け discovery は registry に分離する。

## Read Order

1. `docs/_registry/docs.json`
2. `docs/_registry/graph.jsonld`
3. 対象 topic の authoritative doc
4. 関連する ADR

## Layout

- `docs/{lexicon.foldername}/*.md`: lexicon/folder 単位の design / evaluation / reference 本文
- `docs/*.md`: docs system 直下ドキュメント
- `docs/adr/*.md`: architecture decision records
- `docs/_registry/docs.json`: authoritative registry
- `docs/_registry/graph.jsonld`: relation graph

## Consolidation Policy

- 1 topic = authoritative doc は原則 1 つ
- 重複内容を統合した場合、旧 doc は原則削除する
- 統合先 doc の front matter `supersedes` に削除元 id を残す

詳細ルールは [90-docs/CLAUDE.md](/Users/junkawasaki/github/etzhayyim-root/90-docs/CLAUDE.md) を参照。
