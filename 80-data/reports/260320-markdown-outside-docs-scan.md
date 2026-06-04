# Markdown Outside Docs Scan

Date: 2026-03-20

## Goal

`90-docs/` 配下以外にも Markdown が大量に存在するため、`docs registry` に何を入れるべきで、何を別扱いにすべきかを棚卸しする。

## Scan Rule

集計では次を除外した。

- `node_modules`
- `.git`
- `.next`
- `dist`
- `build`
- `vendor`
- `test-results`
- `playwright-report`
- `.codex-home`

## Summary

- Filtered `*.md` total: `1830`
- `90-docs/`: `32`
- Outside `90-docs/`: `1798`

## Top-Level Distribution

| Top-level | Count |
|---|---:|
| `projects` | 1753 |
| `docs` | 32 |
| `packages` | 17 |
| `reports` | 14 |
| `infra` | 4 |
| repo root (`.`) | 3 |
| `.claude` | 3 |
| `.github` | 2 |
| `rules` | 2 |

## Conclusion

`docs registry` に repo 全体の Markdown を入れるのは不適切である。特に `projects/**` は project-local README / runbook / generated test artifact を多数含み、global discovery index に混ぜると Shannon redundancy と検索ノイズが急増する。

## Recommended Treatment

### 1. `90-docs/`

- canonical design / policy / reference
- current `docs/_registry/docs.json` の対象

### 2. `reports/`

- generated summary / audit / investigation output
- `reports/_index.json` の対象

### 3. `projects/**`

- default は global registry 対象外
- nearest `CLAUDE.md` / project README / project-local docs を優先
- 必要なら将来 `projects/<name>/_index.json` を project 単位で追加

### 4. `packages/**`

- package-local README / CLAUDE / design note を優先
- global registry 対象外
- package 単位の local index は将来追加余地あり

### 5. `rules/**`

- normative rule docs
- global design registry ではなく rule system の一部として扱う

## Sample Outside-Docs Files

- `README.md`
- `AGENTS.md`
- `CLAUDE.md`
- `50-infra/README.md`
- `60-apps/CLAUDE.md`
- `packages/CLAUDE.md`
- `reports/wit-issue-tracker.md`
- `rules/ui/appshellv2-layout-standard.md`
- `60-apps/etzhayyim-project-news/260311-news-tinygo-dataframe-lancedb-query-pattern.md`
- `packages/wasm/docs/authn-authz-access-control-design.md`

## Decision

- `docs registry` は `90-docs/` 専用のまま維持する
- `reports/` は別 index を持つ
- `projects/**` と `packages/**` は nearest-doc discovery に任せ、global registry には入れない
